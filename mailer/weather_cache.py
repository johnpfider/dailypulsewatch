from api.geo import geocode_zip
from mailer.content import fetch_weather

weather_cache = {}


def get_cached_weather(zip_code: str):

    if zip_code in weather_cache:
        return weather_cache[zip_code]

    lat, lon = geocode_zip(zip_code)

    weather = fetch_weather(lat, lon)

    weather_cache[zip_code] = weather

    return weather