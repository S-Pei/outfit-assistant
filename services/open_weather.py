"""OpenWeather helper: fetch current weather and return a display-friendly dict.

Usage:
    from services.open_weather import fetch_weather
    data = fetch_weather('London')

Returns a dict with keys: city, time, temp, condition, feels, wind, recommendation
"""
import os
import requests
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_API_BASE = "https://api.openweathermap.org/data/2.5/forecast"


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
    resp = requests.get(API_BASE, params=params, timeout=5)
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


def _normalize_date_param(date_value):
    if isinstance(date_value, date):
        return date_value
    return datetime.fromisoformat(date_value).date()


def fetch_daily_forecast(city=None, target_date=None, api_key=None, units="metric"):
    """Fetch the day forecast for `city` and `target_date`.

    Returns local forecast entries for the specified date.
    """
    if not city:
        raise ValueError("city must be provided")

    key = api_key or os.getenv("OPENWEATHER_API_KEY")
    if not key:
        raise RuntimeError("OpenWeather API key not found in environment or api_key param")

    if target_date is None:
        target_date = datetime.utcnow().date()
    else:
        target_date = _normalize_date_param(target_date)

    params = {"q": city, "appid": key, "units": units}
    resp = requests.get(FORECAST_API_BASE, params=params, timeout=5)
    resp.raise_for_status()
    data = resp.json()

    timezone_offset = data.get("city", {}).get("timezone", 0)
    sunset = data.get("city", {}).get("sunset")
    sunset_local = datetime.utcfromtimestamp(sunset) + timedelta(seconds=timezone_offset) if sunset else None
    entries = []
    temps = []

    for item in data.get("list", []):
        dt = datetime.utcfromtimestamp(item["dt"]) + timedelta(seconds=timezone_offset)
        if dt.date() != target_date:
            continue

        temp = item.get("main", {}).get("temp")
        feels_like = item.get("main", {}).get("feels_like")
        description = item.get("weather", [{}])[0].get("description", "")

        if temp is not None:
            temps.append(temp)

        entries.append({
            "time": dt.strftime("%H:%M"),
            "temp": int(round(temp)) if temp is not None else "--",
            "feels": int(round(feels_like)) if feels_like is not None else "--",
            "condition": description.title(),
            "wind": item.get("wind", {}).get("speed", "--"),
            "pop": int(round(item.get("pop", 0) * 100)),
        })

    return {
        "city": city,
        "date": target_date.isoformat(),
        "min_temp": int(round(min(temps))) if temps else "--",
        "max_temp": int(round(max(temps))) if temps else "--",
        "sunset": sunset_local.strftime("%H:%M") if sunset_local else "--",
        "forecast": entries,
    }


if __name__ == "__main__":
    # quick CLI test
    try:
        city = os.getenv("CITY", "London")
        weather = fetch_weather(city)
        print(weather)
        forecast = fetch_daily_forecast(city, target_date=date(2026, 5, 25).isoformat())
        print(forecast)
    except Exception as e:
        print("Error fetching weather:", e)
