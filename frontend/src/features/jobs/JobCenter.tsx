"use client";

import { FormEvent, useEffect, useState } from "react";

import { AiProvider, Asset, BasePanel, GenerationJob, Project, StyleProfile, studioApi } from "@/lib/api";

type JobApi = Pick<
  typeof studioApi,
  | "createGenerationJob"
  | "createMockUiGenerationJob"
  | "getAssetFileUrl"
  | "listAiProviders"
  | "listAssets"
  | "listBasePanels"
  | "listGenerationJobResults"
  | "listGenerationJobs"
  | "listProjects"
  | "listStyleProfiles"
  | "retryGenerationJob"
  | "runGenerationJob"
  | "runMockGenerationJob"
>;

export function JobCenter({ api = studioApi }: { api?: JobApi }) {
  const [jobs, setJobs] = useState<GenerationJob[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [styleProfiles, setStyleProfiles] = useState<StyleProfile[]>([]);
  const [basePanels, setBasePanels] = useState<BasePanel[]>([]);
  const [referenceImages, setReferenceImages] = useState<Asset[]>([]);
  const [providers, setProviders] = useState<AiProvider[]>([]);
  const [selectedJob, setSelectedJob] = useState<GenerationJob | null>(null);
  const [results, setResults] = useState<Asset[]>([]);
  const [jobType, setJobType] = useState("");
  const [mockProjectId, setMockProjectId] = useState<string | null>(null);
  const [mockDevice, setMockDevice] = useState("mobile");
  const [mockWidth, setMockWidth] = useState(1080);
  const [mockHeight, setMockHeight] = useState(1920);
  const [realProjectId, setRealProjectId] = useState<string | null>(null);
  const [realStyleProfileId, setRealStyleProfileId] = useState<string | null>(null);
  const [realBasePanelId, setRealBasePanelId] = useState<string | null>(null);
  const [realReferenceImageId, setRealReferenceImageId] = useState<string | null>(null);
  const [realProviderId, setRealProviderId] = useState<string | null>(null);
  const [realPrompt, setRealPrompt] = useState("Create a polished game UI screen");
  const [realDevice, setRealDevice] = useState("mobile");
  const [realWidth, setRealWidth] = useState(1080);
  const [realHeight, setRealHeight] = useState(1920);
  const [providerId, setProviderId] = useState<string | null>(null);
  const [inputJson, setInputJson] = useState("{\"device_type\":\"mobile\",\"width\":1080,\"height\":1920}");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.listGenerationJobs(),
      api.listProjects(),
      api.listAiProviders(),
      api.listStyleProfiles(),
      api.listBasePanels(),
      api.listAssets(undefined, "reference_image"),
    ])
      .then(([jobResult, projectResult, providerResult, styleResult, panelResult, referenceResult]) => {
        setJobs(jobResult.items);
        setProjects(projectResult.items);
        setProviders(providerResult.items);
        setStyleProfiles(styleResult.items);
        setBasePanels(panelResult.items);
        setReferenceImages(referenceResult.items);
        setMockProjectId(projectResult.items[0]?.id ?? null);
        const initialProjectId = projectResult.items[0]?.id ?? null;
        setRealProjectId(initialProjectId);
        setRealStyleProfileId(styleResult.items.find((style) => style.project_id === initialProjectId)?.id ?? null);
        setRealBasePanelId(panelResult.items.find((panel) => panel.project_id === initialProjectId)?.id ?? null);
        setRealReferenceImageId(
          referenceResult.items.find((asset) => asset.project_id === initialProjectId)?.id ?? null,
        );
        const enabledProviderId = providerResult.items.find((provider) => provider.enabled)?.id ?? null;
        setProviderId(enabledProviderId);
        setRealProviderId(enabledProviderId);
      })
      .catch(() => setError("Jobs failed to load"));
  }, [api]);

  async function createJob(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const created = await api.createGenerationJob({
      project_id: null,
      provider_id: providerId,
      job_type: jobType,
      status: "pending",
      progress: 0,
      input_json: inputJson,
      output_json: "",
      output_preview_path: "",
      error_message: "",
      logs: "queued",
    });
    setJobs((items) => [created, ...items]);
    setJobType("");
  }

  async function createMockJob(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const created = await api.createMockUiGenerationJob({
      project_id: mockProjectId,
      device_type: mockDevice,
      width: mockWidth,
      height: mockHeight,
    });
    setJobs((items) => [created, ...items]);
    setSelectedJob(created);
    setResults([]);
  }

  async function createRealJob(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const created = await api.createGenerationJob({
      project_id: realProjectId,
      provider_id: realProviderId,
      job_type: "real_ui_generation",
      status: "pending",
      progress: 0,
      input_json: JSON.stringify({
        project_id: realProjectId,
        style_profile_id: realStyleProfileId,
        base_panel_id: realBasePanelId,
        reference_image_id: realReferenceImageId,
        prompt: realPrompt,
        device_type: realDevice,
        width: realWidth,
        height: realHeight,
      }),
      output_json: "",
      output_preview_path: "",
      error_message: "",
      logs: "queued",
    });
    setJobs((items) => [created, ...items]);
    setSelectedJob(created);
    setResults([]);
  }

  function updateRealProject(projectId: string | null) {
    setRealProjectId(projectId);
    setRealStyleProfileId(styleProfiles.find((style) => style.project_id === projectId)?.id ?? null);
    setRealBasePanelId(basePanels.find((panel) => panel.project_id === projectId)?.id ?? null);
    setRealReferenceImageId(referenceImages.find((asset) => asset.project_id === projectId)?.id ?? null);
  }

  async function retryJob(job: GenerationJob) {
    const retried = await api.retryGenerationJob(job.id);
    setJobs((items) => items.map((item) => (item.id === retried.id ? retried : item)));
    setSelectedJob(retried);
    setResults([]);
  }

  async function runMock(job: GenerationJob) {
    const completed = await api.runMockGenerationJob(job.id);
    const result = await api.listGenerationJobResults(completed.id);
    setJobs((items) => items.map((item) => (item.id === completed.id ? completed : item)));
    setSelectedJob(completed);
    setResults(result.items);
  }

  async function runJob(job: GenerationJob) {
    const completed = await api.runGenerationJob(job.id);
    const result = await api.listGenerationJobResults(completed.id);
    setJobs((items) => items.map((item) => (item.id === completed.id ? completed : item)));
    setSelectedJob(completed);
    setResults(result.items);
  }

  async function viewJob(job: GenerationJob) {
    setSelectedJob(job);
    if (job.output_json || job.job_type === "mock_ui_generation") {
      const result = await api.listGenerationJobResults(job.id);
      setResults(result.items);
    } else {
      setResults([]);
    }
  }

  function jobInput(job: GenerationJob | null): Record<string, unknown> {
    if (!job?.input_json) {
      return {};
    }
    try {
      const parsed = JSON.parse(job.input_json);
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch {
      return {};
    }
  }

  function projectName(projectId: unknown) {
    return projects.find((project) => project.id === projectId)?.name ?? String(projectId || "None");
  }

  function styleName(styleProfileId: unknown) {
    return styleProfiles.find((style) => style.id === styleProfileId)?.name ?? String(styleProfileId || "None");
  }

  function panelName(basePanelId: unknown) {
    const panel = basePanels.find((item) => item.id === basePanelId);
    return panel ? `${panel.panel_type} / ${panel.device_type} / ${panel.width}x${panel.height}` : String(basePanelId || "None");
  }

  function referenceName(referenceImageId: unknown) {
    return referenceImages.find((asset) => asset.id === referenceImageId)?.original_filename ?? String(referenceImageId || "None");
  }

  const filteredStyles = styleProfiles.filter((style) => !realProjectId || style.project_id === realProjectId);
  const filteredPanels = basePanels.filter((panel) => !realProjectId || panel.project_id === realProjectId);
  const filteredReferences = referenceImages.filter((asset) => !realProjectId || asset.project_id === realProjectId);
  const selectedJobInput = jobInput(selectedJob);

  return (
    <section className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">Job Center</h2>
        <p className="mt-2 text-sm text-studio-muted">Sprint 5 runs a local mock pipeline. No real AI model is connected.</p>

        <form className="mt-5 grid gap-3" onSubmit={createMockJob}>
          <label className="grid gap-1 text-sm font-medium">
            Mock 项目
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setMockProjectId(event.target.value || null)}
              value={mockProjectId ?? ""}
            >
              <option value="">Loose mock</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Mock device
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setMockDevice(event.target.value)}
              value={mockDevice}
            >
              <option value="mobile">mobile</option>
              <option value="tablet">tablet</option>
              <option value="desktop">desktop</option>
            </select>
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="grid gap-1 text-sm font-medium">
              Mock width
              <input
                className="rounded-md border border-studio-line px-3 py-2 font-normal"
                min={1}
                onChange={(event) => setMockWidth(Number(event.target.value))}
                type="number"
                value={mockWidth}
              />
            </label>
            <label className="grid gap-1 text-sm font-medium">
              Mock height
              <input
                className="rounded-md border border-studio-line px-3 py-2 font-normal"
                min={1}
                onChange={(event) => setMockHeight(Number(event.target.value))}
                type="number"
                value={mockHeight}
              />
            </label>
          </div>
          <button className="rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white" type="submit">
            Create mock UI job
          </button>
        </form>

        <form className="mt-6 grid gap-3 border-t border-studio-line pt-5" onSubmit={createRealJob}>
          <h3 className="text-sm font-semibold">Generation Wizard</h3>
          <label className="grid gap-1 text-sm font-medium">
            <span>Step 1: Project</span>
            Real project
            <select
              aria-label="Real project"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => updateRealProject(event.target.value || null)}
              value={realProjectId ?? ""}
            >
              <option value="">Loose real job</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            <span>Step 2: Style Profile</span>
            Real style profile
            <select
              aria-label="Real style profile"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setRealStyleProfileId(event.target.value || null)}
              value={realStyleProfileId ?? ""}
            >
              <option value="">No style profile</option>
              {filteredStyles.map((style) => (
                <option key={style.id} value={style.id}>
                  {style.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            <span>Step 3: Base Panel</span>
            Real base panel
            <select
              aria-label="Real base panel"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setRealBasePanelId(event.target.value || null)}
              value={realBasePanelId ?? ""}
            >
              <option value="">No base panel</option>
              {filteredPanels.map((panel) => (
                <option key={panel.id} value={panel.id}>
                  {panel.panel_type} / {panel.device_type} / {panel.width}x{panel.height}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            <span>Step 4: Reference Image</span>
            Real reference image
            <select
              aria-label="Real reference image"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setRealReferenceImageId(event.target.value || null)}
              value={realReferenceImageId ?? ""}
            >
              <option value="">No reference image</option>
              {filteredReferences.map((asset) => (
                <option key={asset.id} value={asset.id}>
                  {asset.original_filename}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Real provider
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setRealProviderId(event.target.value || null)}
              value={realProviderId ?? ""}
            >
              <option value="">Default provider</option>
              {providers.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.name} / {provider.type}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            <span>Step 5: Prompt</span>
            Prompt
            <textarea
              aria-label="Prompt"
              className="min-h-20 rounded-md border border-studio-line px-3 py-2 text-sm font-normal"
              onChange={(event) => setRealPrompt(event.target.value)}
              value={realPrompt}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Real device
            <select
              aria-label="Real device"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setRealDevice(event.target.value)}
              value={realDevice}
            >
              <option value="mobile">mobile</option>
              <option value="tablet">tablet</option>
              <option value="desktop">desktop</option>
            </select>
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="grid gap-1 text-sm font-medium">
              Real width
              <input
                aria-label="Real width"
                className="rounded-md border border-studio-line px-3 py-2 font-normal"
                min={1}
                onChange={(event) => setRealWidth(Number(event.target.value))}
                type="number"
                value={realWidth}
              />
            </label>
            <label className="grid gap-1 text-sm font-medium">
              Real height
              <input
                aria-label="Real height"
                className="rounded-md border border-studio-line px-3 py-2 font-normal"
                min={1}
                onChange={(event) => setRealHeight(Number(event.target.value))}
                type="number"
                value={realHeight}
              />
            </label>
          </div>
          <button className="rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white" type="submit">
            Create Real UI Job
          </button>
          <p className="text-sm font-semibold">Step 6: Create Real UI Job</p>
        </form>

        <form className="mt-6 grid gap-3 border-t border-studio-line pt-5" onSubmit={createJob}>
          <label className="grid gap-1 text-sm font-medium">
            Provider
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setProviderId(event.target.value || null)}
              value={providerId ?? ""}
            >
              <option value="">Default provider</option>
              {providers.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.name} / {provider.type}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Job type
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setJobType(event.target.value)}
              required
              value={jobType}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Input JSON
            <textarea
              className="min-h-24 rounded-md border border-studio-line px-3 py-2 font-mono text-xs font-normal"
              onChange={(event) => setInputJson(event.target.value)}
              value={inputJson}
            />
          </label>
          <button className="rounded-md border border-studio-line px-4 py-2 text-sm font-semibold" type="submit">
            Create test job
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </div>

      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">Job List</h2>
        <div className="mt-4 grid gap-3">
          {jobs.map((job) => (
            <article className="rounded-md border border-studio-line p-4" key={job.id}>
              <div className="grid gap-3 lg:grid-cols-[1fr_0.5fr_0.4fr_auto] lg:items-center">
                <div>
                  <h3 className="font-semibold">{job.job_type}</h3>
                  <p className="mt-1 break-all font-mono text-xs text-studio-muted">{job.id}</p>
                </div>
                <div className="text-sm text-studio-muted">{job.status}</div>
                <div className="text-sm font-semibold">{job.progress}%</div>
                <div className="flex flex-wrap gap-2">
                  <button
                    aria-label={`View ${job.job_type}`}
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    onClick={() => viewJob(job)}
                    type="button"
                  >
                    View
                  </button>
                  {job.job_type === "mock_ui_generation" && job.status !== "completed" ? (
                    <button
                      aria-label={`Run Mock ${job.job_type}`}
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      onClick={() => runMock(job)}
                      type="button"
                    >
                      运行 Mock
                    </button>
                  ) : null}
                  {job.job_type !== "mock_ui_generation" && job.status !== "completed" ? (
                    <button
                      aria-label={`Run Job ${job.job_type}`}
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      onClick={() => runJob(job)}
                      type="button"
                    >
                      运行任务
                    </button>
                  ) : null}
                  {job.status === "failed" ? (
                    <button
                      aria-label={`Retry ${job.job_type}`}
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      onClick={() => retryJob(job)}
                      type="button"
                    >
                      Retry
                    </button>
                  ) : null}
                </div>
              </div>
            </article>
          ))}
          {jobs.length === 0 ? <p className="text-sm text-studio-muted">No jobs yet.</p> : null}
        </div>

        {selectedJob ? (
          <aside className="mt-5 rounded-md border border-studio-line p-4">
            <h3 className="font-semibold">Job Detail</h3>
            <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-medium">Status</dt>
                <dd className="text-studio-muted">{selectedJob.status}</dd>
              </div>
              <div>
                <dt className="font-medium">Retry count</dt>
                <dd className="text-studio-muted">{selectedJob.retry_count}</dd>
              </div>
              <div>
                <dt className="font-medium">Error</dt>
                <dd className="text-studio-muted">{selectedJob.error_message || "None"}</dd>
              </div>
              <div>
                <dt className="font-medium">Input</dt>
                <dd className="break-all text-studio-muted">{selectedJob.input_json || "{}"}</dd>
              </div>
              <div>
                <dt className="font-medium">Project</dt>
                <dd className="text-studio-muted">Project: {projectName(selectedJobInput.project_id)}</dd>
              </div>
              <div>
                <dt className="font-medium">Style</dt>
                <dd className="text-studio-muted">Style: {styleName(selectedJobInput.style_profile_id)}</dd>
              </div>
              <div>
                <dt className="font-medium">Base Panel</dt>
                <dd className="text-studio-muted">Panel: {panelName(selectedJobInput.base_panel_id)}</dd>
              </div>
              <div>
                <dt className="font-medium">Reference Image</dt>
                <dd className="text-studio-muted">Reference: {referenceName(selectedJobInput.reference_image_id)}</dd>
              </div>
              <div>
                <dt className="font-medium">Prompt</dt>
                <dd className="text-studio-muted">Prompt: {String(selectedJobInput.prompt || "None")}</dd>
              </div>
            </dl>
            <h4 className="mt-4 text-sm font-semibold">Log Timeline</h4>
            <pre className="mt-2 whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-xs text-studio-ink">
              {selectedJob.logs || "No logs"}
            </pre>
            <h4 className="mt-4 text-sm font-semibold">Result Assets</h4>
            <div className="mt-2 grid gap-3 sm:grid-cols-3">
              {results.map((asset) => (
                <figure className="rounded-md border border-studio-line p-3" key={asset.id}>
                  <img
                    alt={`Result ${asset.asset_type}`}
                    className="h-28 w-full rounded-md object-cover"
                    src={api.getAssetFileUrl(asset.id)}
                  />
                  <figcaption className="mt-2 break-all text-xs text-studio-muted">
                    {asset.asset_type} / {asset.source}
                  </figcaption>
                </figure>
              ))}
              {results.length === 0 ? <p className="text-sm text-studio-muted">No result assets.</p> : null}
            </div>
          </aside>
        ) : null}
      </div>
    </section>
  );
}
