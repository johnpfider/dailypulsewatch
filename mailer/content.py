# ============================================================
# DailyPulseWatch — Core Content Logic
# ============================================================

import json
import requests
import feedparser
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from html import unescape
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

    tomorrow_high_f: float | None = None
    tomorrow_low_f: float | None = None
    tomorrow_precip_mm: float | None = None
    tomorrow_freezing: bool = False
    tomorrow_sunrise: str | None = None
    tomorrow_sunset: str | None = None

    wind_speed: float = 0.0
    wind_gust: float = 0.0


@dataclass(slots=True)
class PollenSignal:
    alder: float
    birch: float
    grass: float
    ragweed: float


@dataclass(slots=True)
class HeadlineSignal:
    source: str
    title: str
    link: str


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
        "hourly": "windspeed_10m,windgusts_10m",
        "forecast_days": 2,
        "timezone": "auto",
    }

    retries = 3
    delay = 2

    for attempt in range(1, retries + 1):
        try:
            print(f"🌦️ Fetching weather (attempt {attempt})...")

            r = requests.get(url, params=params, timeout=5)
            r.raise_for_status()

            payload = r.json()
            d = payload["daily"]
            hourly = payload.get("hourly", {})

            # -----------------------
            # TODAY
            # -----------------------
            sunrise_dt = datetime.fromisoformat(d["sunrise"][0])
            sunset_dt = datetime.fromisoformat(d["sunset"][0])

            sunrise = sunrise_dt.strftime("%I:%M %p").lstrip("0")
            sunset = sunset_dt.strftime("%I:%M %p").lstrip("0")

            high_c = d["temperature_2m_max"][0]
            low_c = d["temperature_2m_min"][0]
            precip = d["precipitation_sum"][0]

            high_f = round(high_c * 9 / 5 + 32, 1)
            low_f = round(low_c * 9 / 5 + 32, 1)
            precip_mm = round(precip, 1)

            # -----------------------
            # TOMORROW
            # -----------------------
            tomorrow_high_f = None
            tomorrow_low_f = None
            tomorrow_precip_mm = None
            tomorrow_freezing = False
            tomorrow_sunrise = None
            tomorrow_sunset = None

            if len(d.get("temperature_2m_max", [])) > 1:
                tomorrow_high_c = d["temperature_2m_max"][1]
                tomorrow_low_c = d["temperature_2m_min"][1]
                tomorrow_precip = d["precipitation_sum"][1]

                tomorrow_high_f = round(tomorrow_high_c * 9 / 5 + 32, 1)
                tomorrow_low_f = round(tomorrow_low_c * 9 / 5 + 32, 1)
                tomorrow_precip_mm = round(tomorrow_precip, 1)
                tomorrow_freezing = tomorrow_low_f <= 32

                tomorrow_sunrise_dt = datetime.fromisoformat(d["sunrise"][1])
                tomorrow_sunset_dt = datetime.fromisoformat(d["sunset"][1])

                tomorrow_sunrise = tomorrow_sunrise_dt.strftime("%I:%M %p").lstrip("0")
                tomorrow_sunset = tomorrow_sunset_dt.strftime("%I:%M %p").lstrip("0")

            # -----------------------
            # WIND — today only
            # -----------------------
            wind_speed_values = hourly.get("windspeed_10m", [0]) or [0]
            wind_gust_values = hourly.get("windgusts_10m", [0]) or [0]

            today_wind_speed_values = wind_speed_values[:24]
            today_wind_gust_values = wind_gust_values[:24]

            wind_speed = float(max(today_wind_speed_values or [0]))
            wind_gust = float(max(today_wind_gust_values or [0]))

            print("✅ Weather fetched successfully")
            print(f"🌬️ WIND: speed={wind_speed}, gust={wind_gust}")
            print(f"🌤️ TODAY: high={high_f}, low={low_f}")
            print(f"🌤️ TOMORROW: high={tomorrow_high_f}, low={tomorrow_low_f}")

            return WeatherSignal(
                high_f=high_f,
                low_f=low_f,
                precip_mm=precip_mm,
                freezing=low_f <= 32,
                sunrise=sunrise,
                sunset=sunset,
                tomorrow_high_f=tomorrow_high_f,
                tomorrow_low_f=tomorrow_low_f,
                tomorrow_precip_mm=tomorrow_precip_mm,
                tomorrow_freezing=tomorrow_freezing,
                tomorrow_sunrise=tomorrow_sunrise,
                tomorrow_sunset=tomorrow_sunset,
                wind_speed=wind_speed,
                wind_gust=wind_gust,
            )

        except Exception as e:
            print(f"❌ Weather attempt {attempt} failed: {e}")

            if attempt < retries:
                print(f"⏳ Retrying weather in {delay} seconds...")
                time.sleep(delay)

    print("🚨 All weather retries failed — using fallback")
    raise Exception("Weather API failed after retries")


# ============================================================
# POLLEN LOGIC
# ============================================================

def _daily_peak(values) -> float:
    if not values:
        return 0.0

    clean = [v for v in values if v is not None]

    if not clean:
        return 0.0

    return float(max(clean))


def adjust_for_season(pollen: PollenSignal) -> PollenSignal:
    month = date.today().month

    if month in [3, 4, 5]:
        return PollenSignal(
            alder=max(pollen.alder, 2.0),
            birch=max(pollen.birch, 2.0),
            grass=max(pollen.grass, 1.0),
            ragweed=pollen.ragweed,
        )

    elif month in [6, 7]:
        return PollenSignal(
            alder=pollen.alder,
            birch=pollen.birch,
            grass=max(pollen.grass, 2.0),
            ragweed=pollen.ragweed,
        )

    elif month in [8, 9]:
        return PollenSignal(
            alder=pollen.alder,
            birch=pollen.birch,
            grass=pollen.grass,
            ragweed=max(pollen.ragweed, 2.0),
        )

    return pollen


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

            raw_pollen = PollenSignal(
                alder=_daily_peak(data.get("alder_pollen")),
                birch=_daily_peak(data.get("birch_pollen")),
                grass=_daily_peak(data.get("grass_pollen")),
                ragweed=_daily_peak(data.get("ragweed_pollen")),
            )

            pollen = adjust_for_season(raw_pollen)

            print(f"🌿 RAW POLLEN: {raw_pollen}")
            print(f"🌿 ADJUSTED POLLEN: {pollen}")

            return pollen

        except Exception as e:
            print(f"❌ Pollen attempt {attempt} failed: {e}")

            if attempt < retries:
                print(f"⏳ Retrying pollen in {delay} seconds...")
                time.sleep(delay)

    print("🚨 All pollen retries failed — using fallback")

    return PollenSignal(
        alder=0.0,
        birch=0.0,
        grass=0.0,
        ragweed=0.0
    )


def pollen_level(value: float) -> str:
    if value < 0.5:
        return "Low"
    elif value < 2:
        return "Moderate"
    elif value < 5:
        return "High"
    else:
        return "Very High"


def allergy_risk(pollen) -> str:
    values = [
        getattr(pollen, "alder", 0) or 0,
        getattr(pollen, "birch", 0) or 0,
        getattr(pollen, "grass", 0) or 0,
        getattr(pollen, "ragweed", 0) or 0,
    ]

    max_val = max(values)

    if max_val >= 5:
        return "🔴 High"
    elif max_val >= 2:
        return "🟡 Moderate"
    else:
        return "🟢 Low"


def pollen_context_line(weather: WeatherSignal) -> str:
    if weather.precip_mm >= 2:
        return "💡 Rain in the forecast may help reduce pollen levels by washing it out of the air."

    elif weather.precip_mm > 0:
        return "💡 Light rain may temporarily reduce pollen levels."

    if weather.wind_gust >= 20:
        return "💡 Gusty winds may increase pollen spread and worsen allergy symptoms."

    elif weather.wind_speed >= 10:
        return "💡 Breezy conditions may carry more pollen through the air."

    return "💡 Dry and calm conditions may allow pollen levels to remain steady."


# ============================================================
# HEADLINES / RSS LOGIC
# ============================================================

NPR_US_RSS_URL = "https://feeds.npr.org/1003/rss.xml"
NPR_WORLD_RSS_URL = "https://feeds.npr.org/1004/rss.xml"
HEALTH_NEWS_RSS_URL = "https://medicalxpress.com/rss-feed/"


OPINION_KEYWORDS = [
    "opinion",
    "commentary",
    "editorial",
    "op-ed",
    "op ed",
    "analysis",
    "perspective",
    "column",
    "essay",
    "review",
    "critic",
    "critics",
]


def _clean_headline(text: str) -> str:
    return unescape((text or "").strip())


def _is_opinion_like(title: str) -> bool:
    title_lower = (title or "").lower()

    return any(
        keyword in title_lower
        for keyword in OPINION_KEYWORDS
    )


def fetch_rss_headlines(feed_url: str, source_name: str, limit: int) -> list[HeadlineSignal]:
    retries = 3
    delay = 2

    for attempt in range(1, retries + 1):
        try:
            print(f"📰 Fetching {source_name} headlines (attempt {attempt})...")

            feed = feedparser.parse(feed_url)

            if getattr(feed, "bozo", False):
                print(f"⚠️ {source_name} RSS warning: {getattr(feed, 'bozo_exception', 'Unknown RSS issue')}")

            entries = getattr(feed, "entries", []) or []

            headlines = []

            for entry in entries:
                title = _clean_headline(getattr(entry, "title", ""))
                link = getattr(entry, "link", "")

                if not title or not link:
                    continue

                if _is_opinion_like(title):
                    print(f"🚫 Skipping opinion-like headline: {title}")
                    continue

                headlines.append(
                    HeadlineSignal(
                        source=source_name,
                        title=title,
                        link=link,
                    )
                )

                if len(headlines) >= limit:
                    break

            print(f"✅ {source_name} headlines fetched: {len(headlines)}")

            return headlines

        except Exception as e:
            print(f"❌ {source_name} headlines attempt {attempt} failed: {e}")

            if attempt < retries:
                print(f"⏳ Retrying {source_name} headlines in {delay} seconds...")
                time.sleep(delay)

    print(f"🚨 All {source_name} headline retries failed — skipping this feed")
    return []


def fetch_todays_headlines() -> list[HeadlineSignal]:
    international = fetch_rss_headlines(
        feed_url=NPR_WORLD_RSS_URL,
        source_name="NPR World",
        limit=1,
    )

    us = fetch_rss_headlines(
        feed_url=NPR_US_RSS_URL,
        source_name="NPR U.S.",
        limit=2,
    )

    health = fetch_rss_headlines(
        feed_url=HEALTH_NEWS_RSS_URL,
        source_name="Medical Xpress",
        limit=2,
    )

    return international + us + health


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

def build_email_content(
    zip_code: str,
    weather: WeatherSignal,
    pollen: PollenSignal,
    headlines: Optional[list[HeadlineSignal]] = None
) -> str:

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

    context_line = pollen_context_line(weather)

    pollen_section = f"""
Pollen
------
Alder: {pollen_level(pollen.alder)}
Birch: {pollen_level(pollen.birch)}
Grass: {pollen_level(pollen.grass)}
Ragweed: {pollen_level(pollen.ragweed)}
Allergy Risk: {allergy_risk(pollen)}

{context_line}
"""

    tomorrow_weather = ""

    if getattr(weather, "tomorrow_high_f", None) is not None:
        tomorrow_weather = f"""
Tomorrow Weather
----------------
High: {weather.tomorrow_high_f}°F
Low: {weather.tomorrow_low_f}°F
"""

    headlines = headlines or []

    headlines_section = ""

    if headlines:
        headline_lines = "\n".join(
            f"- [{h.source}] {h.title}\n  {h.link}"
            for h in headlines
        )

        headlines_section = f"""
Today's Headlines
-----------------
{headline_lines}
"""

    return f"""
DailyPulseWatch

ZIP: {zip_code}

Weather
-------
Today
High: {weather.high_f}°F
Low: {weather.low_f}°F
{tomorrow_weather}

Sun
---
Today
Sunrise: {weather.sunrise}
Sunset: {weather.sunset}

Tomorrow
Sunrise: {getattr(weather, "tomorrow_sunrise", "—")}
Sunset: {getattr(weather, "tomorrow_sunset", "—")}

Commute Weather Watch
---------------------
{commute["commute_line"]}
{commute_details}
{pollen_section}
{headlines_section}

Moon
----
Phase: {moon.phase}
Meaning: {moon.meaning}

Quote
-----
"{quote.get('text','')}"
— {quote.get('author','')}
"""