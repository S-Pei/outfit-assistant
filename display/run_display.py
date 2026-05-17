import sys
import os

# Add Waveshare library path
sys.path.append('/home/cutiepi/e-Paper/RaspberryPi_JetsonNano/python/lib')

from waveshare_epd import epd5in83_V2
from PIL import Image, ImageDraw
from screen import create_weather_screen

epd = epd5in83_V2.EPD()
epd.init()
epd.Clear()

data = {
    "city": "London",
    "time": "12:45",
    "temp": 14,
    "condition": "Cloudy",
    "feels": 12,
    "wind": 9,
    "recommendation": "Wear a hoodie today"
}

img = create_weather_screen(data, 648, 480)

img.show()
# 3. SEND TO DISPLAY (THIS IS THE IMPORTANT PART)
epd.display(epd.getbuffer(img))

# 4. Sleep display (important for e-paper)
epd.sleep()
