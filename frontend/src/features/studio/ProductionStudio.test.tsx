import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProductionStudio } from "./ProductionStudio";

const api = {
  generateProductionStudioPackage: jest.fn(),
  getProductionStudioFileUrl: jest.fn((path: string) => `http://127.0.0.1:8000${path}`),
  listProductionStyleCodes: jest.fn(),
};

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
  api.generateProductionStudioPackage.mockResolvedValue({
    style_code: "STYLE_0003",
    device_type: "mobile_landscape",
    asset_mode: "resource_production",
    style_source: "existing_style",
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

test("renders Chinese production defaults and generates with an existing style", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  expect(await screen.findByText("生产工作台")).toBeInTheDocument();
  expect(screen.getByLabelText("设备类型")).toHaveDisplayValue("手机横屏");
  expect(screen.getByLabelText("输出模式")).toHaveDisplayValue("资源生产");

  await user.click(screen.getByLabelText("使用已有风格"));
  expect(await screen.findByText(/Sprint 16 Dark Gold Dragon Mobile/)).toBeInTheDocument();

  await user.click(screen.getByLabelText("背包界面"));
  await user.click(screen.getByLabelText("主界面"));
  await user.click(screen.getByRole("button", { name: "开始生成" }));

  expect(api.generateProductionStudioPackage).toHaveBeenCalledWith({
    device_type: "mobile_landscape",
    asset_mode: "resource_production",
    style_source: "existing_style",
    style_code: "STYLE_0003",
    screen_types: ["bag_ui"],
    style_name: "暗黑金龙传奇风",
    prompt: "手机横屏传奇 UI，暗黑金龙风格，技能栏清晰，右侧菜单明显，整体适合 996 引擎资源生产。",
  });
  expect(await screen.findByText("结果中心")).toBeInTheDocument();
  expect(screen.getByText("风格编号：")).toBeInTheDocument();
  expect(screen.getByText("验证通过")).toBeInTheDocument();
  expect(screen.getByText("组件数量")).toBeInTheDocument();
  expect(screen.getByText("候选资源")).toBeInTheDocument();
  expect(screen.getAllByText("待验收").length).toBeGreaterThanOrEqual(1);
  expect(screen.getByText("查看资源")).toBeInTheDocument();
  expect(screen.getByText("查看报告")).toBeInTheDocument();
  expect(screen.getByAltText("背包界面预览图")).toHaveAttribute(
    "src",
    "http://127.0.0.1:8000/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/ui_preview.png",
  );
});

test("keeps new style as the default source and sends main screen by default", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await screen.findByText("生产工作台");
  await user.selectOptions(screen.getByLabelText("设备类型"), "pc_landscape");
  await user.selectOptions(screen.getByLabelText("输出模式"), "ui_package");
  await user.click(screen.getByRole("button", { name: "开始生成" }));

  expect(api.generateProductionStudioPackage).toHaveBeenCalledWith(
    expect.objectContaining({
      device_type: "pc_landscape",
      asset_mode: "ui_package",
      style_source: "new_style",
      style_code: null,
      screen_types: ["main_ui"],
    }),
  );
});

test("supports manual acceptance status and notes in result center", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await screen.findByText("生产工作台");
  await user.click(screen.getByRole("button", { name: "开始生成" }));
  await screen.findByText("人工验收状态");

  await user.selectOptions(screen.getByLabelText("人工验收状态"), "needs_change");
  await user.type(screen.getByLabelText("验收记录"), "按钮命名需要修改");

  expect(screen.getAllByText("需要修改").length).toBeGreaterThanOrEqual(1);
  expect(screen.getByDisplayValue("按钮命名需要修改")).toBeInTheDocument();
});

test("shows clear Chinese next steps when generation fails", async () => {
  const user = userEvent.setup();
  api.generateProductionStudioPackage.mockRejectedValueOnce(new Error("missing key"));
  render(<ProductionStudio api={api} />);

  await screen.findByText("生产工作台");
  await user.click(screen.getByRole("button", { name: "开始生成" }));

  expect(
    await screen.findByText("生成失败：本地工作台还没有准备好。请关闭旧窗口，在项目根目录运行 启动工作台.ps1，然后重新点击开始生成。"),
  ).toBeInTheDocument();
});
