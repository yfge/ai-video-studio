# Narrative World Character-Agent Rehearsal

**Status:** Active design / implementation not started

**Goal:** Extend the current Story Novel v3 chapter pipeline with an optional,
future-isolated character-agent rehearsal stage. Characters act from isolated
perspective packets, a central resolver produces one authoritative scene event
log, and the existing narrator/audit/memory pipeline turns only accepted events
into prose and durable Narrative state.

**Design source:**

- `docs/design/narrative-world-character-agents.md`

**Related current contracts:**

- `docs/design/story-novel-episode-script.md`
- `docs/design/narrative-memory-and-dramatic-state.md`
- `docs/exec-plans/active/story-novel-planning-quality-v3.md`

**Compatibility boundary:** Current `story_novel_generation_plan.v3` and
`story_novel_continuity.v4` remain readable and unchanged. Character rehearsal
is opt-in for a new Revision contract; no historical Revision is migrated or
silently resumed with new prompts.

**Persistence boundary:** Reuse generation-plan/continuity JSON, chapter rows,
Narrative Events, Character Memories, and `llm_invocations`. The first delivery
adds no database table, vector store, third-party dependency, provider bypass,
or long-lived model session.

## Delivery slices

### 0. Contract freeze and baseline

- [x] Record the architecture decision, invariants, data contracts, quality
      boundaries, and rollout gates in the design source.
- [ ] Freeze `story_novel_generation_plan.v4`, `story_novel_continuity.v5`,
      `story_novel_character_perspective.v1`, `story_novel_actor_proposal.v1`,
      and `story_novel_scene_resolution.v1` schemas.
- [ ] Add `interaction_policy.mode=brief_only|rehearsed_scene`, actor/resolver
      models, scene/actor limits, and explicit `fail_closed|brief_only`
      fallback to Revision create/update contracts.
- [ ] Define exact PromptManager template names and freeze them in a new prompt
      policy version; existing v3 prompt fingerprints remain valid legacy
      snapshots.
- [ ] Capture a current `brief_only` baseline from one fixed 12-chapter
      StorySeed: chapter quality, hard violations, calls, tokens, latency,
      retries, and reader-preference inputs.
- [ ] Add repository contracts preventing rehearsal code from expanding the
      task processor, chapter service, Narrative repositories, or existing
      v3 prompt modules beyond their ownership/size limits.

### 1. Scene contracts and participant selection

- [ ] Compile each validated chapter brief into 1–3 current-chapter-only scene
      contracts without exposing later titles, events, dates, end states,
      milestones, or payoff prose.
- [ ] Bind every scene to current beat/event/effect IDs, persistent parent
      location, relative time scope, POV, length budget, and allowed/forbidden
      durable effects.
- [ ] Select only characters with an actual decision, conflict, private
      information, relationship movement, or event responsibility; ordinary
      NPCs remain scene details.
- [ ] Enforce 2–4 actor agents per scene and reject unknown/future character
      IDs before a model call.
- [ ] Make scene contracts deterministic and hash-addressed from brief,
      chapter contract, Canon/state, interaction policy, and prompt policy.
- [ ] Checkpoint scene contracts before actor calls and reuse them only when
      all source hashes match.

### 2. Query-conditioned character perspective

- [ ] Build one isolated Perspective Packet per selected character from that
      character's identity, current state, relationships, desires, beliefs,
      effective private memories, observed public events, physical context,
      and current scene objective.
- [ ] Retrieve records by scene questions—desire, relationship, knowledge,
      promise/debt, object/location, and unresolved conflict—instead of loading
      a chronological prefix.
- [ ] Require every record to belong to the same Story/Revision, an earlier
      `ready` source chapter, the current Canon branch, and a source hash still
      present in the continuity ledger.
- [ ] Keep other characters' private memories, audience-only disclosures,
      future claim cards, future state boundaries, and later chapter contracts
      out of actor packets.
- [ ] Persist selected Event/Memory IDs, source hashes, ranking reasons,
      truncation reasons, packet hash, state hash, and scene-contract hash.
- [ ] Fail before provider invocation if the non-truncatable identity,
      knowledge-boundary, or current-state packet exceeds its budget.
- [ ] Add diagnostic queries proving Anchoring, Selecting, Bounding, and
      Enacting evidence independently for every selected actor.

### 3. Actor proposals

- [ ] Add a versioned actor prompt that returns only immediate goal,
      interpretation, intended action, dialogue intent, concealed intent,
      expected reaction, acceptable/unacceptable outcomes, risk, and possible
      emotional shift.
- [ ] Reject proposal fields that author state deltas, Canon IDs, successful
      outcomes, final prose, or facts absent from the Perspective Packet.
- [ ] Support one batched proposal call with explicitly isolated per-character
      packets; add a policy switch for separate calls when a secret-bearing
      scene requires physical prompt isolation.
- [ ] Bind each proposal to character, scene, Perspective Packet, model,
      prompt, invocation, response, and finish-reason hashes.
- [ ] Allow at most one format repair per proposal call and reject truncated or
      incomplete actor sets without synthesizing missing characters.
- [ ] Checkpoint valid proposals so Resume does not repeat paid actor calls.

### 4. Central world resolution

- [ ] Add deterministic prechecks for presence, knowledge, relationship,
      permission, ownership, object availability, travel/location, world rule,
      and future-state boundaries.
- [ ] Record each rejected proposal with a typed reason; rejected proposal
      content cannot enter the narrator prompt or Narrative Memory.
- [ ] Add a constrained resolver prompt that can order actions, choose failed
      attempts, misunderstandings, concessions, reactions, and surface
      consequences only among legal paths.
- [ ] Keep the chapter contract authoritative: the resolver decides how a
      required event happens, not whether the global outline or durable
      `expected_delta` changes.
- [ ] Require ordered scene events to bind current actor/event/effect IDs and
      reject unknown entities, unowned state changes, or future outcomes.
- [ ] Build a deterministic state-after preview for comparison only; do not
      apply it to `current_state` before prose proof passes.
- [ ] Checkpoint one resolution/event-log hash per scene and make identical
      input hashes idempotent.
- [ ] Mark an impossible interaction `rehearsal_failed/review_required` rather
      than inventing a compliant event.

### 5. Narrator integration

- [ ] Insert rehearsal after a validated chapter brief and before prose block
      generation only when the frozen mode is `rehearsed_scene`.
- [ ] Give the prose model scene contracts, accepted event logs, current
      visible characters/relations, POV permissions, writing style, and length
      contract; keep raw actor memories, rejected proposals, future guard,
      evidence rules, and expected delta absent.
- [ ] Instruct the narrator to compress, merge, and dramatize accepted events,
      not transcribe a turn-by-turn simulation log.
- [ ] Allow only nonpersistent action, dialogue, sensory, emotional, and
      staging details beyond the resolved event log.
- [ ] Extend prose prompt evidence with zero-count assertions for future
      contracts, other-character private memory, rejected proposals, and raw
      state effects.
- [ ] Preserve existing block IDs, length control, truncation continuation,
      local repair, untouched-byte, and one-whole-retry contracts.
- [ ] Keep `brief_only` prompt bytes and behavior unchanged for legacy/current
      v3 policies.

### 6. Audit, memory, and checkpoint

- [ ] Reuse server-owned `expected_delta`, stable sentence IDs, future/world
      semantic audit, and deterministic state application.
- [ ] Add actor-consistency checks: every durable character action must be
      explainable from that character's packet/proposal or from a new event
      visibly learned during the scene.
- [ ] Add event-log conformance: accepted outcomes may appear in prose;
      rejected or unresolved proposals cannot be narrated as facts.
- [ ] Require any rehearsal-related blocking issue to cite actor/packet/
      proposal/resolution IDs plus current-body sentence IDs.
- [ ] Keep milestones and thread lifecycle derived from proved required events;
      do not reintroduce fixed prose strings or separate literal-date proofs.
- [ ] Materialize World Event/Character Memory candidates only from final
      verified prose spans, never directly from Proposal or Resolution text.
- [ ] Commit chapter body, rehearsal manifest, audit, state and candidate
      ledger atomically; a failed body cannot update the narrative world.
- [ ] Extend approval to recompute rehearsal hashes, invocation coverage,
      knowledge isolation, event-log conformance, and state/source chains.

### 7. Resume, invalidation, and cost controls

- [ ] Reuse Perspective Packets, Proposals and Resolutions only when every
      scene/brief/state/memory/source/model/prompt hash matches.
- [ ] Propagate stale from the earliest affected scene when a prior chapter,
      relationship, knowledge grant, memory source, Canon item, participant,
      or interaction policy changes.
- [ ] Keep evidence-only and candidate-only Resume actor-, resolver-, and
      prose-model-free.
- [ ] Keep prose repair actor/resolver-free unless diagnostics prove the
      persisted Resolution itself violates the current contract.
- [ ] Freeze one bounded normal call budget: chapter package, batched actors,
      resolver, prose, and audit; each format stage gets at most one repair.
- [ ] Record per-stage calls, tokens, latency, provider request ID, finish
      reason, output hash, retry reason, and product acceptance status.
- [ ] Show predicted and actual incremental rehearsal cost before making it the
      default for any profile.
- [ ] Never silently switch fallback during a task; `brief_only` fallback is
      legal only when frozen on the Revision and recorded in the ledger.

### 8. API and operator UI

- [ ] Extend existing Revision create/update/response types with interaction
      policy while keeping legacy payloads compatible.
- [ ] Freeze interaction mode and actor/resolver models at task dispatch; after
      a rehearsal checkpoint, changes require a new Revision.
- [ ] Add operator choices “标准章前规划” and “角色场景排演”, including cost,
      latency, privacy and fallback explanations.
- [ ] Display chapter phases `actor_rehearsal` and `world_resolution`, selected
      participants, motives, accepted events, typed rejection reasons, calls,
      tokens, latency, and stale position.
- [ ] Do not expose hidden chain-of-thought; show only model-authored structured
      proposal fields and auditable source references.
- [ ] Keep generate/resume/cancel/regenerate/continuity/approval route names and
      Novel-to-Episode canonical gate compatible.
- [ ] Add user-visible failure states for packet overflow, actor schema,
      illegal proposal, impossible resolution, narrator mismatch, and
      rehearsal budget exhaustion.

### 9. Automated validation

- [ ] Add pure contract tests for all new schemas, hashes, canonical ordering,
      unknown fields, version compatibility, and prompt fingerprints.
- [ ] Prove actor A and actor B receive different private knowledge and neither
      receives later-chapter content.
- [ ] Prove Proposal cannot write state, claim success, invent Canon IDs, or
      use knowledge missing from its packet.
- [ ] Prove Resolver rejects invalid presence/location/ownership/permission/
      knowledge/future actions and emits one ordered result for valid proposals.
- [ ] Prove narrator input excludes raw memory, rejected proposals, future
      contracts, expected delta and evidence instructions.
- [ ] Prove event-log/state/proof mismatches fail closed and produce no
      Narrative candidates or later chapter.
- [ ] Cover checkpoint reuse, actor/resolver call counts, cancellation,
      source drift, stale propagation, evidence-only/candidate-only Resume,
      duplicate worker, and cross-Story/Revision isolation.
- [ ] Cover UI selection, task freeze, progress, failure evidence, Resume, and
      legacy `brief_only` behavior.
- [ ] Run focused backend/frontend suites, all Story Novel units, backend quick
      and full pytest, frontend lint/test/build, docs/contracts, pre-commit,
      production image build, and Chrome-first product flow.

## A/B decision gate

Before a paid 48-chapter run, generate two 12-chapter revisions from the same
frozen StorySeed, Canon, chapter contracts, length policy, prose model and audit
model:

- **A:** `brief_only`;
- **B:** `rehearsed_scene` with identical authorial outcomes.

Both runs must use the real product API, MySQL, task queue, invocation audit and
browser flow. Preserve all prompt manifests, chapter/rehearsal/body hashes,
tokens, latency, failures and retry counts.

Blind review must cover character intentionality, knowledge-boundary accuracy,
dialogue/subtext, relationship continuity, event causality, prose naturalness,
plot progress and reader willingness to continue. Proceed to 48 chapters only
when:

- B has zero additional deterministic consistency violations;
- B has no additional future/knowledge/relationship blocker;
- B is preferred in at least 60% of paired chapter judgments for character
  intentionality and relationship interaction;
- B does not increase `gate_failed` or manual-repair rate over A;
- all incremental calls, tokens, latency and cost are recorded and accepted as
  a product tradeoff;
- no evidence-only or candidate-only recovery rewrites prose or reruns actors.

If the gate fails, retain `brief_only` as the product default and keep the A/B
artifact as evidence; do not weaken Canon/state/future gates to improve B.

## Real 48-chapter acceptance

- [ ] Create a fresh StorySeed and opt-in v4 Revision through the public UI/API;
      do not reuse the existing v3 acceptance manuscript.
- [ ] Generate 48/48 chapters in real MySQL using paid provider calls and
      preserve Story/Seed/Revision/Task/invocation/model/token/finish/hash
      evidence.
- [ ] Include at least 12 meaningful rehearsed scenes covering negotiation,
      cooperation, deception, relationship conflict, delayed disclosure and
      multi-party interests; noninteractive chapters may use `brief_only` only
      when the frozen policy explicitly allows per-scene bypass.
- [ ] After at least two ready chapters, cancel through the public endpoint,
      snapshot chapter, rehearsal, body/source/context/state hashes, then Resume
      once and prove completed bytes/hashes and paid actor calls are unchanged.
- [ ] Require complete 48/48 perspective/proposal/resolution/prose/proof/
      candidate/hash coverage for every rehearsed scene and zero hard metrics.
- [ ] Run continuity review and GPT-5.6 over eight complete six-chapter batches
      plus one global synthesis, including character intentionality, dialogue,
      relationship chemistry and reader engagement.
- [ ] Require no blocking time/location/knowledge/relationship/ability/world/
      causality/future issue, overall score at least 75, and structure,
      character and world scores each at least 7.
- [ ] Approve only after all deterministic, semantic, editorial and invocation
      evidence passes; then verify canonical promotion, old-Revision isolation,
      and Novel-to-Episode/Script acceptance.

## Artifact contract

Store the A/B run under:

`artifacts/runs/story-novel-character-rehearsal-ab-<timestamp>/`

Store the full acceptance run under:

`artifacts/runs/story-novel-character-rehearsal-real-<timestamp>/`

Artifacts include:

- frozen Seed, Canon, chapter/scene contracts, interaction/model/prompt policy;
- per-character Perspective Packet manifests and source hashes;
- Proposals, typed rejection reasons, Resolution and event-log hashes;
- narrator inputs, blocks, sentence/proof manifests, expected delta and
  Narrative candidates;
- task/invocation/provider/token/finish/latency/response-hash evidence;
- cancellation snapshot and Resume comparison;
- A/B blind-review inputs, individual judgments and aggregate decision;
- continuity report, GPT-5.6 batch/global reports and final approval verdict.

Secrets, raw provider credentials and hidden reasoning traces must not enter
artifacts.

## Commit coupling

Each implementation commit must include its matching `agent_chats` ledger and
the task/plan checkbox updates it actually proves. Suggested boundaries:

1. contracts and prompt policy;
2. Perspective Packet retrieval and isolation;
3. Actor Proposal and central Resolver;
4. narrator/audit/checkpoint integration;
5. Resume/invalidation/cost and API/UI;
6. automated validation and browser evidence;
7. A/B and real-run artifacts, approval and downstream proof.

Do not mark runtime or paid-acceptance boxes complete in a code-only commit.

## Exit condition

Move this file to `docs/exec-plans/completed/` only after:

- every automated validation item has current evidence;
- the 12-chapter A/B gate passes;
- the fresh 48-chapter cancel/Resume run completes through the real product
  chain;
- GPT-5.6 review and approval criteria pass without manually accepting a hard
  blocker;
- canonical promotion and Episode/Script isolation are proven; and
- `tasks.md`, `docs/README.md`, the design source and delivery ledger are synced
  in the same logical commit.

Until then, the existing v3 `brief_only` chain remains the default and this
plan must not be described as implemented or accepted.
