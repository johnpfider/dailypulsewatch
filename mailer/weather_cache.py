from api.geo import geocode_zip
from mailer.content import fetch_weather

weather_cache = {}


def get_cached_weather(zip_code: str):

    if zip_code in weather_cache:
        return weather_cache[zip_code]

    try:
        lat, lon = geocode_zip(zip_code)
        weather = fetch_weather(lat, lon)

        weather_cache[zip_code] = weather
        return weather

    except Exception as e:
        print(f"⚠️ Weather failed for ZIP {zip_code}: {e}")

        # fallback weather
        class FallbackWeather:
            high_f = None
            low_f = None
            precip_mm = 0
            freezing = False
            sunrise = None
            sunset = None
            unavailable = True 

        return FallbackWeather()