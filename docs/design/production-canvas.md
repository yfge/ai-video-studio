# Production Canvas Design

> Status: Implemented through Phase 6; consolidated release validation remains
> open
>
> Last updated: 2026-07-15

## Product Decision

The production canvas is an executable and reviewable map of short-drama
production. It is not a general-purpose whiteboard and it is not a frontend
copy of backend APIs, workers, or provider-specific model graphs.

The canvas should let an operator move from a brief to approved media without
losing production context:

1. Create or restore a production plan.
2. Organize work by episode, scene, shot, and shared asset context.
3. Generate and compare image, video, audio, and report outputs in place.
4. Approve one candidate as the explicit input to downstream work.
5. Re-run one node or the affected downstream subgraph when inputs change.
6. Send approved shot assets to Timeline for sequencing, duration, render, and
   export.

Timeline remains the single source of truth for final clip identity, ordering,
duration, tracks, render versions, and export state. The canvas owns production
orchestration, candidate review, dependency visualization, and execution
evidence around that Timeline.

## Why This Exists

The platform already has script, storyboard support, image generation, video
generation, task queues, Timeline, render, and report pipelines. Operators still
need a surface that answers four questions without switching between unrelated
pages:

- What is being produced and why?
- Which approved inputs does each generation use?
- What is running, blocked, failed, stale, or ready for review?
- Which result was selected and where did it go next?

An infinite canvas is useful only when spatial organization and visible edges
make those answers clearer. Pan, zoom, drag, notes, and editable lines are
supporting interactions, not the product outcome.

## Research Basis

The design combines patterns from four product categories.

### Spatial collaboration

- FigJam provides an infinite board, sections, connectors, pages, and familiar
  pan/zoom behavior.
- Miro adds frames, layers, comments, navigation maps, permissions, and
  presentation paths for large boards.

Use these patterns for navigation, grouping, review, and collaboration. Do not
copy general meeting facilitation or decorative whiteboard tools.

Sources:

- https://help.figma.com/hc/en-us/articles/15300412458647-Explore-FigJam-files
- https://help.figma.com/hc/en-us/articles/1500004362321-Guide-to-FigJam
- https://help.miro.com/hc/en-us/articles/20967864443410-Miro-s-new-simplified-user-interface
- https://help.miro.com/hc/en-us/articles/20258488000786-Layers

### Executable workflow graphs

- ComfyUI makes node connections, execution queues, and generated media visible
  on one graph.
- n8n separates node, partial, and production executions and supports retrying
  failures with original or updated workflow definitions.

Use these patterns for dependency semantics, execution state, retries, and
history. Do not expose low-level provider implementation details or require
operators to build large model-specific graphs.

Sources:

- https://docs.comfy.org/interface/overview
- https://docs.n8n.io/workflows/executions/all-executions/

### AI creative production

- FLORA connects text, image, and video nodes so creators can branch and compare
  directions in one canvas.
- Freepik Spaces provides typed ports, compatible-node discovery, run-node,
  run-workflow, run-downstream, inline media results, generation history,
  autosave, and collaboration.
- LTX Studio keeps filmmaking concepts visible from script and storyboard to
  shot retake and Timeline editing.

Use these patterns for multimodal outputs, candidate selection, execution
scope, and domain language.

Sources:

- https://docs.flora.ai/editor/canvas
- https://flora.ai/updates/canvas-at-scale
- https://www.magnific.com/ru/ai/docs/getting-started-with-spaces
- https://ltx.io/studio/platform/ai-movie-maker

### Hierarchical navigation on an infinite canvas

- React Flow distinguishes layouted sub-flows from graph edges and shows
  expand/collapse as a projection of a complete graph, so a UI parent or hidden
  descendant is not treated as a new business relationship.
- Miro combines diagram connectors with mind-map expand/collapse and child
  counts, supporting progressive disclosure without removing source data.
- Figma keeps parent/child structure visible in a synchronized Layers panel and
  uses sections to organize large canvas regions without redefining the
  underlying content.

Use these patterns for stable column placement, progressive disclosure, and
outline-to-canvas focus. Do not copy example code or overload layout ownership
with domain ownership.

Sources:

- https://reactflow.dev/learn/layouting/sub-flows
- https://reactflow.dev/examples/layout/expand-collapse
- https://reactflow.dev/learn/layouting/layouting
- https://help.miro.com/hc/en-us/articles/25275263961874-Miro-Diagrams
- https://help.miro.com/hc/en-us/articles/360017730753-Mind-map
- https://help.figma.com/hc/en-us/articles/360039831974-View-layers-and-assets-in-the-Layers-Panel
- https://help.figma.com/hc/en-us/articles/9771500257687-Organize-your-canvas-with-sections
- https://help.figma.com/hc/en-us/articles/360039959014-Parent-child-and-sibling-relationships

### Autonomous planning and reliability

The production canvas planner follows a constrained planner/compiler/executor
split rather than allowing an LLM to call production workers directly.

- The LLM proposes the smallest useful ordered skill set and declared
  dependencies for the current production goal.
- A deterministic backend compiler maps those dependencies to allowlisted,
  typed ports and rejects unknown skills, unsupported dependencies, duplicate
  bindings, missing prerequisites, and cycles.
- The existing Graph v2 validator is the feasibility gate. Only a validated DAG
  can be returned to the browser or persisted as an executable run.
- Structured output gets at most one repair attempt. Provider failure or a
  second invalid proposal falls back to the canonical deterministic production
  plan, with planner mode, provider/model, repair count, validation errors, and
  fallback reason retained as evidence.
- The model never owns world state or worker dispatch. Persisted Run, Task,
  candidate, Timeline, and graph state remain authoritative.

This is consistent with recent planning research: planner/executor separation
and dynamic plan construction improve adaptability; external constraint
checking is needed before execution; and programmed state tracking should
scaffold LLM reasoning rather than trusting the model to remember environment
state. The initial release intentionally implements bounded proposal repair,
not unbounded runtime self-replanning.

Sources:

- https://arxiv.org/abs/2602.19633
- https://arxiv.org/abs/2503.09572
- https://arxiv.org/abs/2410.14865
- https://openreview.net/forum?id=oCcbZPlQsY
- https://openreview.net/forum?id=bVljzwUxnT
- https://arxiv.org/abs/2509.03581

## Product Principles

### Domain concepts over infrastructure concepts

Operators work with briefs, scenes, shots, characters, environments, candidate
images, candidate videos, audio, approvals, and deliverables. API endpoints,
repositories, workers, raw output dictionaries, and provider lineage belong in
an optional diagnostics view rather than the primary node UI.

### The graph must be executable

An edge is not decoration. It declares a typed input binding between one node
output and one downstream node input. Editing an edge must change execution
context, readiness, invalidation, and downstream scope.

### Human selection is a first-class state transition

Generation success does not mean a node is complete. Media generation moves a
node into review. A downstream node becomes ready only when required inputs
have an approved candidate or an explicit policy allows automatic selection.

### Backend reuse stays behind the canvas contract

The canvas should reuse existing script, storyboard, image, video, Timeline,
render, and report queues. It must not introduce a parallel media generation
stack. The frontend consumes a stable canvas plan and execution contract while
backend services translate nodes into existing domain operations.

### Timeline remains authoritative

The canvas can propose and approve shot assets. It cannot silently redefine
Timeline clip ordering, duration, or render state. Adding a video to Timeline is
an explicit operation against a stable `clip_id` and Timeline version.

## Information Architecture

Large productions should not be represented as one flat graph. The canvas uses
two complementary projections. The entity hierarchy answers where production
content belongs and lets an operator navigate it. The executable DAG answers
what depends on what and what can run. They share stable domain identifiers but
remain independent views, and the operator can switch between them without
rewriting either graph.

The entity hierarchy uses six stable left-to-right columns:

| Column      | Displayed entity                  | Truthful relation                                                           |
| ----------- | --------------------------------- | --------------------------------------------------------------------------- |
| IP          | Virtual IP                        | Root production context                                                     |
| Environment | Reusable environment resource     | Available to the IP; it is not owned by a Story                             |
| Story       | Story                             | References a participating IP                                               |
| Episode     | Episode                           | Belongs to a Story                                                          |
| Storyboard  | Timeline `video` clip             | Stable shot/storyboard identity from the Episode Timeline                   |
| Video       | Current-version video media asset | Bound to a stable Timeline version and `clip_id` through clip-asset lineage |

The truthful primary chain is:

```text
IP -> Story -> Episode -> Timeline video clip -> video asset
```

Environment nodes form the IP's reusable resource pool. A dashed reference edge
may show that a Story can use an Environment, but the canvas must not fabricate
`Environment -> Story` ownership because the current model has no such relation.
The Environment column remains visible between IP and Story so operators can
inspect available production context while the edge style preserves the real
semantics.

Within the executable projection, the canvas continues to use four visible
levels.

| Level                 | Purpose                           | Examples                                                                               |
| --------------------- | --------------------------------- | -------------------------------------------------------------------------------------- |
| Project context       | Shared constraints and references | Brief, Virtual IP, characters, environments, visual style, delivery spec               |
| Narrative             | Story organization                | Episode, scene, beat, shot group                                                       |
| Production            | Executable creative work          | Script, storyboard support, image candidates, video candidates, audio, render          |
| Decision and evidence | Human and runtime outcomes        | Approved candidate, rejection reason, task execution, cost, report, Timeline placement |

Episode and scene sections provide collapsible spatial grouping. Shot-level
production stays visible inside or adjacent to its scene. Shared character,
environment, and style references remain available as explicit graph inputs
rather than being copied invisibly into every node.

Entity nodes stay in their assigned column and use deterministic vertical
ordering. Expansion never reinterprets a layout parent as a domain parent.
Collapsing a node hides its visible descendants but retains them in hierarchy
state, shows the number hidden, and leaves the executable DAG unchanged. The
hierarchy outline and canvas selection stay synchronized: selecting either one
focuses the same stable entity identity in the other.

## Node Model

Every node has a stable identity and a domain-level contract.

Required fields:

- `node_id`: stable within the canvas run.
- `node_type`: domain type, not a provider or service name.
- `scope`: project, episode, scene, shot, or Timeline clip.
- `status`: lifecycle state defined below.
- `input_ports`: typed required and optional inputs.
- `output_ports`: typed outputs available to downstream nodes.
- `config`: operator-controlled generation or transformation settings.
- `selected_output_id`: approved output when the node requires review.
- `definition_version`: version of the node configuration.
- `execution_summary`: latest execution status and evidence reference.

Primary node types:

- Brief and production-plan node.
- Script, scene, beat, and shot-plan node.
- Character, environment, style, and uploaded-media reference node.
- Storyboard-support and keyframe node.
- Image-candidate set and video-candidate set node.
- Voiceover, music, and sound-effect node.
- Timeline placement, render, export, and report node.
- Manual note and review comment node.

Task executions are evidence attached to an executable node. A compact task
evidence node may be displayed when useful, but it is not a connectable workflow
input and must not become a duplicate source of business state.

## Edge Model

Edges bind a source output port to a target input port:

```json
{
  "edge_id": "edge-image-42-to-video-17",
  "from": { "node_id": "image-42", "port": "approved_image" },
  "to": { "node_id": "video-17", "port": "start_frame" },
  "binding_type": "selected_output",
  "required": true
}
```

Initial port types:

- `text`: brief, script, prompt, shot description, motion description.
- `image`: character reference, environment reference, storyboard panel,
  start frame, end frame, approved image.
- `video`: approved clip, source video, rendered output.
- `audio`: dialogue, voiceover, music, sound effect.
- `entity_ref`: Virtual IP, environment, episode, Timeline, stable clip.
- `execution_ref`: task, render job, report evidence.

Connection rules:

- Input and output types must be compatible.
- A required single-value input accepts one active binding.
- Multi-reference inputs may accept several ordered bindings.
- Cycles are rejected in the executable dependency graph.
- Task evidence and manual notes cannot be executable edge targets.
- Deleting or replacing an edge recalculates target readiness and stale state.
- Restored runs must validate unknown nodes, ports, duplicates, self-edges, and
  stale bindings before becoming executable.

## Execution Model

The server evaluates the typed graph as a directed acyclic graph. The browser
may render optimistic state, but it does not independently decide dependency
readiness.

Execution scopes:

- Run node: execute only the selected node with its approved current inputs.
- Run downstream: execute the selected node and affected descendants.
- Run ready: execute all currently ready nodes in dependency order.
- Resume: continue a paused or interrupted run without repeating valid outputs.
- Retry: retry a failed node with the original definition or current saved
  definition.
- Cancel: stop queued or running work while preserving completed outputs.

Node lifecycle:

| Status    | Meaning                                                             |
| --------- | ------------------------------------------------------------------- |
| Draft     | Configuration or required bindings are incomplete                   |
| Ready     | Required approved inputs exist and execution is allowed             |
| Queued    | Existing backend task has been accepted                             |
| Running   | Backend task is active                                              |
| Review    | One or more outputs exist but no required candidate is approved     |
| Approved  | An output is selected and valid for downstream use                  |
| Stale     | An upstream definition, binding, or selected output changed         |
| Failed    | Latest execution failed with inspectable evidence                   |
| Cancelled | Execution stopped without deleting completed history                |
| Blocked   | External prerequisite, permission, quota, or domain gate is missing |

Changing node configuration, an input edge, or an approved upstream candidate
increments `definition_version`. Descendants that consumed the previous version
become stale. The operator can keep the old result, re-run selected descendants,
or run the whole affected subgraph.

## Candidate Review

Image and video generation nodes are candidate sets, not single opaque task
cards.

Each candidate records:

- Previewable media and persistent asset identity.
- Prompt, references, model/provider, parameters, cost, and duration.
- Execution and definition versions.
- Quality or policy warnings.
- Review state, reviewer, timestamp, and optional rejection reason.
- Downstream consumers of the selected candidate.

Required interactions:

- Preview images at useful resolution and play video inline.
- Compare candidates from the same or different executions.
- Approve one candidate for downstream use.
- Reject, regenerate, or branch from a candidate.
- Browse prior generations without replacing the current approval silently.
- Show what will become stale before changing an approved candidate.

## Timeline Integration

The first commercial vertical slice is:

```text
shot context -> image candidates -> approved image -> video candidates
-> approved video -> stable Timeline clip -> render/export
```

The Timeline placement node must:

- Target an existing stable `clip_id`, or explicitly create a clip through the
  Timeline service.
- Require the current Timeline version to prevent silent overwrite.
- Record selected canvas asset and generation lineage on the clip asset.
- Return the resulting Timeline version and clip asset identity to the canvas.
- Make Timeline changes visible immediately in both canvas and Timeline views.

Canvas layout is not Timeline ordering. Moving nodes on the canvas never changes
clip order or duration.

## Interaction Requirements

The existing pan, zoom, fit, node drag, focus, keyboard, note, save, restore, and
Run ID behavior remains the interaction baseline. Product completion additionally
requires:

- Typed input and output ports with direct drag-to-connect behavior.
- Compatible-node discovery when connecting into empty canvas space.
- Minimap and jump-to-selection for large productions.
- Multi-select, alignment, duplication, and scene/episode sections.
- Undo and redo for graph definition changes.
- Search and filters for scene, node type, status, owner, and stale work.
- Contextual node actions instead of a permanently dense global toolbar.
- Raw backend and provider diagnostics behind an explicit advanced view.

### Domain hierarchy interaction contract

- `/canvas` without a Run ID opens the entity hierarchy first. A deep link with
  a Run ID opens the executable graph so shared execution and review links keep
  their existing meaning.
- The view switch changes only the projection. It does not convert entity
  relations into executable bindings or mutate a saved run.
- Initial load fetches IP roots. Child collections load progressively when the
  operator expands an IP, Story, Episode, or Timeline clip. A collapsed node
  retains loaded data and displays its hidden descendant count.
- Each entity type stays in its fixed column across expand, collapse, refresh,
  and refocus operations. New children receive deterministic vertical positions
  so unrelated branches do not jump.
- The outline mirrors the visible hierarchy. Selecting an outline row selects
  and focuses the matching canvas node; selecting a canvas node highlights the
  same outline row.
- Solid labelled edges represent ownership or stable containment, arrowed
  production edges represent Timeline clip-to-asset lineage, and dashed labelled
  edges represent reusable references such as an IP Environment available to a
  Story. Meaning is never conveyed by color alone.
- Storyboard entities come from Timeline `video` clips, not from a second
  independent storyboard identity. Video children come from the matching
  Timeline version and stable `clip_id` asset bindings.
- Empty, loading, and failed branches remain local to the expanded node. One
  failed branch does not replace the complete hierarchy with a global error.

## Persistence And API Contract

The saved canvas run must separate definition, review, and execution history:

- Graph definition: nodes, typed ports, edges, sections, positions, and viewport.
- Review state: candidate approvals, rejections, comments, and selected outputs.
- Execution history: immutable attempts, tasks, artifacts, errors, usage, and
  lineage.
- External bindings: episode, script, Virtual IP, environment, Timeline,
  `clip_id`, task, render job, and media asset identifiers.

Autosave stores graph and review state. Execution history is appended by backend
task processing and must not be overwritten by a stale browser autosave.

The backend remains responsible for:

- Validating graph definitions and typed bindings.
- Resolving approved upstream outputs into existing service requests.
- Calculating readiness, dependency order, and stale descendants.
- Dispatching existing queues idempotently.
- Persisting execution and media lineage.
- Enforcing permissions and current Timeline versions.

## Collaboration And Governance

Collaboration is a later phase, but the data model must not block it.

Required eventual roles:

- Viewer: inspect canvas and outputs.
- Commenter: add review comments without changing the graph.
- Editor: change graph definition and node configuration.
- Approver: approve candidates and Timeline placement.

Comments attach to node, candidate, edge, or section identity. Presence cursors
and live co-editing are not required for the first vertical slice. Audit fields
must already identify who changed definitions and who approved outputs.

## Current State And Gap

As of 2026-07-15, Phases 1-5 are implemented on the real `/canvas` route:

- The backend validates versioned typed ports and edges, computes readiness
  from graph dependencies, resolves bound inputs into existing skill requests,
  and supports Run Node, Run Downstream, and Run Ready.
- Definition, binding, and selected-output changes increment versions and mark
  affected descendants stale. The UI shows that impact before a candidate
  switch.
- Image and video nodes show persistent media history and previewable
  candidates. Approval, rejection with an optional reason, reviewer identity,
  and review timestamps survive Run ID restoration independently from browser
  autosave.
- Approved video placement targets a stable Timeline clip and expected Timeline
  version, then returns the updated version and media lineage to the canvas.
- The planning header loads accessible IP, environment, episode, and script
  options by name. Script choices are scoped to the selected episode, so the
  operator does not copy Episode or Script IDs into the canvas workflow.
- Creating a plan replaces the initial seven-stage placeholder overview with
  one executable Skill graph. Typed edges connect the actual persisted Skill
  node identities; placeholder and Skill nodes are never shown as two parallel
  workflows.
- When an existing Script is selected, Script and Timeline assembly are reuse
  checkpoints rather than automatic regeneration. Storyboard preparation may
  run automatically, while image and video candidates remain explicit operator
  actions gated by review.
- Reusing an existing Timeline rebuilds storyboard support from its stable
  `video` clip identities without invoking the provider planning pipeline. When
  no shot plan exists, support frames map to `video` clips before considering
  dialogue clips, preserving the clip contract required by video generation.
- The current-environment provider-backed acceptance run
  `9a4bbfdb95f846e4be216beb1b09ad88` approved image candidate `442`, generated
  and approved MiniMax video candidate `443`, and placed it into stable clip
  `video_scene_90_beat_3991_001`, advancing Timeline `69` from v5 to v6. Run ID
  restoration preserved the review and placement state.
- Image and video candidate execution defaults to frame `0` when the operator
  does not select frames, so an exploratory canvas action cannot fan out across
  the whole storyboard unexpectedly. Storyboard image workers re-check persisted
  cancellation between expensive stages and frames, and a task cannot report
  success unless at least one requested frame has a persisted image.
- Scene and episode sections, minimap navigation, search and filters,
  multi-select layout operations, duplication, undo/redo, diagnostics, retry,
  resume, and cancel are available as production recovery tools.
- Owner-managed Viewer, Commenter, Editor, and Approver roles gate graph edits,
  execution, comments, candidate review, and Timeline placement. Comments attach
  to stable node, candidate, edge, and section identities, while definition,
  execution, review, placement, comment, and membership events share one
  persistent activity history.
- Provider-agnostic role look, scene look, shot review, and delivery templates
  insert reusable Skill subgraphs with typed edges and persistent sections.
  Every instance receives unique graph identities and inherits the active Run
  and production context without exposing service or worker implementation.
- Task attempts and media assets remain execution evidence; the saved graph and
  review state remain the current orchestration definition.
- The independent six-column entity hierarchy progressively resolves IP,
  Environment resources, Stories, Episodes, Timeline clips, and exact-version
  video assets while keeping saved executable Runs unchanged. It shares a typed
  domain context with one-sentence planning, so either view can identify the
  same Story, Episode, Script, Timeline version, and stable clip without merging
  the hierarchy projection into the executable graph.

The remaining release gap is deliberately outside the completed feature phases:

- Before release, the complete provider-backed image-to-video-to-Timeline path
  still needs one consolidated current-environment browser run; existing
  evidence is distributed across the implementation slices.

## Delivery Phases

### Phase 1: Executable typed graph

Status: Complete.

- Introduce versioned node ports and typed edge bindings.
- Validate graph mutations and restored definitions on the backend.
- Calculate readiness and execution order from dependencies.
- Support run-node and run-downstream with stale propagation.

Exit criterion: changing an edge changes the actual request context and the
affected downstream execution set.

### Phase 2: Media candidate review vertical slice

Status: Implemented for approval, rejection, regeneration and branching,
restoration, stale propagation, and stable Timeline placement. Consolidated
release validation remains open.

- Render real image and video candidates inside nodes.
- Preserve candidate history across retries.
- Add explicit approval and rejection transitions.
- Bind approved image output to video start-frame input.
- Bind approved video output to a stable Timeline clip.

Exit criterion: an operator completes the image-to-video-to-Timeline path in the
canvas without copying URLs or IDs.

### Phase 3: Production organization and recovery

Status: Complete for the interaction and run-control scope below.

- Add scene/episode sections, minimap, search, filters, and multi-select.
- Add retry with original/current definition, cancel, and resume.
- Show stale impact before changing approved inputs.
- Move raw backend details into an advanced diagnostics surface.

Exit criterion: a multi-scene production remains understandable and recoverable
after partial failure or upstream revision.

### Phase 4: Collaboration, reuse, and scale

Status: Complete.

- [Complete] Add comments, approver identity, permissions, and activity history.
- [Complete] Add reusable domain templates and subflows without exposing
  provider-specific implementation graphs.
- [Complete] Add performance budgets and viewport virtualization for large
  productions.

Large-production performance contract:

- The regression baseline is 500 nodes, 1,000 edges, and 100 sections. Filters,
  connection discovery, section state, and the minimap continue to operate on
  the complete logical graph.
- Above 80 logical visible nodes, the surface mounts only node cards intersecting
  the viewport plus 240 CSS pixels of overscan. At 100% zoom in an 1180 x 520
  viewport, the 500-node regression fixture must mount no more than 60 heavy
  node cards.
- Selected and executing nodes remain mounted even outside the viewport so
  keyboard actions, execution state, and focus transitions do not lose their
  targets. Edges render only when both endpoint cards are mounted.
- Small canvases keep the non-virtualized rendering path. Unit and real-browser
  scale checks provide the regression evidence; this is a structural render
  budget, not a device-dependent wall-clock benchmark.

Exit criterion: a production team can review, approve, and reuse workflows
without sharing operator credentials or rebuilding graph structure manually.

### Phase 5: Domain entity hierarchy and navigation

Status: Implemented. Automated acceptance and a real-browser traversal are
recorded under `artifacts/runs/canvas-domain-hierarchy-20260715/`. Chrome DevTools
transport returned HTTP 404 at `/json/version`, so the browser result is
explicitly recorded as a degraded Playwright fallback, not Chrome verification.

- Add a read-only entity projection with fixed `IP / Environment / Story /
Episode / Storyboard / Video` columns.
- Load the real primary chain `IP -> Story -> Episode -> Timeline video clip ->
video asset` from existing APIs and Timeline clip-asset lineage.
- Display IP Environments as reusable resources and optional dashed references,
  never as fabricated Story ownership.
- Keep the entity hierarchy and executable DAG as independent, switchable views.
- Add progressive expansion and collapse, hidden counts, deterministic layout,
  and synchronized hierarchy outline navigation.
- Preserve Timeline as the single source of truth for Storyboard clip identity,
  video binding, ordering, and version.

Exit criterion: an operator starts from an IP, navigates to a bound video asset
through real Story, Episode, and Timeline identities, and returns to the
executable DAG without copying an ID, losing the selected entity, or mutating
the saved run.

Executable acceptance:

- Opening `/canvas` without a Run ID displays all six labelled columns and real
  IP roots; opening a saved Run deep link displays that run's executable DAG.
- Expanding an IP loads its reusable Environments and participating Stories.
  The graph draws `IP -> Story` as the primary relation and does not draw or
  imply Environment ownership of a Story.
- Expanding a Story loads only its Episodes. Expanding an Episode loads stable
  `video` clips from the authoritative Timeline. Expanding a clip loads only
  video assets bound to the same Timeline version and `clip_id`.
- Collapsing any expanded branch hides its descendants, reports the hidden
  count, and restores the same stable positions and identities when reopened.
- Clicking an outline item focuses the matching canvas node, and clicking a
  canvas node highlights the matching outline item. Shared entities selected
  through an outline branch keep that branch's IP context.
- Solid ownership, dashed reference, and arrowed production edges carry visible
  text labels and remain distinguishable without relying on color.
- Switching between hierarchy and execution views leaves the executable graph,
  approvals, Timeline bindings, and hierarchy expansion state unchanged.
- Editing a Run ID remains a local draft. The URL changes only after a Run is
  restored, saved, or created successfully, without remounting the canvas session.
  If routing selects a newer Run while an older request is busy, only the newest
  request may update canvas state and URL identity. Run actions, candidate review
  mutations, and candidate loads capture the current Run identity and operation
  epoch; a response captured before a route or persistence change is discarded.
  Route-attempt deduplication is separate from the confirmed Run identity, which
  changes only after a successful restore.
- Frontend tests cover relation truth, fixed-column layout, progressive loading,
  collapse counts, outline focus, view switching, and Run deep-link routing.
- Real-browser evidence records the six-column traversal, semantic edges,
  collapse/restore, synchronized outline, view switching, console state, and
  successful API responses under `artifacts/runs/<run_id>/`.

### Phase 6: One-sentence generation and hierarchy closure

Status: Implemented.

- Use one typed context across plan, execute, persisted Run nodes, Task results,
  manual hierarchy selection, and automatic hierarchy reveal:
  `virtual_ip_id / environment_id / story_id / episode_id / script_id /
timeline_id / timeline_version / clip_id / task_id`.
- Resolve explicit IDs first and validate their ownership and lineage. Without
  explicit IDs, match an accessible Story by title/tags and only parse an
  unambiguous `第 N 集`; never guess between ambiguous Stories or silently create
  a Story/Episode as a side effect of planning.
- Return `resolved_context` from planning and persist it as the Run request
  context. Return normalized `result_context` from Task responses while keeping
  historical `agent_run.result_ref` and `result_file_path` readable.
- Feed generated Script/Timeline/clip identities back into execution nodes and
  the Board context. A monotonic revision then reloads and expands the entity
  projection to the deepest known Story, Episode, Timeline storyboard, or video
  node; an older request cannot overwrite a newer reveal.
- Merge partial Run, Task, and browser contexts by lineage. When an upstream
  Story/Episode/Script/Timeline/version changes, descendants omitted by the new
  source are cleared instead of combining a new Timeline with an old clip.
  Late plan, execute, task, and render responses are scoped to their captured
  Run and operation identity before they may publish nodes or context.
- Selecting a hierarchy node writes the full domain lineage back to one-sentence
  planning. A selected Environment is retained while navigating within the same
  IP, but remains a reusable IP resource rather than fabricated Story ownership.
- When both IP and Environment are present, the Environment must belong to that
  IP's `VirtualIPEnvironment` pool. An IP with no linked Environment remains
  unbound instead of silently borrowing an unrelated account Environment;
  Environment-only planning remains supported before an IP is selected.
- Keep image/video candidate approval and Timeline placement explicit. Context
  closure enables continuation and navigation; it does not silently approve
  media or spend provider budget on downstream generation.

Exit criterion: an operator can start with a one-sentence instruction tied to a
real Story/Episode, receive the generated Script/Timeline identifiers, and see
the corresponding hierarchy branch refresh, expand, and focus without copying
an ID. Selecting that branch must supply the same identifiers to the next plan
or execution request.

Current-environment acceptance is recorded under
`artifacts/runs/canvas-one-sentence-hierarchy-closure-20260715/`. The real plan
resolved Story `61` / Episode `174`; selecting its stable Timeline clip fed
Script `144`, Timeline `70` v6, and
`video_scene_584_beat_4176_001` into the next plan and execution requests, after
which the hierarchy focused video asset `#353`. Task `6357` returned the same
nine-field `result_context`, and a clean Run deep-link reload had no console or
API failures. Chrome DevTools transport returned HTTP 404 at `/json/version`,
so the evidence names the Playwright fallback explicitly. Provider execution
was stubbed to avoid paid generation; Plan, Run, Task, and hierarchy reads were
real.

## First Vertical-Slice Acceptance Criteria

Implementation status: complete across the tracked slices. Release acceptance
remains open until one current-environment browser run covers the whole path.
The repository task board and per-change `agent_chats` entries are the source
of truth for existing commands, Run IDs, request IDs, and browser artifacts.

- A real image-generation execution creates previewable candidates on its
  canvas node.
- The operator selects the episode and optional existing script by name; changing
  the episode clears an incompatible script selection.
- Selecting one image persists an approved asset identity and changes the image
  node to Approved.
- A typed `approved_image -> start_frame` edge makes the video node Ready.
- Running downstream sends the approved image and shot context to the existing
  video queue without copying a URL manually.
- Task progress, failure, retry, and resulting video are visible on the same
  video node.
- Selecting one video persists approval and exposes an explicit Add to Timeline
  command.
- Timeline placement writes against a stable `clip_id` and current Timeline
  version, then returns the new version and asset lineage to the canvas.
- Changing the approved image marks the video and Timeline placement stale and
  never silently overwrites the current Timeline asset.
- Saving, reloading, and opening a shared Run ID restores graph definition,
  approval state, execution evidence, and Timeline binding consistently.
- Real-browser evidence covers the complete path with console, network, task,
  media, and Timeline assertions under `artifacts/runs/<run_id>/`.

## Success Measures

- Median time from approved shot context to Timeline-ready video.
- Number of manual page switches and copied URLs/IDs per approved shot.
- Candidate approval rate and generations per approved asset.
- Failed executions recovered without rebuilding upstream work.
- Stale downstream work detected before render.
- Percentage of final Timeline clip assets with complete canvas lineage.

## Non-Goals

- Replacing Timeline as the production source of truth.
- Building a general whiteboard, slide editor, or social collaboration product.
- Exposing provider-specific low-level graphs as the default workflow.
- Replacing existing script, storyboard, image, video, render, or report queues.
- Supporting arbitrary cycles or programmable control-flow nodes in the first
  release.
- Delivering real-time multi-user editing before the executable vertical slice.

## Validation Strategy

Design and contract checks:

- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`

Implementation checks are selected by affected layer:

- Backend unit and API tests for graph validation, readiness, dispatch,
  idempotency, stale propagation, Timeline version conflicts, and lineage.
- Frontend state and component tests for ports, candidate review, previews,
  execution states, stale warnings, restore, and keyboard behavior.
- Frontend lint and build for route and hydration-sensitive changes.
- Real-browser validation for every user-visible vertical slice, with evidence
  stored under `artifacts/runs/<run_id>/`.
