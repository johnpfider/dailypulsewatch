import os
from psycopg_pool import ConnectionPool

# Render provides this in your Environment Variables
DATABASE_URL = os.environ["DATABASE_URL"]

# Small pool: good for Starter plan + low traffic
pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=10,
    timeout=30,
)

def get_conn():
    """
    Usage:
        with get_conn() as conn:
            ...
    This grabs a connection from the pool and returns it after the block.
    """
    return pool.connection()

def close_pool():
    pool.close()