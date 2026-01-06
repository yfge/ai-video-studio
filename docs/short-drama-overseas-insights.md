# Short-Drama Overseas Insights (Sanlian Lifeweek PDFs)

This note captures recurring patterns and actionable implications from four Sanlian Lifeweek articles about short‑drama export, web‑fiction export, and overseas production. It is intended to guide story/script/timeline/storyboard agents and prompt design in this repo.

## Sources

- 短剧出海 — 三联生活网 (https://www.lifeweek.com.cn/article/258245?origin=6)
- 流量的进化与驯化：中国短剧如何卖给全球？— 三联生活网 (https://www.lifeweek.com.cn/article/258246?origin=6)
- 从百子湾到洛杉矶：投身短剧的电影学院毕业生 — 三联生活网 (https://www.lifeweek.com.cn/article/258247)
- 网文出海：中国叙事的复制与粘贴 — 三联生活网 (https://www.lifeweek.com.cn/article/258248)

## Key Metrics & Market Signals

- 海外短剧 App 规模：约 300 款出海应用，累计下载量超 4.7 亿；2025 年 1-8 月海外收入贡献超 15 亿美元。
- 爆款规模：单剧播放量可达 4-5 亿级；付费单集约 0.7-0.9 美元，但用户整剧累计付费高于影院单片票价。
- App 结构：单剧常见 60-80 集，题材以“身份隐藏/甜宠/逆袭/萌宝”叠加为主。

## Core Observations (Content + Narrative)

- Short drama is treated as a product, not a traditional “work.” The priority is emotional hooks and release, not slow build or self‑expression.
- Hooks and reversals are engineered into early beats (“golden opening/前三章” logic); fast pacing and clear conflict are expected.
- Micro‑genres dominate (CEO/霸总, revenge, pregnancy/萌宝, werewolf/vampire, mafia, sports, etc.). The core emotional logic stays consistent, the “skin” changes.
- Hook density is not literally “every few seconds,” but is scheduled in a rhythm (emotional build → release) across early episodes.
- 早期免费集强调“先交代核心关系 + 情绪积压”，逻辑可适度压缩；常见节奏是前 10 集内释放 3 个爆点（6/8/10 集）。
- “爽点库”与评分体系成为创作入口，情绪冲突强度与可剪素材密度优先级高于传统叙事完整性。

## Production & SOP Patterns

- “投流表” (ad/traffic sheet) acts like a strict SOP: it includes performance references, music references, and storyboard/shots; missing these can force reshoots.
- Overseas production often expects “1:1 replication” of already validated domestic story models.
- Shot‑level precision is common (timing on specific words, exact gestures, key reaction close‑ups).
- 投流表常以 Excel 形式下发（约 30 条具体拍摄要求），包含台词字词触发的动作、表演与配乐参考、分镜截图。
- “反应镜头”比动作更重要：如扇巴掌后的特写与群众反应是核心卖点，需预先锁定机位与节奏。

## Distribution & Traffic Insights

- Paid traffic is the dominant growth channel; ad materials often decide a show’s fate.
- 15‑second ad clips typically include multiple reversals and an explicit CTA (“Want more? Watch on …”).
- Ad materials are iterated rapidly; data feedback loops guide story rewrites or re‑edits.
- Web‑fiction export patterns (fast conflict, strong hook, “golden three chapters”) directly inform short‑drama export.
- 投放成本占比极高（常见 80%+），素材制作节奏快：2 小时内完成“拉片选点/评级”，按 15/30/60 秒拆出数百条素材。
- 优化师以 30-60 分钟粒度监控投放数据，ROI 低于阈值会即时停投或换素材。
- 北美平均获客成本 > $10；行业常看 Day1 ROI 0.4-0.5，回本周期约 4-6 个月。

## Localization Realities

- Emotional logic can stay the same while the wrapper changes (CEO → mafia/werewolf; contract marriage → supernatural bond, etc.).
- U.S. audiences often expect a “revenge” follow‑through after reversal rather than “silent despair.”
- Cultural/ethical limits differ (e.g., violence toward children/animals is more sensitive), affecting allowable hook design.
- “追妻火葬场/后悔流”在北美常被改写为“复仇流”，情绪反弹后的行动更激烈、主动。
- “霸总一通电话让人消失”在美式语境不成立，常转译为黑帮/吸血鬼/狼人权力结构。
- 道具与金融细节需本地化（例如美股红跌绿涨 vs A 股红涨绿跌）。

## Web‑Fiction Export Patterns (Upstream Supply)

- 网文是短剧素材库的核心上游：累计 4000 万+ 作品、3000 万+ 作者，形成“题材爆炸 + 细分微类型”生态。
- “黄⾦三章/快速钩子/频繁反转”已成为通用叙事语法，被海外作者复制与本地化。
- 海外本土作者会“换皮”中国叙事结构（狼⼈/黑帮/校园等外壳），但保留“升级打脸/逆袭”骨架。

## Implications for ai‑video‑studio Agents

- Story generation must be conditioned on **market_region** and **micro_genre**, not just “genre.”
- A **hook plan** should be produced at story + episode levels (intro hook, reversals, cliffhanger points, emotional release schedule).
- Scripts should output a **material plan** for ads: 15/30/60‑second segments, CTA copy, key frames, and subtitle hooks.
- Timeline and storyboard agents should expose/align to hook beats and “reaction close‑ups” that sell the emotion.
- Add a scoring layer (HookScore/ScriptScore) to rate conflict density, clarity, hook strength, and material extractability.
- 把“投流表/素材清单”作为交付物，确保拍摄层级的动作触发点与反应镜头被标注。
- 素材策略需支持“快速 A/B 迭代”：输出可替换桥段与备用钩子（以便投放数据回流后快速剪改）。

## Suggested Data/Prompt Fields

- `market_region` (e.g., NA/SEA/EU)
- `micro_genre` (e.g., CEO revenge, werewolf romance, mafia revenge)
- `hook_plan` (early hook + reversal cadence)
- `twist_density` (target count per episode/segment)
- `cliffhanger_plan`
- `ad_snippets` (15/30/60‑second cut plan + CTA)

## Open Questions

- What are the highest‑ROI micro‑genres for our first target regions?
- What is the minimum viable “hook cadence” spec to encode in prompts without harming variety?
- Where do we store/serve “投流表” outputs: script metadata vs. a dedicated model?
