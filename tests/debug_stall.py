# -*- coding: utf-8 -*-
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from run_tests import SPEECH_MOCK, FREEZE_CSS, state, start_server, BASE, solve_current, wait_new_activity, play_island
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def diag(page):
    return page.evaluate("""() => { const S = window.__KM.Speech, A = window.__KM.App;
      const ctx = A.currentCtx;
      return {
        instrActive: !!S._instrActive, cancelT: !!S._cancelT,
        pend: S._pend ? {text:S._pend.text, isCount: !!(S._pend.opts&&S._pend.opts.isCount)} : null,
        countQ: S._countQ.map(q=>({done:q.done, w:q.u&&q.u.text})),
        speaking: speechSynthesis.speaking, pending: speechSynthesis.pending,
        ctxAlive: ctx ? (ctx.sid === A.sessionId && A.currentCtx === ctx) : null,
        sid: A.sessionId, ctxSid: ctx && ctx.sid, aid: A.activityId,
        counted: document.querySelectorAll('.counted').length,
        countables: document.querySelectorAll('.countable').length,
        elemAtCenter: (()=>{ const it=document.querySelector('.countable:not(.counted)');
          if(!it) return 'none'; const r=it.getBoundingClientRect();
          const el=document.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
          return el ? (el.className||el.tagName)+'' : 'null'; })()
      }; }""")

def main():
    server = start_server()
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={"width": 1180, "height": 820})
            page = ctx.new_page()
            page.add_init_script(SPEECH_MOCK)
            page.add_init_script(f"addEventListener('DOMContentLoaded',()=>{{const s=document.createElement('style');s.textContent='{FREEZE_CSS}';document.head.appendChild(s);}});")
            errs = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.goto(f"{BASE}/?fast=1&seed=42", wait_until="load")
            page.locator("#btnStart").click()
            page.wait_for_function("() => document.body.dataset.scene==='sceneMap'", timeout=8000)
            types = set()
            play_island(page, 0, types, wrong_on_first=True, slow_first_count=True)
            print("island 0 done, types:", types)
            page.evaluate("""() => { const d = window.__KM.Store.data;
              for(const k in d.skills){ d.skills[k].lvl = 2; d.skills[k].wins = 5; }
              window.__KM.Store.save(); }""")
            page.locator(".island").nth(1).click()
            wait_new_activity(page, -999)
            print("island1 state:", state(page))
            print("diag before click:", diag(page))
            for i in range(6):
                loc = page.locator(".countable:not(.counted)")
                if loc.count() == 0:
                    print("all counted"); break
                loc.first.click(timeout=3000)
                time.sleep(0.35)
                print(f"after click {i}:", diag(page))
            print("errors:", errs)
    finally:
        if server: server.terminate()

if __name__ == "__main__":
    main()
