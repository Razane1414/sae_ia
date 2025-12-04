from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .forms import UploadImageForm

def home(request):
    image_url = None
    result = None

    if request.method == "POST":
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data["image"]

            fs = FileSystemStorage()
            filename = fs.save(image.name, image)
            image_url = fs.url(filename)

            result = "upload fonctionne bien, prochainement : appel IA"
    else:
        form = UploadImageForm()

    return render(request, "core/home.html", {"form": form, "image_url": image_url, "result": result})
