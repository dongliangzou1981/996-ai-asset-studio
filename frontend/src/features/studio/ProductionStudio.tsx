"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

import {
  ProductionAssetMode,
  ProductionDeviceType,
  ProductionGenerationMode,
  ProductionLayoutTemplate,
  ProductionScreenType,
  ProductionStudioResult,
  ProductionStudioStyleCode,
  ProductionStyleSource,
  studioApi,
} from "@/lib/api";

const AUTO_GENERATE_PROMPT =
  "手机横屏传奇手游界面，采用经典传奇手游固定布局：左下摇杆区、右下环绕式技能操作区、右上小地图区、顶部信息区、底部状态信息区、右侧系统入口区、左下聊天区。保持布局稳定，只改变美术风格、按钮材质、边框纹饰和整体色调。";

const REFERENCE_GUIDED_PROMPT =
  "参考上传的传奇手游界面截图，保留核心操作布局：左下摇杆区、右下技能操作区、右上小地图区、顶部信息区、底部状态信息区、右侧系统入口区和聊天区。不要照抄原图素材，只参考布局和风格方向，生成新的统一风格 996 传奇手游 UI，适合后续切图、标注和资源生产。";

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

const LAYOUT_OPTIONS: { value: ProductionLayoutTemplate; label: string }[] = [
  { value: "classic_legend_mobile", label: "经典传奇手游布局" },
  { value: "legend_176", label: "1.76经典版" },
  { value: "legend_185_combo", label: "1.85合击版" },
  { value: "silent_version", label: "沉默版本" },
  { value: "hot_blood", label: "热血版本" },
];

const GENERATION_MODE_LABELS: Record<ProductionGenerationMode, string> = {
  auto_generate: "自动生成",
  reference_guided: "参考生成",
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
  "generateProductionStudioPackage" | "getProductionStudioFileUrl" | "listProductionStyleCodes" | "uploadAsset"
>;

function defaultAcceptanceRecord(): AcceptanceRecord {
  return { status: "pending", notes: "" };
}

export function ProductionStudio({ api = studioApi }: { api?: ProductionStudioApi }) {
  const [deviceType, setDeviceType] = useState<ProductionDeviceType>("mobile_landscape");
  const [assetMode, setAssetMode] = useState<ProductionAssetMode>("resource_production");
  const [styleSource, setStyleSource] = useState<ProductionStyleSource>("new_style");
  const [layoutTemplate, setLayoutTemplate] = useState<ProductionLayoutTemplate>("classic_legend_mobile");
  const [generationMode, setGenerationMode] = useState<ProductionGenerationMode>("auto_generate");
  const [styleCodes, setStyleCodes] = useState<ProductionStudioStyleCode[]>([]);
  const [selectedStyleCode, setSelectedStyleCode] = useState("");
  const [screenTypes, setScreenTypes] = useState<ProductionScreenType[]>(["main_ui"]);
  const [styleName, setStyleName] = useState("暗黑金龙传奇风");
  const [prompt, setPrompt] = useState(AUTO_GENERATE_PROMPT);
  const [referenceImagePath, setReferenceImagePath] = useState<string | null>(null);
  const [referencePreviewUrl, setReferencePreviewUrl] = useState("");
  const [referenceFileName, setReferenceFileName] = useState("");
  const [uploadingReference, setUploadingReference] = useState(false);
  const [result, setResult] = useState<ProductionStudioResult | null>(null);
  const [generatedAt, setGeneratedAt] = useState("");
  const [acceptance, setAcceptance] = useState<Record<string, AcceptanceRecord>>({});
  const [expandedPreview, setExpandedPreview] = useState<{ src: string; label: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listProductionStyleCodes()
      .then((response) => {
        setStyleCodes(response.items);
        setSelectedStyleCode(response.items[0]?.style_code ?? "");
      })
      .catch(() => setError("风格编号加载失败。请重新打开工作台，或运行 启动工作台.ps1。"));
  }, [api]);

  useEffect(() => {
    return () => {
      if (referencePreviewUrl) {
        URL.revokeObjectURL(referencePreviewUrl);
      }
    };
  }, [referencePreviewUrl]);

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

  function chooseGenerationMode(nextMode: ProductionGenerationMode) {
    setGenerationMode(nextMode);
    setPrompt(nextMode === "reference_guided" ? REFERENCE_GUIDED_PROMPT : AUTO_GENERATE_PROMPT);
  }

  async function uploadReferenceImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setError("");
    setUploadingReference(true);
    const previewUrl = URL.createObjectURL(file);
    setReferencePreviewUrl((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }
      return previewUrl;
    });
    setReferenceFileName(file.name);
    chooseGenerationMode("reference_guided");
    try {
      const asset = await api.uploadAsset({
        file,
        project_id: null,
        asset_type: "reference_image",
        device_type: deviceType,
      });
      setReferenceImagePath(asset.file_path);
      setReferenceFileName(asset.original_filename || file.name);
    } catch {
      setReferenceImagePath(null);
      setError("参考图上传失败。请换一张 png、jpg、jpeg 或 webp 图片后重试。");
    } finally {
      setUploadingReference(false);
      event.target.value = "";
    }
  }

  function removeReferenceImage() {
    if (referencePreviewUrl) {
      URL.revokeObjectURL(referencePreviewUrl);
    }
    setReferencePreviewUrl("");
    setReferenceImagePath(null);
    setReferenceFileName("");
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
        layout_template: layoutTemplate,
        generation_mode: generationMode,
        reference_image_path: generationMode === "reference_guided" ? referenceImagePath : null,
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

  const generationDisabled =
    loading ||
    uploadingReference ||
    (styleSource === "existing_style" && !selectedStyleCode) ||
    (generationMode === "reference_guided" && !referenceImagePath);

  return (
    <section className="grid gap-6 lg:grid-cols-[0.82fr_1.18fr]">
      <form className="grid gap-4 rounded-md border border-studio-line bg-white p-5" onSubmit={generate}>
        <div>
          <h2 className="text-lg font-semibold">生产工作台</h2>
          <p className="mt-2 text-sm leading-6 text-studio-muted">生成 996 传奇手游界面资源，结果会进入右侧结果中心。</p>
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

        <label className="grid gap-1 text-sm font-medium">
          布局模板
          <select
            className="rounded-md border border-studio-line px-3 py-2 font-normal"
            onChange={(event) => setLayoutTemplate(event.target.value as ProductionLayoutTemplate)}
            value={layoutTemplate}
          >
            {LAYOUT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="grid gap-2 rounded-md border border-studio-line p-3">
          <legend className="px-1 text-sm font-medium">生成模式</legend>
          <label className="flex items-center gap-2 text-sm">
            <input
              checked={generationMode === "auto_generate"}
              name="generation_mode"
              onChange={() => chooseGenerationMode("auto_generate")}
              type="radio"
            />
            自动生成
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              checked={generationMode === "reference_guided"}
              name="generation_mode"
              onChange={() => chooseGenerationMode("reference_guided")}
              type="radio"
            />
            参考生成
          </label>
        </fieldset>

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
                ? `${selectedStyle.style_name} / ${
                    selectedStyle.device_type
                      ? DEVICE_LABELS[selectedStyle.device_type as ProductionDeviceType] ?? selectedStyle.device_type
                      : "未知设备"
                  }`
                : "暂无风格"}
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

        <div className="grid gap-2 rounded-md border border-studio-line p-3">
          <label className="grid gap-1 text-sm font-medium">
            参考图
            <input
              accept="image/png,image/jpeg,image/webp"
              className="rounded-md border border-studio-line px-3 py-2 font-normal"
              onChange={uploadReferenceImage}
              type="file"
            />
          </label>
          {referencePreviewUrl ? (
            <div className="grid gap-2">
              <img
                alt="参考图缩略图"
                className="aspect-video w-full rounded-md border border-studio-line object-contain"
                src={referencePreviewUrl}
              />
              <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                <span className="text-studio-muted">{referenceFileName}</span>
                <button className="rounded-md border border-studio-line px-3 py-2" onClick={removeReferenceImage} type="button">
                  删除参考图
                </button>
              </div>
            </div>
          ) : null}
          {uploadingReference ? <p className="text-sm text-studio-muted">参考图上传中...</p> : null}
        </div>

        <label className="grid gap-1 text-sm font-medium">
          生成提示词
          <textarea
            className="min-h-36 rounded-md border border-studio-line px-3 py-2 text-sm font-normal leading-6"
            onChange={(event) => setPrompt(event.target.value)}
            value={prompt}
          />
        </label>

        <button
          className="rounded-md bg-studio-action px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
          disabled={generationDisabled}
          type="submit"
        >
          {loading ? "生成中..." : "开始生成"}
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
                布局模板：
                <span className="font-semibold">
                  {LAYOUT_OPTIONS.find((option) => option.value === result.layout_template)?.label ?? result.layout_template}
                </span>
              </div>
              <div>
                生成模式：<span className="font-semibold">{GENERATION_MODE_LABELS[result.generation_mode]}</span>
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
              const previewSrc = api.getProductionStudioFileUrl(item.ui_preview_url);
              return (
                <article className="grid gap-3 rounded-md border border-studio-line p-4" key={item.generation_job_id}>
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-semibold">{SCREEN_LABELS[item.screen_type]}</h3>
                      <p className="mt-1 text-xs text-studio-muted">生成任务：{item.generation_job_id}</p>
                    </div>
                    <span className={item.validator_ok ? "text-sm font-semibold text-green-700" : "text-sm font-semibold text-red-700"}>
                      {item.validator_ok ? "验证通过" : "验证未通过"}
                    </span>
                  </div>
                  <button
                    aria-label={`放大查看${SCREEN_LABELS[item.screen_type]}完整图预览`}
                    className="block overflow-hidden rounded-md border border-studio-line bg-slate-950"
                    onClick={() => setExpandedPreview({ src: previewSrc, label: SCREEN_LABELS[item.screen_type] })}
                    type="button"
                  >
                    <img
                      alt={`${SCREEN_LABELS[item.screen_type]}完整图预览`}
                      className="aspect-video w-full object-contain"
                      src={previewSrc}
                    />
                  </button>
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
                      <dt className="font-medium">资源状态</dt>
                      <dd className={item.missing_semantic_icons ? "text-amber-700" : "text-green-700"}>
                        {item.missing_semantic_icons ? "需要人工确认命名" : "语义命名完整"}
                      </dd>
                    </div>
                    <div>
                      <dt className="font-medium">人工验收状态</dt>
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
                        placeholder="记录需要修改的位置，或标记通过原因"
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
            生成完成后会显示完整图预览、界面名称、风格编号、验证状态、资源入口、报告入口和人工验收记录。
          </p>
        )}
      </div>

      {expandedPreview ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/80 p-4" role="dialog">
          <div className="grid max-h-full w-full max-w-6xl gap-3">
            <div className="flex items-center justify-between text-white">
              <h3 className="text-base font-semibold">{expandedPreview.label}完整图预览</h3>
              <button className="rounded-md bg-white px-3 py-2 text-sm text-slate-900" onClick={() => setExpandedPreview(null)} type="button">
                关闭
              </button>
            </div>
            <img alt={`${expandedPreview.label}放大预览`} className="max-h-[82vh] w-full object-contain" src={expandedPreview.src} />
          </div>
        </div>
      ) : null}
    </section>
  );
}
