import requests
from collections import defaultdict

from mailer.weather_cache import get_cached_weather
from mailer.content import build_email_content, fetch_pollen
from api.geo import geocode_zip

API_URL = "https://dailypulsewatch.onrender.com/subscribers"


def get_subscribers():
    """Fetch active subscribers from the API."""
    r = requests.get(API_URL)
    r.raise_for_status()
    return r.json()


def group_by_zip(subscribers):
    """Group subscribers by ZIP code."""
    grouped = defaultdict(list)

    for sub in subscribers:
        grouped[sub["zip"]].append(sub)

    return grouped


def main():

    subscribers = get_subscribers()

    print(f"\nFound {len(subscribers)} subscribers\n")

    grouped = group_by_zip(subscribers)

    for zip_code, users in grouped.items():

        print(f"\nProcessing ZIP: {zip_code}")

        weather = get_cached_weather(zip_code)

        # Fetch pollen once per ZIP
        lat, lon = geocode_zip(zip_code)
        pollen = fetch_pollen(lat, lon)

        for user in users:

            email = user["email"]

            email_content = build_email_content(
                zip_code=zip_code,
                weather=weather,
                pollen=pollen
            )

            print("\n-----------------------")
            print(f"TO: {email}")
            print(email_content)
            print("-----------------------\n")


if __name__ == "__main__":
    main()