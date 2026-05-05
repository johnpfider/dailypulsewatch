import requests
from collections import defaultdict
import os
import time

from mailer.weather_cache import get_cached_weather
from mailer.content import (
    compute_moon,
    todays_quote,
    fetch_pollen,
    fetch_todays_headlines,
)
from mailer.templates import build_email
from api.geo import geocode_zip
from mailer.horoscope import get_horoscopes


API_URL = "https://dailypulsewatch.onrender.com/internal/subscribers"


# -----------------------
# TEST MODE SETTINGS
# -----------------------
def is_test_mode():
    return os.getenv("TEST_MODE", "false").lower() == "true"


def get_test_emails():
    raw = os.getenv("TEST_EMAILS", "")
    return [
        email.strip().lower()
        for email in raw.split(",")
        if email.strip()
    ]


# -----------------------
# ADMIN API SETTINGS
# -----------------------
def get_admin_headers():
    admin_key = os.getenv("ADMIN_API_KEY")

    if not admin_key:
        print("⚠️ ADMIN_API_KEY is missing from environment variables.")
        return {}

    return {
        "X-Admin-Key": admin_key
    }


# -----------------------
# RESEND EMAIL FUNCTION
# -----------------------
def send_email(to_email, subject, html_body):
    """Send email via Resend API"""

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "from": os.getenv("FROM_EMAIL"),
                "to": [to_email],
                "subject": subject,
                "html": html_body,
            },
            timeout=10,
        )

        if response.status_code == 200:
            print(f"✅ Sent to {to_email}")
        else:
            print(f"❌ Failed to send to {to_email}: {response.text}")

    except Exception as e:
        print(f"❌ Error sending to {to_email}: {e}")


# -----------------------
# Fetch Subscribers
# -----------------------
def get_subscribers(retries=3, delay=2):

    headers = get_admin_headers()

    if not headers:
        print("🚨 Cannot fetch subscribers without ADMIN_API_KEY. Exiting safely.")
        return []

    for attempt in range(1, retries + 1):

        try:
            print(f"📡 Fetching subscribers securely (attempt {attempt})...")

            r = requests.get(
                API_URL,
                headers=headers,
                timeout=5
            )

            if r.status_code == 200:
                print("✅ Subscribers fetched successfully")
                return r.json()

            elif r.status_code == 401:
                print("🚨 Unauthorized. Check ADMIN_API_KEY in Render environment variables.")
                return []

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

    if not subscribers:
        print("⚠️ No subscribers found or API unavailable. Exiting safely.")
        return

    print(f"\nFound {len(subscribers)} subscribers\n")

    # -----------------------
    # TEST MODE FILTER
    # -----------------------
    test_mode = is_test_mode()
    test_emails = get_test_emails()

    if test_mode:
        print("🧪 TEST MODE ACTIVE — sending only to test emails")

        if not test_emails:
            print("⚠️ TEST_MODE is true, but TEST_EMAILS is empty. Exiting safely.")
            return

        subscribers = [
            sub for sub in subscribers
            if sub.get("email", "").lower() in test_emails
        ]

        if not subscribers:
            print("⚠️ No matching test subscribers found. Exiting safely.")
            return

        print(f"🧪 Test recipients: {', '.join(test_emails)}")
        print(f"🧪 Sending test email to {len(subscribers)} matching subscriber(s)\n")

    # -----------------------
    # 📰 FETCH HEADLINES ONCE
    # -----------------------
    headlines = fetch_todays_headlines()

    if headlines:
        print(f"📰 Total headlines ready: {len(headlines)}")
    else:
        print("⚠️ No headlines available today. Email will still send safely.")

    grouped = group_by_zip(subscribers)

    for zip_code, users in grouped.items():

        print(f"\nProcessing ZIP: {zip_code}")

        # -----------------------
        # SHARED DATA PER ZIP
        # -----------------------
        weather = get_cached_weather(zip_code)

        lat, lon = geocode_zip(zip_code)
        pollen = fetch_pollen(lat, lon)

        moon = compute_moon()
        quote = todays_quote()

        # -----------------------
        # COLLECT HOROSCOPES
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
                pollen=pollen,
                headlines=headlines,
            )

            subject = "Your DailyPulseWatch Brief"

            if test_mode:
                subject = "[TEST] Your DailyPulseWatch Brief"

            print("\n-----------------------")
            print(f"TO: {email}")
            print("-----------------------")

            send_email(
                to_email=email,
                subject=subject,
                html_body=html_content
            )


if __name__ == "__main__":
    main()