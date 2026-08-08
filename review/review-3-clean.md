## A. 指定项目闭合核验

| 项目 | 判定 | 核验结果 |
|---|---|---|
| P0-T1 喂一喂提交式测量 | 核心闭合 | `m>n`、首喂后显示绿勾、主动提交、严格 `fed===n`、首提交独立判定均已实现，[index.html:954](/D:/ClaudeCode/kidmath/index.html:954)、[index.html:995](/D:/ClaudeCode/kidmath/index.html:995)。但错误处理期缺少锁，另列 P1。 |
| P0-U1 幽灵手+点阵卡 | 未闭合 | 点阵卡已存在；但找数字的幽灵手指向随机的 `balloons[0]`，多数时候会示范错误答案，[index.html:913](/D:/ClaudeCode/kidmath/index.html:913)、[index.html:934](/D:/ClaudeCode/kidmath/index.html:934)。`flash/add` 没有首次幽灵手，绿勾出现后也未指向绿勾。 |
| I8 计数背压 | 部分闭合 | 点击背压真实存在，[index.html:837](/D:/ClaudeCode/kidmath/index.html:837)。但最后一击只固定等待 700ms 后发问，[index.html:843](/D:/ClaudeCode/kidmath/index.html:843)；若仍有两个数词在播/排队，新指令会 `cancel` 并清空计数队列，[index.html:376](/D:/ClaudeCode/kidmath/index.html:376)。不能保证真机完整播到末数。 |
| A4 SW 原子安装 | 闭合原问题 | 核心 shell 使用 `cache.addAll`，素材才 `allSettled`，[sw.js:71](/D:/ClaudeCode/kidmath/sw.js:71)。 |
| A5 零 force | 闭合原问题 | 源码没有 `force=`，运动气球使用实时包围盒坐标点击，[run_tests.py:423](/D:/ClaudeCode/kidmath/tests/run_tests.py:423)。但压力测试仍用合成 `dispatch_event`，不属于真实命中。 |
| T4 徽章提问时淡出 | 闭合 | `count/add` 均在提问前淡出徽章，[index.html:847](/D:/ClaudeCode/kidmath/index.html:847)、[index.html:1190](/D:/ClaudeCode/kidmath/index.html:1190)。 |
| T5 脚手架阶梯 | 部分闭合 | 数字牌实现“重数→正确牌脉冲”，[index.html:773](/D:/ClaudeCode/kidmath/index.html:773)；但空闲提示/幽灵手不会把结果降为 hinted，喂食错误流程也有并发竞争。 |
| U7 音效闪避 | 部分闭合 | 指令语音期间主增益会降至 `.16`，[index.html:414](/D:/ClaudeCode/kidmath/index.html:414)。计数词通道没有 duck，`pop/chomp` 仍可能与关键数词重叠。 |
| U2 回家确认 | 闭合 | 88px 命中框及 2.6 秒内二次确认均实现，[index.html:56](/D:/ClaudeCode/kidmath/index.html:56)、[index.html:1279](/D:/ClaudeCode/kidmath/index.html:1279)。 |
| I2 被吞恢复 | 部分闭合 | 同 request 的一次重试已实现，[index.html:429](/D:/ClaudeCode/kidmath/index.html:429)；但没有 attemptId，原 utterance 延迟启动时仍可能与重试重复，且活动切换不增加语音 generation。 |
| I10 生命周期 | 未闭合 | `AudioContext.statechange` 是空处理且只恢复 `suspended`，[index.html:524](/D:/ClaudeCode/kidmath/index.html:524)；`pagehide` 暂停无声 loop 后没有可靠的 pageshow/下一手势重启；活动切换也没有执行约定的 `Speech.stopAll()`，[index.html:1389](/D:/ClaudeCode/kidmath/index.html:1389)。 |

## 六维结论

- 幼儿数学教学法：不通过。按数取物、感数、合成、基数探测的结构基本成立，但固定答案位置和 assisted→independent 误计会污染自适应数据。
- 三岁半可用性：不通过。单点、幂等、回家确认不错；首次示范不完整且部分示范会指错，组合活动还有小于 88px 的核心目标。
- 视觉品质：条件通过。地图、角色层级、物品可辨性总体达到可玩水准；但葫芦背景与教学物同形、感数遮罩像占位稿，[合成截图](/D:/ClaudeCode/kidmath/review/shots/t1_1_compose.png)、[感数截图](/D:/ClaudeCode/kidmath/review/shots/t1_2_flash.png)。
- 代码质量：不通过。模块分区清楚、零依赖，但喂食状态竞争、语音生命周期和损坏存储校验仍不足。
- 性能：条件通过。素材约 4.41 MiB、HTML 约 78 KB，磁盘预算通过；实际 FTI、解码峰值、反馈延迟没有测试，隐藏 boot/map 图片也没有按契约卸载。
- iOS WebKit：不通过。同步手势解锁、180ms cancel 间隔、中文声音选择、安全区和 `dvh` 已落实；§9.6 的 pageshow、interrupted AudioContext、活动 generation、无声 loop 恢复仍与实现不符。

## B. 本轮代码级问题

### P0

1. **P0-01｜“谁的多”正确答案永远在左侧/上侧。** 生成器固定 `a=big,b=small`，[index.html:633](/D:/ClaudeCode/kidmath/index.html:633)，随后固定先构建 `a` 侧，[index.html:1062](/D:/ClaudeCode/kidmath/index.html:1062)。孩子无需比较即可永远点第一侧，旧 P1-T7 的位置平衡因此重开。

2. **P0-02｜提示后完成仍会被记录为 independent。** `ctx.nudges` 和空闲幽灵手没有进入 outcome，[index.html:1233](/D:/ClaudeCode/kidmath/index.html:1233)；最终仍只把 `firstTry` 传给技能系统，[index.html:1373](/D:/ClaudeCode/kidmath/index.html:1373)。这直接违反 DESIGN §9.1“未触发任何脚手架”。

3. **P0-03｜无文字首次引导会漏教或教错。** 找数字可能指错气球；`flash/add` 无首次示范；比较活动在无声状态下没有视觉信息表达“请选择更多的一边”；喂食绿勾出现后未由幽灵手介绍。P0-U1 尚未闭合。

### P1

1. **P1-01｜计数背压没有“等待队列排空”完成条件。** 需要 `awaitCountsDrained()` 或等价状态，而不是 700ms 猜测，并增加慢 TTS/高延迟用例。

2. **P1-02｜Speech/I10 状态机与 §9.6 不一致。** 活动切换不 stop/gen++；pageshow 不清计数队列；无声 loop 可能永久停在 pagehide 后；`interrupted/closed` AudioContext 不恢复；被吞重试缺少 attempt 仲裁。

3. **P1-03｜喂食错误反馈期无输入锁。** `onSubmit` 在错误分支 await 多段语音时仍允许继续喂和再次提交，[index.html:995](/D:/ClaudeCode/kidmath/index.html:995)、[index.html:1029](/D:/ClaudeCode/kidmath/index.html:1029)。快速双击会重复累计 attempts、并发复位和提前触发二级脚手架。

4. **P1-04｜88px 与高阶合成布局未兑现。** 合成物品是 `10.5vmin/min 62px`，[index.html:137](/D:/ClaudeCode/kidmath/index.html:137)；768px 宽 iPad 上约 81px。重听按钮也可能只有约84px。L3 的 10 件合成物在窄屏会与槽位/答案区竞争空间。

5. **P1-05｜测试名称超过实际覆盖。** WebKit 竖屏最终日志只覆盖 `count/numeral`；尺寸断言用 86px 且遗漏 `.srcgrp .item`，[run_tests.py:403](/D:/ClaudeCode/kidmath/tests/run_tests.py:403)。压力测试使用 `dispatch_event`，[run_tests.py:330](/D:/ClaudeCode/kidmath/tests/run_tests.py:330)；离线只完成一个活动；T1 会在活动类型齐全后提前停止，不保证六岛全流程。

6. **P1-06｜葫芦场景违反可数性隔离。** 背景含大量同形葫芦，教学葫芦又放在边缘，count/compose 中可能被儿童误计。应换成无葫芦背景或把所有教学物放入明确实体面板。

7. **P1-07｜性能契约未被实现或测量。** boot/map 图片在初始化时永久创建，[index.html:1267](/D:/ClaudeCode/kidmath/index.html:1267)、[index.html:1313](/D:/ClaudeCode/kidmath/index.html:1313)，`show()` 只是隐藏场景，[index.html:1331](/D:/ClaudeCode/kidmath/index.html:1331)，并非 DESIGN 声称的卸载；庆祝时 36 粒子+6 舞者+星星也超过“同时动画≤40”。

### P2

1. **P2-01｜SW 运行时回填未 await。** 两处 `cache.put()` 均为 fire-and-forget，[sw.js:101](/D:/ClaudeCode/kidmath/sw.js:101)，worker 可在写入完成前终止。

2. **P2-02｜损坏存储没有真正结构校验。** `rot/irot/seen` 直接接受任意真值，[index.html:299](/D:/ClaudeCode/kidmath/index.html:299)；若为字符串或数组，严格模式下活动初始化可能抛错。

3. **P2-03｜素材 QA 与声明不符。** 脚本注释声称检查 edge halo，但实际只检查角 alpha、bbox 和接边，[qa_assets.py:23](/D:/ClaudeCode/kidmath/tools/qa_assets.py:23)；bbox 阈值也是 20%–98.5%，不是 DESIGN 的 25%–95%。

4. **P2-04｜视觉收尾和文档整合不足。** 感数遮罩是大面积空白板加小 emoji 云；角色与背景风格仍有明显批次差。DESIGN 旧正文仍保留“六种活动”、旧喂食规则和守恒声明，与 §9 修订并存。

进入下一轮的最低条件是：先修复三个 P0；再补计数排空、完整 I10 状态机、喂食锁、比较位置平衡测试，以及覆盖七活动的 WebKit 横竖屏矩阵。

VERDICT: REJECT
