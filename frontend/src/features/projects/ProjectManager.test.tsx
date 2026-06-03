import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectManager } from "./ProjectManager";

const api = {
  createProject: jest.fn(),
  deleteProject: jest.fn(),
  listProjects: jest.fn(),
  updateProject: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
  api.listProjects.mockResolvedValue({
    items: [
      {
        id: "project-1",
        name: "Match-3 Launch",
        description: "Playable ad art",
        status: "draft",
        created_at: "2026-06-03 10:00:00",
        updated_at: "2026-06-03 10:00:00",
      },
    ],
  });
});

test("creates, edits, and deletes projects through the API client", async () => {
  const user = userEvent.setup();
  api.createProject.mockResolvedValue({
    id: "project-2",
    name: "Runner Icons",
    description: "Icon set",
    status: "active",
    created_at: "2026-06-03 11:00:00",
    updated_at: "2026-06-03 11:00:00",
  });
  api.updateProject.mockResolvedValue({
    id: "project-1",
    name: "Match-3 Launch V2",
    description: "Playable ad art",
    status: "active",
    created_at: "2026-06-03 10:00:00",
    updated_at: "2026-06-03 11:30:00",
  });
  api.deleteProject.mockResolvedValue(undefined);

  render(<ProjectManager api={api} />);

  expect(await screen.findByText("Match-3 Launch")).toBeInTheDocument();

  await user.type(screen.getByLabelText("项目名称"), "Runner Icons");
  await user.type(screen.getByLabelText("项目描述"), "Icon set");
  await user.selectOptions(screen.getByLabelText("项目状态"), "active");
  await user.click(screen.getByRole("button", { name: "创建项目" }));

  expect(api.createProject).toHaveBeenCalledWith({
    name: "Runner Icons",
    description: "Icon set",
    status: "active",
  });
  expect(await screen.findByText("Runner Icons")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "编辑 Match-3 Launch" }));
  await user.clear(screen.getByLabelText("项目名称"));
  await user.type(screen.getByLabelText("项目名称"), "Match-3 Launch V2");
  await user.selectOptions(screen.getByLabelText("项目状态"), "active");
  await user.click(screen.getByRole("button", { name: "保存项目" }));

  expect(api.updateProject).toHaveBeenCalledWith("project-1", {
    name: "Match-3 Launch V2",
    description: "Playable ad art",
    status: "active",
  });
  expect(await screen.findByText("Match-3 Launch V2")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "删除 Match-3 Launch V2" }));

  expect(api.deleteProject).toHaveBeenCalledWith("project-1");
  await waitFor(() => {
    expect(screen.queryByText("Match-3 Launch V2")).not.toBeInTheDocument();
  });
});

