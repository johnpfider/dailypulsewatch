from mailer.weather_cache import get_cached_weather
from mailer.content import build_email_content, fetch_pollen
from api.geo import geocode_zip
import boto3
import os

ses = boto3.client(
    "ses",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

def send_welcome_email(to_email: str, zip_code: str):

    try:
        # Build actual DailyPulseWatch content
        weather = get_cached_weather(zip_code)
        lat, lon = geocode_zip(zip_code)
        pollen = fetch_pollen(lat, lon)

        email_content = build_email_content(
            zip_code=zip_code,
            weather=weather,
            pollen=pollen
        )

        # ---------- TEXT VERSION (fallback) ----------
        body = f"""
Welcome to DailyPulseWatch!

You're officially on the list.

Starting today, you’ll receive a simple daily briefing designed to help you start your day with clarity.

Here’s your first DailyPulseWatch:

----------------------------------------
{email_content}
----------------------------------------

We’ll be delivering this to you each day.

Built by a nurse, for nurses.

Stay sharp,
DailyPulseWatch
"""

        # ---------- HTML VERSION (pretty email) ----------
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; background-color:#f4f6f8; padding:20px;">
    <div style="max-width:600px; margin:auto; background:white; padding:20px; border-radius:10px;">

        <h2 style="color:#2c3e50;">Welcome to DailyPulseWatch 👋</h2>

        <p>You're officially on the list.</p>

        <p>
        Starting today, you’ll receive a simple daily briefing designed to help you start your day with clarity.
        </p>

        <hr>

        <h3 style="color:#2c3e50;">Your First DailyPulseWatch</h3>

        <div style="background:#f9f9f9; padding:12px; border-radius:6px; font-family: monospace; white-space: pre-wrap;">
{email_content}
        </div>

        <hr>

        <p><strong>Built by a nurse, for nurses.</strong></p>

        <p style="color:gray; font-size:12px;">
        You’re receiving this because you signed up for DailyPulseWatch.
        </p>

    </div>
</body>
</html>
"""

        # ---------- SEND EMAIL ----------
        response = ses.send_email(
            Source=os.getenv("FROM_EMAIL"),
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": "Welcome to DailyPulseWatch 🌅"},
                "Body": {
                    "Text": {"Data": body},   # fallback
                    "Html": {"Data": html_body},  # pretty version
                },
            },
        )

        print(f"✅ Welcome + first brief sent to {to_email}")

    except Exception as e:
        print(f"❌ Welcome email failed for {to_email}: {e}")