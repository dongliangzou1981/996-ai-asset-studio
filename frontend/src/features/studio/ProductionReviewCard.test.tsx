import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProductionStudio } from "./ProductionStudio";

const api = {
  generateProductionStudioPackage: jest.fn(),
  runMainUiProduction: jest.fn(),
  updateMainUiCandidate: jest.fn(),
  exportMainUiProduction: jest.fn(),
  getProductionStudioFileUrl: jest.fn((path: string) => `http://127.0.0.1:8000${path}`),
  listProductionStyleCodes: jest.fn(),
  updateProductionManualAcceptance: jest.fn(),
  uploadAsset: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
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

test("shows production review card and writes manual acceptance", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  const generateButton = await screen.findByRole("button", { name: "开始生成" });
  await user.click(generateButton);

  const card = await screen.findByText("Production Review Card");
  const section = card.closest("section") as HTMLElement;

  expect(within(section).getByText("Production Score")).toBeInTheDocument();
  expect(within(section).getByText("72")).toBeInTheDocument();
  expect(within(section).getByText("Ready Status")).toBeInTheDocument();
  expect(within(section).getAllByText("blocked").length).toBeGreaterThanOrEqual(1);
  expect(within(section).getByText("A/B/C")).toBeInTheDocument();
  expect(within(section).getByText("2 / 3 / 1")).toBeInTheDocument();
  expect(within(section).getByText("Screen/Panel/Atomic/Effect/Ignore")).toBeInTheDocument();
  expect(within(section).getByText("1 / 3 / 2 / 0 / 1")).toBeInTheDocument();
  expect(within(section).getByText("blockers")).toBeInTheDocument();
  expect(within(section).getByText("warnings")).toBeInTheDocument();
  expect(within(section).getByText("transparent_issues")).toBeInTheDocument();
  expect(within(section).getByText("manual_acceptance_status")).toBeInTheDocument();
  expect(within(section).getByText("View production_review.json")).toBeInTheDocument();
  expect(within(section).getByText("View component_review_analysis.json")).toBeInTheDocument();
  expect(within(section).getByText("View manual_acceptance.json")).toBeInTheDocument();
  expect(within(section).getByText("View production_review.html")).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText("人工验收状态"), "accepted");

  expect(api.updateProductionManualAcceptance).toHaveBeenCalledWith(
    "assets/uploads/996-ready/STYLE_0003/bag_ui/job-bag",
    expect.objectContaining({ review_status: "accepted" }),
  );
});
