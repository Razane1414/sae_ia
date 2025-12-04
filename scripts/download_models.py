"""
Pré-télécharge les modèles Hugging Face utilisés par Yummy.
Usage:
    python scripts/download_models.py
Cela téléchargera les modèles BLIP et FLAN et les stockera dans le cache de Hugging Face.
"""

import sys
from transformers import (
    AutoProcessor,
    AutoModelForVision2Seq,
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
)

BLIP_MODEL_ID = "Salesforce/blip-image-captioning-base"
FLAN_MODEL_ID = "google/flan-t5-small"


def download_blip():
    print(f"Download BLIP: {BLIP_MODEL_ID}")
    AutoProcessor.from_pretrained(BLIP_MODEL_ID)
    AutoModelForVision2Seq.from_pretrained(BLIP_MODEL_ID)
    print("BLIP OK\n")


def download_flan():
    print(f"Download FLAN: {FLAN_MODEL_ID}")
    AutoTokenizer.from_pretrained(FLAN_MODEL_ID)
    AutoModelForSeq2SeqLM.from_pretrained(FLAN_MODEL_ID)
    print("FLAN OK\n")


def main():
    try:
        download_blip()
        download_flan()
        print("Tous les modèles sont téléchargés et en cache.")
    except Exception as e:
        print("\n Erreur pendant le téléchargement :", repr(e), file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
