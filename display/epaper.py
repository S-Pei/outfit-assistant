def get_epaper_dimensions():
    try:
        from waveshare_epd import epd5in83_V2
    except ImportError:
        return None

    epd = epd5in83_V2.EPD()
    try:
        epd.init()
    except Exception:
        pass
    return getattr(epd, "width", None), getattr(epd, "height", None)


def display_on_epaper(image):
    try:
        from waveshare_epd import epd5in83_V2
    except ImportError as exc:
        raise RuntimeError("Waveshare e-paper library not installed or path not found") from exc

    epd = epd5in83_V2.EPD()
    epd.init()
    epd.Clear()
    epd.display(epd.getbuffer(image))
    epd.sleep()
    print("Sent image to e-paper display")

