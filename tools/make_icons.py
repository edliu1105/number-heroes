# -*- coding: utf-8 -*-
"""Compose PWA icons with PIL: sky gradient + wukong + star."""
import os
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ICONS = os.path.join(ROOT, "assets", "icons")
os.makedirs(ICONS, exist_ok=True)

def base(size):
    im = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(im)
    top, bot = (142, 209, 255), (255, 244, 214)
    for y in range(size):
        t = y / size
        d.line([(0, y), (size, y)], fill=tuple(round(top[i]+(bot[i]-top[i])*t) for i in range(3)))
    return im

def compose(size):
    im = base(size)
    try:
        star = Image.open(os.path.join(ROOT, "assets/item/star.png")).convert("RGBA")
        s = round(size * .42)
        star = star.resize((s, s), Image.LANCZOS)
        im.paste(star, (size - s + s//8, -s//8), star)
    except Exception as e:
        print("star skip", e)
    try:
        wk = Image.open(os.path.join(ROOT, "assets/char/wukong.png")).convert("RGBA")
        w = round(size * .86)
        wk = wk.resize((w, w), Image.LANCZOS)
        im.paste(wk, ((size - w)//2, size - w + round(size*.02)), wk)
    except Exception as e:
        print("wukong skip", e)
    return im

for name, sz in [("icon-512.png", 512), ("icon-192.png", 192), ("apple-touch-icon.png", 180)]:
    compose(sz).save(os.path.join(ICONS, name), optimize=True)
    print("wrote", name)
