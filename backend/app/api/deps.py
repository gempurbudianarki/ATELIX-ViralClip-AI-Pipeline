"""
ATELIX ViralClip AI Pipeline — API Dependencies
Shared FastAPI dependencies (DB session, settings).
"""

from app.core.database import get_db
from app.core.config import get_settings

__all__ = ["get_db", "get_settings"]
