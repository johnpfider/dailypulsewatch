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

            tomorrow_high_f = None
            tomorrow_low_f = None
            tomorrow_precip_mm = None
            tomorrow_freezing = False
            tomorrow_sunrise = None
            tomorrow_sunset = None

            wind_speed = 0.0
            wind_gust = 0.0
            unavailable = True

        return FallbackWeather()