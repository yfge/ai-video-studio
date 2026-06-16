# STD-TIMELINE-001: Timeline-First Provider Chain Preserves Media Lineage

## Intent

Timeline-first production samples should prove more than provider success. The
script, Timeline seed, shot plan, character image, clip videos, render job, and
review artifacts must keep ordered lineage so a reviewer can trace the final
media back to the generated plan.

## Scope

- Provider-chain quality samples under `scripts/harness/provider_chain_*`
- Production quality reports under `scripts/harness/production_quality_*`
- Timeline render/export evidence under `artifacts/runs/<run_id>/`

## Automatic Enforcement

The production quality harness evaluates:

- request order through `evaluate_timeline_order`
- render output structure through `evaluate_render_structure`
- character/clip lineage through `evaluate_character_consistency`
- aggregate stability through `aggregate_quality_report`

## Evidence

Reports include `standard_id=STD-TIMELINE-001`, `covered_standard_ids`,
`timeline_order`, `render_structure`, `character_consistency`, hard failures,
sample artifacts, CSV/review-pack paths, and harness run IDs.

## Repair Path

Repair the earliest broken lineage point. Do not treat a provider-chain sample
as trial-ready when Timeline order, render duration, clip lineage, or visual
review artifacts are missing, even if provider calls succeeded.

## Revision Trigger

Update this standard when Timeline Spec versions change, when a new media stage
becomes required, or when real browser evidence shows a successful report that
cannot be traced back to a concrete Timeline plan.
