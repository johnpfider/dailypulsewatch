from fastapi import FastAPI, HTTPException, Form, Query
from fastapi.responses import HTMLResponse
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

@app.post("/subscribe", response_class=HTMLResponse)
def subscribe(
    email: str = Form(...),
    zip: str = Form(...),
    horoscope: str = Form(None)
):

    from api.geo import geocode_zip

    print("Incoming:", email, zip, horoscope)

    # Validate ZIP
    try:
        geocode_zip(zip)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ZIP code")

    with get_conn() as conn:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT email FROM subscribers WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()

            if row:
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
                cur.execute(
                    """
                    INSERT INTO subscribers (email, zip, horoscope, is_active)
                    VALUES (%s, %s, %s, TRUE)
                    """,
                    (email, zip, horoscope)
                )
                message = "subscribed"

        conn.commit()

    try:
        send_welcome_email(email, zip, horoscope)
    except Exception as e:
        print(f"Welcome email error: {e}")

    if message == "reactivated":
        heading = "✅ Welcome back!"
        body_text = "Your DailyPulseWatch subscription has been reactivated."
    else:
        heading = "✅ Success!"
        body_text = "Thank you for signing up for DailyPulseWatch."

    return f"""
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif; background:#F3F4F6; padding:40px 20px;">

        <div style="
            max-width:520px;
            margin:60px auto;
            background:#FFFFFF;
            padding:32px;
            border-radius:18px;
            border:1px solid #E5E7EB;
            box-shadow:0 12px 28px rgba(0,0,0,0.10);
            text-align:center;
        ">

            <h2 style="margin-top:0;">{heading}</h2>

            <p style="font-size:18px;">
                {body_text}
            </p>

            <p style="color:#4B5563; line-height:1.5;">
                Your nurse-focused daily briefing is on its way.
            </p>

            <p style="margin-top:20px; font-size:14px; color:#6B7280;">
                Check your inbox for your welcome email.
            </p>

            <p style="margin-top:28px; font-size:12px; color:#9CA3AF;">
                Built by a nurse, for nurses.
            </p>

        </div>

    </body>
    </html>
    """


# -----------------------
# Unsubscribe (POST API)
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
# Unsubscribe (GET for email link)
# -----------------------

@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_link(email: str = Query(...)):
    with get_conn() as conn:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT email FROM subscribers WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()

            if row:
                cur.execute(
                    "UPDATE subscribers SET is_active = FALSE WHERE email = %s",
                    (email,)
                )
                conn.commit()
                success = True
            else:
                success = False

    if success:
        return f"""
        <html>
        <body style="font-family:Arial,Helvetica,sans-serif; background:#F3F4F6; padding:30px;">
            <div style="
                max-width:600px;
                margin:auto;
                background:#FFFFFF;
                padding:28px;
                border-radius:18px;
                border:1px solid #E5E7EB;
                box-shadow:0 12px 28px rgba(0,0,0,0.12);
            ">
                <h2 style="margin-top:0;">You’ve been unsubscribed</h2>
                <p>
                    <strong>{email}</strong> will no longer receive DailyPulseWatch emails.
                </p>
                <p style="color:#6B7280;">
                    If this was a mistake, you can sign up again anytime.
                </p>
            </div>
        </body>
        </html>
        """
    else:
        return f"""
        <html>
        <body style="font-family:Arial,Helvetica,sans-serif; background:#F3F4F6; padding:30px;">
            <div style="
                max-width:600px;
                margin:auto;
                background:#FFFFFF;
                padding:28px;
                border-radius:18px;
                border:1px solid #E5E7EB;
                box-shadow:0 12px 28px rgba(0,0,0,0.12);
            ">
                <h2 style="margin-top:0;">Email not found</h2>
                <p>
                    We couldn’t find <strong>{email}</strong>.
                </p>
                <p style="color:#6B7280;">
                    It may already be unsubscribed.
                </p>
            </div>
        </body>
        </html>
        """


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

            cur.execute(
                "SELECT COUNT(*) FROM subscribers WHERE is_active = TRUE"
            )
            active = cur.fetchone()[0]

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