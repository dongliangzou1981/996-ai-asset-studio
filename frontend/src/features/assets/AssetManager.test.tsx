import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AssetManager } from "./AssetManager";

const api = {
  deleteAsset: jest.fn(),
  listAssets: jest.fn(),
  listProjects: jest.fn(),
  uploadAsset: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
  api.listProjects.mockResolvedValue({
    items: [
      {
        id: "project-1",
        name: "Asset Project",
        description: "",
        status: "active",
        created_at: "2026-06-03 10:00:00",
        updated_at: "2026-06-03 10:00:00",
      },
    ],
  });
  api.listAssets.mockResolvedValue({
    items: [
      {
        id: "asset-1",
        project_id: "project-1",
        asset_type: "reference_image",
        device_type: "mobile",
        width: 1080,
        height: 1920,
        file_path: "assets/reference.png",
        original_filename: "reference.png",
        metadata_json: "{}",
        created_at: "2026-06-03 10:00:00",
        updated_at: "2026-06-03 10:00:00",
      },
    ],
  });
});

test("filters, uploads, and deletes assets through the API client", async () => {
  const user = userEvent.setup();
  api.uploadAsset.mockResolvedValue({
    id: "asset-2",
    project_id: "project-1",
    asset_type: "ui_preview",
    device_type: "desktop",
    width: 2,
    height: 3,
    file_path: "assets/uploads/preview.png",
    original_filename: "preview.png",
    metadata_json: "{}",
    created_at: "2026-06-03 11:00:00",
    updated_at: "2026-06-03 11:00:00",
  });
  api.deleteAsset.mockResolvedValue(undefined);

  render(<AssetManager api={api} />);

  expect(await screen.findByText("reference.png")).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText("项目筛选"), "project-1");
  await user.selectOptions(screen.getByLabelText("类型筛选"), "reference_image");
  await user.click(screen.getByRole("button", { name: "应用筛选" }));

  expect(api.listAssets).toHaveBeenLastCalledWith("project-1", "reference_image");

  const file = new File(["fake"], "preview.png", { type: "image/png" });
  await user.upload(screen.getByLabelText("上传文件"), file);
  await user.selectOptions(screen.getByLabelText("上传类型"), "ui_preview");
  await user.selectOptions(screen.getByLabelText("上传设备"), "desktop");
  await user.click(screen.getByRole("button", { name: "上传素材" }));

  expect(api.uploadAsset).toHaveBeenCalledWith({
    file,
    project_id: "project-1",
    asset_type: "ui_preview",
    device_type: "desktop",
  });
  expect(await screen.findByText("preview.png")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "删除 reference.png" }));
  expect(api.deleteAsset).toHaveBeenCalledWith("asset-1");
  await waitFor(() => {
    expect(screen.queryByText("reference.png")).not.toBeInTheDocument();
  });
});

