import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { JobCenter } from "./JobCenter";

const api = {
  createGenerationJob: jest.fn(),
  listGenerationJobs: jest.fn(),
  retryGenerationJob: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
  api.listGenerationJobs.mockResolvedValue({
    items: [
      {
        id: "job-1",
        project_id: "project-1",
        job_type: "base_panel_preview",
        status: "failed",
        progress: 45,
        input_json: "{\"panel_id\":\"panel-1\"}",
        output_json: "",
        error_message: "mock failure",
        retry_count: 0,
        logs: "queued\nfailed",
        created_at: "2026-06-03 12:00:00",
        updated_at: "2026-06-03 12:00:00",
      },
    ],
  });
});

test("creates, shows details, and retries failed generation jobs", async () => {
  api.createGenerationJob.mockResolvedValue({
    id: "job-2",
    project_id: null,
    job_type: "asset_prepare",
    status: "pending",
    progress: 0,
    input_json: "{}",
    output_json: "",
    error_message: "",
    retry_count: 0,
    logs: "queued",
    created_at: "2026-06-03 12:30:00",
    updated_at: "2026-06-03 12:30:00",
  });
  api.retryGenerationJob.mockResolvedValue({
    id: "job-1",
    project_id: "project-1",
    job_type: "base_panel_preview",
    status: "pending",
    progress: 0,
    input_json: "{\"panel_id\":\"panel-1\"}",
    output_json: "",
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
    job_type: "asset_prepare",
    status: "pending",
    progress: 0,
    input_json: "{}",
    output_json: "",
    error_message: "",
    logs: "queued",
  });
  expect(await screen.findByText("asset_prepare")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Retry base_panel_preview" }));
  expect(api.retryGenerationJob).toHaveBeenCalledWith("job-1");
  expect(await screen.findByText(/Retry 1 queued/)).toBeInTheDocument();
});
