"use client";

import { FormEvent, useEffect, useState } from "react";

import { GenerationJob, studioApi } from "@/lib/api";

type JobApi = Pick<typeof studioApi, "createGenerationJob" | "listGenerationJobs" | "retryGenerationJob">;

export function JobCenter({ api = studioApi }: { api?: JobApi }) {
  const [jobs, setJobs] = useState<GenerationJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<GenerationJob | null>(null);
  const [jobType, setJobType] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listGenerationJobs()
      .then((result) => setJobs(result.items))
      .catch(() => setError("Jobs failed to load"));
  }, [api]);

  async function createJob(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const created = await api.createGenerationJob({
      project_id: null,
      job_type: jobType,
      status: "pending",
      progress: 0,
      input_json: "{}",
      output_json: "",
      error_message: "",
      logs: "queued",
    });
    setJobs((items) => [created, ...items]);
    setJobType("");
  }

  async function retryJob(job: GenerationJob) {
    const retried = await api.retryGenerationJob(job.id);
    setJobs((items) => items.map((item) => (item.id === retried.id ? retried : item)));
    setSelectedJob(retried);
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">Job Center</h2>
        <p className="mt-2 text-sm text-studio-muted">Sprint 4 tracks mock job state. No real AI model is connected.</p>
        <form className="mt-5 grid gap-3" onSubmit={createJob}>
          <label className="grid gap-1 text-sm font-medium">
            Job type
            <input
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setJobType(event.target.value)}
              required
              value={jobType}
            />
          </label>
          <button className="rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white" type="submit">
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
                    onClick={() => setSelectedJob(job)}
                    type="button"
                  >
                    View
                  </button>
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
            </dl>
            <pre className="mt-4 whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-xs text-studio-ink">
              {selectedJob.logs || "No logs"}
            </pre>
          </aside>
        ) : null}
      </div>
    </section>
  );
}

