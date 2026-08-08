# -*- coding: utf-8 -*-
"""数字小英雄 — Playwright 发布门槛测试
运行: python tests/run_tests.py
覆盖: 全流程走查(横/竖, chromium/webkit) / 语音时间线断言 / 快速连点压力 /
     断网离线重载 / 真实运动目标命中(不用 force) / 触摸目标尺寸 / 家长面板
"""
import json, os, subprocess, sys, time, socket
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SHOTS = os.path.join(ROOT, "review", "shots")
os.makedirs(SHOTS, exist_ok=True)
PORT = 8141
BASE = f"http://127.0.0.1:{PORT}"

NUM_CN = ['零','一','二','三','四','五','六','七','八','九','十']

# speechSynthesis 记录器 + 队列语义 mock（注入于页面脚本之前）
SPEECH_MOCK = r"""
window.__SPEECH = [];
(function(){
  const S = {
    speaking:false, pending:false, paused:false, _q:[], onvoiceschanged:null,
    getVoices(){ return [{name:'Mock Tingting', lang:'zh-CN', voiceURI:'mock-zh', localService:true, default:true}]; },
    resume(){}, pause(){},
    cancel(){ window.__SPEECH.push({t:performance.now(), a:'cancel'});
      this._q.forEach(u=>{u._cancelled=true;}); this._q=[]; this._upd(); },
    speak(u){ window.__SPEECH.push({t:performance.now(), a:'speak', text:u.text});
      u._cancelled=false; this._q.push(u); this._upd();
      if(this._q[0]===u) this._run(u); },
    _run(u){ this._upd();
      setTimeout(()=>{ if(u._cancelled) return; try{u.onstart && u.onstart({});}catch(e){}
        setTimeout(()=>{ if(u._cancelled) return;
          const i=this._q.indexOf(u); if(i>=0) this._q.splice(i,1); this._upd();
          try{u.onend && u.onend({});}catch(e){}
          const nx=this._q[0]; if(nx) this._run(nx);
        }, 90);
      }, 25); },
    _upd(){ this.speaking=this._q.length>0; this.pending=this._q.length>1; }
  };
  Object.defineProperty(window, 'speechSynthesis', {value:S, configurable:true});
  window.SpeechSynthesisUtterance = function(text){ this.text=text||''; this.lang=''; this.rate=1; this.pitch=1; this.volume=1; this.voice=null; };
})();
"""

FREEZE_CSS = "*,*::before,*::after{animation:none!important;transition-duration:0.02s!important}"

class Fail(Exception): pass

results = []
def report(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + ("  " + detail if detail else ""), flush=True)

def start_server():
    s = socket.socket(); ok = s.connect_ex(("127.0.0.1", PORT)) != 0; s.close()
    if not ok:
        return None
    p = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--directory", ROOT],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    return p

def make_page(ctx, errors, freeze=True):
    page = ctx.new_page()
    page.add_init_script(SPEECH_MOCK)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    if freeze:
        page.add_init_script(f"addEventListener('DOMContentLoaded',()=>{{const s=document.createElement('style');s.textContent='{FREEZE_CSS}';document.head.appendChild(s);}});")
    return page

def state(page):
    return page.evaluate("""() => ({
      act: (document.querySelector('#stage')||{dataset:{}}).dataset.activity || '',
      aid: window.__KM ? window.__KM.App.activityId : -1,
      answer: (document.querySelector('#stage')||{dataset:{}}).dataset.answer || '',
      scene: document.body.dataset.scene || '',
      cele: !!document.querySelector('#cele.on')
    })""")

def click_answer(page, answer, wrong_first=False):
    page.wait_for_selector(".cards .ncard", timeout=12000)
    if answer is None:
        # count/add/compose/flash: data-answer 由 askNumber 挂载时设置, 必须在卡片出现后读取
        answer = page.evaluate("() => document.querySelector('#stage').dataset.answer || ''")
        if not answer:
            raise Fail("no data-answer after cards appeared")
    if wrong_first:
        wrongs = page.locator(f".cards .ncard:not([data-value='{answer}'])")
        if wrongs.count() > 0:
            wrongs.first.click(timeout=3000)
            page.wait_for_function(
                "() => { const b=document.querySelector('.cards'); return b && getComputedStyle(b).visibility!=='hidden'; }",
                timeout=15000)
    # 重问语音期间 lock 未释放会吞点击 → 轮询点击直到卡片消失（活动完成）
    deadline = time.time() + 15
    while time.time() < deadline:
        loc = page.locator(f".cards .ncard[data-value='{answer}']")
        if loc.count() == 0:
            return
        try:
            loc.first.click(timeout=2000)
        except Exception:
            pass
        page.wait_for_timeout(650)
    raise Fail("answer card click never resolved the activity")

SIZE_VIOLATIONS = []
COMPARE_SIDES = []
def audit_sizes(page, label):
    """核心触摸目标 ≥88px（浮点容差 87.5; 槽位/徽章等非目标元素不在列）"""
    bad = page.evaluate("""() => {
      const bad = [];
      for(const sel of ['.countable','.ncard','.balloon','#btnHome','#btnReplay','#btnDone','.tray .item','.srcgrp .item']){
        document.querySelectorAll(sel).forEach(e => {
          const r = e.getBoundingClientRect();
          if(r.width > 0 && (r.width < 87.5 || r.height < 87.5))
            bad.push(sel + ':' + Math.round(r.width) + 'x' + Math.round(r.height));
        });
      }
      return bad; }""")
    for b in bad:
        SIZE_VIOLATIONS.append(f"{label} {b}")

def solve_current(page, wrong_first=False, slow_count=False, audit=None):
    st = state(page)
    act, ans = st["act"], st["answer"]
    if audit:
        audit_sizes(page, f"{audit}/{act}")
    if act in ("count", "add"):
        deadline = time.time() + 25
        while time.time() < deadline:
            loc = page.locator(".countable:not(.counted)")
            if loc.count() == 0:
                break
            loc.first.click(timeout=4000)
            page.wait_for_timeout(700 if slow_count else 150)
        click_answer(page, None, wrong_first)
    elif act == "flash":
        page.wait_for_selector(".flashcover", timeout=15000)
        click_answer(page, None, wrong_first)
    elif act == "numeral":
        page.locator(f".balloon[data-value='{ans}']").click(timeout=8000)
    elif act == "produce":
        n = int(ans)
        for _ in range(n):
            page.locator(".tray .item:not(.dim)").first.click(timeout=4000)
            page.wait_for_timeout(170)
        page.locator("#btnDone").click(timeout=5000)
    elif act == "compare":
        idx = page.evaluate(f"""() => {{
          const sides = [...document.querySelectorAll('.side')];
          return sides.findIndex(s => s.dataset.char === '{ans}'); }}""")
        COMPARE_SIDES.append('L' if idx == 0 else 'R')
        page.locator(f".side[data-char='{ans}']").click(timeout=5000)
    elif act == "compose":
        deadline = time.time() + 25
        while time.time() < deadline:
            loc = page.locator(".srcgrp .item:not(.dim)")
            if loc.count() == 0:
                break
            loc.first.click(timeout=4000)
            page.wait_for_timeout(150)
        click_answer(page, None, wrong_first)
    else:
        raise Fail(f"unknown activity {act}")
    return act

def wait_new_activity(page, prev_aid, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = state(page)
        if st["cele"]:
            return "cele"
        # 必须在游戏场景中且活动已挂载（避免读到过渡期的陈旧 dataset）
        if st["scene"] == "scenePlay" and st["act"] and st["aid"] != prev_aid:
            return st["aid"]
        page.wait_for_timeout(120)
    raise Fail(f"no new activity after aid={prev_aid}")

def play_island(page, idx, types_seen, shots_prefix=None, wrong_on_first=False, slow_first_count=False, audit=None):
    page.locator(".island").nth(idx).click(timeout=5000)
    aid = wait_new_activity(page, -999)
    n_done = 0
    first = True
    while True:
        st = state(page)
        if st["cele"]:
            if shots_prefix:
                page.screenshot(path=os.path.join(SHOTS, f"{shots_prefix}_cele.png"))
            page.locator("#cele").click(timeout=4000)
            page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=15000)
            break
        page.wait_for_timeout(250)
        act = st["act"]
        if shots_prefix and act not in types_seen:
            page.wait_for_timeout(400)
            page.screenshot(path=os.path.join(SHOTS, f"{shots_prefix}_{act}.png"))
        solved = solve_current(page, wrong_first=(wrong_on_first and first),
                               slow_count=(slow_first_count and first and act == "count"),
                               audit=audit)
        types_seen.add(solved)
        n_done += 1
        first = False
        try:
            nxt = wait_new_activity(page, st["aid"])
        except Fail:
            if state(page)["scene"] == "sceneMap":
                break
            raise
        if nxt == "cele":
            continue
        if n_done > 8:
            raise Fail("island did not finish in 8 activities")
    return n_done

def get_speech(page):
    return page.evaluate("window.__SPEECH.slice()")

def assert_speech_rules(log, label):
    speaks = [e for e in log if e["a"] == "speak"]
    welcome = [s for s in speaks if "欢迎来到数字小英雄乐园" in s["text"]]
    if len(welcome) != 1:
        raise Fail(f"{label}: welcome spoken {len(welcome)} times (expect 1)")
    last_cancel = None
    for e in log:
        if e["a"] == "cancel":
            last_cancel = e["t"]
        elif e["a"] == "speak" and last_cancel is not None:
            gap = e["t"] - last_cancel
            if gap < 148:
                raise Fail(f"{label}: speak {gap:.0f}ms after cancel (<150ms): {e['text'][:20]}")
            last_cancel = None
    prev = None
    for s in speaks:
        if prev and s["text"] == prev["text"] and len(s["text"]) > 2 and (s["t"] - prev["t"]) < 3000:
            raise Fail(f"{label}: instruction repeated within 3s: {s['text'][:24]}")
        prev = s
    return len(speaks)

def count_words_in(log):
    return [e["text"] for e in log if e["a"] == "speak" and len(e["text"]) == 1 and e["text"] in NUM_CN]

def main():
    server = start_server()
    ok_all = True
    try:
        with sync_playwright() as pw:
            # ============ T1: chromium 横屏全流程（含语音时间线/答错脚手架/6岛/7活动型） ============
            errors = []
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={"width": 1180, "height": 820}, device_scale_factor=2)
            page = make_page(ctx, errors)
            try:
                page.goto(f"{BASE}/?fast=1&seed=42", wait_until="load")
                page.wait_for_selector("#btnStart", timeout=10000)
                page.screenshot(path=os.path.join(SHOTS, "t1_boot.png"))
                page.locator("#btnStart").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                page.wait_for_timeout(600)
                page.screenshot(path=os.path.join(SHOTS, "t1_map.png"))
                types_seen = set()
                # 岛1: 新手状态; 第一个 count 慢点(700ms间隔)供听觉一一对应断言; 首题故意答错一次走脚手架
                play_island(page, 0, types_seen, shots_prefix="t1a", wrong_on_first=True, slow_first_count=True, audit="t1")
                # 解锁全部活动类型, 六岛全部走查（P1-05）
                page.evaluate("""() => { const d = window.__KM.Store.data;
                  for(const k in d.skills){ d.skills[k].lvl = 2; d.skills[k].wins = 5; }
                  window.__KM.Store.save(); }""")
                for isl in (1, 2, 3, 4, 5):
                    play_island(page, isl, types_seen, shots_prefix=f"t1_{isl}", audit="t1")
                missing = {"count","numeral","produce","flash","compare","compose","add"} - types_seen
                if missing:
                    raise Fail(f"activity types not covered after 6 islands: {missing}")
                if SIZE_VIOLATIONS:
                    raise Fail("touch targets <88px: " + "; ".join(SIZE_VIOLATIONS[:6]))
                # 比较活动位置平衡（P0-01）: 走查过程中"多的一侧"应两侧都出现过（seed 固定, 确定性）
                if len(COMPARE_SIDES) >= 2 and len(set(COMPARE_SIDES)) < 2:
                    raise Fail(f"compare winner always on same side: {COMPARE_SIDES}")
                # 语音时间线
                log = get_speech(page)
                nspeaks = assert_speech_rules(log, "T1")
                # 家长面板（长按3秒）
                gear = page.locator("#gearMap")
                gear.hover()
                page.mouse.down(); page.wait_for_timeout(3300); page.mouse.up()
                page.wait_for_selector("#parent.on", timeout=4000)
                page.screenshot(path=os.path.join(SHOTS, "t1_parent.png"))
                if "Mock Tingting" not in page.locator(".pp .diag").inner_text():
                    raise Fail("parent panel: zh voice not shown in diagnostics")
                page.locator("#ppClose").click()
                # 回家二次确认
                page.locator(".island").nth(0).click()
                wait_new_activity(page, -999)
                page.locator("#btnHome").click()
                page.wait_for_timeout(250)
                if state(page)["scene"] == "sceneMap":
                    raise Fail("home exited on single tap (expect 2-tap confirm)")
                page.locator("#btnHome").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=5000)
                if errors:
                    raise Fail("console/page errors: " + " | ".join(errors[:5]))
                report("T1 chromium 全流程走查+语音时间线+家长面板+回家确认", True, f"{nspeaks} speaks, types={sorted(types_seen)}")
            except Exception as e:
                ok_all = False
                page.screenshot(path=os.path.join(SHOTS, "t1_FAIL.png"))
                report("T1 chromium 全流程", False, str(e)[:300])
            # ---- T2: 听觉一一对应（慢速点数的完整序列）----
            try:
                log = get_speech(page)
                words = count_words_in(log)
                seq_ok = False
                for i in range(len(words)):
                    if words[i] == "一" and i + 1 < len(words) and words[i+1] == "二":
                        j, expect = i, 1
                        while j < len(words) and words[j] == NUM_CN[expect]:
                            j += 1; expect += 1
                        if expect >= 3:
                            seq_ok = True; break
                if not seq_ok:
                    raise Fail(f"no intact 一二三.. sequence in count words: {words[:20]}")
                report("T2 计数词有序完整（听觉一一对应）", True, f"words={words[:12]}")
            except Exception as e:
                ok_all = False; report("T2 计数词序列", False, str(e)[:200])
            ctx.close(); br.close()

            # ============ T3: 快速连点压力 ============
            errors3 = []
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={"width": 1180, "height": 820})
            page = make_page(ctx, errors3)
            try:
                page.goto(f"{BASE}/?fast=1&seed=7&demo=0", wait_until="load")
                page.locator("#btnStart").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                page.locator(".island").nth(1).click()
                wait_new_activity(page, -999)
                # 疯狂连点 3 秒: 真实鼠标点击（实时包围盒坐标, 非合成事件; P1-05）
                end = time.time() + 3
                while time.time() < end:
                    for sel in (".countable", ".ncard", ".balloon", ".tray .item", ".srcgrp .item", "#btnDone"):
                        loc = page.locator(sel)
                        if loc.count():
                            try:
                                bb = loc.nth(0).bounding_box()
                                if bb: page.mouse.click(bb["x"] + bb["width"]/2, bb["y"] + bb["height"]/2)
                            except Exception: pass
                    page.mouse.click(590, 400)
                # 连点后应用仍可推进: 完成当前活动
                page.wait_for_timeout(500)
                st = state(page)
                if st["act"]:
                    solve_current(page)
                log = get_speech(page)
                words = count_words_in(log)
                for i in range(1, len(words)):
                    a, b = NUM_CN.index(words[i-1]), NUM_CN.index(words[i])
                    if b != a + 1 and b != 1:
                        raise Fail(f"count word sequence broken under spam: ...{words[max(0,i-3):i+1]}")
                if errors3:
                    raise Fail("errors: " + " | ".join(errors3[:5]))
                report("T3 快速连点压力（背压保序+无错误）", True, f"words={words}")
            except Exception as e:
                ok_all = False
                page.screenshot(path=os.path.join(SHOTS, "t3_FAIL.png"))
                report("T3 快速连点压力", False, str(e)[:300])
            ctx.close(); br.close()

            # ============ T4: 离线（SW） ============
            errors4 = []
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={"width": 1180, "height": 820})
            page = make_page(ctx, errors4)
            try:
                page.goto(f"{BASE}/?fast=1", wait_until="load")
                page.evaluate("() => navigator.serviceWorker.ready")
                page.wait_for_function("() => caches.keys().then(k=>k.length>0)", timeout=15000)
                page.wait_for_function("""() => caches.open('km-v1').then(c=>c.match('index.html')).then(r=>!!r)""", timeout=20000)
                page.wait_for_timeout(2500)  # 等素材预缓存
                ctx.set_offline(True)
                page.reload(wait_until="load")
                page.wait_for_selector("#btnStart", timeout=10000)
                page.locator("#btnStart").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                imgs_ok = page.evaluate("""() => {
                  const im = [...document.querySelectorAll('#mapGrid img')].slice(0,6);
                  return im.length>0 && im.every(i=>i.complete && i.naturalWidth>0); }""")
                if not imgs_ok:
                    raise Fail("map images not loaded offline")
                types4 = set()
                play_island(page, 0, types4)         # 离线走完整一岛（P1-05）
                if errors4:
                    raise Fail("errors offline: " + " | ".join(errors4[:5]))
                report("T4 断网离线完整可玩（整岛5活动, SW 缓存）", True)
            except Exception as e:
                ok_all = False
                page.screenshot(path=os.path.join(SHOTS, "t4_FAIL.png"))
                report("T4 离线", False, str(e)[:300])
            ctx.close(); br.close()

            # ============ T5: webkit 竖屏走查 + 触摸目标尺寸 ============
            errors5 = []
            br = pw.webkit.launch()
            ctx = br.new_context(viewport={"width": 820, "height": 1180}, device_scale_factor=2)
            page = make_page(ctx, errors5)
            try:
                page.goto(f"{BASE}/?fast=1&seed=9", wait_until="load")
                page.locator("#btnStart").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                page.wait_for_timeout(500)
                page.screenshot(path=os.path.join(SHOTS, "t5_map_portrait.png"))
                # 解锁全部类型: 竖屏矩阵覆盖高阶活动布局（P1-05）
                page.evaluate("""() => { const d = window.__KM.Store.data;
                  for(const k in d.skills){ d.skills[k].lvl = 2; d.skills[k].wins = 5; }
                  window.__KM.Store.save(); }""")
                SIZE_VIOLATIONS.clear()
                types = set()
                play_island(page, 5, types, shots_prefix="t5", audit="t5")
                play_island(page, 1, types, audit="t5")
                play_island(page, 2, types, audit="t5")
                if SIZE_VIOLATIONS:
                    raise Fail("portrait touch targets <88px: " + "; ".join(SIZE_VIOLATIONS[:8]))
                if len(types) < 5:
                    raise Fail(f"portrait matrix covered too few types: {sorted(types)}")
                if errors5:
                    raise Fail("errors: " + " | ".join(errors5[:5]))
                report("T5 webkit 竖屏矩阵(3岛)+触摸目标≥88px", True, f"types={sorted(types)}")
            except Exception as e:
                ok_all = False
                page.screenshot(path=os.path.join(SHOTS, "t5_FAIL.png"))
                report("T5 webkit 竖屏", False, str(e)[:300])
            ctx.close(); br.close()

            # ============ T6: 真实运动目标命中（气球不冻结动画、不用 force） ============
            errors6 = []
            br = pw.webkit.launch()
            ctx = br.new_context(viewport={"width": 1180, "height": 820})
            page = make_page(ctx, errors6, freeze=False)   # 动画保持真实
            try:
                page.goto(f"{BASE}/?fast=1&seed=5&demo=0", wait_until="load")
                bb = page.locator("#btnStart").bounding_box()   # 脉冲动画按钮: 直接坐标真实点击
                page.mouse.click(bb["x"] + bb["width"]/2, bb["y"] + bb["height"]/2)
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                page.evaluate("""() => { const d = window.__KM.Store.data;
                  d.skills.numeral.wins = 9; window.__KM.Store.save(); }""")
                found = False
                for _ in range(10):
                    page.locator(".island").nth(2).click()
                    wait_new_activity(page, -999)
                    for _ in range(6):
                        st = state(page)
                        if st["act"] == "numeral":
                            found = True; break
                        solve_current(page)
                        try: wait_new_activity(page, st["aid"])
                        except Fail: break
                        if state(page)["cele"]:
                            page.locator("#cele").click()
                            page.wait_for_function("() => document.body.dataset.scene==='sceneMap'", timeout=8000)
                            break
                    if found: break
                    if state(page)["scene"] != "sceneMap":
                        page.locator("#btnHome").click(); page.wait_for_timeout(150); page.locator("#btnHome").click()
                        page.wait_for_function("() => document.body.dataset.scene==='sceneMap'", timeout=8000)
                if not found:
                    raise Fail("numeral activity not reachable")
                ans = state(page)["answer"]
                target = page.locator(f".balloon[data-value='{ans}']")
                hit = False
                for _ in range(4):   # 移动目标: 实时取包围盒中心真实点击
                    bb = target.bounding_box()
                    if not bb: break
                    page.mouse.click(bb["x"] + bb["width"]/2, bb["y"] + bb["height"]/2)
                    page.wait_for_timeout(400)
                    if target.count() == 0 or "popped" in (target.get_attribute("class") or ""):
                        hit = True; break
                if not hit:
                    raise Fail("moving balloon not hittable with real clicks")
                if errors6:
                    raise Fail("errors: " + " | ".join(errors6[:5]))
                report("T6 真实运动气球命中（无 force）", True)
            except Exception as e:
                ok_all = False
                page.screenshot(path=os.path.join(SHOTS, "t6_FAIL.png"))
                report("T6 运动目标命中", False, str(e)[:300])
            ctx.close(); br.close()
    finally:
        if server:
            server.terminate()
    print("\n==== SUMMARY ====")
    for n, ok, d in results:
        print(("PASS" if ok else "FAIL"), n)
    if not ok_all:
        sys.exit(1)
    print("ALL GREEN")

if __name__ == "__main__":
    main()
