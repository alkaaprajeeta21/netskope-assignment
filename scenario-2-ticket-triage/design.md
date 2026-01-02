# Design — Ticket Triage Service (Scenario II)

## Goals (from assignment)

- Provide REST endpoints `/classify` and `/respond`
- Ingest docs into a vector DB
- Implement a simple RAG pipeline to help support engineers
- Persist ticket metadata and classification results in PostgreSQL
- Containerize with Docker Compose
- Provide Prometheus metrics:
  - request latency
  - LLM token usage
  - retrieval latency

## High-level architecture

```
Client (support engineer)
   |
   |  POST /classify, POST /respond
   v
FastAPI (triage-service)
   |-- Gemini classifier (semantic classification)
   |-- VectorStore (FAISS + SentenceTransformer embeddings)
   |-- RAG response builder (controlled synthesis + citations)
   |
   +--> PostgreSQL (tickets, retrieval logs, responses)
   |
   +--> /metrics (Prometheus)
```

### Why Gemini for classification

Classification is a semantic interpretation problem (product area + urgency) where:
- rules/keywords are brittle for real-world tickets
- LLMs excel at intent extraction and prioritization signals

**Important design choice:** Gemini is used only for *classification*.
We deliberately avoid using an LLM to generate the final response because support responses are
high-risk for hallucination. Instead, the response is generated deterministically from retrieved
documentation snippets.

This split shows pragmatic AI usage:
- LLM where it adds clear value (semantic labeling)
- deterministic logic where correctness matters (response formatting)

## Data model (PostgreSQL)

### tickets
Stores:
- raw ticket text (and optional external_id)
- Gemini classification output (product_area, urgency, reason, model)
- timestamps

### retrieval_logs
Stores:
- ticket_id
- doc chunk id
- similarity score
- rank

### response_logs
Stores:
- ticket_id
- answer
- citations_json
- timestamps

This supports:
- auditability (why did we classify it like that?)
- debugging (which docs were retrieved?)
- evaluation later (offline replay)

## RAG pipeline (Respond endpoint)

### Step 1 — Classify (Gemini)
`/respond` calls Gemini and stores the classification together with the ticket.

### Step 2 — Retrieve (FAISS)
We embed documentation chunks using `sentence-transformers` and store them in a FAISS index (cosine similarity via dot-product on normalized vectors).
At query time we retrieve top-k chunks using the ticket text.

### Step 3 — Controlled response + citations
Instead of free-form LLM generation, the service formats:
- top ranked doc chunks (with excerpts)
- a short “next steps” checklist

This reduces hallucinations and keeps responses explainable.

### Citations/explainability
We return:
- doc_id (file#chunkN)
- score
- excerpt

Additionally, retrieval logs are persisted.

## Document ingestion

This repo ships sample docs (`data/docs/`) for deterministic local tests.
Index is auto-built on startup if missing, and can be rebuilt via:

```
python -m app.ingest
```

Future work (production):
- crawl docs.netskope.com via sitemap
- chunk by headings and preserve URLs as citation sources
- add re-ranking stage (cross-encoder)

## Metrics

Prometheus endpoints expose:
- `triage_request_latency_seconds{endpoint=...}`
- `triage_retrieval_latency_seconds`
- `triage_gemini_calls_total{status=ok|parse_error}`
- `triage_gemini_retries_total`
- `triage_llm_est_tokens_total{model,kind}` (heuristic estimate)

Token usage is estimated by a simple heuristic (~4 chars/token) to stay vendor-agnostic without requiring proprietary token counters.
In production we would use provider-specific token counts if available.

## Retries
Gemini classification uses `tenacity`:
- up to 3 attempts
- exponential backoff with jitter
- retry on transient errors/timeouts

The classifier also hard-validates output labels; if parsing fails, it returns safe defaults.

## Security considerations

- Gemini API key is provided via env var (in cloud use Secret Manager)
- Inputs are treated as untrusted; response format is constrained
- No doc ingestion from untrusted sources by default
- Rate limiting reduces abuse risk

Future work:
- prompt injection defenses (strip/escape, allow-list labels, system prompts)
- outbound egress restrictions and audit logs

## Deployment notes (future / IaC)
This repo provides Docker + Compose for local evaluation.
For cloud:
- deploy container to Cloud Run / ECS Fargate
- managed Postgres (Cloud SQL / RDS)
- secrets in Secret Manager
- autoscaling based on latency/QPS


## Evaluation pipeline

The repo includes an offline evaluation pipeline under `evaluation/` to support continuous regression testing:

- **Classifier stability:** run `/classify` N times per test case and measure the proportion of identical outputs.
- **RAG groundedness:** compute semantic similarity between the generated answer and concatenated citation excerpts
  using an embedding model (`SentenceTransformer`). Lower similarity indicates higher hallucination risk.

This approach is automated, does not require human labels, and can be run locally or in CI.
