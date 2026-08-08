# -*- coding: utf-8 -*-
"""Asset QA: automated checks (size / corner alpha / bbox coverage 22%-97% /
edge-ring halo sampling) + reviewed-allowlist (keyed by content hash, so any
regeneration invalidates the human sign-off) + contact sheets."""
import os, sys, json, hashlib
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from manifest import build

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 人工复核 allowlist: (文件, sha1前12位) -> 结论。素材重生成 → hash 变 → 需重新目检。
REVIEWED = {
    ("assets/char/blackwidow.png", "43e03db41a17"): "2026-08-08 目检: 形象完整未裁切, 底边为阴影像素, touches-edge 为误报",
    ("assets/char/wujing.png", "ad7daffccd90"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
    ("assets/char/tangseng.png", "f261bc49c1c2"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
    ("assets/char/hulu1.png", "9773dcb78a24"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
    ("assets/char/hulu2.png", "d07014b5f311"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
    ("assets/char/hulu4.png", "948e14b677ab"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
    ("assets/char/hulu6.png", "b1a698377e74"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
    ("assets/char/hulu7.png", "3320b77355b7"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
    ("assets/char/yeye.png", "769ac6679723"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
    ("assets/char/gwen.png", "28e4219ab86a"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
    ("assets/char/ryder.png", "adfa46f6fd7f"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
    ("assets/char/chilli.png", "c815a6df113c"): "2026-08-08 目检: 贴纸风白描边(风格特征), 非抠图脏边",
}

def sha12(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:12]

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
            # 边缘 halo: 只扫 bbox 外圈环带(宽度=bbox短边8%), 半透明亮白像素占比过高 = 疑似抠图脏边
            bw, bh = bbox[2]-bbox[0], bbox[3]-bbox[1]
            ring = max(2, min(bw, bh) // 12)
            semi = bright = 0
            step = max(1, bw // 96)
            for y in range(bbox[1], bbox[3], step):
                for x in range(bbox[0], bbox[2], step):
                    in_ring = (x < bbox[0]+ring or x >= bbox[2]-ring or y < bbox[1]+ring or y >= bbox[3]-ring)
                    if not in_ring:
                        continue
                    r, g, b, al = px[x, y]
                    if 20 < al < 200:
                        semi += 1
                        if r > 235 and g > 235 and b > 235: bright += 1
            if semi > 30 and bright / semi > 0.55:
                # 贴纸风白描边的抗锯齿像素也会命中 → ADVISORY, 需目检; 已复核的记入 REVIEWED
                issues.append(f"ADVISORY: bright edge ring ({bright}/{semi} semi-px; sticker border vs halo)")
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
    bad, adv, reviewed = {}, {}, {}
    for a in manifest:
        iss = qa(a)
        p = os.path.join(ROOT, a["file"])
        key = (a["file"], sha12(p)) if os.path.exists(p) else None
        if key and key in REVIEWED and iss:
            reviewed[a["file"]] = REVIEWED[key]     # 人工已复核该内容版本 → 全部降为已审记录
            continue
        hard = [i for i in iss if not i.startswith("ADVISORY")]
        soft = [i for i in iss if i.startswith("ADVISORY")]
        if hard: bad[a["file"]] = hard
        if soft: adv[a["file"]] = soft
    print(json.dumps(bad, indent=1) if bad else "QA: all hard checks passed")
    if reviewed:
        print(f"({len(reviewed)} reviewed-allowlist entries)")
    if adv:
        print(f"({len(adv)} UNREVIEWED ADVISORY entries — gate FAILS until eyeballed & added to REVIEWED):")
        for k, v in adv.items():
            print("  ", k, v)
    chars = [a["file"] for a in manifest if "/char/" in a["file"]]
    items = [a["file"] for a in manifest if "/item/" in a["file"]]
    isls  = [a["file"] for a in manifest if "/isl_" in a["file"]]
    bgs   = [a["file"] for a in manifest if "/bg_" in a["file"]]
    contact_sheet(chars, "review/sheet_chars.png", cols=6)
    contact_sheet(items + isls, "review/sheet_items_islands.png", cols=7)
    contact_sheet(bgs, "review/sheet_bgs.png", cols=4, cell=300)
    # 未复核的 ADVISORY 同样使门槛失败（P2-05）: 新素材必须目检并登记 REVIEWED 后才放行
    return 0 if (not bad and not adv) else 1

if __name__ == "__main__":
    sys.exit(main())
