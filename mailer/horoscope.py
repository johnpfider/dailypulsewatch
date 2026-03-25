import requests
import json
from pathlib import Path
from datetime import date

# =========================
# FILE PATH
# =========================
CACHE_FILE = Path(__file__).resolve().parents[1] / "data" / "horoscope_cache.json"


# =========================
# FETCH FROM API (SAFE)
# =========================
def fetch_horoscope(sign: str) -> str:
    url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"

    r = requests.get(
        url,
        params={"sign": sign.lower(), "day": "today"},
        timeout=10
    )
    r.raise_for_status()

    data = r.json()

    # 🔒 SAFE PARSING (prevents 'horoscope_data' crash)
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], dict):
            return (
                data["data"].get("horoscope_data")
                or data["data"].get("horoscope")
                or ""
            )

    return ""


# =========================
# LOAD CACHE
# =========================
def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except:
            return {}
    return {}


# =========================
# SAVE CACHE
# =========================
def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


# =========================
# MAIN FUNCTION (BATCH + CACHE)
# =========================
def get_horoscopes(signs: set[str]) -> dict[str, str]:
    today = date.today().isoformat()
    cache = load_cache()
    updated = False

    results = {}

    for sign in signs:
        key = sign.lower()

        # If cached today → reuse
        if key in cache and cache[key]["date"] == today:
            results[key] = cache[key]["text"]
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