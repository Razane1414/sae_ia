from transformers import BlipProcessor, BlipForConditionalGeneration
from rembg import remove
from PIL import Image
import torch
import io
BLIP = None

def get_blip():
    global BLIP
    if BLIP is None:
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base", use_fast=False)
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        model.eval()
        BLIP = (processor, model)
    return BLIP

def generate_caption(image):
    processor, model = get_blip()
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=25)
    return processor.decode(out[0], skip_special_tokens=True)


# remove background avec rembg
def remove_background(pil_rgb: Image.Image) -> Image.Image: #-> Image.Image: enlever le type pour éviter l'erreur
    """
    Retourne une image RGBA avec fond transparent.
    """
    buf = io.BytesIO() #cree un buffer en memoire
    pil_rgb.save(buf, format="PNG") # sauvegarde l'image dans le buffer au format PNG
    out = remove(buf.getvalue()) # utilise rembg pour enlever le fond
    return Image.open(io.BytesIO(out)).convert("RGBA") 