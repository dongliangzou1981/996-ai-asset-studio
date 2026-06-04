# Project Status

## 2026-06-04 Acceptance

Verified:

- Project CRUD
- Job Center
- Mock UI Job Creation
- Mock Job Runner
- Mock Pipeline Complete Flow
- Asset Record Creation
- Asset Binding To Generation Job

Accepted flow:

`Project -> Job -> Mock Runner -> Asset`

Sprint status:

- Sprint 5: accepted
- Sprint 6: accepted
- Sprint 7A: complete
- Sprint 7B: complete

Development priorities:

- P0: Real AI UI generation loop, `Prompt -> Provider -> Image -> Asset -> Preview`
- P1: 996 package export, slicing, manifest
- P2: Provider security hardening, audit, concurrency control, batch jobs

## Sprint 7C Phase 1

Status: complete

Scope:

- Establish Real Generation Pipeline skeleton.
- Add `real_ui_generation` job creation from Job Center.
- Add `RealJobRunner` placeholder execution.
- Create one placeholder `ui_preview` asset per completed real pipeline job.
- Link placeholder asset records to `generation_job_id`.
- Show completed jobs and result assets through existing Job Center and Assets flows.

Phase 1 does not connect OpenAI, OpenRouter, or ComfyUI. It does not add ZIP export or production slicing.

Current priority after Phase 1:

- P0: Connect a real model provider behind the existing pipeline boundary.
- P1: Add 996 package export, slicing, and manifest output.
- P2: Add provider security hardening, audit, concurrency control, and batch jobs.

## Sprint 7C Phase 1.5

Status: complete

Workflow status:

- Project selection: complete
- Style profile selection: complete
- Base panel selection: complete
- Optional reference image selection: complete
- Prompt capture: complete
- Real UI job creation: complete
- RealJobRunner placeholder execution: complete
- Asset creation and job binding: complete
- Job Detail traceability: complete
- Asset source traceability: complete

Closed workflow:

`Project -> Style Profile -> Base Panel -> Reference Image -> Prompt -> Real UI Job -> Asset -> Preview`

Conclusion:

The system now has the full UI generation workflow. The remaining work is real model provider integration.

## Sprint 7C Phase 2

Status: complete

Provider status:

- OpenAI: supported and preserved
- OpenRouter: provider type and runner skeleton added
- ComfyUI: planned

OpenRouter scope:

- Provider configuration uses only `api_key_env`
- Health check validates local environment variable presence
- Runner participates in the existing `Provider -> Runner -> Asset` structure
- No external OpenRouter request is made in this phase

Conclusion:

OpenRouter is now selectable and wired into the unified provider abstraction. The next step is a controlled real-model acceptance phase.

## Sprint 8 Planning

Status: planned

V1 final target:

`Prompt -> UI Generation -> Component Detection -> Annotation -> Transparent PNG Slice -> 996 Export Package`

Target export structure:

```text
996-ready/
  ui_preview.png
  components/
  manifest.json
  annotation.json
  preview.html
```

`annotation.json` requirements:

- component type
- x
- y
- width
- height
- font family
- font size
- font color

Priority order:

- P0: Real AI generation
- P1: Component detection
- P2: Annotation system
- P3: Transparent PNG slicing
- P4: 996 export

Sprint 8 can begin with P0 real AI generation while keeping the later detection, annotation, slicing, and export stages behind stable pipeline boundaries.

## Sprint 8A

Status: complete

Scope:

- Template-based component processing is available for `ui_preview` assets.
- `main_ui` currently generates six fixed proportional regions.
- The backend writes `manifest.json`, `annotation.json`, component PNGs, and `preview.html`.
- Component PNGs are recorded as `sliced_component` assets.
- Component assets use `source = component_processing`.
- Component assets inherit the source UI preview `generation_job_id`.
- Assets detail can trigger processing and display manifest, annotation, component count, and preview link.

Limitations:

- This is not intelligent visual recognition.
- Transparent background optimization is not implemented yet.
- The existing Mock Pipeline and Real Pipeline remain intact.
