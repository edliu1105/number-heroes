# -*- coding: utf-8 -*-
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import run_tests as RT
from run_tests import (SPEECH_MOCK, FREEZE_CSS, state, start_server, BASE,
                       enter_island, unlock_all, play_level, make_page, Fail)
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
            ctx = br.new_context(viewport={"width": 1180, "height": 820}, device_scale_factor=2)
            errors = []
            page = make_page(ctx, errors)
            page.goto(f"{BASE}/?fast=1&seed=42", wait_until="load")   # demo ON, 与 T1 一致
            page.locator("#btnStart").click()
            page.wait_for_function("() => document.body.dataset.scene==='sceneMap'", timeout=8000)
            unlock_all(page)
            enter_island(page, "paw")
            for li, wrong in [(0, True), (1, False), (2, False)]:
                t0 = time.time()
                try:
                    play_level(page, "paw", li, audit="dbg", wrong_once=wrong, shots_prefix="dbg")
                    print(f"paw L{li+1} OK in {time.time()-t0:.0f}s", flush=True)
                except Exception as e:
                    print(f"paw L{li+1} FAIL: {e}", flush=True)
                    page.screenshot(path="review/shots/debug_pawctx.png")
                    st = page.evaluate("""() => ({
                      scene: document.body.dataset.scene,
                      act: (document.querySelector('#stage')||{dataset:{}}).dataset.activity,
                      round: (document.querySelector('#stage')||{dataset:{}}).dataset.round,
                      answer: (document.querySelector('#stage')||{dataset:{}}).dataset.answer,
                      bones: document.querySelectorAll('.bonepile .item').length,
                      undim: document.querySelectorAll('.bonepile .item:not(.dim)').length,
                      cards: document.querySelectorAll('.cards .ncard').length,
                      icards: document.querySelectorAll('.icards .icard').length,
                      icardVis: [...document.querySelectorAll('.icards')].map(b=>getComputedStyle(b).visibility),
                      cele: !!document.querySelector('#cele.on')
                    })""")
                    print("STATE:", st, flush=True)
                    break
            print("errors:", errors[:6], flush=True)
    finally:
        if server: server.terminate()

if __name__ == "__main__":
    main()
