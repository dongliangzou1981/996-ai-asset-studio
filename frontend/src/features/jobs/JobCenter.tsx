"use client";

import { useEffect, useState } from "react";

import { GenerationJob, studioApi } from "@/lib/api";

type JobApi = Pick<typeof studioApi, "listGenerationJobs">;

export function JobCenter({ api = studioApi }: { api?: JobApi }) {
  const [jobs, setJobs] = useState<GenerationJob[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listGenerationJobs()
      .then((result) => setJobs(result.items))
      .catch(() => setError("任务列表加载失败"));
  }, [api]);

  return (
    <section className="rounded-md border border-studio-line bg-white p-5">
      <h2 className="text-lg font-semibold">任务中心</h2>
      <p className="mt-2 text-sm text-studio-muted">Sprint 3 只展示任务状态，不接入 AI 生成队列。</p>
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      <div className="mt-4 grid gap-3">
        {jobs.map((job) => (
          <article className="rounded-md border border-studio-line p-4" key={job.id}>
            <div className="grid gap-3 sm:grid-cols-[1.2fr_0.8fr_0.5fr] sm:items-center">
              <div>
                <h3 className="font-semibold">{job.job_type}</h3>
                <p className="mt-1 break-all font-mono text-xs text-studio-muted">{job.id}</p>
              </div>
              <div className="text-sm text-studio-muted">{job.status}</div>
              <div className="text-sm font-semibold">{job.progress}%</div>
            </div>
          </article>
        ))}
        {jobs.length === 0 ? <p className="text-sm text-studio-muted">暂无生成任务。</p> : null}
      </div>
    </section>
  );
}

