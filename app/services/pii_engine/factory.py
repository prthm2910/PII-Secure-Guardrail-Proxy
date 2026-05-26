"""
Factory module for creating and caching PII Engine singleton.

Provides lazy initialization of the global PIIEngine instance.
"""

from app.services.pii_engine.engine import PIIEngine

# Global cached instance
_pii_engine_instance = None


def get_pii_engine() -> PIIEngine:
    """
    Get or create the global PIIEngine singleton.
    
    Returns:
        The singleton PIIEngine instance.
    """
    global _pii_engine_instance
    if _pii_engine_instance is None:
        _pii_engine_instance = PIIEngine()
    return _pii_engine_instance


# Create the singleton instance at module load time
pii_engine = get_pii_engine()