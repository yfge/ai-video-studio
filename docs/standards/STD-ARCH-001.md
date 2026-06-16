# STD-ARCH-001: Source Files Stay Below Size Limits

## Intent

Large files hide ownership, make agent edits riskier, and turn review into
whole-file archaeology. Source files should stay below the repository limits in
`docs/architecture/file-size-limits.md`.

## Scope

- Backend Python under `ai-pic-backend/app/`, `ai-pic-backend/tests/`, and
  `ai-pic-backend/scripts/`
- Frontend TypeScript and TSX under `ai-pic-frontend/src/`
- Repository automation under `scripts/`

## Automatic Enforcement

`python scripts/check_repo_contracts.py --mode diff <changed files>` fails on
new oversized files. `--mode audit` reports historical oversized files with
baseline exemption metadata.

## Evidence

Contract reports include `standard_id=STD-ARCH-001`, `line_count`, `limit`,
`baseline_exemption`, and the affected path.

## Repair Path

Split oversized code into focused helpers, repositories, services, hooks,
components, or fixtures that match the existing module boundary. Do not raise a
limit unless the baseline entry includes a concrete repayment note.

## Revision Trigger

Update this standard when size limits change or when a repeated review finding
shows that a file can stay under the limit while still concentrating unrelated
ownership.
