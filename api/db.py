import os
from contextlib import contextmanager
from typing import Iterator, Optional

from psycopg_pool import ConnectionPool
from psycopg import Connection


# Render provides this as an env var (you already added it)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Failing fast makes it obvious what's wrong during deploy
    raise RuntimeError("DATABASE_URL env var is not set")

# IMPORTANT:
# - max_size controls your maximum concurrent open DB connections from THIS service.
# - Keep this low on Starter plans to avoid exhausting Postgres connections.
_pool: Optional[ConnectionPool] = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=5,         # good starter default; can bump later
    timeout=30,         # seconds to wait for a connection
    open=True,          # open pool immediately at import time
)


@contextmanager
def get_conn() -> Iterator[Connection]:
    """
    Usage:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    """
    assert _pool is not None
    with _pool.connection() as conn:
        yield conn


def close_pool() -> None:
    """Called on app shutdown to close all pooled connections cleanly."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None