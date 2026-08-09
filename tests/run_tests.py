# -*- coding: utf-8 -*-
"""数字小英雄 v2 — Playwright 发布门槛测试
运行: python tests/run_tests.py
覆盖: 六岛×三关全走查(18关/72回合) / 关卡解锁断言 / 语音时间线 / 错误路径脚手架 /
     快速连点 / 断网整关 / webkit 竖屏矩阵 / 运动目标真实命中 / 触摸目标≥88px
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
ISLANDS = ["xiyou", "hulu", "avengers", "paw", "bluey", "peppa"]

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
      const dur = window.__SPEECH_DUR || 90;
      setTimeout(()=>{ if(u._cancelled) return; try{u.onstart && u.onstart({});}catch(e){}
        setTimeout(()=>{ if(u._cancelled) return;
          const i=this._q.indexOf(u); if(i>=0) this._q.splice(i,1); this._upd();
          try{u.onend && u.onend({});}catch(e){}
          const nx=this._q[0]; if(nx) this._run(nx);
        }, dur);
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
    s = socket.socket(); free = s.connect_ex(("127.0.0.1", PORT)) != 0; s.close()
    if not free:
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
      round: (document.querySelector('#stage')||{dataset:{}}).dataset.round || '',
      aid: window.__KM ? window.__KM.App.activityId : -1,
      answer: (document.querySelector('#stage')||{dataset:{}}).dataset.answer || '',
      phase: (document.querySelector('#stage')||{dataset:{}}).dataset.phase || '',
      scene: document.body.dataset.scene || '',
      cele: !!document.querySelector('#cele.on')
    })""")

SIZE_VIOLATIONS = []
def audit_sizes(page, label):
    bad = page.evaluate("""() => {
      const bad = [];
      for(const sel of ['.peach-on-tree','.ncard','.icard','.numball','#btnHome','#btnReplay','#btnDone','#btnLvBack',
                        '.bonepile .item','.waitline button','.pedestal-row button','.dicebtn','.lvbtn']){
        document.querySelectorAll(sel).forEach(e => {
          const r = e.getBoundingClientRect();
          if(r.width > 0 && (r.width < 87.5 || r.height < 87.5))
            bad.push(sel + ':' + Math.round(r.width) + 'x' + Math.round(r.height));
        });
      }
      return bad; }""")
    for b in bad:
        SIZE_VIOLATIONS.append(f"{label} {b}")

def wait_cards(page, kind=".cards .ncard", timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if page.locator(kind).count() > 0:
            return True
        page.wait_for_timeout(120)
    return False

def _round_alive(page, entry_aid):
    s = state(page)
    return s["aid"] == entry_aid and s["scene"] == "scenePlay" and not s["cele"]

def click_number_answer(page):
    entry_aid = state(page)["aid"]
    deadline = time.time() + 18
    seen = False
    while time.time() < deadline:
        if not _round_alive(page, entry_aid):
            if seen:
                return                              # 本回合已随答题推进结束
            raise Fail("round ended before number cards appeared")
        if page.locator(".cards .ncard").count() == 0:
            if seen:
                return                              # 牌已消失=本题解决; 下一题/下一回合由外层驱动
            page.wait_for_timeout(150)
            continue
        seen = True
        # 同一回合内可重读答案(bluey 等多问题回合); 回合边界由 aid 锚定, 绝不跨回合点击
        answer = page.evaluate("() => document.querySelector('#stage').dataset.answer || ''")
        loc = page.locator(f".cards .ncard[data-value='{answer}']")
        if loc.count() == 0:
            page.wait_for_timeout(300)
            continue
        try: loc.first.click(timeout=2000)
        except Exception: pass
        page.wait_for_timeout(600)
    raise Fail("number card click never resolved")

def click_icon_answer(page, wrong_first=False):
    entry_aid = state(page)["aid"]
    if not wait_cards(page, ".icards .icard", 18):
        raise Fail("icon cards never appeared")
    if wrong_first:
        answer = page.evaluate("() => document.querySelector('#stage').dataset.answer || ''")
        w = page.locator(f".icards .icard:not([data-value='{answer}'])")
        if w.count():
            w.first.click(timeout=3000)
            page.wait_for_timeout(400)
    deadline = time.time() + 20
    while time.time() < deadline:
        if not _round_alive(page, entry_aid):
            return
        if page.locator(".icards .icard").count() == 0:
            return
        answer = page.evaluate("() => document.querySelector('#stage').dataset.answer || ''")
        loc = page.locator(f".icards .icard[data-value='{answer}']")
        if loc.count() == 0:
            page.wait_for_timeout(300)
            continue
        try: loc.first.click(timeout=2000)
        except Exception: pass
        page.wait_for_timeout(650)
    raise Fail("icon card click never resolved")

def tap_pool(page, sel, times, gap=210):
    for _ in range(times):
        loc = page.locator(sel)
        if loc.count() == 0:
            return False
        loc.first.click(timeout=4000)
        page.wait_for_timeout(gap)
    return True

def drive_round(page, audit=None, wrong_once=False):
    """驱动一个回合直至 round/scene 变化。按 activity 分派。返回 activity 名。"""
    st0 = state(page)
    act = st0["act"]
    if audit:
        page.wait_for_timeout(300)
        audit_sizes(page, f"{audit}/{act}r{st0['round']}")
    deadline = time.time() + 55
    def round_over():
        s = state(page)
        return s["cele"] or s["scene"] != "scenePlay" or s["aid"] != st0["aid"]

    if act.startswith("xiyou") and act.endswith(("L1", "L2")):
        while not round_over() and time.time() < deadline:
            s = state(page)
            n = int(s["answer"] or 0)
            if wrong_once and act.endswith("L1"):
                tap_pool(page, ".peach-on-tree:not(.dim)", max(1, n - 1))
                page.wait_for_timeout(300)
                if page.locator("#btnDone").count():
                    page.locator("#btnDone").click()
                page.wait_for_timeout(1500)          # 脚手架念数
                wrong_once = False
                # 复位后重来
                deadline2 = time.time() + 20
                while time.time() < deadline2 and page.locator(".peach-on-tree:not(.dim)").count() < n:
                    page.wait_for_timeout(200)
                continue
            got = page.evaluate("() => document.querySelectorAll('.peach-on-tree.dim').length")
            need = n - (got if act.endswith("L1") else 0)
            if act.endswith("L2"):
                # 每阶段重新数: 需要的 = 目标 - 本阶段已投(用 dataset.ph 无法读, 直接点满目标次数)
                tap_pool(page, ".peach-on-tree:not(.dim)", n)
            else:
                tap_pool(page, ".peach-on-tree:not(.dim)", max(0, need))
            page.wait_for_timeout(400)
            if page.locator("#btnDone").count():
                try: page.locator("#btnDone").click(timeout=2000)
                except Exception: pass
            page.wait_for_timeout(900)
            if act.endswith("L2") and not round_over():
                # 可能进入第二阶段(答案变化), 继续外层循环
                page.wait_for_timeout(400)
    elif act == "xiyouL3":
        while page.locator(".countable:not(.counted)").count() and time.time() < deadline:
            page.locator(".countable:not(.counted)").first.click(timeout=4000)
            page.wait_for_timeout(200)
        click_number_answer(page)
    elif act == "huluL1":
        ans = st0["answer"]
        if wrong_once:
            w = page.locator(f".pedestal-row button:not([data-pos='{ans}'])")
            if w.count(): w.first.click(); page.wait_for_timeout(500)
        page.locator(f".pedestal-row button[data-pos='{ans}']").click(timeout=5000)
    elif act == "huluL2":
        while not round_over() and time.time() < deadline:
            s = state(page)
            ans = s["answer"]
            loc = page.locator(f".waitline button[data-pos='{ans}']")
            if loc.count() and loc.first.is_visible():
                try: loc.first.click(timeout=2000)
                except Exception: pass
            page.wait_for_timeout(420)
    elif act == "huluL3":
        deadline2 = time.time() + 25
        while time.time() < deadline2 and not round_over():
            s = state(page)
            if s["phase"] == "swap" and "," in s["answer"]:
                i, j = s["answer"].split(",")
                for p in (i, j):
                    loc = page.locator(f".pedestal-row button[data-pos='{p}']")
                    if loc.count():
                        try: loc.first.click(timeout=2000)
                        except Exception: pass
                    page.wait_for_timeout(500)
                page.wait_for_timeout(800)
            elif page.locator(".cards .ncard").count():
                click_number_answer(page)
            else:
                page.wait_for_timeout(200)
    elif act in ("avengersL1", "avengersL2"):
        click_number_answer(page)
    elif act == "avengersL3":
        ans = st0["answer"]
        deadline2 = time.time() + 15
        while time.time() < deadline2 and not round_over():
            loc = page.locator(f".numball[data-value='{ans}']")
            if loc.count():
                bb = loc.first.bounding_box()
                if bb: page.mouse.click(bb["x"] + bb["width"]/2, bb["y"] + bb["height"]/2)
            page.wait_for_timeout(600)
    elif act == "pawL1":
        while page.locator(".bonepile .item:not(.dim)").count() and time.time() < deadline:
            page.locator(".bonepile .item:not(.dim)").first.click(timeout=4000)
            page.wait_for_timeout(230)
        click_icon_answer(page, wrong_first=wrong_once)
    elif act == "pawL2":
        click_number_answer(page)
    elif act == "pawL3":
        while page.locator(".bonepile .item:not(.dim)").count() and time.time() < deadline:
            page.locator(".bonepile .item:not(.dim)").first.click(timeout=4000)
            page.wait_for_timeout(230)
        click_number_answer(page)
    elif act.startswith("bluey"):
        while not round_over() and time.time() < deadline:
            if page.locator(".cards .ncard").count():
                click_number_answer(page)
            elif page.locator(".icards .icard").count():
                click_icon_answer(page)
            elif page.locator(".dicebtn:not([data-value])").count():
                try: page.locator(".dicebtn").click(timeout=2000)
                except Exception: pass
                page.wait_for_timeout(1600)
            else:
                page.wait_for_timeout(250)
    elif act == "peppaL1":
        while page.locator(".bonepile .item:not(.dim)").count() and time.time() < deadline:
            page.locator(".bonepile .item:not(.dim)").first.click(timeout=4000)
            page.wait_for_timeout(230)
        click_number_answer(page)
    elif act == "peppaL2":
        while not round_over() and time.time() < deadline:
            if page.locator(".cards .ncard").count():
                click_number_answer(page)
            else:
                loc = page.locator(".bonepile .item:not(.dim):visible")
                if loc.count():
                    try: loc.first.click(timeout=2000)
                    except Exception: pass
                page.wait_for_timeout(300)
    elif act == "peppaL3":
        click_number_answer(page)
    else:
        raise Fail(f"unknown activity {act}")
    # 等回合真正结束
    deadline3 = time.time() + 30
    while time.time() < deadline3:
        if round_over():
            return act
        page.wait_for_timeout(150)
    raise Fail(f"round did not finish: {act} r{st0['round']}")

def play_level(page, island, li, audit=None, wrong_once=False, shots_prefix=None):
    """从关卡页点击并玩完一关（4回合+庆祝）"""
    page.locator(f".lvbtn[data-level='{li}']").click(timeout=5000)
    deadline = time.time() + 20
    while time.time() < deadline:
        s = state(page)
        if s["scene"] == "scenePlay" and s["act"]:
            break
        page.wait_for_timeout(150)
    else:
        raise Fail(f"level {island} L{li+1} did not start")
    shot_done = False
    last_aid = None
    first = True
    for _ in range(8):
        # 只有当"新回合已挂载"(aid 变化)时才驱动; 末回合→庆祝的空档不再误驱动（防幽灵回合）
        fresh = None
        deadline_r = time.time() + 25
        while time.time() < deadline_r:
            s = state(page)
            if s["cele"] or s["scene"] != "scenePlay":
                fresh = "end"; break
            if s["act"] and s["aid"] != last_aid:
                fresh = s; break
            page.wait_for_timeout(150)
        if fresh == "end" or fresh is None:
            break
        last_aid = fresh["aid"]
        if shots_prefix and not shot_done:
            page.wait_for_timeout(500)
            page.screenshot(path=os.path.join(SHOTS, f"{shots_prefix}_{island}L{li+1}.png"))
            shot_done = True
        drive_round(page, audit=audit, wrong_once=(wrong_once and first))
        first = False
    # 庆祝 → 回关卡页
    deadline = time.time() + 25
    while time.time() < deadline:
        s = state(page)
        if s["cele"]:
            page.locator("#cele").click(timeout=4000)
        if s["scene"] == "sceneLevels":
            return
        page.wait_for_timeout(200)
    raise Fail(f"did not return to level select after {island} L{li+1}")

def enter_island(page, island):
    idx = ISLANDS.index(island)
    page.locator(".island").nth(idx).click(timeout=5000)
    page.wait_for_function("() => document.body.dataset.scene === 'sceneLevels'", timeout=10000)
    page.wait_for_timeout(300)

def unlock_all(page):
    page.evaluate("""() => { const d = window.__KM.Store.data;
      for(const k in d.islands){ d.islands[k].unlocked = 3; }
      window.__KM.Store.save(); }""")

def get_speech(page):
    return page.evaluate("window.__SPEECH.slice()")

def assert_speech_rules(log, label):
    speaks = [e for e in log if e["a"] == "speak"]
    welcome = [s for s in speaks if "欢迎来到数字小英雄乐园" in s["text"]]
    if len(welcome) != 1:
        raise Fail(f"{label}: welcome spoken {len(welcome)} times")
    last_cancel = None
    for e in log:
        if e["a"] == "cancel":
            last_cancel = e["t"]
        elif e["a"] == "speak" and last_cancel is not None:
            gap = e["t"] - last_cancel
            if gap < 148:
                raise Fail(f"{label}: speak {gap:.0f}ms after cancel: {e['text'][:20]}")
            last_cancel = None
    prev = None
    for s in speaks:
        # 意外双发是近同时的(<1.2s); 合法空闲重复最早也在 T(9000)(fast≈2s, 真机9s)之后
        if prev and s["text"] == prev["text"] and len(s["text"]) > 2 and (s["t"] - prev["t"]) < 1200:
            raise Fail(f"{label}: duplicate speak within 1.2s: {s['text'][:24]}")
        prev = s
    return len(speaks)

def count_words_in(log):
    return [e["text"] for e in log if e["a"] == "speak" and len(e["text"]) == 1 and e["text"] in NUM_CN]

def main():
    server = start_server()
    ok_all = True
    try:
        with sync_playwright() as pw:
            # ============ T1: chromium 六岛×三关全走查 + 解锁断言 + 语音时间线 ============
            errors = []
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={"width": 1180, "height": 820}, device_scale_factor=2)
            page = make_page(ctx, errors)
            try:
                page.goto(f"{BASE}/?fast=1&seed=42", wait_until="load")
                page.locator("#btnStart").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                page.wait_for_timeout(500)
                page.screenshot(path=os.path.join(SHOTS, "v2_map.png"))
                # 花果山: 新手状态 L1(含一次错误提交路径) → 解锁断言 → L2 L3
                enter_island(page, "xiyou")
                page.screenshot(path=os.path.join(SHOTS, "v2_levels.png"))
                locked = page.evaluate("() => document.querySelector('.lvbtn[data-level=\\'1\\']').classList.contains('locked')")
                if not locked:
                    raise Fail("L2 should start locked")
                play_level(page, "xiyou", 0, audit="t1", wrong_once=True, shots_prefix="v2")
                prog = page.evaluate("() => window.__KM.Store.data.islands.xiyou")
                if prog["stars"][0] != 1 or prog["unlocked"] < 2:
                    raise Fail(f"xiyou L1 completion not recorded: {prog}")
                play_level(page, "xiyou", 1, audit="t1", shots_prefix="v2")
                play_level(page, "xiyou", 2, audit="t1", shots_prefix="v2")
                page.locator("#btnLvBack").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                # 其余五岛: 解锁全部, 三关全玩
                unlock_all(page)
                for island in ISLANDS[1:]:
                    enter_island(page, island)
                    for li in range(3):
                        play_level(page, island, li, audit="t1",
                                   wrong_once=(island == "paw" and li == 0),
                                   shots_prefix="v2")
                    page.locator("#btnLvBack").click()
                    page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                if SIZE_VIOLATIONS:
                    raise Fail("targets <88px: " + "; ".join(SIZE_VIOLATIONS[:8]))
                log = get_speech(page)
                n_speaks = assert_speech_rules(log, "T1")
                words = count_words_in(log)
                seq_ok = any(words[i] == "一" and i + 1 < len(words) and words[i+1] == "二" for i in range(len(words)))
                if not seq_ok:
                    raise Fail("no ordered count sequence found")
                # 回家二次确认: 玩关中退出应回关卡页
                enter_island(page, "xiyou")
                page.locator(".lvbtn[data-level='0']").click()
                page.wait_for_function("() => document.body.dataset.scene === 'scenePlay'", timeout=10000)
                page.locator("#btnHome").click()
                page.wait_for_timeout(250)
                if state(page)["scene"] != "scenePlay":
                    raise Fail("home exited on single tap")
                page.locator("#btnHome").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneLevels'", timeout=5000)
                # 家长面板
                page.locator("#btnLvBack").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=5000)
                gear = page.locator("#gearMap")
                gear.hover(); page.mouse.down(); page.wait_for_timeout(3300); page.mouse.up()
                page.wait_for_selector("#parent.on", timeout=4000)
                if "Mock Tingting" not in page.locator(".pp .diag").inner_text():
                    raise Fail("parent panel voice missing")
                page.screenshot(path=os.path.join(SHOTS, "v2_parent.png"))
                page.locator("#ppClose").click()
                if errors:
                    raise Fail("console/page errors: " + " | ".join(errors[:5]))
                report("T1 六岛×三关全走查+解锁+语音时间线+回家/面板", True, f"{n_speaks} speaks")
            except Exception as e:
                ok_all = False
                page.screenshot(path=os.path.join(SHOTS, "t1_FAIL.png"))
                report("T1 v2 全走查", False, str(e)[:300])
            ctx.close(); br.close()

            # ============ T3: 快速连点压力（真实坐标） ============
            errors3 = []
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={"width": 1180, "height": 820})
            page = make_page(ctx, errors3)
            try:
                page.goto(f"{BASE}/?fast=1&seed=7&demo=0", wait_until="load")
                page.locator("#btnStart").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                enter_island(page, "xiyou")
                page.locator(".lvbtn[data-level='0']").click(timeout=5000)
                page.wait_for_function("() => document.body.dataset.scene === 'scenePlay'", timeout=10000)
                page.wait_for_timeout(600)
                end = time.time() + 3
                while time.time() < end:
                    for sel in (".peach-on-tree", "#btnDone", ".cards .ncard"):
                        loc = page.locator(sel)
                        if loc.count():
                            try:
                                bb = loc.nth(0).bounding_box()
                                if bb: page.mouse.click(bb["x"] + bb["width"]/2, bb["y"] + bb["height"]/2)
                            except Exception: pass
                    page.mouse.click(590, 400)
                page.wait_for_timeout(600)
                log = get_speech(page)
                words = count_words_in(log)
                for i in range(1, len(words)):
                    a, b = NUM_CN.index(words[i-1]), NUM_CN.index(words[i])
                    if b != a + 1 and b != 1:
                        raise Fail(f"count seq broken under spam: {words[max(0,i-3):i+1]}")
                if errors3:
                    raise Fail("errors: " + " | ".join(errors3[:5]))
                report("T3 快速连点压力（背压保序+无错误）", True, f"words={words[:10]}")
            except Exception as e:
                ok_all = False
                page.screenshot(path=os.path.join(SHOTS, "t3_FAIL.png"))
                report("T3 连点压力", False, str(e)[:300])
            ctx.close(); br.close()

            # ============ T4: 断网离线整关 ============
            errors4 = []
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={"width": 1180, "height": 820})
            page = make_page(ctx, errors4)
            try:
                page.goto(f"{BASE}/?fast=1&demo=0", wait_until="load")
                page.evaluate("() => navigator.serviceWorker.ready")
                page.wait_for_function("""() => caches.open('km-v1').then(c=>c.match('index.html')).then(r=>!!r)""", timeout=20000)
                page.wait_for_timeout(3000)
                ctx.set_offline(True)
                page.reload(wait_until="load")
                page.wait_for_selector("#btnStart", timeout=10000)
                page.locator("#btnStart").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                enter_island(page, "xiyou")
                play_level(page, "xiyou", 0)
                if errors4:
                    raise Fail("offline errors: " + " | ".join(errors4[:5]))
                report("T4 断网离线整关可玩（SW 缓存）", True)
            except Exception as e:
                ok_all = False
                page.screenshot(path=os.path.join(SHOTS, "t4_FAIL.png"))
                report("T4 离线", False, str(e)[:300])
            ctx.close(); br.close()

            # ============ T5: webkit 竖屏矩阵（六岛代表关卡 + 尺寸审计） ============
            errors5 = []
            br = pw.webkit.launch()
            ctx = br.new_context(viewport={"width": 820, "height": 1180}, device_scale_factor=2)
            page = make_page(ctx, errors5)
            try:
                page.goto(f"{BASE}/?fast=1&seed=9", wait_until="load")
                page.locator("#btnStart").click()
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                unlock_all(page)
                SIZE_VIOLATIONS.clear()
                matrix = [("xiyou", 0), ("xiyou", 2), ("hulu", 0), ("hulu", 1), ("avengers", 1), ("avengers", 2),
                          ("paw", 0), ("paw", 2), ("bluey", 0), ("bluey", 2), ("peppa", 1), ("peppa", 2)]
                for island, li in matrix:
                    enter_island(page, island)
                    play_level(page, island, li, audit="t5", shots_prefix="v2p")
                    page.locator("#btnLvBack").click()
                    page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                if SIZE_VIOLATIONS:
                    raise Fail("portrait targets <88px: " + "; ".join(SIZE_VIOLATIONS[:8]))
                if errors5:
                    raise Fail("errors: " + " | ".join(errors5[:5]))
                report("T5 webkit 竖屏矩阵(12关)+触摸目标≥88px", True)
            except Exception as e:
                ok_all = False
                page.screenshot(path=os.path.join(SHOTS, "t5_FAIL.png"))
                report("T5 webkit 竖屏", False, str(e)[:300])
            ctx.close(); br.close()

            # ============ T6: 运动目标真实命中（英雄城 L3 数字球, 动画开启零 force） ============
            errors6 = []
            br = pw.webkit.launch()
            ctx = br.new_context(viewport={"width": 1180, "height": 820})
            page = make_page(ctx, errors6, freeze=False)
            try:
                page.goto(f"{BASE}/?fast=1&seed=5&demo=0", wait_until="load")
                bb = page.locator("#btnStart").bounding_box()
                page.mouse.click(bb["x"] + bb["width"]/2, bb["y"] + bb["height"]/2)
                page.wait_for_function("() => document.body.dataset.scene === 'sceneMap'", timeout=8000)
                unlock_all(page)
                enter_island(page, "avengers")
                bb = page.locator(".lvbtn[data-level='2']").bounding_box()
                page.mouse.click(bb["x"] + bb["width"]/2, bb["y"] + bb["height"]/2)
                page.wait_for_function("() => document.body.dataset.scene === 'scenePlay'", timeout=10000)
                page.wait_for_selector(".numball", timeout=10000)
                ans = state(page)["answer"]
                hit = False
                for _ in range(5):
                    loc = page.locator(f".numball[data-value='{ans}']")
                    if loc.count() == 0:
                        hit = True; break
                    bb = loc.first.bounding_box()
                    if bb: page.mouse.click(bb["x"] + bb["width"]/2, bb["y"] + bb["height"]/2)
                    page.wait_for_timeout(500)
                    if loc.count() == 0 or "dim" in (loc.first.get_attribute("class") or ""):
                        hit = True; break
                if not hit:
                    raise Fail("moving numball not hittable")
                if errors6:
                    raise Fail("errors: " + " | ".join(errors6[:5]))
                report("T6 运动数字球真实命中（无 force）", True)
            except Exception as e:
                ok_all = False
                page.screenshot(path=os.path.join(SHOTS, "t6_FAIL.png"))
                report("T6 运动命中", False, str(e)[:300])
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
