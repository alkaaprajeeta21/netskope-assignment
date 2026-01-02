# Evaluation Pipeline

This folder provides an offline evaluation pipeline for:
1) **Classifier stability**: repeated runs of `/classify` to measure output consistency.
2) **RAG groundedness**: semantic similarity between the `/respond` answer and retrieved citation excerpts.

## Prerequisites
- Service running locally (docker compose) at `http://localhost:8002`
- Python deps installed locally (or run inside the service container)

## Run

From repo root:

```bash
python evaluation/eval_runner.py
```

Outputs:
- `evaluation/report.json`
- prints a short summary to console
