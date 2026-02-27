from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from api.db import close_pool, get_conn


# -----------------------
# Request Models
# -----------------------

class SubscribeRequest(BaseModel):
    email: str
    zip: str


class UnsubscribeRequest(BaseModel):
    email: str


# -----------------------
# App Setup
# -----------------------

app = FastAPI()


# -----------------------
# Basic Health Routes
# -----------------------

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


# -----------------------
# Initialize DB
# -----------------------

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


# -----------------------
# Subscribe
# -----------------------

@app.post("/subscribe")
def subscribe(req: SubscribeRequest):

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Check if email exists
            cur.execute(
                "SELECT email, is_active FROM subscribers WHERE email = %s",
                (req.email,)
            )
            row = cur.fetchone()

            if row:
                cur.execute(
                    "UPDATE subscribers SET is_active = TRUE WHERE email = %s",
                    (req.email,)
                )
                message = "reactivated"
            else:
                cur.execute(
                    "INSERT INTO subscribers (email, zip, is_active) VALUES (%s, %s, TRUE)",
                    (req.email, req.zip)
                )
                message = "subscribed"

        conn.commit()

    return {"status": message, "email": req.email}

# -----------------------
# Unsubscribe
# -----------------------

@app.post("/unsubscribe")
def unsubscribe(req: UnsubscribeRequest):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE subscribers SET is_active = FALSE WHERE email = %s",
                (req.email,)
            )
        conn.commit()

    return {"status": "unsubscribed", "email": req.email}


# -----------------------
# Shutdown Cleanup
# -----------------------

@app.on_event("shutdown")
def shutdown_event():
    close_pool()