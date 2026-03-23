from mailer.weather_cache import get_cached_weather
from mailer.content import build_email_content, fetch_pollen
from api.geo import geocode_zip


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

        response = ses.send_email(
            Source=os.getenv("FROM_EMAIL"),
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": "Welcome to DailyPulseWatch 🌅"},
                "Body": {"Text": {"Data": body}},
            },
        )

        print(f"✅ Welcome + first brief sent to {to_email}")

    except Exception as e:
        print(f"❌ Welcome email failed for {to_email}: {e}")