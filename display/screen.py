from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime
import os
from icons import get_icon
from recommendation import make_daily_recommendation

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


def _text_size(draw, text, font):
    box = draw.textbbox((0, 0), str(text), font=font)
    return box[2] - box[0], box[3] - box[1]


def _center_text(draw, box, text, font, fill=0):
    x0, y0, x1, y1 = box
    text_w, text_h = _text_size(draw, text, font)
    draw.text(
        (x0 + (x1 - x0 - text_w) / 2, y0 + (y1 - y0 - text_h) / 2),
        text,
        font=font,
        fill=fill,
    )


def _wrap_text(draw, text, font, max_width, max_lines=2):
    words = str(text).split()
    lines = []
    current = ""
    consumed_words = 0

    for word in words:
        candidate = word if not current else f"{current} {word}"
        if _text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
            consumed_words += 1
            continue

        if current:
            lines.append(current)
        current = word
        consumed_words += 1

        if len(lines) == max_lines:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) == max_lines and consumed_words < len(words):
        while _text_size(draw, lines[-1] + "...", font)[0] > max_width and len(lines[-1]) > 1:
            lines[-1] = lines[-1][:-1].rstrip()
        if not lines[-1].endswith("..."):
            lines[-1] += "..."

    return lines


def _format_value(value, suffix=""):
    if value is None or value == "":
        return "--"
    if value == "--":
        return "--"
    return f"{value}{suffix}"


def _format_display_date(date_value):
    if not date_value:
        return None
    try:
        return datetime.fromisoformat(str(date_value)).strftime("%d %b")
    except ValueError:
        return str(date_value)


def _as_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _forecast_hour(entry):
    time_text = str(entry.get("time", ""))
    try:
        return int(time_text.split(":", 1)[0])
    except (TypeError, ValueError):
        return None


def _time_minutes(time_text):
    try:
        hour, minute = str(time_text).split(":", 1)
        return int(hour) * 60 + int(minute)
    except (TypeError, ValueError):
        return None


def _filter_forecast_window(entries, start_hour=7, end_hour=23):
    filtered = []
    for entry in entries:
        hour = _forecast_hour(entry)
        if hour is None:
            continue
        if start_hour <= hour <= end_hour:
            filtered.append(entry)
    return filtered or entries


def _forecast_number(entries, key, reducer):
    values = [_as_number(entry.get(key)) for entry in entries]
    values = [value for value in values if value is not None]
    if not values:
        return "--"
    return int(round(reducer(values)))


def _forecast_time_for(entries, key, reducer):
    best_entry = None
    best_value = None

    for entry in entries:
        value = _as_number(entry.get(key))
        if value is None:
            continue
        if best_value is None or reducer([best_value, value]) == value:
            best_entry = entry
            best_value = value

    if not best_entry:
        return "--:--"
    return best_entry.get("time", "--:--")


def _forecast_temp_after(entries, time_text):
    threshold = _time_minutes(time_text)
    if threshold is None:
        return "--"

    temps = []
    for entry in entries:
        entry_minutes = _time_minutes(entry.get("time"))
        if entry_minutes is not None and entry_minutes >= threshold:
            temp = _as_number(entry.get("temp"))
            if temp is not None:
                temps.append(temp)

    return int(round(min(temps))) if temps else "--"


def _wind_label(speed):
    speed = _as_number(speed)
    if speed is None:
        return "--"
    if speed <= 2:
        return "Calm"
    if speed <= 5:
        return "Light breeze"
    if speed <= 8:
        return "Breezy"
    if speed <= 12:
        return "Windy"
    return "Very windy"


def _wind_impact(speed):
    speed = _as_number(speed)
    if speed is None:
        return "Wind unknown"
    if speed <= 2:
        return "No outfit issue"
    if speed <= 5:
        return "Fine outside"
    if speed <= 8:
        return "Light layer helps"
    if speed <= 12:
        return "Secure loose layers"
    return "Avoid fragile umbrella"


def _rain_timing(entries, max_pop, threshold=35):
    rainy = [entry for entry in entries if _as_number(entry.get("pop")) is not None and _as_number(entry.get("pop")) >= threshold]
    if not rainy:
        return False, "Unlikely", f"Peak {_format_value(max_pop, '%')}"
    return True, rainy[0].get("time", "--:--"), f"Stops {rainy[-1].get('time', '--:--')}"


def create_daily_forecast_screen(data, width, height):
    image = Image.new("1", (width, height), 255)
    draw = ImageDraw.Draw(image)

    font_title = _load_font(22)
    font_header = _load_font(20)
    font_large = _load_font(34)
    font_medium = _load_font(18)
    font_small = _load_font(14)
    font_tiny = _load_font(12)

    margin = 18
    city = data.get("city", "Unknown City")
    day_label = _format_display_date(data.get("date")) or data.get("date_label") or "Today"
    entries = _filter_forecast_window(data.get("forecast", []))
    high_low_entries = _filter_forecast_window(entries, start_hour=8)

    recommendation_low_temp = _forecast_number(high_low_entries, "temp", min)
    low_temp = recommendation_low_temp
    if low_temp == "--":
        low_temp = data.get("min_temp")
    low_time = data.get("min_temp_time") or _forecast_time_for(high_low_entries, "temp", min)

    recommendation_high_temp = _forecast_number(high_low_entries, "temp", max)
    high_temp = recommendation_high_temp
    if high_temp == "--":
        high_temp = data.get("max_temp")
    high_time = data.get("max_temp_time") or _forecast_time_for(high_low_entries, "temp", max)

    max_pop = data.get("max_pop")
    if max_pop in (None, "--"):
        max_pop = _forecast_number(entries, "pop", max)

    max_wind = data.get("max_wind")
    if max_wind in (None, "--"):
        max_wind = _forecast_number(entries, "wind", max)

    sunset = data.get("sunset")
    night_temp = data.get("night_temp")
    if night_temp in (None, "--"):
        night_temp = _forecast_temp_after(entries, sunset)

    has_rain, rain_start, rain_stop = _rain_timing(entries, max_pop)
    summary = data.get("summary") or make_daily_recommendation(
        max_pop,
        max_wind,
        recommendation_low_temp,
        recommendation_high_temp,
        night_temp,
    )

    # Header
    header_title = "GOOD MORNING UWU"
    draw.text((margin, margin), header_title, font=font_title, fill=0)
    current_time = data.get("time") or datetime.now().strftime("%H:%M")
    time_w, _ = _text_size(draw, current_time, font_header)
    draw.text(((width - time_w) / 2, margin + 6), current_time, font=font_header, fill=0)
    day_w, _ = _text_size(draw, day_label, font_header)
    draw.text((width - margin - day_w, margin + 6), day_label, font=font_header, fill=0)
    draw.line((margin, margin + 42, width - margin, margin + 42), fill=0)

    # Lead condition icon and practical summary
    lead_condition = data.get("condition")
    if not lead_condition and entries:
        lead_condition = max(entries, key=lambda entry: _as_number(entry.get("pop")) or 0).get("condition")
    lead_condition = lead_condition or "Clouds"

    icon_size = 82
    icon_y = margin + 58
    image.paste(get_icon(lead_condition, (icon_size, icon_size)), (margin, icon_y))

    summary_x = margin + icon_size + 18
    for idx, line in enumerate(_wrap_text(draw, summary, font_medium, width - summary_x - margin, max_lines=2)):
        draw.text((summary_x, icon_y + 18 + idx * 23), line, font=font_medium, fill=0)

    # Four signal cards: rain, high, low, wind.
    card_top = icon_y + icon_size + 18
    gap = 10
    card_w = (width - margin * 2 - gap * 3) // 4
    card_h = 92
    cards = [
        ("Rain starts" if has_rain else "Rain", rain_start, rain_stop, "rain"),
        ("High", _format_value(high_temp, "°C"), f"At {high_time}", "clear"),
        ("Low", _format_value(low_temp, "°C"), f"At {low_time}", "snow"),
        ("Wind", _wind_label(max_wind), "", "wind"),
    ]

    for idx, (label, value, detail, icon_condition) in enumerate(cards):
        x0 = margin + idx * (card_w + gap)
        x1 = x0 + card_w
        y0 = card_top
        y1 = y0 + card_h
        is_rain = icon_condition == "rain" and _as_number(max_pop) is not None and max_pop >= 35
        if is_rain:
            draw.rectangle((x0, y0, x1, y1), outline=0, fill=0)
            fill = 255
        else:
            draw.rectangle((x0, y0, x1, y1), outline=0)
            fill = 0

        draw.text((x0 + 8, y0 + 6), label, font=font_medium, fill=fill)
        value_font = font_large if _text_size(draw, value, font_large)[0] <= card_w - 16 else font_header
        value_lines = _wrap_text(draw, value, value_font, card_w - 16, max_lines=1)
        draw.text((x0 + 8, y0 + 30), value_lines[0], font=value_font, fill=fill)
        if detail:
            detail_font = font_medium if _text_size(draw, detail, font_medium)[0] <= card_w - 16 else font_small
            detail_lines = _wrap_text(draw, detail, detail_font, card_w - 16, max_lines=1)
            draw.text((x0 + 8, y1 - 30), detail_lines[0], font=detail_font, fill=fill)

    # Hourly forecast strip
    strip_top = card_top + card_h + 34
    draw.text((margin, strip_top), "Forecasts", font=font_header, fill=0)
    timeline_top = strip_top + 30
    timeline_h = 130

    max_boxes = 8
    if len(entries) > max_boxes:
        step = float(len(entries)) / max_boxes
        entries_to_draw = [entries[int(i * step)] for i in range(max_boxes)]
    else:
        entries_to_draw = entries

    if not entries_to_draw:
        entries_to_draw = [{"time": "--:--", "temp": "--", "condition": lead_condition, "pop": "--", "wind": "--"}]

    box_w = (width - margin * 2) // len(entries_to_draw)
    for idx, entry in enumerate(entries_to_draw):
        x0 = margin + idx * box_w
        x1 = margin + (idx + 1) * box_w - 4
        pop = _as_number(entry.get("pop"))
        rainy = pop is not None and pop >= 35
        if rainy:
            draw.rectangle((x0, timeline_top, x1, timeline_top + timeline_h), fill=0)
            fill = 255
        else:
            draw.rectangle((x0, timeline_top, x1, timeline_top + timeline_h), outline=0)
            fill = 0

        _center_text(draw, (x0, timeline_top + 8, x1, timeline_top + 32), entry.get("time", "--:--"), font_medium, fill=fill)
        icon_size = 44
        icon = get_icon(entry.get("condition", lead_condition), (icon_size, icon_size))
        if rainy:
            inverted = Image.eval(icon.convert("1"), lambda px: 255 - px)
            image.paste(inverted, (x0 + (x1 - x0 - icon_size) // 2, timeline_top + 38))
        else:
            image.paste(icon, (x0 + (x1 - x0 - icon_size) // 2, timeline_top + 38))
        _center_text(draw, (x0, timeline_top + 84, x1, timeline_top + 106), _format_value(entry.get("temp"), "°"), font_header, fill=fill)
        _center_text(draw, (x0, timeline_top + 108, x1, timeline_top + 128), _format_value(entry.get("pop"), "%"), font_medium, fill=fill)

    return image


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
