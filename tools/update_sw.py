# -*- coding: utf-8 -*-
"""Regenerate sw.js precache list from files on disk (run after asset changes)."""
import os, io

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_VER = "km-v2"

def main():
    core = ["./", "index.html", "manifest.webmanifest",
            "assets/icons/icon-192.png", "assets/icons/icon-512.png", "assets/icons/apple-touch-icon.png"]
    assets = []
    for sub in ["assets/char", "assets/item", "assets/bg"]:
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(".png"):
                assets.append(f"{sub}/{f}")
    core_lst = ",\n  ".join(f"'{a}'" for a in core)
    lst = ",\n  ".join(f"'{a}'" for a in assets)
    sw = """/* 数字小英雄 service worker — 页面网络优先 / 素材缓存优先 */
const CACHE = '%s';
const CORE = [
  %s
];
const ASSETS = [
  %s
];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    // 核心 shell 原子安装: 任一失败 → 整个 install 失败, 旧版本缓存保持可用（A4）
    await c.addAll(CORE);
    // 可选素材逐个缓存, 单项失败不阻塞（运行时缓存补齐）
    await Promise.allSettled(ASSETS.map(u => c.add(u)));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  const isPage = req.mode === 'navigate' || url.pathname.endsWith('/index.html') || url.pathname.endsWith('/');
  if (isPage) {
    // 网络优先：修 bug 后用户刷新即得新版；断网回退缓存
    e.respondWith((async () => {
      try {
        const r = await fetch(req);
        if (r && r.ok) {
          const copy = r.clone();
          e.waitUntil(caches.open(CACHE).then(c => c.put(req, copy)));  // 回填在 worker 生命周期内完成
        }
        return r;
      } catch (err) {
        const c = await caches.open(CACHE);
        return (await c.match(req)) || (await c.match('./')) || (await c.match('index.html')) || Response.error();
      }
    })());
    return;
  }
  // 素材缓存优先，未命中回源并回填
  e.respondWith((async () => {
    const hit = await caches.match(req);
    if (hit) return hit;
    try {
      const r = await fetch(req);
      if (r && r.ok) {
        const copy = r.clone();
        e.waitUntil(caches.open(CACHE).then(c => c.put(req, copy)));
      }
      return r;
    } catch (err) { return Response.error(); }
  })());
});
""" % (CACHE_VER, core_lst, lst)
    with io.open(os.path.join(ROOT, "sw.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write(sw)
    print(f"sw.js written with {len(assets)} precache entries")

if __name__ == "__main__":
    main()
