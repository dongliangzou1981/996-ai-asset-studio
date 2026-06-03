import { ProviderManager } from "@/features/providers/ProviderManager";

export default function ProvidersPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-studio-muted">Sprint 6</p>
        <h1 className="mt-2 text-3xl font-bold">Provider 管理</h1>
        <p className="mt-2 text-studio-muted">配置 mock、OpenAI 或自定义生成模型；真实密钥不写入 .env.local。</p>
      </div>
      <ProviderManager />
    </main>
  );
}
