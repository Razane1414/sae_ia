import os
import uuid
from PIL import Image, ImageDraw, ImageFilter, ImageChops

from .ai import remove_background



# background removal
def detourer_sujet(img_rgb: Image.Image) -> Image.Image:
    """Retourne un PNG RGBA avec fond transparent (avec rembg)."""
    if img_rgb.mode != "RGB":
        img_rgb = img_rgb.convert("RGB")
    return remove_background(img_rgb)

# sticker
def ajouter_contour(image_rgba: Image.Image, stroke_px: int = 10, color=(255, 255, 255, 255)) -> Image.Image:
    """
    Ajoute un contour type sticker autour du sujet.
    - image_rgba : image avec transparence (RGBA)
    - epaisseur  : épaisseur du contour en pixels
    - couleur    : couleur du contour (RGBA)
    """
    image_rgba = image_rgba.convert("RGBA")
    
    # alpha : le masque de transparence : 0 = transparent, 255 = opaque
    alpha = image_rgba.split()[-1]

    # on dilate le masque alpha pour créer le contour
    dilated = alpha.filter(ImageFilter.MaxFilter(stroke_px * 2 + 1))

    masque_contour  = ImageChops.subtract(dilated, alpha)
    masque_contour  = masque_contour .filter(ImageFilter.GaussianBlur(1)) 

    contour = Image.new("RGBA", image_rgba.size, color)
    contour.putalpha(masque_contour )

    out = Image.new("RGBA", image_rgba.size, (0, 0, 0, 0))
    out.alpha_composite(contour)
    out.alpha_composite(image_rgba)
    return out




# badge
def creer_fond(size: int, theme: str = "pink") -> Image.Image:
    themes = {
        "pink": ((255, 90, 160, 255), (255, 255, 255, 85)),
        "dark": ((20, 20, 30, 255), (255, 255, 255, 70)),
        "mint": ((60, 220, 180, 255), (255, 255, 255, 85)),
    }
    base, glow = themes.get(theme, themes["pink"])

    bg = Image.new("RGBA", (size, size), base)
    halo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(halo)
    draw.ellipse([40, 40, size - 40, size - 40], fill=glow)
    halo = halo.filter(ImageFilter.GaussianBlur(35))
    bg.alpha_composite(halo)
    return bg

def creer_badge(img_rgb: Image.Image, size: int = 512, theme: str = "dark") -> Image.Image:
    """
    Crée un badge rond avec le sujet centré sur un fond coloré.
    - img_rgb : image RGB d'entrée
    - size    : taille du badge (largeur=hauteur)           
    - theme   : thème de couleur du fond ("pink", "dark", "mint")
    """
    cut = detourer_sujet(img_rgb)
    cut = cut.copy()
    cut.thumbnail((size, size), Image.LANCZOS)

    bg = creer_fond(size, theme=theme)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(bg)

    x = (size - cut.size[0]) // 2
    y = (size - cut.size[1]) // 2
    canvas.alpha_composite(cut, (x, y))

    masque_rond = Image.new("L", (size, size), 0)
    dm = ImageDraw.Draw(masque_rond)
    dm.ellipse([10, 10, size - 10, size - 10], fill=255)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(canvas, (0, 0), masque_rond)

    border = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    db = ImageDraw.Draw(border)
    db.ellipse([10, 10, size - 10, size - 10], outline=(255, 255, 255, 255), width=12)
    out.alpha_composite(border)

    return out


def main(pil_rgb: Image.Image, out_dir: str, base_name: str, mode: str = "sticker", theme: str = "dark"):
    os.makedirs(out_dir, exist_ok=True)
    base = uuid.uuid4().hex
    paths = []

    if mode == "bg":
        cut = detourer_sujet(pil_rgb)
        p = os.path.join(out_dir, f"{base}_cutout.png")
        cut.save(p)
        paths.append(p)

    elif mode == "badge":
        badge = creer_badge(pil_rgb, size=512, theme=theme)
        p = os.path.join(out_dir, f"{base}_badge_{theme}.png")
        badge.save(p)
        paths.append(p)

    else:  # "sticker"
        cut = detourer_sujet(pil_rgb)
        sticker = ajouter_contour(cut, stroke_px=18, color=(255, 255, 255, 255))

        p1 = os.path.join(out_dir, f"{base}_cutout.png")
        p2 = os.path.join(out_dir, f"{base}_sticker.png")

        cut.save(p1)
        sticker.save(p2)
        paths.extend([p1, p2])

    return paths
