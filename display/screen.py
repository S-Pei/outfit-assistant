from PIL import Image, ImageDraw, ImageFont
import os
from icons import get_icon


def _load_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue

    return ImageFont.load_default()


def create_weather_screen(data, width, height):
    image = Image.new("1", (width, height), 255)
    draw = ImageDraw.Draw(image)

    font_title = _load_font(26)
    font_header = _load_font(20)
    font_large = _load_font(90)
    font_medium = _load_font(22)
    font_small = _load_font(18)

    city = data.get("city", "Unknown City")
    timestamp = data.get("time", "--:--")
    temp = data.get("temp", "--")
    condition = data.get("condition", "Unknown")
    feels = data.get("feels", "--")
    wind = data.get("wind", "--")
    recommendation = data.get("recommendation", "Check the weather and dress for it.")
    extra = data.get("extra", None)

    margin = 18

    # Header
    draw.text((margin, margin), city.upper(), font=font_title, fill=0)
    time_box = draw.textbbox((0, 0), timestamp, font=font_small)
    time_width = time_box[2] - time_box[0]
    draw.text((width - margin - time_width, margin + 4), timestamp, font=font_small, fill=0)
    draw.line((margin, margin + 42, width - margin, margin + 42), fill=0)

    # Main temperature
    temp_text = f"{temp}°C"
    draw.text((margin, margin + 54), temp_text, font=font_large, fill=0)
    draw.text((margin, margin + 170), condition.title(), font=font_medium, fill=0)

    # Icon (paste from icons module)
    icon_box = (width - margin - 140, margin + 48, width - margin, margin + 140)
    x0, y0, x1, y1 = icon_box
    iw = max(1, x1 - x0)
    ih = max(1, y1 - y0)
    icon_img = get_icon(condition, (iw, ih))
    image.paste(icon_img, (x0, y0))

    # Stats card
    stats_top = margin + 220
    stats_height = 110
    draw.rectangle((margin, stats_top, width - margin, stats_top + stats_height), outline=0)

    label_x = margin + 14
    value_x = width // 2 + 10
    draw.text((label_x, stats_top + 14), "Feels like", font=font_small, fill=0)
    draw.text((label_x, stats_top + 40), f"{feels}°C", font=font_header, fill=0)
    draw.text((value_x, stats_top + 14), "Wind", font=font_small, fill=0)
    draw.text((value_x, stats_top + 40), f"{wind} km/h", font=font_header, fill=0)

    if extra:
        draw.text((label_x, stats_top + 80), extra, font=font_small, fill=0)

    # Recommendation footer
    rec_top = stats_top + stats_height + 18
    draw.rectangle((margin, rec_top, width - margin, height - margin), outline=0)
    draw.text((margin + 12, rec_top + 12), "Recommendation", font=font_small, fill=0)
    draw.multiline_text((margin + 12, rec_top + 40), recommendation, font=font_small, fill=0, spacing=4)

    return image
