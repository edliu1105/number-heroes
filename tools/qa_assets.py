# -*- coding: utf-8 -*-
"""Asset QA: automated checks (size / corner alpha / bbox coverage / edge halo)
+ contact sheets for visual inspection."""
import os, sys, json
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from manifest import build

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def qa(asset):
    rel = asset["file"]; p = os.path.join(ROOT, rel)
    issues = []
    if not os.path.exists(p):
        return ["MISSING"]
    im = Image.open(p); im.load()
    w, h = im.size
    if rel.startswith("assets/bg/bg_"):
        if w < 1000: issues.append(f"small {w}x{h}")
    elif max(w, h) < 500:
        issues.append(f"small {w}x{h}")
    if asset["transparent"]:
        rgba = im.convert("RGBA")
        a = rgba.split()[3]
        for xy in [(2,2),(w-3,2),(2,h-3),(w-3,h-3)]:
            if a.getpixel(xy) > 12: issues.append(f"corner opaque {xy}"); break
        bbox = a.point(lambda v: 255 if v > 16 else 0).getbbox()
        if not bbox:
            issues.append("empty")
        else:
            cov = (bbox[2]-bbox[0])*(bbox[3]-bbox[1])/(w*h)
            if cov < 0.20: issues.append(f"subject tiny cov={cov:.2f}")
            if cov > 0.985: issues.append(f"likely cropped cov={cov:.2f}")
            if bbox[0] <= 1 or bbox[1] <= 1 or bbox[2] >= w-1 or bbox[3] >= h-1:
                issues.append("touches edge (possible crop)")
    return issues

def contact_sheet(files, out, cols=6, cell=200, label=True):
    from PIL import ImageDraw
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols*cell, rows*(cell+18)), (245, 245, 250))
    d = ImageDraw.Draw(sheet)
    for i, rel in enumerate(files):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p): continue
        im = Image.open(p).convert("RGBA")
        im.thumbnail((cell-8, cell-8), Image.LANCZOS)
        x = (i % cols)*cell; y = (i // cols)*(cell+18)
        bg = Image.new("RGBA", (cell, cell), (255,255,255,255))
        bg.paste(im, ((cell-im.size[0])//2, (cell-im.size[1])//2), im)
        sheet.paste(bg.convert("RGB"), (x, y))
        if label:
            d.text((x+6, y+cell+2), os.path.basename(rel).replace(".png",""), fill=(60,60,80))
    sheet.save(os.path.join(ROOT, out), optimize=True)
    print("sheet:", out)

def main():
    manifest = build()
    bad = {}
    for a in manifest:
        iss = qa(a)
        if iss: bad[a["file"]] = iss
    print(json.dumps(bad, indent=1) if bad else "QA: all automated checks passed")
    chars = [a["file"] for a in manifest if "/char/" in a["file"]]
    items = [a["file"] for a in manifest if "/item/" in a["file"]]
    isls  = [a["file"] for a in manifest if "/isl_" in a["file"]]
    bgs   = [a["file"] for a in manifest if "/bg_" in a["file"]]
    contact_sheet(chars, "review/sheet_chars.png", cols=6)
    contact_sheet(items + isls, "review/sheet_items_islands.png", cols=7)
    contact_sheet(bgs, "review/sheet_bgs.png", cols=4, cell=300)
    return 0 if not bad else 1

if __name__ == "__main__":
    sys.exit(main())
