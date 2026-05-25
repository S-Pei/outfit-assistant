import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WAVESHARE_EPD_LIB = Path("/home/cutiepi/e-Paper/RaspberryPi_JetsonNano/python/lib")


def _add_sys_path(path):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.append(path_text)


def _add_waveshare_driver_paths():
    env_path = os.getenv("WAVESHARE_EPD_LIB")
    candidates = [
        Path(env_path) if env_path else None,
        DEFAULT_WAVESHARE_EPD_LIB,
        REPO_ROOT / "lib",
        REPO_ROOT / "vendor" / "e-Paper" / "RaspberryPi_JetsonNano" / "python" / "lib",
        REPO_ROOT.parent / "e-Paper" / "RaspberryPi_JetsonNano" / "python" / "lib",
        Path.home() / "e-Paper" / "RaspberryPi_JetsonNano" / "python" / "lib",
        Path.home() / "projects" / "e-Paper" / "RaspberryPi_JetsonNano" / "python" / "lib",
    ]

    for path in candidates:
        if path and (path / "waveshare_epd").is_dir():
            _add_sys_path(path)


def _import_epaper_driver():
    _add_waveshare_driver_paths()
    from waveshare_epd import epd5in83_V2

    return epd5in83_V2


def get_epaper_dimensions():
    try:
        epd5in83_V2 = _import_epaper_driver()
    except ImportError:
        return None

    epd = epd5in83_V2.EPD()
    try:
        epd.init()
    except Exception:
        pass
    return getattr(epd, "width", None), getattr(epd, "height", None)


def display_on_epaper(image, clear=False):
    try:
        epd5in83_V2 = _import_epaper_driver()
    except ImportError as exc:
        raise RuntimeError(
            "Waveshare e-paper driver path was not found. Set WAVESHARE_EPD_LIB "
            "to the directory containing the waveshare_epd package, for example "
            "/home/cutiepi/e-Paper/RaspberryPi_JetsonNano/python/lib"
        ) from exc

    epd = epd5in83_V2.EPD()
    epd.init()
    if clear:
        epd.Clear()
    epd.display(epd.getbuffer(image))
    epd.sleep()
    print("Sent image to e-paper display")
