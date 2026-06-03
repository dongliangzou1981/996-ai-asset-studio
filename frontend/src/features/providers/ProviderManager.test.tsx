import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProviderManager } from "./ProviderManager";

const api = {
  createAiProvider: jest.fn(),
  getAiProviderHealth: jest.fn(),
  listAiProviders: jest.fn(),
  updateAiProvider: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
  api.listAiProviders.mockResolvedValue({
    items: [
      {
        id: "provider-1",
        name: "OpenAI Images",
        type: "openai",
        enabled: true,
        config_json: "{\"api_key_env\":\"OPENAI_API_KEY\"}",
        created_at: "2026-06-03 10:00:00",
        updated_at: "2026-06-03 10:00:00",
      },
    ],
  });
});

test("creates, toggles, and checks provider health", async () => {
  const user = userEvent.setup();
  api.createAiProvider.mockResolvedValue({
    id: "provider-2",
    name: "Mock Provider",
    type: "mock",
    enabled: true,
    config_json: "{}",
    created_at: "2026-06-03 11:00:00",
    updated_at: "2026-06-03 11:00:00",
  });
  api.updateAiProvider.mockResolvedValue({
    id: "provider-1",
    name: "OpenAI Images",
    type: "openai",
    enabled: false,
    config_json: "{\"api_key_env\":\"OPENAI_API_KEY\"}",
    created_at: "2026-06-03 10:00:00",
    updated_at: "2026-06-03 11:30:00",
  });
  api.getAiProviderHealth.mockResolvedValue({
    id: "provider-1",
    name: "OpenAI Images",
    type: "openai",
    enabled: true,
    status: "healthy",
    message: "Environment variable OPENAI_API_KEY is configured",
  });

  render(<ProviderManager api={api} />);

  expect(await screen.findByText("OpenAI Images")).toBeInTheDocument();
  expect(screen.getByText(/Real API keys must live in local environment variables/)).toBeInTheDocument();
  expect(screen.getByText("Health: not checked")).toBeInTheDocument();

  await user.clear(screen.getByLabelText("Provider name"));
  await user.type(screen.getByLabelText("Provider name"), "Mock Provider");
  await user.selectOptions(screen.getByLabelText("Provider type"), "mock");
  await user.click(screen.getByRole("button", { name: "Create provider" }));

  expect(api.createAiProvider).toHaveBeenCalledWith({
    name: "Mock Provider",
    type: "mock",
    enabled: true,
    config_json: "{}",
  });
  expect(await screen.findByText("Mock Provider")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Toggle OpenAI Images" }));
  expect(api.updateAiProvider).toHaveBeenCalledWith("provider-1", {
    name: "OpenAI Images",
    type: "openai",
    enabled: false,
    config_json: "{\"api_key_env\":\"OPENAI_API_KEY\"}",
  });

  await user.click(screen.getByRole("button", { name: "Health OpenAI Images" }));
  expect(await screen.findByText(/Health: healthy/)).toBeInTheDocument();
});
