import { render, screen } from "@testing-library/react";
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

const mainUiProductionResult = {
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
  confirmed_components_url:
    "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/confirmed_components/screen_main_ui.jpg",
  candidates: [
    {
      candidate_id: "skill_01",
      component_id: "skill_01",
      component_name: "技能按钮 1",
      component_type: "skill_button",
      number: 1,
      bounds: { x: 10, y: 20, width: 48, height: 48 },
      level: "A",
      production_category: "Atomic",
      recommended_action: "确认切图",
      confirmed: true,
      output_format: "png",
      output_name: "btn_skill_01.png",
      transparent_required: true,
      transparent_warning: "源图无透明像素，已输出 PNG 但需要人工抠透明背景",
      image_path: "confirmed_components/btn_skill_01.png",
    },
  ],
  confirmed_components: [
    {
      component_id: "skill_01",
      component_type: "skill_button",
      number: 1,
      confirmed: true,
      file: "confirmed_components/btn_skill_01.png",
      format: "png",
      transparent_warning: "源图无透明像素，已输出 PNG 但需要人工抠透明背景",
      url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/confirmed_components/btn_skill_01.png",
    },
  ],
  exported_count: 1,
} as const;

beforeAll(() => {
  global.URL.createObjectURL = jest.fn(() => "blob:reference-preview");
  global.URL.revokeObjectURL = jest.fn();
});

beforeEach(() => {
  jest.clearAllMocks();
  api.listProductionStyleCodes.mockResolvedValue({
    items: [
      {
        style_code: "STYLE_0003",
        style_name: "Sprint 16 Dark Gold Dragon Mobile",
        source_job_id: "job-main",
        device_type: "mobile_landscape",
      },
    ],
  });
  api.uploadAsset.mockResolvedValue({
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
  api.runMainUiProduction.mockResolvedValue(mainUiProductionResult);
  api.updateMainUiCandidate.mockResolvedValue({
    ...mainUiProductionResult.candidates[0],
    confirmed: false,
  });
  api.exportMainUiProduction.mockResolvedValue(mainUiProductionResult);
  api.generateProductionStudioPackage.mockResolvedValue({
    style_code: "STYLE_0003",
    device_type: "mobile_landscape",
    asset_mode: "resource_production",
    style_source: "existing_style",
    layout_template: "classic_legend_mobile",
    generation_mode: "auto_generate",
    reference_image_path: null,
    final_prompt: "手机横屏传奇手游界面，采用经典传奇手游固定布局",
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
        missing_semantic_icons: true,
        common_icons_note: "common_icons semantic naming still needs improvement; current slices are generic candidates.",
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

test("主界面生产区块可生成、确认候选并执行切图", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  expect(await screen.findByText("主界面生产")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "生成主界面实验包" }));

  expect(api.runMainUiProduction).toHaveBeenCalled();
  expect(await screen.findByAltText("主界面")).toHaveAttribute(
    "src",
    "http://127.0.0.1:8000/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/main_ui.jpg",
  );
  expect(screen.getByAltText("编号候选组件")).toBeInTheDocument();
  expect(screen.getByText("skill_01")).toBeInTheDocument();
  expect(screen.getByText("确认切图")).toBeInTheDocument();
  expect(screen.getByText("Atomic")).toBeInTheDocument();

  await user.click(screen.getByLabelText("确认切图 skill_01"));
  expect(api.updateMainUiCandidate).toHaveBeenCalledWith(
    "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui",
    "skill_01",
    false,
  );

  await user.click(screen.getByRole("button", { name: "执行确认切图" }));
  expect(api.exportMainUiProduction).toHaveBeenCalledWith(
    "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui",
  );
  expect(screen.getByText(/transparent_warning/)).toBeInTheDocument();
});

test("显示布局模板、中文字段和可编辑自动生成提示词", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  expect(await screen.findByText("生产工作台")).toBeInTheDocument();
  expect(screen.getByLabelText("设备类型")).toHaveDisplayValue("手机横屏");
  expect(screen.getByLabelText("输出模式")).toHaveDisplayValue("资源生产");
  expect(screen.getByLabelText("布局模板")).toHaveDisplayValue("经典传奇手游布局");
  expect((screen.getByLabelText("生成提示词") as HTMLTextAreaElement).value).toContain("左下摇杆区");
  expect((screen.getByLabelText("生成提示词") as HTMLTextAreaElement).value).toContain("右下环绕式技能操作区");

  await user.selectOptions(screen.getByLabelText("布局模板"), "legend_185_combo");
  await user.clear(screen.getByLabelText("生成提示词"));
  await user.type(screen.getByLabelText("生成提示词"), "保持固定布局，只替换暗金材质。");
  await user.click(screen.getByRole("button", { name: "开始生成" }));

  expect(api.generateProductionStudioPackage).toHaveBeenCalledWith(
    expect.objectContaining({
      layout_template: "legend_185_combo",
      generation_mode: "auto_generate",
      reference_image_path: null,
      prompt: "保持固定布局，只替换暗金材质。",
    }),
  );
});

test("支持参考图上传、缩略图、删除和参考生成提示词", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await screen.findByText("生产工作台");
  const file = new File(["fake"], "reference-main-ui.png", { type: "image/png" });
  await user.upload(screen.getByLabelText("参考图"), file);

  expect(api.uploadAsset).toHaveBeenCalledWith({
    file,
    project_id: null,
    asset_type: "reference_image",
    device_type: "mobile_landscape",
  });
  expect(await screen.findByAltText("参考图缩略图")).toHaveAttribute("src", "blob:reference-preview");
  expect((screen.getByLabelText("生成提示词") as HTMLTextAreaElement).value).toContain("参考上传的传奇手游界面截图");

  await user.click(screen.getByRole("button", { name: "开始生成" }));
  expect(api.generateProductionStudioPackage).toHaveBeenCalledWith(
    expect.objectContaining({
      generation_mode: "reference_guided",
      reference_image_path: "assets/uploads/reference-main-ui.png",
      prompt: expect.stringContaining("不要照抄原图素材"),
    }),
  );

  await user.click(screen.getByRole("button", { name: "删除参考图" }));
  expect(screen.queryByAltText("参考图缩略图")).not.toBeInTheDocument();
});

test("结果中心优先显示完整图预览、资源入口和验收记录", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await screen.findByText("生产工作台");
  await user.click(screen.getByLabelText("使用已有风格"));
  await user.click(screen.getByLabelText("背包界面"));
  await user.click(screen.getByLabelText("主界面"));
  await user.click(screen.getByRole("button", { name: "开始生成" }));

  expect(await screen.findByText("结果中心")).toBeInTheDocument();
  expect(screen.getByAltText("背包界面完整图预览")).toHaveAttribute(
    "src",
    "http://127.0.0.1:8000/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/ui_preview.png",
  );
  expect(screen.getByText("验证通过")).toBeInTheDocument();
  expect(screen.getByText("组件数量")).toBeInTheDocument();
  expect(screen.getByText("候选资源")).toBeInTheDocument();
  expect(screen.getByText("查看资源")).toBeInTheDocument();
  expect(screen.getByText("查看报告")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "放大查看背包界面完整图预览" }));
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  expect(screen.getByAltText("背包界面放大预览")).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText("人工验收状态"), "rejected");
  await user.type(screen.getByLabelText("验收记录"), "右下技能区需要更环绕。");

  expect(screen.getAllByText("验收拒绝").length).toBeGreaterThanOrEqual(1);
  expect(screen.getByDisplayValue("右下技能区需要更环绕。")).toBeInTheDocument();
});
