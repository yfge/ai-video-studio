## User Prompt

IP 页面的图像生成展示有问题 都聚在一起了

## Goals

- Fix the Virtual IP detail page image manager layout so generated/uploaded images no longer crowd into a narrow column.
- Keep the change scoped to the frontend Virtual IP image display path.
- Add regression coverage for adaptive image-grid columns.
- Capture real browser evidence for the user-visible image layout path.

## Changes

- Moved `VirtualIPImageManager` out of the constrained `OperatorWorkspace` main column on the Virtual IP detail page so it can use the full operator content width below the detail/inspector workspace.
- Changed the image grid from fixed `grid-cols-2` to an adaptive `auto-fit/minmax` grid so cards naturally drop to fewer columns when the available width is small.
- Changed the image manager internal layout so category + gallery use a two-column layout on large screens, while the generate/upload panel spans full width until `2xl`.
- Removed the later `2xl` narrow generation rail after user screenshot evidence showed the form controls still squeezed at wide viewports.
- Forced top-level generation form controls to occupy full rows inside the image manager so model/profile/style controls cannot collapse into narrow columns.
- Added `tests/virtualIPImageGrid.test.tsx` to guard against reintroducing a fixed two-column image rail.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npm run test -- tests/virtualIPImageGrid.test.tsx` -> failed before the fix with `grid grid-cols-2 gap-3 2xl:grid-cols-3` missing `auto-fit`, then passed after the layout change.
- `cd ai-pic-frontend && npm run test -- tests/virtualIPImageGrid.test.tsx` -> failed again while `VirtualIPImageManager` still had `2xl:grid-cols-[160px_minmax(0,1fr)_340px]`, then passed after removing the 340px generation rail.
- `cd ai-pic-frontend && npm run test -- tests/virtualIPImageGrid.test.tsx` -> failed while `ImageGenerationForm` lacked `[&>*]:col-span-full`, then passed after forcing top-level generation controls to span the full form row.
- `cd ai-pic-frontend && npm run lint` -> passed with 0 errors and 18 existing warnings.
- `cd ai-pic-frontend && npm run test` -> passed, 28 tests.
- `cd ai-pic-frontend && npm run build` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff 'ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx' ai-pic-frontend/src/components/features/virtual-ip-images/ImageGrid.tsx ai-pic-frontend/src/components/features/virtual-ip-images/VirtualIPImageManager.tsx ai-pic-frontend/tests/virtualIPImageGrid.test.tsx` -> passed.
- `python scripts/check_repo_contracts.py --mode diff 'ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx' ai-pic-frontend/src/components/features/virtual-ip-images/ImageGrid.tsx ai-pic-frontend/src/components/features/virtual-ip-images/VirtualIPImageManager.tsx ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx ai-pic-frontend/tests/virtualIPImageGrid.test.tsx` -> passed after keeping `ImageGenerationForm.tsx` at 249 lines.

2. Browser or MCP validation:

- Entry URL: `http://localhost:3000/virtual-ip/233525e9045146d580a1d18ef4a28161`.
- User path: opened the local app, used the test auth token from `POST http://localhost:8000/api/v1/auth/login` because the scripted login form did not submit, opened the IP detail page, scrolled to `#ip-images`, and clicked `生成图片`.
- Console: only dev/HMR and React DevTools messages were observed during the fallback run; no layout-blocking runtime error was observed.
- Network: Virtual IP detail, environments, images, categories, styles, and AI model requests returned `200` in the fallback browser path.
- Result: before fix, `#ip-images` was constrained to `772px`, the image grid was `202px`, and cards were about `95px` wide. After fix, `#ip-images` used `1152px`, the image grid was `942px`, and cards were about `179px` wide. Evidence is stored under `artifacts/runs/ip-image-layout-20260603T085821Z/`.
- Follow-up screenshot evidence: the generation form still collapsed in a 340px `2xl` rail. After removing that rail and forcing full-row form controls, Playwright fallback at `900px` viewport showed the form grid computed to one `784px` column, the profile/style controls occupied full rows, and model dropdowns were `388px` each. Evidence is stored under `artifacts/runs/ip-image-form-layout-20260603T100306Z/`.

3. Conflict signals and corrections:

- Initial assumption: the image card component might be overlapping internally.
- Contradicting evidence: browser metrics showed the shared card was being squeezed by nested page grids rather than overlapping itself.
- Reproduction and fix: reproduced on the real IP detail page at 1440px viewport, then widened the image manager by moving it outside the main/inspector workspace and made the image grid adaptive.
- Final verified state: image cards render in a normal-width adaptive grid, and the generate form sits below the gallery at this viewport instead of consuming the gallery width.

Chrome DevTools note: the preferred DevTools MCP path failed twice with `http://127.0.0.1:9222/json/version` returning HTTP Not Found. Playwright's bundled Chromium was not installed, so the browser fallback used Playwright with the system Chrome executable. This is fallback evidence, not Chrome DevTools MCP evidence.

## Next Steps

- No further code changes required for this layout issue.
- None.

## Linked Commits

- This commit.
