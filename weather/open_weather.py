import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

CITY = "London"

url = (
    "https://api.openweathermap.org/data/2.5/weather"
    f"?q={CITY}"
    f"&appid={API_KEY}"
    "&units=metric"
)

response = requests.get(url)

data = response.json()

temp = data["main"]["temp"]
feels_like = data["main"]["feels_like"]
description = data["weather"][0]["description"]

print(f"Weather in {CITY}")
print(f"Temperature: {temp}°C")
print(f"Feels like: {feels_like}°C")
print(f"Condition: {description}")