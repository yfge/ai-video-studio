# Short-Drama Micro-Genre & Performance-Led Creation Spec

This document defines the market x micro-genre matrix, a Story Bible template, hook/twist cadence rules, and the standard ad-material (traffic) sheet structure. It is the baseline for story, script, timeline, and storyboard agents.

## Goals

- Anchor story and script generation in market-specific micro-genre rules.
- Encode hook, twist, and cliff cadence so early episodes deliver payoffs fast.
- Produce ad-ready material plans (15/30/60s) as first-class outputs.
- Standardize scoring so low-performing scripts trigger rewrite guidance.

## Market x Micro-Genre Matrix (Draft v1)

| Market | Micro-Genre Cluster         | Primary Audience | Core Hook Archetype           | Localization Wrapper             | No-Go / Risk Flags      |
| ------ | --------------------------- | ---------------- | ----------------------------- | -------------------------------- | ----------------------- |
| NA     | Mafia romance revenge       | F18-34           | Betrayal -> retaliation       | Organized crime / family dynasty | Child harm, non-consent |
| NA     | Werewolf mate drama         | F18-34           | Fate-bonded rejection         | Supernatural clans               | Underage romance        |
| NA     | Billionaire secret identity | F18-34           | Hidden power reveal           | Tech/finance elite               | Abuse glamorization     |
| LATAM  | Revenge + family honor      | F18-44           | Humiliation -> comeback       | Telenovela family saga           | Domestic violence       |
| LATAM  | Forbidden romance           | F18-34           | Social taboo reveal           | Class/faith barriers             | Religious sensitivity   |
| SEA    | CEO contract marriage       | F18-34           | Marriage deal -> real love    | Corporate heir                   | Stalking/harassment     |
| SEA    | Campus revenge              | F16-28           | Bullying -> status flip       | School/club rivalry              | Minor safety            |
| MENA   | Elite family intrigue       | F18-34           | Family betrayal               | Estate/inheritance               | Explicit content        |
| KR/JP  | Idol scandal romance        | F18-34           | Public disgrace -> redemption | Entertainment industry           | Defamation risk         |
| Global | Secret baby / hidden heir   | F18-44           | Child reveal                  | Hospital/legacy drama            | Infant endangerment     |

Notes:

- This matrix is a starting point; update monthly using ad performance data.
- Each micro-genre should map to a Story Bible (see template).

## Story Bible Template (Micro-Genre Specific)

Use this template per market x micro-genre. Keep each section concise (bullets). The Story Bible is the contract between Story -> Script -> Timeline -> Storyboard.

- Market region
- Micro-genre name
- Audience persona (age, motivations, content tolerance)
- Core hook library (3-5 hook archetypes)
- Emotional engine (what builds, what releases, how fast)
- Primary conflict ladder (episode 1-10 progression)
- Character identity anchors (visual/behavioral tags that help recognition)
- Taboo list / compliance guardrails
- Localization wrapper (setting, status symbols, cultural markers)
- Ad material targets (top 5 sellable beats, CTA angles)
- Metrics to optimize (hook retention, ROI proxy, clip yield)

## Hook / Twist / Cliff Cadence Rules

Define cadence at both episode and season levels. These are default guardrails, not rigid formulas.

### Episode Cadence (60-120 seconds)

- Cold open hook within first 5-8 seconds (visual or line).
- Inciting conflict within first 20-30 seconds.
- At least 1 reversal per episode (2 if episode > 90s).
- Cliffhanger must land in final 6-10 seconds.

### Early-Season Cadence (Episodes 1-10)

- Episodes 1-3: establish core relationship + 1 high-stakes betrayal/reveal.
- Episodes 4-6: first payoff release + escalation into new obstacle.
- Episodes 7-10: second payoff + decisive setback or irreversible reveal.

### Twist Density Targets

- Episode twist density: 1.0-1.5 (1 twist minimum, 2 for big beats).
- Micro-genre adjustment:
  - Revenge/mafia: 1.5-2.0 (higher volatility)
  - Romance/contract: 1.0-1.2 (steady emotional rhythm)
  - Supernatural: 1.2-1.6 (mystery reveals + power moments)

## Ad Material (Traffic Sheet) Standard Structure

The traffic sheet is a production-facing output that drives paid acquisition. It must be exportable as JSON and CSV. Each row describes one cuttable asset.

Required fields:

- asset_id
- duration_seconds (15 / 30 / 60)
- market_region
- micro_genre
- hook_type (betrayal, reveal, revenge, reunion, threat, taboo, power-shift)
- source_episode
- source_timecode_start / source_timecode_end
- key_line (subtitle anchor)
- visual_hook (first-frame action)
- shot_list (1-5 key shots)
- cliff_or_cta (CTA line + destination)
- music_reference (optional)
- compliance_flags (optional)

### Asset Count Targets (Per 10 Episodes)

- 15s assets: 12-20
- 30s assets: 6-10
- 60s assets: 2-4

## Script Scoring (HookScore / ScriptScore)

Each script receives a scorecard and structured feedback. The score drives auto-rewrite suggestions.

### Dimensions (0-5 each)

- Conflict intensity
- Character recognizability
- Cultural fit / localization
- Clip-ability (cuttable hooks per 60s)
- Logic coherence (continuity + clarity)

### Thresholds

- Pass: overall >= 4.0 and no dimension below 3.5
- Review: overall 3.5-3.9 or any dimension 3.0-3.4
- Rewrite: overall < 3.5 or any dimension < 3.0

### Output Schema (Agent Report)

- overall_score
- dimension_scores (map)
- strengths (list)
- risks (list)
- rewrite_guidance (list)
- suggested_ad_hooks (list)

## Integration Expectations

- Story generation outputs: Story Bible summary + hook plan + twist density.
- Episode/Script generation outputs: hook schedule + cliff plan + ad snippets.
- Timeline/Storyboard: tag hook beats and reference traffic sheet asset IDs.
