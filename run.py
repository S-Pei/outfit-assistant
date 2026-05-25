import os
import argparse
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.platform import is_raspberry_pi
from display.epaper import display_on_epaper, get_epaper_dimensions
from display.preview import save_preview
from screens.greeting import create_greeting_screen
from screens.weather import create_daily_forecast_screen
from services.open_weather import fetch_daily_forecast

PREVIEW_DIR = REPO_ROOT / "previews"
DEFAULT_SIZE = (648, 480)
WEATHER_WINDOW_MINUTES = 10


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


def get_screen_size(on_pi):
    epaper_dims = get_epaper_dimensions() if on_pi else None
    return epaper_dims if epaper_dims and all(epaper_dims) else DEFAULT_SIZE


def show_image(image, on_pi, preview_name):
    if on_pi:
        display_on_epaper(image)
    else:
        save_preview(image, filename=PREVIEW_DIR / preview_name, scale=2)


def render_greeting(now=None):
    on_pi = is_raspberry_pi()
    width, height = get_screen_size(on_pi)
    image = create_greeting_screen(width, height, now=now)
    show_image(image, on_pi, "greeting_preview.png")


def render_daily_forecast():
    on_pi = is_raspberry_pi()
    width, height = get_screen_size(on_pi)
    data = fetch_screen_data()
    image = create_daily_forecast_screen(data, width, height)
    show_image(image, on_pi, "daily_forecast_key_preview.png")


def desired_screen(now):
    return "weather" if now.minute < WEATHER_WINDOW_MINUTES else "greeting"


def render_current_screen(now=None):
    now = now or datetime.now()
    if desired_screen(now) == "weather":
        render_daily_forecast()
        return "weather"

    render_greeting(now=now)
    return "greeting"


def render_slot(now):
    screen = desired_screen(now)
    if screen == "weather":
        return (screen, now.date().isoformat(), now.hour)
    return (screen, now.date().isoformat(), now.hour, now.minute)


def run_display_loop(poll_seconds=300):
    print("Rendering greeting by default. Weather is shown for the first 10 minutes of every hour.")
    print("Press Ctrl+C to stop.")

    last_slot = None
    while True:
        now = datetime.now()
        slot = render_slot(now)

        if slot != last_slot:
            try:
                screen = render_current_screen(now)
            except Exception as exc:
                print(f"Display update failed while rendering {desired_screen(now)}: {exc}")
                raise

            print(f"Rendered {screen} at {now:%H:%M}.")
            last_slot = slot

        time.sleep(poll_seconds)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the outfit assistant e-paper display.")
    parser.add_argument("--once", action="store_true", help="Render the current scheduled screen once and exit.")
    parser.add_argument("--poll-seconds", type=int, default=30, help="Seconds between schedule checks.")
    parser.add_argument("--weather", action="store_true", help="Render the weather screen once and exit.")
    parser.add_argument("--greeting", action="store_true", help="Render the greeting screen once and exit.")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.weather:
        render_daily_forecast()
        return

    if args.greeting:
        render_greeting()
        return

    if args.once:
        rendered = render_current_screen()
        print(f"Rendered {rendered}.")
        return

    run_display_loop(poll_seconds=args.poll_seconds)


if __name__ == "__main__":
    main()
