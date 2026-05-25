import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image, ImageDraw, ImageOps

from app.platform import is_raspberry_pi
from display.epaper import display_on_epaper, get_epaper_dimensions
from display.preview import save_preview
from screens.weather import _center_text, _format_display_date, _load_font

ASSETS_DIR = REPO_ROOT / "assets"
UWU_ASSET = ASSETS_DIR / "epaper" / "UwU.png"
UWU_SOURCE = ASSETS_DIR / "images" / "UwU.png"


def make_greeting(now=None):
    now = now or datetime.now()
    if now.hour < 12:
        return "GOOD MORNING UwU"
    if now.hour < 18:
        return "GOOD AFTERNOON UwU"
    return "GOOD EVENING UwU"


def _cover_crop(image, size):
    target_w, target_h = size
    source_w, source_h = image.size
    scale = max(target_w / source_w, target_h / source_h)
    resized = image.resize((round(source_w * scale), round(source_h * scale)), Image.Resampling.LANCZOS)

    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def _load_uwu_thumbnail(size):
    if not UWU_SOURCE.is_file():
        raise FileNotFoundError(f"Greeting source image not found: {UWU_SOURCE}")

    thumbnail = Image.open(UWU_SOURCE)
    thumbnail = ImageOps.exif_transpose(thumbnail).convert("RGB")
    thumbnail = _cover_crop(thumbnail, size)
    thumbnail = ImageOps.autocontrast(thumbnail.convert("L"))
    return thumbnail.convert("1", dither=Image.Dither.FLOYDSTEINBERG)


def create_greeting_screen(width, height, now=None):
    now = now or datetime.now()

    image = Image.new("1", (width, height), 255)
    draw = ImageDraw.Draw(image)

    font_greeting = _load_font(38)
    font_time = _load_font(72)
    font_date = _load_font(28)

    margin = 24
    greeting = make_greeting(now)
    current_time = now.strftime("%H:%M")
    date_label = _format_display_date(now.date().isoformat())

    thumbnail_w = min(380, width - margin * 2)
    source_w, source_h = Image.open(UWU_SOURCE).size
    thumbnail_h = round(source_h * (thumbnail_w / source_w))
    if thumbnail_h > 245:
        thumbnail_h = 245
        thumbnail_w = round(source_w * (thumbnail_h / source_h))
    thumbnail = _load_uwu_thumbnail((thumbnail_w, thumbnail_h))
    image.paste(thumbnail, ((width - thumbnail_w) // 2, 104))

    _center_text(draw, (margin, 34, width - margin, 82), greeting, font_greeting)
    _center_text(draw, (margin, 336, width - margin, 416), current_time, font_time)
    _center_text(draw, (margin, 420, width - margin, 458), date_label, font_date)

    return image


def main():
    on_pi = is_raspberry_pi()
    epaper_dims = get_epaper_dimensions() if on_pi else None
    width, height = epaper_dims if epaper_dims and all(epaper_dims) else (648, 480)
    image = create_greeting_screen(width, height)

    if on_pi:
        display_on_epaper(image)
    else:
        save_preview(image, filename=REPO_ROOT / "previews" / "greeting_preview.png", scale=2)


if __name__ == "__main__":
    main()
