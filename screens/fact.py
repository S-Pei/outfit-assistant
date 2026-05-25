import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image, ImageDraw

from app.platform import is_raspberry_pi
from display.epaper import display_on_epaper, get_epaper_dimensions
from display.preview import save_preview
from screens.quote import _wrap_lines
from screens.weather import _center_text, _load_font, _text_size
from services.facts import fetch_random_fact

FLORAL_BORDER_PATH = REPO_ROOT / "assets" / "images" / "floral_border_1bit_648x480.png"


def _fact_text(fact):
    text = fact.get("fact")
    if not text:
        raise RuntimeError("Fact response is missing fact text")
    return str(text).strip()


def _load_floral_border(width, height):
    if not FLORAL_BORDER_PATH.is_file():
        raise FileNotFoundError(f"Floral border asset not found: {FLORAL_BORDER_PATH}")

    border = Image.open(FLORAL_BORDER_PATH).convert("1")
    if border.size != (width, height):
        border = border.resize((width, height), Image.Resampling.NEAREST)
    return border


def _fit_text_block(draw, text, max_width, max_height):
    line_gap = 8
    for size in range(38, 19, -2):
        font = _load_font(size)
        lines = _wrap_lines(draw, text, font, max_width)
        line_h = _text_size(draw, "Ag", font)[1] + line_gap
        block_h = len(lines) * line_h
        widest = max((_text_size(draw, line, font)[0] for line in lines), default=0)
        if widest <= max_width and block_h <= max_height:
            return font, lines, line_h, block_h

    font = _load_font(20)
    lines = _wrap_lines(draw, text, font, max_width)
    line_h = _text_size(draw, "Ag", font)[1] + line_gap
    return font, lines, line_h, len(lines) * line_h


def create_fact_screen(data, width, height):
    image = _load_floral_border(width, height)
    draw = ImageDraw.Draw(image)

    margin = 28
    fact = _fact_text(data)
    content_top = 128
    content_bottom = height - 136
    max_width = width - 128
    max_height = content_bottom - content_top
    fact_font, fact_lines, fact_line_h, block_h = _fit_text_block(draw, fact, max_width, max_height)
    y = content_top + (max_height - block_h) // 2

    for line in fact_lines:
        _center_text(draw, (margin, y, width - margin, y + fact_line_h), line, fact_font)
        y += fact_line_h

    return image


def create_random_fact_screen(width, height):
    return create_fact_screen(fetch_random_fact(), width, height)


def main():
    on_pi = is_raspberry_pi()
    epaper_dims = get_epaper_dimensions() if on_pi else None
    width, height = epaper_dims if epaper_dims and all(epaper_dims) else (648, 480)
    image = create_random_fact_screen(width, height)

    if on_pi:
        display_on_epaper(image)
    else:
        save_preview(image, filename=REPO_ROOT / "previews" / "fact_preview.png", scale=2)


if __name__ == "__main__":
    main()
