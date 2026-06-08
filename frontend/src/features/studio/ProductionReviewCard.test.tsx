import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProductionStudio } from "./ProductionStudio";

const api = {
  generateProductionStudioPackage: jest.fn(),
  generateUiProductionPackage: jest.fn(),
  markUiProductionCandidates: jest.fn(),
  selectUiProductionCandidate: jest.fn(),
  updateUiProductionCandidate: jest.fn(),
  exportUiProductionComponents: jest.fn(),
  runMarkingAcceptanceTest: jest.fn(),
  runMainUiProduction: jest.fn(),
  getMainUiProduction: jest.fn(),
  updateMainUiCandidate: jest.fn(),
  exportMainUiProduction: jest.fn(),
  getProductionStudioFileUrl: jest.fn((path: string) => `http://127.0.0.1:8000${path}`),
  listProjects: jest.fn(),
  createProject: jest.fn(),
  listProductionStyleCodes: jest.fn(),
  getPromptSampleSuggestion: jest.fn(),
  updateProductionManualAcceptance: jest.fn(),
  uploadAsset: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
  api.listProjects.mockResolvedValue({
    items: [
      {
        id: "project-996",
        name: "996 主界面",
        description: "P996",
        status: "draft",
        created_at: "2026-06-08T00:00:00Z",
        updated_at: "2026-06-08T00:00:00Z",
      },
    ],
  });
  api.createProject.mockImplementation(async (payload) => ({
    id: payload.description === "MARKING_TEST" ? "project-marking" : "project-new",
    name: payload.name,
    description: payload.description,
    status: "draft",
    created_at: "2026-06-08T00:00:00Z",
    updated_at: "2026-06-08T00:00:00Z",
  }));
  api.listProductionStyleCodes.mockResolvedValue({
    items: [
      {
        style_code: "STYLE_0003",
        style_name: "Dark Gold",
        source_job_id: "job-main",
        device_type: "mobile_landscape",
      },
    ],
  });
  api.updateProductionManualAcceptance.mockResolvedValue({
    review_status: "accepted",
    reviewer: "",
    remarks: "",
    updated_at: "2026-06-07T00:00:00Z",
    accepted_at: "2026-06-07T00:00:00Z",
    accepted_by: "",
    components: [],
  });
  api.getPromptSampleSuggestion.mockResolvedValue({ found: false });
  api.runMainUiProduction.mockResolvedValue({
    package_dir: "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui",
    main_ui_url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/main_ui.jpg",
    candidate_preview_url:
      "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_preview.jpg",
    candidate_manifest_url:
      "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_manifest.json",
    production_review_url:
      "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/production_review.json",
    manual_acceptance_url:
      "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/manual_acceptance.json",
    confirmed_components_url: "",
    candidates: [],
    confirmed_components: [],
  });
  api.getMainUiProduction.mockRejectedValue(new Error("no saved package"));
  api.generateUiProductionPackage.mockResolvedValue({
    package_dir: "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui",
    main_ui_url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/main_ui.jpg",
    candidate_preview_url: "",
    candidate_manifest_url: "",
    manifest_url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/manifest.json",
    annotation_url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/annotation.json",
    production_review_url:
      "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/production_review.json",
    manual_acceptance_url:
      "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/manual_acceptance.json",
    confirmed_components_url: "",
    candidates: [],
    confirmed_components: [],
  });
  api.markUiProductionCandidates.mockResolvedValue(api.runMainUiProduction.getMockImplementation()?.() ?? {});
  api.updateUiProductionCandidate.mockResolvedValue({});
  api.exportUiProductionComponents.mockResolvedValue(api.runMainUiProduction.getMockImplementation()?.() ?? {});
  api.updateMainUiCandidate.mockResolvedValue({});
  api.exportMainUiProduction.mockResolvedValue({
    package_dir: "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui",
    main_ui_url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/main_ui.jpg",
    candidate_preview_url:
      "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_preview.jpg",
    candidate_manifest_url:
      "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_manifest.json",
    production_review_url:
      "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/production_review.json",
    manual_acceptance_url:
      "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/manual_acceptance.json",
    confirmed_components_url: "",
    candidates: [],
    confirmed_components: [],
  });
  api.generateProductionStudioPackage.mockResolvedValue({
    style_code: "STYLE_0003",
    device_type: "mobile_landscape",
    asset_mode: "resource_production",
    style_source: "existing_style",
    layout_template: "classic_legend_mobile",
    generation_mode: "auto_generate",
    reference_image_path: null,
    final_prompt: "Generate production UI",
    results: [
      {
        screen_type: "bag_ui",
        generation_job_id: "job-bag",
        status: "completed",
        package_dir: "assets/uploads/996-ready/STYLE_0003/bag_ui/job-bag",
        ui_preview_url: "/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/ui_preview.png",
        delivery_report_url: "/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/delivery_report.html",
        candidate_preview_url: "/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/candidate_preview.html",
        component_quality_report_url:
          "/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/component_quality_report.html",
        components_count: 6,
        candidates_count: 6,
        validator_ok: true,
        missing_semantic_icons: false,
        common_icons_note: "ok",
        production_review: {
          production_score: 72,
          production_ready: false,
          level_a_count: 2,
          level_b_count: 3,
          level_c_count: 1,
          screen_count: 1,
          panel_count: 3,
          atomic_count: 2,
          effect_count: 0,
          ignore_count: 1,
          blockers: ["primary_action_button: required transparent PNG is fully opaque"],
          warnings: ["Optional package file missing: delivery_report.json"],
          transparent_issues: 1,
        },
        manual_acceptance_status: "pending",
        production_review_url: "/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/production_review.json",
        component_review_url:
          "/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/component_review_analysis.json",
        manual_acceptance_url: "/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/manual_acceptance.json",
        production_review_html_url:
          "/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/production_review.html",
        production_review_warning: "",
      },
    ],
  });
});

test("shows material production result links after generating the interface", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  const generateButton = await screen.findByRole("button", { name: "生成界面" });
  await user.click(generateButton);

  const resultCenter = await screen.findByText("结果中心 / 素材生产");
  const section = resultCenter.closest("div") as HTMLElement;

  expect(within(section).getByAltText("完整界面预览")).toBeInTheDocument();
  expect(within(section).getByText("查看输出包 manifest.json")).toBeInTheDocument();
  expect(within(section).getByText("查看 manual_acceptance.json")).toBeInTheDocument();
  expect(within(section).queryByText("Production Review Card")).not.toBeInTheDocument();
  expect(api.updateProductionManualAcceptance).not.toHaveBeenCalled();
});
