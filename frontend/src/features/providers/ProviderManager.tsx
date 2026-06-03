"use client";

import { FormEvent, useEffect, useState } from "react";

import { AiProvider, ProviderHealth, studioApi } from "@/lib/api";

type ProviderApi = Pick<
  typeof studioApi,
  "createAiProvider" | "getAiProviderHealth" | "listAiProviders" | "updateAiProvider"
>;

export function ProviderManager({ api = studioApi }: { api?: ProviderApi }) {
  const [providers, setProviders] = useState<AiProvider[]>([]);
  const [health, setHealth] = useState<Record<string, ProviderHealth>>({});
  const [name, setName] = useState("Mock Provider");
  const [type, setType] = useState<AiProvider["type"]>("mock");
  const [enabled, setEnabled] = useState(true);
  const [configJson, setConfigJson] = useState("{}");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listAiProviders()
      .then((result) => setProviders(result.items))
      .catch(() => setError("Providers failed to load"));
  }, [api]);

  async function createProvider(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const created = await api.createAiProvider({
      name,
      type,
      enabled,
      config_json: configJson,
    });
    setProviders((items) => [created, ...items]);
  }

  async function toggleProvider(provider: AiProvider) {
    const updated = await api.updateAiProvider(provider.id, {
      name: provider.name,
      type: provider.type,
      enabled: !provider.enabled,
      config_json: provider.config_json,
    });
    setProviders((items) => items.map((item) => (item.id === updated.id ? updated : item)));
  }

  async function checkHealth(provider: AiProvider) {
    const result = await api.getAiProviderHealth(provider.id);
    setHealth((items) => ({ ...items, [provider.id]: result }));
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">Provider Config</h2>
        <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          Real API keys must live in local environment variables. config_json stores only{" "}
          <code>{"{\"api_key_env\":\"OPENAI_API_KEY\"}"}</code>. Do not write keys to the database or commit them to
          GitHub.
        </div>
        <form className="mt-4 grid gap-3" onSubmit={createProvider}>
          <label className="grid gap-1 text-sm font-medium">
            Provider name
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setName(event.target.value)}
              value={name}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Provider type
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setType(event.target.value as AiProvider["type"])}
              value={type}
            >
              <option value="mock">mock</option>
              <option value="openai">openai</option>
              <option value="custom">custom</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm font-medium">
            <input checked={enabled} onChange={(event) => setEnabled(event.target.checked)} type="checkbox" />
            Enabled
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Config JSON
            <textarea
              className="min-h-28 rounded-md border border-studio-line px-3 py-2 font-mono text-xs font-normal"
              onChange={(event) => setConfigJson(event.target.value)}
              value={configJson}
            />
          </label>
          <button className="rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white" type="submit">
            Create provider
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </div>

      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">Providers</h2>
        <div className="mt-4 grid gap-3">
          {providers.map((provider) => (
            <article className="rounded-md border border-studio-line p-4" key={provider.id}>
              <div className="grid gap-3 lg:grid-cols-[1fr_auto] lg:items-start">
                <div>
                  <h3 className="font-semibold">{provider.name}</h3>
                  <p className="mt-1 text-sm text-studio-muted">
                    {provider.type} / {provider.enabled ? "enabled" : "disabled"}
                  </p>
                  <p className="mt-2 break-all font-mono text-xs text-studio-muted">{provider.config_json}</p>
                  {health[provider.id] ? (
                    <p className="mt-2 text-sm text-studio-muted">
                      Health: {health[provider.id].status} / {health[provider.id].message}
                    </p>
                  ) : (
                    <p className="mt-2 text-sm text-studio-muted">Health: not checked</p>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    aria-label={`Toggle ${provider.name}`}
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    onClick={() => toggleProvider(provider)}
                    type="button"
                  >
                    {provider.enabled ? "Disable" : "Enable"}
                  </button>
                  <button
                    aria-label={`Health ${provider.name}`}
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    onClick={() => checkHealth(provider)}
                    type="button"
                  >
                    Health
                  </button>
                </div>
              </div>
            </article>
          ))}
          {providers.length === 0 ? <p className="text-sm text-studio-muted">No providers yet.</p> : null}
        </div>
      </div>
    </section>
  );
}
