# -*- coding: utf-8 -*-
"""Optimize assets: back up originals, resize (char/item/island 512px, bg 1280px),
quantize to 256 colors. Idempotent: skips files already at target size.
Also removes codex intermediate files (-source/-chroma/-key)."""
import os, sys, shutil
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from manifest import build

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "tools", "raw_backup")

def cleanup_intermediates():
    removed = 0
    for sub in ["assets/char", "assets/item", "assets/bg"]:
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            low = f.lower()
            if any(k in low for k in ["-source", "-chroma", "-key", "_source", "_chroma", "_key"]):
                os.remove(os.path.join(d, f)); removed += 1
    print(f"removed {removed} intermediate files")

def optimize(asset):
    rel = asset["file"]
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return (rel, "missing", 0, 0)
    target = 1280 if (rel.startswith("assets/bg/bg_")) else 512
    before = os.path.getsize(p)
    im = Image.open(p); im.load()
    if max(im.size) <= target and before < 400_000:
        return (rel, "skip", before, before)
    # backup original once
    os.makedirs(os.path.join(RAW, os.path.dirname(rel)), exist_ok=True)
    bak = os.path.join(RAW, rel)
    if not os.path.exists(bak):
        shutil.copy2(p, bak)
    scale = target / max(im.size)
    if scale < 1:
        im = im.resize((round(im.size[0]*scale), round(im.size[1]*scale)), Image.LANCZOS)
    if asset["transparent"]:
        im = im.convert("RGBA")
        q = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
    else:
        q = im.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    q.save(p, optimize=True)
    after = os.path.getsize(p)
    return (rel, "ok", before, after)

def main():
    cleanup_intermediates()
    tb = ta = 0
    for a in build():
        rel, st, b, aft = optimize(a)
        tb += b; ta += aft
        if st != "skip":
            print(f"{st:7s} {rel:36s} {b//1024:5d}KB -> {aft//1024:5d}KB")
    print(f"TOTAL {tb/1048576:.1f}MB -> {ta/1048576:.1f}MB")

if __name__ == "__main__":
    main()
