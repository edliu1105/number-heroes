# -*- coding: utf-8 -*-
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from run_tests import SPEECH_MOCK, FREEZE_CSS, state, start_server, BASE, wait_new_activity, solve_current, Fail, click_answer
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
            ctx = br.new_context(viewport={"width": 1180, "height": 820})
            page = ctx.new_page()
            page.add_init_script(SPEECH_MOCK)
            page.add_init_script(f"addEventListener('DOMContentLoaded',()=>{{const s=document.createElement('style');s.textContent='{FREEZE_CSS}';document.head.appendChild(s);}});")
            page.goto(f"{BASE}/?fast=1&seed=42&demo=0", wait_until="load")
            page.locator("#btnStart").click()
            page.wait_for_function("() => document.body.dataset.scene==='sceneMap'", timeout=8000)
            page.evaluate("""() => { const d = window.__KM.Store.data;
              for(const k in d.skills){ d.skills[k].lvl = 2; d.skills[k].wins = 5; }
              window.__KM.Store.save(); }""")
            found = 0
            for isl in range(6):
                page.locator(".island").nth(isl).click()
                wait_new_activity(page, -999)
                while True:
                    st = state(page)
                    if st["cele"]:
                        page.locator("#cele").click()
                        page.wait_for_function("() => document.body.dataset.scene==='sceneMap'", timeout=8000)
                        break
                    page.wait_for_timeout(250)
                    if st["act"] == "compare":
                        found += 1
                        probe = page.evaluate("""() => {
                          const sides = [...document.querySelectorAll('.side')];
                          return { answer: document.querySelector('#stage').dataset.answer,
                            sideChars: sides.map(s => s.dataset.char),
                            sideCounts: sides.map(s => s.querySelectorAll('.item').length) }; }""")
                        print("COMPARE probe:", probe)
                    solve_current(page)
                    try:
                        nxt = wait_new_activity(page, st["aid"])
                    except Fail:
                        break
                if found >= 4:
                    break
            print("total compares probed:", found)
    finally:
        if server: server.terminate()

if __name__ == "__main__":
    main()
