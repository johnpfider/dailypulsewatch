import json
from pathlib import Path

# Load ZIP dataset
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "zip_lat_lon.json"

with open(DATA_PATH, "r") as f:
    ZIP_DATA = json.load(f)


def geocode_zip(zip_code: str):
    """
    Convert ZIP code to latitude and longitude.
    """

    coords = ZIP_DATA.get(zip_code)

    if not coords:
        raise ValueError("ZIP code not found")

    return coords["lat"], coords["lon"]