import requests
from api.geo import geocode_zip

weather_cache = {}


def get_weather(zip_code: str):

    lat, lon = geocode_zip(zip_code)

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current_weather=true"
    )

    r = requests.get(url)
    data = r.json()

    return data["current_weather"]


def get_cached_weather(zip_code: str):

    if zip_code in weather_cache:
        return weather_cache[zip_code]

    weather = get_weather(zip_code)

    weather_cache[zip_code] = weather

    return weather