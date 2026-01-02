import os
import json
import logging
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
from .metrics import GEMINI_CALLS, GEMINI_RETRIES, EST_TOKENS

log = logging.getLogger("triage.gemini")

ALLOWED_PRODUCT = {"CASB", "SWG", "ZTNA", "OTHER"}
ALLOWED_URGENCY = {"P0", "P1", "P2", "P3"}

CLASSIFICATION_PROMPT = """You are a support ticket classifier.

Classify the following ticket into:
- product_area: one of [CASB, SWG, ZTNA, OTHER]
- urgency: one of [P0, P1, P2, P3]

Definitions:
P0: Service down, security incident, customer blocked
P1: Major functionality broken, workaround exists
P2: Partial issue, degraded experience
P3: How-to, informational, documentation request

Ticket:
"{ticket_text}"

Respond ONLY in valid JSON:
{{
  "product_area": "...",
  "urgency": "...",
  "reason": "short explanation"
}}
"""

class GeminiError(RuntimeError):
    pass

def _estimate_tokens(text: str) -> int:
    # rough estimate: ~4 chars per token (heuristic)
    return max(1, int(len(text) / 4))

def _init_model():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise GeminiError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return genai.GenerativeModel(
        model_name=model_name,
        generation_config={
            "temperature": 0,
            "response_mime_type": "application/json",
        },
    ), model_name

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.5, max=4.0),
    retry=retry_if_exception_type((GeminiError, TimeoutError, ConnectionError)),
)
def classify_with_gemini(ticket_text: str) -> dict:
    model, model_name = _init_model()
    prompt = CLASSIFICATION_PROMPT.format(ticket_text=ticket_text)

    # metrics: estimated tokens in/out
    EST_TOKENS.labels(model=model_name, kind="input").inc(_estimate_tokens(prompt))

    try:
        resp = model.generate_content(prompt)
    except Exception as e:
        GEMINI_RETRIES.inc()
        raise GeminiError(str(e))

    text = getattr(resp, "text", "") or ""
    EST_TOKENS.labels(model=model_name, kind="output").inc(_estimate_tokens(text))

    try:
        data = json.loads(text)
    except Exception:
        GEMINI_CALLS.labels(status="parse_error").inc()
        return {"product_area": "OTHER", "urgency": "P2", "reason": "fallback: invalid JSON", "model": model_name}

    product = str(data.get("product_area", "OTHER")).upper().strip()
    urgency = str(data.get("urgency", "P2")).upper().strip()
    reason = str(data.get("reason", "")).strip()

    if product not in ALLOWED_PRODUCT:
        product = "OTHER"
    if urgency not in ALLOWED_URGENCY:
        urgency = "P2"

    GEMINI_CALLS.labels(status="ok").inc()
    return {"product_area": product, "urgency": urgency, "reason": reason, "model": model_name}
