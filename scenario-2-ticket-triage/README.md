# Scenario II — Ticket Triage Service (Full)

Implements Scenario II from the Practical Test: a service that:
1) Classifies tickets by product area and urgency (Gemini)
2) Responds using a simple RAG pipeline over documentation (vector search + citations)
3) Stores ticket metadata and retrieval logs in PostgreSQL
4) Exposes Prometheus metrics for request latency, token usage (estimated), and retrieval latency
5) Runs locally via Docker Compose

## Quickstart (Local)

### 1) Set Gemini API key
Export your key in your shell:

```bash
export GEMINI_API_KEY="YOUR_KEY"
```

(Optional) choose model:

```bash
export GEMINI_MODEL="gemini-1.5-flash"
```

### 2) Start the stack

```bash
docker compose up --build
```

Service: http://localhost:8002  
Docs: http://localhost:8002/docs  
Metrics: http://localhost:8002/metrics  

### 3) Test `/classify`

```bash
curl -X POST http://localhost:8002/classify \
  -H "content-type: application/json" \
  -d '{"text":"Users cannot browse web via proxy. SSL inspection failing. urgent."}'
```

### 4) Test `/respond`

```bash
curl -X POST http://localhost:8002/respond \
  -H "content-type: application/json" \
  -d '{"text":"ZTNA app access denied for a user group after posture check update. Need steps."}'
```

## Document ingestion

By default, the container ships with a few sample docs in `data/docs/` and will auto-build a FAISS index
on startup if it doesn't exist.

To rebuild the index manually (inside container or locally):
```bash
python -m app.ingest
```

## Notes

- Gemini is used ONLY for classification (semantic task). RAG response generation is intentionally controlled
  to reduce hallucinations and keep behavior deterministic.


## Evaluation

An offline evaluation pipeline is included in `evaluation/` to measure:
- Gemini classifier stability (repeatability)
- RAG groundedness (answer vs retrieved context similarity)

Run (after starting the stack):
```bash
python evaluation/eval_runner.py
```

This writes `evaluation/report.json`.
