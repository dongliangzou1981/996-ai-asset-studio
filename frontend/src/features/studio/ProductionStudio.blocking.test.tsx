import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProductionStudio } from "./ProductionStudio";

const project = {
  id: "project-996",
  name: "996 测试项目",
  description: "P996",
  status: "draft",
  created_at: "2026-06-08T00:00:00Z",
  updated_at: "2026-06-08T00:00:00Z",
};

const mainUiProductionResult = {
  package_dir: "assets/uploads/996-ready/SPRINT20N/main_ui/job-main-ui",
  main_ui_url: "/production-studio/files/996-ready/SPRINT20N/main_ui/job-main-ui/main_ui.jpg",
  candidate_preview_url: "",
  candidate_manifest_url: "",
  manifest_url: "/production-studio/files/996-ready/SPRINT20N/main_ui/job-main-ui/manifest.json",
  annotation_url: "/production-studio/files/996-ready/SPRINT20N/main_ui/job-main-ui/annotation.json",
  production_review_url: "/production-studio/files/996-ready/SPRINT20N/main_ui/job-main-ui/production_review.json",
  manual_acceptance_url: "/production-studio/files/996-ready/SPRINT20N/main_ui/job-main-ui/manual_acceptance.json",
  confirmed_components_url:
    "/production-studio/files/996-ready/SPRINT20N/main_ui/job-main-ui/confirmed_components/screen_main_ui.jpg",
  candidates: [],
  confirmed_components: [],
  package_files: [],
  candidate_options: [],
  selected_candidate_id: "candidate_1",
  style_reference_strength: "none",
  style_reference_note: "",
  project_context: {
    project_name: "996 测试项目",
    screen_type: "main_ui",
    style_package_name: "none",
    style_notes: "",
    reference_status: "none",
  },
  training_samples_url:
    "/production-studio/files/996-ready/SPRINT20N/main_ui/job-main-ui/training_samples/main_ui/candidate_samples.json",
  exported_count: 0,
};

const markingAcceptanceResult = {
  project_code: "MARKING_TEST",
  candidate_id: "candidate_1",
  total_marks: 5,
  by_type: { background: 1, panel: 1, button: 1, icon: 1, skill: 1 },
  slice_success: 5,
  slice_failed: 0,
  missing_required: [],
  warnings: [],
  project: { ...project, id: "project-marking", name: "标记验收测试", description: "MARKING_TEST" },
  candidate_preview_url: "/production-studio/files/996-ready/SPRINT20N/main_ui/job-main-ui/candidate_preview.jpg",
  candidate_preview_path: "harness/examples/main_ui/marking_test/candidate_preview.png",
  manifest_path: "harness/examples/main_ui/marking_test/manifest.json",
  marking_json_path: "harness/examples/main_ui/marking_test/marking.json",
  manual_acceptance_path: "harness/examples/main_ui/marking_test/manual_acceptance.json",
  training_samples_path: "training_samples/main_ui/candidate_samples.json",
  harness_dir: "harness/examples/main_ui/marking_test",
  report_path: "harness/examples/main_ui/marking_test/marking_acceptance_report.json",
  production: mainUiProductionResult,
};

function makeApi() {
  return {
    generateProductionStudioPackage: jest.fn(),
    generateUiProductionPackage: jest.fn().mockResolvedValue(mainUiProductionResult),
    markUiProductionCandidates: jest.fn(),
    selectUiProductionCandidate: jest.fn(),
    updateUiProductionCandidate: jest.fn(),
    exportUiProductionComponents: jest.fn(),
    runOpenCvUiSlicer: jest.fn(),
    runMarkingAcceptanceTest: jest.fn().mockResolvedValue(markingAcceptanceResult),
    runMainUiProduction: jest.fn(),
    getMainUiProduction: jest.fn().mockRejectedValue(new Error("no saved package")),
    updateMainUiCandidate: jest.fn(),
    exportMainUiProduction: jest.fn(),
    getProductionStudioFileUrl: jest.fn((path: string) => `http://127.0.0.1:8000${path}`),
    listProjects: jest.fn().mockResolvedValue({ items: [project] }),
    createProject: jest.fn().mockResolvedValue(project),
    listProductionStyleCodes: jest.fn().mockResolvedValue({ items: [] }),
    getPromptSampleSuggestion: jest.fn().mockResolvedValue({ found: false }),
    updateProductionManualAcceptance: jest.fn(),
    uploadAsset: jest.fn().mockResolvedValue({
      id: "asset-reference",
      project_id: null,
      asset_type: "reference_image",
      device_type: "mobile_landscape",
      width: 1536,
      height: 864,
      file_path: "assets/uploads/reference-main-ui.png",
      original_filename: "reference-main-ui.png",
      metadata_json: "{}",
      source: "uploaded",
      generation_job_id: null,
      thumbnail_path: "",
      created_at: "",
      updated_at: "",
    }),
    importLayerPackage: jest.fn(),
  };
}

beforeAll(() => {
  global.URL.createObjectURL = jest.fn(() => "blob:reference-preview");
  global.URL.revokeObjectURL = jest.fn();
});

test("marking acceptance mode still opens when project APIs fail", async () => {
  const api = makeApi();
  api.listProjects.mockRejectedValue(
    new Error("请求失败：http://127.0.0.1:8000/projects，status=network_error，error=Failed to fetch"),
  );
  api.createProject.mockRejectedValue(
    new Error("请求失败：http://127.0.0.1:8000/projects，status=500，error=project unavailable"),
  );
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await user.click(await screen.findByRole("button", { name: "进入标记验收测试" }));

  expect(await screen.findByText("已进入标记验收测试：参数已自动填充，请点击一键生成并标记测试。")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "一键生成并标记测试" })).toBeInTheDocument();
});

test("reference upload failure keeps generation blocked and shows request details", async () => {
  const api = makeApi();
  api.uploadAsset.mockRejectedValueOnce(
    new Error("请求失败：http://127.0.0.1:8000/assets/upload，status=network_error，error=Failed to fetch"),
  );
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await user.selectOptions(await screen.findByLabelText("生成模式"), "reference");
  const file = new File(["fake"], "reference-main-ui.png", { type: "image/png" });
  await user.upload(screen.getByLabelText("2. 上传参考图"), file);

  expect(await screen.findByText(/参考图上传失败：请求失败：http:\/\/127\.0\.0\.1:8000\/assets\/upload/)).toBeInTheDocument();
  expect(screen.queryByAltText("UI素材生产参考图预览")).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "生成界面" }));
  expect(api.generateUiProductionPackage).not.toHaveBeenCalled();
});

test("generation failures expose request URL status and backend error", async () => {
  const api = makeApi();
  api.generateUiProductionPackage.mockRejectedValueOnce(
    new Error("请求失败：http://127.0.0.1:8000/production-studio/ui-production/generate，status=500，error=mock failed"),
  );
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await user.click(await screen.findByRole("button", { name: "生成界面" }));

  expect(
    await screen.findByText(/请求失败：http:\/\/127\.0\.0\.1:8000\/production-studio\/ui-production\/generate/),
  ).toBeInTheDocument();
  expect(screen.getByText(/status=500/)).toBeInTheDocument();
  expect(screen.getByText(/error=mock failed/)).toBeInTheDocument();
});

test("reference ratio generation sends reference image and influence percent", async () => {
  const api = makeApi();
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await user.selectOptions(await screen.findByLabelText("生成模式"), "reference_ratio");
  const file = new File(["fake"], "reference-main-ui.png", { type: "image/png" });
  await user.upload(screen.getByLabelText("2. 上传参考图"), file);
  await user.clear(screen.getByLabelText("参考图影响比例数值"));
  await user.type(screen.getByLabelText("参考图影响比例数值"), "65");
  await user.click(screen.getByRole("button", { name: "生成界面" }));

  expect(api.generateUiProductionPackage).toHaveBeenCalledWith(
    expect.objectContaining({
      reference_image_path: "assets/uploads/reference-main-ui.png",
      reference_image: "assets/uploads/reference-main-ui.png",
      style_reference_strength: "65",
      reference_influence_percent: 65,
    }),
  );
});

test("adjustment screenshot upload failure clears bound path before generation", async () => {
  const api = makeApi();
  api.uploadAsset
    .mockResolvedValueOnce({
      id: "asset-adjustment-ok",
      project_id: null,
      asset_type: "reference_image",
      device_type: "mobile_landscape",
      width: 300,
      height: 200,
      file_path: "assets/uploads/adjustment-ok.png",
      original_filename: "adjustment-ok.png",
      metadata_json: "{}",
      source: "uploaded",
      generation_job_id: null,
      thumbnail_path: "",
      created_at: "",
      updated_at: "",
    })
    .mockRejectedValueOnce(
      new Error("请求失败：http://127.0.0.1:8000/assets/upload，status=500，error=upload failed"),
    );
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  const adjustmentInput = await screen.findByLabelText("上传调整截图");
  await user.upload(adjustmentInput, new File(["ok"], "adjustment-ok.png", { type: "image/png" }));
  await user.upload(screen.getByLabelText("上传调整截图"), new File(["bad"], "adjustment-bad.jpg", { type: "image/jpeg" }));

  expect(await screen.findByText(/调整截图上传失败：请求失败：http:\/\/127\.0\.0\.1:8000\/assets\/upload/)).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "生成界面" }));
  expect(api.generateUiProductionPackage).toHaveBeenCalledWith(
    expect.objectContaining({
      adjustment_image_path: null,
    }),
  );
});
