# Harness Foundation

## Goal

Land the first harness-first slice:

- worktree bootstrap
- doctor / browser / golden-path CLIs
- repo doc drift checks
- repo contracts checks
- trace headers and JSONL logs

## Exit Criteria

- A run creates `artifacts/runs/<run_id>/manifest.json`.
- The doctor can report reachable frontend, backend, and nginx URLs.
- Browser flow writes console/network/result evidence.
- Golden path can at least validate mock smoke and authenticated task polling.
