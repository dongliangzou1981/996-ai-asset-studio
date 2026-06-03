"use client";

import { FormEvent, useEffect, useState } from "react";

import { Asset, Project, studioApi } from "@/lib/api";

type AssetApi = Pick<typeof studioApi, "deleteAsset" | "listAssets" | "listProjects" | "uploadAsset">;

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
  const [uploadProjectId, setUploadProjectId] = useState<string | null>(null);
  const [uploadType, setUploadType] = useState<Asset["asset_type"]>("reference_image");
  const [uploadDevice, setUploadDevice] = useState("mobile");
  const [file, setFile] = useState<File | null>(null);
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
    const result = await api.listAssets(projectFilter || undefined, typeFilter || undefined);
    setAssets(result.items);
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
    setFile(null);
  }

  async function deleteAsset(asset: Asset) {
    await api.deleteAsset(asset.id);
    setAssets((items) => items.filter((item) => item.id !== asset.id));
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
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <h3 className="font-semibold">{asset.original_filename}</h3>
                  <p className="mt-1 text-sm text-studio-muted">
                    {asset.asset_type} / {asset.device_type || "unknown"} / {asset.width}x{asset.height}
                  </p>
                  <p className="mt-1 text-sm text-studio-muted">{projectName(asset.project_id)}</p>
                  <p className="mt-2 break-all font-mono text-xs text-studio-muted">{asset.file_path}</p>
                </div>
                <button
                  aria-label={`删除 ${asset.original_filename}`}
                  className="rounded-md border border-red-200 px-3 py-2 text-sm text-red-700"
                  onClick={() => deleteAsset(asset)}
                  type="button"
                >
                  删除
                </button>
              </div>
            </article>
          ))}
          {assets.length === 0 ? <p className="text-sm text-studio-muted">No assets yet.</p> : null}
        </div>
      </div>
    </section>
  );
}

