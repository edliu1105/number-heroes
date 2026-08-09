/* 数字小英雄 service worker — 页面网络优先 / 素材缓存优先 */
const CACHE = 'km-v1';
const CORE = [
  './',
  'index.html',
  'manifest.webmanifest',
  'assets/icons/icon-192.png',
  'assets/icons/icon-512.png',
  'assets/icons/apple-touch-icon.png'
];
const ASSETS = [
  'assets/char/bailongma.png',
  'assets/char/bajie.png',
  'assets/char/bandit.png',
  'assets/char/bingo.png',
  'assets/char/blackwidow.png',
  'assets/char/bluey.png',
  'assets/char/cap.png',
  'assets/char/chase.png',
  'assets/char/chilli.png',
  'assets/char/george.png',
  'assets/char/gwen.png',
  'assets/char/hawkeye.png',
  'assets/char/hulk.png',
  'assets/char/hulu1.png',
  'assets/char/hulu2.png',
  'assets/char/hulu3.png',
  'assets/char/hulu4.png',
  'assets/char/hulu5.png',
  'assets/char/hulu6.png',
  'assets/char/hulu7.png',
  'assets/char/ironman.png',
  'assets/char/mama.png',
  'assets/char/marshall.png',
  'assets/char/miles.png',
  'assets/char/papa.png',
  'assets/char/peppa.png',
  'assets/char/rocky.png',
  'assets/char/rubble.png',
  'assets/char/ryder.png',
  'assets/char/shejing.png',
  'assets/char/skye.png',
  'assets/char/spiderman.png',
  'assets/char/tangseng.png',
  'assets/char/thor.png',
  'assets/char/wujing.png',
  'assets/char/wukong.png',
  'assets/char/xiezijing.png',
  'assets/char/yeye.png',
  'assets/char/zuma.png',
  'assets/item/apple.png',
  'assets/item/ball.png',
  'assets/item/baozi.png',
  'assets/item/basket.png',
  'assets/item/bone.png',
  'assets/item/bowl.png',
  'assets/item/cookie.png',
  'assets/item/hulu.png',
  'assets/item/peach.png',
  'assets/item/puddle.png',
  'assets/item/star.png',
  'assets/item/tree.png',
  'assets/item/web.png',
  'assets/bg/bg_avengers.png',
  'assets/bg/bg_bluey.png',
  'assets/bg/bg_hulu.png',
  'assets/bg/bg_paw.png',
  'assets/bg/bg_peppa.png',
  'assets/bg/bg_sky.png',
  'assets/bg/bg_xiyou.png',
  'assets/bg/isl_avengers.png',
  'assets/bg/isl_bluey.png',
  'assets/bg/isl_hulu.png',
  'assets/bg/isl_paw.png',
  'assets/bg/isl_peppa.png',
  'assets/bg/isl_xiyou.png'
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
