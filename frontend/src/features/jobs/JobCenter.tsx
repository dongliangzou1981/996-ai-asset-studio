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
      .catch(() => setError("任务加载失败"));
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
    return projects.find((project) => project.id === projectId)?.name ?? String(projectId || "无");
  }

  function styleName(styleProfileId: unknown) {
    return styleProfiles.find((style) => style.id === styleProfileId)?.name ?? String(styleProfileId || "无");
  }

  function panelName(basePanelId: unknown) {
    const panel = basePanels.find((item) => item.id === basePanelId);
    return panel ? `${panel.panel_type} / ${panel.device_type} / ${panel.width}x${panel.height}` : String(basePanelId || "无");
  }

  function referenceName(referenceImageId: unknown) {
    return referenceImages.find((asset) => asset.id === referenceImageId)?.original_filename ?? String(referenceImageId || "无");
  }

  const filteredStyles = styleProfiles.filter((style) => !realProjectId || style.project_id === realProjectId);
  const filteredPanels = basePanels.filter((panel) => !realProjectId || panel.project_id === realProjectId);
  const filteredReferences = referenceImages.filter((asset) => !realProjectId || asset.project_id === realProjectId);
  const selectedJobInput = jobInput(selectedJob);

  return (
    <section className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">任务中心</h2>
        <p className="mt-2 text-sm text-studio-muted">Sprint 5 使用本地模拟流水线，当前不会连接真实 AI 模型。</p>

        <form className="mt-5 grid gap-3" onSubmit={createMockJob}>
          <label className="grid gap-1 text-sm font-medium">
            模拟项目
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setMockProjectId(event.target.value || null)}
              value={mockProjectId ?? ""}
            >
              <option value="">零散模拟任务</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            模拟设备
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
              模拟宽度
              <input
                className="rounded-md border border-studio-line px-3 py-2 font-normal"
                min={1}
                onChange={(event) => setMockWidth(Number(event.target.value))}
                type="number"
                value={mockWidth}
              />
            </label>
            <label className="grid gap-1 text-sm font-medium">
              模拟高度
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
            创建模拟UI任务
          </button>
        </form>

        <form className="mt-6 grid gap-3 border-t border-studio-line pt-5" onSubmit={createRealJob}>
          <h3 className="text-sm font-semibold">生成向导</h3>
          <label className="grid gap-1 text-sm font-medium">
            <span>步骤 1：选择项目</span>
            真实项目
            <select
              aria-label="真实项目"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => updateRealProject(event.target.value || null)}
              value={realProjectId ?? ""}
            >
              <option value="">零散真实任务</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            <span>步骤 2：选择风格</span>
            真实风格
            <select
              aria-label="真实风格"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setRealStyleProfileId(event.target.value || null)}
              value={realStyleProfileId ?? ""}
            >
              <option value="">不选择风格</option>
              {filteredStyles.map((style) => (
                <option key={style.id} value={style.id}>
                  {style.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            <span>步骤 3：选择基础面板</span>
            真实基础面板
            <select
              aria-label="真实基础面板"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setRealBasePanelId(event.target.value || null)}
              value={realBasePanelId ?? ""}
            >
              <option value="">不选择基础面板</option>
              {filteredPanels.map((panel) => (
                <option key={panel.id} value={panel.id}>
                  {panel.panel_type} / {panel.device_type} / {panel.width}x{panel.height}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            <span>步骤 4：选择参考图</span>
            真实参考图
            <select
              aria-label="真实参考图"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setRealReferenceImageId(event.target.value || null)}
              value={realReferenceImageId ?? ""}
            >
              <option value="">不选择参考图</option>
              {filteredReferences.map((asset) => (
                <option key={asset.id} value={asset.id}>
                  {asset.original_filename}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            真实提供商
            <select
              aria-label="真实提供商"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setRealProviderId(event.target.value || null)}
              value={realProviderId ?? ""}
            >
              <option value="">默认提供商</option>
              {providers.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.name} / {provider.type}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            <span>步骤 5：输入 Prompt</span>
            Prompt
            <textarea
              aria-label="Prompt"
              className="min-h-20 rounded-md border border-studio-line px-3 py-2 text-sm font-normal"
              onChange={(event) => setRealPrompt(event.target.value)}
              value={realPrompt}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            真实设备
            <select
              aria-label="真实设备"
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
              真实宽度
              <input
                aria-label="真实宽度"
                className="rounded-md border border-studio-line px-3 py-2 font-normal"
                min={1}
                onChange={(event) => setRealWidth(Number(event.target.value))}
                type="number"
                value={realWidth}
              />
            </label>
            <label className="grid gap-1 text-sm font-medium">
              真实高度
              <input
                aria-label="真实高度"
                className="rounded-md border border-studio-line px-3 py-2 font-normal"
                min={1}
                onChange={(event) => setRealHeight(Number(event.target.value))}
                type="number"
                value={realHeight}
              />
            </label>
          </div>
          <button className="rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white" type="submit">
            创建真实UI任务
          </button>
          <p className="text-sm font-semibold">步骤 6：创建真实UI任务</p>
        </form>

        <form className="mt-6 grid gap-3 border-t border-studio-line pt-5" onSubmit={createJob}>
          <label className="grid gap-1 text-sm font-medium">
            提供商
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setProviderId(event.target.value || null)}
              value={providerId ?? ""}
            >
              <option value="">默认提供商</option>
              {providers.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.name} / {provider.type}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            任务类型
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
            创建测试任务
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </div>

      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">任务列表</h2>
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
                    aria-label={`查看 ${job.job_type}`}
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    onClick={() => viewJob(job)}
                    type="button"
                  >
                    查看
                  </button>
                  {job.job_type === "mock_ui_generation" && job.status !== "completed" ? (
                    <button
                      aria-label={`运行模拟生成 ${job.job_type}`}
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      onClick={() => runMock(job)}
                      type="button"
                    >
                      运行模拟生成
                    </button>
                  ) : null}
                  {job.job_type !== "mock_ui_generation" && job.status !== "completed" ? (
                    <button
                      aria-label={`运行任务 ${job.job_type}`}
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      onClick={() => runJob(job)}
                      type="button"
                    >
                      运行任务
                    </button>
                  ) : null}
                  {job.status === "failed" ? (
                    <button
                      aria-label={`重试 ${job.job_type}`}
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      onClick={() => retryJob(job)}
                      type="button"
                    >
                      重试
                    </button>
                  ) : null}
                </div>
              </div>
            </article>
          ))}
          {jobs.length === 0 ? <p className="text-sm text-studio-muted">暂无任务。</p> : null}
        </div>

        {selectedJob ? (
          <aside className="mt-5 rounded-md border border-studio-line p-4">
            <h3 className="font-semibold">任务详情</h3>
            <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-medium">状态</dt>
                <dd className="text-studio-muted">{selectedJob.status}</dd>
              </div>
              <div>
                <dt className="font-medium">重试次数</dt>
                <dd className="text-studio-muted">{selectedJob.retry_count}</dd>
              </div>
              <div>
                <dt className="font-medium">错误</dt>
                <dd className="text-studio-muted">{selectedJob.error_message || "无"}</dd>
              </div>
              <div>
                <dt className="font-medium">输入</dt>
                <dd className="break-all text-studio-muted">{selectedJob.input_json || "{}"}</dd>
              </div>
              <div>
                <dt className="font-medium">项目</dt>
                <dd className="text-studio-muted">项目：{projectName(selectedJobInput.project_id)}</dd>
              </div>
              <div>
                <dt className="font-medium">风格</dt>
                <dd className="text-studio-muted">风格：{styleName(selectedJobInput.style_profile_id)}</dd>
              </div>
              <div>
                <dt className="font-medium">基础面板</dt>
                <dd className="text-studio-muted">基础面板：{panelName(selectedJobInput.base_panel_id)}</dd>
              </div>
              <div>
                <dt className="font-medium">参考图</dt>
                <dd className="text-studio-muted">参考图：{referenceName(selectedJobInput.reference_image_id)}</dd>
              </div>
              <div>
                <dt className="font-medium">Prompt</dt>
                <dd className="text-studio-muted">Prompt：{String(selectedJobInput.prompt || "无")}</dd>
              </div>
            </dl>
            <h4 className="mt-4 text-sm font-semibold">日志时间线</h4>
            <pre className="mt-2 whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-xs text-studio-ink">
              {selectedJob.logs || "暂无日志"}
            </pre>
            <h4 className="mt-4 text-sm font-semibold">结果素材</h4>
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
              {results.length === 0 ? <p className="text-sm text-studio-muted">暂无结果素材。</p> : null}
            </div>
          </aside>
        ) : null}
      </div>
    </section>
  );
}
