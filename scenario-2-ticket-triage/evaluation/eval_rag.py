import requests
from sentence_transformers import SentenceTransformer, util

RESPOND_URL = "http://localhost:8002/respond"
_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def groundedness(answer: str, citations: list[dict]) -> float:
    """Semantic similarity between answer and concatenated citation excerpts."""
    context = " ".join([c.get("excerpt", "") for c in citations]).strip()
    if not context:
        return 0.0
    emb_a = _MODEL.encode(answer, convert_to_tensor=True, normalize_embeddings=True)
    emb_c = _MODEL.encode(context, convert_to_tensor=True, normalize_embeddings=True)
    return float(util.cos_sim(emb_a, emb_c).cpu().numpy()[0][0])

def evaluate_rag(cases, timeout=60):
    results = []
    for case in cases:
        r = requests.post(RESPOND_URL, json={"text": case["text"]}, timeout=timeout)
        r.raise_for_status()
        j = r.json()

        g = groundedness(j.get("answer",""), j.get("citations", []))

        results.append({
            "id": case["id"],
            "product_area": j.get("product_area"),
            "urgency": j.get("urgency"),
            "groundedness": g,
            "num_citations": len(j.get("citations", [])),
        })
    return results
