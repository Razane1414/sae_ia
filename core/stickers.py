import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from matplotlib.pyplot import draw

from .ai import remove_background 

#_slug génère un nom de fichier "propre" : partir du nom original
def _slug(name: str) -> str:
    name = (name or "").lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name) # remplace les caractères non alphanumériques par des tirets
    return (name.strip("-")[:60] or "sticker")

def make_cutout(pil_rgb: Image.Image) -> Image.Image:
    """
    Retourne un PNG RGBA avec fond transparent (via rembg).
    """
    if pil_rgb.mode != "RGB":
        pil_rgb = pil_rgb.convert("RGB")
    return remove_background(pil_rgb)

def add_outline(cut_rgba: Image.Image, stroke_px: int = 18) -> Image.Image:
    """
    Ajoute un contour type sticker autour du sujet.
    (Contour blanc par défaut)
    """
    cut_rgba = cut_rgba.convert("RGBA")
    alpha = cut_rgba.split()[-1]

    # dilation du masque alpha
    dilated = alpha.filter(ImageFilter.MaxFilter(stroke_px * 2 + 1))
    outline_mask = ImageChops.subtract(dilated, alpha)
    outline_mask = outline_mask.filter(ImageFilter.GaussianBlur(1))


    outline = Image.new("RGBA", cut_rgba.size, (255, 255, 255, 255))
    outline.putalpha(outline_mask)

    out = Image.new("RGBA", cut_rgba.size, (0, 0, 0, 0))
    out.alpha_composite(outline)
    out.alpha_composite(cut_rgba)
    return out



def make_label_sticker(sticker_rgba: Image.Image, caption: str) -> Image.Image:
    """
    Ajoute une étiquette texte (caption) sous le sticker.
    """
    sticker_rgba = sticker_rgba.convert("RGBA")
    w, h = sticker_rgba.size

    pad = 40
    label_h = 100
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2 + label_h), (0, 0, 0, 0))
    canvas.alpha_composite(sticker_rgba, (pad, pad))

    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    text = (caption or "").strip()
    if len(text) > 70:
        text = text[:67] + "…"

    # bandeau semi-transparent
    y0 = h + pad + 15
    
    draw.rounded_rectangle([pad, y0, w + pad, y0 + 70], radius=16, fill=(255,255,255,220))
    draw.text((pad + 14, y0 + 20), text, font=font, fill=(10,10,10,255))

    return canvas



def trim_transparent(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    bbox = img.getbbox()
    if not bbox:
        return img
    return img.crop(bbox)

def center_on_canvas(img: Image.Image, size=(512, 512), margin=40) -> Image.Image:
    img = img.convert("RGBA")
    img = trim_transparent(img)

    w, h = img.size
    max_w, max_h = size[0] - 2*margin, size[1] - 2*margin
    scale = min(max_w / w, max_h / h, 1.0)
    img = img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", size, (0,0,0,0))
    x = (size[0] - img.size[0]) // 2
    y = (size[1] - img.size[1]) // 2
    canvas.alpha_composite(img, (x, y))
    return canvas


def generate_stickers(pil_rgb: Image.Image, caption: str, out_dir: str, base_name: str):
    """
    Génère 3 PNG :
    - cutout (fond transparent)
    - outline (contour sticker)
    - label (outline + caption)
    Retourne la liste des chemins.
    """
    os.makedirs(out_dir, exist_ok=True)
    base = _slug(base_name)
    cut = center_on_canvas(make_cutout(pil_rgb), size=(512, 512), margin=40)

    outline = add_outline(cut, stroke_px=18)
    label = make_label_sticker(outline, caption)

    p1 = os.path.join(out_dir, f"{base}_cutout.png")
    p2 = os.path.join(out_dir, f"{base}_outline.png")
    p3 = os.path.join(out_dir, f"{base}_label.png")

    cut.save(p1)
    outline.save(p2)
    label.save(p3)

    return [p1, p2, p3]
