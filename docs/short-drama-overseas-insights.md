# Short-Drama Overseas Insights (Sanlian Lifeweek PDFs)

This note captures recurring patterns and actionable implications from four Sanlian Lifeweek articles about short‑drama export, web‑fiction export, and overseas production. It is intended to guide story/script/timeline/storyboard agents and prompt design in this repo.

## Sources

- 短剧出海 — 三联生活网 (https://www.lifeweek.com.cn/article/258245?origin=6)
- 流量的进化与驯化：中国短剧如何卖给全球？— 三联生活网 (https://www.lifeweek.com.cn/article/258246?origin=6)
- 从百子湾到洛杉矶：投身短剧的电影学院毕业生 — 三联生活网 (https://www.lifeweek.com.cn/article/258247)
- 网文出海：中国叙事的复制与粘贴 — 三联生活网 (https://www.lifeweek.com.cn/article/258248)

## Core Observations (Content + Narrative)

- Short drama is treated as a product, not a traditional “work.” The priority is emotional hooks and release, not slow build or self‑expression.
- Hooks and reversals are engineered into early beats (“golden opening/前三章” logic); fast pacing and clear conflict are expected.
- Micro‑genres dominate (CEO/霸总, revenge, pregnancy/萌宝, werewolf/vampire, mafia, sports, etc.). The core emotional logic stays consistent, the “skin” changes.
- Hook density is not literally “every few seconds,” but is scheduled in a rhythm (emotional build → release) across early episodes.

## Production & SOP Patterns

- “投流表” (ad/traffic sheet) acts like a strict SOP: it includes performance references, music references, and storyboard/shots; missing these can force reshoots.
- Overseas production often expects “1:1 replication” of already validated domestic story models.
- Shot‑level precision is common (timing on specific words, exact gestures, key reaction close‑ups).

## Distribution & Traffic Insights

- Paid traffic is the dominant growth channel; ad materials often decide a show’s fate.
- 15‑second ad clips typically include multiple reversals and an explicit CTA (“Want more? Watch on …”).
- Ad materials are iterated rapidly; data feedback loops guide story rewrites or re‑edits.
- Web‑fiction export patterns (fast conflict, strong hook, “golden three chapters”) directly inform short‑drama export.

## Localization Realities

- Emotional logic can stay the same while the wrapper changes (CEO → mafia/werewolf; contract marriage → supernatural bond, etc.).
- U.S. audiences often expect a “revenge” follow‑through after reversal rather than “silent despair.”
- Cultural/ethical limits differ (e.g., violence toward children/animals is more sensitive), affecting allowable hook design.

## Implications for ai‑video‑studio Agents

- Story generation must be conditioned on **market_region** and **micro_genre**, not just “genre.”
- A **hook plan** should be produced at story + episode levels (intro hook, reversals, cliffhanger points, emotional release schedule).
- Scripts should output a **material plan** for ads: 15/30/60‑second segments, CTA copy, key frames, and subtitle hooks.
- Timeline and storyboard agents should expose/align to hook beats and “reaction close‑ups” that sell the emotion.
- Add a scoring layer (HookScore/ScriptScore) to rate conflict density, clarity, hook strength, and material extractability.

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

