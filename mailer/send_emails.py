import requests
from collections import defaultdict
import boto3
import os
import time  # ✅ NEW

from mailer.weather_cache import get_cached_weather
from mailer.content import compute_moon, todays_quote
from mailer.templates import build_email
from api.geo import geocode_zip
from mailer.horoscope import get_horoscopes
from mailer.content import fetch_pollen

API_URL = "https://dailypulsewatch.onrender.com/subscribers"

# -----------------------
# AWS SES Setup
# -----------------------
ses = boto3.client(
    "ses",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


def send_email(to_email, subject, html_body):
    """Send HTML email via Amazon SES"""
    try:
        response = ses.send_email(
            Source=os.getenv("FROM_EMAIL"),
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Html": {"Data": html_body}
                },
            },
        )
        print(f"✅ Sent to {to_email}")
        return response

    except Exception as e:
        print(f"❌ Failed to send to {to_email}: {e}")


# -----------------------
# Fetch Subscribers (RETRY VERSION)
# -----------------------
def get_subscribers(retries=3, delay=2):

    for attempt in range(1, retries + 1):

        try:
            print(f"📡 Fetching subscribers (attempt {attempt})...")

            r = requests.get(API_URL, timeout=5)

            if r.status_code == 200:
                print("✅ Subscribers fetched successfully")
                return r.json()

            else:
                print(f"⚠️ API error: {r.status_code} - {r.text}")

        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")

        if attempt < retries:
            print(f"⏳ Retrying in {delay} seconds...")
            time.sleep(delay)

    print("🚨 All retries failed. Returning empty subscriber list.")
    return []


# -----------------------
# Group by ZIP
# -----------------------
def group_by_zip(subscribers):
    grouped = defaultdict(list)

    for sub in subscribers:
        grouped[sub["zip"]].append(sub)

    return grouped


# -----------------------
# Main Runner
# -----------------------
def main():

    subscribers = get_subscribers()

    # ✅ SAFETY EXIT (prevents crash)
    if not subscribers:
        print("⚠️ No subscribers found or API unavailable. Exiting safely.")
        return

    print(f"\nFound {len(subscribers)} subscribers\n")

    grouped = group_by_zip(subscribers)

    for zip_code, users in grouped.items():

        print(f"\nProcessing ZIP: {zip_code}")

        # -----------------------
        # SHARED DATA (per ZIP)
        # -----------------------
        weather = get_cached_weather(zip_code)

        lat, lon = geocode_zip(zip_code)
        pollen = fetch_pollen(lat, lon)
        moon = compute_moon()
        quote = todays_quote()

        # -----------------------
        # 🧠 COLLECT HOROSCOPES (BATCH)
        # -----------------------
        signs = set(
            user["horoscope"]
            for user in users
            if user.get("horoscope")
        )

        horoscope_map = get_horoscopes(signs) if signs else {}

        # -----------------------
        # SEND EMAILS
        # -----------------------
        for user in users:

            email = user["email"]

            user_horoscopes = {}

            if user.get("horoscope"):
                sign = user["horoscope"].lower()
                user_horoscopes[sign] = horoscope_map.get(sign, "")

            html_content = build_email(
                moon=moon,
                weather=weather,
                horoscopes=user_horoscopes,
                quote=quote,
                user_email=email,
                pollen=pollen
            )

            print("\n-----------------------")
            print(f"TO: {email}")
            print("-----------------------")

            send_email(
                to_email=email,
                subject="Your DailyPulseWatch Brief",
                html_body=html_content
            )


if __name__ == "__main__":
    main()