from pydantic import BaseModel, Field
from typing import List, Optional

class TicketRequest(BaseModel):
    text: str = Field(..., min_length=1)
    external_id: Optional[str] = None

class ClassifyResponse(BaseModel):
    product_area: str
    urgency: str
    reason: str
    model: str

class Citation(BaseModel):
    doc_id: str
    score: float
    excerpt: str

class RespondResponse(BaseModel):
    ticket_id: int
    product_area: str
    urgency: str
    answer: str
    citations: List[Citation]
    classifier_model: str
