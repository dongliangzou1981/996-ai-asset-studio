import Link from "next/link";

const tables = [
  "projects",
  "style_profiles",
  "base_panels",
  "reference_images",
  "ui_screens",
  "assets",
  "exports",
  "generation_jobs",
  "ai_providers",
];

const milestones = ["项目与风格 CRUD", "基础面板系统", "素材与参考图管理", "Mock AI Pipeline", "统一 Job Runner"];

export default function Home() {
  return (
    <main className="min-h-screen px-6 py-6 text-studio-ink sm:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-4 border-b border-studio-line pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold leading-tight sm:text-3xl">996 AI Asset Studio</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-studio-muted">
              面向 996 美术资源生成的本地工作台，覆盖项目、风格、基础面板、素材、任务和提供商配置。
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link className="rounded-md bg-studio-action px-4 py-3 text-sm font-semibold text-white" href="/projects">
              项目管理
            </Link>
            <Link className="rounded-md border border-studio-line bg-white px-4 py-3 text-sm font-semibold" href="/styles">
              风格管理
            </Link>
            <Link className="rounded-md border border-studio-line bg-white px-4 py-3 text-sm font-semibold" href="/panels">
              基础面板
            </Link>
            <Link className="rounded-md border border-studio-line bg-white px-4 py-3 text-sm font-semibold" href="/assets">
              素材管理
            </Link>
            <Link className="rounded-md border border-studio-line bg-white px-4 py-3 text-sm font-semibold" href="/job-center">
              任务中心
            </Link>
            <Link className="rounded-md border border-studio-line bg-white px-4 py-3 text-sm font-semibold" href="/providers">
              提供商管理
            </Link>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-5">
          {milestones.map((milestone, index) => (
            <div className="rounded-md border border-studio-line bg-white p-4" key={milestone}>
              <div className="text-xs font-medium uppercase text-studio-muted">Sprint {index + 2}</div>
              <div className="mt-2 text-sm font-semibold">{milestone}</div>
            </div>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-md border border-studio-line bg-white p-5">
            <h2 className="text-lg font-semibold">数据库表</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {tables.map((table) => (
                <div className="rounded-md border border-studio-line px-3 py-2 text-sm" key={table}>
                  {table}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-md border border-studio-line bg-white p-5">
            <h2 className="text-lg font-semibold">后端入口</h2>
            <dl className="mt-4 space-y-3 text-sm">
              <div>
                <dt className="font-medium">GET /health</dt>
                <dd className="text-studio-muted">健康检查</dd>
              </div>
              <div>
                <dt className="font-medium">GET /schema/tables</dt>
                <dd className="text-studio-muted">查看数据库表</dd>
              </div>
              <div>
                <dt className="font-medium">GET /docs</dt>
                <dd className="text-studio-muted">FastAPI Swagger 文档</dd>
              </div>
            </dl>
          </div>
        </section>
      </div>
    </main>
  );
}
