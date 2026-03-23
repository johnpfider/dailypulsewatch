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
        # -------------------------------
        # BUILD CONTENT (your existing system)
        # -------------------------------
        weather = get_cached_weather(zip_code)
        lat, lon = geocode_zip(zip_code)
        pollen = fetch_pollen(lat, lon)

        email_content = build_email_content(
            zip_code=zip_code,
            weather=weather,
            pollen=pollen
        )

        # -------------------------------
        # TEXT FALLBACK
        # -------------------------------
        text_body = f"""
Welcome to DailyPulseWatch!

You're officially on the list.

Starting today, you’ll receive a simple daily briefing designed to help you start your day with clarity.

Here’s your first DailyPulseWatch:

----------------------------------------
{email_content}
----------------------------------------

Built by a nurse, for nurses.
"""

        # -------------------------------
        # 🔥 CLEAN HTML (BASED ON YOUR ORIGINAL STYLE)
        # -------------------------------
        html_body = f"""
<html>
<body style="font-family:Arial,Helvetica,sans-serif; background:#F3F4F6; padding:20px;">

  <div style="
    max-width:640px;
    margin:auto;
    background:#FFFFFF;
    padding:24px;
    border-radius:16px;
    border:1px solid #E5E7EB;
    box-shadow:0 10px 24px rgba(0,0,0,0.08);
  ">

    <h2 style="margin-top:0;">Welcome to DailyPulseWatch 👋</h2>

    <p>
      You're officially on the list.
    </p>

    <p>
      Starting today, you’ll receive a simple daily briefing designed to help you start your day with clarity.
    </p>

    <!-- FIRST BRIEF CARD -->
    <div style="
      margin-top:20px;
      padding:18px;
      background:#F9FAFB;
      border:1px solid #E5E7EB;
      border-radius:14px;
    ">

      <h3 style="margin-top:0;">Your First DailyPulseWatch</h3>

      <div style="
        font-family:monospace;
        white-space:pre-wrap;
        line-height:1.5;
      ">
{email_content}
      </div>

    </div>

    <!-- BRAND MESSAGE -->
    <div style="margin-top:24px;">
      <p><strong>Built by a nurse, for nurses.</strong></p>
      <p style="color:#6B7280; font-size:12px;">
        You’re receiving this because you signed up for DailyPulseWatch.
      </p>
    </div>

  </div>

</body>
</html>
"""

        # -------------------------------
        # SEND EMAIL
        # -------------------------------
        ses.send_email(
            Source=os.getenv("FROM_EMAIL"),
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": "Welcome to DailyPulseWatch 🌅"},
                "Body": {
                    "Text": {"Data": text_body},
                    "Html": {"Data": html_body},
                },
            },
        )

        print(f"✅ Welcome + first brief sent to {to_email}")

    except Exception as e:
        print(f"❌ Welcome email failed for {to_email}: {e}")