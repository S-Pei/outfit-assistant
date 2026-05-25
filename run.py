import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DISPLAY_DIR = REPO_ROOT / "display"
if str(DISPLAY_DIR) not in sys.path:
    sys.path.insert(0, str(DISPLAY_DIR))

from run_display import display_on_epaper, get_epaper_dimensions, save_preview
from screen import create_daily_forecast_screen
from weather.open_weather import fetch_daily_forecast


def is_raspberry_pi():
    model_path = Path("/proc/device-tree/model")
    if not model_path.exists():
        return False

    try:
        return "raspberry pi" in model_path.read_text(errors="ignore").lower()
    except OSError:
        return False


def read_key():
    if not sys.stdin.isatty():
        return sys.stdin.read(1)

    try:
        import termios
        import tty
    except ImportError:
        return input().strip()[:1]

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def get_target_date():
    target_date = date.today()
    if datetime.now().hour >= 20:
        target_date = target_date + timedelta(days=1)
    return target_date


def fetch_screen_data():
    city = os.getenv("CITY", "London")
    target_date = get_target_date()
    data = fetch_daily_forecast(city, target_date=target_date.isoformat())
    data["time"] = datetime.now().strftime("%H:%M")
    return data


def render_daily_forecast():
    on_pi = is_raspberry_pi()
    epaper_dims = get_epaper_dimensions() if on_pi else None
    width, height = epaper_dims if epaper_dims and all(epaper_dims) else (648, 480)

    data = fetch_screen_data()
    image = create_daily_forecast_screen(data, width, height)

    if on_pi:
        display_on_epaper(image)
    else:
        save_preview(image, filename="daily_forecast_key_preview.png", scale=2)


def main():
    print("Press 1 to render the daily forecast screen. Press q to quit.")

    while True:
        key = read_key()
        print()

        if key == "1":
            render_daily_forecast()
            print("Ready. Press 1 to render again, or q to quit.")
        elif key in ("q", "Q"):
            print("Exiting.")
            return
        else:
            print(f"Ignored key: {key!r}. Press 1 to render, or q to quit.")


if __name__ == "__main__":
    main()
