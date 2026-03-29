from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
from api.db import close_pool, get_conn
from mailer.send_welcome import send_welcome_email


# -----------------------
# Request Models
# -----------------------

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
                    horoscope TEXT,
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
def subscribe(
    email: str = Form(...),
    zip: str = Form(...),
    horoscope: str = Form(None)
):

    from api.geo import geocode_zip

    print("Incoming:", email, zip, horoscope)

    # Validate ZIP
    try:
        lat, lon = geocode_zip(zip)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ZIP code")

    with get_conn() as conn:
        with conn.cursor() as cur:

            # Check if user exists
            cur.execute(
                "SELECT email FROM subscribers WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()

            if row:
                # Reactivate + update info
                cur.execute(
                    """
                    UPDATE subscribers
                    SET is_active = TRUE,
                        zip = %s,
                        horoscope = %s
                    WHERE email = %s
                    """,
                    (zip, horoscope, email)
                )
                message = "reactivated"

            else:
                # Insert new user
                cur.execute(
                    """
                    INSERT INTO subscribers (email, zip, horoscope, is_active)
                    VALUES (%s, %s, %s, TRUE)
                    """,
                    (email, zip, horoscope)
                )
                message = "subscribed"

        conn.commit()

    # Send welcome email
    try:
        send_welcome_email(email, zip, horoscope)
    except Exception as e:
        print(f"Welcome email error: {e}")

    return {"status": message, "email": email}


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
# Get All Subscribers
# -----------------------

@app.get("/subscribers")
def get_all_subscribers():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT email, zip, horoscope FROM subscribers WHERE is_active = TRUE"
            )
            rows = cur.fetchall()

    subscribers = []

    for row in rows:
        subscribers.append({
            "email": row[0],
            "zip": row[1],
            "horoscope": row[2]
        })

    return subscribers


# -----------------------
# Subscriber Count
# -----------------------

@app.get("/subscriber-count")
def subscriber_count():
    with get_conn() as conn:
        with conn.cursor() as cur:

            # Active subscribers
            cur.execute(
                "SELECT COUNT(*) FROM subscribers WHERE is_active = TRUE"
            )
            active = cur.fetchone()[0]

            # Total subscribers ever
            cur.execute(
                "SELECT COUNT(*) FROM subscribers"
            )
            total = cur.fetchone()[0]

    return {
        "active_subscribers": active,
        "total_subscribers": total
    }


# -----------------------
# Shutdown Cleanup
# -----------------------

@app.on_event("shutdown")
def shutdown_event():
    close_pool()