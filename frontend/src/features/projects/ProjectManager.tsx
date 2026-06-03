"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { Project, ProjectInput, studioApi } from "@/lib/api";

type ProjectApi = Pick<
  typeof studioApi,
  "createProject" | "deleteProject" | "listProjects" | "updateProject"
>;

const emptyForm: ProjectInput = {
  name: "",
  description: "",
  status: "draft",
};

export function ProjectManager({ api = studioApi }: { api?: ProjectApi }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<ProjectInput>(emptyForm);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listProjects()
      .then((result) => setProjects(result.items))
      .catch(() => setError("项目列表加载失败"));
  }, [api]);

  async function submitProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (editingId) {
      const updated = await api.updateProject(editingId, form);
      setProjects((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setEditingId(null);
      setForm(emptyForm);
      return;
    }

    const created = await api.createProject(form);
    setProjects((items) => [...items, created]);
    setForm(emptyForm);
  }

  function startEditing(project: Project) {
    setEditingId(project.id);
    setForm({
      name: project.name,
      description: project.description,
      status: project.status,
    });
  }

  async function removeProject(project: Project) {
    await api.deleteProject(project.id);
    setProjects((items) => items.filter((item) => item.id !== project.id));
    if (editingId === project.id) {
      setEditingId(null);
      setForm(emptyForm);
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
      <form className="rounded-md border border-studio-line bg-white p-5" onSubmit={submitProject}>
        <h2 className="text-lg font-semibold">{editingId ? "编辑项目" : "创建项目"}</h2>
        <div className="mt-4 grid gap-3">
          <label className="grid gap-1 text-sm font-medium">
            项目名称
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              required
              value={form.name}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            项目描述
            <textarea
              className="min-h-24 rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              value={form.description}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            项目状态
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setForm({ ...form, status: event.target.value })}
              value={form.status}
            >
              <option value="draft">draft</option>
              <option value="active">active</option>
              <option value="archived">archived</option>
            </select>
          </label>
        </div>
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        <div className="mt-5 flex gap-2">
          <button className="rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white" type="submit">
            {editingId ? "保存项目" : "创建项目"}
          </button>
          {editingId ? (
            <button
              className="rounded-md border border-studio-line px-4 py-2 text-sm"
              onClick={() => {
                setEditingId(null);
                setForm(emptyForm);
              }}
              type="button"
            >
              取消
            </button>
          ) : null}
        </div>
      </form>

      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">项目列表</h2>
        <div className="mt-4 grid gap-3">
          {projects.map((project) => (
            <article className="rounded-md border border-studio-line p-4" key={project.id}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="font-semibold">{project.name}</h3>
                  <p className="mt-1 text-sm text-studio-muted">{project.description || "暂无描述"}</p>
                  <p className="mt-2 text-xs font-medium text-studio-muted">状态：{project.status}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Link className="rounded-md border border-studio-line px-3 py-2 text-sm" href={`/projects/${project.id}`}>
                    详情
                  </Link>
                  <button
                    aria-label={`编辑 ${project.name}`}
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    onClick={() => startEditing(project)}
                    type="button"
                  >
                    编辑
                  </button>
                  <button
                    aria-label={`删除 ${project.name}`}
                    className="rounded-md border border-red-200 px-3 py-2 text-sm text-red-700"
                    onClick={() => removeProject(project)}
                    type="button"
                  >
                    删除
                  </button>
                </div>
              </div>
            </article>
          ))}
          {projects.length === 0 ? <p className="text-sm text-studio-muted">还没有项目。</p> : null}
        </div>
      </div>
    </section>
  );
}

