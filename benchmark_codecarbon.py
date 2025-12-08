import os
import time
from statistics import mean
from PIL import Image
from codecarbon import OfflineEmissionsTracker

from core.ai import generate_caption
from core.stickers import make_cutout, add_outline  # ou generate_stickers

COUNTRY = "FRA"
N_RUNS = 10
TEST_IMAGE_PATH = os.path.join("tests", "images_test.jpg")

def measure_many(label: str, output_file: str, fn, n=N_RUNS, warmup=True):
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
    img = Image.open(TEST_IMAGE_PATH).convert("RGB")

    # A) BLIP
    t, kg, cap = measure_many("BLIP_caption", "blip.csv", lambda: generate_caption(img))
    print("\nBLIP")
    print(f"- temps: {t:.2f}s | emissions: {kg:.8f} kgCO2eq")
    print(f"- caption: {cap}")

    # B) REMBG cutout (IA #2)
    t, kg, cut = measure_many("REMBG_cutout", "rembg.csv", lambda: make_cutout(img))
    print("\nREMBG (cutout)")
    print(f"- temps: {t:.2f}s | emissions: {kg:.8f} kgCO2eq")

    # C) FULL pipeline (caption -> cutout -> outline)
    def full():
        cap2 = generate_caption(img)
        cut2 = make_cutout(img)
        out2 = add_outline(cut2)
        return (cap2, out2.size)

    t, kg, out = measure_many("FULL_pipeline", "full.csv", full)
    print("\nFULL")
    print(f"- temps: {t:.2f}s | emissions: {kg:.8f} kgCO2eq")
    print(f"- exemple: {out}")

    print("\nCSV dans ./emissions : blip.csv, rembg.csv, full.csv")

if __name__ == "__main__":
    main()
