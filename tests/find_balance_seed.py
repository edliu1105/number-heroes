# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run_tests as RT
from run_tests import SPEECH_MOCK, FREEZE_CSS, state, start_server, BASE, wait_new_activity, solve_current, Fail
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def main():
    server = start_server()
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            for seed in (7, 8, 11, 13, 17, 23, 31):
                RT.COMPARE_SIDES.clear()
                ctx = br.new_context(viewport={"width": 1180, "height": 820})
                page = ctx.new_page()
                page.add_init_script(SPEECH_MOCK)
                page.add_init_script(f"addEventListener('DOMContentLoaded',()=>{{const s=document.createElement('style');s.textContent='{FREEZE_CSS}';document.head.appendChild(s);}});")
                page.goto(f"{BASE}/?fast=1&seed={seed}&demo=0", wait_until="load")
                page.locator("#btnStart").click()
                page.wait_for_function("() => document.body.dataset.scene==='sceneMap'", timeout=8000)
                page.evaluate("""() => { const d = window.__KM.Store.data;
                  for(const k in d.skills){ d.skills[k].lvl = 2; d.skills[k].wins = 5; }
                  window.__KM.Store.save(); }""")
                for isl in range(4):
                    page.locator(".island").nth(isl).click()
                    wait_new_activity(page, -999)
                    while True:
                        st = state(page)
                        if st["cele"]:
                            page.locator("#cele").click()
                            page.wait_for_function("() => document.body.dataset.scene==='sceneMap'", timeout=8000)
                            break
                        page.wait_for_timeout(200)
                        solve_current(page)
                        try:
                            wait_new_activity(page, st["aid"])
                        except Fail:
                            break
                    if len(set(RT.COMPARE_SIDES)) >= 2:
                        break
                print(f"seed={seed}: sides={RT.COMPARE_SIDES}", flush=True)
                ctx.close()
                if len(set(RT.COMPARE_SIDES)) >= 2:
                    print(f"==> GOOD SEED: {seed}")
            br.close()
    finally:
        if server: server.terminate()

if __name__ == "__main__":
    main()
