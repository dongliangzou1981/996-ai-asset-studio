import Link from "next/link";

const tables = [
  "projects",
  "style_profiles",
  "base_panels",
  "reference_images",
  "ui_screens",
  "assets",
  "exports",
];

const milestones = [
  "项目骨架",
  "文档体系",
  "前端框架",
  "后端框架",
  "数据库结构",
];

export default function Home() {
  return (
    <main className="min-h-screen px-6 py-6 text-studio-ink sm:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-4 border-b border-studio-line pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold leading-tight sm:text-3xl">
              996 AI Asset Studio
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-studio-muted">
              Sprint 1 初始化工作台：项目结构、文档、前端、后端和数据库表结构已进入可验证状态。
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
            <Link className="rounded-md border border-studio-line bg-white px-4 py-3 text-sm font-semibold" href="/job-center">
              Job Center
            </Link>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-5">
          {milestones.map((milestone) => (
            <div
              className="rounded-md border border-studio-line bg-white p-4"
              key={milestone}
            >
              <div className="text-xs font-medium uppercase text-studio-muted">
                Sprint 1
              </div>
              <div className="mt-2 text-sm font-semibold">{milestone}</div>
            </div>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-md border border-studio-line bg-white p-5">
            <h2 className="text-lg font-semibold">数据库表结构</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {tables.map((table) => (
                <div
                  className="rounded-md border border-studio-line px-3 py-2 text-sm"
                  key={table}
                >
                  {table}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-md border border-studio-line bg-white p-5">
            <h2 className="text-lg font-semibold">后端接口</h2>
            <dl className="mt-4 space-y-3 text-sm">
              <div>
                <dt className="font-medium">GET /health</dt>
                <dd className="text-studio-muted">服务健康检查</dd>
              </div>
              <div>
                <dt className="font-medium">GET /schema/tables</dt>
                <dd className="text-studio-muted">核心表清单</dd>
              </div>
            </dl>
          </div>
        </section>
      </div>
    </main>
  );
}
