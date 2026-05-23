import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path so sibling packages like `weather` can be imported
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Add Waveshare library path if available on Raspberry Pi / Jetson Nano
EPD_LIB_PATH = Path('/home/cutiepi/e-Paper/RaspberryPi_JetsonNano/python/lib')
if EPD_LIB_PATH.is_dir():
    sys.path.append(str(EPD_LIB_PATH))

from screen import create_weather_screen
from weather.open_weather import fetch_weather


def get_sample_weather_data():
    return {
        "city": "London",
        "time": "12:45",
        "temp": 14,
        "condition": "Cloudy",
        "feels": 12,
        "wind": 9,
        "recommendation": "Wear a hoodie today.",
    }


def save_preview(image, filename="weather_screen_preview.png"):
    image.save(filename)
    print(f"Saved preview image: {filename}")


def display_on_epaper(image):
    try:
        from waveshare_epd import epd5in83_V2
    except ImportError as exc:
        print("Waveshare e-paper library not installed or path not found:", exc)
        return

    epd = epd5in83_V2.EPD()
    epd.init()
    epd.Clear()
    epd.display(epd.getbuffer(image))
    epd.sleep()
    print("Sent image to e-paper display")


def main():
    width = 648
    height = 480
    data = get_sample_weather_data()

    image = create_weather_screen(data, width, height)
    # support live weather fetch
    live_mode = "--live" in sys.argv or "--weather" in sys.argv
    preview_mode = "--preview" in sys.argv or "--save" in sys.argv or "--all" in sys.argv
    display_mode = "--display" in sys.argv or "--all" in sys.argv

    if not preview_mode and not display_mode:
        preview_mode = True

    if live_mode:
        try:
            live_city = os.getenv("CITY", data.get("city", "London"))
            data_live = fetch_weather(live_city)
            data = data_live
            image = create_weather_screen(data, width, height)
            print("Fetched live weather for", live_city)
        except Exception as e:
            print("Live weather fetch failed, using sample data:", e)

    if preview_mode:
        save_preview(image)

    if display_mode:
        display_on_epaper(image)


if __name__ == "__main__":
    main()
