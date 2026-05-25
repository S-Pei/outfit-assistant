import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image, ImageDraw

from app.platform import is_raspberry_pi
from display.epaper import display_on_epaper, get_epaper_dimensions
from display.preview import save_preview
from screens.weather import _center_text, _load_font, _text_size
from services.quotes import fetch_random_quote


def _wrap_lines(draw, text, font, max_width):
    words = str(text).split()
    lines = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"
        if _text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
        current = word

    if current:
        lines.append(current)
    return lines


def _quote_text(quote):
    text = quote.get("quote")
    if not text:
        raise RuntimeError("Quote response is missing quote text")
    return str(text).strip()


def _attribution_text(quote):
    author = str(quote.get("author") or "Unknown").strip()
    work = str(quote.get("work") or "").strip()
    if work:
        return f"- {author} ({work})"
    return f"- {author}"


def create_quote_screen(data, width, height, now=None):
    image = Image.new("1", (width, height), 255)
    draw = ImageDraw.Draw(image)

    font_quote = _load_font(34)
    font_quote_small = _load_font(28)
    font_author = _load_font(24)

    margin = 28
    quote = _quote_text(data)
    attribution = _attribution_text(data)

    quote_max_width = width - margin * 2
    quote_font = font_quote
    quote_lines = _wrap_lines(draw, quote, quote_font, quote_max_width)
    if len(quote_lines) > 5:
        quote_font = font_quote_small
        quote_lines = _wrap_lines(draw, quote, quote_font, quote_max_width)

    line_gap = 8
    quote_line_h = _text_size(draw, "Ag", quote_font)[1] + line_gap
    author_h = _text_size(draw, attribution, font_author)[1]
    block_h = len(quote_lines) * quote_line_h + 26 + author_h
    y = max(margin, (height - block_h) // 2)

    for line in quote_lines:
        _center_text(draw, (margin, y, width - margin, y + quote_line_h), line, quote_font)
        y += quote_line_h

    y += 18
    author_lines = _wrap_lines(draw, attribution, font_author, quote_max_width)
    for line in author_lines[:2]:
        _center_text(draw, (margin, y, width - margin, y + 32), line, font_author)
        y += 32

    return image


def create_random_quote_screen(width, height, categories=None):
    return create_quote_screen(fetch_random_quote(categories=categories), width, height)


def main():
    on_pi = is_raspberry_pi()
    epaper_dims = get_epaper_dimensions() if on_pi else None
    width, height = epaper_dims if epaper_dims and all(epaper_dims) else (648, 480)
    image = create_random_quote_screen(width, height)

    if on_pi:
        display_on_epaper(image)
    else:
        save_preview(image, filename=REPO_ROOT / "previews" / "quote_preview.png", scale=2)


if __name__ == "__main__":
    main()
