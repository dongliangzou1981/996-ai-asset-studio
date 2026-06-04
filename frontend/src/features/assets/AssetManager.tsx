"use client";

import { FormEvent, useEffect, useState } from "react";

import { Asset, BasePanel, ComponentProcessingResult, Project, StyleProfile, studioApi } from "@/lib/api";

type AssetApi = Pick<
  typeof studioApi,
  | "deleteAsset"
  | "getAssetFileUrl"
  | "getAssetThumbnailUrl"
  | "listAssets"
  | "listBasePanels"
  | "listProjects"
  | "listStyleProfiles"
  | "processAssetComponents"
  | "uploadAsset"
>;

const assetTypes = [
  "reference_image",
  "ui_preview",
  "annotated_preview",
  "sliced_component",
  "base_panel",
  "icon",
] as const;

export function AssetManager({ api = studioApi }: { api?: AssetApi }) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [styleProfiles, setStyleProfiles] = useState<StyleProfile[]>([]);
  const [basePanels, setBasePanels] = useState<BasePanel[]>([]);
  const [projectFilter, setProjectFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [deviceFilter, setDeviceFilter] = useState("");
  const [jobFilter, setJobFilter] = useState("");
  const [uploadProjectId, setUploadProjectId] = useState<string | null>(null);
  const [uploadType, setUploadType] = useState<Asset["asset_type"]>("reference_image");
  const [uploadDevice, setUploadDevice] = useState("mobile");
  const [file, setFile] = useState<File | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [componentResult, setComponentResult] = useState<ComponentProcessingResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.listProjects(), api.listStyleProfiles(), api.listBasePanels(), api.listAssets()])
      .then(([projectResult, styleResult, panelResult, assetResult]) => {
        setProjects(projectResult.items);
        setStyleProfiles(styleResult.items);
        setBasePanels(panelResult.items);
        setAssets(assetResult.items);
        setUploadProjectId(projectResult.items[0]?.id ?? null);
      })
      .catch(() => setError("素材加载失败"));
  }, [api]);

  async function applyFilters() {
    const result = await api.listAssets(
      projectFilter || undefined,
      typeFilter || undefined,
      deviceFilter || undefined,
      jobFilter || undefined,
    );
    setAssets(result.items);
    setSelectedAsset(null);
    setComponentResult(null);
  }

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("请先选择文件");
      return;
    }
    setError("");
    const created = await api.uploadAsset({
      file,
      project_id: uploadProjectId,
      asset_type: uploadType,
      device_type: uploadDevice,
    });
    setAssets((items) => [created, ...items]);
    setSelectedAsset(created);
    setComponentResult(null);
    setFile(null);
  }

  async function deleteAsset(asset: Asset) {
    await api.deleteAsset(asset.id);
    setAssets((items) => items.filter((item) => item.id !== asset.id));
    setSelectedAsset((current) => (current?.id === asset.id ? null : current));
  }

  async function processComponents(asset: Asset) {
    const result = await api.processAssetComponents(asset.id);
    setComponentResult(result);
  }

  async function copyPath(asset: Asset) {
    await navigator.clipboard?.writeText(asset.file_path);
  }

  function projectName(projectId: string | null) {
    if (!projectId) {
      return "零散素材";
    }
    return projects.find((project) => project.id === projectId)?.name ?? projectId;
  }

  function metadata(asset: Asset): Record<string, unknown> {
    try {
      const parsed = JSON.parse(asset.metadata_json || "{}");
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch {
      return {};
    }
  }

  function styleName(styleProfileId: unknown) {
    return styleProfiles.find((style) => style.id === styleProfileId)?.name ?? String(styleProfileId || "无");
  }

  function panelName(basePanelId: unknown) {
    const panel = basePanels.find((item) => item.id === basePanelId);
    return panel ? `${panel.panel_type} / ${panel.device_type} / ${panel.width}x${panel.height}` : String(basePanelId || "无");
  }

  function sourceDetails(asset: Asset) {
    const data = metadata(asset);
    return {
      project: projectName(String(data.project_id || asset.project_id || "")),
      style: styleName(data.style_profile_id),
      panel: panelName(data.base_panel_id),
      prompt: String(data.prompt || "无"),
    };
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">素材上传</h2>
        <div className="mt-4 grid gap-3">
          <label className="grid gap-1 text-sm font-medium">
            项目筛选
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setProjectFilter(event.target.value)}
              value={projectFilter}
            >
              <option value="">全部项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            类型筛选
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setTypeFilter(event.target.value)}
              value={typeFilter}
            >
              <option value="">全部类型</option>
              {assetTypes.map((assetType) => (
                <option key={assetType} value={assetType}>
                  {assetType}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            任务 ID 筛选
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setJobFilter(event.target.value)}
              placeholder="generation_job_id"
              value={jobFilter}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            设备筛选
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setDeviceFilter(event.target.value)}
              value={deviceFilter}
            >
              <option value="">全部设备</option>
              <option value="pc">pc</option>
              <option value="mobile">mobile</option>
              <option value="both">both</option>
              <option value="tablet">tablet</option>
              <option value="desktop">desktop</option>
            </select>
          </label>
          <button
            className="rounded-md border border-studio-line px-4 py-2 text-sm font-semibold"
            onClick={applyFilters}
            type="button"
          >
            应用筛选
          </button>
        </div>

        <form className="mt-6 grid gap-3 border-t border-studio-line pt-5" onSubmit={upload}>
          <label className="grid gap-1 text-sm font-medium">
            上传文件
            <input
              accept=".png,.jpg,.jpeg,.webp"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              type="file"
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            上传项目
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setUploadProjectId(event.target.value || null)}
              value={uploadProjectId ?? ""}
            >
              <option value="">零散素材</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            上传类型
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setUploadType(event.target.value as Asset["asset_type"])}
              value={uploadType}
            >
              {assetTypes.map((assetType) => (
                <option key={assetType} value={assetType}>
                  {assetType}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            上传设备
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setUploadDevice(event.target.value)}
              value={uploadDevice}
            >
              <option value="mobile">mobile</option>
              <option value="tablet">tablet</option>
              <option value="desktop">desktop</option>
            </select>
          </label>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <button className="rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white" type="submit">
            上传素材
          </button>
        </form>
      </div>

      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">素材列表</h2>
        <div className="mt-4 grid gap-3">
          {assets.map((asset) => {
            const details = sourceDetails(asset);
            return (
              <article className="rounded-md border border-studio-line p-4" key={asset.id}>
                <div className="grid gap-3 lg:grid-cols-[96px_1fr_auto] lg:items-start">
                  <img
                    alt={`Preview ${asset.original_filename}`}
                    className="h-24 w-24 rounded-md border border-studio-line object-cover"
                    src={api.getAssetThumbnailUrl(asset.id)}
                  />
                  <div>
                    <h3 className="font-semibold">{asset.original_filename}</h3>
                    <p className="mt-1 text-sm text-studio-muted">
                      {asset.asset_type} / {asset.device_type || "unknown"} / {asset.width}x{asset.height}
                    </p>
                    <p className="mt-1 text-sm text-studio-muted">{projectName(asset.project_id)}</p>
                    <p className="mt-1 text-sm text-studio-muted">
                      来源：{asset.source} / 任务：{asset.generation_job_id || "无"}
                    </p>
                    {asset.source === "real_pipeline_placeholder" || asset.source === "ai_generated" ? (
                      <div className="mt-2 grid gap-1 text-sm text-studio-muted">
                        <p>项目：{details.project}</p>
                        <p>风格：{details.style}</p>
                        <p>基础面板：{details.panel}</p>
                        <p>Prompt：{details.prompt}</p>
                      </div>
                    ) : null}
                    <p className="mt-2 break-all font-mono text-xs text-studio-muted">{asset.file_path}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      aria-label={`查看 ${asset.original_filename}`}
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      onClick={() => {
                        setSelectedAsset(asset);
                        setComponentResult(null);
                      }}
                      type="button"
                    >
                      查看
                    </button>
                    <a
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      download={asset.original_filename}
                      href={api.getAssetFileUrl(asset.id)}
                    >
                      下载
                    </a>
                    <button
                      aria-label={`复制路径 ${asset.original_filename}`}
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      onClick={() => copyPath(asset)}
                      type="button"
                    >
                      复制路径
                    </button>
                    <button
                      aria-label={`删除 ${asset.original_filename}`}
                      className="rounded-md border border-red-200 px-3 py-2 text-sm text-red-700"
                      onClick={() => deleteAsset(asset)}
                      type="button"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
          {assets.length === 0 ? <p className="text-sm text-studio-muted">暂无素材。</p> : null}
        </div>

        {selectedAsset ? (
          <aside className="mt-5 rounded-md border border-studio-line p-4">
            {(() => {
              const details = sourceDetails(selectedAsset);
              return (
                <>
                  <h3 className="font-semibold">素材详情</h3>
                  <img
                    alt={`Detail ${selectedAsset.original_filename}`}
                    className="mt-3 max-h-80 w-full rounded-md border border-studio-line object-contain"
                    src={api.getAssetFileUrl(selectedAsset.id)}
                  />
                  {selectedAsset.asset_type === "ui_preview" ? (
                    <button
                      className="mt-3 rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white"
                      onClick={() => processComponents(selectedAsset)}
                      type="button"
                    >
                      生成组件切图与标注
                    </button>
                  ) : null}
                  {componentResult ? (
                    <div className="mt-3 grid gap-2 rounded-md border border-studio-line p-3 text-sm text-studio-muted">
                      <p className="break-all">{componentResult.manifest_path}</p>
                      <p className="break-all">{componentResult.annotation_path}</p>
                      <p>组件数量：{componentResult.component_asset_ids.length}</p>
                      <a className="font-semibold text-studio-action" href={componentResult.preview_html_path}>
                        preview.html
                      </a>
                    </div>
                  ) : null}
                  <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="font-medium">来源</dt>
                      <dd className="text-studio-muted">{selectedAsset.source}</dd>
                    </div>
                    <div>
                      <dt className="font-medium">生成任务</dt>
                      <dd className="break-all text-studio-muted">{selectedAsset.generation_job_id || "无"}</dd>
                    </div>
                    <div>
                      <dt className="font-medium">缩略图</dt>
                      <dd className="break-all text-studio-muted">{selectedAsset.thumbnail_path || "无"}</dd>
                    </div>
                    <div>
                      <dt className="font-medium">类型</dt>
                      <dd className="text-studio-muted">{selectedAsset.asset_type}</dd>
                    </div>
                    <div>
                      <dt className="font-medium">元数据</dt>
                      <dd className="break-all text-studio-muted">{selectedAsset.metadata_json || "{}"}</dd>
                    </div>
                    <div>
                      <dt className="font-medium">项目</dt>
                      <dd className="text-studio-muted">项目：{details.project}</dd>
                    </div>
                    <div>
                      <dt className="font-medium">风格</dt>
                      <dd className="text-studio-muted">风格：{details.style}</dd>
                    </div>
                    <div>
                      <dt className="font-medium">基础面板</dt>
                      <dd className="text-studio-muted">基础面板：{details.panel}</dd>
                    </div>
                    <div>
                      <dt className="font-medium">Prompt</dt>
                      <dd className="text-studio-muted">Prompt：{details.prompt}</dd>
                    </div>
                  </dl>
                </>
              );
            })()}
          </aside>
        ) : null}
      </div>
    </section>
  );
}
