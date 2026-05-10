import redis
import json
from typing import Optional, Dict
from app.core.config import settings

class RedisService:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            ssl=settings.REDIS_SSL,
            decode_responses=True
        )
        self.ttl = 3600 # 1 hour self-destruct for token persistence

    def store_tokens(self, request_id: str, token_map: Dict[str, str]):
        """Store PII mapping in Redis with TTL."""
        if not token_map:
            return
        key = f"req:{request_id}:tokens"
        self.client.set(key, json.dumps(token_map), ex=self.ttl)

    def get_tokens(self, request_id: str) -> Optional[Dict[str, str]]:
        """Retrieve PII mapping from Redis."""
        key = f"req:{request_id}:tokens"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def delete_tokens(self, request_id: str):
        """Manually delete tokens if needed."""
        key = f"req:{request_id}:tokens"
        self.client.delete(key)

redis_service = RedisService()
