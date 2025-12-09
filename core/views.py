from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from PIL import Image
import os

from .forms import UploadImageForm
from .ai import generate_caption
from .stickers import main

SESSION_KEY = "sticker_state"

THEMES = ["dark","pink", "mint"]  #choix badge

def _reset_state(request):
    request.session.pop(SESSION_KEY, None)

def home(request):
    if request.GET.get("reset") == "1":
        _reset_state(request)
        return redirect("home")

    state = request.session.get(SESSION_KEY)
    upload_form = UploadImageForm()

    # Upload l'image
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

            request.session[SESSION_KEY] = {
                "filename": filename,
                "image_url": image_url,
                "caption": caption,
                "step": "choose_mode",
                "mode": None,
                "theme": "dark",
                "output_urls": [],
            }
            request.session.modified = True
            return redirect("home")

    # choix du mode
    if request.method == "POST" and request.POST.get("mode") and state and state.get("step") == "choose_mode":
        mode = request.POST.get("mode")
        state["mode"] = mode

        # si badge alors on dmd le le thème
        if mode == "badge":
            state["step"] = "choose_theme"
            request.session[SESSION_KEY] = state
            request.session.modified = True
            return redirect("home")

        # sinon on génère direct
        img_path = os.path.join(settings.MEDIA_ROOT, state["filename"])
        pil_img = Image.open(img_path).convert("RGB")

        out_dir = os.path.join(settings.MEDIA_ROOT, "outputs")
        paths = main(pil_img, out_dir, state["filename"], mode=mode)

        state["output_urls"] = [settings.MEDIA_URL + "outputs/" + os.path.basename(p) for p in paths]
        state["step"] = "done"

        request.session[SESSION_KEY] = state
        request.session.modified = True
        return redirect("home")

    # choix thème (badge)
    if request.method == "POST" and request.POST.get("theme") and state and state.get("step") == "choose_theme":
        theme = request.POST.get("theme")
        if theme not in THEMES:
            theme = "dark"

        img_path = os.path.join(settings.MEDIA_ROOT, state["filename"])
        pil_img = Image.open(img_path).convert("RGB")

        out_dir = os.path.join(settings.MEDIA_ROOT, "outputs")
        paths = main(pil_img, out_dir, state["filename"], mode="badge", theme=theme)

        # mettre à jour la session
        state["theme"] = theme
        state["output_urls"] = [settings.MEDIA_URL + "outputs/" + os.path.basename(p) for p in paths] 
        state["step"] = "done"

        request.session[SESSION_KEY] = state
        request.session.modified = True
        return redirect("home")
    # afficher la page
    return render(request, "core/home.html", {
        "upload_form": upload_form,
        "state": state,
        "themes": THEMES,
    })
