from PIL import Image, ImageDraw, ImageFont

def create_weather_screen(data, width, height):
    image = Image.new("1", (width, height), 255)
    draw = ImageDraw.Draw(image)

    # Fonts (default safe choice)
    font_large = ImageFont.load_default()
    font_med = ImageFont.load_default()
    font_small = ImageFont.load_default()

    # ===== HEADER =====
    draw.text((10, 10), f"{data['city']}", font=font_med, fill=0)
    draw.text((width - 80, 10), data['time'], font=font_small, fill=0)

    # ===== MAIN WEATHER =====
    draw.text((20, 80), f"{data['temp']}°C", font=font_large, fill=0)
    draw.text((20, 120), data['condition'], font=font_med, fill=0)

    # ===== STATS =====
    draw.text((20, 200),
              f"Feels: {data['feels']}°C   Wind: {data['wind']} km/h",
              font=font_small,
              fill=0)

    # ===== RECOMMENDATION =====
    draw.text((20, 260),
              data['recommendation'],
              font=font_med,
              fill=0)

    return image
