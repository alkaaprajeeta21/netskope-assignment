from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String, nullable=True, index=True)
    text = Column(Text, nullable=False)

    product_area = Column(String, nullable=True, index=True)
    urgency = Column(String, nullable=True, index=True)
    classification_reason = Column(Text, nullable=True)
    classifier_model = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    retrievals = relationship("RetrievalLog", back_populates="ticket", cascade="all, delete-orphan")
    responses = relationship("ResponseLog", back_populates="ticket", cascade="all, delete-orphan")

class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), index=True)
    doc_id = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    ticket = relationship("Ticket", back_populates="retrievals")

class ResponseLog(Base):
    __tablename__ = "response_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), index=True)
    answer = Column(Text, nullable=False)
    citations_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    ticket = relationship("Ticket", back_populates="responses")
