from PIL import Image, ImageDraw
import math
from pathlib import Path


ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets" / "icons"


def _load_asset(name, size):
    path = ASSETS_DIR / name
    if path.is_file():
        img = Image.open(path)
        # If image has alpha, create a silhouette from alpha mask
        if img.mode == "RGBA" or (hasattr(img, "getchannel") and "A" in img.getbands()):
            rgba = img.convert("RGBA")
            alpha = rgba.split()[3]
            mask = alpha.resize((int(size[0]), int(size[1])), Image.LANCZOS)
            # threshold alpha to create solid mask
            mask = mask.point(lambda a: 255 if a > 32 else 0).convert("1")
            result = Image.new("1", (int(size[0]), int(size[1])), 255)
            result.paste(0, (0, 0), mask)
            return result
        else:
            # fallback: convert by luminance
            gray = img.convert("L")
            gray = gray.resize((int(size[0]), int(size[1])), Image.LANCZOS)
            bw = gray.point(lambda x: 0 if x < 128 else 255, '1')
            return bw
    return None


def get_icon(condition, size):
    cond = (condition or "").lower()
    # map keywords to filenames
    if "sun" in cond or "clear" in cond:
        asset = "clear.png"
    elif "rain" in cond or "drizzle" in cond:
        asset = "rain.png"
    elif "snow" in cond:
        asset = "snow.png"
    elif "thunder" in cond:
        asset = "thunderstorm.png"
    elif "mist" in cond or "fog" in cond:
        asset = "mist.png"
    else:
        asset = "clouds.png"

    img = _load_asset(asset, size)
    if img:
        return img

    # fallback: programmatic simple icons
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    img = Image.new("1", (w, h), 255)
    draw = ImageDraw.Draw(img)

    pad = int(min(w, h) * 0.08)
    iw = w - pad * 2
    ih = h - pad * 2
    ix = pad
    iy = pad

    if "sun" in cond or "clear" in cond:
        r = int(min(iw, ih) * 0.28)
        cx = ix + iw // 2
        cy = iy + ih // 2
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=0)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x2 = cx + int((r + max(4, r // 2)) * math.cos(rad))
            y2 = cy + int((r + max(4, r // 2)) * math.sin(rad))
            draw.line((cx, cy, x2, y2), fill=0)
    elif "rain" in cond or "drizzle" in cond:
        cw = int(iw * 0.78)
        ch = int(ih * 0.48)
        cx = ix + (iw - cw) // 2
        cy = iy + int(ih * 0.12)
        draw.ellipse((cx, cy, cx + cw // 2, cy + ch), fill=0)
        draw.ellipse((cx + cw // 4, cy - ch // 4, cx + cw * 3 // 4, cy + ch), fill=0)
        draw.ellipse((cx + cw // 2, cy, cx + cw, cy + ch), fill=0)
        draw.rectangle((cx + cw // 8, cy + ch // 2, cx + cw * 7 // 8, cy + ch), fill=0)
        drops_x = [cx + cw // 4, cx + cw // 2, cx + cw * 3 // 4]
        for dx in drops_x:
            draw.line((dx, cy + ch + 4, dx, cy + ch + 14), fill=0, width=2)
    else:
        cw = int(iw * 0.78)
        ch = int(ih * 0.56)
        cx = ix + (iw - cw) // 2
        cy = iy + int(ih * 0.2)
        draw.ellipse((cx, cy, cx + cw // 2, cy + ch), fill=0)
        draw.ellipse((cx + cw // 4, cy - ch // 6, cx + cw * 3 // 4, cy + ch), fill=0)
        draw.ellipse((cx + cw // 2, cy, cx + cw, cy + ch), fill=0)
        draw.rectangle((cx + cw // 8, cy + ch // 2, cx + cw * 7 // 8, cy + ch), fill=0)

    return img
