from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.db.session import SessionLocal
import logging

class AuditService:
    def log_request(
        self, 
        request_id: str, 
        entity_summary: dict, 
        masked_entities: dict,
        latency_ms: float, 
        status: str = "SUCCESS", 
        client_name: str = "default-client"
    ):
        """Log request metadata to PostgreSQL."""
        db = SessionLocal()
        try:
            db_log = AuditLog(
                request_id=request_id,
                entity_summary=entity_summary,
                masked_entities=masked_entities,
                latency_ms=latency_ms,
                status=status,
                client_name=client_name
            )
            db.add(db_log)
            db.commit()
        except Exception as e:
            # In production, we'd log this to a file or monitoring tool
            logging.error(f"Failed to write audit log: {e}")
            db.rollback()
        finally:
            db.close()

audit_service = AuditService()
