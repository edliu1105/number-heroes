# -*- coding: utf-8 -*-
"""线上冒烟: python tests/smoke_online.py https://edliu1105.github.io/number-heroes/
覆盖: 加载零错误 / 无重定向劫持 / 走查一岛 / SW就绪 / 断网重载可玩 / 竖屏加载"""
import sys, time, os
sys.path.insert(0, os.path.dirname(__file__))
from run_tests import SPEECH_MOCK, FREEZE_CSS, state, play_island, Fail
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def make_page(ctx, errors):
    page = ctx.new_page()
    page.add_init_script(SPEECH_MOCK)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    page.add_init_script(f"addEventListener('DOMContentLoaded',()=>{{const s=document.createElement('style');s.textContent='{FREEZE_CSS}';document.head.appendChild(s);}});")
    return page

def main(url):
    ok = True
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={"width": 1180, "height": 820})
        errors = []
        page = make_page(ctx, errors)
        # 1. 加载 + 无劫持
        resp = page.goto(url + "?fast=1&demo=0", wait_until="load", timeout=30000)
        final = page.url
        print("HTTP", resp.status, "final URL:", final)
        if resp.status != 200: ok = False; print("FAIL: status != 200")
        if "behindthepixels" in final or not final.startswith(url.split("?")[0][:30]):
            ok = False; print("FAIL: redirected off-site ->", final)
        # 2. 走查一岛
        page.locator("#btnStart").click()
        page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=10000)
        types = set()
        play_island(page, 0, types)
        print("island 0 done, types:", sorted(types))
        # 3. SW 就绪 + 预缓存
        page.evaluate("() => navigator.serviceWorker.ready")
        page.wait_for_function("() => caches.keys().then(k => k.length > 0)", timeout=20000)
        page.wait_for_timeout(4000)   # 等素材预缓存
        has_core = page.evaluate("() => caches.open('km-v1').then(c => c.match('index.html')).then(r => !!r)")
        print("SW core cached:", has_core)
        if not has_core: ok = False; print("FAIL: SW core not cached")
        # 4. 断网重载
        ctx.set_offline(True)
        page.reload(wait_until="load")
        page.wait_for_selector("#btnStart", timeout=10000)
        page.locator("#btnStart").click()
        page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=10000)
        types2 = set()
        play_island(page, 1, types2)
        print("OFFLINE island 1 done, types:", sorted(types2))
        ctx.set_offline(False)
        if errors:
            ok = False
            print("FAIL console/page errors:", errors[:6])
        ctx.close(); br.close()
        # 5. 竖屏加载
        br = pw.webkit.launch()
        ctx = br.new_context(viewport={"width": 820, "height": 1180})
        errors2 = []
        page = make_page(ctx, errors2)
        page.goto(url + "?fast=1&demo=0", wait_until="load", timeout=30000)
        page.locator("#btnStart").click()
        page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=10000)
        print("portrait load ok")
        if errors2: ok = False; print("FAIL portrait errors:", errors2[:4])
        ctx.close(); br.close()
    print("SMOKE:", "ALL GREEN" if ok else "FAILED")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main(sys.argv[1].rstrip("/") + "/")
