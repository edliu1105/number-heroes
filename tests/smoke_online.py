# -*- coding: utf-8 -*-
"""线上冒烟: python tests/smoke_online.py https://edliu1105.github.io/number-heroes/
覆盖: 加载零错误 / 无重定向劫持 / 完整玩一关 / SW就绪 / 断网重载整关可玩 / 竖屏加载"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from run_tests import SPEECH_MOCK, FREEZE_CSS, enter_island, play_level, unlock_all
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
        resp = page.goto(url + "?fast=1&demo=0", wait_until="load", timeout=30000)
        final = page.url
        print("HTTP", resp.status, "final URL:", final)
        if resp.status != 200: ok = False; print("FAIL: status != 200")
        if "behindthepixels" in final:
            ok = False; print("FAIL: redirected to personal domain")
        page.locator("#btnStart").click()
        page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=10000)
        enter_island(page, "xiyou")
        play_level(page, "xiyou", 0)
        print("xiyou L1 completed online")
        page.evaluate("() => navigator.serviceWorker.ready")
        page.wait_for_function("() => caches.keys().then(k => k.length > 0)", timeout=20000)
        page.wait_for_timeout(4000)
        has_core = page.evaluate("() => caches.open('km-v2').then(c => c.match('index.html')).then(r => !!r)")
        print("SW core cached:", has_core)
        if not has_core: ok = False; print("FAIL: SW core not cached")
        ctx.set_offline(True)
        page.reload(wait_until="load")
        page.wait_for_selector("#btnStart", timeout=10000)
        page.locator("#btnStart").click()
        page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=10000)
        unlock_all(page)
        enter_island(page, "bluey")
        play_level(page, "bluey", 0)
        print("OFFLINE bluey L1 completed")
        ctx.set_offline(False)
        if errors:
            ok = False
            print("FAIL console/page errors:", errors[:6])
        ctx.close(); br.close()
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
