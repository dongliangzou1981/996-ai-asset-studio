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
  project_id: string;
  job_type: string;
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
};

export type ListResponse<T> = {
  items: T[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
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
};
