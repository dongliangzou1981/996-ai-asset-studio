import Link from "next/link";

import { AssetManager } from "@/features/assets/AssetManager";

export default function AssetsPage() {
  return (
    <main className="min-h-screen px-6 py-6 text-studio-ink sm:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-3 border-b border-studio-line pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">素材管理</h1>
            <p className="mt-2 text-sm text-studio-muted">上传、筛选、预览和处理项目素材。</p>
          </div>
          <Link className="rounded-md border border-studio-line bg-white px-4 py-2 text-sm" href="/">
            返回首页
          </Link>
        </header>
        <AssetManager />
      </div>
    </main>
  );
}
