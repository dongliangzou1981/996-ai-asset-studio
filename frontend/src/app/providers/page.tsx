import { ProviderManager } from "@/features/providers/ProviderManager";

export default function ProvidersPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-studio-muted">Sprint 6+</p>
        <h1 className="mt-2 text-3xl font-bold">提供商管理</h1>
        <p className="mt-2 text-studio-muted">管理 mock、OpenAI、OpenRouter 等提供商配置；真实密钥只允许写入本地环境变量。</p>
      </div>
      <ProviderManager />
    </main>
  );
}
