import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProductionStudio } from "./ProductionStudio";

const api = {
  generateProductionStudioPackage: jest.fn(),
  getProductionStudioFileUrl: jest.fn((path: string) => `http://127.0.0.1:8000${path}`),
  listProductionStyleCodes: jest.fn(),
  uploadAsset: jest.fn(),
};

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
      },
    ],
  });
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

  await user.selectOptions(screen.getByLabelText("人工验收状态"), "needs_change");
  await user.type(screen.getByLabelText("验收记录"), "右下技能区需要更环绕。");

  expect(screen.getAllByText("需要修改").length).toBeGreaterThanOrEqual(1);
  expect(screen.getByDisplayValue("右下技能区需要更环绕。")).toBeInTheDocument();
});
