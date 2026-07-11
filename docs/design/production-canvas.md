# Production Canvas Design

> Status: Proposed
>
> Last updated: 2026-07-11

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

The design combines patterns from three product categories.

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
four visible levels.

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

As of 2026-07-11, the implementation has a real `/canvas` route, dynamic plan
nodes, direct skill execution, task evidence, task refresh, media parameters,
editable visual edges, notes, pan/zoom/drag interactions, keyboard controls,
server-backed run persistence, autosave, and restore links.

The current graph is not yet the execution source of truth:

- The planner does not consume canvas edges when building skill requests.
- Auto-execution scans ready nodes rather than scheduling from graph
  dependencies.
- Visual edges do not define typed ports, input mapping, or stale descendants.
- Node cards do not show real candidate previews, generation history, approval,
  or downstream consumption.
- Timeline placement is represented as a stage but is not yet the complete
  approved-video-to-stable-clip contract described above.
- Raw outputs and backend reuse details are more visible than creative review
  decisions.

This means the current product is an interactive task dashboard over existing
pipelines, not yet a complete production workflow canvas.

## Delivery Phases

### Phase 1: Executable typed graph

- Introduce versioned node ports and typed edge bindings.
- Validate graph mutations and restored definitions on the backend.
- Calculate readiness and execution order from dependencies.
- Support run-node and run-downstream with stale propagation.

Exit criterion: changing an edge changes the actual request context and the
affected downstream execution set.

### Phase 2: Media candidate review vertical slice

- Render real image and video candidates inside nodes.
- Preserve candidate history across retries.
- Add explicit approval and rejection transitions.
- Bind approved image output to video start-frame input.
- Bind approved video output to a stable Timeline clip.

Exit criterion: an operator completes the image-to-video-to-Timeline path in the
canvas without copying URLs or IDs.

### Phase 3: Production organization and recovery

- Add scene/episode sections, minimap, search, filters, and multi-select.
- Add retry with original/current definition, cancel, and resume.
- Show stale impact before changing approved inputs.
- Move raw backend details into an advanced diagnostics surface.

Exit criterion: a multi-scene production remains understandable and recoverable
after partial failure or upstream revision.

### Phase 4: Collaboration and reuse

- Add comments, approver identity, permissions, and activity history.
- Add reusable domain templates and subflows without exposing provider-specific
  implementation graphs.
- Add performance budgets and virtualization for large productions.

Exit criterion: a production team can review, approve, and reuse workflows
without sharing operator credentials or rebuilding graph structure manually.

## First Vertical-Slice Acceptance Criteria

- A real image-generation execution creates previewable candidates on its
  canvas node.
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
