from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from PIL import Image
import os

from .forms import UploadImageForm
from .ai import generate_caption
from .stickers import generate_stickers

SESSION_KEY = "sticker_state"

def _reset_state(request):
    request.session.pop(SESSION_KEY, None)

def _save_state(request, state):
    request.session[SESSION_KEY] = state
    request.session.modified = True

def home(request):
    if request.GET.get("reset") == "1":
        _reset_state(request)
        return redirect("home")

    state = request.session.get(SESSION_KEY)
    upload_form = UploadImageForm()

    if request.method == "POST" and request.FILES.get("image"):
        upload_form = UploadImageForm(request.POST, request.FILES)
        if upload_form.is_valid():
            image_file = upload_form.cleaned_data["image"]

            fs = FileSystemStorage()
            filename = fs.save(image_file.name, image_file)
            image_url = fs.url(filename)

            image_file.seek(0)
            pil_img = Image.open(image_file).convert("RGB")

            caption = generate_caption(pil_img)

            # stickers output dans MEDIA_ROOT/stickers
            stickers_dir = os.path.join(settings.MEDIA_ROOT, "stickers")
            paths = generate_stickers(pil_img, caption, stickers_dir, filename)

            sticker_urls = [
                settings.MEDIA_URL + "stickers/" + os.path.basename(p)
                for p in paths
            ]

            state = {
                "image_url": image_url,
                "caption": caption,
                "sticker_urls": sticker_urls,
            }
            _save_state(request, state)
            return redirect("home")

    return render(request, "core/home.html", {
        "upload_form": upload_form,
        "state": state,
    })
