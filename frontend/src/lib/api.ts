export type Project = {
  id: string;
  name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ProjectInput = {
  name: string;
  description: string;
  status: string;
};

export type StyleProfile = {
  id: string;
  project_id: string;
  name: string;
  description: string;
  palette_json: string;
  prompt_notes: string;
  created_at: string;
  updated_at: string;
};

export type StyleProfileInput = {
  project_id: string;
  name: string;
  description: string;
  palette_json: string;
  prompt_notes: string;
};

export type BasePanel = {
  id: string;
  project_id: string;
  style_profile_id: string;
  panel_type:
    | "main_panel"
    | "sub_panel"
    | "popup_panel"
    | "list_panel"
    | "input_panel"
    | "button_panel"
    | "icon_panel";
  device_type: string;
  width: number;
  height: number;
  texture: string;
  border_style: string;
  background_style: string;
  color_scheme: string;
  created_at: string;
  updated_at: string;
};

export type BasePanelInput = Omit<BasePanel, "id" | "created_at" | "updated_at">;

export type GenerationJob = {
  id: string;
  project_id: string | null;
  provider_id: string | null;
  job_type: string;
  status: string;
  progress: number;
  input_json: string;
  output_json: string;
  output_preview_path: string;
  error_message: string;
  retry_count: number;
  logs: string;
  created_at: string;
  updated_at: string;
};

export type GenerationJobInput = {
  project_id: string | null;
  provider_id?: string | null;
  job_type: string;
  status: string;
  progress: number;
  input_json: string;
  output_json: string;
  output_preview_path?: string;
  error_message: string;
  logs: string;
  auto_run?: boolean;
};

export type MockUiGenerationInput = {
  project_id: string | null;
  device_type: string;
  width: number;
  height: number;
};

export type Asset = {
  id: string;
  project_id: string | null;
  asset_type:
    | "reference_image"
    | "ui_preview"
    | "annotated_preview"
    | "sliced_component"
    | "base_panel"
    | "icon";
  device_type: string;
  width: number;
  height: number;
  file_path: string;
  original_filename: string;
  metadata_json: string;
  source: "uploaded" | "mock_generated" | "ai_generated" | "real_pipeline_placeholder" | "component_processing";
  generation_job_id: string | null;
  thumbnail_path: string;
  created_at: string;
  updated_at: string;
};

export type AiProvider = {
  id: string;
  name: string;
  type: "mock" | "openai" | "openrouter" | "ofox" | "custom";
  enabled: boolean;
  config_json: string;
  created_at: string;
  updated_at: string;
};

export type AiProviderInput = {
  name: string;
  type: AiProvider["type"];
  enabled: boolean;
  config_json: string;
};

export type ProviderHealth = {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  status: string;
  message: string;
};

export type UploadAssetInput = {
  file: File;
  project_id: string | null;
  asset_type: Asset["asset_type"];
  device_type: string;
};

export type ComponentProcessingResult = {
  manifest_path: string;
  annotation_path: string;
  preview_html_path: string;
  candidate_manifest_path?: string;
  candidate_preview_html_path?: string;
  component_quality_report_path?: string;
  component_quality_report_html_path?: string;
  component_asset_ids: string[];
};

export type ProductionDeviceType = "mobile_landscape" | "pc_landscape";
export type ProductionAssetMode = "ui_package" | "resource_production";
export type ProductionStyleSource = "new_style" | "existing_style";
export type ProductionScreenType = "main_ui" | "role_ui" | "bag_ui" | "shop_ui" | "activity_ui";
export type ProductionLayoutTemplate =
  | "classic_legend_mobile"
  | "legend_176"
  | "legend_185_combo"
  | "silent_version"
  | "hot_blood";
export type ProductionGenerationMode = "auto_generate" | "reference_guided";

export type ProductionStudioStyleCode = {
  style_code: string;
  style_name: string;
  source_job_id: string;
  device_type: string;
};

export type ProductionStudioInput = {
  device_type: ProductionDeviceType;
  asset_mode: ProductionAssetMode;
  style_source: ProductionStyleSource;
  style_code?: string | null;
  screen_types: ProductionScreenType[];
  layout_template: ProductionLayoutTemplate;
  generation_mode: ProductionGenerationMode;
  reference_image_path?: string | null;
  style_name: string;
  prompt: string;
};

export type ManualAcceptanceStatus = "pending" | "accepted" | "rejected";

export type ManualAcceptance = {
  review_status: ManualAcceptanceStatus;
  reviewer: string;
  remarks: string;
  updated_at: string;
  accepted_at: string | null;
  accepted_by: string;
  components: unknown[];
};

export type ProductionReviewSummary = {
  production_score?: number;
  production_ready?: boolean;
  level_a_count?: number;
  level_b_count?: number;
  level_c_count?: number;
  screen_count?: number;
  panel_count?: number;
  atomic_count?: number;
  effect_count?: number;
  ignore_count?: number;
  blockers?: string[];
  warnings?: string[];
  transparent_issues?: number;
};

export type ProductionStudioScreenResult = {
  screen_type: ProductionScreenType;
  generation_job_id: string;
  status: string;
  package_dir: string;
  ui_preview_url: string;
  delivery_report_url: string;
  candidate_preview_url: string;
  component_quality_report_url: string;
  components_count: number;
  candidates_count: number;
  validator_ok: boolean;
  missing_semantic_icons: boolean;
  common_icons_note: string;
  production_review?: ProductionReviewSummary;
  manual_acceptance_status?: ManualAcceptanceStatus;
  production_review_url?: string;
  component_review_url?: string;
  manual_acceptance_url?: string;
  production_review_html_url?: string;
  production_review_warning?: string;
};

export type ProductionStudioResult = {
  style_code: string;
  device_type: ProductionDeviceType;
  asset_mode: ProductionAssetMode;
  style_source: ProductionStyleSource;
  layout_template: ProductionLayoutTemplate;
  generation_mode: ProductionGenerationMode;
  reference_image_path?: string | null;
  final_prompt: string;
  results: ProductionStudioScreenResult[];
};

export type MainUiProductionCandidate = {
  candidate_id: string;
  component_id: string;
  component_name?: string;
  component_type: string;
  number: number;
  bounds: { x: number; y: number; width: number; height: number };
  bbox?: { x: number; y: number; width: number; height: number };
  outline_points?: Array<{ x: number; y: number }>;
  layout_zone?: string;
  shape_type?: "rect" | "circle" | "composite";
  level: "A" | "B" | "C";
  production_category: "Screen" | "Panel" | "Atomic" | "Effect" | "Ignore";
  recommended_action: string;
  confirmed: boolean;
  output_format: "png" | "jpg";
  output_name: string;
  transparent_required: boolean;
  transparent_warning?: string;
  image_path?: string;
};

export type MainUiConfirmedComponent = {
  component_id: string;
  component_type: string;
  number: number;
  confirmed: boolean;
  file: string;
  format: string;
  transparent_required?: boolean;
  has_transparent_pixels?: boolean;
  transparent_warning: string;
  url: string;
};

export type MainUiPackageFile = {
  label: string;
  file: string;
  exists: boolean;
  url: string;
};

export type MainUiCandidateOption = {
  candidate_id: string;
  label: string;
  file: string;
  selected?: boolean;
  url: string;
};

export type MainUiProjectContext = {
  project_name: string;
  screen_type: string;
  style_package_name: string;
  style_notes: string;
  reference_status: string;
};

export type MainUiProductionResult = {
  package_dir: string;
  main_ui_url: string;
  candidate_preview_url: string;
  candidate_manifest_url: string;
  manifest_url?: string;
  annotation_url?: string;
  production_review_url: string;
  manual_acceptance_url: string;
  confirmed_components_url: string;
  candidates: MainUiProductionCandidate[];
  confirmed_components: MainUiConfirmedComponent[];
  package_files?: MainUiPackageFile[];
  candidate_options?: MainUiCandidateOption[];
  selected_candidate_id?: string;
  style_reference_strength?: string;
  style_reference_note?: string;
  project_context?: MainUiProjectContext;
  training_samples_url?: string;
  exported_count?: number;
};

export type MarkingAcceptanceResult = {
  project_code: "MARKING_TEST";
  candidate_id: string;
  total_marks: number;
  by_type: {
    background: number;
    panel: number;
    button: number;
    icon: number;
    skill: number;
  };
  slice_success: number;
  slice_failed: number;
  missing_required: string[];
  warnings: string[];
  project: Project;
  candidate_preview_url: string;
  candidate_preview_path: string;
  manifest_path: string;
  marking_json_path: string;
  manual_acceptance_path: string;
  training_samples_path: string;
  harness_dir: string;
  report_path: string;
  production: MainUiProductionResult;
};

export type PromptSampleSuggestion = {
  found: boolean;
  sample_id?: string;
  system_prompt?: string;
  final_prompt?: string;
  quality?: string;
  updated_at?: string;
};

export type ListResponse<T> = {
  items: T[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

function apiUrl(path: string) {
  return `${API_BASE_URL}${path}`;
}

async function responseErrorMessage(url: string, response: Response) {
  let detail = `API request failed`;
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") {
      detail = body.detail;
    } else if (Array.isArray(body?.detail)) {
      detail = body.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join("; ") || detail;
    }
  } catch {
    // Keep the generic message when the response body is not JSON.
  }
  return `请求失败：${url}，status=${response.status}，error=${detail}`;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = apiUrl(path);
  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });
  } catch (exc) {
    throw new Error(`请求失败：${url}，status=network_error，error=${exc instanceof Error ? exc.message : "unknown"}`);
  }

  if (!response.ok) {
    throw new Error(await responseErrorMessage(url, response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function uploadRequest<T>(path: string, formData: FormData): Promise<T> {
  const url = apiUrl(path);
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      body: formData,
    });
  } catch (exc) {
    throw new Error(`请求失败：${url}，status=network_error，error=${exc instanceof Error ? exc.message : "unknown"}`);
  }

  if (!response.ok) {
    throw new Error(await responseErrorMessage(url, response));
  }

  return response.json() as Promise<T>;
}

export const studioApi = {
  createProject(payload: ProjectInput) {
    return request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  deleteProject(projectId: string) {
    return request<void>(`/projects/${projectId}`, { method: "DELETE" });
  },
  getProject(projectId: string) {
    return request<Project>(`/projects/${projectId}`);
  },
  listProjects() {
    return request<ListResponse<Project>>("/projects");
  },
  updateProject(projectId: string, payload: ProjectInput) {
    return request<Project>(`/projects/${projectId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
  createStyleProfile(payload: StyleProfileInput) {
    return request<StyleProfile>("/style_profiles", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  deleteStyleProfile(styleProfileId: string) {
    return request<void>(`/style_profiles/${styleProfileId}`, { method: "DELETE" });
  },
  listStyleProfiles(projectId?: string) {
    const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
    return request<ListResponse<StyleProfile>>(`/style_profiles${query}`);
  },
  updateStyleProfile(styleProfileId: string, payload: StyleProfileInput) {
    return request<StyleProfile>(`/style_profiles/${styleProfileId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
  copyBasePanel(basePanelId: string) {
    return request<BasePanel>(`/base_panels/${basePanelId}/copy`, { method: "POST" });
  },
  createBasePanel(payload: BasePanelInput) {
    return request<BasePanel>("/base_panels", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  deleteBasePanel(basePanelId: string) {
    return request<void>(`/base_panels/${basePanelId}`, { method: "DELETE" });
  },
  getBasePanel(basePanelId: string) {
    return request<BasePanel>(`/base_panels/${basePanelId}`);
  },
  listBasePanels(projectId?: string) {
    const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
    return request<ListResponse<BasePanel>>(`/base_panels${query}`);
  },
  updateBasePanel(basePanelId: string, payload: BasePanelInput) {
    return request<BasePanel>(`/base_panels/${basePanelId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
  listGenerationJobs(projectId?: string) {
    const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
    return request<ListResponse<GenerationJob>>(`/generation_jobs${query}`);
  },
  createGenerationJob(payload: GenerationJobInput) {
    return request<GenerationJob>("/generation_jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getGenerationJob(generationJobId: string) {
    return request<GenerationJob>(`/generation_jobs/${generationJobId}`);
  },
  retryGenerationJob(generationJobId: string) {
    return request<GenerationJob>(`/generation_jobs/${generationJobId}/retry`, { method: "POST" });
  },
  createMockUiGenerationJob(payload: MockUiGenerationInput) {
    return request<GenerationJob>("/generation_jobs/mock-ui", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  runMockGenerationJob(generationJobId: string) {
    return request<GenerationJob>(`/generation_jobs/${generationJobId}/run-mock`, { method: "POST" });
  },
  runGenerationJob(generationJobId: string) {
    return request<GenerationJob>(`/generation_jobs/${generationJobId}/run`, { method: "POST" });
  },
  listGenerationJobResults(generationJobId: string) {
    return request<ListResponse<Asset>>(`/generation_jobs/${generationJobId}/results`);
  },
  updateGenerationJob(generationJobId: string, payload: Partial<GenerationJobInput>) {
    return request<GenerationJob>(`/generation_jobs/${generationJobId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  deleteAsset(assetId: string) {
    return request<void>(`/assets/${assetId}`, { method: "DELETE" });
  },
  processAssetComponents(assetId: string) {
    return request<ComponentProcessingResult>(`/assets/${assetId}/process-components`, { method: "POST" });
  },
  listProductionStyleCodes() {
    return request<ListResponse<ProductionStudioStyleCode>>("/production-studio/style-codes");
  },
  generateProductionStudioPackage(payload: ProductionStudioInput) {
    return request<ProductionStudioResult>("/production-studio/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateProductionManualAcceptance(packageDir: string, payload: Partial<ManualAcceptance>) {
    return request<ManualAcceptance>(`/production-studio/manual-acceptance?package_dir=${encodeURIComponent(packageDir)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
  runMainUiProduction() {
    return request<MainUiProductionResult>("/production-studio/main-ui-production/run", { method: "POST" });
  },
  generateUiProductionPackage(payload: {
    screen_type: string;
    reference_image_path?: string | null;
    system_prompt?: string;
    requirement: string;
    style_reference_strength: string;
    project_id?: string;
    device_type?: string;
    layout_template?: string;
    adjustment_note?: string;
    adjustment_image_path?: string | null;
  }) {
    return request<MainUiProductionResult | { status: "placeholder"; screen_type: string; message: string }>(
      "/production-studio/ui-production/generate",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },
  selectUiProductionCandidate(packageDir: string, candidateId: string) {
    return request<MainUiProductionResult>(
      `/production-studio/ui-production/select-candidate?package_dir=${encodeURIComponent(packageDir)}&candidate_id=${encodeURIComponent(candidateId)}`,
      { method: "POST" },
    );
  },
  markUiProductionCandidates(packageDir: string) {
    return request<MainUiProductionResult>(
      `/production-studio/ui-production/mark-candidates?package_dir=${encodeURIComponent(packageDir)}`,
      { method: "POST" },
    );
  },
  updateUiProductionCandidate(packageDir: string, candidateId: string, confirmed: boolean) {
    return request<MainUiProductionCandidate>(
      `/production-studio/ui-production/candidate?package_dir=${encodeURIComponent(packageDir)}&candidate_id=${encodeURIComponent(candidateId)}`,
      {
        method: "PUT",
        body: JSON.stringify({ confirmed }),
      },
    );
  },
  exportUiProductionComponents(packageDir: string) {
    return request<MainUiProductionResult>(
      `/production-studio/ui-production/export?package_dir=${encodeURIComponent(packageDir)}`,
      { method: "POST" },
    );
  },
  runMarkingAcceptanceTest(payload: {
    reference_image_path?: string | null;
    system_prompt?: string;
    requirement: string;
    style_reference_strength: string;
    project_id?: string;
    device_type?: string;
    layout_template?: string;
    adjustment_note?: string;
    adjustment_image_path?: string | null;
  }) {
    return request<MarkingAcceptanceResult>("/production-studio/marking-acceptance-test/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getPromptSampleSuggestion(params: { interface_type: string; device_type: string; layout_template: string }) {
    const query = new URLSearchParams(params).toString();
    return request<PromptSampleSuggestion>(`/production-studio/prompt-samples/best?${query}`);
  },
  getMainUiProduction(packageDir: string) {
    return request<MainUiProductionResult>(
      `/production-studio/main-ui-production?package_dir=${encodeURIComponent(packageDir)}`,
    );
  },
  updateMainUiCandidate(packageDir: string, candidateId: string, confirmed: boolean) {
    return request<MainUiProductionCandidate>(
      `/production-studio/main-ui-production/candidate?package_dir=${encodeURIComponent(packageDir)}&candidate_id=${encodeURIComponent(candidateId)}`,
      {
        method: "PUT",
        body: JSON.stringify({ confirmed }),
      },
    );
  },
  exportMainUiProduction(packageDir: string) {
    return request<MainUiProductionResult>(
      `/production-studio/main-ui-production/export?package_dir=${encodeURIComponent(packageDir)}`,
      { method: "POST" },
    );
  },
  listAssets(projectId?: string, assetType?: string, deviceType?: string, generationJobId?: string) {
    const params = new URLSearchParams();
    if (projectId) {
      params.set("project_id", projectId);
    }
    if (assetType) {
      params.set("asset_type", assetType);
    }
    if (deviceType) {
      params.set("device_type", deviceType);
    }
    if (generationJobId) {
      params.set("generation_job_id", generationJobId);
    }
    const query = params.toString() ? `?${params.toString()}` : "";
    return request<ListResponse<Asset>>(`/assets${query}`);
  },
  getAssetFileUrl(assetId: string) {
    return `${API_BASE_URL}/assets/${assetId}/file`;
  },
  getAssetThumbnailUrl(assetId: string) {
    return `${API_BASE_URL}/assets/${assetId}/thumbnail`;
  },
  getProductionStudioFileUrl(path: string) {
    return path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
  },
  uploadAsset(payload: UploadAssetInput) {
    const formData = new FormData();
    formData.append("file", payload.file);
    if (payload.project_id) {
      formData.append("project_id", payload.project_id);
    }
    formData.append("asset_type", payload.asset_type);
    formData.append("device_type", payload.device_type);
    return uploadRequest<Asset>("/assets/upload", formData);
  },
  createAiProvider(payload: AiProviderInput) {
    return request<AiProvider>("/ai_providers", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  listAiProviders() {
    return request<ListResponse<AiProvider>>("/ai_providers");
  },
  updateAiProvider(providerId: string, payload: AiProviderInput) {
    return request<AiProvider>(`/ai_providers/${providerId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
  getAiProviderHealth(providerId: string) {
    return request<ProviderHealth>(`/ai_providers/${providerId}/health`);
  },
  listAiProviderHealth() {
    return request<ListResponse<ProviderHealth>>("/ai_providers/health");
  },
};
