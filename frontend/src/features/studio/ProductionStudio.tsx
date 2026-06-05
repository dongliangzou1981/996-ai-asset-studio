"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  ProductionAssetMode,
  ProductionDeviceType,
  ProductionScreenType,
  ProductionStudioResult,
  ProductionStudioStyleCode,
  ProductionStyleSource,
  studioApi,
} from "@/lib/api";

const SCREEN_OPTIONS: { value: ProductionScreenType; label: string }[] = [
  { value: "main_ui", label: "主界面" },
  { value: "role_ui", label: "角色界面" },
  { value: "bag_ui", label: "背包界面" },
  { value: "shop_ui", label: "商城界面" },
  { value: "activity_ui", label: "活动界面" },
];

const SCREEN_LABELS: Record<ProductionScreenType, string> = {
  main_ui: "主界面",
  role_ui: "角色界面",
  bag_ui: "背包界面",
  shop_ui: "商城界面",
  activity_ui: "活动界面",
};

const DEVICE_LABELS: Record<ProductionDeviceType, string> = {
  mobile_landscape: "手机横屏",
  pc_landscape: "电脑端",
};

const ASSET_MODE_LABELS: Record<ProductionAssetMode, string> = {
  resource_production: "资源生产",
  ui_package: "整图预览",
};

const ACCEPTANCE_LABELS = {
  pending: "待验收",
  approved: "验收通过",
  needs_change: "需要修改",
} as const;

type AcceptanceStatus = keyof typeof ACCEPTANCE_LABELS;

type AcceptanceRecord = {
  status: AcceptanceStatus;
  notes: string;
};

type ProductionStudioApi = Pick<
  typeof studioApi,
  "generateProductionStudioPackage" | "getProductionStudioFileUrl" | "listProductionStyleCodes"
>;

function defaultAcceptanceRecord(): AcceptanceRecord {
  return { status: "pending", notes: "" };
}

export function ProductionStudio({ api = studioApi }: { api?: ProductionStudioApi }) {
  const [deviceType, setDeviceType] = useState<ProductionDeviceType>("mobile_landscape");
  const [assetMode, setAssetMode] = useState<ProductionAssetMode>("resource_production");
  const [styleSource, setStyleSource] = useState<ProductionStyleSource>("new_style");
  const [styleCodes, setStyleCodes] = useState<ProductionStudioStyleCode[]>([]);
  const [selectedStyleCode, setSelectedStyleCode] = useState("");
  const [screenTypes, setScreenTypes] = useState<ProductionScreenType[]>(["main_ui"]);
  const [styleName, setStyleName] = useState("暗黑金龙传奇风");
  const [prompt, setPrompt] = useState("手机横屏传奇 UI，暗黑金龙风格，技能栏清晰，右侧菜单明显，整体适合 996 引擎资源生产。");
  const [result, setResult] = useState<ProductionStudioResult | null>(null);
  const [generatedAt, setGeneratedAt] = useState("");
  const [acceptance, setAcceptance] = useState<Record<string, AcceptanceRecord>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listProductionStyleCodes()
      .then((response) => {
        setStyleCodes(response.items);
        setSelectedStyleCode(response.items[0]?.style_code ?? "");
      })
      .catch(() => setError("风格编号加载失败。请先运行 环境检查.ps1，再重新打开工作台。"));
  }, [api]);

  const selectedStyle = useMemo(
    () => styleCodes.find((style) => style.style_code === selectedStyleCode),
    [selectedStyleCode, styleCodes],
  );

  function toggleScreen(screenType: ProductionScreenType) {
    setScreenTypes((items) => {
      if (items.includes(screenType)) {
        const next = items.filter((item) => item !== screenType);
        return next.length ? next : items;
      }
      return [...items, screenType];
    });
  }

  function updateAcceptance(jobId: string, patch: Partial<AcceptanceRecord>) {
    setAcceptance((items) => ({
      ...items,
      [jobId]: {
        ...(items[jobId] ?? defaultAcceptanceRecord()),
        ...patch,
      },
    }));
  }

  async function generate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    setGeneratedAt("");
    setAcceptance({});
    try {
      const response = await api.generateProductionStudioPackage({
        device_type: deviceType,
        asset_mode: assetMode,
        style_source: styleSource,
        style_code: styleSource === "existing_style" ? selectedStyleCode : null,
        screen_types: screenTypes,
        style_name: styleName,
        prompt,
      });
      setResult(response);
      setGeneratedAt(new Date().toLocaleString("zh-CN"));
      setAcceptance(
        Object.fromEntries(response.results.map((item) => [item.generation_job_id, defaultAcceptanceRecord()])),
      );
    } catch {
      setError("生成失败：本地工作台还没有准备好。请关闭旧窗口，在项目根目录运行 启动工作台.ps1，然后重新点击开始生成。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[0.82fr_1.18fr]">
      <form className="grid gap-4 rounded-md border border-studio-line bg-white p-5" onSubmit={generate}>
        <div>
          <h2 className="text-lg font-semibold">生产工作台</h2>
          <p className="mt-2 text-sm leading-6 text-studio-muted">
            选择风格和界面后，系统会生成可验收的 996 美术资源，并在右侧集中展示结果、报告和验收记录。
          </p>
        </div>

        <label className="grid gap-1 text-sm font-medium">
          设备类型
          <select
            className="rounded-md border border-studio-line px-3 py-2 font-normal"
            onChange={(event) => setDeviceType(event.target.value as ProductionDeviceType)}
            value={deviceType}
          >
            <option value="mobile_landscape">手机横屏</option>
            <option value="pc_landscape">电脑端</option>
          </select>
        </label>

        <label className="grid gap-1 text-sm font-medium">
          输出模式
          <select
            className="rounded-md border border-studio-line px-3 py-2 font-normal"
            onChange={(event) => setAssetMode(event.target.value as ProductionAssetMode)}
            value={assetMode}
          >
            <option value="resource_production">资源生产</option>
            <option value="ui_package">整图预览</option>
          </select>
        </label>

        <fieldset className="grid gap-2 rounded-md border border-studio-line p-3">
          <legend className="px-1 text-sm font-medium">风格来源</legend>
          <label className="flex items-center gap-2 text-sm">
            <input
              checked={styleSource === "new_style"}
              name="style_source"
              onChange={() => setStyleSource("new_style")}
              type="radio"
            />
            新建风格
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              checked={styleSource === "existing_style"}
              name="style_source"
              onChange={() => setStyleSource("existing_style")}
              type="radio"
            />
            使用已有风格
          </label>
        </fieldset>

        {styleSource === "existing_style" ? (
          <label className="grid gap-1 text-sm font-medium">
            风格编号
            <select
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={(event) => setSelectedStyleCode(event.target.value)}
              value={selectedStyleCode}
            >
              {styleCodes.map((style) => (
                <option key={style.style_code} value={style.style_code}>
                  {style.style_code}
                </option>
              ))}
            </select>
            <span className="text-xs font-normal text-studio-muted">
              {selectedStyle
                ? `${selectedStyle.style_name} / ${selectedStyle.device_type ? DEVICE_LABELS[selectedStyle.device_type as ProductionDeviceType] ?? selectedStyle.device_type : "未知设备"}`
                : "未选择风格"}
            </span>
          </label>
        ) : null}

        <fieldset className="grid gap-2 rounded-md border border-studio-line p-3">
          <legend className="px-1 text-sm font-medium">界面类型</legend>
          {SCREEN_OPTIONS.map((option) => (
            <label className="flex items-center gap-2 text-sm" key={option.value}>
              <input
                checked={screenTypes.includes(option.value)}
                onChange={() => toggleScreen(option.value)}
                type="checkbox"
              />
              {option.label}
            </label>
          ))}
        </fieldset>

        <label className="grid gap-1 text-sm font-medium">
          风格名称
          <input
            className="rounded-md border border-studio-line px-3 py-2 font-normal"
            onChange={(event) => setStyleName(event.target.value)}
            value={styleName}
          />
        </label>

        <label className="grid gap-1 text-sm font-medium">
          需求描述
          <textarea
            className="min-h-28 rounded-md border border-studio-line px-3 py-2 text-sm font-normal leading-6"
            onChange={(event) => setPrompt(event.target.value)}
            value={prompt}
          />
        </label>

        <button
          className="rounded-md bg-studio-action px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
          disabled={loading || (styleSource === "existing_style" && !selectedStyleCode)}
          type="submit"
        >
          {loading ? "正在生成..." : "开始生成"}
        </button>
        {error ? <p className="text-sm leading-6 text-red-600">{error}</p> : null}
      </form>

      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">结果中心</h2>
        {result ? (
          <div className="mt-4 grid gap-4">
            <div className="grid gap-2 rounded-md border border-studio-line bg-slate-50 p-3 text-sm sm:grid-cols-2">
              <div>
                风格编号：<span className="font-semibold">{result.style_code}</span>
              </div>
              <div>
                生成时间：<span className="font-semibold">{generatedAt}</span>
              </div>
              <div>
                设备类型：<span className="font-semibold">{DEVICE_LABELS[result.device_type]}</span>
              </div>
              <div>
                输出模式：<span className="font-semibold">{ASSET_MODE_LABELS[result.asset_mode]}</span>
              </div>
            </div>

            {result.results.map((item) => {
              const record = acceptance[item.generation_job_id] ?? defaultAcceptanceRecord();
              return (
                <article className="grid gap-3 rounded-md border border-studio-line p-4" key={item.generation_job_id}>
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-semibold">{SCREEN_LABELS[item.screen_type]}</h3>
                      <p className="mt-1 text-xs text-studio-muted">生成编号：{item.generation_job_id}</p>
                    </div>
                    <span className={item.validator_ok ? "text-sm font-semibold text-green-700" : "text-sm font-semibold text-red-700"}>
                      {item.validator_ok ? "验证通过" : "验证未通过"}
                    </span>
                  </div>
                  <img
                    alt={`${SCREEN_LABELS[item.screen_type]}预览图`}
                    className="aspect-video w-full rounded-md border border-studio-line object-cover"
                    src={api.getProductionStudioFileUrl(item.ui_preview_url)}
                  />
                  <dl className="grid gap-2 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="font-medium">组件数量</dt>
                      <dd className="text-studio-muted">{item.components_count}</dd>
                    </div>
                    <div>
                      <dt className="font-medium">候选资源</dt>
                      <dd className="text-studio-muted">{item.candidates_count}</dd>
                    </div>
                    <div>
                      <dt className="font-medium">常用图标</dt>
                      <dd className={item.missing_semantic_icons ? "text-amber-700" : "text-green-700"}>
                        {item.missing_semantic_icons ? "需要人工确认命名" : "已完成命名"}
                      </dd>
                    </div>
                    <div>
                      <dt className="font-medium">验收状态</dt>
                      <dd className="text-studio-muted">{ACCEPTANCE_LABELS[record.status]}</dd>
                    </div>
                  </dl>
                  <div className="flex flex-wrap gap-2">
                    <a
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      href={api.getProductionStudioFileUrl(item.candidate_preview_url)}
                      rel="noreferrer"
                      target="_blank"
                    >
                      查看资源
                    </a>
                    <a
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      href={api.getProductionStudioFileUrl(item.delivery_report_url)}
                      rel="noreferrer"
                      target="_blank"
                    >
                      查看报告
                    </a>
                    <a
                      className="rounded-md border border-studio-line px-3 py-2 text-sm"
                      href={api.getProductionStudioFileUrl(item.component_quality_report_url)}
                      rel="noreferrer"
                      target="_blank"
                    >
                      查看质量报告
                    </a>
                  </div>
                  <div className="grid gap-2 rounded-md bg-slate-50 p-3 text-sm">
                    <label className="grid gap-1 font-medium">
                      人工验收状态
                      <select
                        className="rounded-md border border-studio-line px-3 py-2 font-normal"
                        onChange={(event) =>
                          updateAcceptance(item.generation_job_id, { status: event.target.value as AcceptanceStatus })
                        }
                        value={record.status}
                      >
                        <option value="pending">待验收</option>
                        <option value="approved">验收通过</option>
                        <option value="needs_change">需要修改</option>
                      </select>
                    </label>
                    <label className="grid gap-1 font-medium">
                      验收记录
                      <textarea
                        className="min-h-20 rounded-md border border-studio-line px-3 py-2 font-normal"
                        onChange={(event) => updateAcceptance(item.generation_job_id, { notes: event.target.value })}
                        placeholder="记录需要修改的地方，或写下通过原因。"
                        value={record.notes}
                      />
                    </label>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <p className="mt-4 text-sm leading-6 text-studio-muted">
            生成完成后，这里会集中显示界面名称、生成时间、风格编号、预览图、资源入口、报告入口、验证状态和人工验收记录。
          </p>
        )}
      </div>
    </section>
  );
}
