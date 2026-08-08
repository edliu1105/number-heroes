# 对第五轮审查（REJECT）的逐条回应

两个阻塞项 + 全部 P2 尾项已修复, 套件 ALL GREEN（review/test_run14.log, 新增比较错误路径断言）。

## 阻塞项处置

### P0-03（assisted 兜底教错/指向无效）——已修

空闲第二次提醒的锚点改为**每活动注册的动态求值函数**, 指点瞬间实时求值, 永远指向"当前正确的下一步"; 无有效锚点时只重复语音、不指点（宁缺毋错）:

| 活动 | 动态锚点函数 |
|---|---|
| count / add | 下一个未数物品 → 全数完后为答案牌**区域**（.cards 容器, 不指具体牌不泄答案） |
| numeral | **正确气球**（未爆的 target 气球; 指点=脚手架, assisted 已置位） |
| produce | `fed >= n` → **绿勾按钮**; 未够 → 下一个可喂物品（消除"诱导多喂"路径） |
| compose | 下一个未放物品 → 答案牌区域 |
| flash | 答案牌区域 |
| compare | 多的一侧（视觉胜者=正确教学） |

通用 CSS 选择器兜底已删除。首遇示范与二次指点全部经此路径。

### P1-02（旧回调污染新语境）——已修

- `_speakNow` 的 finish（含事件/超时看门狗全部路径）现按**代际 + 当前话语 uid** 双闸：`gen !== this._gen`（stopAll 之后）或 `_instrUid !== uid`（同代际内被更新的说话）时, 只释放自身引用与 Promise, **不触碰** `_instrActive` / duck / `_activeCountSay`——这些全局状态归新语境所有（stopAll 已重置）。
- `_enqCount` 的 fin 同样按代际退休：过期数词回调不再操作新语境的 `_countQ` / `_latestCount` 链。
- 由此: cancel 无终止事件的场景下, 旧看门狗迟到触发也不会清掉新语音状态或让 drain 早判。

## P2 尾项

- **P2-04**：DESIGN 素材清单行改为 39 角色/60 张；README 测试描述改为八组。
- **P2-05**：未复核 ADVISORY 现使 `qa_assets.py` **退出码 1**（硬门槛）, 打印文案明示 "gate FAILS until eyeballed & added to REVIEWED"。
- **截图缺口**：新增 T1 比较错误路径流程——点错侧 → `wait_for_selector('.crown')` 硬断言星星胜者标识出现 → 截图 `t1_compare_crown.png` → 纠正完成。星标已锚定到获胜角色头顶（offsetTop 定位）。

## 请求

第六轮请核验以上两个阻塞项与 P2 尾项。所有既往编号问题至此全部处置完毕（你第五轮逐项复核表中其余项均已判闭合）。若再无 P0/P1 实质缺陷, 请给 APPROVE（非阻塞新建议请列"非阻塞建议"清单）。
