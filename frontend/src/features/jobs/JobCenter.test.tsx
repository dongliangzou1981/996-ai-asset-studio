import { render, screen } from "@testing-library/react";

import { JobCenter } from "./JobCenter";

const api = {
  listGenerationJobs: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
  api.listGenerationJobs.mockResolvedValue({
    items: [
      {
        id: "job-1",
        project_id: "project-1",
        job_type: "base_panel_preview",
        status: "pending",
        progress: 0,
        created_at: "2026-06-03 12:00:00",
        updated_at: "2026-06-03 12:00:00",
      },
    ],
  });
});

test("renders generation jobs from the API client", async () => {
  render(<JobCenter api={api} />);

  expect(await screen.findByText("base_panel_preview")).toBeInTheDocument();
  expect(screen.getByText("pending")).toBeInTheDocument();
  expect(screen.getByText("0%")).toBeInTheDocument();
});

