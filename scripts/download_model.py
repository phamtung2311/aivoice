#!/usr/bin/env python3
"""Download VieNeu TTS model locally using huggingface_hub.
This saves the model under ./models/<model-id> so inference can run offline.
"""
import argparse
from huggingface_hub import snapshot_download
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="pnnbao-ump/VieNeu-TTS-v2", help="Hugging Face model id to download")
    parser.add_argument("--out", default="models", help="Output directory to store model snapshot")
    args = parser.parse_args()

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    print(f"Downloading {args.model} to {out_dir} (this may take a while)...")
    path = snapshot_download(repo_id=args.model, cache_dir=out_dir)
    print("Downloaded files to:", path)


if __name__ == "__main__":
    main()
