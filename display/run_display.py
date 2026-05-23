from PIL import Image
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
    width = 648
    height = 480
    data = get_sample_weather_data()
    preview_scale = parse_preview_scale(sys.argv)

    image = create_weather_screen(data, width, height)
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
            data_live = fetch_weather(live_city)
            data = data_live
            image = create_weather_screen(data, width, height)
            print("Fetched live weather for", live_city)
        except Exception as e:
            print("Live weather fetch failed, using sample data:", e)

    if preview_mode:
        save_preview(image, scale=preview_scale, as_epaper=device_preview)

    if display_mode:
        display_on_epaper(image)


if __name__ == "__main__":
    main()
