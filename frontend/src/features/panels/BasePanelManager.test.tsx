import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { BasePanelManager } from "./BasePanelManager";

const api = {
  copyBasePanel: jest.fn(),
  createBasePanel: jest.fn(),
  deleteBasePanel: jest.fn(),
  listBasePanels: jest.fn(),
  listProjects: jest.fn(),
  listStyleProfiles: jest.fn(),
  updateBasePanel: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
  api.listProjects.mockResolvedValue({
    items: [
      {
        id: "project-1",
        name: "Panel Project",
        description: "",
        status: "active",
        created_at: "2026-06-03 10:00:00",
        updated_at: "2026-06-03 10:00:00",
      },
    ],
  });
  api.listStyleProfiles.mockResolvedValue({
    items: [
      {
        id: "style-1",
        project_id: "project-1",
        name: "Clean Mobile",
        description: "",
        palette_json: "{}",
        prompt_notes: "",
        created_at: "2026-06-03 10:00:00",
        updated_at: "2026-06-03 10:00:00",
      },
    ],
  });
  api.listBasePanels.mockResolvedValue({
    items: [
      {
        id: "panel-1",
        project_id: "project-1",
        style_profile_id: "style-1",
        panel_type: "main_panel",
        device_type: "mobile",
        width: 1080,
        height: 1920,
        texture: "soft_glass",
        border_style: "rounded_8",
        background_style: "layered_gradient",
        color_scheme: "blue_white",
        created_at: "2026-06-03 10:00:00",
        updated_at: "2026-06-03 10:00:00",
      },
    ],
  });
});

test("creates, edits, copies, and deletes base panels through the API client", async () => {
  const user = userEvent.setup();
  api.createBasePanel.mockResolvedValue({
    id: "panel-2",
    project_id: "project-1",
    style_profile_id: "style-1",
    panel_type: "popup_panel",
    device_type: "tablet",
    width: 1536,
    height: 2048,
    texture: "paper",
    border_style: "thin_line",
    background_style: "flat",
    color_scheme: "warm_gray",
    created_at: "2026-06-03 11:00:00",
    updated_at: "2026-06-03 11:00:00",
  });
  api.updateBasePanel.mockResolvedValue({
    id: "panel-1",
    project_id: "project-1",
    style_profile_id: "style-1",
    panel_type: "list_panel",
    device_type: "mobile",
    width: 1080,
    height: 1600,
    texture: "matte",
    border_style: "none",
    background_style: "flat",
    color_scheme: "neutral",
    created_at: "2026-06-03 10:00:00",
    updated_at: "2026-06-03 11:30:00",
  });
  api.copyBasePanel.mockResolvedValue({
    id: "panel-copy",
    project_id: "project-1",
    style_profile_id: "style-1",
    panel_type: "list_panel",
    device_type: "mobile",
    width: 1080,
    height: 1600,
    texture: "matte",
    border_style: "none",
    background_style: "flat",
    color_scheme: "neutral",
    created_at: "2026-06-03 11:40:00",
    updated_at: "2026-06-03 11:40:00",
  });
  api.deleteBasePanel.mockResolvedValue(undefined);

  render(<BasePanelManager api={api} />);

  expect(await screen.findByText("main_panel")).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText("面板类型"), "popup_panel");
  await user.selectOptions(screen.getByLabelText("设备类型"), "tablet");
  await user.clear(screen.getByLabelText("宽度"));
  await user.type(screen.getByLabelText("宽度"), "1536");
  await user.clear(screen.getByLabelText("高度"));
  await user.type(screen.getByLabelText("高度"), "2048");
  await user.clear(screen.getByLabelText("纹理"));
  await user.type(screen.getByLabelText("纹理"), "paper");
  await user.clear(screen.getByLabelText("边框样式"));
  await user.type(screen.getByLabelText("边框样式"), "thin_line");
  await user.clear(screen.getByLabelText("背景样式"));
  await user.type(screen.getByLabelText("背景样式"), "flat");
  await user.clear(screen.getByLabelText("配色方案"));
  await user.type(screen.getByLabelText("配色方案"), "warm_gray");
  await user.click(screen.getByRole("button", { name: "创建面板" }));

  expect(api.createBasePanel).toHaveBeenCalledWith({
    project_id: "project-1",
    style_profile_id: "style-1",
    panel_type: "popup_panel",
    device_type: "tablet",
    width: 1536,
    height: 2048,
    texture: "paper",
    border_style: "thin_line",
    background_style: "flat",
    color_scheme: "warm_gray",
  });
  expect(await screen.findByText("panel-2")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "编辑 main_panel panel-1" }));
  await user.selectOptions(screen.getByLabelText("面板类型"), "list_panel");
  await user.clear(screen.getByLabelText("高度"));
  await user.type(screen.getByLabelText("高度"), "1600");
  await user.click(screen.getByRole("button", { name: "保存面板" }));

  expect(api.updateBasePanel).toHaveBeenCalledWith("panel-1", expect.objectContaining({
    panel_type: "list_panel",
    height: 1600,
  }));
  expect(await screen.findByText("mobile / 1080x1600")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "复制 list_panel panel-1" }));
  expect(api.copyBasePanel).toHaveBeenCalledWith("panel-1");
  expect(await screen.findByText("panel-copy")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "删除 list_panel panel-1" }));
  expect(api.deleteBasePanel).toHaveBeenCalledWith("panel-1");
  await waitFor(() => {
    expect(screen.queryByText("panel-1")).not.toBeInTheDocument();
  });
});
