from mailer.weather_cache import get_cached_weather
from mailer.content import build_email_content, fetch_pollen
from api.geo import geocode_zip
import boto3
import os


# =========================
# AWS SES CLIENT
# =========================
ses = boto3.client(
    "ses",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


# =========================
# SECTION PARSER
# =========================
def format_sections(email_content: str):
    sections = {}
    current_section = None

    for line in email_content.splitlines():
        line = line.strip()

        if not line:
            continue

        # Detect section headers
        if line in ["Weather", "Sun", "Commute Weather Watch", "Moon", "Quote"]:
            current_section = line
            sections[current_section] = []
            continue

        if line.startswith("---"):
            continue

        if current_section:
            sections[current_section].append(line)

    return sections


# =========================
# SEND WELCOME EMAIL
# =========================
def send_welcome_email(to_email: str, zip_code: str):

    try:
        # -------------------------------
        # BUILD DATA
        # -------------------------------
        weather = get_cached_weather(zip_code)
        lat, lon = geocode_zip(zip_code)
        pollen = fetch_pollen(lat, lon)

        email_content = build_email_content(
            zip_code=zip_code,
            weather=weather,
            pollen=pollen
        )

        sections = format_sections(email_content)

        # -------------------------------
        # TEXT VERSION (fallback)
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
        # HTML VERSION (🔥 CLEAN UI)
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

<p>You're officially on the list.</p>

<p>
Starting today, you’ll receive a simple daily briefing designed to help you start your day with clarity.
</p>

<h3 style="margin-top:24px;">Your First DailyPulseWatch</h3>

<!-- WEATHER -->
<h4>Weather</h4>
<p>{"<br>".join(sections.get("Weather", []))}</p>

<!-- SUN -->
<h4>Sun</h4>
<p>{"<br>".join(sections.get("Sun", []))}</p>

<!-- COMMUTE -->
<div style="
  margin-top:16px;
  padding:18px;
  background:#F9FAFB;
  border:1px solid #E5E7EB;
  border-radius:14px;
">
  <h4 style="margin-top:0;">Commute Weather Watch</h4>
  <p>{"<br>".join(sections.get("Commute Weather Watch", []))}</p>
</div>

<!-- MOON -->
<h4 style="margin-top:20px;">Moon</h4>
<p>{"<br>".join(sections.get("Moon", []))}</p>

<!-- QUOTE -->
<h4 style="margin-top:20px;">Quote</h4>
<p>{"<br>".join(sections.get("Quote", []))}</p>

<!-- FOOTER -->
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