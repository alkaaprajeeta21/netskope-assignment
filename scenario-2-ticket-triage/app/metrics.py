from prometheus_client import Counter, Histogram

REQUEST_LATENCY = Histogram("triage_request_latency_seconds", "API request latency", ["endpoint"])
RETRIEVAL_LATENCY = Histogram("triage_retrieval_latency_seconds", "Vector retrieval latency")
GEMINI_CALLS = Counter("triage_gemini_calls_total", "Gemini classification calls", ["status"])
GEMINI_RETRIES = Counter("triage_gemini_retries_total", "Gemini classification retries")
EST_TOKENS = Counter("triage_llm_est_tokens_total", "Estimated LLM tokens used", ["model", "kind"])
