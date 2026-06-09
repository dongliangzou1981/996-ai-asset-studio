"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import {
  Project,
  ProductionAssetMode,
  ProductionDeviceType,
  ProductionGenerationMode,
  MainUiProductionResult,
  MarkingAcceptanceResult,
  ManualAcceptanceStatus,
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
  accepted: "验收通过",
  rejected: "验收拒绝",
} as const;

type AcceptanceRecord = {
  status: ManualAcceptanceStatus;
  notes: string;
};

type ProductionStudioApi = Pick<
  typeof studioApi,
  | "generateProductionStudioPackage"
  | "generateUiProductionPackage"
  | "markUiProductionCandidates"
  | "selectUiProductionCandidate"
  | "updateUiProductionCandidate"
  | "exportUiProductionComponents"
  | "runOpenCvUiSlicer"
  | "runMarkingAcceptanceTest"
  | "runMainUiProduction"
  | "getMainUiProduction"
  | "updateMainUiCandidate"
  | "exportMainUiProduction"
  | "getProductionStudioFileUrl"
  | "listProjects"
  | "createProject"
  | "listProductionStyleCodes"
  | "getPromptSampleSuggestion"
  | "updateProductionManualAcceptance"
  | "uploadAsset"
>;

type UiProductionScreenType = "main_ui" | "bag_ui" | "role_ui" | "shop_ui" | "activity_ui";
type UiProductionGenerationMode = "plain" | "reference" | "reference_ratio";

const UI_PRODUCTION_SCREEN_OPTIONS: { value: UiProductionScreenType; label: string; enabled: boolean }[] = [
  { value: "main_ui", label: "主界面", enabled: true },
  { value: "bag_ui", label: "背包（即将支持）", enabled: false },
  { value: "role_ui", label: "角色（即将支持）", enabled: false },
  { value: "shop_ui", label: "商城（即将支持）", enabled: false },
  { value: "activity_ui", label: "活动（即将支持）", enabled: false },
];

const UI_PRODUCTION_GENERATION_OPTIONS: { value: UiProductionGenerationMode; label: string }[] = [
  { value: "plain", label: "普通生成" },
  { value: "reference", label: "参考图生成（不按比例）" },
  { value: "reference_ratio", label: "参考图生成（按比例）" },
];

const UI_PRODUCTION_GENERATION_LABELS: Record<UiProductionGenerationMode, string> = {
  plain: "普通生成",
  reference: "参考图生成（不按比例）",
  reference_ratio: "参考图生成（按比例）",
};

const STYLE_REFERENCE_OPTIONS = [
  { value: "none", label: "不参考风格" },
  { value: "30", label: "30%参考" },
  { value: "60", label: "60%参考" },
  { value: "90", label: "90%参考" },
  { value: "copy", label: "高复刻" },
];

const MARKING_TEST_PROJECT_NAME = "标记验收测试";
const MARKING_TEST_PROJECT_CODE = "MARKING_TEST";
const MARKING_TEST_REQUIREMENT = "生成一张用于996传奇引擎的主界面UI";
const MARKING_TEST_ADJUSTMENT = "用于测试自动标记和自动切图准确性";

const PROMPT_DEVICE_LABELS: Record<ProductionDeviceType, string> = {
  mobile_landscape: "手机横屏",
  pc_landscape: "PC横屏",
};

const PROMPT_ASSET_MODE_LABELS: Record<ProductionAssetMode, string> = {
  resource_production: "资源生产",
  ui_package: "UI整包",
};

const PROMPT_LAYOUT_LABELS: Record<ProductionLayoutTemplate, string> = {
  classic_legend_mobile: "经典传奇手游布局",
  legend_176: "1.76经典布局",
  legend_185_combo: "1.85合击布局",
  silent_version: "沉默版本布局",
  hot_blood: "热血版本布局",
};

function isUiProductionResult(value: unknown): value is MainUiProductionResult {
  return Boolean(value && typeof value === "object" && "package_dir" in value);
}

function buildMainUiProductionPrompt(input: {
  projectName: string;
  projectCode: string;
  deviceType: ProductionDeviceType;
  assetMode: ProductionAssetMode;
  layoutTemplate: ProductionLayoutTemplate;
  screenType: UiProductionScreenType;
  generationMode: ProductionGenerationMode;
  uiGenerationMode: UiProductionGenerationMode;
  hasReferenceImage: boolean;
  referenceInfluence: number;
  adjustmentNote: string;
  historicalPrompt?: string;
}) {
  const referenceInfluence = Math.min(100, Math.max(0, Math.round(input.referenceInfluence)));
  const referenceLine =
    input.uiGenerationMode === "plain"
      ? "普通生成：不使用参考图，不依赖 P5 资源或项目参考图。"
      : input.hasReferenceImage
        ? "已上传参考图：风格跟随参考图或整体风格，不照抄参考图内容。"
        : "未上传参考图：使用系统内置 fallback 测试图或整体风格生成，不依赖 P5 资源。";
  const referenceInfluenceLine =
    input.uiGenerationMode === "reference_ratio"
      ? "参考图影响比例为 " +
        referenceInfluence +
        "%，仅影响风格、纹饰、色彩、材质、按钮视觉皮肤、面板装饰和图标表现，不改变固定布局骨架。"
      : input.uiGenerationMode === "reference"
        ? "参考图生成（不按比例）：参考图仅作为本次风格、纹饰、色彩、材质和视觉皮肤参考，不改变固定布局骨架。"
        : "参考图影响比例：未启用，本次普通生成不使用参考图。";
  const screenLine =
    input.screenType === "main_ui"
      ? "生成手机横屏传奇手游主界面，包含顶部信息区、右上地图、右侧入口按钮、右下技能操作区、左下摇杆、底部经验条、聊天区清晰。"
      : `生成 ${input.screenType} 界面。`;

  return [
    input.historicalPrompt ? `历史高质量提示词参考：\n${input.historicalPrompt}` : "",
    `项目：${input.projectName || "未命名项目"} / ${input.projectCode || "未设置代号"}`,
    `生产参数：${PROMPT_DEVICE_LABELS[input.deviceType]}，${PROMPT_ASSET_MODE_LABELS[input.assetMode]}，${PROMPT_LAYOUT_LABELS[input.layoutTemplate]}，界面类型 ${input.screenType}，生成模式 ${UI_PRODUCTION_GENERATION_LABELS[input.uiGenerationMode]}。`,
    screenLine,
    "布局要求：经典传奇手游布局，UI 元素边界清楚，方便自动标记和切图；按钮、图标、面板需要独立清晰。",
    referenceInfluenceLine,
    "固定布局骨架必须保持：顶部信息区、右上地图、右侧入口按钮、右下技能区、左下摇杆、底部经验条、聊天区。",
    "可变元素仅限：风格、纹饰、色彩、材质和装饰表现；不得改变核心布局、操作区域位置、聊天区可读性和移动端可操作性。",
    "移动端操作体验规则：手机横屏操作体验优先，右下技能按钮适配右手拇指操作，技能区可支持第二圈技能按钮，不遮挡经验条、聊天区和主视觉，按钮间距避免误触。布局可参考成熟手游操作设计，但不得破坏经典传奇手游布局骨架。",
    "右下技能区：主技能按钮固定右下角偏内侧，小技能围绕主技能形成半圆布局，预留第二圈技能按钮空间，避免遮挡底部经验条和聊天区域，符合手机横屏右手拇指操作体验。",
    referenceLine,
    input.adjustmentNote ? `调整说明：${input.adjustmentNote}` : "调整说明：无。",
  ]
    .filter(Boolean)
    .join("\n");
}

function defaultAcceptanceRecord(): AcceptanceRecord {
  return { status: "pending", notes: "" };
}

function isSupportedUploadImage(file: File) {
  const type = file.type.toLowerCase();
  const name = file.name.toLowerCase();
  return (
    type === "image/png" ||
    type === "image/jpeg" ||
    name.endsWith(".png") ||
    name.endsWith(".jpg") ||
    name.endsWith(".jpeg")
  );
}

function normalizeReferenceInfluence(value: string) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "0";
  }
  return String(Math.min(100, Math.max(0, Math.round(number))));
}

function backendGenerationMode(mode: UiProductionGenerationMode): ProductionGenerationMode {
  return mode === "plain" ? "auto_generate" : "reference_guided";
}

function shouldUseUiReference(mode: UiProductionGenerationMode) {
  return mode !== "plain";
}

function shouldUseUiReferenceRatio(mode: UiProductionGenerationMode) {
  return mode === "reference_ratio";
}

function uiStyleReferenceStrength(mode: UiProductionGenerationMode, influence: string) {
  return shouldUseUiReferenceRatio(mode) ? normalizeReferenceInfluence(influence) : "none";
}

export function ProductionStudio({ api = studioApi }: { api?: ProductionStudioApi }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectCode, setNewProjectCode] = useState("");
  const [showNewProjectForm, setShowNewProjectForm] = useState(false);
  const [projectLoading, setProjectLoading] = useState(false);
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
  const [mainUiProduction, setMainUiProduction] = useState<MainUiProductionResult | null>(null);
  const [mainUiLoading, setMainUiLoading] = useState(false);
  const [uiProductionScreenType, setUiProductionScreenType] = useState<UiProductionScreenType>("main_ui");
  const [uiProductionGenerationMode, setUiProductionGenerationMode] = useState<UiProductionGenerationMode>("plain");
  const [uiProductionRequirement, setUiProductionRequirement] = useState("");
  const [uiProductionSystemPrompt, setUiProductionSystemPrompt] = useState("");
  const [uiProductionPromptEdited, setUiProductionPromptEdited] = useState(false);
  const [uiProductionStyleReference, setUiProductionStyleReference] = useState("40");
  const [uiProductionReferencePath, setUiProductionReferencePath] = useState<string | null>(null);
  const [uiProductionReferencePreviewUrl, setUiProductionReferencePreviewUrl] = useState("");
  const [uiProductionReferenceFileName, setUiProductionReferenceFileName] = useState("");
  const [uiAdjustmentNote, setUiAdjustmentNote] = useState("");
  const [uiAdjustmentImagePath, setUiAdjustmentImagePath] = useState<string | null>(null);
  const [uiAdjustmentImageName, setUiAdjustmentImageName] = useState("");
  const [uiProductionMessage, setUiProductionMessage] = useState("");
  const [markingTestMode, setMarkingTestMode] = useState(false);
  const [markingTestLoading, setMarkingTestLoading] = useState(false);
  const [markingAcceptanceResult, setMarkingAcceptanceResult] = useState<MarkingAcceptanceResult | null>(null);
  const [generatedAt, setGeneratedAt] = useState("");
  const [acceptance, setAcceptance] = useState<Record<string, AcceptanceRecord>>({});
  const [expandedPreview, setExpandedPreview] = useState<{ src: string; label: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [projectError, setProjectError] = useState("");
  const [styleCodeWarning, setStyleCodeWarning] = useState("");
  const [uiReferenceUploadError, setUiReferenceUploadError] = useState("");
  const [uiAdjustmentUploadError, setUiAdjustmentUploadError] = useState("");
  const selectedProject = projects.find((project) => project.id === selectedProjectId);

  useEffect(() => {
    api
      .listProjects()
      .then((response) => {
        setProjects(response.items);
        setSelectedProjectId((current) => current || response.items[0]?.id || "");
      })
      .catch(() => setError("项目列表加载失败，请确认后端服务已启动。"));
  }, [api]);

  useEffect(() => {
    api
      .listProductionStyleCodes()
      .then((response) => {
        setStyleCodes(response.items);
        setSelectedStyleCode(response.items[0]?.style_code ?? "");
        setStyleCodeWarning("");
      })
      .catch(() => setStyleCodeWarning("风格编号暂时不可用，不影响项目创建、普通生成、参考图生成和标记验收测试。"));
  }, [api]);

  useEffect(() => {
    return () => {
      if (referencePreviewUrl) {
        URL.revokeObjectURL(referencePreviewUrl);
      }
    };
  }, [referencePreviewUrl]);

  useEffect(() => {
    return () => {
      if (uiProductionReferencePreviewUrl) {
        URL.revokeObjectURL(uiProductionReferencePreviewUrl);
      }
    };
  }, [uiProductionReferencePreviewUrl]);

  useEffect(() => {
    const savedPackageDir = window.localStorage.getItem("uiProductionPackageDir");
    if (!savedPackageDir) {
      return;
    }
    api
      .getMainUiProduction(savedPackageDir)
      .then((response) => setMainUiProduction(response))
      .catch(() => window.localStorage.removeItem("uiProductionPackageDir"));
  }, [api]);

  useEffect(() => {
    if (uiProductionPromptEdited) {
      return;
    }
    let cancelled = false;
    const basePromptInput = {
      projectName: selectedProject?.name ?? MARKING_TEST_PROJECT_NAME,
      projectCode: selectedProject?.description ?? MARKING_TEST_PROJECT_CODE,
      deviceType,
      assetMode,
      layoutTemplate,
      screenType: uiProductionScreenType,
      generationMode: backendGenerationMode(uiProductionGenerationMode),
      uiGenerationMode: uiProductionGenerationMode,
      hasReferenceImage: shouldUseUiReference(uiProductionGenerationMode) && Boolean(uiProductionReferencePath),
      referenceInfluence: Number(uiProductionStyleReference) || 0,
      adjustmentNote: uiAdjustmentNote,
    };
    const basePrompt = buildMainUiProductionPrompt(basePromptInput);
    setUiProductionSystemPrompt(basePrompt);
    setUiProductionRequirement(basePrompt);
    api
      .getPromptSampleSuggestion({
        interface_type: uiProductionScreenType,
        device_type: deviceType,
        layout_template: layoutTemplate,
      })
      .then((suggestion) => {
        if (cancelled || uiProductionPromptEdited || !suggestion.found || !suggestion.final_prompt) {
          return;
        }
        const learnedPrompt = buildMainUiProductionPrompt({
          ...basePromptInput,
          historicalPrompt: suggestion.final_prompt,
        });
        setUiProductionSystemPrompt(learnedPrompt);
        setUiProductionRequirement(learnedPrompt);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [
    api,
    assetMode,
    deviceType,
    layoutTemplate,
    selectedProject?.description,
    selectedProject?.name,
    uiAdjustmentNote,
    uiProductionGenerationMode,
    uiProductionPromptEdited,
    uiProductionReferencePath,
    uiProductionScreenType,
    uiProductionStyleReference,
  ]);

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

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = newProjectName.trim();
    const code = newProjectCode.trim();
    if (!name || !code) {
      setProjectError("请填写项目名称和代号。");
      return;
    }
    setProjectLoading(true);
    setProjectError("");
    try {
      const created = await api.createProject({
        name,
        description: code,
        status: "draft",
      });
      setProjects((items) => [created, ...items]);
      setSelectedProjectId(created.id);
      setNewProjectName("");
      setNewProjectCode("");
      setShowNewProjectForm(false);
    } catch {
      setProjectError("新建项目失败，请确认项目服务可用。");
    } finally {
      setProjectLoading(false);
    }
  }

  async function enterMarkingAcceptanceMode() {
    setProjectLoading(true);
    setError("");
    setProjectError("");
    setUiReferenceUploadError("");
    setUiAdjustmentUploadError("");
    setUiProductionMessage("");
    setMarkingAcceptanceResult(null);
    try {
      let projectList: { items: Project[] } = { items: projects };
      try {
        projectList = await api.listProjects();
        setProjects(projectList.items);
      } catch {
        projectList = { items: projects };
      }
      let project = projectList.items.find(
        (item) => item.name === MARKING_TEST_PROJECT_NAME && item.description === MARKING_TEST_PROJECT_CODE,
      );
      if (!project) {
        try {
          project = await api.createProject({
            name: MARKING_TEST_PROJECT_NAME,
            description: MARKING_TEST_PROJECT_CODE,
            status: "draft",
          });
        } catch {
          project = {
            id: MARKING_TEST_PROJECT_CODE,
            name: MARKING_TEST_PROJECT_NAME,
            description: MARKING_TEST_PROJECT_CODE,
            status: "draft",
            created_at: "",
            updated_at: "",
          };
        }
        setProjects((items) => (items.some((item) => item.id === project?.id) ? items : [project as Project, ...items]));
      }
      setSelectedProjectId(project.id);
      setDeviceType("mobile_landscape");
      setAssetMode("resource_production");
      setLayoutTemplate("classic_legend_mobile");
      setUiProductionScreenType("main_ui");
      setUiProductionGenerationMode("plain");
      chooseGenerationMode("auto_generate");
      setUiProductionPromptEdited(false);
      setUiAdjustmentNote(MARKING_TEST_ADJUSTMENT);
      setUiProductionStyleReference("40");
      if (uiProductionReferencePreviewUrl) {
        URL.revokeObjectURL(uiProductionReferencePreviewUrl);
      }
      setUiProductionReferencePath(null);
      setUiProductionReferencePreviewUrl("");
      setUiProductionReferenceFileName("");
      setUiAdjustmentImagePath(null);
      setUiAdjustmentImageName("");
      const testPrompt = buildMainUiProductionPrompt({
        projectName: project.name,
        projectCode: project.description,
        deviceType: "mobile_landscape",
        assetMode: "resource_production",
        layoutTemplate: "classic_legend_mobile",
        screenType: "main_ui",
        generationMode: "auto_generate",
        uiGenerationMode: "plain",
        hasReferenceImage: false,
        referenceInfluence: 40,
        adjustmentNote: MARKING_TEST_ADJUSTMENT,
      });
      setUiProductionSystemPrompt(testPrompt);
      setUiProductionRequirement(testPrompt);
      setMarkingTestMode(true);
      setUiProductionMessage("已进入标记验收测试：参数已自动填充，请点击一键生成并标记测试。");
    } catch (exc) {
      setError(`进入标记验收测试失败：${exc instanceof Error ? exc.message : "未知错误"}`);
    } finally {
      setProjectLoading(false);
    }
  }

  async function runMarkingAcceptanceTest() {
    setMarkingTestLoading(true);
    setMainUiLoading(true);
    setError("");
    setUiProductionMessage("正在自动生成三张候选图、选择第一张、标记组件并执行切图...");
    try {
      const response = await api.runMarkingAcceptanceTest({
        reference_image_path: null,
        system_prompt: uiProductionSystemPrompt,
        requirement: uiProductionRequirement,
        style_reference_strength: "none",
        project_id: selectedProjectId,
        device_type: deviceType,
        layout_template: layoutTemplate,
        adjustment_note: uiAdjustmentNote,
        adjustment_image_path: uiAdjustmentImagePath,
      });
      setMarkingAcceptanceResult(response);
      setMainUiProduction(response.production);
      setSelectedProjectId(response.project.id);
      setProjects((items) =>
        items.some((item) => item.id === response.project.id) ? items : [response.project, ...items],
      );
      window.localStorage.setItem("uiProductionPackageDir", response.production.package_dir);
      setUiProductionMessage("标记验收测试完成：已输出 candidate_preview、marking JSON、切图和验收报告。");
    } catch (exc) {
      setError(`一键生成并标记测试失败：${exc instanceof Error ? exc.message : "未知错误"}`);
    } finally {
      setMarkingTestLoading(false);
      setMainUiLoading(false);
    }
  }

  async function persistAcceptance(packageDir: string, jobId: string, patch: Partial<AcceptanceRecord>) {
    updateAcceptance(jobId, patch);
    try {
      await api.updateProductionManualAcceptance(packageDir, {
        review_status: patch.status,
        remarks: patch.notes,
      });
    } catch {
      setError("人工验收写入失败。请确认后端工作台仍在运行。");
    }
  }

  async function uploadUiProductionReference(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setUiReferenceUploadError("");
    setUiProductionMessage("");
    if (!isSupportedUploadImage(file)) {
      setUiReferenceUploadError("参考图上传失败，请使用 PNG、JPG 或 JPEG。");
      event.target.value = "";
      return;
    }
    const previewUrl = URL.createObjectURL(file);
    try {
      const asset = await api.uploadAsset({
        file,
        project_id: null,
        asset_type: "reference_image",
        device_type: deviceType,
      });
      setUiProductionReferencePreviewUrl((current) => {
        if (current) {
          URL.revokeObjectURL(current);
        }
        return previewUrl;
      });
      setUiProductionReferencePath(asset.file_path);
      setUiProductionReferenceFileName(asset.original_filename || file.name);
    } catch (exc) {
      URL.revokeObjectURL(previewUrl);
      setUiProductionReferencePath(null);
      setUiProductionReferencePreviewUrl((current) => {
        if (current) {
          URL.revokeObjectURL(current);
        }
        return "";
      });
      setUiProductionReferenceFileName("");
      setUiReferenceUploadError(`参考图上传失败：${exc instanceof Error ? exc.message : "未知错误"}`);
    } finally {
      event.target.value = "";
    }
  }

  async function uploadUiAdjustmentImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setUiAdjustmentUploadError("");
    setUiProductionMessage("");
    if (!isSupportedUploadImage(file)) {
      setUiAdjustmentUploadError("调整截图上传失败，请使用 PNG、JPG 或 JPEG。");
      event.target.value = "";
      return;
    }
    try {
      const asset = await api.uploadAsset({
        file,
        project_id: null,
        asset_type: "reference_image",
        device_type: deviceType,
      });
      setUiAdjustmentImagePath(asset.file_path);
      setUiAdjustmentImageName(asset.original_filename || file.name);
      setUiProductionMessage("调整截图已保存，下次生成会带入调整记录。");
    } catch (exc) {
      setUiAdjustmentImagePath(null);
      setUiAdjustmentImageName("");
      setUiAdjustmentUploadError(`调整截图上传失败：${exc instanceof Error ? exc.message : "未知错误"}`);
    } finally {
      event.target.value = "";
    }
  }

  function removeUiProductionReference() {
    if (uiProductionReferencePreviewUrl) {
      URL.revokeObjectURL(uiProductionReferencePreviewUrl);
    }
    setUiProductionReferencePreviewUrl("");
    setUiProductionReferencePath(null);
    setUiProductionReferenceFileName("");
    setUiReferenceUploadError("");
    setUiProductionMessage("已移除参考图。");
  }

  async function generateUiProductionInterface() {
    const useReference = shouldUseUiReference(uiProductionGenerationMode);
    if (useReference && !uiProductionReferencePath) {
      setUiReferenceUploadError("请先上传参考图。");
      return;
    }
    setMainUiLoading(true);
    setError("");
    setUiReferenceUploadError("");
    setUiProductionMessage("");
    try {
      const referenceImagePath = useReference ? uiProductionReferencePath : null;
      const referenceInfluencePercent = shouldUseUiReferenceRatio(uiProductionGenerationMode)
        ? Number(uiProductionStyleReference) || 0
        : null;
      const response = await api.generateUiProductionPackage({
        screen_type: uiProductionScreenType,
        reference_image_path: referenceImagePath,
        reference_image: referenceImagePath,
        system_prompt: uiProductionSystemPrompt,
        requirement: uiProductionRequirement,
        style_reference_strength: uiStyleReferenceStrength(uiProductionGenerationMode, uiProductionStyleReference),
        reference_influence_percent: referenceInfluencePercent,
        project_id: selectedProjectId,
        device_type: deviceType,
        layout_template: layoutTemplate,
        adjustment_note: uiAdjustmentNote,
        adjustment_image_path: uiAdjustmentImagePath,
      });
      if (!isUiProductionResult(response)) {
        setUiProductionMessage(response.message);
        return;
      }
      setMainUiProduction(response);
      window.localStorage.setItem("uiProductionPackageDir", response.package_dir);
      setUiProductionMessage("生成完成：已输出 main_ui.jpg，请继续标记候选组件。");
    } catch (exc) {
      setError(`生成界面失败：${exc instanceof Error ? exc.message : "未知错误"}`);
    } finally {
      setMainUiLoading(false);
    }
  }

  async function markUiProductionCandidates() {
    if (!mainUiProduction) {
      return;
    }
    setMainUiLoading(true);
    setError("");
    try {
      const response = await api.markUiProductionCandidates(mainUiProduction.package_dir);
      setMainUiProduction(response);
      window.localStorage.setItem("uiProductionPackageDir", response.package_dir);
      setUiProductionMessage("标记完成：已输出 candidate_preview.jpg，请确认需要切图的组件。");
    } catch {
      setError("标记候选组件失败。");
    } finally {
      setMainUiLoading(false);
    }
  }

  async function selectUiCandidateOption(candidateId: string) {
    if (!mainUiProduction) {
      return;
    }
    setMainUiLoading(true);
    setError("");
    try {
      const response = await api.selectUiProductionCandidate(mainUiProduction.package_dir, candidateId);
      setMainUiProduction(response);
      window.localStorage.setItem("uiProductionPackageDir", response.package_dir);
      setUiProductionMessage("当前方案已切换，请重新标记候选组件。");
    } catch {
      setError("候选方案切换失败。");
    } finally {
      setMainUiLoading(false);
    }
  }

  async function runMainUiProduction() {
    setMainUiLoading(true);
    setError("");
    try {
      setMainUiProduction(await api.runMainUiProduction());
    } catch {
      setError("主界面实验包生成失败，请确认 P5 主界面参考资源可访问。");
    } finally {
      setMainUiLoading(false);
    }
  }

  async function updateMainUiCandidate(candidateId: string, confirmed: boolean) {
    if (!mainUiProduction) {
      return;
    }
    const packageDir = mainUiProduction.package_dir;
    setMainUiProduction({
      ...mainUiProduction,
      candidates: mainUiProduction.candidates.map((candidate) =>
        candidate.candidate_id === candidateId ? { ...candidate, confirmed } : candidate,
      ),
    });
    try {
      await api.updateUiProductionCandidate(packageDir, candidateId, confirmed);
      setUiProductionMessage("确认状态已保存。");
    } catch {
      setError("主界面候选确认状态保存失败。");
    }
  }

  async function exportMainUiProduction() {
    if (!mainUiProduction) {
      return;
    }
    setMainUiLoading(true);
    setError("");
    try {
      setMainUiProduction(await api.exportUiProductionComponents(mainUiProduction.package_dir));
      setUiProductionMessage("切图完成：已输出 confirmed_components，并生成 996-ready 包。");
    } catch {
      setError("确认组件切图失败，请检查 candidate_manifest.json。");
    } finally {
      setMainUiLoading(false);
    }
  }

  async function runOpenCvUiSlicer() {
    if (!mainUiProduction) {
      return;
    }
    setMainUiLoading(true);
    setError("");
    try {
      const response = await api.runOpenCvUiSlicer(mainUiProduction.package_dir);
      setMainUiProduction(response);
      window.localStorage.setItem("uiProductionPackageDir", response.package_dir);
      setUiProductionMessage(`OpenCV baseline 切图完成：识别 ${response.opencv_layer_count ?? 0} 个组件。`);
    } catch (exc) {
      setError(`OpenCV baseline 切图失败：${exc instanceof Error ? exc.message : "unknown"}`);
    } finally {
      setMainUiLoading(false);
    }
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
        Object.fromEntries(
          response.results.map((item) => [
            item.generation_job_id,
            { ...defaultAcceptanceRecord(), status: item.manual_acceptance_status ?? "pending" },
          ]),
        ),
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

  const projectContext = mainUiProduction?.project_context;
  const canPreviewPackageFile = (file: string) => /\.(png|jpe?g|webp)$/i.test(file);

  return (
    <section className="grid min-w-0 gap-4 xl:grid-cols-[260px_320px_minmax(0,1fr)]">
      <aside className="grid h-fit min-w-0 gap-4 rounded-md border border-studio-line bg-white p-4 text-sm">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">项目列表</h2>
          <button
            className="shrink-0 rounded-md border border-studio-line px-3 py-2 text-xs font-medium"
            onClick={() => setShowNewProjectForm((value) => !value)}
            type="button"
          >
            新建项目
          </button>
        </div>

        {showNewProjectForm ? (
          <form className="grid gap-3 rounded-md bg-slate-50 p-3" onSubmit={createProject}>
            <label className="grid gap-1 font-medium">
              项目名称
              <input
                className="min-w-0 rounded-md border border-studio-line px-3 py-2 font-normal"
                onChange={(event) => setNewProjectName(event.target.value)}
                value={newProjectName}
              />
            </label>
            <label className="grid gap-1 font-medium">
              项目代号
              <input
                className="min-w-0 rounded-md border border-studio-line px-3 py-2 font-normal"
                onChange={(event) => setNewProjectCode(event.target.value)}
                value={newProjectCode}
              />
            </label>
            <button
              className="rounded-md bg-studio-action px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
              disabled={projectLoading}
              type="submit"
            >
              {projectLoading ? "创建中..." : "保存项目"}
            </button>
            {projectError ? <p className="text-xs leading-5 text-red-600">{projectError}</p> : null}
          </form>
        ) : null}

        <div className="grid gap-2">
          {projects.length ? (
            projects.map((project) => (
              <button
                className={`grid min-w-0 gap-1 rounded-md border px-3 py-2 text-left ${
                  project.id === selectedProjectId ? "border-studio-action bg-slate-50" : "border-studio-line bg-white"
                }`}
                key={project.id}
                onClick={() => setSelectedProjectId(project.id)}
                type="button"
              >
                <span className="truncate font-semibold">{project.name}</span>
                <span className="truncate text-xs text-studio-muted">{project.description || "未设置代号"}</span>
              </button>
            ))
          ) : (
            <p className="rounded-md bg-slate-50 p-3 text-studio-muted">暂无项目，点击新建项目开始。</p>
          )}
        </div>
      </aside>

      <section className="grid h-fit min-w-0 gap-4 rounded-md border border-studio-line bg-white p-4">
        <div>
          <h2 className="text-lg font-semibold">生产工作台</h2>
          <p className="mt-2 text-sm leading-6 text-studio-muted">选择当前项目的生产方向，后续素材任务将在结果中心执行</p>
        </div>
        {selectedProject ? (
          <div className="rounded-md bg-slate-50 p-3 text-sm">
            <div className="font-semibold">{selectedProject.name}</div>
            <div className="mt-1 text-xs text-studio-muted">{selectedProject.description || "未设置代号"}</div>
          </div>
        ) : null}
        <label className="grid gap-1 text-sm font-medium">
          设备类型
          <select
            className="min-w-0 rounded-md border border-studio-line px-3 py-2 font-normal"
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
            className="min-w-0 rounded-md border border-studio-line px-3 py-2 font-normal"
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
            className="min-w-0 rounded-md border border-studio-line px-3 py-2 font-normal"
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
        {error ? <p className="text-sm leading-6 text-red-600">{error}</p> : null}
      </section>

      <div className="min-w-0 rounded-md border border-studio-line bg-white p-5">
        <h2 className="text-lg font-semibold">结果中心 / 素材生产</h2>
        {styleCodeWarning ? <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{styleCodeWarning}</p> : null}
        <section className="mt-4 grid gap-3 rounded-md border border-amber-300 bg-amber-50 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="min-w-0">
              <h3 className="font-semibold text-amber-950">验收测试模式</h3>
              <p className="mt-1 text-sm leading-6 text-amber-900">
                自动准备 MARKING_TEST 项目和主界面生产参数，用于直接验收自动标记与切图结果。
              </p>
            </div>
            <button
              className="rounded-md bg-amber-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
              disabled={projectLoading || markingTestLoading}
              onClick={enterMarkingAcceptanceMode}
              type="button"
            >
              进入标记验收测试
            </button>
          </div>
          {markingTestMode ? (
            <div className="flex flex-wrap items-center gap-3 rounded-md bg-white/70 p-3">
              <span className="text-sm font-medium text-amber-950">
                当前模式：{MARKING_TEST_PROJECT_NAME} / {MARKING_TEST_PROJECT_CODE}
              </span>
              <button
                className="rounded-md bg-studio-action px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                disabled={markingTestLoading}
                onClick={runMarkingAcceptanceTest}
                type="button"
              >
                {markingTestLoading ? "验收测试执行中..." : "一键生成并标记测试"}
              </button>
            </div>
          ) : null}
        </section>
        <section className="mt-4 grid gap-4 rounded-md border border-studio-line bg-white p-4">
          <div>
            <h3 className="font-semibold">UI素材生产</h3>
            <p className="mt-1 text-sm text-studio-muted">选择界面、上传参考、生成完整界面、标记候选、人工确认、执行切图、查看输出包。</p>
          </div>
          <div className="grid gap-3 rounded-md bg-slate-50 p-3 sm:grid-cols-2">
            <label className="grid gap-1 text-sm font-medium">
              1. 选择界面类型
              <select
                className="rounded-md border border-studio-line px-3 py-2 font-normal"
                onChange={(event) => setUiProductionScreenType(event.target.value as UiProductionScreenType)}
                value={uiProductionScreenType}
              >
                {UI_PRODUCTION_SCREEN_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {uiProductionScreenType !== "main_ui" ? (
                <span className="text-xs font-normal text-amber-700">该界面类型即将支持，本轮仅主界面完整跑通。</span>
              ) : null}
            </label>
            <label className="grid gap-1 text-sm font-medium">
              生成模式
              <select
                className="rounded-md border border-studio-line px-3 py-2 font-normal"
                onChange={(event) => {
                  const nextMode = event.target.value as UiProductionGenerationMode;
                  setUiProductionGenerationMode(nextMode);
                  chooseGenerationMode(backendGenerationMode(nextMode));
                  setUiReferenceUploadError("");
                }}
                value={uiProductionGenerationMode}
              >
                {UI_PRODUCTION_GENERATION_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {shouldUseUiReference(uiProductionGenerationMode) ? (
            <div className="grid gap-3 rounded-md border border-studio-line p-3">
              <label className="grid gap-1 text-sm font-medium">
                2. 上传参考图
                <input
                  accept="image/png,image/jpeg,.png,.jpg,.jpeg"
                  className="rounded-md border border-studio-line px-3 py-2 font-normal"
                  onChange={uploadUiProductionReference}
                  type="file"
                />
              </label>
              {uiReferenceUploadError ? <p className="text-xs leading-5 text-red-600">{uiReferenceUploadError}</p> : null}
              {shouldUseUiReferenceRatio(uiProductionGenerationMode) ? (
                <div className="grid gap-2 rounded-md bg-slate-50 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <label className="text-sm font-medium" htmlFor="ui-reference-influence">
                      参考图影响比例
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        aria-label="参考图影响比例数值"
                        className="w-20 rounded-md border border-studio-line px-2 py-1 text-sm"
                        max={100}
                        min={0}
                        onChange={(event) => setUiProductionStyleReference(normalizeReferenceInfluence(event.target.value))}
                        type="number"
                        value={uiProductionStyleReference}
                      />
                      <span className="text-sm text-studio-muted">%</span>
                    </div>
                  </div>
                  <input
                    aria-label="参考图影响比例"
                    className="w-full"
                    id="ui-reference-influence"
                    max={100}
                    min={0}
                    onChange={(event) => setUiProductionStyleReference(normalizeReferenceInfluence(event.target.value))}
                    step={1}
                    type="range"
                    value={Number(uiProductionStyleReference) || 0}
                  />
                  <p className="text-xs leading-5 text-studio-muted">
                    仅影响风格、纹饰、色彩、材质、按钮皮肤、面板装饰和图标表现，不改变固定布局骨架。
                  </p>
                </div>
              ) : null}
              {uiProductionReferencePreviewUrl ? (
                <div className="grid gap-2">
                  <img
                    alt="UI素材生产参考图预览"
                    className="aspect-video w-full rounded-md border border-studio-line object-contain"
                    src={uiProductionReferencePreviewUrl}
                  />
                  <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                    <span className="text-studio-muted">{uiProductionReferenceFileName}</span>
                    <button className="rounded-md border border-studio-line px-3 py-2" onClick={removeUiProductionReference} type="button">
                      移除参考图
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
          <label className="grid gap-2 text-sm font-medium">
            <span>系统生成提示词</span>
            <span className="text-xs font-normal text-studio-muted">
              系统会根据项目、设备、布局、界面类型、参考图和调整说明生成；可直接编辑，实际生成会使用这里的最终文本。
            </span>
            3. 生成提示词 / 需求描述
            <textarea
              aria-label="系统生成提示词"
              className="min-h-44 rounded-md border border-studio-line px-3 py-2 font-normal leading-6"
              onChange={(event) => {
                setUiProductionPromptEdited(true);
                setUiProductionRequirement(event.target.value);
              }}
              value={uiProductionRequirement}
            />
          </label>
          <div className="grid gap-3 rounded-md border border-studio-line p-3">
            <label className="grid gap-1 text-sm font-medium">
              调整说明
              <textarea
                className="min-h-20 rounded-md border border-studio-line px-3 py-2 font-normal leading-6"
                onChange={(event) => setUiAdjustmentNote(event.target.value)}
                placeholder="例如：任务栏向左缩进，右下技能按钮更贴近边缘。"
                value={uiAdjustmentNote}
              />
            </label>
            <label className="grid gap-1 text-sm font-medium">
              上传调整截图
              <input
                accept="image/png,image/jpeg,.png,.jpg,.jpeg"
                className="rounded-md border border-studio-line px-3 py-2 font-normal"
                onChange={uploadUiAdjustmentImage}
                type="file"
              />
            </label>
            {uiAdjustmentUploadError ? <p className="text-xs leading-5 text-red-600">{uiAdjustmentUploadError}</p> : null}
            {uiAdjustmentImageName ? <p className="text-xs text-studio-muted">已保存调整截图：{uiAdjustmentImageName}</p> : null}
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              className="rounded-md bg-studio-action px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
              disabled={mainUiLoading || uiProductionScreenType !== "main_ui"}
              onClick={generateUiProductionInterface}
              type="button"
            >
              生成界面
            </button>
            <button
              className="rounded-md border border-studio-line px-3 py-2 text-sm disabled:opacity-60"
              disabled={mainUiLoading || !mainUiProduction}
              onClick={markUiProductionCandidates}
              type="button"
            >
              标记候选组件
            </button>
            <button
              className="rounded-md border border-studio-line px-3 py-2 text-sm disabled:opacity-60"
              disabled={mainUiLoading || !mainUiProduction || !mainUiProduction.candidates.length}
              onClick={exportMainUiProduction}
              type="button"
            >
              执行切图
            </button>
            <button
              className="rounded-md border border-studio-line px-3 py-2 text-sm font-semibold disabled:opacity-60"
              disabled={mainUiLoading || !mainUiProduction || !mainUiProduction.candidates.length}
              onClick={exportMainUiProduction}
              type="button"
            >
              导出 996-ready
            </button>
            <button
              className="rounded-md border border-studio-line px-3 py-2 text-sm disabled:opacity-60"
              disabled={mainUiLoading || !mainUiProduction}
              onClick={runOpenCvUiSlicer}
              type="button"
            >
              OpenCV baseline 切图
            </button>
          </div>
          {uiProductionMessage ? <p className="text-sm text-amber-700">{uiProductionMessage}</p> : null}
          {markingAcceptanceResult ? (
            <section className="grid gap-4 rounded-md border border-emerald-300 bg-emerald-50 p-4">
              <div>
                <h3 className="font-semibold text-emerald-950">标记验收结果</h3>
                <p className="mt-1 text-sm text-emerald-900">
                  candidate_preview、marking JSON、切图和验收报告已生成，可直接截图验收。
                </p>
              </div>
              {markingAcceptanceResult.candidate_preview_url ? (
                <div className="grid gap-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-medium">candidate_preview 预览图</div>
                    <button
                      className="rounded-md border border-emerald-300 bg-white px-2 py-1 text-xs"
                      onClick={() =>
                        setExpandedPreview({
                          src: api.getProductionStudioFileUrl(markingAcceptanceResult.candidate_preview_url),
                          label: "candidate_preview 预览图",
                        })
                      }
                      type="button"
                    >
                      预览
                    </button>
                  </div>
                  <img
                    alt="标记验收 candidate_preview"
                    className="aspect-video w-full rounded-md border border-emerald-300 bg-slate-950 object-contain"
                    src={api.getProductionStudioFileUrl(markingAcceptanceResult.candidate_preview_url)}
                  />
                </div>
              ) : null}
              <dl className="grid gap-2 text-sm sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-md bg-white p-3">
                  <dt className="text-studio-muted">标记组件总数</dt>
                  <dd className="mt-1 text-xl font-semibold">{markingAcceptanceResult.total_marks}</dd>
                </div>
                <div className="rounded-md bg-white p-3">
                  <dt className="text-studio-muted">背景数量</dt>
                  <dd className="mt-1 text-xl font-semibold">{markingAcceptanceResult.by_type.background}</dd>
                </div>
                <div className="rounded-md bg-white p-3">
                  <dt className="text-studio-muted">面板数量</dt>
                  <dd className="mt-1 text-xl font-semibold">{markingAcceptanceResult.by_type.panel}</dd>
                </div>
                <div className="rounded-md bg-white p-3">
                  <dt className="text-studio-muted">按钮数量</dt>
                  <dd className="mt-1 text-xl font-semibold">{markingAcceptanceResult.by_type.button}</dd>
                </div>
                <div className="rounded-md bg-white p-3">
                  <dt className="text-studio-muted">图标数量</dt>
                  <dd className="mt-1 text-xl font-semibold">{markingAcceptanceResult.by_type.icon}</dd>
                </div>
                <div className="rounded-md bg-white p-3">
                  <dt className="text-studio-muted">技能数量</dt>
                  <dd className="mt-1 text-xl font-semibold">{markingAcceptanceResult.by_type.skill}</dd>
                </div>
                <div className="rounded-md bg-white p-3">
                  <dt className="text-studio-muted">切图成功数量</dt>
                  <dd className="mt-1 text-xl font-semibold">{markingAcceptanceResult.slice_success}</dd>
                </div>
                <div className="rounded-md bg-white p-3">
                  <dt className="text-studio-muted">切图失败数量</dt>
                  <dd className="mt-1 text-xl font-semibold">{markingAcceptanceResult.slice_failed}</dd>
                </div>
              </dl>
              <div className="grid gap-2 rounded-md bg-white p-3 text-xs leading-6">
                <div className="break-all">
                  <span className="font-semibold">manifest 路径：</span>
                  {markingAcceptanceResult.manifest_path}
                </div>
                <div className="break-all">
                  <span className="font-semibold">marking.json 路径：</span>
                  {markingAcceptanceResult.marking_json_path}
                </div>
                <div className="break-all">
                  <span className="font-semibold">manual_acceptance.json 路径：</span>
                  {markingAcceptanceResult.manual_acceptance_path}
                </div>
                <div className="break-all">
                  <span className="font-semibold">training_samples 路径：</span>
                  {markingAcceptanceResult.training_samples_path}
                </div>
                <div className="break-all">
                  <span className="font-semibold">marking_acceptance_report.json 路径：</span>
                  {markingAcceptanceResult.report_path}
                </div>
              </div>
            </section>
          ) : null}
          {mainUiProduction ? (
            <div className="grid gap-4">
              {mainUiProduction.style_reference_note ? (
                <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{mainUiProduction.style_reference_note}</p>
              ) : null}
              {mainUiProduction.opencv_candidate_preview_url ? (
                <div className="grid gap-2 rounded-md border border-studio-line p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-medium">
                      OpenCV candidate_preview.png
                      {typeof mainUiProduction.opencv_layer_count === "number" ? `（${mainUiProduction.opencv_layer_count}）` : ""}
                    </div>
                    <button
                      className="rounded-md border border-studio-line px-2 py-1 text-xs"
                      onClick={() =>
                        setExpandedPreview({
                          src: api.getProductionStudioFileUrl(mainUiProduction.opencv_candidate_preview_url || ""),
                          label: "OpenCV candidate_preview.png",
                        })
                      }
                      type="button"
                    >
                      预览
                    </button>
                  </div>
                  <img
                    alt="OpenCV candidate_preview"
                    className="aspect-video w-full rounded-md border border-studio-line bg-slate-950 object-contain"
                    src={api.getProductionStudioFileUrl(mainUiProduction.opencv_candidate_preview_url)}
                  />
                  {mainUiProduction.opencv_layer_manifest_url ? (
                    <a
                      className="w-fit rounded-md border border-studio-line px-2 py-1 text-xs"
                      href={api.getProductionStudioFileUrl(mainUiProduction.opencv_layer_manifest_url)}
                      rel="noreferrer"
                      target="_blank"
                    >
                      打开 layer_manifest.json
                    </a>
                  ) : null}
                </div>
              ) : null}
              <div className="grid gap-3 lg:grid-cols-2">
                <div className="grid gap-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-medium">完整界面预览</div>
                    <button
                      className="rounded-md border border-studio-line px-2 py-1 text-xs"
                      onClick={() =>
                        setExpandedPreview({
                          src: api.getProductionStudioFileUrl(mainUiProduction.main_ui_url),
                          label: "完整界面",
                        })
                      }
                      type="button"
                    >
                      预览
                    </button>
                  </div>
                  <img
                    alt="完整界面预览"
                    className="aspect-video w-full rounded-md border border-studio-line bg-slate-950 object-contain"
                    src={api.getProductionStudioFileUrl(mainUiProduction.main_ui_url)}
                  />
                </div>
                {mainUiProduction.candidate_preview_url ? (
                  <div className="grid gap-2">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-sm font-medium">编号图</div>
                      <button
                        className="rounded-md border border-studio-line px-2 py-1 text-xs"
                        onClick={() =>
                          setExpandedPreview({
                            src: api.getProductionStudioFileUrl(mainUiProduction.candidate_preview_url),
                            label: "候选组件编号图",
                          })
                        }
                        type="button"
                      >
                        预览
                      </button>
                    </div>
                    <img
                      alt="候选组件编号图"
                      className="aspect-video w-full rounded-md border border-studio-line bg-slate-950 object-contain"
                      src={api.getProductionStudioFileUrl(mainUiProduction.candidate_preview_url)}
                    />
                  </div>
                ) : null}
              </div>
              {mainUiProduction.candidate_options?.length ? (
                <div className="grid gap-2 rounded-md border border-studio-line p-3">
                  <div className="font-semibold">候选方案</div>
                  <div className="grid gap-3 md:grid-cols-3">
                    {mainUiProduction.candidate_options.map((option) => (
                      <article className="grid gap-2 rounded-md bg-slate-50 p-2" key={option.candidate_id}>
                        <img
                          alt={`${option.label}预览`}
                          className="aspect-video w-full rounded-md bg-slate-950 object-contain"
                          src={api.getProductionStudioFileUrl(option.url)}
                        />
                        <div className="text-xs font-medium">{option.label}</div>
                        <div className="flex gap-2">
                          <button
                            className="rounded-md border border-studio-line px-2 py-1 text-xs"
                            onClick={() =>
                              setExpandedPreview({
                                src: api.getProductionStudioFileUrl(option.url),
                                label: option.label,
                              })
                            }
                            type="button"
                          >
                            预览
                          </button>
                          <button
                            className="rounded-md border border-studio-line px-2 py-1 text-xs disabled:opacity-60"
                            disabled={mainUiLoading || option.selected}
                            onClick={() => selectUiCandidateOption(option.candidate_id)}
                            type="button"
                          >
                            {option.selected ? "当前方案" : "选择此方案"}
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                </div>
              ) : null}
              <div className="grid gap-2 rounded-md border border-studio-line p-3">
                <div className="font-semibold">主界面布局骨架</div>
                <div className="flex flex-wrap gap-2 text-xs">
                  {["顶部信息区", "右上地图区", "右侧系统入口区", "右下技能区", "左下摇杆区", "聊天区", "底部状态区"].map((zone) => (
                    <span className="rounded-md bg-slate-100 px-2 py-1" key={zone}>
                      {zone}
                    </span>
                  ))}
                </div>
              </div>
              {mainUiProduction.candidates.length ? (
                <div className="overflow-x-auto rounded-md border border-studio-line">
                  <table className="w-full min-w-[1040px] text-left text-sm">
                    <thead className="bg-slate-100 text-xs text-studio-muted">
                      <tr>
                        <th className="px-3 py-2">确认</th>
                        <th className="px-3 py-2">编号</th>
                        <th className="px-3 py-2">组件名称</th>
                        <th className="px-3 py-2">组件类型</th>
                        <th className="px-3 py-2">布局区</th>
                        <th className="px-3 py-2">形状</th>
                        <th className="px-3 py-2">A/B/C</th>
                        <th className="px-3 py-2">输出格式</th>
                        <th className="px-3 py-2">建议动作</th>
                        <th className="px-3 py-2">预览</th>
                      </tr>
                    </thead>
                    <tbody>
                      {mainUiProduction.candidates.map((candidate) => (
                        <tr className="border-t border-studio-line" key={candidate.candidate_id}>
                          <td className="px-3 py-2">
                            <input
                              aria-label={`确认切图 ${candidate.component_id}`}
                              checked={candidate.confirmed}
                              onChange={(event) => updateMainUiCandidate(candidate.candidate_id, event.target.checked)}
                              type="checkbox"
                            />
                          </td>
                          <td className="px-3 py-2">{candidate.number}</td>
                          <td className="px-3 py-2">{candidate.component_name ?? candidate.component_id}</td>
                          <td className="px-3 py-2">{candidate.component_type}</td>
                          <td className="px-3 py-2">{candidate.layout_zone ?? "-"}</td>
                          <td className="px-3 py-2">{candidate.shape_type ?? "rect"}</td>
                          <td className="px-3 py-2">{candidate.level}</td>
                          <td className="px-3 py-2 uppercase">{candidate.output_format}</td>
                          <td className="px-3 py-2">{candidate.recommended_action}</td>
                          <td className="px-3 py-2">
                            {mainUiProduction.candidate_preview_url ? (
                              <button
                                className="rounded-md border border-studio-line px-2 py-1 text-xs"
                                onClick={() =>
                                  setExpandedPreview({
                                    src: api.getProductionStudioFileUrl(mainUiProduction.candidate_preview_url),
                                    label: `编号 ${candidate.number} ${candidate.component_id}`,
                                  })
                                }
                                type="button"
                              >
                                预览
                              </button>
                            ) : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
              {mainUiProduction.confirmed_components.filter((item) => item.file).length ? (
                <div className="grid gap-3">
                  <div className="font-semibold">PNG / JPG 输出预览</div>
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                    {mainUiProduction.confirmed_components
                      .filter((item) => item.file)
                      .map((item) => (
                        <article className="grid gap-2 rounded-md border border-studio-line p-3" key={`${item.component_id}-${item.file}`}>
                          <img
                            alt={`${item.component_id} 输出预览`}
                            className="aspect-video w-full rounded-md bg-slate-950 object-contain"
                            src={api.getProductionStudioFileUrl(item.url)}
                          />
                          <div className="font-mono text-xs">{item.file}</div>
                          <div className="text-xs text-studio-muted">
                            {item.component_type} / {item.format.toUpperCase()} / 透明：
                            {item.has_transparent_pixels ? "是" : "否"}
                          </div>
                          {item.transparent_warning ? <div className="text-xs text-amber-700">透明警告：{item.transparent_warning}</div> : null}
                          <button
                            className="w-fit rounded-md border border-studio-line px-2 py-1 text-xs"
                            onClick={() =>
                              setExpandedPreview({
                                src: api.getProductionStudioFileUrl(item.url),
                                label: item.file,
                              })
                            }
                            type="button"
                          >
                            预览
                          </button>
                        </article>
                      ))}
                  </div>
                </div>
              ) : null}
              {mainUiProduction.package_files?.length ? (
                <div className="grid gap-2 rounded-md border border-studio-line p-3">
                  <div className="font-semibold">996-ready 包清单</div>
                  <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                    {mainUiProduction.package_files.map((item) => (
                      <div className="rounded-md bg-slate-50 p-3 text-sm" key={item.file}>
                        <div className="font-mono text-xs">{item.label}</div>
                        <div className={item.exists ? "mt-1 text-emerald-700" : "mt-1 text-studio-muted"}>
                          {item.exists ? "已生成" : "待生成"}
                        </div>
                        {item.url ? (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {canPreviewPackageFile(item.file) ? (
                              <button
                                className="inline-flex rounded-md border border-studio-line px-2 py-1 text-xs"
                                onClick={() =>
                                  setExpandedPreview({
                                    src: api.getProductionStudioFileUrl(item.url),
                                    label: item.label,
                                  })
                                }
                                type="button"
                              >
                                预览
                              </button>
                            ) : null}
                            <a
                              className="inline-flex rounded-md border border-studio-line px-2 py-1 text-xs"
                              href={api.getProductionStudioFileUrl(item.url)}
                              rel="noreferrer"
                              target="_blank"
                            >
                              查看
                            </a>
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
              <div className="flex flex-wrap gap-2">
                {mainUiProduction.manifest_url ? (
                  <a
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    href={api.getProductionStudioFileUrl(mainUiProduction.manifest_url)}
                    rel="noreferrer"
                    target="_blank"
                  >
                    查看输出包 manifest.json
                  </a>
                ) : null}
                {mainUiProduction.annotation_url ? (
                  <a
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    href={api.getProductionStudioFileUrl(mainUiProduction.annotation_url)}
                    rel="noreferrer"
                    target="_blank"
                  >
                    查看 annotation.json
                  </a>
                ) : null}
                {mainUiProduction.candidate_manifest_url ? (
                  <a
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    href={api.getProductionStudioFileUrl(mainUiProduction.candidate_manifest_url)}
                    rel="noreferrer"
                    target="_blank"
                  >
                    查看 candidate_manifest.json
                  </a>
                ) : null}
                {mainUiProduction.training_samples_url ? (
                  <a
                    className="rounded-md border border-studio-line px-3 py-2 text-sm"
                    href={api.getProductionStudioFileUrl(mainUiProduction.training_samples_url)}
                    rel="noreferrer"
                    target="_blank"
                  >
                    查看 training_samples
                  </a>
                ) : null}
              </div>
            </div>
          ) : null}
        </section>
        <section className="hidden">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-semibold">主界面生产</h3>
              <p className="mt-1 text-xs text-studio-muted">生成、标号、确认、切图、透明 PNG、输出。</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                className="rounded-md bg-studio-action px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
                disabled={mainUiLoading}
                onClick={runMainUiProduction}
                type="button"
              >
                {mainUiLoading ? "处理中..." : "生成主界面实验包"}
              </button>
              <button
                className="rounded-md border border-studio-line bg-white px-3 py-2 text-sm disabled:opacity-60"
                disabled={!mainUiProduction || mainUiLoading}
                onClick={exportMainUiProduction}
                type="button"
              >
                执行确认切图
              </button>
            </div>
          </div>
          {mainUiProduction ? (
            <div className="grid gap-4">
              <div className="grid gap-3 lg:grid-cols-2">
                <div className="grid gap-2">
                  <div className="text-sm font-medium">主界面</div>
                  <img
                    alt="主界面"
                    className="aspect-video w-full rounded-md border border-studio-line bg-slate-950 object-contain"
                    src={api.getProductionStudioFileUrl(mainUiProduction.main_ui_url)}
                  />
                </div>
                <div className="grid gap-2">
                  <div className="text-sm font-medium">编号候选组件</div>
                  <img
                    alt="编号候选组件"
                    className="aspect-video w-full rounded-md border border-studio-line bg-slate-950 object-contain"
                    src={api.getProductionStudioFileUrl(mainUiProduction.candidate_preview_url)}
                  />
                </div>
              </div>
              <div className="overflow-x-auto rounded-md border border-studio-line bg-white">
                <table className="w-full min-w-[780px] text-left text-sm">
                  <thead className="bg-slate-100 text-xs text-studio-muted">
                    <tr>
                      <th className="px-3 py-2">确认</th>
                      <th className="px-3 py-2">编号</th>
                      <th className="px-3 py-2">component_id</th>
                      <th className="px-3 py-2">类型</th>
                      <th className="px-3 py-2">动作</th>
                      <th className="px-3 py-2">等级</th>
                      <th className="px-3 py-2">分类</th>
                      <th className="px-3 py-2">输出</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mainUiProduction.candidates.map((candidate) => (
                      <tr className="border-t border-studio-line" key={candidate.candidate_id}>
                        <td className="px-3 py-2">
                          <input
                            aria-label={`确认切图 ${candidate.component_id}`}
                            checked={candidate.confirmed}
                            onChange={(event) => updateMainUiCandidate(candidate.candidate_id, event.target.checked)}
                            type="checkbox"
                          />
                        </td>
                        <td className="px-3 py-2">{candidate.number}</td>
                        <td className="px-3 py-2 font-mono text-xs">{candidate.component_id}</td>
                        <td className="px-3 py-2">{candidate.component_type}</td>
                        <td className="px-3 py-2">{candidate.recommended_action}</td>
                        <td className="px-3 py-2">{candidate.level}</td>
                        <td className="px-3 py-2">{candidate.production_category}</td>
                        <td className="px-3 py-2">{candidate.output_name}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="grid gap-2 rounded-md border border-studio-line bg-white p-3 text-sm">
                <div className="font-semibold">切图结果</div>
                {mainUiProduction.confirmed_components.filter((item) => item.file).length ? (
                  <ul className="grid gap-2">
                    {mainUiProduction.confirmed_components
                      .filter((item) => item.file)
                      .map((item) => (
                        <li className="grid gap-1 rounded-md bg-slate-50 p-2" key={`${item.component_id}-${item.file}`}>
                          <a
                            className="font-mono text-xs text-studio-action"
                            href={api.getProductionStudioFileUrl(item.url)}
                            rel="noreferrer"
                            target="_blank"
                          >
                            {item.file}
                          </a>
                          {item.transparent_warning ? (
                            <span className="text-xs text-amber-700">transparent_warning: {item.transparent_warning}</span>
                          ) : null}
                        </li>
                      ))}
                  </ul>
                ) : (
                  <p className="text-studio-muted">还没有 confirmed_components 输出。</p>
                )}
                <div className="flex flex-wrap gap-2">
                  <a
                    className="rounded-md border border-studio-line px-3 py-2"
                    href={api.getProductionStudioFileUrl(mainUiProduction.candidate_manifest_url)}
                    rel="noreferrer"
                    target="_blank"
                  >
                    查看 candidate_manifest.json
                  </a>
                  {mainUiProduction.production_review_url ? (
                    <a
                      className="rounded-md border border-studio-line px-3 py-2"
                      href={api.getProductionStudioFileUrl(mainUiProduction.production_review_url)}
                      rel="noreferrer"
                      target="_blank"
                    >
                      查看 production_review.json
                    </a>
                  ) : null}
                  {mainUiProduction.manual_acceptance_url ? (
                    <a
                      className="rounded-md border border-studio-line px-3 py-2"
                      href={api.getProductionStudioFileUrl(mainUiProduction.manual_acceptance_url)}
                      rel="noreferrer"
                      target="_blank"
                    >
                      查看 manual_acceptance.json
                    </a>
                  ) : null}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm leading-6 text-studio-muted">点击生成主界面实验包后，这里会显示主界面、编号图、候选组件、确认状态和切图结果。</p>
          )}
        </section>
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
              const review = item.production_review ?? {};
              const blockersCount = review.blockers?.length ?? 0;
              const warningsCount = review.warnings?.length ?? 0;
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
                  <section className="grid gap-3 rounded-md border border-studio-line bg-white p-3 text-sm">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                      <h4 className="font-semibold">Production Review Card</h4>
                      <span className={review.production_ready ? "font-semibold text-green-700" : "font-semibold text-red-700"}>
                        {review.production_ready ? "ready" : "blocked"}
                      </span>
                    </div>
                    <dl className="grid gap-2 sm:grid-cols-2">
                      <div>
                        <dt className="font-medium">Production Score</dt>
                        <dd className="text-studio-muted">{review.production_score ?? "n/a"}</dd>
                      </div>
                      <div>
                        <dt className="font-medium">Ready Status</dt>
                        <dd className="text-studio-muted">{review.production_ready ? "ready" : "blocked"}</dd>
                      </div>
                      <div>
                        <dt className="font-medium">A/B/C</dt>
                        <dd className="text-studio-muted">
                          {review.level_a_count ?? 0} / {review.level_b_count ?? 0} / {review.level_c_count ?? 0}
                        </dd>
                      </div>
                      <div>
                        <dt className="font-medium">Screen/Panel/Atomic/Effect/Ignore</dt>
                        <dd className="text-studio-muted">
                          {review.screen_count ?? 0} / {review.panel_count ?? 0} / {review.atomic_count ?? 0} /{" "}
                          {review.effect_count ?? 0} / {review.ignore_count ?? 0}
                        </dd>
                      </div>
                      <div>
                        <dt className="font-medium">blockers</dt>
                        <dd className="text-studio-muted">{blockersCount}</dd>
                      </div>
                      <div>
                        <dt className="font-medium">warnings</dt>
                        <dd className="text-studio-muted">{warningsCount}</dd>
                      </div>
                      <div>
                        <dt className="font-medium">transparent_issues</dt>
                        <dd className="text-studio-muted">{review.transparent_issues ?? 0}</dd>
                      </div>
                      <div>
                        <dt className="font-medium">manual_acceptance_status</dt>
                        <dd className="text-studio-muted">{record.status}</dd>
                      </div>
                    </dl>
                    {item.production_review_warning ? (
                      <p className="text-sm text-amber-700">{item.production_review_warning}</p>
                    ) : null}
                    <div className="flex flex-wrap gap-2">
                      {item.production_review_url ? (
                        <a
                          className="rounded-md border border-studio-line px-3 py-2 text-sm"
                          href={api.getProductionStudioFileUrl(item.production_review_url)}
                          rel="noreferrer"
                          target="_blank"
                        >
                          View production_review.json
                        </a>
                      ) : null}
                      {item.component_review_url ? (
                        <a
                          className="rounded-md border border-studio-line px-3 py-2 text-sm"
                          href={api.getProductionStudioFileUrl(item.component_review_url)}
                          rel="noreferrer"
                          target="_blank"
                        >
                          View component_review_analysis.json
                        </a>
                      ) : null}
                      {item.manual_acceptance_url ? (
                        <a
                          className="rounded-md border border-studio-line px-3 py-2 text-sm"
                          href={api.getProductionStudioFileUrl(item.manual_acceptance_url)}
                          rel="noreferrer"
                          target="_blank"
                        >
                          View manual_acceptance.json
                        </a>
                      ) : null}
                      {item.production_review_html_url ? (
                        <a
                          className="rounded-md border border-studio-line px-3 py-2 text-sm"
                          href={api.getProductionStudioFileUrl(item.production_review_html_url)}
                          rel="noreferrer"
                          target="_blank"
                        >
                          View production_review.html
                        </a>
                      ) : null}
                    </div>
                  </section>
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
                          persistAcceptance(item.package_dir, item.generation_job_id, {
                            status: event.target.value as ManualAcceptanceStatus,
                            notes: record.notes,
                          })
                        }
                        value={record.status}
                      >
                        <option value="pending">待验收</option>
                        <option value="accepted">验收通过</option>
                        <option value="rejected">验收拒绝</option>
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
