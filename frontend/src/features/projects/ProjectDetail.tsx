"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Project, studioApi } from "@/lib/api";

export function ProjectDetail({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    studioApi
      .getProject(projectId)
      .then(setProject)
      .catch(() => setError("项目详情加载失败"));
  }, [projectId]);

  if (error) {
    return <p className="rounded-md border border-red-200 bg-white p-4 text-sm text-red-700">{error}</p>;
  }

  if (!project) {
    return <p className="rounded-md border border-studio-line bg-white p-4 text-sm text-studio-muted">加载中...</p>;
  }

  return (
    <section className="rounded-md border border-studio-line bg-white p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{project.name}</h1>
          <p className="mt-2 text-sm text-studio-muted">{project.description || "暂无描述"}</p>
          <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="font-medium">状态</dt>
              <dd className="text-studio-muted">{project.status}</dd>
            </div>
            <div>
              <dt className="font-medium">项目 ID</dt>
              <dd className="break-all text-studio-muted">{project.id}</dd>
            </div>
            <div>
              <dt className="font-medium">创建时间</dt>
              <dd className="text-studio-muted">{project.created_at}</dd>
            </div>
            <div>
              <dt className="font-medium">更新时间</dt>
              <dd className="text-studio-muted">{project.updated_at}</dd>
            </div>
          </dl>
        </div>
        <Link className="rounded-md border border-studio-line px-4 py-2 text-sm" href="/projects">
          返回项目
        </Link>
      </div>
    </section>
  );
}

