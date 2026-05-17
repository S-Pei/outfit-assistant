import sys
import os

libdir = os.path.join(os.path.dirname(__file__), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd5in83_V2
from PIL import Image, ImageDraw

epd = epd5in83_V2.EPD()
epd.init()
epd.Clear()

img = create_weather_screen(data, 648, 480)

# 3. SEND TO DISPLAY (THIS IS THE IMPORTANT PART)
epd.display(epd.getbuffer(img))

# 4. Sleep display (important for e-paper)
epd.sleep()
