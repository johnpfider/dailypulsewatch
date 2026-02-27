from fastapi import FastAPI
from api.db import close_pool, get_conn

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/healthz")
def health_check():
    return {"status": "healthy"}

@app.get("/db-check")
def db_check():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            val = cur.fetchone()[0]
    return {"db": "ok", "value": val}

@app.get("/init-db")
def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    email TEXT PRIMARY KEY,
                    zip TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """)
            conn.commit()
    return {"status": "subscribers table ready"}

@app.on_event("shutdown")
def shutdown_event():
    close_pool()