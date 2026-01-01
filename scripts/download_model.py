#!/usr/bin/env python3
import sys
from mlx_lm import load

def download_model():
    """
    Downloads the Gemma model for MLX.
    Using 'mlx-community/gemma-2-2b-it-4bit' as the default lightweight model.
    """
    model_id = "mlx-community/gemma-2-2b-it-4bit"
    print(f"Start downloading model: {model_id}...")
    try:
        # load() functions triggers the download if not cached
        load(model_id)
        print(f"✅ Model {model_id} downloaded successfully.")
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_model()
