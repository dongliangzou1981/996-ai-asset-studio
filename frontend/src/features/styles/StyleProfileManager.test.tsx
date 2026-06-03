import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StyleProfileManager } from "./StyleProfileManager";

const api = {
  createStyleProfile: jest.fn(),
  deleteStyleProfile: jest.fn(),
  listProjects: jest.fn(),
  listStyleProfiles: jest.fn(),
  updateStyleProfile: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
  api.listProjects.mockResolvedValue({
    items: [
      {
        id: "project-1",
        name: "Match-3 Launch",
        description: "",
        status: "draft",
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
        name: "Candy UI",
        description: "Bright and rounded",
        palette_json: "{\"primary\":\"#ff6b9a\"}",
        prompt_notes: "Glossy buttons",
        created_at: "2026-06-03 10:00:00",
        updated_at: "2026-06-03 10:00:00",
      },
    ],
  });
});

test("creates, selects, edits, and deletes style profiles through the API client", async () => {
  const user = userEvent.setup();
  api.createStyleProfile.mockResolvedValue({
    id: "style-2",
    project_id: "project-1",
    name: "Cyber Neon",
    description: "High contrast",
    palette_json: "{\"primary\":\"#22d3ee\"}",
    prompt_notes: "Sharp panels",
    created_at: "2026-06-03 11:00:00",
    updated_at: "2026-06-03 11:00:00",
  });
  api.updateStyleProfile.mockResolvedValue({
    id: "style-1",
    project_id: "project-1",
    name: "Candy UI Plus",
    description: "Bright and rounded",
    palette_json: "{\"primary\":\"#f43f5e\"}",
    prompt_notes: "Bolder buttons",
    created_at: "2026-06-03 10:00:00",
    updated_at: "2026-06-03 11:30:00",
  });
  api.deleteStyleProfile.mockResolvedValue(undefined);

  render(<StyleProfileManager api={api} />);

  expect(await screen.findByText("Candy UI")).toBeInTheDocument();

  await user.type(screen.getByLabelText("风格名称"), "Cyber Neon");
  await user.type(screen.getByLabelText("风格描述"), "High contrast");
  fireEvent.change(screen.getByLabelText("色板 JSON"), {
    target: { value: "{\"primary\":\"#22d3ee\"}" },
  });
  await user.type(screen.getByLabelText("Prompt 备注"), "Sharp panels");
  await user.click(screen.getByRole("button", { name: "创建风格" }));

  expect(api.createStyleProfile).toHaveBeenCalledWith({
    project_id: "project-1",
    name: "Cyber Neon",
    description: "High contrast",
    palette_json: "{\"primary\":\"#22d3ee\"}",
    prompt_notes: "Sharp panels",
  });
  expect(await screen.findByText("Cyber Neon")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "选择 Cyber Neon" }));
  expect(screen.getByText("当前选择：Cyber Neon")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "编辑 Candy UI" }));
  await user.clear(screen.getByLabelText("风格名称"));
  await user.type(screen.getByLabelText("风格名称"), "Candy UI Plus");
  await user.clear(screen.getByLabelText("色板 JSON"));
  fireEvent.change(screen.getByLabelText("色板 JSON"), {
    target: { value: "{\"primary\":\"#f43f5e\"}" },
  });
  await user.clear(screen.getByLabelText("Prompt 备注"));
  await user.type(screen.getByLabelText("Prompt 备注"), "Bolder buttons");
  await user.click(screen.getByRole("button", { name: "保存风格" }));

  expect(api.updateStyleProfile).toHaveBeenCalledWith("style-1", {
    project_id: "project-1",
    name: "Candy UI Plus",
    description: "Bright and rounded",
    palette_json: "{\"primary\":\"#f43f5e\"}",
    prompt_notes: "Bolder buttons",
  });
  expect(await screen.findByText("Candy UI Plus")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "删除 Candy UI Plus" }));

  expect(api.deleteStyleProfile).toHaveBeenCalledWith("style-1");
  await waitFor(() => {
    expect(screen.queryByText("Candy UI Plus")).not.toBeInTheDocument();
  });
});
