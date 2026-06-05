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
  { value: "main_ui", label: "main_ui 主界面" },
  { value: "role_ui", label: "role_ui 角色界面" },
  { value: "bag_ui", label: "bag_ui 背包界面" },
  { value: "shop_ui", label: "shop_ui 商城界面" },
  { value: "activity_ui", label: "activity_ui 活动界面" },
];

type ProductionStudioApi = Pick<
  typeof studioApi,
  "generateProductionStudioPackage" | "getProductionStudioFileUrl" | "listProductionStyleCodes"
>;

export function ProductionStudio({ api = studioApi }: { api?: ProductionStudioApi }) {
  const [deviceType, setDeviceType] = useState<ProductionDeviceType>("mobile_landscape");
  const [assetMode, setAssetMode] = useState<ProductionAssetMode>("resource_production");
  const [styleSource, setStyleSource] = useState<ProductionStyleSource>("new_style");
  const [styleCodes, setStyleCodes] = useState<ProductionStudioStyleCode[]>([]);
  const [selectedStyleCode, setSelectedStyleCode] = useState("");
  const [screenTypes, setScreenTypes] = useState<ProductionScreenType[]>(["main_ui"]);
  const [styleName, setStyleName] = useState("暗黑金龙传奇风");
  const [prompt, setPrompt] = useState(
    "手机横屏传奇 UI，暗黑金龙风格，技能栏清晰，右侧菜单明显，整体适合 996 引擎资源生产。",
  );
  const [result, setResult] = useState<ProductionStudioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listProductionStyleCodes()
      .then((response) => {
        setStyleCodes(response.items);
        setSelectedStyleCode(response.items[0]?.style_code ?? "");
      })
      .catch(() => setError("STYLE_CODE 列表加载失败"));
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

  async function generate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
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
    } catch {
      setError("生成失败，请检查 provider 环境变量和后端日志");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[0.86fr_1.14fr]">
      <form className="grid gap-4 rounded-md border border-studio-line bg-white p-5" onSubmit={generate}>
        <div>
          <h2 className="text-lg font-semibold">生产工作台</h2>
          <p className="mt-2 text-sm leading-6 text-studio-muted">
            生成统一 STYLE_CODE 的 996-ready UI 资源包，包含预览图、标注、切图、候选切图和质量报告。
          </p>
        </div>

        <label className="grid gap-1 text-sm font-medium">
          设备类型
          <select
            className="rounded-md border border-studio-line px-3 py-2 font-normal"
            onChange={(event) => setDeviceType(event.target.value as ProductionDeviceType)}
            value={deviceType}
          >
            <option value="mobile_landscape">mobile_landscape</option>
            <option value="pc_landscape">pc_landscape</option>
          </select>
        </label>

        <label className="grid gap-1 text-sm font-medium">
          输出模式
          <select
            className="rounded-md border border-studio-line px-3 py-2 font-normal"
            onChange={(event) => setAssetMode(event.target.value as ProductionAssetMode)}
            value={assetMode}
          >
            <option value="ui_package">ui_package</option>
            <option value="resource_production">resource_production</option>
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
            使用已有 STYLE_CODE
          </label>
        </fieldset>

        {styleSource === "existing_style" ? (
          <label className="grid gap-1 text-sm font-medium">
            STYLE_CODE
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
              {selectedStyle ? `${selectedStyle.style_name} / ${selectedStyle.device_type || "unknown device"}` : "暂无可用 STYLE_CODE"}
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
          {loading ? "生成中..." : "生成 UI 资源"}
        </button>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
      </form>

      <div className="rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">生成结果</h2>
        {result ? (
          <div className="mt-4 grid gap-4">
            <div className="grid gap-2 rounded-md border border-studio-line bg-slate-50 p-3 text-sm">
              <div>
                STYLE_CODE: <span className="font-semibold">{result.style_code}</span>
              </div>
              <div>
                device_type: <span className="font-semibold">{result.device_type}</span>
              </div>
              <div>
                asset_mode: <span className="font-semibold">{result.asset_mode}</span>
              </div>
            </div>

            {result.results.map((item) => (
              <article className="grid gap-3 rounded-md border border-studio-line p-4" key={item.generation_job_id}>
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-semibold">{item.screen_type}</h3>
                    <p className="mt-1 break-all font-mono text-xs text-studio-muted">{item.generation_job_id}</p>
                  </div>
                  <span className={item.validator_ok ? "text-sm font-semibold text-green-700" : "text-sm font-semibold text-red-700"}>
                    validator {item.validator_ok ? "PASS" : "FAIL"}
                  </span>
                </div>
                <img
                  alt={`${item.screen_type} ui_preview`}
                  className="aspect-video w-full rounded-md border border-studio-line object-cover"
                  src={api.getProductionStudioFileUrl(item.ui_preview_url)}
                />
                <dl className="grid gap-2 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="font-medium">996-ready 路径</dt>
                    <dd className="break-all text-studio-muted">{item.package_dir}</dd>
                  </div>
                  <div>
                    <dt className="font-medium">切图数量</dt>
                    <dd className="text-studio-muted">
                      components {item.components_count} / candidates {item.candidates_count}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-medium">小图标语义命名</dt>
                    <dd className={item.missing_semantic_icons ? "text-amber-700" : "text-green-700"}>
                      {item.missing_semantic_icons ? "仍需优化 common_icons" : "已覆盖"}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-medium">说明</dt>
                    <dd className="text-studio-muted">{item.common_icons_note}</dd>
                  </div>
                </dl>
                <div className="flex flex-wrap gap-2">
                  <a
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    href={api.getProductionStudioFileUrl(item.delivery_report_url)}
                    rel="noreferrer"
                    target="_blank"
                  >
                    delivery_report.html
                  </a>
                  <a
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    href={api.getProductionStudioFileUrl(item.candidate_preview_url)}
                    rel="noreferrer"
                    target="_blank"
                  >
                    candidate_preview.html
                  </a>
                  <a
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    href={api.getProductionStudioFileUrl(item.component_quality_report_url)}
                    rel="noreferrer"
                    target="_blank"
                  >
                    component_quality_report.html
                  </a>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm leading-6 text-studio-muted">
            生成完成后会显示 STYLE_CODE、每个界面的预览、996-ready 路径、切图数量、validator 状态和报告入口。
          </p>
        )}
      </div>
    </section>
  );
}
