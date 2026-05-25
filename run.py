import os
import argparse
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.platform import is_raspberry_pi, read_key, read_key_with_timeout
from display.epaper import display_on_epaper, get_epaper_dimensions
from display.preview import save_preview
from screens.fact import create_random_fact_screen
from screens.greeting import create_greeting_screen
from screens.weather import create_daily_forecast_screen
from services.open_weather import fetch_daily_forecast

PREVIEW_DIR = REPO_ROOT / "previews"
DEFAULT_SIZE = (648, 480)
WEATHER_WINDOW_MINUTES = 10
BUTTON_IDLE_SECONDS = 10 * 60


def get_target_date():
    target_date = date.today()
    if datetime.now().hour >= 20:
        target_date = target_date + timedelta(days=1)
    return target_date


def fetch_screen_data():
    city = os.getenv("CITY", "London")
    target_date = get_target_date()
    print(f"Fetching weather for {city} on {target_date.isoformat()}...")
    data = fetch_daily_forecast(city, target_date=target_date.isoformat())
    data["time"] = datetime.now().strftime("%H:%M")
    return data


def get_screen_size(on_pi):
    epaper_dims = get_epaper_dimensions() if on_pi else None
    return epaper_dims if epaper_dims and all(epaper_dims) else DEFAULT_SIZE


def show_image(image, on_pi, preview_name, clear=False):
    if on_pi:
        display_on_epaper(image, clear=clear)
    else:
        save_preview(image, filename=PREVIEW_DIR / preview_name, scale=2)


def render_greeting(now=None, clear=False):
    on_pi = is_raspberry_pi()
    width, height = get_screen_size(on_pi)
    image = create_greeting_screen(width, height, now=now)
    show_image(image, on_pi, "greeting_preview.png", clear=clear)


def render_daily_forecast(clear=False):
    on_pi = is_raspberry_pi()
    width, height = get_screen_size(on_pi)
    data = fetch_screen_data()
    print("Creating weather screen image...")
    image = create_daily_forecast_screen(data, width, height)
    print("Sending weather screen to display...")
    show_image(image, on_pi, "daily_forecast_key_preview.png", clear=clear)


def render_fact(clear=False):
    on_pi = is_raspberry_pi()
    width, height = get_screen_size(on_pi)
    print("Fetching fact...")
    image = create_random_fact_screen(width, height)
    print("Sending fact screen to display...")
    show_image(image, on_pi, "fact_preview.png", clear=clear)


def desired_screen(now):
    return "weather" if now.minute < WEATHER_WINDOW_MINUTES else "greeting"


def render_current_screen(now=None, clear=False):
    now = now or datetime.now()
    if desired_screen(now) == "weather":
        render_daily_forecast(clear=clear)
        return "weather"

    render_greeting(now=now, clear=clear)
    return "greeting"


def render_slot(now):
    screen = desired_screen(now)
    if screen == "weather":
        return (screen, now.date().isoformat(), now.hour)
    return (screen, now.date().isoformat(), now.hour, now.minute)


def run_display_loop(poll_seconds=30):
    print("Rendering greeting by default. Weather is shown for the first 10 minutes of every hour.")
    print("Press Ctrl+C to stop.")

    last_slot = None
    last_screen = None
    while True:
        now = datetime.now()
        slot = render_slot(now)

        if slot != last_slot:
            expected_screen = desired_screen(now)
            clear = last_screen is not None and expected_screen != last_screen
            try:
                screen = render_current_screen(now, clear=clear)
            except Exception as exc:
                print(f"Display update failed while rendering {desired_screen(now)}: {exc}")
                raise

            print(f"Rendered {screen} at {now:%H:%M}.")
            last_slot = slot
            last_screen = screen

        time.sleep(poll_seconds)


def _read_key_with_timeout(timeout_seconds):
    return read_key_with_timeout(timeout_seconds)


def _seconds_until_next_minute(now=None):
    now = now or datetime.now()
    return max(1, 60 - now.second)


def run_button_loop(idle_seconds=BUTTON_IDLE_SECONDS):
    print("Button mode. Press 1 for weather, 2 for greeting, 3 for fact. Non-greeting screens idle back to greeting after 10 minutes. Press q to quit.")
    render_greeting()
    current_screen = "greeting"
    active_started_at = None

    while True:
        if current_screen == "greeting":
            key = _read_key_with_timeout(_seconds_until_next_minute())
            if key is None:
                render_greeting()
                current_screen = "greeting"
                print(f"Refreshed greeting at {datetime.now():%H:%M}.")
                continue
            print()
        else:
            remaining = idle_seconds - (time.monotonic() - active_started_at)
            if remaining <= 0:
                render_greeting(clear=current_screen != "greeting")
                current_screen = "greeting"
                active_started_at = None
                print("Returned to greeting. Press 1 for weather, 2 for greeting, 3 for fact, or q to quit.")
                continue

            key = _read_key_with_timeout(remaining)
            if key is None:
                continue
            print()

        if key == "1":
            try:
                render_daily_forecast(clear=current_screen != "weather")
            except Exception as exc:
                print(f"Weather render failed: {exc}")
                raise

            current_screen = "weather"
            active_started_at = time.monotonic()
            print("Rendered weather. It will return to greeting after 10 minutes. Press 1 to refresh, 2 for greeting, 3 for fact, or q to quit.")
        elif key == "2":
            render_greeting(clear=current_screen != "greeting")
            current_screen = "greeting"
            active_started_at = None
            print("Rendered greeting. Press 1 for weather, 2 to refresh greeting, 3 for fact, or q to quit.")
        elif key == "3":
            try:
                render_fact(clear=current_screen != "fact")
            except Exception as exc:
                print(f"Fact render failed: {exc}")
                raise

            current_screen = "fact"
            active_started_at = time.monotonic()
            print("Rendered fact. It will return to greeting after 10 minutes. Press 1 for weather, 2 for greeting, 3 to refresh fact, or q to quit.")
        elif key in ("q", "Q"):
            print("Exiting.")
            return
        else:
            print(f"Ignored key: {key!r}. Press 1 for weather, 2 for greeting, 3 for fact, or q to quit.")


def parse_args():
    parser = argparse.ArgumentParser(description="Run the outfit assistant e-paper display.")
    parser.add_argument("--once", action="store_true", help="Render the current scheduled screen once and exit.")
    parser.add_argument("--poll-seconds", type=int, default=30, help="Seconds between schedule checks.")
    parser.add_argument("--weather", action="store_true", help="Render the weather screen once and exit.")
    parser.add_argument("--greeting", action="store_true", help="Render the greeting screen once and exit.")
    parser.add_argument("--fact", action="store_true", help="Render the fact screen once and exit.")
    parser.add_argument("--button", action="store_true", help="Wait for keypresses; press 1 for weather, 2 for greeting, or 3 for fact.")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.weather:
        render_daily_forecast()
        return

    if args.greeting:
        render_greeting()
        return

    if args.fact:
        render_fact()
        return

    if args.once:
        rendered = render_current_screen()
        print(f"Rendered {rendered}.")
        return

    if args.button:
        run_button_loop()
        return

    run_display_loop(poll_seconds=args.poll_seconds)


if __name__ == "__main__":
    main()
