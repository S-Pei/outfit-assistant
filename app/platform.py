import sys
from pathlib import Path


def is_raspberry_pi():
    model_path = Path("/proc/device-tree/model")
    if not model_path.exists():
        return False

    try:
        return "raspberry pi" in model_path.read_text(errors="ignore").lower()
    except OSError:
        return False


def read_key():
    if not sys.stdin.isatty():
        return sys.stdin.read(1)

    try:
        import termios
        import tty
    except ImportError:
        return input().strip()[:1]

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

