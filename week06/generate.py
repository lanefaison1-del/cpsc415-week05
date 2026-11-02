"""Generate an image set through OpenRouter's Image API and write a manifest (spec.md, Week 6).

    python generate.py prompts.json --out images                       # five FLUX images, needs OPENROUTER_API_KEY
    python generate.py prompts.json --out images-seed --only fernkit   # the seed check: one image
    python generate.py prompts.json --out images-nb --only fernkit --model google/gemini-3.1-flash-lite-image

One billed call per prompt. The manifest records prompt, seed, model, media type, file, and the
cost from the reply for every image, so the critic and the checker never guess what was asked for.
"""
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

DEFAULT_MODEL = "black-forest-labs/flux.2-klein-4b"
EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def generate_one(client, model: str, prompt: str, seed: int, aspect_ratio: str = "1:1") -> dict:
    """One Image API call (the SDK posts to /api/v1/images): image bytes, media type, cost."""
    r = client.images.generate(model=model, prompt=prompt, aspect_ratio=aspect_ratio, seed=seed)
    if not getattr(r, "data", None):
        raise RuntimeError(f"{model} returned no image for this prompt")
    item = r.data[0]
    cost = getattr(r.usage, "cost", None) if r.usage is not None else None
    return {"bytes": base64.b64decode(item.b64_json), "media_type": item.media_type, "cost": cost}


def run(client, prompts: list, out: Path, model: str, aspect_ratio: str = "1:1",
        only: str | None = None) -> list:
    """Generate each prompt once (or only the named one), save the images, write manifest.json."""
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for p in prompts:
        if only and p["name"] != only:
            continue
        t0 = time.time()
        g = generate_one(client, model, p["prompt"], p["seed"], aspect_ratio)
        path = out / f"{p['name']}.{EXT.get(g['media_type'], 'bin')}"
        path.write_bytes(g["bytes"])
        entry = {**p, "model": model, "aspect_ratio": aspect_ratio, "file": path.name,
                 "media_type": g["media_type"], "cost": g["cost"], "seconds": round(time.time() - t0, 1)}
        manifest.append(entry)
        # Written after every image: a failure later in the run keeps the record of what was paid for.
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"{path}  {g['media_type']}  seed={p['seed']}  ${g['cost']}  {entry['seconds']}s")
    return manifest


def summary(manifest: list) -> str:
    """Image count and total cost, saying how many replies carried no cost instead of counting $0."""
    missing = sum(1 for e in manifest if e["cost"] is None)
    total = sum(e["cost"] for e in manifest if e["cost"] is not None)
    return f"{len(manifest)} image(s), ${total:.4f} total" + (
        f", cost missing for {missing} image(s)" if missing else "")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("prompts", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--model", default=os.environ.get("IMAGE_MODEL", DEFAULT_MODEL))
    ap.add_argument("--aspect-ratio", default="1:1")
    ap.add_argument("--only", help="generate just the prompt with this name")
    args = ap.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set; image generation is a billed call. Nothing generated.")
    # Imported here so the no-key path and the tests never need the SDK.
    from openrouter import OpenRouter

    manifest = run(OpenRouter(api_key=key), json.loads(args.prompts.read_text()), args.out,
                   args.model, args.aspect_ratio, args.only)
    print(summary(manifest))


if __name__ == "__main__":
    main()
