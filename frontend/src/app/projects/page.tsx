import Link from "next/link";

import { ProjectManager } from "@/features/projects/ProjectManager";

export default function ProjectsPage() {
  return (
    <main className="min-h-screen px-6 py-6 text-studio-ink sm:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-3 border-b border-studio-line pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">项目管理</h1>
            <p className="mt-2 text-sm text-studio-muted">创建、查看、编辑和删除 996 美术资产项目。</p>
          </div>
          <Link className="rounded-md border border-studio-line bg-white px-4 py-2 text-sm" href="/">
            返回首页
          </Link>
        </header>
        <ProjectManager />
      </div>
    </main>
  );
}

