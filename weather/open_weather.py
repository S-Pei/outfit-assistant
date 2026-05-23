"""OpenWeather helper: fetch current weather and return a display-friendly dict.

Usage:
    from weather.open_weather import fetch_weather
    data = fetch_weather('London')

Returns a dict with keys: city, time, temp, condition, feels, wind, recommendation
"""
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.openweathermap.org/data/2.5/weather"


def _make_recommendation(temp_c, condition_text):
    cond = condition_text.lower()
    if "rain" in cond or "drizzle" in cond:
        return "Take an umbrella and a waterproof layer."
    if temp_c <= 5:
        return "Wear a heavy coat, hat and gloves."
    if temp_c <= 15:
        return "Wear a jacket or sweater."
    if temp_c >= 25:
        return "BRO IT'S SO HOT, maybe stay home."
    return "Comfortable weather — dress in layers."


def fetch_weather(city=None, api_key=None, units="metric"):
    """Fetch current weather for `city` (string). Returns dict or raises.

    If `city` is None, function raises ValueError.
    """
    if not city:
        raise ValueError("city must be provided")

    key = api_key or os.getenv("OPENWEATHER_API_KEY")
    if not key:
        raise RuntimeError("OpenWeather API key not found in environment or api_key param")

    params = {"q": city, "appid": key, "units": units}
    resp = requests.get(API_BASE, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    temp = data["main"].get("temp")
    feels_like = data["main"].get("feels_like")
    description = data["weather"][0].get("description", "")
    wind_speed = data.get("wind", {}).get("speed", "--")

    now = datetime.now().strftime("%H:%M")

    return {
        "city": city,
        "time": now,
        "temp": int(round(temp)) if temp is not None else "--",
        "condition": description.title(),
        "feels": int(round(feels_like)) if feels_like is not None else "--",
        "wind": wind_speed,
        "recommendation": _make_recommendation(temp if temp is not None else 20, description),
    }


if __name__ == "__main__":
    # quick CLI test
    try:
        city = os.getenv("CITY", "London")
        weather = fetch_weather(city)
        print(weather)
    except Exception as e:
        print("Error fetching weather:", e)