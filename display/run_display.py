from PIL import Image
import os
import sys
from pathlib import Path
from datetime import date, datetime, timedelta

# Ensure repo root is on sys.path so sibling packages like `weather` can be imported
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Add Waveshare library path if available on Raspberry Pi / Jetson Nano
EPD_LIB_PATH = Path('/home/cutiepi/e-Paper/RaspberryPi_JetsonNano/python/lib')
if EPD_LIB_PATH.is_dir():
    sys.path.append(str(EPD_LIB_PATH))

from screen import create_daily_forecast_screen, create_weather_screen
from weather.open_weather import fetch_daily_forecast, fetch_weather


def parse_preview_scale(argv):
    for arg in argv:
        if arg.startswith("--preview-scale="):
            try:
                return int(arg.split("=", 1)[1])
            except ValueError:
                pass
    return 1


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


def get_sample_daily_forecast_data():
    return {
        "city": "London",
        "date_label": "Today",
        "condition": "Light Rain",
        "summary": "Umbrella | removable layer | wind picks up late",
        "min_temp": 11,
        "max_temp": 19,
        "max_pop": 80,
        "max_wind": 8,
        "rain_window": "13:00 - 19:00",
        "forecast": [
            {"time": "07:00", "temp": 11, "condition": "Clouds", "pop": 10, "wind": 3},
            {"time": "10:00", "temp": 15, "condition": "Clouds", "pop": 25, "wind": 4},
            {"time": "13:00", "temp": 18, "condition": "Light Rain", "pop": 65, "wind": 6},
            {"time": "16:00", "temp": 19, "condition": "Rain", "pop": 80, "wind": 8},
            {"time": "19:00", "temp": 16, "condition": "Drizzle", "pop": 55, "wind": 7},
            {"time": "22:00", "temp": 13, "condition": "Clouds", "pop": 20, "wind": 5},
        ],
    }


def save_preview(image, filename="weather_screen_preview.png", scale=1, as_epaper=False):
    if as_epaper:
        image = get_epaper_preview(image)
        filename = filename.replace("preview", "epaper_preview")

    if scale == 1:
        image.save(filename)
        print(f"Saved preview image: {filename}")
    else:
        scaled = image.resize((image.width * scale, image.height * scale), resample=Image.NEAREST)
        scaled_name = filename.replace(".png", f"@{scale}x.png")
        scaled.save(scaled_name)
        print(f"Saved scaled debug preview image: {scaled_name}")


def get_epaper_dimensions():
    try:
        from waveshare_epd import epd5in83_V2
    except ImportError:
        return None

    epd = epd5in83_V2.EPD()
    try:
        epd.init()
    except Exception:
        pass
    return getattr(epd, "width", None), getattr(epd, "height", None)


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


def _buffer_to_pil(buffer, width, height):
    image = Image.new("1", (width, height), 1)
    pixels = image.load()
    row_bytes = (width + 7) // 8
    for y in range(height):
        offset = y * row_bytes
        for x_byte in range(row_bytes):
            byte = buffer[offset + x_byte]
            for bit in range(8):
                x = x_byte * 8 + bit
                if x >= width:
                    break
                pixels[x, y] = 0 if (byte & (0x80 >> bit)) else 1
    return image


def get_epaper_preview(image):
    try:
        from waveshare_epd import epd5in83_V2
    except ImportError as exc:
        print("E-paper preview unavailable, device library not installed:", exc)
        return image

    epd = epd5in83_V2.EPD()
    epd.init()
    epd.Clear()
    buffer = epd.getbuffer(image)
    return _buffer_to_pil(buffer, epd.width, epd.height)


def main():
    daily_mode = "--daily" in sys.argv or "--forecast" in sys.argv
    data = get_sample_daily_forecast_data() if daily_mode else get_sample_weather_data()
    preview_scale = parse_preview_scale(sys.argv)
    device_preview = "--preview-device" in sys.argv or "--preview-epaper" in sys.argv or "--debug" in sys.argv
    epaper_dims = get_epaper_dimensions() if device_preview or "--display" in sys.argv or "--all" in sys.argv else None
    width, height = epaper_dims if epaper_dims and all(epaper_dims) else (648, 480)

    image = create_daily_forecast_screen(data, width, height) if daily_mode else create_weather_screen(data, width, height)
    # support live weather fetch
    live_mode = "--live" in sys.argv or "--weather" in sys.argv
    device_preview = "--preview-device" in sys.argv or "--preview-epaper" in sys.argv or "--debug" in sys.argv
    preview_mode = ("--preview" in sys.argv or "--save" in sys.argv or "--all" in sys.argv or preview_scale != 1 or device_preview)
    display_mode = "--display" in sys.argv or "--all" in sys.argv

    if not preview_mode and not display_mode:
        preview_mode = True

    if live_mode:
        try:
            live_city = os.getenv("CITY", data.get("city", "London"))
            if daily_mode:
                target_date = date.today()
                date_label = "Today"
                if datetime.now().hour >= 20:
                    target_date = target_date + timedelta(days=1)
                    date_label = "Tomorrow"

                data_live = fetch_daily_forecast(live_city, target_date=target_date.isoformat())
                data_live["date_label"] = date_label
                image = create_daily_forecast_screen(data_live, width, height)
            else:
                data_live = fetch_weather(live_city)
                image = create_weather_screen(data_live, width, height)
            data = data_live
            print("Fetched live weather for", live_city)
        except Exception as e:
            print("Live weather fetch failed, using sample data:", e)

    if preview_mode:
        preview_filename = "daily_forecast_preview.png" if daily_mode else "weather_screen_preview.png"
        save_preview(image, filename=preview_filename, scale=preview_scale, as_epaper=device_preview)

    if display_mode:
        display_on_epaper(image)


if __name__ == "__main__":
    main()
