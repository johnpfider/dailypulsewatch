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
    """
    Fetch daily horoscope from Aztro.

    Aztro uses POST, not GET.
    API docs:
    POST https://aztro.sameerkumar.website?sign=<sign>&day=today
    """

    url = "https://aztro.sameerkumar.website"

    r = requests.post(
        url,
        params={
            "sign": sign.lower(),
            "day": "today"
        },
        timeout=10
    )

    r.raise_for_status()

    data = r.json()

    if not isinstance(data, dict):
        return ""

    description = data.get("description", "")
    mood = data.get("mood", "")
    lucky_number = data.get("lucky_number", "")
    lucky_color = data.get("color", "")
    compatibility = data.get("compatibility", "")

    parts = []

    if description:
        parts.append(description)

    extras = []

    if mood:
        extras.append(f"Mood: {mood}")

    if lucky_number:
        extras.append(f"Lucky number: {lucky_number}")

    if lucky_color:
        extras.append(f"Lucky color: {lucky_color}")

    if compatibility:
        extras.append(f"Compatibility: {compatibility}")

    if extras:
        parts.append(" | ".join(extras))

    return "\n\n".join(parts)


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