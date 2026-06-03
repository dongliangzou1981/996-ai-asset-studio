"use client";

import { FormEvent, useEffect, useState } from "react";

import { BasePanel, BasePanelInput, Project, studioApi, StyleProfile } from "@/lib/api";

type BasePanelApi = Pick<
  typeof studioApi,
  | "copyBasePanel"
  | "createBasePanel"
  | "deleteBasePanel"
  | "listBasePanels"
  | "listProjects"
  | "listStyleProfiles"
  | "updateBasePanel"
>;

const panelTypes = [
  "main_panel",
  "sub_panel",
  "popup_panel",
  "list_panel",
  "input_panel",
  "button_panel",
  "icon_panel",
] as const;

const emptyForm: BasePanelInput = {
  project_id: "",
  style_profile_id: "",
  panel_type: "main_panel",
  device_type: "mobile",
  width: 1080,
  height: 1920,
  texture: "",
  border_style: "",
  background_style: "",
  color_scheme: "",
};

export function BasePanelManager({ api = studioApi }: { api?: BasePanelApi }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [styles, setStyles] = useState<StyleProfile[]>([]);
  const [panels, setPanels] = useState<BasePanel[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<BasePanelInput>(emptyForm);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.listProjects(), api.listStyleProfiles(), api.listBasePanels()])
      .then(([projectResult, styleResult, panelResult]) => {
        setProjects(projectResult.items);
        setStyles(styleResult.items);
        setPanels(panelResult.items);
        setForm((current) => ({
          ...current,
          project_id: current.project_id || projectResult.items[0]?.id || "",
          style_profile_id: current.style_profile_id || styleResult.items[0]?.id || "",
        }));
      })
      .catch(() => setError("基础面板加载失败"));
  }, [api]);

  async function submitPanel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const payload = { ...form, width: Number(form.width), height: Number(form.height) };

    if (editingId) {
      const updated = await api.updateBasePanel(editingId, payload);
      setPanels((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setEditingId(null);
      return;
    }

    const created = await api.createBasePanel(payload);
    setPanels((items) => [...items, created]);
  }

  function startEditing(panel: BasePanel) {
    setEditingId(panel.id);
    setForm({
      project_id: panel.project_id,
      style_profile_id: panel.style_profile_id,
      panel_type: panel.panel_type,
      device_type: panel.device_type,
      width: panel.width,
      height: panel.height,
      texture: panel.texture,
      border_style: panel.border_style,
      background_style: panel.background_style,
      color_scheme: panel.color_scheme,
    });
  }

  async function copyPanel(panel: BasePanel) {
    const copied = await api.copyBasePanel(panel.id);
    setPanels((items) => [...items, copied]);
  }

  async function deletePanel(panel: BasePanel) {
    await api.deleteBasePanel(panel.id);
    setPanels((items) => items.filter((item) => item.id !== panel.id));
    if (editingId === panel.id) {
      setEditingId(null);
    }
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <form className="rounded-md border border-studio-line bg-white p-5" onSubmit={submitPanel}>
        <h2 className="text-lg font-semibold">{editingId ? "编辑基础面板" : "创建基础面板"}</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label className="grid gap-1 text-sm font-medium">
            所属项目
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, project_id: event.target.value })}
              required
              value={form.project_id}
            >
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            风格资料
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, style_profile_id: event.target.value })}
              required
              value={form.style_profile_id}
            >
              {styles.map((style) => (
                <option key={style.id} value={style.id}>
                  {style.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            面板类型
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) =>
                setForm({ ...form, panel_type: event.target.value as BasePanelInput["panel_type"] })
              }
              value={form.panel_type}
            >
              {panelTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            设备类型
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, device_type: event.target.value })}
              value={form.device_type}
            >
              <option value="mobile">mobile</option>
              <option value="tablet">tablet</option>
              <option value="desktop">desktop</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            宽度
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              min={1}
              onChange={(event) => setForm({ ...form, width: Number(event.target.value) })}
              type="number"
              value={form.width}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            高度
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              min={1}
              onChange={(event) => setForm({ ...form, height: Number(event.target.value) })}
              type="number"
              value={form.height}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            纹理
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, texture: event.target.value })}
              value={form.texture}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            边框样式
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, border_style: event.target.value })}
              value={form.border_style}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            背景样式
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, background_style: event.target.value })}
              value={form.background_style}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            配色方案
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, color_scheme: event.target.value })}
              value={form.color_scheme}
            />
          </label>
        </div>
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        <div className="mt-5 flex gap-2">
          <button className="rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white" type="submit">
            {editingId ? "保存面板" : "创建面板"}
          </button>
          {editingId ? (
            <button
              className="rounded-md border border-studio-line px-4 py-2 text-sm"
              onClick={() => setEditingId(null)}
              type="button"
            >
              取消
            </button>
          ) : null}
        </div>
      </form>

      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">基础面板列表</h2>
        <div className="mt-4 grid gap-3">
          {panels.map((panel) => (
            <article className="rounded-md border border-studio-line p-4" key={panel.id}>
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <h3 className="font-semibold">{panel.panel_type}</h3>
                  <p className="mt-1 text-sm text-studio-muted">
                    {panel.device_type} / {panel.width}x{panel.height}
                  </p>
                  <p className="mt-2 break-all font-mono text-xs text-studio-muted">{panel.id}</p>
                  <p className="mt-2 text-xs text-studio-muted">
                    {panel.texture || "no texture"} · {panel.border_style || "no border"} ·{" "}
                    {panel.background_style || "no background"} · {panel.color_scheme || "no colors"}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    aria-label={`编辑 ${panel.panel_type} ${panel.id}`}
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    onClick={() => startEditing(panel)}
                    type="button"
                  >
                    编辑
                  </button>
                  <button
                    aria-label={`复制 ${panel.panel_type} ${panel.id}`}
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    onClick={() => copyPanel(panel)}
                    type="button"
                  >
                    复制
                  </button>
                  <button
                    aria-label={`删除 ${panel.panel_type} ${panel.id}`}
                    className="rounded-md border border-red-200 px-3 py-2 text-sm text-red-700"
                    onClick={() => deletePanel(panel)}
                    type="button"
                  >
                    删除
                  </button>
                </div>
              </div>
            </article>
          ))}
          {panels.length === 0 ? <p className="text-sm text-studio-muted">还没有基础面板。</p> : null}
        </div>
      </div>
    </section>
  );
}
