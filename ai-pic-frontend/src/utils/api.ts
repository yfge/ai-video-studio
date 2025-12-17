// API 基础配置：默认使用相对路径，生产通过反向代理到后端
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

// 通用响应类型
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 用户相关类型
export interface User {
  id: number;
  business_id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  is_admin: boolean;
  is_approved: boolean;
  email_verified: boolean;
  last_login_at?: string;
  failed_login_attempts: number;
  is_account_locked: boolean;
  language?: string;
  timezone?: string;
  created_at: string;
  updated_at?: string;
}

export interface AdminUser extends User {
  approved_at?: string;
  approved_by_user_id?: number;
  activation_token_expires?: string;
  account_locked_until?: string;
}

export interface UserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface UserStatsResponse {
  total_users: number;
  active_users: number;
  pending_approval: number;
  suspended_users: number;
  admin_users: number;
  recent_registrations: number;
}

export interface UserApprovalRequest {
  action: "approve" | "reject";
  reason?: string;
}

export interface UserAuditLog {
  id: number;
  user_id: number;
  admin_user_id?: number;
  action: string;
  old_values?: string;
  new_values?: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

// 任务相关类型
export interface Task {
  id: number;
  business_id: string;
  title: string;
  task_type?: string;
  prompt?: string;
  parameters?: Record<string, unknown> | null;
  status: "pending" | "processing" | "completed" | "failed";
  progress_detail?: string;
  created_at: string;
  updated_at?: string;
  description?: string;
  result_file_path?: string;
  error_message?: string;
  user_id: number;
  target_business_id?: string | null;
}

export interface CreateTaskRequest {
  title: string;
  prompt: string;
  platform: string;
  model_id?: string;
  model_name?: string;
  count?: number;
}

// 图片相关类型
export interface ImageItem {
  id: string;
  title: string;
  prompt: string;
  platform: "gpt" | "keling" | "jimeng";
  imageUrl: string;
  createdAt: string;
  tags: string[];
  userId: string;
}

// 虚拟IP图像相关类型
export interface VirtualIPImage {
  id: number;
  business_id: string;
  virtual_ip_id: number;
  virtual_ip_business_id?: string | null;
  file_path: string;
  oss_url?: string;
  category: string;
  subcategory?: string | null;
  tags: string[];
  prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, unknown>;
  is_default: boolean;
  is_public?: boolean;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface VirtualIPImageCreate {
  virtual_ip_id: number;
  file_path: string;
  category: string;
  tags: string[];
  is_default: boolean;
  metadata?: Record<string, unknown>;
}

export interface VirtualIPImageUpdate {
  category?: string;
  tags?: string[];
  is_default?: boolean;
  metadata?: Record<string, unknown>;
}

// 风格 schema（后端为唯一真源）
export interface StyleOption {
  value: string;
  label: string;
}

export type StyleSpec = Partial<{
  style_universe: string;
  character_proportion: string;
  character_face_style: string;
  line_art_style: string;
  color_render_style: string;
  lighting_style: string;
  color_mood: string;
  shot_storyboard_style: string;
  composition_style: string;
  background_detail_level: string;
  emotion_action_level: string;
  style_lock_level: string;
  output_target: string;
}>;

export interface StylePreset {
  preset_id: string;
  label: string;
  description?: string | null;
  spec: StyleSpec;
}

export interface StyleSchemaResponse {
  dimensions: Record<string, StyleOption[]>;
  defaults: StyleSpec;
}

export interface AIImageGenerationRequest {
  style: string;
  style_preset_id?: string;
  style_spec?: StyleSpec;
  category: string;
  model: string;
  additional_prompts: string;
  is_default: boolean;
  count?: number;
  size?: string;
}

export interface ImageToImageRequestPayload {
  image_url: string;
  prompt?: string;
  model?: string;
  prefer_provider?: string;
  style?: string;
  style_preset_id?: string;
  style_spec?: StyleSpec;
  count?: number;
  size?: string;
  reference_images?: string[];
}

export interface StoryboardVideoGenerationOptions {
  prompt?: string;
  model?: string;
  duration?: number;
  fps?: number;
  resolution?: string;
  ratio?: string;
  watermark?: boolean;
  seed?: number;
  camera_fixed?: boolean;
  service_tier?: string;
  execution_expires_after?: number;
  return_last_frame?: boolean;
}

export interface AIModel {
  model_id: string;
  id?: string;
  name: string;
  provider: string;
  type: string;
  capabilities: string[];
}

export interface VoiceOption {
  value: string;
  label_zh: string;
  label_en: string;
}

export interface VoiceItem {
  voice_id: string;
  voice_name?: string;
  description?: string[];
  created_time?: string;
}

export interface VoiceEnums {
  providers: VoiceOption[];
  tts_models: VoiceOption[];
  voice_types: VoiceOption[];
  emotions: VoiceOption[];
  language_boost: VoiceOption[];
  output_formats: VoiceOption[];
  audio_formats: VoiceOption[];
  sample_rates: VoiceOption[];
  bitrates: VoiceOption[];
  channels: VoiceOption[];
  music_models: VoiceOption[];
  defaults?: {
    tts_model?: string;
    voice_id?: string;
    output_format?: string;
    music_model?: string;
  };
  system_voices?: Array<VoiceOption & { language?: string }>;
}

export interface VoiceList {
  system_voice?: VoiceItem[];
  voice_cloning?: VoiceItem[];
  voice_generation?: VoiceItem[];
  trace_id?: string;
  base_resp?: Record<string, unknown>;
}

export interface VoiceConfig {
  provider?: string;
  model?: string;
  voice_type?: string;
  voice_id?: string;
  display_name?: string;
  sample_url?: string;
}

export interface VoicePreviewResponse {
  audio_url?: string | null;
  audio_hex?: string | null;
  subtitle_file?: string | null;
  trace_id?: string | null;
  extra_info?: Record<string, unknown>;
  base_resp?: Record<string, unknown>;
}

// AI模型类型常量 (对应后端 AIModelType)
export const AIModelType = {
  Text: "text_generation",
  Image: "text_to_image",
  Video: "text_to_video",
  Audio: "text_to_speech",
  SpeechToText: "speech_to_text",
  ImageToImage: "image_to_image",
  ImageToVideo: "image_to_video",
  ImageUnderstanding: "image_understanding",
  VideoUnderstanding: "video_understanding",
} as const;

export type AIModelType = (typeof AIModelType)[keyof typeof AIModelType];

export interface AvailableModelsResponse {
  models: AIModel[];
  default?: string;
  count?: number;
}

// 虚拟IP相关类型
export interface VirtualIP {
  id: number;
  business_id: string;
  name: string;
  default_avatar_url?: string;
  description?: string;
  tags: string[];
  background_story?: string;
  biography?: string;
  style_prompt?: string;
  style_reference_images?: string[];
  voice_config?: VoiceConfig;
  is_active: boolean;
  is_public: boolean;
  created_at: string;
  updated_at?: string;
  images?: VirtualIPImage[];
}

export interface CreateVirtualIPRequest {
  name: string;
  description?: string;
  tags?: string[];
  background_story?: string;
  biography?: string;
  style_prompt?: string;
  style_reference_images?: string[];
  voice_config?: VoiceConfig;
  is_active?: boolean;
  is_public?: boolean;
}

export interface UpdateVirtualIPRequest {
  name?: string;
  description?: string;
  tags?: string[];
  background_story?: string;
  biography?: string;
  style_prompt?: string;
  style_reference_images?: string[];
  voice_config?: VoiceConfig;
  is_active?: boolean;
  is_public?: boolean;
}

// AI增强虚拟IP创建相关类型
export interface VirtualIPAICreateRequest {
  name: string;
  basic_info?: string;
  style_preference?: string;
  tags?: string[];
  is_active?: boolean;
  is_public?: boolean;
}

export interface VirtualIPAIGenerationRequest {
  name: string;
  basic_info?: string;
  style_preference?: string;
  image_category?: string;
}

export interface VirtualIPAIGenerationResponse {
  description: string;
  background_story: string;
  biography: string;
  style_prompt: string;
}

export interface AIGenerationDetails {
  model: string;
  temperature: number;
  prompts_used: string[];
  tokens_used: number;
  generation_time: number;
  steps: string[];
}

export interface VirtualIPAIGenerationDetailedResponse {
  description: string;
  background_story: string;
  biography: string;
  style_prompt: string;
  generation_details: AIGenerationDetails;
}

// 剧本相关类型
export interface StoryCharacter {
  id: number;
  business_id: string;
  story_id: number;
  virtual_ip_id: number;
  character_name?: string;
  role_type?: string;
  importance: number;
  personality?: string;
  background?: string;
  motivation?: string;
  character_arc?: string;
  relationships?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Story {
  id: number;
  business_id: string;
  title: string;
  genre: string;
  theme?: string;
  target_audience?: string;
  duration_minutes?: number;
  premise?: string;
  synopsis?: string;
  main_conflict?: string;
  resolution?: string;
  main_characters?: unknown[];
  character_relationships?: Record<string, unknown>;
  setting_time?: string;
  setting_location?: string;
  world_building?: string;
  status: string;
  is_public: boolean;
  tags?: string[];
  metadata?: Record<string, unknown>;
  extra_metadata?: Record<string, unknown>;
  generation_prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  story_characters?: StoryCharacter[];
}

export interface Episode {
  id: number;
  business_id: string;
  story_id: number;
  story_business_id?: string | null;
  episode_number: number;
  title: string;
  summary?: string;
  plot_points?: unknown[];
  character_arcs?: Record<string, unknown>;
  conflicts?: unknown[];
  duration_minutes?: number;
  scene_count?: number;
  status: string;
  tags?: string[];
  extra_metadata?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  generation_prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Script {
  id: number;
  business_id: string;
  episode_id: number;
  episode_business_id?: string | null;
  title: string;
  content?: string;
  scenes?: unknown[];
  dialogues?: unknown[];
  stage_directions?: unknown[];
  format_type: string;
  language: string;
  page_count?: number;
  word_count?: number;
  character_count?: number;
  status: string;
  version: string;
  tags?: string[];
  extra_metadata?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  generation_prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type StoryboardVideoGenerationMeta = {
  duration?: number;
  provider?: string;
  model?: string;
  method?: string;
  prompt?: string;
  resolution?: string;
  ratio?: string;
  start_image_url?: string;
  end_image_url?: string;
  thumbnail_url?: string;
  last_frame_url?: string;
} & Record<string, unknown>;

export type StoryboardFrame = {
  frame_id?: string;
  frame_number?: number;
  scene_number?: number | string;
  scene_index?: number;
  shot_type?: string;
  camera_movement?: string;
  composition?: string;
  description?: string;
  duration_seconds?: number;
  start_ms?: number;
  end_ms?: number;
  ai_prompt?: string;
  reference_images?: string[];
  image_url?: string;
  start_image_url?: string;
  start_image_urls?: string[];
  end_image_url?: string;
  end_image_urls?: string[];
  video_url?: string;
  video_url_original?: string;
  video_urls?: string[];
  video_thumbnail_url?: string;
  video_thumbnail_url_original?: string;
  video_thumbnail_urls?: string[];
  video_last_frame_url?: string;
  video_last_frame_url_original?: string;
  video_last_frame_urls?: string[];
  video_generation?: StoryboardVideoGenerationMeta;
  generation_source?: string;
  generation_method?: string;
  generation_model?: string;
  status?: string;
  generated_at?: string;
  updated_at?: string;
} & Record<string, unknown>;

export type StoryboardMeta = {
  version?: number;
  updated_at?: string;
  generation_source?: string;
  generation_method?: string;
  generation_model?: string;
  provider?: string;
  scene_scope?: number[] | null;
} & Record<string, unknown>;

export type StoryboardPlanFrame = {
  shot_type?: string;
  camera_movement?: string;
  composition?: string;
  intent?: string;
} & Record<string, unknown>;

export type StoryboardPlanScene = {
  scene_number: number;
  target_frames: number;
  frames: StoryboardPlanFrame[];
};

export type StoryboardPlan = {
  scenes: StoryboardPlanScene[];
} & Record<string, unknown>;

export interface StoryboardPayload {
  frames: StoryboardFrame[];
  meta?: StoryboardMeta;
  plan?: StoryboardPlan;
}

// 环境资产
export interface Environment {
  id: number;
  name: string;
  category?: string | null;
  tags?: string[] | null;
  description?: string | null;
  reference_images?: string[] | null;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentCreate {
  name: string;
  category?: string;
  tags?: string[];
  description?: string;
  reference_images?: string[];
  metadata?: Record<string, unknown>;
}

export interface EnvironmentImagesResponse {
  images: { url: string }[];
  count: number;
}

// 规范化结构类型
export interface NormalizedScene {
  id: number;
  scene_number: string;
  slug_line: string;
  status: string;
  environment_id?: number | null;
  environment_type?: string | null;
  location?: string | null;
  time_of_day?: string | null;
  summary?: string | null;
  metadata?: Record<string, unknown>;
}

export interface SceneBeat {
  id: number;
  business_id?: string;
  scene_id: number;
  scene_business_id?: string | null;
  order_index: number;
  beat_type?: string | null;
  beat_summary?: string | null;
  characters_involved?: Record<string, unknown> | null;
  dialogue_excerpt?: string | null;
  camera_notes?: string | null;
  duration_seconds?: number | null;
  metadata?: Record<string, unknown> | null;
  created_at?: string;
  updated_at?: string;
}

export interface NormalizedShot {
  id: number;
  shot_number: string;
  shot_type?: string;
  camera_movement?: string;
  scene_beat_id?: number | null;
  character_ids?: number[] | null;
}

export interface StoryGenerationRequest {
  title: string;
  genre: string;
  theme?: string;
  target_audience?: string;
  duration_minutes?: number;
  character_ids: number[];
  setting_time?: string;
  setting_location?: string;
  world_building?: string;
  additional_requirements?: string;
  style_preferences?: string[];
  content_restrictions?: string[];
  tags?: string[];
  model?: string;
  temperature?: number;
}

export interface EpisodeGenerationRequest {
  story_id: number;
  episode_count: number;
  episode_duration?: number;
  focus_characters?: number[];
  plot_complexity: string;
  pacing: string;
  additional_requirements?: string;
  style_preferences?: string[];
  model?: string;
  temperature?: number;
}

export interface ScriptGenerationRequest {
  episode_id: number;
  format_type: string;
  language: string;
  dialogue_style: string;
  scene_detail_level: string;
  additional_requirements?: string;
  style_preferences?: string[];
  model?: string;
  temperature?: number;
}

// HTTP 请求工具函数
class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    // 从 localStorage 获取 token
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("auth_token");
    }
  }

  private isBusinessIdentifier(value: number | string): boolean {
    if (typeof value === "number") return false;
    const raw = String(value || "").trim();
    if (!raw) return false;
    const isDigitsOnly = /^\d+$/.test(raw);
    return !isDigitsOnly || raw.length >= 16;
  }

  private storyPath(storyIdOrBiz: number | string, suffix: string = ""): string {
    const base = this.isBusinessIdentifier(storyIdOrBiz)
      ? `/api/v1/stories/business/${storyIdOrBiz}`
      : `/api/v1/stories/${storyIdOrBiz}`;
    return `${base}${suffix}`;
  }

  private episodePath(episodeIdOrBiz: number | string, suffix: string = ""): string {
    const base = this.isBusinessIdentifier(episodeIdOrBiz)
      ? `/api/v1/episodes/business/${episodeIdOrBiz}`
      : `/api/v1/episodes/${episodeIdOrBiz}`;
    return `${base}${suffix}`;
  }

  private scriptPath(scriptIdOrBiz: number | string, suffix: string = ""): string {
    const base = this.isBusinessIdentifier(scriptIdOrBiz)
      ? `/api/v1/scripts/business/${scriptIdOrBiz}`
      : `/api/v1/scripts/${scriptIdOrBiz}`;
    return `${base}${suffix}`;
  }

  private virtualIPPath(ipIdOrBiz: number | string, suffix: string = ""): string {
    const base = this.isBusinessIdentifier(ipIdOrBiz)
      ? `/api/v1/virtual-ips/business/${ipIdOrBiz}`
      : `/api/v1/virtual-ips/${ipIdOrBiz}`;
    return `${base}${suffix}`;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retry: boolean = true,
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;

    // 每次请求前更新token
    this.updateToken();

    const normalizeHeaders = (
      headers?: HeadersInit,
    ): Record<string, string> => {
      if (!headers) return {};
      if (typeof Headers !== "undefined" && headers instanceof Headers) {
        return Object.fromEntries(headers.entries());
      }
      if (Array.isArray(headers)) {
        return Object.fromEntries(headers);
      }
      return { ...(headers as Record<string, string>) };
    };

    const isFormData =
      typeof FormData !== "undefined" && options.body instanceof FormData;
    const baseHeaders = isFormData ? {} : { "Content-Type": "application/json" };
    const mergedHeaders = {
      ...baseHeaders,
      ...normalizeHeaders(options.headers),
    };
    const sanitizedHeaders = Object.fromEntries(
      Object.entries(mergedHeaders).filter(
        ([, value]) => typeof value === "string" && value.length >= 0,
      ),
    ) as Record<string, string>;

    const config: RequestInit = {
      ...options,
      headers: sanitizedHeaders,
    };

    // 添加认证头
    if (this.token) {
      config.headers = {
        ...(config.headers as Record<string, string>),
        Authorization: `Bearer ${this.token}`,
      };
    }

    try {
      console.log(`Making request to ${url}`, {
        method: config.method,
        headers: config.headers,
      });
      const response = await fetch(url, config);

      // 处理401未授权错误
      if (response.status === 401 && retry) {
        console.log("Token expired or invalid, redirecting to login...");
        this.clearToken();
        if (
          typeof window !== "undefined" &&
          !window.location.pathname.includes("/login")
        ) {
          window.location.href = "/login";
        }
        return {
          success: false,
          error: "登录已过期，请重新登录",
        };
      }

      const data = await response.json();
      console.log(`Response from ${url}:`, response.status, data);

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            `HTTP error! status: ${response.status}`,
        );
      }

      // 如果后端返回的是标准格式 {success, data}，直接返回
      if (data.hasOwnProperty("success")) {
        return data;
      }

      // 否则封装为标准格式
      return {
        success: true,
        data: data,
      };
    } catch (error) {
      console.error("API request failed:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  // 设置认证 token
  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token);
    }
  }

  // 更新token（从localStorage重新读取）
  updateToken() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("auth_token");
    }
  }

  // 清除认证 token
  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
    }
  }

  // 用户认证相关 API
  async login(
    credentials: LoginRequest,
  ): Promise<ApiResponse<{ access_token: string; token_type: string }>> {
    // 使用URLSearchParams而不是FormData，因为后端期望application/x-www-form-urlencoded格式
    const formBody = new URLSearchParams();
    formBody.append("username", credentials.email); // 注意：后端使用username字段
    formBody.append("password", credentials.password);

    console.log("Login request:", credentials.email, credentials.password);

    const response = await this.request<{
      access_token: string;
      token_type: string;
    }>(
      "/api/v1/auth/login",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formBody.toString(),
      },
      false,
    ); // 登录请求不需要重试

    // 如果登录成功，保存token
    if (response.success && response.data) {
      this.setToken(response.data.access_token);
    }

    return response;
  }

  async register(userData: RegisterRequest): Promise<ApiResponse<User>> {
    return this.request("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  }

  async logout(): Promise<ApiResponse> {
    this.clearToken();
    return { success: true };
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request("/api/v1/auth/me");
  }

  // 用户管理相关 API (管理员权限)
  async getUsers(params?: {
    page?: number;
    size?: number;
    status_filter?: string;
    role_filter?: string;
    search?: string;
  }): Promise<ApiResponse<UserListResponse>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.append("page", params.page.toString());
    if (params?.size) searchParams.append("size", params.size.toString());
    if (params?.status_filter)
      searchParams.append("status_filter", params.status_filter);
    if (params?.role_filter)
      searchParams.append("role_filter", params.role_filter);
    if (params?.search) searchParams.append("search", params.search);

    const queryString = searchParams.toString();
    const endpoint = queryString
      ? `/api/v1/admin/users?${queryString}`
      : "/api/v1/admin/users";

    return this.request(endpoint);
  }

  async getUser(userId: number): Promise<ApiResponse<AdminUser>> {
    return this.request(`/api/v1/admin/users/${userId}`);
  }

  async approveUser(
    userId: number,
    data: UserApprovalRequest,
  ): Promise<ApiResponse<AdminUser>> {
    return this.request(`/api/v1/admin/users/${userId}/approval`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async updateUserRole(
    userId: number,
    data: {
      is_admin?: boolean;
      is_superuser?: boolean;
      role_change_reason?: string;
    },
  ): Promise<ApiResponse<AdminUser>> {
    const formData = new URLSearchParams();
    if (data.is_admin !== undefined)
      formData.append("is_admin", data.is_admin.toString());
    if (data.is_superuser !== undefined)
      formData.append("is_superuser", data.is_superuser.toString());
    if (data.role_change_reason)
      formData.append("reason", data.role_change_reason);

    return this.request(`/api/v1/admin/users/${userId}/role`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });
  }

  async suspendUser(
    userId: number,
    data: {
      duration_hours?: number;
      reason?: string;
    },
  ): Promise<ApiResponse<AdminUser>> {
    const searchParams = new URLSearchParams();
    if (data.duration_hours)
      searchParams.append("duration_hours", data.duration_hours.toString());
    if (data.reason) searchParams.append("reason", data.reason);

    const queryString = searchParams.toString();
    const endpoint = queryString
      ? `/api/v1/admin/users/${userId}/suspend?${queryString}`
      : `/api/v1/admin/users/${userId}/suspend`;

    return this.request(endpoint, {
      method: "PUT",
    });
  }

  async reactivateUser(userId: number): Promise<ApiResponse<AdminUser>> {
    return this.request(`/api/v1/admin/users/${userId}/reactivate`, {
      method: "PUT",
    });
  }

  async deleteUser(
    userId: number,
  ): Promise<ApiResponse<{ message: string; success: boolean }>> {
    return this.request(`/api/v1/admin/users/${userId}`, {
      method: "DELETE",
    });
  }

  async getUserStats(): Promise<ApiResponse<UserStatsResponse>> {
    return this.request("/api/v1/admin/stats");
  }

  async getUserAuditLogs(
    userId: number,
    params?: {
      page?: number;
      size?: number;
    },
  ): Promise<ApiResponse<UserAuditLog[]>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.append("page", params.page.toString());
    if (params?.size) searchParams.append("size", params.size.toString());

    const queryString = searchParams.toString();
    const endpoint = queryString
      ? `/api/v1/admin/users/${userId}/audit-logs?${queryString}`
      : `/api/v1/admin/users/${userId}/audit-logs`;

    return this.request(endpoint);
  }

  async resetUserLoginAttempts(
    userId: number,
  ): Promise<ApiResponse<AdminUser>> {
    return this.request(`/api/v1/admin/users/${userId}/reset-login-attempts`, {
      method: "POST",
    });
  }

  async generateUserActivationToken(
    userId: number,
  ): Promise<ApiResponse<{ activation_token: string; message: string }>> {
    return this.request(
      `/api/v1/admin/users/${userId}/generate-activation-token`,
      {
        method: "POST",
      },
    );
  }

  async updateUserAdmin(
    userId: number,
    data: {
      is_active?: boolean;
      is_admin?: boolean;
      is_approved?: boolean;
      email_verified?: boolean;
      failed_login_attempts?: number;
      account_locked_until?: string;
    },
  ): Promise<ApiResponse<AdminUser>> {
    return this.request(`/api/v1/admin/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  // 任务相关 API
  async getTasks(params?: {
    page?: number;
    size?: number;
    status_filter?: string;
    task_type?: string;
  }): Promise<
    ApiResponse<{ tasks: Task[]; total: number; page: number; size: number }>
  > {
    const searchParams = new URLSearchParams();
    const size = params?.size && params.size > 0 ? params.size : 20;
    const page = params?.page && params.page > 0 ? params.page : 1;
    searchParams.append("skip", String((page - 1) * size));
    searchParams.append("limit", String(size));
    if (params?.status_filter) {
      searchParams.append("status_filter", params.status_filter);
    }
    if (params?.task_type) {
      searchParams.append("task_type", params.task_type);
    }
    const qs = searchParams.toString();
    const endpoint = qs ? `/api/v1/tasks?${qs}` : "/api/v1/tasks";
    return this.request(endpoint);
  }

  async createTask(taskData: CreateTaskRequest): Promise<ApiResponse<Task>> {
    // 映射到后端 TaskCreate 结构
    const backendPayload = {
      title: taskData.title,
      description: `${taskData.platform} image generation task`,
      task_type: "image_generation",
      prompt: taskData.prompt,
      parameters: {
        platform: taskData.platform,
        model_id: taskData.model_id,
        model_name: taskData.model_name,
        count: taskData.count,
      },
    };
    return this.request("/api/v1/tasks", {
      method: "POST",
      body: JSON.stringify(backendPayload),
    });
  }

  async getTask(id: string): Promise<ApiResponse<Task>> {
    return this.request(`/api/v1/tasks/${id}`);
  }

  async deleteTask(id: string): Promise<ApiResponse> {
    return this.request(`/api/v1/tasks/${id}`, {
      method: "DELETE",
    });
  }

  async startTask(
    id: number,
  ): Promise<ApiResponse<{ message: string; task_id: number }>> {
    return this.request(`/api/v1/tasks/${id}/start`, {
      method: "POST",
    });
  }

  // 图片相关 API
  async getImages(params?: {
    search?: string;
    platform?: string;
    page?: number;
    limit?: number;
  }): Promise<ApiResponse<{ images: ImageItem[]; total: number }>> {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.append("search", params.search);
    if (params?.platform) searchParams.append("platform", params.platform);
    if (params?.page) searchParams.append("page", params.page.toString());
    if (params?.limit) searchParams.append("limit", params.limit.toString());

    const queryString = searchParams.toString();
    const endpoint = queryString ? `/images?${queryString}` : "/images";

    return this.request(endpoint);
  }

  async getImage(id: string): Promise<ApiResponse<ImageItem>> {
    return this.request(`/images/${id}`);
  }

  async deleteImage(id: string): Promise<ApiResponse> {
    return this.request(`/images/${id}`, {
      method: "DELETE",
    });
  }

  // 文件上传 API
  async uploadImage(file: File): Promise<ApiResponse<{ url: string }>> {
    const formData = new FormData();
    formData.append("file", file);

    return this.request("/upload/image", {
      method: "POST",
      headers: {
        // 不设置 Content-Type，让浏览器自动设置 multipart/form-data
      },
      body: formData,
    });
  }

  // 虚拟IP相关 API
  async getVirtualIPs(params?: {
    search?: string;
    tags?: string[];
    page?: number;
    limit?: number;
  }): Promise<ApiResponse<VirtualIP[]>> {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.append("search", params.search);
    if (params?.tags)
      params.tags.forEach((tag) => searchParams.append("tags", tag));
    if (params?.page) searchParams.append("page", params.page.toString());
    if (params?.limit) searchParams.append("limit", params.limit.toString());

    const queryString = searchParams.toString();
    const endpoint = queryString
      ? `/api/v1/virtual-ips/?${queryString}`
      : "/api/v1/virtual-ips/";

    return this.request(endpoint);
  }

  async getVirtualIP(id: number | string): Promise<ApiResponse<VirtualIP>> {
    return this.request(this.virtualIPPath(id));
  }

  async createVirtualIP(
    data: CreateVirtualIPRequest,
  ): Promise<ApiResponse<VirtualIP>> {
    return this.request("/api/v1/virtual-ips/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateVirtualIP(
    id: number | string,
    data: UpdateVirtualIPRequest,
  ): Promise<ApiResponse<VirtualIP>> {
    return this.request(this.virtualIPPath(id), {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteVirtualIP(id: number | string): Promise<ApiResponse> {
    return this.request(this.virtualIPPath(id), {
      method: "DELETE",
    });
  }

  // AI增强虚拟IP相关 API
  async generateAIContent(
    data: VirtualIPAIGenerationRequest,
  ): Promise<ApiResponse<VirtualIPAIGenerationResponse>> {
    return this.request("/api/v1/virtual-ips/generate-ai-content", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async generateAIContentDetailed(
    data: VirtualIPAIGenerationRequest,
  ): Promise<ApiResponse<VirtualIPAIGenerationDetailedResponse>> {
    return this.request("/api/v1/virtual-ips/generate-ai-content-detailed", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // 语音相关 API
  async getVoiceEnums(): Promise<ApiResponse<VoiceEnums>> {
    return this.request("/api/v1/voice/enums");
  }

  async getVoices(params?: {
    voice_type?: string;
    provider?: string;
    refresh?: boolean;
  }): Promise<ApiResponse<VoiceList>> {
    const searchParams = new URLSearchParams();
    if (params?.voice_type)
      searchParams.append("voice_type", params.voice_type);
    if (params?.provider) searchParams.append("provider", params.provider);
    if (params?.refresh) searchParams.append("refresh", "true");
    const query = searchParams.toString();
    const endpoint = query
      ? `/api/v1/voice/voices?${query}`
      : "/api/v1/voice/voices";
    return this.request(endpoint);
  }

  async previewVoice(payload: {
    text: string;
    model: string;
    voice_id?: string;
    provider?: string;
    output_format?: "url" | "hex";
  }): Promise<ApiResponse<VoicePreviewResponse>> {
    const body = {
      ...payload,
      output_format: payload.output_format || "url",
      stream: false,
    };
    return this.request("/api/v1/voice/tts", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  async createVirtualIPWithAI(
    data: VirtualIPAICreateRequest,
  ): Promise<ApiResponse<VirtualIP>> {
    return this.request("/api/v1/virtual-ips/create-with-ai", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // 虚拟IP图像相关 API
  async getVirtualIPImages(
    virtual_ip_id: number,
    params?: {
      category?: string;
      subcategory?: string;
    },
  ): Promise<ApiResponse<VirtualIPImage[]>> {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.append("category", params.category);
    if (params?.subcategory)
      searchParams.append("subcategory", params.subcategory);

    const queryString = searchParams.toString();
    const endpoint = queryString
      ? `/api/v1/virtual-ips/${virtual_ip_id}/images?${queryString}`
      : `/api/v1/virtual-ips/${virtual_ip_id}/images`;

    return this.request(endpoint);
  }

  async getVirtualIPImage(
    virtual_ip_id: number,
    image_id: number,
  ): Promise<ApiResponse<VirtualIPImage>> {
    return this.request(
      `/api/v1/virtual-ips/${virtual_ip_id}/images/${image_id}`,
    );
  }

  async uploadVirtualIPImage(
    virtual_ip_id: number,
    file: File,
    data: {
      category: string;
      subcategory?: string;
      tags?: string[] | string;
      prompt?: string;
      ai_model?: string;
      is_default?: boolean;
    },
  ): Promise<ApiResponse<VirtualIPImage>> {
    const formData = new FormData();
    formData.append("image", file);
    formData.append("category", data.category);
    if (data.subcategory) formData.append("subcategory", data.subcategory);
    if (data.tags !== undefined) {
      const tagValue = Array.isArray(data.tags)
        ? data.tags.join(",")
        : data.tags;
      if (tagValue) {
        formData.append("tags", tagValue);
      }
    }
    if (data.prompt) formData.append("prompt", data.prompt);
    if (data.ai_model) formData.append("ai_model", data.ai_model);
    if (data.is_default !== undefined)
      formData.append("is_default", data.is_default.toString());

    return this.request(`/api/v1/virtual-ips/${virtual_ip_id}/images`, {
      method: "POST",
      body: formData,
    });
  }

  async deleteVirtualIPImage(
    virtual_ip_id: number,
    image_id: number,
  ): Promise<ApiResponse> {
    return this.request(
      `/api/v1/virtual-ips/${virtual_ip_id}/images/${image_id}`,
      {
        method: "DELETE",
      },
    );
  }

  async setDefaultVirtualIPImage(
    virtual_ip_id: number,
    image_id: number,
  ): Promise<ApiResponse> {
    return this.request(
      `/api/v1/virtual-ips/${virtual_ip_id}/images/${image_id}/set-default`,
      {
        method: "POST",
      },
    );
  }

  // 剧本相关方法
  async getStories(params?: {
    skip?: number;
    limit?: number;
    genre?: string;
    status?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append("skip", params.skip.toString());
    if (params?.limit) searchParams.append("limit", params.limit.toString());
    if (params?.genre) searchParams.append("genre", params.genre);
    if (params?.status) searchParams.append("status", params.status);

    return this.request<Story[]>(`/api/v1/stories?${searchParams}`);
  }

  async getStory(idOrBusinessId: number | string) {
    return this.request<Story>(this.storyPath(idOrBusinessId));
  }

  async generateStory(data: StoryGenerationRequest) {
    return this.request<Story>("/api/v1/stories/generate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async generateStoryAsync(data: StoryGenerationRequest) {
    return this.request<{ task_id: number; status: string }>(
      "/api/v1/stories/generate-async",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    );
  }

  async previewStoryPrompt(data: StoryGenerationRequest) {
    return this.request<{ prompt: string }>("/api/v1/stories/prompt/preview", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateStory(idOrBusinessId: number | string, data: Partial<Story>) {
    return this.request<Story>(this.storyPath(idOrBusinessId), {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteStory(idOrBusinessId: number | string) {
    return this.request(this.storyPath(idOrBusinessId), {
      method: "DELETE",
    });
  }

  async getStoryCharacters(storyId: number | string) {
    return this.request<StoryCharacter[]>(
      this.storyPath(storyId, "/characters"),
    );
  }

  async getStoryGenres() {
    return this.request<Array<{ value: string; label: string }>>(
      "/api/v1/stories/genres",
    );
  }

  // 环境资产管理
  async listEnvironments(): Promise<ApiResponse<Environment[]>> {
    return this.request("/api/v1/story-structure/environments");
  }

  async getEnvironment(
    id: number,
  ): Promise<ApiResponse<Environment>> {
    return this.request(`/api/v1/story-structure/environments/${id}`);
  }

  async createEnvironment(
    payload: EnvironmentCreate,
  ): Promise<ApiResponse<Environment>> {
    return this.request("/api/v1/story-structure/environments", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async updateEnvironment(
    id: number,
    payload: Partial<EnvironmentCreate>,
  ): Promise<ApiResponse<Environment>> {
    return this.request(`/api/v1/story-structure/environments/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }

  async deleteEnvironment(id: number): Promise<ApiResponse> {
    return this.request(`/api/v1/story-structure/environments/${id}`, {
      method: "DELETE",
    });
  }

  async listEnvironmentImages(
    envId: number,
  ): Promise<ApiResponse<EnvironmentImagesResponse>> {
    return this.request(`/api/v1/story-structure/environments/${envId}/images`);
  }

  async uploadEnvironmentImage(
    envId: number,
    file: File,
  ): Promise<ApiResponse<{ url: string }>> {
    const formData = new FormData();
    formData.append("image", file);
    return this.request(
      `/api/v1/story-structure/environments/${envId}/images/upload`,
      {
        method: "POST",
        body: formData,
      },
    );
  }

  async generateEnvironmentImages(
    envId: number,
    payload: {
      prompt?: string;
      model?: string;
      count?: number;
      size?: string;
      style?: string;
      style_preset_id?: string;
      style_spec?: StyleSpec;
    },
  ): Promise<ApiResponse<{ images: string[]; count: number }>> {
    return this.request(
      `/api/v1/story-structure/environments/${envId}/images/generate`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  }

  async generateEnvironmentImageVariants(
    envId: number,
    payload: {
      base_image?: string;
      prompt?: string;
      model?: string;
      count?: number;
      size?: string;
      style?: string;
      style_preset_id?: string;
      style_spec?: StyleSpec;
    },
  ): Promise<ApiResponse<{ images: string[]; count: number }>> {
    return this.request(
      `/api/v1/story-structure/environments/${envId}/images/variants`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  }

  async generateEnvironmentImagesAsync(
    envId: number,
    payload: {
      prompt?: string;
      model?: string;
      count?: number;
      size?: string;
      style?: string;
      style_preset_id?: string;
      style_spec?: StyleSpec;
    },
  ): Promise<ApiResponse<{ task_id: number; status: string }>> {
    return this.request(
      `/api/v1/story-structure/environments/${envId}/images/generate-async`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  }

  async generateEnvironmentImageVariantsAsync(
    envId: number,
    payload: {
      base_image?: string;
      prompt?: string;
      model?: string;
      count?: number;
      size?: string;
      style?: string;
      style_preset_id?: string;
      style_spec?: StyleSpec;
      reference_images?: string[];
    },
  ): Promise<ApiResponse<{ task_id: number; status: string }>> {
    return this.request(
      `/api/v1/story-structure/environments/${envId}/images/variants-async`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  }

  async deleteEnvironmentImage(
    envId: number,
    imageUrl: string,
  ): Promise<ApiResponse> {
    const params = new URLSearchParams({ image_url: imageUrl });
    return this.request(
      `/api/v1/story-structure/environments/${envId}/images?${params.toString()}`,
      {
        method: "DELETE",
      },
    );
  }

  // 统一可用模型列表
  async getAvailableModels(params?: {
    type?: "text" | "image" | "video" | string;
  }) {
    const t = params?.type ?? "text";
    return this.request<AvailableModelsResponse>(
      `/api/v1/ai/models/available?model_type=${encodeURIComponent(t)}`,
    );
  }

  // 风格 schema / presets（后端为唯一真源）
  async getStyleSchema() {
    return this.request<StyleSchemaResponse>(`/api/v1/styles/schema`);
  }

  async listStylePresets() {
    return this.request<StylePreset[]>(`/api/v1/styles/presets`);
  }

  async getStylePreset(presetId: string) {
    return this.request<StylePreset>(`/api/v1/styles/presets/${presetId}`);
  }

  // 剧集相关方法
  async getEpisodes(params?: {
    story_id?: number;
    story_business_id?: string;
    skip?: number;
    limit?: number;
    status?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.story_id)
      searchParams.append("story_id", params.story_id.toString());
    if (params?.story_business_id)
      searchParams.append("story_business_id", params.story_business_id);
    if (params?.skip) searchParams.append("skip", params.skip.toString());
    if (params?.limit) searchParams.append("limit", params.limit.toString());
    if (params?.status) searchParams.append("status", params.status);

    return this.request<Episode[]>(`/api/v1/episodes?${searchParams}`);
  }

  async getEpisode(idOrBusinessId: number | string) {
    return this.request<Episode>(this.episodePath(idOrBusinessId));
  }

  async generateEpisodes(data: EpisodeGenerationRequest) {
    return this.request<Episode[]>("/api/v1/episodes/generate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async previewEpisodePrompt(data: EpisodeGenerationRequest) {
    return this.request<{ prompt: string }>(`/api/v1/episodes/prompt/preview`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async generateEpisodesAsync(data: EpisodeGenerationRequest) {
    return this.request<{ task_id: number; status: string }>(
      `/api/v1/episodes/generate-async`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    );
  }

  async updateEpisode(idOrBusinessId: number | string, data: Partial<Episode>) {
    return this.request<Episode>(this.episodePath(idOrBusinessId), {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteEpisode(idOrBusinessId: number | string) {
    return this.request(this.episodePath(idOrBusinessId), {
      method: "DELETE",
    });
  }

  async getStoryEpisodes(storyIdOrBusinessId: number | string) {
    const endpoint = this.isBusinessIdentifier(storyIdOrBusinessId)
      ? `/api/v1/episodes/story/business/${storyIdOrBusinessId}`
      : `/api/v1/episodes/story/${storyIdOrBusinessId}`;
    return this.request<Episode[]>(endpoint);
  }

  async regenerateEpisode(idOrBusinessId: number | string) {
    return this.request<Episode>(this.episodePath(idOrBusinessId, "/regenerate"), {
      method: "POST",
    });
  }

  // 剧本相关方法
  async getScripts(params?: {
    episode_id?: number;
    episode_business_id?: string;
    skip?: number;
    limit?: number;
    status?: string;
    format_type?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.episode_id)
      searchParams.append("episode_id", params.episode_id.toString());
    if (params?.episode_business_id)
      searchParams.append("episode_business_id", params.episode_business_id);
    if (params?.skip) searchParams.append("skip", params.skip.toString());
    if (params?.limit) searchParams.append("limit", params.limit.toString());
    if (params?.status) searchParams.append("status", params.status);
    if (params?.format_type)
      searchParams.append("format_type", params.format_type);

    return this.request<Script[]>(`/api/v1/scripts?${searchParams}`);
  }

  async getScript(idOrBusinessId: number | string) {
    return this.request<Script>(this.scriptPath(idOrBusinessId));
  }

  async generateScript(data: ScriptGenerationRequest) {
    return this.request<Script>("/api/v1/scripts/generate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async generateScriptAsync(data: ScriptGenerationRequest) {
    return this.request<{ task_id: number; status: string }>(
      `/api/v1/scripts/generate-async`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    );
  }

  async previewScriptPrompt(data: ScriptGenerationRequest) {
    return this.request<{ prompt: string }>(`/api/v1/scripts/prompt/preview`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateScript(idOrBusinessId: number | string, data: Partial<Script>) {
    return this.request<Script>(this.scriptPath(idOrBusinessId), {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteScript(idOrBusinessId: number | string) {
    return this.request(this.scriptPath(idOrBusinessId), {
      method: "DELETE",
    });
  }

  async getEpisodeScripts(episodeIdOrBusinessId: number | string) {
    const endpoint = this.isBusinessIdentifier(episodeIdOrBusinessId)
      ? `/api/v1/scripts/episode/business/${episodeIdOrBusinessId}`
      : `/api/v1/scripts/episode/${episodeIdOrBusinessId}`;
    return this.request<Script[]>(endpoint);
  }

  async regenerateScript(idOrBusinessId: number | string) {
    return this.request<Script>(this.scriptPath(idOrBusinessId, "/regenerate"), {
      method: "POST",
    });
  }

  async getScriptFormats() {
    return this.request<Array<{ value: string; label: string }>>(
      "/api/v1/scripts/formats",
    );
  }

  async getScriptLanguages() {
    return this.request<Array<{ value: string; label: string }>>(
      "/api/v1/scripts/languages",
    );
  }

  async exportScript(idOrBusinessId: number | string, format: string = "txt") {
    return this.request(this.scriptPath(idOrBusinessId, `/export?format=${format}`), {
      method: "POST",
    });
  }

  async generateSceneDialogueAudioAsync(
    scriptId: number | string,
    payload?: {
      tts_model?: string;
      scene_numbers?: number[];
      overwrite_audio?: boolean;
      overwrite_beats?: boolean;
    },
  ) {
    return this.request<{ task_id: number; status: string }>(
      this.scriptPath(scriptId, "/dialogue-audio/generate-async"),
      {
        method: "POST",
        body: JSON.stringify(payload || {}),
      },
    );
  }

  async generateAudioTimelineAsync(
    scriptId: number | string,
    payload?: {
      overwrite?: boolean;
    },
  ) {
    return this.request<{ task_id: number; status: string }>(
      this.scriptPath(scriptId, "/audio-timeline/generate-async"),
      {
        method: "POST",
        body: JSON.stringify(payload || {}),
      },
    );
  }

  async generateStoryboardFromAudioTimelineAsync(
    scriptId: number | string,
    payload?: {
      overwrite_existing?: boolean;
      min_pause_seconds?: number;
    },
  ) {
    return this.request<{ task_id: number; status: string }>(
      this.scriptPath(scriptId, "/storyboard/from-audio-timeline/generate-async"),
      {
        method: "POST",
        body: JSON.stringify(payload || {}),
      },
    );
  }

  // 分镜相关
  async getStoryboard(scriptId: number | string) {
    return this.request<StoryboardPayload>(
      this.scriptPath(scriptId, "/storyboard"),
    );
  }
  async previewStoryboardPrompt(scriptId: number | string) {
    return this.request<{ prompt: string }>(
      this.scriptPath(scriptId, "/storyboard/preview"),
      { method: "POST" },
    );
  }
  async generateStoryboard(
    scriptId: number | string,
    data?: {
      model?: string;
      temperature?: number;
      frames_per_scene?: number;
      max_frames?: number;
      scene_numbers?: number[];
      use_plan?: boolean;
    },
  ) {
    const params = new URLSearchParams();
    if (data?.model) params.append("model", data.model);
    if (typeof data?.temperature === "number")
      params.append("temperature", String(data.temperature));
    if (typeof data?.frames_per_scene === "number")
      params.append("frames_per_scene", String(data.frames_per_scene));
    if (typeof data?.max_frames === "number")
      params.append("max_frames", String(data.max_frames));
    if (data?.scene_numbers && data.scene_numbers.length > 0)
      params.append("scene_numbers", data.scene_numbers.join(","));
    if (data?.use_plan) params.append("use_plan", "true");
    const qs = params.toString();
    return this.request<StoryboardPayload>(
      `${this.scriptPath(scriptId, "/storyboard/generate")}${qs ? `?${qs}` : ""}`,
      { method: "POST" },
    );
  }
  async generateStoryboardAsync(
    scriptId: number | string,
    data?: {
      model?: string;
      temperature?: number;
      frames_per_scene?: number;
      max_frames?: number;
      scene_numbers?: number[];
      use_plan?: boolean;
    },
  ) {
    const params = new URLSearchParams();
    if (data?.model) params.append("model", data.model);
    if (typeof data?.temperature === "number")
      params.append("temperature", String(data.temperature));
    if (typeof data?.frames_per_scene === "number")
      params.append("frames_per_scene", String(data.frames_per_scene));
    if (typeof data?.max_frames === "number")
      params.append("max_frames", String(data.max_frames));
    if (data?.scene_numbers && data.scene_numbers.length > 0)
      params.append("scene_numbers", data.scene_numbers.join(","));
    if (data?.use_plan) params.append("use_plan", "true");
    const qs = params.toString();
    return this.request<{ task_id: number; status: string }>(
      `${this.scriptPath(scriptId, "/storyboard/generate-async")}${qs ? `?${qs}` : ""}`,
      { method: "POST" },
    );
  }
  async generateStoryboardVideo(
    scriptId: number | string,
    frames?: number[],
    selections?: Array<{
      frame_index: number;
      start_image_url?: string;
      end_image_url?: string;
    }>,
    options?: StoryboardVideoGenerationOptions,
  ) {
    return this.request(
      this.scriptPath(scriptId, "/storyboard/generate-video"),
      {
        method: "POST",
        body: JSON.stringify({
          frames: frames || [],
          selections: selections || [],
          ...(options || {}),
        }),
      },
    );
  }
  async generateStoryboardImages(
    scriptId: number | string,
    payload?: {
      prompt?: string;
      frames?: number[];
      model?: string;
      width?: number;
      height?: number;
      style?: string;
      style_preset_id?: string;
      style_spec?: StyleSpec;
      reference_images?: string[];
      count?: number;
      keyframe_mode?: "single" | "start_end";
      start_enabled?: boolean;
      end_enabled?: boolean;
    },
  ) {
    const isStartEnd = payload?.keyframe_mode === "start_end";
    const desiredCount = payload?.count ?? (isStartEnd ? 4 : 1);
    const normalizedCount = Math.max(1, Math.min(desiredCount, 4));
    return this.request(
      this.scriptPath(scriptId, "/storyboard/generate-images"),
      {
        method: "POST",
        body: JSON.stringify({
          frames: payload?.frames || [],
          prompt: payload?.prompt,
          model: payload?.model,
          width: payload?.width ?? 1024,
          height: payload?.height ?? 1024,
          style: payload?.style ?? "realistic",
          style_preset_id: payload?.style_preset_id,
          style_spec: payload?.style_spec,
          reference_images: payload?.reference_images,
          count: normalizedCount,
          keyframe_mode: payload?.keyframe_mode ?? "single",
          start_enabled: payload?.start_enabled,
          end_enabled: payload?.end_enabled,
        }),
      },
    );
  }
  async updateStoryboard(scriptId: number | string, frames: StoryboardFrame[]) {
    return this.request(this.scriptPath(scriptId, "/storyboard/update"), {
      method: "POST",
      body: JSON.stringify({ frames }),
    });
  }

  // 规范化叙事结构（实验性）
  async getNormalizedScenes(scriptId: number) {
    return this.request<Array<NormalizedScene>>(
      `/api/v1/story-structure/scripts/${scriptId}/scenes`,
    );
  }
  async createScene(
    scriptId: number,
    payload: {
      script_id: number;
      scene_number: string;
      slug_line: string;
      status?: string;
      environment_id?: number;
      environment_type?: string;
      location?: string;
      time_of_day?: string;
      summary?: string;
    },
  ) {
    return this.request(`/api/v1/story-structure/scripts/${scriptId}/scenes`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }
  async updateScene(
    sceneId: number,
    payload: Partial<{
      slug_line: string;
      scene_number: string;
      story_step_outline_id: number;
      environment_id?: number | null;
      environment_type: string;
      location: string;
      time_of_day: string;
      summary: string;
      page_length_eighths: number;
      primary_characters: Record<string, unknown>;
      conflict_notes: string;
      ai_prompt_snapshot: Record<string, unknown>;
      status: string;
      metadata: Record<string, unknown>;
    }>,
  ) {
    return this.request(`/api/v1/story-structure/scenes/${sceneId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }
  async deleteScene(sceneId: number) {
    return this.request(`/api/v1/story-structure/scenes/${sceneId}`, {
      method: "DELETE",
    });
  }

  async getNormalizedSceneBeats(sceneId: number) {
    return this.request<Array<SceneBeat>>(
      `/api/v1/story-structure/scenes/${sceneId}/beats`,
    );
  }
  async createSceneBeat(
    sceneId: number,
    payload: {
      scene_id: number;
      order_index: number;
      beat_type?: string;
      beat_summary?: string;
      characters_involved?: Record<string, unknown>;
      dialogue_excerpt?: string;
      camera_notes?: string;
      duration_seconds?: number;
      metadata?: Record<string, unknown>;
    },
  ) {
    return this.request(`/api/v1/story-structure/scenes/${sceneId}/beats`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }
  async updateSceneBeat(
    beatId: number,
    payload: Partial<{
      order_index: number;
      beat_type: string;
      beat_summary: string;
      characters_involved: Record<string, unknown>;
      dialogue_excerpt: string;
      camera_notes: string;
      duration_seconds: number;
      metadata: Record<string, unknown>;
    }>,
  ) {
    return this.request(`/api/v1/story-structure/scene-beats/${beatId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }
  async deleteSceneBeat(beatId: number) {
    return this.request(`/api/v1/story-structure/scene-beats/${beatId}`, {
      method: "DELETE",
    });
  }

  async getNormalizedSceneShots(sceneId: number) {
    return this.request<Array<NormalizedShot>>(
      `/api/v1/story-structure/scenes/${sceneId}/shots`,
    );
  }
  async createSceneShot(
    sceneId: number,
    payload: {
      scene_id: number;
      shot_number: string;
      scene_beat_id?: number;
      shot_type?: string;
      camera_setup?: string;
      camera_movement?: string;
      framing?: string;
      focus_subject?: string;
      character_ids?: number[];
      duration_seconds?: number;
      storyboard_frame_asset_id?: number;
      lighting_notes?: string;
      audio_notes?: string;
      status?: string;
      metadata?: Record<string, unknown>;
    },
  ) {
    return this.request(`/api/v1/story-structure/scenes/${sceneId}/shots`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }
  async updateSceneShot(
    shotId: number,
    payload: Partial<{
      shot_number: string;
      scene_beat_id?: number;
      shot_type?: string;
      camera_setup?: string;
      camera_movement?: string;
      framing?: string;
      focus_subject?: string;
      character_ids?: number[];
      duration_seconds?: number;
      storyboard_frame_asset_id?: number;
      lighting_notes?: string;
      audio_notes?: string;
      status?: string;
      metadata?: Record<string, unknown>;
    }>,
  ) {
    return this.request(`/api/v1/story-structure/shots/${shotId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }
  async deleteSceneShot(shotId: number) {
    return this.request(`/api/v1/story-structure/shots/${shotId}`, {
      method: "DELETE",
    });
  }

  async getStoryTreatments(storyId: number, opts?: { latestOnly?: boolean }) {
    const latest = opts?.latestOnly ? "?latest_only=true" : "";
    return this.request<
      Array<{
        id: number;
        revision_number: number;
        title: string;
        status: string;
      }>
    >(`/api/v1/story-structure/stories/${storyId}/treatments${latest}`);
  }

  async createStoryTreatment(
    storyId: number,
    payload: {
      revision_number?: number;
      title: string;
      status?: string;
      logline?: string;
    },
  ) {
    const body = {
      story_id: storyId,
      revision_number: payload.revision_number ?? 1,
      title: payload.title,
      status: payload.status ?? "draft",
      logline: payload.logline,
    };
    return this.request(
      `/api/v1/story-structure/stories/${storyId}/treatments`,
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
  }

  // 公开request方法供其他API使用
  async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, options);
  }
}

// 创建全局 API 客户端实例（同时导出默认与具名，便于测试/覆写）
export const apiClient = new ApiClient(API_BASE_URL);

// 导出便捷方法
export const authAPI = {
  login: apiClient.login.bind(apiClient),
  register: apiClient.register.bind(apiClient),
  logout: apiClient.logout.bind(apiClient),
  getCurrentUser: apiClient.getCurrentUser.bind(apiClient),
};

export const adminAPI = {
  getUsers: apiClient.getUsers.bind(apiClient),
  getUser: apiClient.getUser.bind(apiClient),
  approveUser: apiClient.approveUser.bind(apiClient),
  updateUserRole: apiClient.updateUserRole.bind(apiClient),
  suspendUser: apiClient.suspendUser.bind(apiClient),
  reactivateUser: apiClient.reactivateUser.bind(apiClient),
  deleteUser: apiClient.deleteUser.bind(apiClient),
  getUserStats: apiClient.getUserStats.bind(apiClient),
  getUserAuditLogs: apiClient.getUserAuditLogs.bind(apiClient),
  resetUserLoginAttempts: apiClient.resetUserLoginAttempts.bind(apiClient),
  generateUserActivationToken:
    apiClient.generateUserActivationToken.bind(apiClient),
  updateUserAdmin: apiClient.updateUserAdmin.bind(apiClient),
};

export const taskAPI = {
  getTasks: apiClient.getTasks.bind(apiClient),
  createTask: apiClient.createTask.bind(apiClient),
  getTask: apiClient.getTask.bind(apiClient),
  deleteTask: apiClient.deleteTask.bind(apiClient),
  startTask: apiClient.startTask.bind(apiClient),
};

export const imageAPI = {
  getImages: apiClient.getImages.bind(apiClient),
  getImage: apiClient.getImage.bind(apiClient),
  deleteImage: apiClient.deleteImage.bind(apiClient),
  uploadImage: apiClient.uploadImage.bind(apiClient),
};

export const virtualIPAPI = {
  getVirtualIPs: apiClient.getVirtualIPs.bind(apiClient),
  getVirtualIP: apiClient.getVirtualIP.bind(apiClient),
  createVirtualIP: apiClient.createVirtualIP.bind(apiClient),
  updateVirtualIP: apiClient.updateVirtualIP.bind(apiClient),
  deleteVirtualIP: apiClient.deleteVirtualIP.bind(apiClient),
  generateAIContent: apiClient.generateAIContent.bind(apiClient),
  generateAIContentDetailed:
    apiClient.generateAIContentDetailed.bind(apiClient),
  createVirtualIPWithAI: apiClient.createVirtualIPWithAI.bind(apiClient),
  getVirtualIPImages: apiClient.getVirtualIPImages.bind(apiClient),
  uploadVirtualIPImage: apiClient.uploadVirtualIPImage.bind(apiClient),
  deleteVirtualIPImage: apiClient.deleteVirtualIPImage.bind(apiClient),
  setDefaultVirtualIPImage: apiClient.setDefaultVirtualIPImage.bind(apiClient),
};

export const voiceAPI = {
  getEnums: apiClient.getVoiceEnums.bind(apiClient),
  getVoices: apiClient.getVoices.bind(apiClient),
  preview: apiClient.previewVoice.bind(apiClient),
};

export const storyAPI = {
  getStories: apiClient.getStories.bind(apiClient),
  getStory: apiClient.getStory.bind(apiClient),
  generateStory: apiClient.generateStory.bind(apiClient),
  generateStoryAsync: apiClient.generateStoryAsync.bind(apiClient),
  previewStoryPrompt: apiClient.previewStoryPrompt.bind(apiClient),
  updateStory: apiClient.updateStory.bind(apiClient),
  deleteStory: apiClient.deleteStory.bind(apiClient),
  getStoryCharacters: apiClient.getStoryCharacters.bind(apiClient),
  getStoryGenres: apiClient.getStoryGenres.bind(apiClient),
};

export const episodeAPI = {
  getEpisodes: apiClient.getEpisodes.bind(apiClient),
  getEpisode: apiClient.getEpisode.bind(apiClient),
  generateEpisodes: apiClient.generateEpisodes.bind(apiClient),
  generateEpisodesAsync: apiClient.generateEpisodesAsync.bind(apiClient),
  previewEpisodePrompt: apiClient.previewEpisodePrompt.bind(apiClient),
  updateEpisode: apiClient.updateEpisode.bind(apiClient),
  deleteEpisode: apiClient.deleteEpisode.bind(apiClient),
  getStoryEpisodes: apiClient.getStoryEpisodes.bind(apiClient),
  regenerateEpisode: apiClient.regenerateEpisode.bind(apiClient),
};

export const scriptAPI = {
  getScripts: apiClient.getScripts.bind(apiClient),
  getScript: apiClient.getScript.bind(apiClient),
  generateScript: apiClient.generateScript.bind(apiClient),
  generateScriptAsync: apiClient.generateScriptAsync.bind(apiClient),
  updateScript: apiClient.updateScript.bind(apiClient),
  deleteScript: apiClient.deleteScript.bind(apiClient),
  getEpisodeScripts: apiClient.getEpisodeScripts.bind(apiClient),
  regenerateScript: apiClient.regenerateScript.bind(apiClient),
  getScriptFormats: apiClient.getScriptFormats.bind(apiClient),
  getScriptLanguages: apiClient.getScriptLanguages.bind(apiClient),
  exportScript: apiClient.exportScript.bind(apiClient),
  previewScriptPrompt: apiClient.previewScriptPrompt.bind(apiClient),
  generateSceneDialogueAudioAsync:
    apiClient.generateSceneDialogueAudioAsync.bind(apiClient),
  generateAudioTimelineAsync:
    apiClient.generateAudioTimelineAsync.bind(apiClient),
  generateStoryboardFromAudioTimelineAsync:
    apiClient.generateStoryboardFromAudioTimelineAsync.bind(apiClient),
  // Storyboard
  getStoryboard: apiClient.getStoryboard.bind(apiClient),
  previewStoryboardPrompt: apiClient.previewStoryboardPrompt.bind(apiClient),
  generateStoryboard: apiClient.generateStoryboard.bind(apiClient),
  generateStoryboardAsync: apiClient.generateStoryboardAsync.bind(apiClient),
  generateStoryboardVideo: apiClient.generateStoryboardVideo.bind(apiClient),
  generateStoryboardImages: apiClient.generateStoryboardImages.bind(apiClient),
  updateStoryboard: apiClient.updateStoryboard.bind(apiClient),
};

export const storyStructureAPI = {
  getNormalizedScenes: apiClient.getNormalizedScenes.bind(apiClient),
  getNormalizedSceneBeats: apiClient.getNormalizedSceneBeats.bind(apiClient),
  getNormalizedSceneShots: apiClient.getNormalizedSceneShots.bind(apiClient),
  getStoryTreatments: apiClient.getStoryTreatments.bind(apiClient),
  createStoryTreatment: apiClient.createStoryTreatment.bind(apiClient),
  listEnvironments: apiClient.listEnvironments.bind(apiClient),
  getEnvironment: apiClient.getEnvironment.bind(apiClient),
  createEnvironment: apiClient.createEnvironment.bind(apiClient),
  updateEnvironment: apiClient.updateEnvironment.bind(apiClient),
  deleteEnvironment: apiClient.deleteEnvironment.bind(apiClient),
  listEnvironmentImages: apiClient.listEnvironmentImages.bind(apiClient),
  uploadEnvironmentImage: apiClient.uploadEnvironmentImage.bind(apiClient),
  generateEnvironmentImages:
    apiClient.generateEnvironmentImages.bind(apiClient),
  generateEnvironmentImageVariants:
    apiClient.generateEnvironmentImageVariants.bind(apiClient),
  generateEnvironmentImagesAsync:
    apiClient.generateEnvironmentImagesAsync.bind(apiClient),
  generateEnvironmentImageVariantsAsync:
    apiClient.generateEnvironmentImageVariantsAsync.bind(apiClient),
  deleteEnvironmentImage: apiClient.deleteEnvironmentImage.bind(apiClient),
  updateScene: apiClient.updateScene.bind(apiClient),
  updateSceneShot: apiClient.updateSceneShot.bind(apiClient),
};

export const aiAPI = {
  getAvailableModels: apiClient.getAvailableModels.bind(apiClient),
};

export const styleAPI = {
  getSchema: apiClient.getStyleSchema.bind(apiClient),
  listPresets: apiClient.listStylePresets.bind(apiClient),
  getPreset: apiClient.getStylePreset.bind(apiClient),
};

// 虚拟IP图像管理API（使用统一的API客户端）
export const virtualIPImageAPI = {
  // 获取虚拟IP图像列表
  getImages: (virtualIPId: number, category?: string) =>
    apiClient.getVirtualIPImages(virtualIPId, { category }),

  // 获取单张虚拟IP图像
  getImage: (virtualIPId: number, imageId: number) =>
    apiClient.getVirtualIPImage(virtualIPId, imageId),

  // 上传图像
  uploadImage: (
    virtualIPId: number,
    file: File,
    category: string = "portrait",
    tags: string = "",
    isDefault: boolean = false,
  ) => {
    const normalizedTags = tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean)
      .join(",");

    return apiClient.uploadVirtualIPImage(virtualIPId, file, {
      category,
      tags: normalizedTags,
      is_default: isDefault,
    });
  },

  // AI生成图像（统一JSON）
  generateImage: async (
    virtualIPId: number,
    request: AIImageGenerationRequest,
  ): Promise<ApiResponse<VirtualIPImage>> => {
    return apiClient.makeRequest(
      `/api/v1/virtual-ips/${virtualIPId}/images/generate`,
      {
        method: "POST",
        body: JSON.stringify({
          style: request.style,
          style_preset_id: request.style_preset_id,
          style_spec: request.style_spec,
          category: request.category,
          model: request.model,
          additional_prompts: request.additional_prompts,
          is_default: request.is_default,
          count: request.count ?? 1,
          size: request.size,
        }),
      },
    );
  },

  // 文生图（异步：通过 Task 执行）
  generateImageAsync: async (
    virtualIPId: number,
    request: AIImageGenerationRequest,
  ): Promise<ApiResponse<{ task_id: number; status: string }>> => {
    return apiClient.makeRequest(
      `/api/v1/virtual-ips/${virtualIPId}/images/generate-async`,
      {
        method: "POST",
        body: JSON.stringify({
          style: request.style,
          style_preset_id: request.style_preset_id,
          style_spec: request.style_spec,
          category: request.category,
          model: request.model,
          additional_prompts: request.additional_prompts,
          is_default: request.is_default,
          count: request.count ?? 1,
          size: request.size,
        }),
      },
    );
  },

  // 图生图（通用接口：仅返回 URL，不入库）
  generateVariantFromImage: async (
    imageUrl: string,
    payload: ImageToImageRequestPayload,
  ): Promise<ApiResponse<{ images: string[] }>> => {
    return apiClient.makeRequest("/api/v1/ai/generate/image-to-image", {
      method: "POST",
      body: JSON.stringify({
        image_url: imageUrl,
        prompt: payload.prompt,
        model: payload.model,
        prefer_provider: payload.prefer_provider,
        style: payload.style,
        style_preset_id: payload.style_preset_id,
        style_spec: payload.style_spec,
        count: payload.count ?? 1,
      }),
    });
  },

  // 图生图（基于虚拟 IP 资产并保存变体记录）
  generateVariantAndSave: async (
    virtualIPId: number,
    imageId: number,
    payload: Pick<
      ImageToImageRequestPayload,
      | "prompt"
      | "model"
      | "count"
      | "size"
      | "style"
      | "style_preset_id"
      | "style_spec"
    >,
  ): Promise<ApiResponse<VirtualIPImage | VirtualIPImage[]>> => {
    return apiClient.makeRequest(
      `/api/v1/virtual-ips/${virtualIPId}/images/${imageId}/variants`,
      {
        method: "POST",
        body: JSON.stringify({
          prompt: payload.prompt,
          model: payload.model,
          count: payload.count ?? 1,
          size: payload.size,
          style: payload.style,
          style_preset_id: payload.style_preset_id,
          style_spec: payload.style_spec,
        }),
      },
    );
  },

  // 图生图（异步：通过 Task 执行）
  generateVariantAndSaveAsync: async (
    virtualIPId: number,
    imageId: number,
    payload: Pick<
      ImageToImageRequestPayload,
      | "prompt"
      | "model"
      | "count"
      | "size"
      | "reference_images"
      | "style"
      | "style_preset_id"
      | "style_spec"
    >,
  ): Promise<ApiResponse<{ task_id: number; status: string }>> => {
    return apiClient.makeRequest(
      `/api/v1/virtual-ips/${virtualIPId}/images/${imageId}/variants-async`,
      {
        method: "POST",
        body: JSON.stringify({
          prompt: payload.prompt,
          model: payload.model,
          count: payload.count ?? 1,
          size: payload.size,
          reference_images: payload.reference_images,
          style: payload.style,
          style_preset_id: payload.style_preset_id,
          style_spec: payload.style_spec,
        }),
      },
    );
  },

  // 更新图像信息
  updateImage: async (
    virtualIPId: number,
    imageId: number,
    update: VirtualIPImageUpdate,
  ): Promise<ApiResponse<VirtualIPImage>> => {
    return apiClient.makeRequest(
      `/api/v1/virtual-ips/${virtualIPId}/images/${imageId}`,
      {
        method: "PUT",
        body: JSON.stringify(update),
      },
    );
  },

  // 删除图像
  deleteImage: (virtualIPId: number, imageId: number) =>
    apiClient.deleteVirtualIPImage(virtualIPId, imageId),

  // 设置默认图像
  setDefaultImage: (virtualIPId: number, imageId: number) =>
    apiClient.setDefaultVirtualIPImage(virtualIPId, imageId),

  // 获取图像分类
  getCategories: async (
    virtualIPId: number,
  ): Promise<ApiResponse<string[]>> => {
    return apiClient.makeRequest(
      `/api/v1/virtual-ips/${virtualIPId}/images/categories`,
    );
  },
};

export default apiClient;
