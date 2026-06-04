import { fireEvent, render, screen } from "@testing-library/react";
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
    name: "Ofox",
    type: "ofox",
    enabled: true,
    config_json: "{\"api_key_env\":\"OFOX_API_KEY\",\"base_url\":\"https://api.ofox.ai/v1\",\"model\":\"gpt-image-2\"}",
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
  expect(screen.getByText(/真实 API Key 必须配置在本地环境变量/)).toBeInTheDocument();
  expect(screen.getByText("健康状态：未检查")).toBeInTheDocument();

  await user.clear(screen.getByLabelText("提供商名称"));
  await user.type(screen.getByLabelText("提供商名称"), "Ofox");
  await user.selectOptions(screen.getByLabelText("提供商类型"), "ofox");
  await user.clear(screen.getByLabelText("Config JSON"));
  fireEvent.change(screen.getByLabelText("Config JSON"), {
    target: { value: "{\"api_key_env\":\"OFOX_API_KEY\",\"base_url\":\"https://api.ofox.ai/v1\",\"model\":\"gpt-image-2\"}" },
  });
  await user.click(screen.getByRole("button", { name: "创建提供商" }));

  expect(api.createAiProvider).toHaveBeenCalledWith({
    name: "Ofox",
    type: "ofox",
    enabled: true,
    config_json: "{\"api_key_env\":\"OFOX_API_KEY\",\"base_url\":\"https://api.ofox.ai/v1\",\"model\":\"gpt-image-2\"}",
  });
  expect(await screen.findByText("Ofox")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "切换 OpenAI Images" }));
  expect(api.updateAiProvider).toHaveBeenCalledWith("provider-1", {
    name: "OpenAI Images",
    type: "openai",
    enabled: false,
    config_json: "{\"api_key_env\":\"OPENAI_API_KEY\"}",
  });

  await user.click(screen.getByRole("button", { name: "检查健康状态 OpenAI Images" }));
  expect(await screen.findByText(/健康状态：healthy/)).toBeInTheDocument();
});
