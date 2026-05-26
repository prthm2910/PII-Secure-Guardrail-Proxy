from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.session import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    client_name = Column(String, default="default-client")
    latency_ms = Column(Float)
    status = Column(String)
    # JSONB for entity summary: {"PAN": 1, "UPI": 1}
    entity_summary = Column(JSONB)
    # JSONB for masked entities: {"[IN_PAN_1]": "ABCDE****F"}
    masked_entities = Column(JSONB)
    # JSONB for the final messages sent to LLM
    sanitized_messages = Column(JSONB)
    # JSONB for chronological technical events
    technical_timeline = Column(JSONB)
