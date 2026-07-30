# Story → Novel → Episode → Script

> Narrative-memory rules live in
> `docs/design/narrative-memory-and-dramatic-state.md`. The implementation plan
> for structured outlines and platform length profiles lives in
> `docs/exec-plans/active/structured-outline-platform-lengths.md`.

## Decision

New narrative series use:

`StorySeed → Novel Revision → approved adaptation plan → Episode → Script → Timeline`

The sources of truth are deliberately split:

- `StorySeed` owns story content and the confirmed chapter structure.
- A Novel Revision owns platform length requirements, generation model, task
  state, chapter bodies, extraction state, and approval state.
- The approved canonical Novel Revision is the narrative SSOT.
- Timeline remains the production-time, clip-order, asset-lineage, render, and
  delivery SSOT.

Platform names, character-count ranges, provider models, task state, and draft
chapter bodies must never enter Story Canon.

## Compatibility boundary

- New narrative Stories continue to use `workflow_mode=novel_adaptation_v1`.
- `story_seed_v1` remains readable and editable. It is upgraded explicitly; no
  historical Story is silently rewritten.
- Historical/direct Stories, production-canvas compatibility paths, and
  single-video projects remain `direct`.
- Legacy `style=zhihu`, download, task, and `/novel/exports` contracts retain
  their existing limits and semantics.
- Old prose clients may send `target_words` and `chapter_count`; the server
  accepts but ignores them and returns a compatibility warning.
- Direct Episode generation for a novel-adaptation Story returns HTTP 409 with
  code `NOVEL_APPROVAL_REQUIRED`.

## Canon-gated long-form quality contract

New prose revisions first implement this contract as
`story_novel_generation_plan.v2`. The structured-outline/length-profile work
may later materialize a higher plan version, but it must preserve the Canon,
chapter-contract, state-chain, invalidation, and approval guarantees in this
section. Historical plans remain readable and are not silently migrated.

Planning has two bounded model phases:

1. compile one typed Canon from the frozen StorySeed, characters, relationships,
   setting, and world constraints;
2. generate the finite, contiguous chapter contracts from the outline plus that
   Canon.

Canon owns stable IDs and one `canon_hash` over:

- the unique timeline and absolute/relative dates;
- characters, locations, key objects, and initial state;
- identity, relationship, knowledge, injury, ability, and permission
  boundaries;
- non-negotiable world rules;
- one-shot milestones such as reveal, choice, activation, merge, or death;
- character-arc start, turn, and end checkpoints.

The strict Canon contract declares `gate_version=1`, mirrored as
`canon_gate_version=1` on the generation plan. Every non-repeatable milestone
with a planned chapter must declare one or more typed `outcomes`:
`subject_id`, dotted `field`, `operator` (`eq` or `contains`), and a real JSON
`value`. Outcome subjects must resolve to Canon entities; string-encoded
`"null"`, `"[]"`, and `"{}"` are invalid because they cannot be compared as
typed state.

Each chapter contract retains its title, plot goal, key events, character focus,
open threads, end state, and 3000–5000 non-whitespace-character target, and adds
`preconditions`, `required_event_ids`, `state_transitions`,
`knowledge_grants`, `location_transitions`, `milestones_consumed`,
`forbidden_event_ids`, `payoffs_due`, and `canon_refs`.

Deterministic planning validation requires stable, unique, resolvable IDs;
contiguous chapter positions; one-time milestone consumption; connected state
transitions; no knowledge before its grant; planned payoff closure; and ordered
character-arc checkpoints. Knowledge changes exist only in
`knowledge_grants`, with a character, fact, and source event; a
`state_transitions` entry whose field is `knowledge` is invalid. Future
milestone outcomes are checked at three boundaries: chapter zero rejects an
initial state that already contains a later outcome; deterministic plan replay
applies each chapter contract in order and rejects a consumed outcome that did
not land or a future outcome that landed early; actual-body validation performs
the same checks after applying the independently extracted typed delta. Canon
and chapter-contract output each receive at most one format repair. A second
failure stops before prose and never trims the plan. Long-form Canon, plan,
chapter, and global-review calls may use the provider-supported budget up to
16000 output tokens; this path must not restore a fixed 8192-token ceiling.

The fixed 3000–5000 range is the current v2 quality contract. A future
Revision-owned length profile may replace that range only by producing an
equally frozen, hash-addressed chapter contract; it cannot weaken Canon/state
validation.

## StorySeed v2

`story_seed_v2` extends the existing seed with both the original text and an
editable structured outline:

```json
{
  "schema": "story_seed_v2",
  "title": "潮汐档案馆",
  "premise": "故事前提",
  "outline_text": "原始文字大纲",
  "structured_outline": {
    "status": "draft",
    "version": 1,
    "chapters": [
      {
        "position": 1,
        "title": "零点来电",
        "goal": "主角收到亡女的异常回声",
        "key_events": ["收到零点求救信号"],
        "character_focus": ["老拐"],
        "open_threads": ["回声是否真实"],
        "end_state": "老拐决定潜入档案馆"
      }
    ]
  },
  "protagonists": [
    {
      "virtual_ip_business_id": "vip_x",
      "initial_state": "故事开始时的处境与目标"
    }
  ],
  "world_constraints": [],
  "central_conflict": "核心冲突",
  "ending_direction": "结局方向",
  "content_constraints": []
}
```

Structured-outline invariants:

- positions start at 1 and are contiguous;
- at least one chapter exists, with no application-level maximum;
- title, goal, at least one key event, and end state are required;
- chapter-list length is the sole authoritative novel chapter count;
- the ending chapter covers `ending_direction` when it is present;
- prose generation cannot add, merge, delete, or reorder chapters;
- cross-chapter setup/payoff is represented by explicit open threads.

For a v1 seed or plain-text outline, an explicit asynchronous planning action
may produce a v2 draft. Invalid, truncated, incomplete, or non-contiguous output
gets at most one repair and then fails without silent trimming. The user edits
and confirms the complete outline before any prose task can start.

The StorySeed service boundary accepts either an already validated model or an
endpoint `model_dump(by_alias=True)` dictionary, but always runs
`StorySeedModel.model_validate` before version, task, confirmation, and
invalidation checks. The asynchronous structuring task uses the Story's
configured model when present; otherwise it resolves the stable planning
default `deepseek:<DEEPSEEK_DEFAULT_MODEL>` rather than inheriting an unrelated
worker default.

The outline editor supports add, delete, reorder, split, and merge while the
outline is a draft. Confirmation creates a new immutable StorySeed version for
downstream generation; later edits create another version and invalidate
dependent draft plans rather than rewriting history.

## Novel Revision length specification

Length belongs to a Novel Revision, not StorySeed:

```json
{
  "length_profile": {
    "profile_id": "standard_serial",
    "profile_name": "标准连载",
    "count_mode": "non_whitespace_chars",
    "default_min_chars": 3000,
    "default_target_chars": 4000,
    "default_max_chars": 5000
  },
  "chapter_length_overrides": {
    "2": {
      "min_chars": 3800,
      "target_chars": 4600,
      "max_chars": 5200
    }
  }
}
```

Profiles are configurable and product-neutral. Initial defaults are:

| Profile         |    Minimum |     Target |    Maximum |
| --------------- | ---------: | ---------: | ---------: |
| Commercial web  |       2000 |       2500 |       3000 |
| Short serial    |       1500 |       2200 |       3000 |
| Standard serial |       3000 |       4000 |       5000 |
| Long chapter    |       4500 |       6000 |       8000 |
| Custom          | user value | user value | user value |

Every resolved chapter range satisfies:

```text
0 < min_chars <= target_chars <= max_chars
```

All values are finite integers. There is no application-level chapter-count or
whole-novel character cap. Character counts remove spaces, line breaks, tabs,
and other whitespace but retain punctuation, digits, and non-Chinese text.
Model-reported counts and token counts are never authoritative.

The planned totals are derived only from resolved chapter ranges:

```text
planned_min_chars    = sum(chapter.min_chars)
planned_target_chars = sum(chapter.target_chars)
planned_max_chars    = sum(chapter.max_chars)
```

There is no independent whole-book target input.

## generation_plan v4

Before generation, the server materializes a reproducible snapshot in the
existing `generation_plan` JSON:

```json
{
  "version": 4,
  "status": "ready",
  "story_seed_version": 3,
  "outline_hash": "sha256",
  "length_profile": {},
  "chapter_count": 48,
  "planned_min_chars": 144000,
  "planned_target_chars": 201600,
  "planned_max_chars": 240000,
  "chapters": []
}
```

Each chapter copies the confirmed outline fields, resolved length range and
source (`profile_default` or `chapter_override`). Its checkpoint later records
actual character count, body/context/source hashes, extraction status, event
IDs, and memory IDs. The plan version and hashes are approval evidence.

`generation_plan.status=ready` means complete and editable. Dispatch atomically
freezes the StorySeed version, plan version, resolved ranges, and model. While a
task is running, these fields cannot be changed. The user must cancel first and
create a new plan version.

## Chapter-planning quality pipeline v3

Research basis (checked 2026-07-27):

- [DOME (NAACL 2025)](https://aclanthology.org/2025.naacl-long.63/) motivates
  dynamic hierarchical outline/write coupling plus temporal memory instead of a
  single rigid outline dump.
- [FactTrack (NAACL 2025)](https://aclanthology.org/2025.naacl-long.144/)
  motivates directional atomic effects, time-aware validity, contradiction
  detection, and ordered state update.
- [E²RAG (EACL 2026)](https://aclanthology.org/2026.eacl-long.90/) motivates
  keeping entity state and event causality as distinct retrieval/ranking signals.
- [ConStory-Bench (Findings ACL 2026)](https://aclanthology.org/2026.findings-acl.410.pdf)
  motivates evidence-grounded factual/temporal consistency categories rather
  than relying on a single opaque LLM score.

These papers inform the decomposition and evaluation boundaries; they do not
replace the product's deterministic Canon, hash, state, and approval gates.

New revisions created with an explicit three-stage model policy use
`story_novel_generation_plan.v3` and `story_novel_continuity.v4`. Existing v2
revisions remain readable and resumable under their original contract; they are
not migrated and cannot enter the v3-only Episode/Script downstream boundary.

StorySeed structuring accepts a finite positive `chapter_count` and a planning
model. The model must return exactly the contiguous positions
`1..chapter_count`; an omitted count is compatible only when the textual outline
contains an explicit finite range. The confirmed structured-outline list remains
the sole chapter-count authority. There is no separate novel-total input or
application-level chapter ceiling. A roughly two-million-character serial is
therefore expressed, for example, as about 800 chapters under the default
2,000–3,000 non-whitespace-character profile, not as a mutable `target_words`
field.

Outlines longer than 32 chapters use `planning_structure_version=1`: one bounded
progression call freezes contiguous 32-chapter arc ranges, followed by one
bounded chapter-detail call per arc. Every call has one format repair and an
output ceiling no higher than 16K tokens; an invalid or incomplete arc fails
closed instead of truncating or synthesizing empty chapters. Each arc may carry
four optional prose directions—cognition, capability, resources, and
activity/time scale. These are whole-arc editorial curves, may be null, and are
never per-chapter numeric KPIs. Buildup, failure, and costly regression remain
valid chapter shapes.

A Revision freezes:

```json
{
  "model_policy": {
    "planning_model": "provider:model",
    "prose_model": "provider:model",
    "audit_model": "provider:model"
  }
}
```

`revision.model` mirrors `prose_model`. Legacy clients that send only `model`
continue to use that model for every stage. New clients always send the policy;
after task dispatch or the first chapter checkpoint, changing the policy requires
a new Revision. Planning defaults to reasoning enabled, while prose and audit
default to reasoning disabled. Per-chapter brief, prose, audit, and local repair
budgets are respectively 12000, dynamically 12000–16000, 6000, and 4000 output
tokens; no v3 stage restores an 8192 cap.

All V3 model-facing instructions use the repository PromptManager rather than
Python f-string prompt bodies. Dedicated, versioned templates cover the system
prompt, structured-outline conversion and both repair paths, Canon
compilation/repair, thread scheduling/repair, bounded chapter-plan batches,
targeted and full-plan repair, semantic audit, chapter brief, prose blocks and
truncation continuation, proof audit, local block repair, bounded JSON repair,
and continuity window/global review. The generation plan freezes
`story_novel_prompt_policy.v9` with each template name, metadata version, and
source hash. Each invocation persists the exact rendered user-prompt hash plus
the versioned system-prompt fingerprint, including provider calls rejected for
`finish_reason=length`; continuity and approval compare that evidence with the
real invocation row. A template source change therefore invalidates V3 plan or
checkpoint reuse instead of silently changing the generation contract. Stored
v1-v8 policies remain structurally verifiable as legacy snapshots; new plans
always freeze v9. Legacy Zhihu templates and behavior remain separate.

Novel runtime instructions are genre-neutral. StorySeed, Canon, and the current
chapter contract are the only sources of subject matter, relationship arcs, and
special mechanisms. The server does not inject agriculture, transmigration,
gendered lead roles, fixed payoff prose, or domain-specific process examples;
an automated scan covers every `story_novel_*.txt` template and the Python
modules that assemble novel prompts.

Global chapter-contract planning is split between model-authored narrative
intent and a deterministic server state compiler. The model selects the current
event effects and desired destinations; the service replays the Canon state
machine and owns every `from_value`, movement origin, and executable
precondition. Provider JSON is checked as one structural error vector before
semantic validation, and a parseable invalid batch receives field-level patches
instead of reprinting all chapters. The semantic audit reports both missing and
unsupported effects, so scene description or model inference cannot silently
become a durable state change. Batches remain at most eight chapters but shrink
to three or more chapters as event, character, thread, timeline, and milestone
complexity increases; each batch receives only the next boundary anchor.

The audit also freezes one typed execution contract for every required event:
action phase, time scope, actors, effort class, timeline bindings, and knowledge
bindings. Blocking issues are limited to direct contradictions among the frozen
event, timeline, chapter end state, knowledge effects, and explicit world rules.
Unspecified scale stays unspecified; the auditor must not invent dimensions or
labor assumptions. General realism, slightly accelerated labor, dramatic
coincidence, pacing, prose style, and other commercial-web-fiction choices are
editorial advisories, never deterministic blockers. A prose passage becomes a
hard world-rule failure only when its own concrete claim directly violates an
explicit rule or another frozen contract. The service derives severity from the
typed issue code rather than trusting the model's severity field: generic labor
feasibility is advisory, while direct timeline/state/knowledge/end-state/world-
rule conflict codes remain blocking.

Canon locations may declare static `attributes.location_scope` as `persistent`
or `scene`. A scene location must have a valid acyclic
`attributes.parent_location_id`; it is available for prose staging but compiles
to its persistent ancestor for state replay. Initial state and milestone
location outcomes cannot target a scene location. This prevents visits to a
station room or warehouse from becoming fictitious cross-chapter travel while
preserving real vehicle, route, and destination transitions.

Each chapter executes four durable phases:

1. **Chapter planning.** The planning model receives only the current frozen
   contract, visible Canon and `state_before`, valid earlier Revision events and
   memories, unresolved threads, recent summaries, and the previous body tail.
   It never receives later chapter titles, dates, actions, end states, or payoff
   prose. It returns `story_novel_chapter_brief.v1`; new commercial plans freeze
   brief policy v4 with 4–6 larger, non-overlapping beats, while historical
   policy v3 keeps 6–12 beats for hash compatibility. Each brief records
   character budgets, allowed entities/events/effects, motivations,
   emotional continuity, causal bridge, and current setup/payoff IDs.
   The active progression arc is included only as a multi-chapter soft direction;
   future arcs, future entries, and future payoff text remain absent.
   The brief preserves the execution contract and shapes commercial-web-fiction
   rhythm as pressure/conflict -> protagonist choice -> action -> visible gain
   or cost -> chapter-end hook; it does not turn the chapter into an engineering
   report merely to satisfy plausibility.
   Valid earlier Event/Memory rows are deterministically ranked by current
   characters, contract terms, source position, and knowledge boundary before
   the context budget is applied; low-relevance history is discarded first.
   The non-truncatable world projection is bounded to current-chapter references
   plus their direct current-state dependencies. Merely appearing in an old
   chapter never makes an entity occupy every later hard context.
2. **Block prose.** The prose model receives the validated brief, current visible
   Canon projection, writing style, and length contract. The projection includes
   only current-chapter event text/execution contracts plus currently visible
   character introductions, motivations, state, and relationships; references
   to future characters and later relationship progress are filtered out. It receives zero raw
   Narrative Event/Memory rows, zero future contracts, zero evidence rules, and
   no expected/state delta. It returns only contiguous `B01..Bnn` body blocks.
3. **Proof audit.** The server compiles the only authoritative `expected_delta`
   from the chapter contract plus `state_before`, splits the assembled body into
   stable Unicode sentence IDs/offsets, and asks the audit model only to bind
   contract IDs to sentence IDs and report unexpected, future, or world-rule
   hits. The model cannot author state IDs, from/to values, owners, locations, or
   milestones. Required-event, material state, location, and knowledge contracts
   need semantic sentence proof. Milestone consumption and thread open/payoff are
   deterministic effects of a proved required event and do not demand a second
   restatement. Timeline bindings remain audit context rather than proof
   contracts: natural relative time or omitted repeated dates are valid whenever
   the event sequence, travel duration, and day/night continuity are reasonable.
   Quotes and spans are always reconstructed from the stored body.
4. **Narrative materialization.** After every proof and deterministic gate passes,
   required events become World Event candidates and knowledge grants become
   Character Memory candidates, enriched by the brief's motivation/emotional
   intent and current character-arc checkpoint. No additional Narrative
   extraction model is called. Only source-hash-valid, earlier ready candidates
   may enter the next chapter's planning context.

Major people, locations, organizations, objects, and concepts may be registered
in Canon before generation while remaining hidden until the first chapter whose
frozen outline names them. A chapter package may also introduce a previously
unplanned persistent entity when the current event actually needs it. The
service assigns a stable Revision-local ID, binds the introduction to the
current required event, records initial state and first appearance, and rejects
any earlier ID or name reference. Once its chapter passes proof/state gates, the
entity joins `revision_local_entities` and may be used by later chapter planning;
one-scene extras and ordinary props do not become permanent world state. This
lets a serial expand from village to county, city, country, continent, planet,
or other genre-appropriate scopes without requiring any particular scale or a
forced map change.

The global plan compiles a hash-addressed `future_guard_index` containing only
stable event IDs, first-allowed positions, protected entities/dates/conclusions,
milestone outcomes, and semantic match terms. The prose model never sees it.
Claim-card selection is only a candidate-recall step, never a deterministic prose
failure. The audit model also receives the current values of chapter-relevant
subjects and compact future state boundaries for those subjects, without future
titles, goals, or end states. This lets it reject a paraphrased early permission,
ownership, location, knowledge, or payoff outcome while allowing harmless name,
date, world-detail, and hypothetical mentions. Literal date/entity/world-rule
matches do not fail a v3 chapter until the semantic audit identifies a real
contract contradiction and binds it to current-body sentence IDs.
The brief and context checkpoint records input Event/Memory IDs and source
hashes, state/chapter-contract/Canon hashes, excluded future count, and complete
record-level truncation reasons. `hard_constraints` alone are non-truncatable;
optional evidence, summaries, ledger rows, and tail text are retained only as
complete bounded records.

The service assembles block offsets and hashes before persistence. Body plus
ledger checkpoint commit atomically. A content failure may replace only the
failed blocks once and then re-audits the whole assembled body; untouched block
bytes remain identical. If provider transport ends with `finish_reason=length`,
the service recovers only complete leading block objects and requests the exact
missing block IDs once; no recovered byte is regenerated. With no complete
block it allows one whole-prose retry. A format failure gets at most one recovery
call. Invocation audit keeps provider transport status separate from
`product_status=rejected` and the precise product error. An
evidence-only failure preserves an `audit` checkpoint and a later Resume calls
only the auditor; it never rewrites prose. `ready` and candidate-only recovery
paths are model-free when all hashes match.

`story_novel_continuity.v4` stores the brief/input/model/hash evidence, block
manifest, expected delta, sentence-index hash, proof spans, future/world audit,
all stage invocation IDs/tokens/finish reasons/latency, Narrative candidate IDs,
and the Canon/context/body/source/state hash chain. Six-chapter continuity
reviews additionally report reader-retention warnings for conflict, payoff
cadence, relationship movement, repetition, and chapter hooks. These are
editorial signals, not deterministic approval blockers. Global review also
scores optional long-range cognition, capability, resource, and activity/time
progression plus reader appeal; a curve that does not fit the genre is not
penalized, and no chapter is required to announce an upgrade. V3 approval recomputes these
values, requires every stage invocation and all eight six-chapter plus one global
review invocation for a 48-chapter book, and rejects any tampering. The approved
canonical v3 Revision is the only novel source accepted by the adaptation plan,
Episode, and Script lineage gates.

## Generation, repair, and resume

One asynchronous task generates chapters sequentially:

1. validate the preceding extraction, Canon hash, and state hash;
2. build a roughly 32K-character context whose non-truncatable
   `hard_constraints` contain the chapter contract, relevant Canon, current
   character/object state, knowledge boundaries, consumed milestones,
   forbidden repeated events, and due payoffs;
3. generate the next chapter and count non-whitespace characters locally;
4. independently extract a typed state delta from the actual body instead of
   trusting a prose response's self-reported plot delta;
5. validate length, preconditions, location movement, knowledge sources,
   permissions, object ownership, world rules, one-shot milestones, and thread
   state;
6. combine all body/state failures into one bounded prose repair, then extract
   and validate again;
7. after the gate passes, checkpoint the body and state hashes, run Narrative
   Event/Character Memory extraction, and atomically apply the state delta.

These steps form three explicit future-outcome gates. Canon normalization
validates chapter-zero state before planning; the chapter-plan linter replays
all contracts from that state; and the actual-body gate validates the applied
typed delta before any memory extraction or state commit. A pass at one layer
does not substitute for either of the others.

The prose call has a strict future-information boundary. Planning may read the
complete frozen `StorySeed v2.structured_outline`, but prose for chapter N
receives only chapter N's frozen contract. The context builder removes
`outline`, `outline_text`, `structured_outline`, `ending_direction`, later
chapter contracts, later character-arc checkpoints, and future arc end states.
It may still include immutable story/world constraints, valid evidence from
chapters before N, current state, recent summaries, and the previous body tail.
Prompt evidence records `outline_scope=current_chapter_contract_only`, the
current contract hash, and the count of excluded future chapters.

The independent state-extraction call is not a prose call. It may receive a
compact audit-only catalog of later event IDs and semantic targets so it can
mark `premature_future_event_ids`. Deterministic validation rejects those IDs,
unplanned events/transitions/knowledge/movement/thread changes, and premature
milestones before any state is applied. The audit catalog is never added to a
prose or repair context; a failed chapter remains outside `current_state`.

The output-token budget is derived from the resolved chapter range, the
provider's supported limit, and a documented character/token estimate, or is
omitted for a provider that safely controls long output. No prose path injects
a fixed 8192-token ceiling.

The repair prompt includes the allowed range, actual count, chapter contract,
all deterministic gate issues, summary/plot delta, and short body boundary
excerpts. It does not echo an oversized body in full. A second body/state gate
failure saves the attempted body and evidence as
`gate_failed/review_required`, stops before the next chapter, and does not
apply its state or make it revision-local Canon.

`continuity_ledger` schema `story_novel_continuity.v3` records per chapter:
`canon_hash`, `context_hash`, `body_hash`, `source_hash`,
`state_before_hash`, `state_after_hash`, the typed state delta, state-validation
issues, body/extraction repair counts, and Narrative Event/Memory IDs and
hashes. Resume skips only `ready` chapters whose Canon, context, body, source,
and state-chain evidence all matches. If only Narrative extraction is missing,
it runs extraction without rewriting prose; `gate_failed` or `stale` resumes
generation from the earliest affected position through the end.

Planning checkpoints follow the same fail-closed rule. A failed plan, an older
or missing gate version, an invalid Canon, or a stale/mismatched Canon hash is
never reused. When a frozen plan failed specifically in chapter-contract
planning, its `gate_version=1` Canon may be reused for the single planning
repair only if both stored Canon hashes match and normalization succeeds; this
does not make the failed chapter plan reusable. A fully ready frozen plan is
reused only when its Canon, plan hash, and deterministic replay all validate.

If `hard_constraints` alone exceed the context budget, generation fails before
calling the prose model. Canon is never truncated; prompt evidence records the
hard-constraint hash, referenced IDs, omitted optional context, and reasons.

## Editing and invalidation

- Changing only a chapter length range never calls a model.
- An existing body inside the new range is retained and marked
  `target_changed`.
- An existing body outside the new range is retained and marked
  `length_mismatch`; its facts and memories remain valid because the source body
  did not change.
- Changing chapter goal, key events, character focus, end state, order, or
  membership marks the affected body/extraction and successor context
  `stale/review_required`.
- Changing body text invalidates candidates tied to the old source hash and
  marks successor context, continuity, and adaptation state for review.
- `PATCH /stories/novel/revisions/{revision}/canon` requires
  `expected_plan_version`, `expected_canon_hash`, and the complete typed Canon.
  Saving is an explicit human action and never calls a model.
- A Canon save recomputes its hash, uses chapter `canon_refs` to find the
  earliest affected position, and marks that chapter through the end stale.
  The operator must explicitly resume sequential regeneration.
- Approved revisions remain immutable; editing begins by cloning a new draft.
- All saves use optimistic version/timestamp checks and return HTTP 409 on
  conflict. Local saves never invoke a model.

## Continuity and editorial review

`story_novel_continuity_review.v3` keeps the adjacent full-text windows and one
global synthesis. The global pass receives the complete Canon, state-hash chain,
typed deltas, facts, character memories, open threads, plan, and every current
chapter ID/hash. Its structured output contains conflicts, affected Canon IDs,
a suggested unique value, related chapters, the earliest invalid position, and
Canon-targeted `repair_groups`.

The product computes the seven deterministic hard metrics listed below from
stored evidence. `chapter_repair_rate` is observational only. The model reports
separate scores and reasons for structure, character, prose, world-building,
emotion, originality, and adaptation value; the product does not fabricate a
weighted total or use those editorial scores as a deterministic approval gate.

## Revision-local memory and approval

Generated facts, Narrative Events, and Character Memories remain candidates
scoped to the current Story, Revision, source chapter/hash, and narrative
position. A Revision may read only valid earlier candidates from itself; it
cannot read candidates from another Revision or a future chapter.

Approval requires:

- chapter count and order match the frozen outline;
- every body is within its resolved range;
- Canon, body, context, source, outline, plan, and state-chain hashes match;
- Narrative extraction and typed state validation are ready for every chapter;
- `story_novel_continuity_review.v3` covers every current chapter/hash and the
  current Canon hash;
- `canon_violation_count`, `state_reversion_count`,
  `duplicate_milestone_count`, `illegal_knowledge_count`,
  `unexplained_location_transition_count`,
  `hard_constraint_truncation_count`, and
  `overdue_open_thread_count` are all zero;
- no unaccepted model blocking issue exists. A reviewer reason may acknowledge
  a model judgment for audit, but can never bypass length, Canon, hash-chain,
  or deterministic-state failures;
- the approved plan version is still current.

Approval promotes only valid candidates from that Revision to Story Canon,
makes the Revision canonical, and supersedes the previous canonical Revision.
Old Revision candidates and existing Episode source snapshots never move.

## API surface

All identifiers are business IDs. Routes below are relative to `/api/v1`.

- `GET /novel/length-profiles`
- `PUT /stories/business/{story}/story-seed`
- `POST /stories/business/{story}/novel/revisions`
- `GET /stories/business/{story}/novel/revisions`
- `GET /stories/novel/revisions/{revision}`
- `PATCH /stories/novel/revisions/{revision}/canon`
- `PATCH /stories/novel/revisions/{revision}` for draft length/model settings
- `POST /stories/novel/revisions/{revision}/generate-async`
- `POST /stories/novel/revisions/{revision}/resume-async`
- `PATCH /stories/novel/revisions/{revision}/chapters/{chapter}`
- `POST /stories/novel/revisions/{revision}/chapters/reorder`
- `POST /stories/novel/revisions/{revision}/chapters/{chapter}/regenerate-async`
- `POST /stories/novel/revisions/{revision}/clone`
- `POST /stories/novel/revisions/{revision}/continuity-check-async`
- `POST /stories/novel/revisions/{revision}/continuity-issues/{issue}/accept`
  records reviewer acknowledgement/reason for audit only and does not unblock
  approval
- `POST /stories/novel/revisions/{revision}/approve`
- existing adaptation-plan generation, edit, approval, and apply endpoints

`POST /stories/business/{story}/novel/generate-async` remains a compatibility
wrapper. For prose it resolves or creates a draft Revision but never treats
legacy whole-book length or chapter-count fields as authoritative.

## Operator workflow

The Story page presents StorySeed, Novel Revision, adaptation-plan, and Episode
stages. Before generation it exposes:

- a complete structured-outline editor;
- preset/custom default ranges and per-chapter overrides;
- real-time planned min/target/max totals;
- the frozen plan version and any stale/mismatch state.

During generation, plan controls are locked and the UI refreshes chapter body
and extraction progress independently. Legacy Zhihu UI and behavior remain
unchanged.

The long-form workflow also exposes a typed/JSON Canon editor with optimistic
locking, per-chapter `state validated` progress, deterministic quality metrics,
model quality scores, conflict `repair_groups`, the earliest stale chapter, and
an explicit “resume from this chapter through the end” action. Applying a
repair suggestion only prepares a Canon draft; the user must review and save
it. Structural, character, prose, world-building, emotional, originality, and
adaptation-value scores remain editorial evidence rather than deterministic
approval gates.

## Explicit non-goals

- New databases, vector stores, or a separate platform-profile persistence
  service.
- Automatic migration or paid regeneration of historical content.
- Rich text, comments, real-time collaboration, or chapter branching.
- Silent truncation, automatic downstream rewriting, or automatic approval.
- Changes to audio, storyboard, video, render, or export after Script.
