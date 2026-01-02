import time
import uuid
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .logging_setup import setup_logging
from .db import engine, Base, SessionLocal
from .models import Ticket, RetrievalLog, ResponseLog
from .schemas import TicketRequest, ClassifyResponse, RespondResponse, Citation
from .metrics import REQUEST_LATENCY, RETRIEVAL_LATENCY
from .gemini_classifier import classify_with_gemini, GeminiError
from .vector_store import VectorStore
from .rag import build_rag_answer

setup_logging()
log = logging.getLogger("triage.api")

app = FastAPI(title="Ticket Triage Service (Scenario II)")

VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "data/vector_store")
DOCS_DIR = os.getenv("DOCS_DIR", "data/docs")

vs = VectorStore(store_dir=VECTOR_STORE_DIR)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load vector store; if missing, build from local docs for convenience.
    if not vs.load():
        vs.build_from_dir(DOCS_DIR)
        vs.save()
        log.info("Vector store built from local docs", extra={"operation": "vector_build"})
    else:
        log.info("Vector store loaded", extra={"operation": "vector_load"})

@app.middleware("http")
async def correlation_logging(request: Request, call_next):
    start = time.perf_counter()
    correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    try:
        response = await call_next(request)
        return response
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        log.info(
            "request_done",
            extra={"correlation_id": correlation_id, "operation": "http_request", "latency_ms": latency_ms},
        )

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/classify", response_model=ClassifyResponse)
async def classify(req: TicketRequest, request: Request):
    with REQUEST_LATENCY.labels(endpoint="/classify").time():
        try:
            result = classify_with_gemini(req.text)
        except GeminiError as e:
            # Hard failure: explicit so caller knows model is unavailable
            raise HTTPException(status_code=503, detail=f"classifier unavailable: {str(e)}")

        # Persist ticket + classification
        async with SessionLocal() as session:
            t = Ticket(
                external_id=req.external_id,
                text=req.text,
                product_area=result["product_area"],
                urgency=result["urgency"],
                classification_reason=result["reason"],
                classifier_model=result["model"],
            )
            session.add(t)
            await session.commit()

        return ClassifyResponse(
            product_area=result["product_area"],
            urgency=result["urgency"],
            reason=result["reason"],
            model=result["model"],
        )

@app.post("/respond", response_model=RespondResponse)
async def respond(req: TicketRequest, request: Request):
    with REQUEST_LATENCY.labels(endpoint="/respond").time():
        # 1) Classify (Gemini) and persist ticket metadata
        try:
            cls = classify_with_gemini(req.text)
        except GeminiError as e:
            raise HTTPException(status_code=503, detail=f"classifier unavailable: {str(e)}")

        async with SessionLocal() as session:
            t = Ticket(
                external_id=req.external_id,
                text=req.text,
                product_area=cls["product_area"],
                urgency=cls["urgency"],
                classification_reason=cls["reason"],
                classifier_model=cls["model"],
            )
            session.add(t)
            await session.flush()  # get ticket id

            # 2) Retrieve docs
            t0 = time.perf_counter()
            retrieved = vs.query(req.text, k=4)
            retrieval_s = time.perf_counter() - t0
            RETRIEVAL_LATENCY.observe(retrieval_s)

            # store retrieval logs
            for rank, (chunk, score) in enumerate(retrieved, start=1):
                session.add(RetrievalLog(ticket_id=t.id, doc_id=chunk.doc_id, score=float(score), rank=rank))

            # 3) Build controlled answer + citations
            answer, citations = build_rag_answer(req.text, retrieved)

            session.add(ResponseLog(ticket_id=t.id, answer=answer, citations_json=str(citations)))
            await session.commit()

        return RespondResponse(
            ticket_id=t.id,
            product_area=cls["product_area"],
            urgency=cls["urgency"],
            answer=answer,
            citations=[Citation(**c) for c in citations],
            classifier_model=cls["model"],
        )
