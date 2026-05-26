from fastapi import APIRouter, HTTPException
from app.api.v1.endpoints import chat
from app.db.session import SessionLocal
from app.models.audit import AuditLog
from sqlalchemy import func, text
from typing import Dict, List

from app.services.redis_service import redis_service

api_router = APIRouter()

@api_router.get("/proxy/v1/cache/{request_id}")
async def get_request_cache(request_id: str):
    """Retrieve raw tokens from Redis for a specific request."""
    tokens = redis_service.get_tokens(request_id)
    if not tokens:
        raise HTTPException(status_code=404, detail="Tokens not found in cache or expired")
    return tokens
api_router.include_router(chat.router, prefix="/proxy/v1", tags=["proxy"])

@api_router.get("/proxy/v1/stats")
async def get_stats():
    """Retrieve aggregated audit metrics for the demo dashboard."""
    db = SessionLocal()
    try:
        # 1. Total Requests & Avg Latency
        stats = db.query(
            func.count(AuditLog.id).label("total_requests"),
            func.avg(AuditLog.latency_ms).label("avg_latency")
        ).first()
        
        total_requests = stats.total_requests or 0
        avg_latency = stats.avg_latency or 0
        
        # 2. Global PII Counts (Aggregation of JSONB keys)
        global_pii_counts = {}
        if total_requests > 0:
            global_counts_query = text("""
                SELECT key, SUM(value::int) as total
                FROM audit_logs, jsonb_each_text(entity_summary)
                WHERE entity_summary IS NOT NULL
                GROUP BY key
                ORDER BY total DESC
            """)
            result = db.execute(global_counts_query).all()
            global_pii_counts = {row[0]: int(row[1]) for row in result}
        
        # 3. Recent Activity (Last 20 requests)
        recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(20).all()
        recent_activity = []
        for log in recent_logs:
            entity_count = sum(log.entity_summary.values()) if log.entity_summary else 0
            recent_activity.append({
                "request_id": log.request_id,
                "timestamp": log.timestamp.isoformat(),
                "entity_count": entity_count,
                "status": log.status
            })
            
        return {
            "total_requests": total_requests,
            "avg_latency_ms": round(float(avg_latency), 2),
            "global_pii_counts": global_pii_counts,
            "recent_activity": recent_activity
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error while retrieving stats")
    finally:
        db.close()

@api_router.get("/proxy/v1/request/{request_id}")
async def get_request_details(request_id: str):
    """Retrieve details for a specific request by ID."""
    db = SessionLocal()
    try:
        log = db.query(AuditLog).filter(AuditLog.request_id == request_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return {
            "request_id": log.request_id,
            "timestamp": log.timestamp.isoformat(),
            "status": log.status,
            "entity_summary": log.entity_summary,
            "masked_entities": log.masked_entities,
            "sanitized_messages": log.sanitized_messages,
            "technical_timeline": log.technical_timeline
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error while retrieving request details")
    finally:
        db.close()
