import os
import requests
from pathlib import Path
from PIL import Image

ICON_MAP = {
    "clear": "01d",
    "few clouds": "02d",
    "clouds": "03d",
    "overcast": "04d",
    "rain": "09d",
    "drizzle": "09d",
    "thunderstorm": "11d",
    "snow": "13d",
    "mist": "50d",
}

OUT_DIR = Path(__file__).resolve().parents[1] / "assets" / "icons"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def download_icon(code, out_path):
    url = f"https://openweathermap.org/img/wn/{code}@2x.png"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)


def fetch_all():
    for name, code in ICON_MAP.items():
        filename = f"{name.replace(' ', '_')}.png"
        out_path = OUT_DIR / filename
        try:
            print("Downloading", code, "->", out_path)
            download_icon(code, out_path)
        except Exception as e:
            print("Failed to download", code, e)


if __name__ == "__main__":
    fetch_all()
