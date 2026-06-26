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
    condition: str = "Unavailable"
    summary: str = "Weather summary unavailable."

    foggy: bool = False
    heavy_rain: bool = False

    tomorrow_high_f: float | None = None
    tomorrow_low_f: float | None = None
    tomorrow_precip_mm: float | None = None
    tomorrow_freezing: bool = False
    tomorrow_sunrise: str | None = None
    tomorrow_sunset: str | None = None
    tomorrow_condition: str | None = None
    tomorrow_summary: str | None = None
    tomorrow_foggy: bool = False
    tomorrow_heavy_rain: bool = False

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

def weather_code_description(code) -> str:
    descriptions = {
        0: "Clear sky",
        1: "Mostly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Freezing fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Heavy drizzle",
        56: "Light freezing drizzle",
        57: "Freezing drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Freezing rain",
        71: "Light snow",
        73: "Snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Light rain showers",
        81: "Rain showers",
        82: "Heavy rain showers",
        85: "Light snow showers",
        86: "Snow showers",
        95: "Thunderstorms",
        96: "Thunderstorms with hail",
        99: "Severe thunderstorms with hail",
    }

    try:
        return descriptions.get(int(code), "Weather conditions unavailable")
    except Exception:
        return "Weather conditions unavailable"


def summarize_day_weather(hourly_weather_codes, hourly_precip_probs=None, start_index=0) -> str:
    hourly_precip_probs = hourly_precip_probs or []

    morning_codes = hourly_weather_codes[start_index + 6:start_index + 12]
    afternoon_codes = hourly_weather_codes[start_index + 12:start_index + 18]
    evening_codes = hourly_weather_codes[start_index + 18:start_index + 23]

    day_codes = morning_codes + afternoon_codes + evening_codes

    if not day_codes:
        return "Weather summary unavailable."

    def has_fog(codes):
        return any(code in [45, 48] for code in codes)

    def has_heavy_rain(codes):
        return any(code in [65, 82] for code in codes)

    def has_rain(codes):
        return any(code in [51, 53, 55, 61, 63, 65, 80, 81, 82] for code in codes)

    def has_snow(codes):
        return any(code in [71, 73, 75, 77, 85, 86] for code in codes)

    def mostly_clear(codes):
        return codes and sum(1 for code in codes if code in [0, 1]) >= max(1, len(codes) // 2)

    def mostly_cloudy(codes):
        return codes and sum(1 for code in codes if code in [2, 3]) >= max(1, len(codes) // 2)

    def block_name(codes):
        if has_fog(codes):
            return "fog"
        if has_snow(codes):
            return "snow"
        if has_heavy_rain(codes):
            return "heavy rain"
        if has_rain(codes):
            return "rain"
        if mostly_clear(codes):
            return "mostly clear"
        if mostly_cloudy(codes):
            return "cloudy"
        return "mixed"

    morning = block_name(morning_codes)
    afternoon = block_name(afternoon_codes)
    evening = block_name(evening_codes)

    max_precip = 0

    if hourly_precip_probs:
        day_probs = hourly_precip_probs[start_index + 6:start_index + 23]
        clean_probs = [p for p in day_probs if p is not None]
        max_precip = max(clean_probs) if clean_probs else 0

    # Fog gets priority because it matters for driving visibility
    if morning == "fog":
        return "Fog may reduce visibility during the morning commute."

    if afternoon == "fog" or evening == "fog":
        return "Fog may reduce visibility later in the day."

    if morning == afternoon == evening:
        if morning == "mostly clear":
            return "Mostly clear through the day."
        if morning == "cloudy":
            return "Cloudy through much of the day."
        if morning == "rain":
            return "Rain is possible through much of the day."
        if morning == "heavy rain":
            return "Heavy rain may affect travel at times today."
        if morning == "snow":
            return "Snow is possible through much of the day."

    if morning != afternoon:
        if afternoon == "heavy rain":
            return "Clouds may build through the morning, with heavier rain possible later."
        if afternoon == "rain":
            return "Clouds may build through the morning, with rain possible later in the day."
        if morning == "rain" and afternoon != "rain":
            return "Rain is possible early, with conditions improving later."
        if morning == "mostly clear" and afternoon == "cloudy":
            return "A clearer start may turn cloudier later in the day."
        if morning == "cloudy" and afternoon == "mostly clear":
            return "Clouds may linger early, with brighter conditions later."

    if evening == "heavy rain":
        return "Heavier rain may become more likely later in the day."

    if evening == "rain":
        return "Rain may become more likely later in the day."

    if max_precip >= 50:
        return "Keep an eye out for showers at some point today."

    return "Mixed conditions through the day."


def has_fog_in_day(hourly_weather_codes, start_index=0) -> bool:
    day_codes = hourly_weather_codes[start_index + 5:start_index + 23]
    return any(code in [45, 48] for code in day_codes)


def has_heavy_rain_in_day(hourly_weather_codes, start_index=0) -> bool:
    day_codes = hourly_weather_codes[start_index + 5:start_index + 23]
    return any(code in [65, 82] for code in day_codes)


def fetch_weather(lat: float, lon: float) -> WeatherSignal:
    from mailer.weather_openweather import fetch_weather_openweather

    return fetch_weather_openweather(lat, lon)


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
    if getattr(weather, "foggy", False):
        return {
            "commute_line": "Fog may reduce visibility during your commute. Allow extra space and use low beams.",
            "ice_risk": "Visibility concern",
            "ice_text": "Fog can make it harder to see stopped traffic, pedestrians, and road changes.",
            "show_details": True
        }

    if getattr(weather, "heavy_rain", False):
        return {
            "commute_line": "Heavy rain may affect travel today. Watch for ponding on roads and reduced visibility.",
            "ice_risk": "Rain concern",
            "ice_text": "Heavy rain can increase stopping distance and reduce visibility.",
            "show_details": True
        }

    if weather.wind_gust >= 35:
        return {
            "commute_line": "Gusty winds may affect the commute, especially on open roads and bridges.",
            "ice_risk": "Wind concern",
            "ice_text": "Strong gusts can make driving feel unstable, especially for high-profile vehicles.",
            "show_details": True
        }

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
Commute Concern: {commute["ice_risk"]}
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
Summary: {getattr(weather, "tomorrow_summary", "—")}
Condition: {getattr(weather, "tomorrow_condition", "—")}
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
Summary: {getattr(weather, "summary", "—")}
Condition: {getattr(weather, "condition", "—")}
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
