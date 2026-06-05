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

test("renders production defaults and generates with existing STYLE_CODE selection", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  expect(await screen.findByText("生产工作台")).toBeInTheDocument();
  expect(screen.getByLabelText("设备类型")).toHaveValue("mobile_landscape");
  expect(screen.getByLabelText("输出模式")).toHaveValue("resource_production");

  await user.click(screen.getByLabelText("使用已有 STYLE_CODE"));
  expect(await screen.findByText(/Sprint 16 Dark Gold Dragon Mobile/)).toBeInTheDocument();

  await user.click(screen.getByLabelText("bag_ui 背包界面"));
  await user.click(screen.getByLabelText("main_ui 主界面"));
  await user.click(screen.getByRole("button", { name: "生成 UI 资源" }));

  expect(api.generateProductionStudioPackage).toHaveBeenCalledWith({
    device_type: "mobile_landscape",
    asset_mode: "resource_production",
    style_source: "existing_style",
    style_code: "STYLE_0003",
    screen_types: ["bag_ui"],
    style_name: "暗黑金龙传奇风",
    prompt: "手机横屏传奇 UI，暗黑金龙风格，技能栏清晰，右侧菜单明显，整体适合 996 引擎资源生产。",
  });
  expect(await screen.findByText("device_type:")).toBeInTheDocument();
  expect(screen.getAllByText("STYLE_0003").length).toBeGreaterThanOrEqual(1);
  expect(screen.getByText("validator PASS")).toBeInTheDocument();
  expect(screen.getByText("components 6 / candidates 6")).toBeInTheDocument();
  expect(screen.getByText("仍需优化 common_icons")).toBeInTheDocument();
  expect(screen.getByAltText("bag_ui ui_preview")).toHaveAttribute(
    "src",
    "http://127.0.0.1:8000/production-studio/files/996-ready/STYLE_0003/bag_ui/job-bag/ui_preview.png",
  );
});

test("keeps new style as the default source and sends main_ui by default", async () => {
  const user = userEvent.setup();
  render(<ProductionStudio api={api} />);

  await screen.findByText("生产工作台");
  await user.selectOptions(screen.getByLabelText("设备类型"), "pc_landscape");
  await user.selectOptions(screen.getByLabelText("输出模式"), "ui_package");
  await user.click(screen.getByRole("button", { name: "生成 UI 资源" }));

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
