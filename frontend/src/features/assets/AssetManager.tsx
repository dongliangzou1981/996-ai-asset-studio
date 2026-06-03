"use client";

import { FormEvent, useEffect, useState } from "react";

import { Asset, Project, studioApi } from "@/lib/api";

type AssetApi = Pick<
  typeof studioApi,
  "deleteAsset" | "getAssetFileUrl" | "listAssets" | "listProjects" | "uploadAsset"
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
  const [projectFilter, setProjectFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [jobFilter, setJobFilter] = useState("");
  const [uploadProjectId, setUploadProjectId] = useState<string | null>(null);
  const [uploadType, setUploadType] = useState<Asset["asset_type"]>("reference_image");
  const [uploadDevice, setUploadDevice] = useState("mobile");
  const [file, setFile] = useState<File | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.listProjects(), api.listAssets()])
      .then(([projectResult, assetResult]) => {
        setProjects(projectResult.items);
        setAssets(assetResult.items);
        setUploadProjectId(projectResult.items[0]?.id ?? null);
      })
      .catch(() => setError("Assets failed to load"));
  }, [api]);

  async function applyFilters() {
    const result = await api.listAssets(
      projectFilter || undefined,
      typeFilter || undefined,
      jobFilter || undefined,
    );
    setAssets(result.items);
    setSelectedAsset(null);
  }

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Select a file first");
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
    setFile(null);
  }

  async function deleteAsset(asset: Asset) {
    await api.deleteAsset(asset.id);
    setAssets((items) => items.filter((item) => item.id !== asset.id));
    setSelectedAsset((current) => (current?.id === asset.id ? null : current));
  }

  function projectName(projectId: string | null) {
    if (!projectId) {
      return "Loose asset";
    }
    return projects.find((project) => project.id === projectId)?.name ?? projectId;
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">Asset Upload</h2>
        <div className="mt-4 grid gap-3">
          <label className="grid gap-1 text-sm font-medium">
            项目筛选
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setProjectFilter(event.target.value)}
              value={projectFilter}
            >
              <option value="">All projects</option>
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
              <option value="">All types</option>
              {assetTypes.map((assetType) => (
                <option key={assetType} value={assetType}>
                  {assetType}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Job ID 筛选
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setJobFilter(event.target.value)}
              placeholder="generation_job_id"
              value={jobFilter}
            />
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
              <option value="">Loose asset</option>
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
        <h2 className="text-lg font-semibold">Asset List</h2>
        <div className="mt-4 grid gap-3">
          {assets.map((asset) => (
            <article className="rounded-md border border-studio-line p-4" key={asset.id}>
              <div className="grid gap-3 lg:grid-cols-[96px_1fr_auto] lg:items-start">
                <img
                  alt={`Preview ${asset.original_filename}`}
                  className="h-24 w-24 rounded-md border border-studio-line object-cover"
                  src={api.getAssetFileUrl(asset.id)}
                />
                <div>
                  <h3 className="font-semibold">{asset.original_filename}</h3>
                  <p className="mt-1 text-sm text-studio-muted">
                    {asset.asset_type} / {asset.device_type || "unknown"} / {asset.width}x{asset.height}
                  </p>
                  <p className="mt-1 text-sm text-studio-muted">{projectName(asset.project_id)}</p>
                  <p className="mt-1 text-sm text-studio-muted">
                    Source: {asset.source} / Job: {asset.generation_job_id || "none"}
                  </p>
                  <p className="mt-2 break-all font-mono text-xs text-studio-muted">{asset.file_path}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    aria-label={`查看 ${asset.original_filename}`}
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    onClick={() => setSelectedAsset(asset)}
                    type="button"
                  >
                    查看
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
          ))}
          {assets.length === 0 ? <p className="text-sm text-studio-muted">No assets yet.</p> : null}
        </div>

        {selectedAsset ? (
          <aside className="mt-5 rounded-md border border-studio-line p-4">
            <h3 className="font-semibold">Asset Detail</h3>
            <img
              alt={`Detail ${selectedAsset.original_filename}`}
              className="mt-3 max-h-80 w-full rounded-md border border-studio-line object-contain"
              src={api.getAssetFileUrl(selectedAsset.id)}
            />
            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-medium">Source</dt>
                <dd className="text-studio-muted">{selectedAsset.source}</dd>
              </div>
              <div>
                <dt className="font-medium">Generation Job</dt>
                <dd className="break-all text-studio-muted">{selectedAsset.generation_job_id || "none"}</dd>
              </div>
              <div>
                <dt className="font-medium">Type</dt>
                <dd className="text-studio-muted">{selectedAsset.asset_type}</dd>
              </div>
              <div>
                <dt className="font-medium">Metadata</dt>
                <dd className="break-all text-studio-muted">{selectedAsset.metadata_json || "{}"}</dd>
              </div>
            </dl>
          </aside>
        ) : null}
      </div>
    </section>
  );
}
