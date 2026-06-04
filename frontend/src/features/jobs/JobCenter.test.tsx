import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { JobCenter } from "./JobCenter";

const api = {
  createGenerationJob: jest.fn(),
  createMockUiGenerationJob: jest.fn(),
  getAssetFileUrl: jest.fn((assetId: string) => `/assets/${assetId}/file`),
  listAiProviders: jest.fn(),
  listGenerationJobResults: jest.fn(),
  listGenerationJobs: jest.fn(),
  listProjects: jest.fn(),
  retryGenerationJob: jest.fn(),
  runGenerationJob: jest.fn(),
  runMockGenerationJob: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
  api.listGenerationJobs.mockResolvedValue({
    items: [
      {
        id: "job-1",
        project_id: "project-1",
        provider_id: null,
        job_type: "base_panel_preview",
        status: "failed",
        progress: 45,
        input_json: "{\"panel_id\":\"panel-1\"}",
        output_json: "",
        output_preview_path: "",
        error_message: "mock failure",
        retry_count: 0,
        logs: "queued\nfailed",
        created_at: "2026-06-03 12:00:00",
        updated_at: "2026-06-03 12:00:00",
      },
    ],
  });
  api.listProjects.mockResolvedValue({
    items: [
      {
        id: "project-1",
        name: "Mock Project",
        description: "",
        status: "active",
        created_at: "2026-06-03 10:00:00",
        updated_at: "2026-06-03 10:00:00",
      },
    ],
  });
  api.listAiProviders.mockResolvedValue({
    items: [
      {
        id: "provider-1",
        name: "Mock Provider",
        type: "mock",
        enabled: true,
        config_json: "{}",
        created_at: "2026-06-03 10:00:00",
        updated_at: "2026-06-03 10:00:00",
      },
    ],
  });
  api.listGenerationJobResults.mockResolvedValue({ items: [] });
});

test("creates, shows details, and retries failed generation jobs", async () => {
  api.createGenerationJob.mockResolvedValue({
    id: "job-2",
    project_id: null,
    provider_id: "provider-1",
    job_type: "asset_prepare",
    status: "pending",
    progress: 0,
    input_json: "{}",
    output_json: "",
    output_preview_path: "",
    error_message: "",
    retry_count: 0,
    logs: "queued",
    created_at: "2026-06-03 12:30:00",
    updated_at: "2026-06-03 12:30:00",
  });
  api.retryGenerationJob.mockResolvedValue({
    id: "job-1",
    project_id: "project-1",
    provider_id: null,
    job_type: "base_panel_preview",
    status: "pending",
    progress: 0,
    input_json: "{\"panel_id\":\"panel-1\"}",
    output_json: "",
    output_preview_path: "",
    error_message: "",
    retry_count: 1,
    logs: "queued\nfailed\nRetry 1 queued",
    created_at: "2026-06-03 12:00:00",
    updated_at: "2026-06-03 12:40:00",
  });

  const user = userEvent.setup();
  render(<JobCenter api={api} />);

  expect(await screen.findByText("base_panel_preview")).toBeInTheDocument();
  expect(screen.getByText("failed")).toBeInTheDocument();
  expect(screen.getByText("45%")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "View base_panel_preview" }));
  expect(screen.getByText(/queued/)).toBeInTheDocument();
  expect(screen.getByText("mock failure")).toBeInTheDocument();

  await user.type(screen.getByLabelText("Job type"), "asset_prepare");
  await user.click(screen.getByRole("button", { name: "Create test job" }));
  expect(api.createGenerationJob).toHaveBeenCalledWith({
    project_id: null,
    provider_id: "provider-1",
    job_type: "asset_prepare",
    status: "pending",
    progress: 0,
    input_json: "{\"device_type\":\"mobile\",\"width\":1080,\"height\":1920}",
    output_json: "",
    output_preview_path: "",
    error_message: "",
    logs: "queued",
  });
  expect(await screen.findByText("asset_prepare")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Retry base_panel_preview" }));
  expect(api.retryGenerationJob).toHaveBeenCalledWith("job-1");
  expect(await screen.findByText(/Retry 1 queued/)).toBeInTheDocument();
});

test("creates a mock UI job, runs mock, and shows logs and result assets", async () => {
  api.createMockUiGenerationJob.mockResolvedValue({
    id: "job-3",
    project_id: "project-1",
    provider_id: null,
    job_type: "mock_ui_generation",
    status: "pending",
    progress: 0,
    input_json: "{\"device_type\":\"desktop\",\"width\":640,\"height\":360}",
    output_json: "",
    output_preview_path: "",
    error_message: "",
    retry_count: 0,
    logs: "Mock UI job queued",
    created_at: "2026-06-03 13:00:00",
    updated_at: "2026-06-03 13:00:00",
  });
  api.runMockGenerationJob.mockResolvedValue({
    id: "job-3",
    project_id: "project-1",
    provider_id: null,
    job_type: "mock_ui_generation",
    status: "completed",
    progress: 100,
    input_json: "{\"device_type\":\"desktop\",\"width\":640,\"height\":360}",
    output_json: "{\"asset_ids\":[\"asset-result-1\"]}",
    output_preview_path: "assets/996-ready/job-3/previews/ui_preview.png",
    error_message: "",
    retry_count: 0,
    logs: "Mock UI job queued\nMock run started\nMock run completed",
    created_at: "2026-06-03 13:00:00",
    updated_at: "2026-06-03 13:01:00",
  });
  api.listGenerationJobResults.mockResolvedValue({
    items: [
      {
        id: "asset-result-1",
        project_id: "project-1",
        asset_type: "ui_preview",
        device_type: "desktop",
        width: 640,
        height: 360,
        file_path: "assets/uploads/mock/ui_preview.png",
        original_filename: "ui_preview.png",
        metadata_json: "{\"mock\":true}",
        source: "mock_generated",
        generation_job_id: "job-3",
        thumbnail_path: "assets/uploads/mock/thumb.png",
        created_at: "2026-06-03 13:01:00",
        updated_at: "2026-06-03 13:01:00",
      },
    ],
  });

  const user = userEvent.setup();
  render(<JobCenter api={api} />);

  await screen.findByText("base_panel_preview");
  await user.selectOptions(screen.getByLabelText("Mock 项目"), "project-1");
  await user.selectOptions(screen.getByLabelText("Mock device"), "desktop");
  await user.clear(screen.getByLabelText("Mock width"));
  await user.type(screen.getByLabelText("Mock width"), "640");
  await user.clear(screen.getByLabelText("Mock height"));
  await user.type(screen.getByLabelText("Mock height"), "360");
  await user.click(screen.getByRole("button", { name: "Create mock UI job" }));

  expect(api.createMockUiGenerationJob).toHaveBeenCalledWith({
    project_id: "project-1",
    device_type: "desktop",
    width: 640,
    height: 360,
  });
  expect(await screen.findByText("mock_ui_generation")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Run Mock mock_ui_generation" }));

  expect(api.runMockGenerationJob).toHaveBeenCalledWith("job-3");
  expect(api.listGenerationJobResults).toHaveBeenCalledWith("job-3");
  expect(await screen.findAllByText("completed")).toHaveLength(2);
  expect(screen.getByText(/Mock run completed/)).toBeInTheDocument();
  expect(screen.getByText(/ui_preview\s*\/\s*mock_generated/)).toBeInTheDocument();
  expect(screen.getByAltText("Result ui_preview")).toHaveAttribute("src", "/assets/asset-result-1/file");
});

test("creates a real UI generation placeholder job from the job center", async () => {
  api.createGenerationJob.mockResolvedValue({
    id: "job-4",
    project_id: "project-1",
    provider_id: "provider-1",
    job_type: "real_ui_generation",
    status: "pending",
    progress: 0,
    input_json: "{\"prompt\":\"Battle pass shop\",\"device_type\":\"mobile\",\"width\":1080,\"height\":1920}",
    output_json: "",
    output_preview_path: "",
    error_message: "",
    retry_count: 0,
    logs: "queued",
    created_at: "2026-06-04 10:00:00",
    updated_at: "2026-06-04 10:00:00",
  });

  const user = userEvent.setup();
  render(<JobCenter api={api} />);

  await screen.findByText("base_panel_preview");
  await user.selectOptions(screen.getByLabelText("Real project"), "project-1");
  await user.selectOptions(screen.getByLabelText("Real provider"), "provider-1");
  await user.clear(screen.getByLabelText("Prompt"));
  await user.type(screen.getByLabelText("Prompt"), "Battle pass shop");
  await user.selectOptions(screen.getByLabelText("Real device"), "mobile");
  await user.clear(screen.getByLabelText("Real width"));
  await user.type(screen.getByLabelText("Real width"), "1080");
  await user.clear(screen.getByLabelText("Real height"));
  await user.type(screen.getByLabelText("Real height"), "1920");
  await user.click(screen.getByRole("button", { name: "Create Real UI Job" }));

  expect(api.createGenerationJob).toHaveBeenCalledWith({
    project_id: "project-1",
    provider_id: "provider-1",
    job_type: "real_ui_generation",
    status: "pending",
    progress: 0,
    input_json: JSON.stringify({
      prompt: "Battle pass shop",
      device_type: "mobile",
      width: 1080,
      height: 1920,
    }),
    output_json: "",
    output_preview_path: "",
    error_message: "",
    logs: "queued",
  });
  expect(await screen.findByText("real_ui_generation")).toBeInTheDocument();
});
