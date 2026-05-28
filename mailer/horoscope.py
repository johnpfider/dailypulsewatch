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

    r = requests.get(
        url,
        params={"sign": sign},
        timeout=10,
    )

    r.raise_for_status()

    data = r.json()

    if not isinstance(data, dict):
        return ""

    horoscope_text = (
        data.get("data", {}).get("horoscope_data")
        or data.get("horoscope")
        or data.get("horoscope_data")
        or ""
    )

    return horoscope_text.strip()


# =========================
# LOAD CACHE
# =========================
def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}


# =========================
# SAVE CACHE
# =========================
def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


# =========================
# MAIN FUNCTION
# =========================
def get_horoscopes(signs: set[str]) -> dict[str, str]:
    today = date.today().isoformat()
    cache = load_cache()
    updated = False

    results = {}

    for sign in signs:
        key = sign.lower().strip()

        if key in cache and cache[key].get("date") == today:
            results[key] = cache[key].get("text", "")
        else:
            try:
                text = fetch_horoscope(key)
            except Exception as e:
                print(f"❌ Horoscope fetch failed for {key}: {e}")
                text = ""

            cache[key] = {
                "date": today,
                "text": text
            }

            results[key] = text
            updated = True

    if updated:
        save_cache(cache)

    return results