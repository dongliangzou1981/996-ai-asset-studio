import Link from "next/link";

import { ProjectDetail } from "@/features/projects/ProjectDetail";

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <main className="min-h-screen px-6 py-6 text-studio-ink sm:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="flex items-center justify-between border-b border-studio-line pb-5">
          <Link className="rounded-md border border-studio-line bg-white px-4 py-2 text-sm" href="/projects">
            返回项目列表
          </Link>
        </header>
        <ProjectDetail projectId={id} />
      </div>
    </main>
  );
}

