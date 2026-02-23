# ============================================================
# DailyPulseWatch — Core Content Logic
# ============================================================

import json
import requests
from dataclasses import dataclass
from datetime import date
from pathlib import Path

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


# ============================================================
# MOON LOGIC (UNCHANGED)
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
# WEATHER LOGIC (UNCHANGED)
# ============================================================

def fetch_weather(lat: float, lon: float) -> WeatherSignal:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": 1,
        "timezone": "auto",
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    d = r.json()["daily"]

    high_c = d["temperature_2m_max"][0]
    low_c = d["temperature_2m_min"][0]
    precip = d["precipitation_sum"][0]

    high_f = round(high_c * 9 / 5 + 32, 1)
    low_f = round(low_c * 9 / 5 + 32, 1)

    return WeatherSignal(
        high_f=high_f,
        low_f=low_f,
        precip_mm=round(precip, 1),
        freezing=low_f <= 32,
    )


# ============================================================
# HOROSCOPES (Simplified — in-memory cache per run)
# ============================================================

def fetch_horoscope(sign: str) -> str:
    url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    r = requests.get(url, params={"sign": sign, "day": "today"}, timeout=10)
    r.raise_for_status()
    return r.json()["data"]["horoscope_data"]


def normalize_horoscope(value) -> str:
    if isinstance(value, dict):
        return value.get("text", "")
    if isinstance(value, str):
        return value
    return ""


# ============================================================
# QUOTES (UNCHANGED)
# ============================================================

def todays_quote():
    if not QUOTES_FILE.exists():
        return {"text": "", "author": ""}

    quotes = json.loads(QUOTES_FILE.read_text(encoding="utf-8") or "[]")
    if not quotes:
        return {"text": "", "author": ""}

    idx = date.today().toordinal() % len(quotes)
    return quotes[idx]