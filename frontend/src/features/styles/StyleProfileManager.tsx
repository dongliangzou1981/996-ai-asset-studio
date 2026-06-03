"use client";

import { FormEvent, useEffect, useState } from "react";

import { Project, studioApi, StyleProfile, StyleProfileInput } from "@/lib/api";

type StyleProfileApi = Pick<
  typeof studioApi,
  | "createStyleProfile"
  | "deleteStyleProfile"
  | "listProjects"
  | "listStyleProfiles"
  | "updateStyleProfile"
>;

const emptyForm: StyleProfileInput = {
  project_id: "",
  name: "",
  description: "",
  palette_json: "",
  prompt_notes: "",
};

export function StyleProfileManager({ api = studioApi }: { api?: StyleProfileApi }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [styles, setStyles] = useState<StyleProfile[]>([]);
  const [selectedStyleName, setSelectedStyleName] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<StyleProfileInput>(emptyForm);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.listProjects(), api.listStyleProfiles()])
      .then(([projectResult, styleResult]) => {
        setProjects(projectResult.items);
        setStyles(styleResult.items);
        if (!form.project_id && projectResult.items[0]) {
          setForm((current) => ({ ...current, project_id: projectResult.items[0].id }));
        }
      })
      .catch(() => setError("风格资料加载失败"));
  }, [api, form.project_id]);

  async function submitStyle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (editingId) {
      const updated = await api.updateStyleProfile(editingId, form);
      setStyles((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setEditingId(null);
      setForm({ ...emptyForm, project_id: form.project_id });
      return;
    }

    const created = await api.createStyleProfile(form);
    setStyles((items) => [...items, created]);
    setForm({ ...emptyForm, project_id: form.project_id });
  }

  function startEditing(style: StyleProfile) {
    setEditingId(style.id);
    setForm({
      project_id: style.project_id,
      name: style.name,
      description: style.description,
      palette_json: style.palette_json,
      prompt_notes: style.prompt_notes,
    });
  }

  async function removeStyle(style: StyleProfile) {
    await api.deleteStyleProfile(style.id);
    setStyles((items) => items.filter((item) => item.id !== style.id));
    if (selectedStyleName === style.name) {
      setSelectedStyleName("");
    }
    if (editingId === style.id) {
      setEditingId(null);
      setForm({ ...emptyForm, project_id: form.project_id });
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
      <form className="rounded-md border border-studio-line bg-white p-5" onSubmit={submitStyle}>
        <h2 className="text-lg font-semibold">{editingId ? "编辑风格" : "创建风格"}</h2>
        <div className="mt-4 grid gap-3">
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
            风格名称
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              required
              value={form.name}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            风格描述
            <textarea
              className="min-h-20 rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              value={form.description}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            色板 JSON
            <textarea
              className="min-h-20 rounded-md border border-studio-line px-3 py-2 font-mono text-xs"
              onChange={(event) => setForm({ ...form, palette_json: event.target.value })}
              value={form.palette_json}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Prompt 备注
            <textarea
              className="min-h-20 rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, prompt_notes: event.target.value })}
              value={form.prompt_notes}
            />
          </label>
        </div>
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        <div className="mt-5 flex gap-2">
          <button className="rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white" type="submit">
            {editingId ? "保存风格" : "创建风格"}
          </button>
          {editingId ? (
            <button
              className="rounded-md border border-studio-line px-4 py-2 text-sm"
              onClick={() => {
                setEditingId(null);
                setForm({ ...emptyForm, project_id: form.project_id });
              }}
              type="button"
            >
              取消
            </button>
          ) : null}
        </div>
      </form>

      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">风格模板列表</h2>
        <p className="mt-2 text-sm text-studio-muted">
          {selectedStyleName ? `当前选择：${selectedStyleName}` : "当前选择：未选择"}
        </p>
        <div className="mt-4 grid gap-3">
          {styles.map((style) => (
            <article className="rounded-md border border-studio-line p-4" key={style.id}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="font-semibold">{style.name}</h3>
                  <p className="mt-1 text-sm text-studio-muted">{style.description || "暂无描述"}</p>
                  <p className="mt-2 break-all font-mono text-xs text-studio-muted">{style.palette_json || "{}"}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    aria-label={`选择 ${style.name}`}
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    onClick={() => setSelectedStyleName(style.name)}
                    type="button"
                  >
                    选择
                  </button>
                  <button
                    aria-label={`编辑 ${style.name}`}
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    onClick={() => startEditing(style)}
                    type="button"
                  >
                    编辑
                  </button>
                  <button
                    aria-label={`删除 ${style.name}`}
                    className="rounded-md border border-red-200 px-3 py-2 text-sm text-red-700"
                    onClick={() => removeStyle(style)}
                    type="button"
                  >
                    删除
                  </button>
                </div>
              </div>
            </article>
          ))}
          {styles.length === 0 ? <p className="text-sm text-studio-muted">还没有风格模板。</p> : null}
        </div>
      </div>
    </section>
  );
}

