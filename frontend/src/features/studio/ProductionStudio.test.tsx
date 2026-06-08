import { render, screen, waitFor, within } from "@testing-library/react";
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

const mainUiProductionResult = {
  package_dir: "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui",
  main_ui_url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/main_ui.jpg",
  candidate_preview_url:
    "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_preview.jpg",
  candidate_manifest_url:
    "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_manifest.json",
  manifest_url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/manifest.json",
  annotation_url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/annotation.json",
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
      bbox: { x: 10, y: 20, width: 48, height: 48 },
      outline_points: [
        { x: 10, y: 20 },
        { x: 58, y: 20 },
        { x: 58, y: 68 },
        { x: 10, y: 68 },
      ],
      layout_zone: "right_skill",
      shape_type: "circle",
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
      transparent_required: true,
      has_transparent_pixels: false,
      transparent_warning: "源图无透明像素，已输出 PNG 但需要人工抠透明背景",
      url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/confirmed_components/btn_skill_01.png",
    },
  ],
  package_files: [
    {
      label: "main_ui.jpg",
      file: "main_ui.jpg",
      exists: true,
      url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/main_ui.jpg",
    },
    {
      label: "candidate_preview.jpg",
      file: "candidate_preview.jpg",
      exists: true,
      url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_preview.jpg",
    },
    {
      label: "confirmed_components/",
      file: "confirmed_components/",
      exists: true,
      url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/confirmed_components/screen_main_ui.jpg",
    },
  ],
  candidate_options: [
    {
      candidate_id: "candidate_1",
      label: "候选 1：原始参考布局",
      file: "candidate_options/candidate_1.jpg",
      selected: true,
      url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_options/candidate_1.jpg",
    },
    {
      candidate_id: "candidate_2",
      label: "候选 2：增强对比度",
      file: "candidate_options/candidate_2.jpg",
      selected: false,
      url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_options/candidate_2.jpg",
    },
    {
      candidate_id: "candidate_3",
      label: "候选 3：增强边缘清晰度",
      file: "candidate_options/candidate_3.jpg",
      selected: false,
      url: "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_options/candidate_3.jpg",
    },
  ],
  selected_candidate_id: "candidate_1",
  style_reference_strength: "60",
  style_reference_note: "60%参考：已写入提示词，效果取决模型",
  project_context: {
    project_name: "996 UI Asset Studio",
    screen_type: "main_ui",
    style_package_name: "60",
    style_notes: "60%参考：已写入提示词，效果取决模型",
    reference_status: "已上传/已读取",
  },
  training_samples_url:
    "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/training_samples/main_ui/candidate_samples.json",
  exported_count: 1,
} as const;

const markingAcceptanceResult = {
  project_code: "MARKING_TEST",
  candidate_id: "candidate_1",
  total_marks: 8,
  by_type: {
    background: 1,
    panel: 3,
    button: 3,
    icon: 1,
    skill: 2,
  },
  slice_success: 6,
  slice_failed: 0,
  missing_required: [],
  warnings: [],
  project: {
    id: "project-marking",
    name: "标记验收测试",
    description: "MARKING_TEST",
    status: "draft",
    created_at: "2026-06-08T00:00:00Z",
    updated_at: "2026-06-08T00:00:00Z",
  },
  candidate_preview_url:
    "/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_preview.jpg",
  candidate_preview_path: "harness/examples/main_ui/marking_test/candidate_preview.png",
  manifest_path: "harness/examples/main_ui/marking_test/manifest.json",
  marking_json_path: "harness/examples/main_ui/marking_test/marking.json",
  manual_acceptance_path: "harness/examples/main_ui/marking_test/manual_acceptance.json",
  training_samples_path:
    "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/training_samples/main_ui/candidate_samples.json",
  harness_dir: "harness/examples/main_ui/marking_test",
  report_path: "harness/examples/main_ui/marking_test/marking_acceptance_report.json",
  production: mainUiProductionResult,
} as const;

beforeAll(() => {
  global.URL.createObjectURL = jest.fn(() => "blob:reference-preview");
  global.URL.revokeObjectURL = jest.fn();
});

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
  api.getPromptSampleSuggestion.mockResolvedValue({ found: false });
  api.runMainUiProduction.mockResolvedValue(mainUiProductionResult);
  api.getMainUiProduction.mockRejectedValue(new Error("no saved package"));
  api.generateUiProductionPackage.mockResolvedValue({
    ...mainUiProductionResult,
    candidate_preview_url: "",
    candidate_manifest_url: "",
    candidates: [],
    confirmed_components: [],
  });
  api.markUiProductionCandidates.mockResolvedValue({
    ...mainUiProductionResult,
    confirmed_components: [],
  });
  api.updateUiProductionCandidate.mockResolvedValue({
    ...mainUiProductionResult.candidates[0],
    confirmed: false,
  });
  api.selectUiProductionCandidate.mockResolvedValue({
    ...mainUiProductionResult,
    selected_candidate_id: "candidate_2",
    candidate_preview_url: "",
    candidate_manifest_url: "",
    candidates: [],
    confirmed_components: [],
    candidate_options: mainUiProductionResult.candidate_options.map((item) => ({
      ...item,
      selected: item.candidate_id === "candidate_2",
    })),
  });
  api.exportUiProductionComponents.mockResolvedValue(mainUiProductionResult);
  api.runMarkingAcceptanceTest.mockResolvedValue(markingAcceptanceResult);
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

test("UI素材生产流程可生成、标记、确认、切图并预览输出", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  expect(await screen.findByText("UI素材生产")).toBeInTheDocument();
  expect(screen.getByText("项目列表")).toBeInTheDocument();
  expect(screen.getByLabelText("1. 选择界面类型")).toHaveDisplayValue("主界面");
  expect(screen.getByLabelText("生成模式")).toHaveDisplayValue("普通生成");
  expect(screen.queryByLabelText("2. 上传参考图")).not.toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText("生成模式"), "reference_ratio");
  expect(screen.getByLabelText("生成模式")).toHaveDisplayValue("参考图生成（按比例）");
  expect(screen.getByLabelText("参考图影响比例")).toHaveValue("40");

  const file = new File(["fake"], "reference-main-ui.png", { type: "image/png" });
  await user.upload(screen.getByLabelText("2. 上传参考图"), file);

  expect(api.uploadAsset).toHaveBeenCalledWith({
    file,
    project_id: null,
    asset_type: "reference_image",
    device_type: "mobile_landscape",
  });
  expect(await screen.findByAltText("UI素材生产参考图预览")).toHaveAttribute("src", "blob:reference-preview");

  const generatedPrompt = screen.getByLabelText("系统生成提示词") as HTMLTextAreaElement;
  await waitFor(() => {
    expect(generatedPrompt.value).toContain("手机横屏传奇手游主界面");
    expect(generatedPrompt.value).toContain("参考图影响比例为 40%");
    expect(generatedPrompt.value).toContain("固定布局骨架必须保持");
  });
  await user.clear(generatedPrompt);
  await user.type(generatedPrompt, "主界面布局清晰，技能区和地图区优先。");
  await user.click(screen.getByRole("button", { name: "生成界面" }));

  expect(api.generateUiProductionPackage).toHaveBeenCalledWith(
    expect.objectContaining({
      screen_type: "main_ui",
      reference_image_path: "assets/uploads/reference-main-ui.png",
      system_prompt: expect.stringContaining("手机横屏传奇手游主界面"),
      requirement: "主界面布局清晰，技能区和地图区优先。",
      style_reference_strength: "40",
      project_id: "project-996",
      device_type: "mobile_landscape",
      layout_template: "classic_legend_mobile",
      adjustment_note: "",
      adjustment_image_path: null,
    }),
  );
  expect(await screen.findByAltText("完整界面预览")).toHaveAttribute(
    "src",
    "http://127.0.0.1:8000/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/main_ui.jpg",
  );
  expect(screen.getByText("候选方案")).toBeInTheDocument();
  expect(screen.getByText("候选 2：增强对比度")).toBeInTheDocument();
  await user.click(screen.getAllByRole("button", { name: "选择此方案" })[0]);
  expect(api.selectUiProductionCandidate).toHaveBeenCalledWith(
    "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui",
    "candidate_2",
  );

  await user.click(screen.getByRole("button", { name: "标记候选组件" }));
  expect(api.markUiProductionCandidates).toHaveBeenCalledWith(
    "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui",
  );
  expect(await screen.findByAltText("候选组件编号图")).toBeInTheDocument();
  expect(screen.getByText("skill_01")).toBeInTheDocument();
  expect(screen.getAllByText("确认切图").length).toBeGreaterThanOrEqual(1);
  expect(screen.getByText("Atomic")).toBeInTheDocument();
  expect(screen.getByText("right_skill")).toBeInTheDocument();
  expect(screen.getByText("circle")).toBeInTheDocument();

  await user.click(screen.getAllByLabelText("确认切图 skill_01")[0]);
  expect(api.updateUiProductionCandidate).toHaveBeenCalledWith(
    "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui",
    "skill_01",
    false,
  );

  await user.click(screen.getByRole("button", { name: "执行切图" }));
  expect(api.exportUiProductionComponents).toHaveBeenCalledWith(
    "assets/uploads/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui",
  );
  expect(screen.getByAltText("skill_01 输出预览")).toBeInTheDocument();
  expect(screen.getByText(/透明警告/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "导出 996-ready" })).toBeInTheDocument();
  expect(screen.getByText("996-ready 包清单")).toBeInTheDocument();
  expect(screen.getByText("main_ui.jpg")).toBeInTheDocument();
  expect(screen.getByText("confirmed_components/")).toBeInTheDocument();
  expect(screen.getByText("查看输出包 manifest.json")).toBeInTheDocument();
  expect(screen.getByText("查看 training_samples")).toBeInTheDocument();
});

test("项目栏和生产工作台只显示 Sprint20G 要求的基础信息", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  expect(await screen.findByText("项目列表")).toBeInTheDocument();
  expect((await screen.findAllByText("996 主界面")).length).toBeGreaterThanOrEqual(1);
  expect((await screen.findAllByText("P996")).length).toBeGreaterThanOrEqual(1);
  expect(screen.getByRole("button", { name: "新建项目" })).toBeInTheDocument();

  const workbench = screen.getByText("生产工作台").closest("section") as HTMLElement;
  expect(within(workbench).getByText("选择当前项目的生产方向，后续素材任务将在结果中心执行")).toBeInTheDocument();
  expect(within(workbench).getByLabelText("设备类型")).toHaveDisplayValue("手机横屏");
  expect(within(workbench).getByLabelText("输出模式")).toHaveDisplayValue("资源生产");
  expect(within(workbench).getByLabelText("布局模板")).toHaveDisplayValue("经典传奇手游布局");
  expect(within(workbench).queryByText("生成模式")).not.toBeInTheDocument();
  expect(within(workbench).queryByText("风格来源")).not.toBeInTheDocument();
  expect(within(workbench).queryByText("界面类型")).not.toBeInTheDocument();
  expect(within(workbench).queryByText("参考图")).not.toBeInTheDocument();
  expect(within(workbench).queryByText("生成提示词")).not.toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "新建项目" }));
  await user.type(screen.getByLabelText("项目名称"), "新项目");
  await user.type(screen.getByLabelText("项目代号"), "NEW001");
  await user.click(screen.getByRole("button", { name: "保存项目" }));

  expect(api.createProject).toHaveBeenCalledWith({
    name: "新项目",
    description: "NEW001",
    status: "draft",
  });
  expect((await screen.findAllByText("新项目")).length).toBeGreaterThanOrEqual(1);
  expect(screen.getAllByText("NEW001").length).toBeGreaterThanOrEqual(1);
});

test("风格编号加载失败只显示 warning，不阻断新建项目", async () => {
  api.listProductionStyleCodes.mockRejectedValueOnce(new Error("style unavailable"));
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  expect(await screen.findByText("风格编号暂时不可用，不影响项目创建、普通生成、参考图生成和标记验收测试。")).toBeInTheDocument();
  expect(screen.queryByText(/启动工作台\.ps1/)).not.toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "新建项目" }));
  await user.type(screen.getByLabelText("项目名称"), "无风格项目");
  await user.type(screen.getByLabelText("项目代号"), "NO_STYLE");
  await user.click(screen.getByRole("button", { name: "保存项目" }));

  expect(api.createProject).toHaveBeenCalledWith({
    name: "无风格项目",
    description: "NO_STYLE",
    status: "draft",
  });
  expect((await screen.findAllByText("无风格项目")).length).toBeGreaterThanOrEqual(1);
  expect(screen.getAllByText("NO_STYLE").length).toBeGreaterThanOrEqual(1);
});

test("普通生成不显示参考图控件，生成请求不依赖参考图", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await screen.findByText("UI素材生产");
  expect(screen.getByLabelText("生成模式")).toHaveDisplayValue("普通生成");
  expect(screen.queryByLabelText("2. 上传参考图")).not.toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "生成界面" }));

  expect(api.generateUiProductionPackage).toHaveBeenCalledWith(
    expect.objectContaining({
      screen_type: "main_ui",
      reference_image_path: null,
      style_reference_strength: "none",
      project_id: "project-996",
      device_type: "mobile_landscape",
      layout_template: "classic_legend_mobile",
    }),
  );
});

test("生产工作台基础选项可调整，素材生产区保留参考图和调整说明", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await screen.findByText("生产工作台");
  await user.selectOptions(screen.getByLabelText("布局模板"), "legend_185_combo");
  expect(screen.getByLabelText("布局模板")).toHaveDisplayValue("1.85合击版");
  await user.selectOptions(screen.getByLabelText("生成模式"), "reference");
  expect(screen.getByLabelText("2. 上传参考图")).toBeInTheDocument();
  expect(screen.queryByLabelText("参考图影响比例")).not.toBeInTheDocument();

  const file = new File(["fake"], "reference-main-ui.png", { type: "image/png" });
  await user.upload(screen.getByLabelText("2. 上传参考图"), file);

  expect(api.uploadAsset).toHaveBeenCalledWith({
    file,
    project_id: null,
    asset_type: "reference_image",
    device_type: "mobile_landscape",
  });
  expect(await screen.findByAltText("UI素材生产参考图预览")).toHaveAttribute("src", "blob:reference-preview");
  await user.type(screen.getByLabelText("调整说明"), "技能按钮更贴边。");
  expect(screen.getByDisplayValue("技能按钮更贴边。")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "移除参考图" }));
  expect(screen.queryByAltText("UI素材生产参考图预览")).not.toBeInTheDocument();
});

test("参考图影响比例会写入提示词，且调整截图上传错误显示在正确位置", async () => {
  const user = userEvent.setup({ applyAccept: false });
  render(<ProductionStudio api={api} />);

  await screen.findByText("UI素材生产");
  await waitFor(() => {
    const promptField = screen.getByLabelText("系统生成提示词") as HTMLTextAreaElement;
    expect(promptField.value).toContain("普通生成");
    expect(promptField.value).toContain("本次普通生成不使用参考图");
  });
  expect(screen.queryByLabelText("2. 上传参考图")).not.toBeInTheDocument();
  await user.selectOptions(screen.getByLabelText("生成模式"), "reference");
  expect(screen.getByLabelText("2. 上传参考图")).toBeInTheDocument();
  expect(screen.queryByLabelText("参考图影响比例")).not.toBeInTheDocument();
  await user.selectOptions(screen.getByLabelText("生成模式"), "reference_ratio");

  await user.clear(screen.getByLabelText("参考图影响比例数值"));
  await user.type(screen.getByLabelText("参考图影响比例数值"), "65");
  await waitFor(() => {
    const promptField = screen.getByLabelText("系统生成提示词") as HTMLTextAreaElement;
    expect(promptField.value).toContain("参考图影响比例为 65%");
  });
  expect((screen.getByLabelText("系统生成提示词") as HTMLTextAreaElement).value).toContain("不改变固定布局骨架");

  const adjustmentInput = screen.getByLabelText("上传调整截图");
  const pngFile = new File(["fake"], "adjustment.png", { type: "" });
  await user.upload(adjustmentInput, pngFile);
  expect(api.uploadAsset).toHaveBeenCalledWith({
    file: pngFile,
    project_id: null,
    asset_type: "reference_image",
    device_type: "mobile_landscape",
  });
  expect(screen.queryByText("调整截图上传失败，请使用 PNG、JPG 或 JPEG。")).not.toBeInTheDocument();

  api.uploadAsset.mockClear();
  const jpgFile = new File(["fake"], "adjustment.jpg", { type: "image/jpeg" });
  await user.upload(screen.getByLabelText("上传调整截图"), jpgFile);
  expect(api.uploadAsset).toHaveBeenCalledWith({
    file: jpgFile,
    project_id: null,
    asset_type: "reference_image",
    device_type: "mobile_landscape",
  });

  api.uploadAsset.mockClear();
  const jpegFile = new File(["fake"], "adjustment.jpeg", { type: "" });
  await user.upload(screen.getByLabelText("上传调整截图"), jpegFile);
  expect(api.uploadAsset).toHaveBeenCalledWith({
    file: jpegFile,
    project_id: null,
    asset_type: "reference_image",
    device_type: "mobile_landscape",
  });

  api.uploadAsset.mockClear();
  const invalidFile = new File(["fake"], "adjustment.txt", { type: "text/plain" });
  await user.upload(screen.getByLabelText("上传调整截图"), invalidFile);
  expect(api.uploadAsset).not.toHaveBeenCalled();
  const adjustmentBlock = screen.getByText("上传调整截图").closest("div") as HTMLElement;
  const workbench = screen.getByText("生产工作台").closest("section") as HTMLElement;
  expect(within(adjustmentBlock).getByText("调整截图上传失败，请使用 PNG、JPG 或 JPEG。")).toBeInTheDocument();
  expect(within(workbench).queryByText("调整截图上传失败，请使用 PNG、JPG 或 JPEG。")).not.toBeInTheDocument();
});

test("标记验收测试模式可自动填充并展示验收结果", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  expect(await screen.findByText("验收测试模式")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "进入标记验收测试" }));

  expect(api.createProject).toHaveBeenCalledWith({
    name: "标记验收测试",
    description: "MARKING_TEST",
    status: "draft",
  });
  expect(await screen.findByText("当前模式：标记验收测试 / MARKING_TEST")).toBeInTheDocument();
  const promptField = screen.getByLabelText("系统生成提示词") as HTMLTextAreaElement;
  expect(promptField.value).toContain("手机横屏传奇手游主界面");
  expect(promptField.value).toContain("右下技能操作区");
  expect(promptField.value).toContain("主技能按钮固定右下角偏内侧");
  expect(promptField.value).toContain("普通生成");
  expect(promptField.value).toContain("不使用参考图");
  expect(screen.getByDisplayValue("用于测试自动标记和自动切图准确性")).toBeInTheDocument();
  await user.clear(promptField);
  await user.type(promptField, "编辑后的验收提示词：技能区需要半圆布局。");

  await user.click(screen.getByRole("button", { name: "一键生成并标记测试" }));

  expect(api.runMarkingAcceptanceTest).toHaveBeenCalledWith(
    expect.objectContaining({
      reference_image_path: null,
      system_prompt: expect.stringContaining("手机横屏传奇手游主界面"),
      requirement: "编辑后的验收提示词：技能区需要半圆布局。",
      project_id: "project-marking",
      device_type: "mobile_landscape",
      layout_template: "classic_legend_mobile",
      style_reference_strength: "none",
      adjustment_note: "用于测试自动标记和自动切图准确性",
    }),
  );
  expect(await screen.findByText("标记验收结果")).toBeInTheDocument();
  expect(screen.getByAltText("标记验收 candidate_preview")).toHaveAttribute(
    "src",
    "http://127.0.0.1:8000/production-studio/files/996-ready/SPRINT20B_MAIN_UI/main_ui/job-main-ui/candidate_preview.jpg",
  );
  expect(screen.getByText("标记组件总数")).toBeInTheDocument();
  expect(screen.getByText("背景数量")).toBeInTheDocument();
  expect(screen.getByText("面板数量")).toBeInTheDocument();
  expect(screen.getByText("按钮数量")).toBeInTheDocument();
  expect(screen.getByText("图标数量")).toBeInTheDocument();
  expect(screen.getByText("技能数量")).toBeInTheDocument();
  expect(screen.getByText("切图成功数量")).toBeInTheDocument();
  expect(screen.getByText("切图失败数量")).toBeInTheDocument();
  expect(screen.getByText("harness/examples/main_ui/marking_test/manifest.json")).toBeInTheDocument();
  expect(screen.getByText("harness/examples/main_ui/marking_test/marking.json")).toBeInTheDocument();
  expect(screen.getByText("harness/examples/main_ui/marking_test/manual_acceptance.json")).toBeInTheDocument();
  expect(screen.getByText("harness/examples/main_ui/marking_test/marking_acceptance_report.json")).toBeInTheDocument();
  expect(screen.getByText(/training_samples\/main_ui\/candidate_samples\.json/)).toBeInTheDocument();
});

test("系统生成提示词优先读取同类 high_quality prompt", async () => {
  api.getPromptSampleSuggestion.mockResolvedValue({
    found: true,
    sample_id: "sample-high-quality",
    final_prompt: "历史高质量主界面提示词：技能半圆布局清晰，按钮和面板独立。",
    quality: "high_quality",
  });
  render(<ProductionStudio api={api} />);

  expect(await screen.findByText("系统生成提示词")).toBeInTheDocument();
  await waitFor(() => {
    const promptField = screen.getByLabelText("系统生成提示词") as HTMLTextAreaElement;
    expect(promptField.value).toContain("历史高质量提示词参考");
    expect(promptField.value).toContain("历史高质量主界面提示词");
  });
});
