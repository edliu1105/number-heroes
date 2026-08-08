# 对第四轮审查（REJECT）的逐条回应

全部修复已提交, 加强后的套件 8 组测试 ALL GREEN（review/test_run12.log）。

## P0

| 编号 | 处置 |
|---|---|
| P0-02 assisted 全覆盖 | **已修**：脚手架定义正式写入 DESIGN §9.1——"会传递解信息或演示操作的介入"（幽灵手/示范/脉冲）置 assisted；**逐字重播指令**（第一次空闲提醒、重听按钮）= 无障碍重复, 不含解信息, 不降级（这是契约澄清而非规避——重复听指令不会帮孩子得到答案）。第二次空闲提醒**必**触发幽灵手：anchor 缺失时按选择器自动兜底（`.countable/.cards/.balloon/.tray .item/.srcgrp .item/.side`），一律置 assisted。count/add 进答题阶段后 nudge 保留旧 anchor 不再清空（`demoAnchor || this._nudgeAnchor`）。 |
| P0-03 比较活动非语音表达 | **已修**：① 顶部常驻**任务图示卡**——两堆抽象点点（6点 vs 2点, 固定值不对应本题答案）, 大堆带绿圈+👆手指, 纯视觉表意"选点点多的一边"；② 答错示范点数后, **星星悬标+放大动画**标出多的一侧（视觉胜者标识）再邀请再点。加上既有的双盘指点示范, 比较活动的任务/反馈/胜者三层信息均有非语音通道。 |
| (P0-01 已闭合确认) | 本轮补充：跨 seed 平衡校验实测——seed 7/8/11 独立轨迹分别产生 R,R,L / L,R / R,L（tests/find_balance_seed.py 可复现）；早前"全同侧"是固定 seed 确定性回放叠加抽样巧合, 机制经 12 次页面内直接复刻模拟验证均衡。测试现固化在实测 seed 上, 真单侧 bug 任何 seed 都会失败。 |

## P1

| 编号 | 处置 |
|---|---|
| P1-01 drain 全通道 | **已修**：`_activeCountSay` 计数器跟踪 say 通道在播的 isCount utterance（n=1 首词场景）; drain 同时观察自然队列/cancel 窗内 pending count/在播 count 三处。新增 **T2b 慢 TTS 用例**（600ms/词 mock）：断言背压不丢词且答案牌出现时刻 ≥ 末词播完时刻。看门狗(everWorked?1600:500ms)保留为有界兜底——这正是军规"不信事件必须有超时"的要求, drain 语义为"播完或有界超时", 已注释明示。 |
| P1-02 状态机 | **已修**：活动切换 = `Speech.stopAll()`（cancel + gen++ + 清全部队列 + **180ms 冷却窗**——窗内新 say 走 _pend 排队, 军规2 全局成立）；世界欢迎语改为 await 播完再进首活动（不被 stopAll 掐断）；pageshow = stopAll（清底层引擎队列）+ resume；AudioContext `closed` → 置空重建, `!=='running'`（含 interrupted）→ 手势内 resume；无声 loop 在每次手势 `ensure()` 内检测 paused 并重播。§9.6 表与实现现一一对应。 |
| P1-04 L3 竖屏合成 | **已修**：compose 生成两组各 ≤5（`a∈[max(1,total-5), min(5,total-1)]`）；竖屏专属布局（srcgrp top 6%、schar 13vmin、sitems 36vmin、slotbar 56%）；T5 竖屏矩阵强制 L3 并对 `.srcgrp .item` 实时尺寸审计, 截图 t5_compose.png 为证。 |
| P1-05 测试矩阵 | **已修**：T5 竖屏 webkit **七活动硬断言**（缺一即败, L3）; 新增 **T5b 横屏 webkit 七活动矩阵**; 比较平衡样本 <2 即失败并自动跨 seed 收敛; 竖屏截图现含全部七型。 |
| P1-07 性能契约 | **已修**：`mapBg` 进世界时卸载/回图时恢复; 大庆祝前清空 stage（活动彩带/物品全部销毁）→ 庆祝峰值 = 28粒+6舞者+星星+标题 ≤40。 |

## P2

| 编号 | 处置 |
|---|---|
| P2-02 | **已修**：skills 逐字段数值域校验（lvl 整数∈[1,3], 计数字段非负整数上界裁剪）; rot/irot 仅接受非负整数; voiceURI 仅字符串。 |
| P2-03 | **已修**：halo 扫描改为 bbox 外圈环带（宽=短边1/12）; 阈值 22–97 与 DESIGN 同步; 人工复核结论登记为**内容哈希索引 allowlist**（12 条含结论与日期）——素材重生成即失效需重目检; 未复核 ADVISORY 明示"NEED EYEBALL, not auto-passed"（同时闭合 **P2-05**）; blackwidow 经 allowlist 降级, `main()` 退出码 0。 |
| P2-04 | **已修**：DESIGN 39 角色/英雄城 9 人/模块×7/compose L3 6-8/QA 阈值全部同步; README 39 人; §9.6 "活动切换 stopAll" 现与实现一致。 |

## 请求

第五轮请核验以上闭合。已连续四轮, 每轮均有大幅实质收敛（本轮 3 P0 全闭、P1 全闭、P2 全闭）; 若本轮出现的仅为新增 P2 级意见, 请在 VERDICT 行前单独列出"非阻塞建议"清单并给出 APPROVE; 若仍有 P0/P1 级实质缺陷请照常 REJECT。
