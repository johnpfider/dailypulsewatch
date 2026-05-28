import requests
import json
from pathlib import Path
from datetime import date

# =========================
# FILE PATH
# =========================
CACHE_FILE = Path(__file__).resolve().parents[1] / "data" / "horoscope_cache.json"


# =========================
# FETCH FROM API
# =========================
def fetch_horoscope(sign: str) -> str:
    """
    Fetch daily horoscope from Free Horoscope API.

    Example:
    https://freehoroscopeapi.com/api/v1/get-horoscope/daily?sign=pisces
    """

    sign = sign.lower().strip()
    url = "https://freehoroscopeapi.com/api/v1/get-horoscope/daily"

    print(f"🔮 Fetching horoscope for {sign}...")

    response = requests.get(
        url,
        params={"sign": sign},
        timeout=10,
        headers={
            "Accept": "application/json",
            "User-Agent": "DailyPulseWatch/1.0"
        }
    )

    print(f"🔮 Horoscope API status for {sign}: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ Horoscope API failed for {sign}")
        print(f"❌ Response preview: {response.text[:300]}")
        response.raise_for_status()

    data = response.json()

    print(f"🔮 Horoscope API response keys for {sign}: {list(data.keys())}")

    horoscope_text = (
        data.get("data", {}).get("horoscope")
        or data.get("data", {}).get("horoscope_data")
        or data.get("horoscope")
        or data.get("horoscope_data")
        or ""
    )

    horoscope_text = horoscope_text.strip()

    if horoscope_text:
        print(f"✅ Horoscope fetched for {sign}: {len(horoscope_text)} characters")
    else:
        print(f"⚠️ Horoscope API returned empty text for {sign}")
        print(f"⚠️ Full response preview: {str(data)[:500]}")

    return horoscope_text


# =========================
# LOAD CACHE
# =========================
def load_cache():
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text())
            print("🔮 Horoscope cache loaded")
            return cache
        except Exception as e:
            print(f"⚠️ Horoscope cache could not be read: {e}")
            return {}

    print("🔮 No horoscope cache file found")
    return {}


# =========================
# SAVE CACHE
# =========================
def save_cache(cache):
    try:
        CACHE_FILE.write_text(json.dumps(cache, indent=2))
        print("✅ Horoscope cache saved")
    except Exception as e:
        print(f"⚠️ Horoscope cache could not be saved: {e}")


# =========================
# MAIN FUNCTION
# =========================
def get_horoscopes(signs: set[str]) -> dict[str, str]:
    today = date.today().isoformat()
    cache = load_cache()
    updated = False

    results = {}

    clean_signs = {
        sign.lower().strip()
        for sign in signs
        if sign and sign.strip()
    }

    print(f"🔮 Requested horoscope signs: {sorted(clean_signs)}")

    if not clean_signs:
        print("🔮 No horoscope signs requested")
        return results

    for sign in clean_signs:

        cached_entry = cache.get(sign)

        if cached_entry and cached_entry.get("date") == today:
            cached_text = cached_entry.get("text", "")

            if cached_text:
                print(f"✅ Using cached horoscope for {sign}")
                results[sign] = cached_text
                continue

            print(f"⚠️ Cached horoscope for {sign} is empty — retrying API")

        try:
            text = fetch_horoscope(sign)
        except Exception as e:
            print(f"❌ Horoscope fetch failed for {sign}: {e}")
            text = ""

        # IMPORTANT:
        # Only cache successful non-empty horoscope text.
        # Do NOT cache blanks, or one API failure ruins the whole day.
        if text:
            cache[sign] = {
                "date": today,
                "text": text
            }
            updated = True
            print(f"✅ Horoscope ready for {sign}")
        else:
            print(f"⚠️ No horoscope available for {sign}; not caching blank result")

        results[sign] = text

    if updated:
        save_cache(cache)
    else:
        print("🔮 Horoscope cache not updated")

    return results