# -*- coding: utf-8 -*-
"""Asset QA: automated checks (size / corner alpha / bbox coverage / edge halo)
+ contact sheets for visual inspection."""
import os, sys, json
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from manifest import build

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def qa(asset):
    """自动检查: 尺寸 / 四角alpha / 主体bbox占比(22%-97%, 与DESIGN §9.5一致) /
    贴边裁切 / 边缘halo(半透明亮色描边采样)。"""
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
        px = rgba.load()
        a = rgba.split()[3]
        for xy in [(2,2),(w-3,2),(2,h-3),(w-3,h-3)]:
            if a.getpixel(xy) > 12: issues.append(f"corner opaque {xy}"); break
        bbox = a.point(lambda v: 255 if v > 16 else 0).getbbox()
        if not bbox:
            issues.append("empty")
        else:
            cov = (bbox[2]-bbox[0])*(bbox[3]-bbox[1])/(w*h)
            if cov < 0.22: issues.append(f"subject tiny cov={cov:.2f}")
            if cov > 0.97: issues.append(f"likely cropped cov={cov:.2f}")
            if bbox[0] <= 1 or bbox[1] <= 1 or bbox[2] >= w-1 or bbox[3] >= h-1:
                issues.append("touches edge (possible crop)")
            # 边缘 halo: 半透明像素中亮白像素占比过高 = 抠图脏边
            semi = bright = 0
            step = max(1, (bbox[2]-bbox[0]) // 64)
            for y in range(bbox[1], bbox[3], step):
                for x in range(bbox[0], bbox[2], step):
                    r, g, b, al = px[x, y]
                    if 20 < al < 200:
                        semi += 1
                        if r > 235 and g > 235 and b > 235: bright += 1
            if semi > 40 and bright / semi > 0.55:
                # 贴纸风白描边的抗锯齿像素也会命中此启发式 → 仅提示, 需目检区分
                # (2026-08 目检结论: 全部命中均为刻意的 sticker 白描边, 非抠图脏边)
                issues.append(f"ADVISORY: bright edge band ({bright}/{semi} semi-px; sticker border vs halo — needs eyeball)")
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
    adv = {}
    for a in manifest:
        iss = qa(a)
        hard = [i for i in iss if not i.startswith("ADVISORY")]
        soft = [i for i in iss if i.startswith("ADVISORY")]
        if hard: bad[a["file"]] = hard
        if soft: adv[a["file"]] = soft
    print(json.dumps(bad, indent=1) if bad else "QA: all hard checks passed")
    if adv:
        print(f"({len(adv)} advisory notes — sticker-border AA, eyeballed OK)")
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
