from mailer.content import (
    compute_moon,
    fetch_weather,
    fetch_horoscope,
    todays_quote,
)
from mailer.templates import build_email


def run_test():
    # Fake subscriber data (Harrisburg, PA coordinates)
    lat = 40.2732
    lon = -76.8867
    zodiac = "leo"

    moon = compute_moon()
    weather = fetch_weather(lat, lon)
    quote = todays_quote()

    horoscope_text = fetch_horoscope(zodiac)

    html = build_email(
        moon=moon,
        weather=weather,
        horoscopes={"Leo": horoscope_text},
        quote=quote,
    )

    print("\nEMAIL GENERATED SUCCESSFULLY\n")
    print(html)  # only show first 500 characters


if __name__ == "__main__":
    run_test()