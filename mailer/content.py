# ============================================================
# DailyPulseWatch — Core Content Logic
# ============================================================

import json
import requests
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional
import time

from astral.moon import phase as moon_phase


# ============================================================
# FILES
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
QUOTES_FILE = BASE_DIR / "data" / "quotes.json"

TODAY = date.today().isoformat()


# ============================================================
# DATA MODELS
# ============================================================

@dataclass(slots=True)
class MoonSignal:
    phase: str
    meaning: str


@dataclass(slots=True)
class WeatherSignal:
    high_f: float
    low_f: float
    precip_mm: float
    freezing: bool
    sunrise: str
    sunset: str


@dataclass(slots=True)
class PollenSignal:
    alder: Optional[float]
    birch: Optional[float]
    grass: Optional[float]
    ragweed: Optional[float]


# ============================================================
# MOON LOGIC
# ============================================================

def compute_moon() -> MoonSignal:

    age = float(moon_phase(date.today()))

    if age < 1 or age > 28.5:
        return MoonSignal("New Moon", "The moon is not visible in the sky.")

    if 6 <= age <= 8:
        return MoonSignal("First Quarter", "Half of the moon is visible and getting brighter.")

    if 13 <= age <= 16:
        return MoonSignal("Full Moon", "The entire moon is fully visible and bright.")

    if 20 <= age <= 22:
        return MoonSignal("Last Quarter", "Half of the moon is visible and getting darker.")

    if age < 14.5:
        return MoonSignal("Waxing", "The moon is getting brighter each night.")

    return MoonSignal("Waning", "The moon is getting darker each night.")


# ============================================================
# WEATHER LOGIC
# ============================================================

def fetch_weather(lat: float, lon: float) -> WeatherSignal:

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset",
        "forecast_days": 1,
        "timezone": "auto",
    }

    retries = 3
    delay = 2

    for attempt in range(1, retries + 1):

        try:
            print(f"🌦️ Fetching weather (attempt {attempt})...")

            r = requests.get(url, params=params, timeout=5)
            r.raise_for_status()

            d = r.json()["daily"]

            # 🌅 FORMAT TIME
            sunrise_raw = d["sunrise"][0]
            sunset_raw = d["sunset"][0]

            sunrise_dt = datetime.fromisoformat(sunrise_raw)
            sunset_dt = datetime.fromisoformat(sunset_raw)

            sunrise = sunrise_dt.strftime("%I:%M %p").lstrip("0")
            sunset = sunset_dt.strftime("%I:%M %p").lstrip("0")

            # 🌡️ TEMP + PRECIP
            high_c = d["temperature_2m_max"][0]
            low_c = d["temperature_2m_min"][0]
            precip = d["precipitation_sum"][0]

            high_f = round(high_c * 9/5 + 32, 1)
            low_f = round(low_c * 9/5 + 32, 1)

            print("✅ Weather fetched successfully")

            return WeatherSignal(
                high_f=high_f,
                low_f=low_f,
                precip_mm=round(precip, 1),
                freezing=low_f <= 32,
                sunrise=sunrise,
                sunset=sunset
            )

        except Exception as e:
            print(f"❌ Weather attempt {attempt} failed: {e}")

            if attempt < retries:
                print(f"⏳ Retrying weather in {delay} seconds...")
                time.sleep(delay)

    # 🚨 FINAL FAILURE
    print("🚨 All weather retries failed — using fallback")

    raise Exception("Weather API failed after retries")

# ============================================================
# POLLEN LOGIC
# ============================================================

def _daily_peak(values) -> Optional[float]:

    if not values:
        return None

    clean = [v for v in values if v is not None]

    if not clean:
        return None

    return max(clean)


def fetch_pollen(lat: float, lon: float) -> PollenSignal:

    url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "alder_pollen,birch_pollen,grass_pollen,ragweed_pollen",
        "forecast_days": 1,
        "timezone": "auto"
    }

    retries = 3
    delay = 2

    for attempt in range(1, retries + 1):
        try:
            print(f"🌿 Fetching pollen (attempt {attempt})...")

            r = requests.get(url, params=params, timeout=5)
            r.raise_for_status()

            data = r.json().get("hourly", {})

            print("✅ Pollen fetched successfully")

            return PollenSignal(
                alder=_daily_peak(data.get("alder_pollen")),
                birch=_daily_peak(data.get("birch_pollen")),
                grass=_daily_peak(data.get("grass_pollen")),
                ragweed=_daily_peak(data.get("ragweed_pollen")),
            )

        except Exception as e:
            print(f"❌ Pollen attempt {attempt} failed: {e}")

            if attempt < retries:
                print(f"⏳ Retrying pollen in {delay} seconds...")
                time.sleep(delay)

    # 🚨 FINAL FAILURE → graceful fallback
    print("🚨 All pollen retries failed — using fallback")

    return PollenSignal(
        alder=None,
        birch=None,
        grass=None,
        ragweed=None
    )


def pollen_level(value: Optional[float]) -> str:

    if value is None:
        return "Unavailable"

    if value < 1:
        return "Low"
    elif value < 5:
        return "Moderate"
    elif value < 20:
        return "High"
    else:
        return "Very High"

# -----------------------
# 🌿 Allergy Risk Score
# -----------------------
def allergy_risk(pollen):
    try:
        values = [
            getattr(pollen, "alder", 0),
            getattr(pollen, "birch", 0),
            getattr(pollen, "grass", 0),
            getattr(pollen, "ragweed", 0),
        ]

        max_val = max(values)

        if max_val >= 7:
            return "🔴 High"
        elif max_val >= 3:
            return "🟡 Moderate"
        else:
            return "🟢 Low"

    except Exception:
        return "Unavailable"
    
# ============================================================
# COMMUTE / BLACK ICE LOGIC
# ============================================================

def compute_commute(weather: WeatherSignal):

    if weather.freezing and weather.precip_mm == 0:

        return {
            "commute_line": "Cold temperatures are present, but dry conditions reduce the risk of slick roads.",
            "ice_risk": "Low",
            "ice_text": "Freezing temperatures are present, but without precipitation, black ice is unlikely.",
            "show_details": True
        }

    elif weather.freezing and weather.precip_mm > 0:

        return {
            "commute_line": "Cold temperatures combined with precipitation may make the commute more hazardous.",
            "ice_risk": "Elevated",
            "ice_text": "Freezing temperatures and moisture mean black ice could form on untreated surfaces.",
            "show_details": True
        }

    else:

        return {
            "commute_line": "No major weather-related commute concerns.",
            "ice_risk": "None",
            "ice_text": "Temperatures are above freezing.",
            "show_details": False
        }


# ============================================================
# QUOTES
# ============================================================

def todays_quote():

    if not QUOTES_FILE.exists():
        return {"text": "", "author": ""}

    quotes = json.loads(QUOTES_FILE.read_text(encoding="utf-8") or "[]")

    if not quotes:
        return {"text": "", "author": ""}

    idx = date.today().toordinal() % len(quotes)

    return quotes[idx]


# ============================================================
# EMAIL CONTENT BUILDER (TEXT VERSION)
# ============================================================

def build_email_content(zip_code: str, weather: WeatherSignal, pollen: PollenSignal) -> str:

    moon = compute_moon()
    quote = todays_quote()

    commute = compute_commute(weather)

    commute_details = ""

    if commute["show_details"]:
        precip_in = round(weather.precip_mm * 0.03937, 2)

        commute_details = f"""
Precipitation: {precip_in} in
Black Ice Risk: {commute["ice_risk"]}
{commute["ice_text"]}
"""

    pollen_section = ""

    if any([
        pollen.alder,
        pollen.birch,
        pollen.grass,
        pollen.ragweed
    ]):

        pollen_section = f"""
Pollen
------
Alder: {pollen_level(pollen.alder)}
Birch: {pollen_level(pollen.birch)}
Grass: {pollen_level(pollen.grass)}
Ragweed: {pollen_level(pollen.ragweed)}
"""

    return f"""
DailyPulseWatch

ZIP: {zip_code}

Weather
-------
High: {weather.high_f}°F
Low: {weather.low_f}°F

Sun
---
Sunrise: {weather.sunrise}
Sunset: {weather.sunset}

Commute Weather Watch
---------------------
{commute["commute_line"]}
{commute_details}
{pollen_section}

Moon
----
Phase: {moon.phase}
Meaning: {moon.meaning}

Quote
-----
"{quote.get('text','')}"
— {quote.get('author','')}
"""