import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.platform import is_raspberry_pi
from display.epaper import display_on_epaper, get_epaper_dimensions
from display.preview import save_preview

ASSETS_DIR = REPO_ROOT / "assets" / "epaper"


def cover_crop(image, size):
    target_w, target_h = size
    source_w, source_h = image.size
    scale = max(target_w / source_w, target_h / source_h)
    resized = image.resize((round(source_w * scale), round(source_h * scale)), Image.Resampling.LANCZOS)

    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def convert_for_epaper(path, size, dither=True):
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Image not found: {source_path}")

    image = Image.open(source_path)
    image = ImageOps.exif_transpose(image).convert("RGB")
    image = cover_crop(image, size)
    image = ImageOps.autocontrast(image.convert("L"))

    if dither:
        return image.convert("1", dither=Image.Dither.FLOYDSTEINBERG)

    return image.point(lambda pixel: 0 if pixel < 150 else 255).convert("1")


def parse_args():
    parser = argparse.ArgumentParser(description="Render a real image on the e-paper display.")
    parser.add_argument("image", help="Path to the image file to render.")
    parser.add_argument("--width", type=int, default=648, help="Preview/render width when not using Pi dimensions.")
    parser.add_argument("--height", type=int, default=480, help="Preview/render height when not using Pi dimensions.")
    parser.add_argument("--no-dither", action="store_true", help="Use a hard threshold instead of dithering.")
    return parser.parse_args()


def main():
    args = parse_args()
    on_pi = is_raspberry_pi()
    epaper_dims = get_epaper_dimensions() if on_pi else None
    size = epaper_dims if epaper_dims and all(epaper_dims) else (args.width, args.height)

    image = convert_for_epaper(args.image, size, dither=not args.no_dither)

    if on_pi:
        display_on_epaper(image)
    else:
        output_path = ASSETS_DIR / f"{Path(args.image).stem}.png"
        save_preview(image, filename=str(output_path), scale=1)


if __name__ == "__main__":
    main()
