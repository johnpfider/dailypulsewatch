import os
import requests
from datetime import datetime, timezone

from mailer.content import (
    WeatherSignal,
    summarize_day_weather,
    has_fog_in_day,
    has_heavy_rain_in_day,
)


def _format_openweather_time(timestamp: int, timezone_offset: int) -> str:
    local_dt = datetime.fromtimestamp(timestamp + timezone_offset, tz=timezone.utc)
    return local_dt.strftime("%I:%M %p").lstrip("0")


def _openweather_to_internal_code(weather_id: int) -> int:
    if 200 <= weather_id < 300:
        return 95

    if 300 <= weather_id < 400:
        return 53

    if 500 <= weather_id < 600:
        if weather_id in [502, 503, 504, 522, 531]:
            return 65
        if weather_id in [520, 521]:
            return 81
        return 61

    if 600 <= weather_id < 700:
        if weather_id in [602, 622]:
            return 75
        return 73

    if 700 <= weather_id < 800:
        if weather_id in [701, 741]:
            return 45
        return 3

    if weather_id == 800:
        return 0

    if weather_id == 801:
        return 1

    if weather_id == 802:
        return 2

    if weather_id in [803, 804]:
        return 3

    return 3


def _condition_text(day_data: dict) -> str:
    weather_items = day_data.get("weather") or []

    if not weather_items:
        return "Weather conditions unavailable"

    description = weather_items[0].get("description", "")

    if not description:
        return "Weather conditions unavailable"

    return description.title()


def _daily_precip_mm(day_data: dict) -> float:
    rain = day_data.get("rain", 0) or 0
    snow = day_data.get("snow", 0) or 0
    return round(float(rain) + float(snow), 1)


def fetch_weather_openweather(lat: float, lon: float) -> WeatherSignal:
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        raise Exception("OPENWEATHER_API_KEY is missing from environment variables")

    url = "https://api.openweathermap.org/data/3.0/onecall"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "imperial",
        "exclude": "minutely,alerts",
    }

    print("🌦️ Fetching weather from OpenWeather...")

    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 401:
        print("🚨 OpenWeather unauthorized — check OPENWEATHER_API_KEY")
        raise Exception("OpenWeather unauthorized")

    if response.status_code == 429:
        print("🚨 OpenWeather rate limit hit")
        raise Exception("OpenWeather rate limited")

    response.raise_for_status()

    payload = response.json()

    timezone_offset = int(payload.get("timezone_offset", 0))
    daily = payload.get("daily", [])
    hourly = payload.get("hourly", [])

    if not daily:
        raise Exception("OpenWeather response missing daily forecast")

    today = daily[0]
    tomorrow = daily[1] if len(daily) > 1 else None

    hourly_weather_codes = []
    hourly_precip_probs = []

    for hour in hourly[:48]:
        weather_items = hour.get("weather") or []
        weather_id = weather_items[0].get("id") if weather_items else 804

        hourly_weather_codes.append(
            _openweather_to_internal_code(int(weather_id))
        )

        pop = hour.get("pop", 0) or 0
        hourly_precip_probs.append(round(float(pop) * 100))

    high_f = round(float(today["temp"]["max"]), 1)
    low_f = round(float(today["temp"]["min"]), 1)
    precip_mm = _daily_precip_mm(today)

    sunrise = _format_openweather_time(today["sunrise"], timezone_offset)
    sunset = _format_openweather_time(today["sunset"], timezone_offset)

    condition = _condition_text(today)

    summary = summarize_day_weather(
        hourly_weather_codes=hourly_weather_codes,
        hourly_precip_probs=hourly_precip_probs,
        start_index=0,
    )

    foggy = has_fog_in_day(hourly_weather_codes, start_index=0)
    heavy_rain = has_heavy_rain_in_day(hourly_weather_codes, start_index=0)

    tomorrow_high_f = None
    tomorrow_low_f = None
    tomorrow_precip_mm = None
    tomorrow_freezing = False
    tomorrow_sunrise = None
    tomorrow_sunset = None
    tomorrow_condition = None
    tomorrow_summary = None
    tomorrow_foggy = False
    tomorrow_heavy_rain = False

    if tomorrow:
        tomorrow_high_f = round(float(tomorrow["temp"]["max"]), 1)
        tomorrow_low_f = round(float(tomorrow["temp"]["min"]), 1)
        tomorrow_precip_mm = _daily_precip_mm(tomorrow)
        tomorrow_freezing = tomorrow_low_f <= 32

        tomorrow_sunrise = _format_openweather_time(
            tomorrow["sunrise"],
            timezone_offset
        )

        tomorrow_sunset = _format_openweather_time(
            tomorrow["sunset"],
            timezone_offset
        )

        tomorrow_condition = _condition_text(tomorrow)

        tomorrow_summary = summarize_day_weather(
            hourly_weather_codes=hourly_weather_codes,
            hourly_precip_probs=hourly_precip_probs,
            start_index=24,
        )

        tomorrow_foggy = has_fog_in_day(
            hourly_weather_codes,
            start_index=24
        )

        tomorrow_heavy_rain = has_heavy_rain_in_day(
            hourly_weather_codes,
            start_index=24
        )

    wind_speed_values = [
        float(hour.get("wind_speed", 0) or 0)
        for hour in hourly[:24]
    ]

    wind_gust_values = [
        float(hour.get("wind_gust", 0) or 0)
        for hour in hourly[:24]
        if hour.get("wind_gust") is not None
    ]

    wind_speed = max(wind_speed_values or [0.0])
    wind_gust = max(wind_gust_values or [0.0])

    print("✅ OpenWeather fetched successfully")
    print(f"🌬️ WIND: speed={wind_speed}, gust={wind_gust}")
    print(f"🌫️ FOG TODAY: {foggy}")
    print(f"🌧️ HEAVY RAIN TODAY: {heavy_rain}")
    print(f"🌤️ TODAY: {condition}, {summary}, high={high_f}, low={low_f}")
    print(
        f"🌤️ TOMORROW: {tomorrow_condition}, {tomorrow_summary}, "
        f"high={tomorrow_high_f}, low={tomorrow_low_f}"
    )

    return WeatherSignal(
        high_f=high_f,
        low_f=low_f,
        precip_mm=precip_mm,
        freezing=low_f <= 32,
        sunrise=sunrise,
        sunset=sunset,
        condition=condition,
        summary=summary,
        foggy=foggy,
        heavy_rain=heavy_rain,
        tomorrow_high_f=tomorrow_high_f,
        tomorrow_low_f=tomorrow_low_f,
        tomorrow_precip_mm=tomorrow_precip_mm,
        tomorrow_freezing=tomorrow_freezing,
        tomorrow_sunrise=tomorrow_sunrise,
        tomorrow_sunset=tomorrow_sunset,
        tomorrow_condition=tomorrow_condition,
        tomorrow_summary=tomorrow_summary,
        tomorrow_foggy=tomorrow_foggy,
        tomorrow_heavy_rain=tomorrow_heavy_rain,
        wind_speed=wind_speed,
        wind_gust=wind_gust,
    )