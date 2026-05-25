from pathlib import Path

from PIL import Image


def save_preview(image, filename, scale=1):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    if scale == 1:
        image.save(path)
        print(f"Saved preview image: {path}")
        return str(path)

    scaled = image.resize((image.width * scale, image.height * scale), resample=Image.NEAREST)
    scaled_path = path.with_name(f"{path.stem}@{scale}x{path.suffix}")
    scaled.save(scaled_path)
    print(f"Saved scaled debug preview image: {scaled_path}")
    return str(scaled_path)

