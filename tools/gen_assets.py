# -*- coding: utf-8 -*-
"""Parallel asset generation driver: batches of 2-3 images per codex call,
6 concurrent workers, local PIL validation, up to 3 repair rounds."""
import os, sys, json, subprocess, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from manifest import build

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODEX = r"C:\Users\edliu\AppData\Local\OpenAI\Codex\bin\cfac6bda2d141e07\codex.exe"
LOGDIR = os.path.join(ROOT, "tools", "logs")
os.makedirs(LOGDIR, exist_ok=True)

def validate(asset):
    p = os.path.join(ROOT, asset["file"])
    if not os.path.exists(p) or os.path.getsize(p) < 30000:
        return "missing"
    try:
        im = Image.open(p)
        im.load()
        w, h = im.size
        if w < 900:
            return "too-small"
        if asset["transparent"]:
            if im.mode != "RGBA":
                return "no-alpha"
            for xy in [(4, 4), (w - 5, 4), (4, h - 5), (w - 5, h - 5)]:
                if im.getpixel(xy)[3] > 12:
                    return "corner-opaque"
        return "ok"
    except Exception as e:
        return f"error:{e}"

def batch_instruction(assets):
    lines = [
        f"Use your image generation capability (GPT Image 2) to generate {len(assets)} separate images for a children's game. Generate them ONE BY ONE. For EACH image listed below: generate it with the exact subject and style given, save it to the exact path given (relative to the project root).",
    ]
    for i, a in enumerate(assets, 1):
        size = a.get("size", "1024x1024")
        trans = "fully TRANSPARENT background" if a["transparent"] else "full-bleed opaque background"
        lines.append(f"IMAGE {i}: path={a['file']} ; size {size} ; {trans} ; PROMPT: {a['prompt']}")
    lines.append(
        "After saving ALL images, verify each: run magick <path> -format '%w %h %[pixel:p{5,5}] %[pixel:p{w-5,5}] %[pixel:p{5,h-5}] %[pixel:p{w-5,h-5}]' info: . "
        "For images marked TRANSPARENT all four sampled corner pixels must have alpha 0; if a transparent image has opaque corners, regenerate that image once with stronger 'isolated sticker on fully transparent background' emphasis. "
        "Opaque background images must simply be full-bleed. Do not add text or watermarks to any image. Finally print one line per image: <path> OK or <path> FAIL."
    )
    return "\n".join(lines)

def run_batch(idx, assets):
    instr = batch_instruction(assets)
    log = os.path.join(LOGDIR, f"gen_{idx:02d}.log")
    t0 = time.time()
    try:
        r = subprocess.run(
            [CODEX, "exec", "-C", ROOT, "--skip-git-repo-check", "-s", "workspace-write",
             "-c", 'model_reasoning_effort="low"', instr],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1500)
        out = (r.stdout or "") + "\n--STDERR--\n" + (r.stderr or "")
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"
    with open(log, "w", encoding="utf-8") as f:
        f.write(instr + "\n\n=== OUTPUT ===\n" + out)
    dt = time.time() - t0
    states = {a["file"]: validate(a) for a in assets}
    print(f"[batch {idx:02d}] {dt:.0f}s -> {states}", flush=True)
    return states

def main():
    manifest = build()
    for rnd in range(1, 4):
        pending = [a for a in manifest if validate(a) != "ok"]
        if not pending:
            break
        print(f"=== ROUND {rnd}: {len(pending)} pending ===", flush=True)
        bs = 3 if rnd == 1 else 1
        batches = [pending[i:i + bs] for i in range(0, len(pending), bs)]
        with ThreadPoolExecutor(max_workers=6) as ex:
            list(ex.map(lambda t: run_batch(t[0], t[1]), enumerate(batches)))
    final = {a["file"]: validate(a) for a in manifest}
    bad = {k: v for k, v in final.items() if v != "ok"}
    print(json.dumps({"total": len(final), "ok": len(final) - len(bad), "bad": bad}, indent=1))
    with open(os.path.join(LOGDIR, "final_report.json"), "w", encoding="utf-8") as f:
        json.dump({"bad": bad}, f)

if __name__ == "__main__":
    main()
