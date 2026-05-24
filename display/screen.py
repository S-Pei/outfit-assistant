from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os
from icons import get_icon

def get_font_path():
    if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        return "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # Raspberry Pi / Linux

    if os.path.exists("/System/Library/Fonts/Supplemental/Arial.ttf"):
        return "/System/Library/Fonts/Supplemental/Arial.ttf"  # macOS

    return None

def _load_font(size):
    FONT_PATH = get_font_path()
    if not FONT_PATH:
        raise ValueError("Font file not found")
    return ImageFont.truetype(FONT_PATH, size)


def create_weather_screen(data, width, height):
    image = Image.new("1", (width, height), 255)
    draw = ImageDraw.Draw(image)

    font_title = _load_font(28)
    font_header = _load_font(20)
    font_large = _load_font(56)
    font_medium = _load_font(24)
    font_small = _load_font(16)

    city = data.get("city", "Unknown City")
    timestamp = data.get("time", "--:--")
    temp = data.get("temp", "--")
    condition = data.get("condition", "Unknown")
    feels = data.get("feels", "--")
    wind = data.get("wind", "--")
    recommendation = data.get("recommendation", "Check the weather and dress for it.")
    extra = data.get("extra", None)

    margin = 20

    # Header
    draw.text((margin, margin), city.upper(), font=font_title, fill=0)
    time_box = draw.textbbox((0, 0), timestamp, font=font_small)
    time_width = time_box[2] - time_box[0]
    draw.text((width - margin - time_width, margin + 4), timestamp, font=font_small, fill=0)
    draw.line((margin, margin + 42, width - margin, margin + 42), fill=0)

    # Main temperature
    temp_text = f"{temp}°C"
    temp_box = draw.textbbox((0, 0), temp_text, font=font_large)
    temp_height = temp_box[3] - temp_box[1]
    temp_y = margin + 55
    draw.text((margin, temp_y), temp_text, font=font_large, fill=0)
    condition_y = temp_y + temp_height + 35
    draw.text((margin, condition_y), condition.title(), font=font_medium, fill=0)
    condition_box = draw.textbbox((0, 0), condition.title(), font=font_medium)
    condition_height = condition_box[3] - condition_box[1]

    # Icon (paste from icons module)
    icon_size = min(100, width // 5)
    icon_top = temp_y + max(0, (temp_height - icon_size) // 2)
    icon_box = (width - margin - icon_size, icon_top, width - margin, icon_top + icon_size)
    x0, y0, x1, y1 = icon_box
    iw = max(1, x1 - x0)
    ih = max(1, y1 - y0)
    icon_img = get_icon(condition, (iw, ih))
    image.paste(icon_img, (x0, y0))

    body_bottom = max(condition_y + condition_height + 15, y1)
    stats_top = body_bottom + 16
    stats_height = min(80, max(60, height - margin - stats_top - 90))
    stats_bottom = stats_top + stats_height
    draw.rectangle((margin, stats_top, width - margin, stats_bottom), outline=0)

    label_x = margin + 14
    value_x = width // 2 + 10
    draw.text((label_x, stats_top + 14), "Feels like", font=font_small, fill=0)
    draw.text((label_x, stats_top + 40), f"{feels}°C", font=font_header, fill=0)
    draw.text((value_x, stats_top + 14), "Wind", font=font_small, fill=0)
    draw.text((value_x, stats_top + 40), f"{wind} km/h", font=font_header, fill=0)

    if extra and stats_height >= 100:
        draw.text((label_x, stats_top + 80), extra, font=font_small, fill=0)

    # Recommendation footer
    rec_top = stats_bottom + 18
    if rec_top >= height - margin - 40:
        rec_top = max(stats_bottom + 18, height - margin - 80)
    draw.rectangle((margin, rec_top, width - margin, height - margin), outline=0)
    draw.text((margin + 12, rec_top + 12), "Recommendation", font=font_small, fill=0)
    draw.multiline_text((margin + 12, rec_top + 40), recommendation, font=font_small, fill=0, spacing=4)

    return image
