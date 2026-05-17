import sys
import os
from PIL import Image, ImageDraw, ImageFont

# Add Waveshare library path
sys.path.append('/home/cutiepi/e-Paper/RaspberryPi_JetsonNano/python/lib')

from waveshare_epd import epd5in83_V2

# -----------------------------
# SIMPLE UI FUNCTION
# -----------------------------
def create_weather_screen(data, width, height):
    image = Image.new("1", (width, height), 255)
    draw = ImageDraw.Draw(image)

    font = ImageFont.load_default()

    draw.text((20, 20), f"City: {data['city']}", font=font, fill=0)
    draw.text((20, 60), f"Temp: {data['temp']}C", font=font, fill=0)
    draw.text((20, 100), data['condition'], font=font, fill=0)

    return image

# -----------------------------
# TEST DATA
# -----------------------------
data = {
    "city": "London",
    "temp": 14,
    "condition": "Cloudy"
}

# -----------------------------
# INIT DISPLAY
# -----------------------------
epd = epd5in83_V2.EPD()

epd.init()
epd.Clear()

# -----------------------------
# CREATE IMAGE
# -----------------------------
img = create_weather_screen(data, epd.height, epd.width)

# -----------------------------
# DISPLAY IMAGE
# -----------------------------
epd.display(epd.getbuffer(img))

# -----------------------------
# SLEEP
# -----------------------------
epd.sleep()
