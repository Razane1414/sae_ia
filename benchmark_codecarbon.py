import os
import time
from statistics import mean
from PIL import Image
from codecarbon import OfflineEmissionsTracker

from core.ai import generate_caption
from core.stickers import detourer_sujet, ajouter_contour  
COUNTRY = "FRA"
N_RUNS = 10
TEST_IMAGE_PATH = os.path.join("tests", "images_test.jpg")


def measure_many(label: str, output_file: str, fn, n=N_RUNS, warmup=True):
    # warmup (hors mesure)
    if warmup:
        _ = fn()

    os.makedirs("emissions", exist_ok=True)

    tracker = OfflineEmissionsTracker(
        country_iso_code=COUNTRY,
        project_name=label,
        output_dir="emissions",
        output_file=output_file,
        log_level="error",
    )

    times = []
    last_result = None

    tracker.start()
    for _ in range(n):
        t0 = time.perf_counter()
        last_result = fn()
        times.append(time.perf_counter() - t0)
    kg_total = tracker.stop()

    return mean(times), (kg_total / n), last_result


def main():
    if not os.path.exists(TEST_IMAGE_PATH):
        raise FileNotFoundError(f"Image introuvable: {TEST_IMAGE_PATH}")

    img = Image.open(TEST_IMAGE_PATH).convert("RGB")

    # BLIP
    t, kg, cap = measure_many(
        "BLIP_caption",
        "blip_final.csv", 
        lambda: generate_caption(img),
        warmup=True
    )
    print("\nBLIP")
    print(f"- temps moyen: {t:.2f}s | emissions moy: {kg:.8f} kgCO2eq")
    print(f"- caption: {cap}")

    # REMBG (cutout)
    t, kg, _ = measure_many(
        "REMBG_cutout",
        "rembg_final.csv",
        lambda: detourer_sujet(img),
        warmup=True
    )
    print("\nREMBG (détourage)")
    print(f"- temps moyen: {t:.2f}s | emissions moy: {kg:.8f} kgCO2eq")

    # Pipeline complet
    def full():
        cap2 = generate_caption(img)
        cut2 = detourer_sujet(img)
        sticker = ajouter_contour(cut2, stroke_px=18)
        return cap2, sticker.size

    t, kg, out = measure_many(
        "FULL_pipeline",
        "full_final.csv", 
        full,
        warmup=True
    )
    print("\nFULL pipeline")
    print(f"- temps moyen: {t:.2f}s | emissions moy: {kg:.8f} kgCO2eq")
    print(f"- exemple: {out}")

    print("\nCSV dans ./emissions : blip.csv, rembg.csv, full.csv")


if __name__ == "__main__":
    main()
