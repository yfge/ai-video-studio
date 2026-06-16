# STD-SCRIPT-001: Production Scripts Satisfy Beat-Level Quality Gates

## Intent

Production script generation must not persist scripts that are only
structurally valid. Beat-level drama, specificity, and filmability are part of
the production contract.

## Scope

- Product production script generation
- `StructuredScriptContract v1`
- Script quality gates and production harnesses under `scripts/harness/`
- Regression tests under `ai-pic-backend/tests/unit/services/script/` and
  `ai-pic-backend/tests/scripts/`

## Automatic Enforcement

Focused pytest coverage and production quality harnesses enforce the beat
contract, commercial specificity, dialogue quality, progression, hook, conflict,
payoff, cliffhanger, and filmability checks.

## Evidence

Use `structured_script_contract`, beat quality `failed_checks`, focused pytest
output, and `artifacts/runs/<run_id>/` harness reports as evidence.

## Repair Path

Fix the beat contract normalizer, prompt template, quality gate, repair loop, or
provider-chain payload. Do not mark a task successful merely because an HTTP
request returned 200 or a task row reached a terminal status.

## Revision Trigger

Update this standard when a real generated script passes existing checks but the
persisted task, script, or Timeline evidence still shows weak drama, bad
dialogue, missing beat structure, or unfilmable action.
