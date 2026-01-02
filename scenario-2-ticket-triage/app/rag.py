from typing import List, Dict
from .vector_store import VectorStore, DocChunk

def build_rag_answer(ticket_text: str, retrieved: List[tuple[DocChunk, float]]) -> tuple[str, List[Dict]]:
    # Lightweight, controlled answer:
    # - We do NOT let the model hallucinate.
    # - We produce a structured, support-agent-friendly response.
    citations = []
    for c, score in retrieved:
        excerpt = c.text[:260].replace("\n", " ").strip()
        citations.append({"doc_id": c.doc_id, "score": score, "excerpt": excerpt})

    # Simple synthesis:
    if not citations:
        answer = (
            "I couldn't find a relevant article in the indexed docs for this ticket. "
            "Try refining the query or ingest more documentation. "
            "Meanwhile, gather logs, reproduction steps, and confirm impacted users."
        )
        return answer, citations

    answer_lines = [
        "Suggested approach based on documentation snippets:",
        "",
    ]
    # Provide top recommendations as bullets
    for i, cit in enumerate(citations[:3], start=1):
        answer_lines.append(f"{i}. Refer to **{cit['doc_id']}** (score={cit['score']:.3f}).")
        answer_lines.append(f"   Excerpt: {cit['excerpt']}")

    answer_lines.append("")
    answer_lines.append("Next steps:")
    answer_lines.append("- Confirm scope/impact and gather exact error messages.")
    answer_lines.append("- Validate configuration and policy order relevant to the product area.")
    answer_lines.append("- If still blocked, escalate with logs and connector/proxy status details.")

    return "\n".join(answer_lines), citations
