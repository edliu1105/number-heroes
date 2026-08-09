# -*- coding: utf-8 -*-
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from run_tests import (SPEECH_MOCK, FREEZE_CSS, state, start_server, BASE,
                       enter_island, unlock_all, Fail)
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def dump(page, tag):
    d = page.evaluate("""() => ({
      scene: document.body.dataset.scene,
      act: (document.querySelector('#stage')||{dataset:{}}).dataset.activity || '',
      round: (document.querySelector('#stage')||{dataset:{}}).dataset.round || '',
      answer: (document.querySelector('#stage')||{dataset:{}}).dataset.answer || '',
      bones: document.querySelectorAll('.bonepile .item').length,
      undimmed: document.querySelectorAll('.bonepile .item:not(.dim)').length,
      cards: document.querySelectorAll('.cards .ncard').length,
      icards: document.querySelectorAll('.icards .icard').length,
      cele: !!document.querySelector('#cele.on'),
      countQ: window.__KM ? window.__KM.Speech._countQ.length : -1,
      activeSay: window.__KM ? (window.__KM.Speech._activeCountSay||0) : -1
    })""")
    print(tag, d, flush=True)

def main():
    server = start_server()
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={"width": 1180, "height": 820})
            page = ctx.new_page()
            page.add_init_script(SPEECH_MOCK)
            errs = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            page.add_init_script(f"addEventListener('DOMContentLoaded',()=>{{const s=document.createElement('style');s.textContent='{FREEZE_CSS}';document.head.appendChild(s);}});")
            page.goto(f"{BASE}/?fast=1&seed=42&demo=0", wait_until="load")
            page.locator("#btnStart").click()
            page.wait_for_function("() => document.body.dataset.scene==='sceneMap'", timeout=8000)
            unlock_all(page)
            enter_island(page, "paw")
            page.locator(".lvbtn[data-level='2']").click()
            page.wait_for_function("() => document.body.dataset.scene==='scenePlay'", timeout=10000)
            for rnd in range(4):
                print(f"--- round {rnd} ---", flush=True)
                deadline = time.time() + 40
                solved = False
                while time.time() < deadline:
                    s = state(page)
                    if s["cele"] or s["scene"] != "scenePlay":
                        print("level ended early", s, flush=True); solved = True; break
                    if int(s["round"] or -1) > rnd:
                        solved = True; break
                    if page.locator(".cards .ncard").count():
                        ans = page.evaluate("() => document.querySelector('#stage').dataset.answer")
                        print("cards up, ans =", ans, flush=True)
                        page.locator(f".cards .ncard[data-value='{ans}']").first.click()
                        page.wait_for_timeout(800)
                        continue
                    loc = page.locator(".bonepile .item:not(.dim)")
                    if loc.count():
                        loc.first.click(timeout=3000)
                        page.wait_for_timeout(240)
                        continue
                    dump(page, f"r{rnd} waiting")
                    page.wait_for_timeout(600)
                if not solved and time.time() >= deadline:
                    dump(page, f"r{rnd} STALLED")
                    page.screenshot(path="review/shots/debug_paw3.png")
                    break
                s = state(page)
                if s["cele"]:
                    page.locator("#cele").click()
                    page.wait_for_function("() => document.body.dataset.scene==='sceneLevels'", timeout=10000)
                    break
            print("errors:", errs[:5], flush=True)
    finally:
        if server: server.terminate()

if __name__ == "__main__":
    main()
