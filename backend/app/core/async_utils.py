"""
ATELIX ViralClip AI Pipeline — Async Utilities
Provides safe async execution helpers for sync → async bridging.
"""

import asyncio
from typing import Coroutine, TypeVar

T = TypeVar("T")


def run_async(coro: Coroutine) -> T:
    """
    Safely run an async coroutine from synchronous code.
    Uses nest_asyncio to handle nested event loops.
    """
    try:
        loop = asyncio.get_running_loop()
        import nest_asyncio
        nest_asyncio.apply()
        future = asyncio.ensure_future(coro)
        return loop.run_until_complete(future)
    except RuntimeError:
        return asyncio.run(coro)
