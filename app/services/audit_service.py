from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.db.session import SessionLocal
from app.core.logging import logger

class AuditService:
    def log_request(
        self, 
        request_id: str, 
        entity_summary: dict, 
        masked_entities: dict,
        latency_ms: float,
        sanitized_messages: list = None,
        technical_timeline: list = None,
        status: str = "SUCCESS", 
        client_name: str = "default-client"
    ):
        """Log request metadata to PostgreSQL."""
        db = SessionLocal()
        try:
            logger.debug(f"Req: {request_id} | Writing audit log to Postgres...")
            db_log = AuditLog(
                request_id=request_id,
                entity_summary=entity_summary,
                masked_entities=masked_entities,
                sanitized_messages=sanitized_messages,
                technical_timeline=technical_timeline,
                latency_ms=latency_ms,
                status=status,
                client_name=client_name
            )
            db.add(db_log)
            db.commit()
            logger.info(f"Req: {request_id} | Audit log committed successfully.")
        except Exception as e:
            logger.error(f"Req: {request_id} | Failed to write audit log: {e}")
            db.rollback()
        finally:
            db.close()

audit_service = AuditService()
