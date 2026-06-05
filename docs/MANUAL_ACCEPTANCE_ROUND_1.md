# First Manual Acceptance Round

## Scope

This round validates the first usable Sprint 16 package set and the Sprint 17 Production Studio preflight.

The acceptance target is technical handoff readiness, not final production art approval.

## Baseline

- Commit: `d30678510e8e0a434408562e307cde79d5e2a302`
- STYLE_CODE: `STYLE_0003`
- Device type: `mobile_landscape`
- Asset mode: `resource_production`
- Screens:
  - `main_ui`
  - `role_ui`
  - `bag_ui`
  - `shop_ui`
  - `activity_ui`

## Preflight Verification

Automated checks passed:

- Root tests: `37 passed`
- Backend tests: `32 passed`
- Frontend tests: `7 suites passed`, `10 tests passed`
- Frontend build: passed
- 996 export validator: passed for all five `STYLE_0003` packages

Production Studio preflight:

- `GET /studio`: HTTP 200
- `GET /production-studio/style-codes`: returns `STYLE_0001`, `STYLE_0002`, and `STYLE_0003`
- Report file access through `/production-studio/files/...`: HTTP 200 for every checked `ui_preview.png`, `delivery_report.html`, `candidate_preview.html`, and `component_quality_report.html`

## Manual Review Checklist

For each screen package:

1. Open `ui_preview.png`.
2. Check overall visual consistency with `STYLE_0003`.
3. Open `candidate_preview.html`.
4. Mark useful candidates for later naming and cleanup.
5. Open `component_quality_report.html`.
6. Record missing or incorrectly grouped regions.
7. Confirm whether current generic candidates are enough for 996 technical handoff.

Acceptance statuses now supported in `/studio` Result Center:

- `待验收`
- `验收通过`
- `需要修改`

Each generated screen also has an `验收记录` field for manual notes during review.

Package paths:

- `assets/uploads/996-ready/STYLE_0003/main_ui/14115d5fb8df4bfe91b9b2e504019167`
- `assets/uploads/996-ready/STYLE_0003/role_ui/d4b8e13ac79d42f5820b02899e6eefbd`
- `assets/uploads/996-ready/STYLE_0003/bag_ui/03cc14e509ad4a33a4ce5e3ddb726d7f`
- `assets/uploads/996-ready/STYLE_0003/shop_ui/bd5b81c98d8a4e51b72ac8554b07fb2f`
- `assets/uploads/996-ready/STYLE_0003/activity_ui/0f95bbdd82cb408d8b9afeb9ed8669aa`

## Known Acceptance Risks

- Live generation from `/studio` currently requires an enabled real provider and a local key environment variable such as `OFOX_API_KEY` or `OPENAI_API_KEY`.
- On this machine, the smoke request returned: `Environment variable OFOX_API_KEY is not set`.
- Therefore this round can accept existing package quality and Studio preflight, but not live re-generation from the web UI.
- `common_icons` semantic naming is still incomplete.
- Transparent PNG status remains metadata-level and requires manual art review.
- `role_ui`, `bag_ui`, and `activity_ui` should receive closer visual review because earlier quality reports showed suspected missing regions.

## Round 1 Decision Template

- Package structure: Pass / Fail
- Visual style consistency: Pass / Conditional / Fail
- Candidate usefulness: Pass / Conditional / Fail
- Missing semantic icons acceptable for technical handoff: Yes / No
- Ready for Sprint 18 improvements: Yes / No
