// API 基础配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 通用响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// 用户相关类型
export interface User {
  id: string
  username: string
  email: string
  createdAt: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

// 任务相关类型
export interface Task {
  id: string
  title: string
  prompt: string
  platform: 'gpt' | 'keling' | 'jimeng'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  createdAt: string
  completedAt?: string
  imageUrl?: string
  userId: string
}

export interface CreateTaskRequest {
  title: string
  prompt: string
  platform: 'gpt' | 'keling' | 'jimeng'
}

// 图片相关类型
export interface ImageItem {
  id: string
  title: string
  prompt: string
  platform: 'gpt' | 'keling' | 'jimeng'
  imageUrl: string
  createdAt: string
  tags: string[]
  userId: string
}

// 虚拟IP图像相关类型
export interface VirtualIPImage {
  id: number;
  virtual_ip_id: number;
  file_path: string;
  category: string;
  tags: string[];
  is_default: boolean;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface VirtualIPImageCreate {
  virtual_ip_id: number;
  file_path: string;
  category: string;
  tags: string[];
  is_default: boolean;
  metadata?: Record<string, any>;
}

export interface VirtualIPImageUpdate {
  category?: string;
  tags?: string[];
  is_default?: boolean;
  metadata?: Record<string, any>;
}

export interface AIImageGenerationRequest {
  style: string;
  category: string;
  additional_prompts: string;
  is_default: boolean;
}

// 虚拟IP相关类型
export interface VirtualIP {
  id: number
  name: string
  default_avatar_url?: string
  description?: string
  tags: string[]
  background_story?: string
  style_prompt?: string
  style_reference_images?: string[]
  is_active: boolean
  is_public: boolean
  created_at: string
  updated_at?: string
  images?: VirtualIPImage[]
}

export interface CreateVirtualIPRequest {
  name: string
  description?: string
  tags?: string[]
  background_story?: string
  style_prompt?: string
  style_reference_images?: string[]
  is_active?: boolean
  is_public?: boolean
}

export interface UpdateVirtualIPRequest {
  name?: string
  description?: string
  tags?: string[]
  background_story?: string
  style_prompt?: string
  style_reference_images?: string[]
  is_active?: boolean
  is_public?: boolean
}

// 剧本相关类型
export interface StoryCharacter {
  id: number;
  story_id: number;
  virtual_ip_id: number;
  character_name?: string;
  role_type?: string;
  importance: number;
  personality?: string;
  background?: string;
  motivation?: string;
  character_arc?: string;
  relationships?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Story {
  id: number;
  title: string;
  genre: string;
  theme?: string;
  target_audience?: string;
  duration_minutes?: number;
  premise?: string;
  synopsis?: string;
  main_conflict?: string;
  resolution?: string;
  main_characters?: any[];
  character_relationships?: Record<string, any>;
  setting_time?: string;
  setting_location?: string;
  world_building?: string;
  status: string;
  is_public: boolean;
  tags?: string[];
  metadata?: Record<string, any>;
  generation_prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, any>;
  created_at: string;
  updated_at: string;
  story_characters?: StoryCharacter[];
}

export interface Episode {
  id: number;
  story_id: number;
  episode_number: number;
  title: string;
  summary?: string;
  plot_points?: any[];
  character_arcs?: Record<string, any>;
  conflicts?: any[];
  duration_minutes?: number;
  scene_count?: number;
  status: string;
  tags?: string[];
  metadata?: Record<string, any>;
  generation_prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Script {
  id: number;
  episode_id: number;
  title: string;
  content?: string;
  scenes?: any[];
  dialogues?: any[];
  stage_directions?: any[];
  format_type: string;
  language: string;
  page_count?: number;
  word_count?: number;
  character_count?: number;
  status: string;
  version: string;
  tags?: string[];
  metadata?: Record<string, any>;
  generation_prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, any>;
  created_at: string;
  updated_at: string;
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
}

export interface ScriptGenerationRequest {
  episode_id: number;
  format_type: string;
  language: string;
  dialogue_style: string;
  scene_detail_level: string;
  additional_requirements?: string;
  style_preferences?: string[];
}

// HTTP 请求工具函数
class ApiClient {
  private baseURL: string
  private token: string | null = null

  constructor(baseURL: string) {
    this.baseURL = baseURL
    // 从 localStorage 获取 token
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token')
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    // 添加认证头
    if (this.token) {
      config.headers = {
        ...config.headers,
        'Authorization': `Bearer ${this.token}`,
      }
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`)
      }

      return data
    } catch (error) {
      console.error('API request failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  }

  // 设置认证 token
  setToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token)
    }
  }

  // 清除认证 token
  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
    }
  }

  // 用户认证相关 API
  async login(credentials: LoginRequest): Promise<ApiResponse<{ user: User; token: string }>> {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
  }

  async register(userData: RegisterRequest): Promise<ApiResponse<{ user: User; token: string }>> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  }

  async logout(): Promise<ApiResponse> {
    const response = await this.request('/auth/logout', {
      method: 'POST',
    })
    this.clearToken()
    return response
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request('/auth/me')
  }

  // 任务相关 API
  async getTasks(): Promise<ApiResponse<Task[]>> {
    return this.request('/tasks')
  }

  async createTask(taskData: CreateTaskRequest): Promise<ApiResponse<Task>> {
    return this.request('/tasks', {
      method: 'POST',
      body: JSON.stringify(taskData),
    })
  }

  async getTask(id: string): Promise<ApiResponse<Task>> {
    return this.request(`/tasks/${id}`)
  }

  async deleteTask(id: string): Promise<ApiResponse> {
    return this.request(`/tasks/${id}`, {
      method: 'DELETE',
    })
  }

  // 图片相关 API
  async getImages(params?: {
    search?: string
    platform?: string
    page?: number
    limit?: number
  }): Promise<ApiResponse<{ images: ImageItem[]; total: number }>> {
    const searchParams = new URLSearchParams()
    if (params?.search) searchParams.append('search', params.search)
    if (params?.platform) searchParams.append('platform', params.platform)
    if (params?.page) searchParams.append('page', params.page.toString())
    if (params?.limit) searchParams.append('limit', params.limit.toString())

    const queryString = searchParams.toString()
    const endpoint = queryString ? `/images?${queryString}` : '/images'
    
    return this.request(endpoint)
  }

  async getImage(id: string): Promise<ApiResponse<ImageItem>> {
    return this.request(`/images/${id}`)
  }

  async deleteImage(id: string): Promise<ApiResponse> {
    return this.request(`/images/${id}`, {
      method: 'DELETE',
    })
  }

  // 文件上传 API
  async uploadImage(file: File): Promise<ApiResponse<{ url: string }>> {
    const formData = new FormData()
    formData.append('file', file)

    return this.request('/upload/image', {
      method: 'POST',
      headers: {
        // 不设置 Content-Type，让浏览器自动设置 multipart/form-data
      },
      body: formData,
    })
  }

  // 虚拟IP相关 API
  async getVirtualIPs(params?: {
    search?: string
    tags?: string[]
    page?: number
    limit?: number
  }): Promise<ApiResponse<VirtualIP[]>> {
    const searchParams = new URLSearchParams()
    if (params?.search) searchParams.append('search', params.search)
    if (params?.tags) params.tags.forEach(tag => searchParams.append('tags', tag))
    if (params?.page) searchParams.append('page', params.page.toString())
    if (params?.limit) searchParams.append('limit', params.limit.toString())

    const queryString = searchParams.toString()
    const endpoint = queryString ? `/ips?${queryString}` : '/ips'
    
    return this.request(endpoint)
  }

  async getVirtualIP(id: number): Promise<ApiResponse<VirtualIP>> {
    return this.request(`/ips/${id}`)
  }

  async createVirtualIP(data: CreateVirtualIPRequest): Promise<ApiResponse<VirtualIP>> {
    return this.request('/ips', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateVirtualIP(id: number, data: UpdateVirtualIPRequest): Promise<ApiResponse<VirtualIP>> {
    return this.request(`/ips/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteVirtualIP(id: number): Promise<ApiResponse> {
    return this.request(`/ips/${id}`, {
      method: 'DELETE',
    })
  }

  // 虚拟IP图像相关 API
  async getVirtualIPImages(virtual_ip_id: number, params?: {
    category?: string
    subcategory?: string
  }): Promise<ApiResponse<VirtualIPImage[]>> {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.append('category', params.category)
    if (params?.subcategory) searchParams.append('subcategory', params.subcategory)

    const queryString = searchParams.toString()
    const endpoint = queryString ? `/ips/${virtual_ip_id}/images?${queryString}` : `/ips/${virtual_ip_id}/images`
    
    return this.request(endpoint)
  }

  async uploadVirtualIPImage(
    virtual_ip_id: number,
    file: File,
    data: {
      category: string
      subcategory?: string
      tags?: string[]
      prompt?: string
      ai_model?: string
      is_default?: boolean
    }
  ): Promise<ApiResponse<VirtualIPImage>> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', data.category)
    if (data.subcategory) formData.append('subcategory', data.subcategory)
    if (data.tags) formData.append('tags', JSON.stringify(data.tags))
    if (data.prompt) formData.append('prompt', data.prompt)
    if (data.ai_model) formData.append('ai_model', data.ai_model)
    if (data.is_default !== undefined) formData.append('is_default', data.is_default.toString())

    return this.request(`/ips/${virtual_ip_id}/images`, {
      method: 'POST',
      headers: {
        // 不设置 Content-Type，让浏览器自动设置 multipart/form-data
      },
      body: formData,
    })
  }

  async deleteVirtualIPImage(virtual_ip_id: number, image_id: number): Promise<ApiResponse> {
    return this.request(`/ips/${virtual_ip_id}/images/${image_id}`, {
      method: 'DELETE',
    })
  }

  async setDefaultVirtualIPImage(virtual_ip_id: number, image_id: number): Promise<ApiResponse> {
    return this.request(`/ips/${virtual_ip_id}/images/${image_id}/set-default`, {
      method: 'POST',
    })
  }

  // 剧本相关方法
  async getStories(params?: { skip?: number; limit?: number; genre?: string; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.genre) searchParams.append('genre', params.genre);
    if (params?.status) searchParams.append('status', params.status);
    
    return this.request<Story[]>(`/api/v1/stories?${searchParams}`);
  }

  async getStory(id: number) {
    return this.request<Story>(`/api/v1/stories/${id}`);
  }

  async generateStory(data: StoryGenerationRequest) {
    return this.request<Story>('/api/v1/stories/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateStory(id: number, data: Partial<Story>) {
    return this.request<Story>(`/api/v1/stories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteStory(id: number) {
    return this.request(`/api/v1/stories/${id}`, {
      method: 'DELETE',
    });
  }

  async getStoryCharacters(storyId: number) {
    return this.request<StoryCharacter[]>(`/api/v1/stories/${storyId}/characters`);
  }

  async getStoryGenres() {
    return this.request<Array<{ value: string; label: string }>>('/api/v1/stories/genres');
  }

  // 剧集相关方法
  async getEpisodes(params?: { story_id?: number; skip?: number; limit?: number; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.story_id) searchParams.append('story_id', params.story_id.toString());
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.status) searchParams.append('status', params.status);
    
    return this.request<Episode[]>(`/api/v1/episodes?${searchParams}`);
  }

  async getEpisode(id: number) {
    return this.request<Episode>(`/api/v1/episodes/${id}`);
  }

  async generateEpisodes(data: EpisodeGenerationRequest) {
    return this.request<Episode[]>('/api/v1/episodes/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateEpisode(id: number, data: Partial<Episode>) {
    return this.request<Episode>(`/api/v1/episodes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteEpisode(id: number) {
    return this.request(`/api/v1/episodes/${id}`, {
      method: 'DELETE',
    });
  }

  async getStoryEpisodes(storyId: number) {
    return this.request<Episode[]>(`/api/v1/episodes/story/${storyId}`);
  }

  async regenerateEpisode(id: number) {
    return this.request<Episode>(`/api/v1/episodes/${id}/regenerate`, {
      method: 'POST',
    });
  }

  // 剧本相关方法
  async getScripts(params?: { episode_id?: number; skip?: number; limit?: number; status?: string; format_type?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.episode_id) searchParams.append('episode_id', params.episode_id.toString());
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.status) searchParams.append('status', params.status);
    if (params?.format_type) searchParams.append('format_type', params.format_type);
    
    return this.request<Script[]>(`/api/v1/scripts?${searchParams}`);
  }

  async getScript(id: number) {
    return this.request<Script>(`/api/v1/scripts/${id}`);
  }

  async generateScript(data: ScriptGenerationRequest) {
    return this.request<Script>('/api/v1/scripts/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateScript(id: number, data: Partial<Script>) {
    return this.request<Script>(`/api/v1/scripts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteScript(id: number) {
    return this.request(`/api/v1/scripts/${id}`, {
      method: 'DELETE',
    });
  }

  async getEpisodeScripts(episodeId: number) {
    return this.request<Script[]>(`/api/v1/scripts/episode/${episodeId}`);
  }

  async regenerateScript(id: number) {
    return this.request<Script>(`/api/v1/scripts/${id}/regenerate`, {
      method: 'POST',
    });
  }

  async getScriptFormats() {
    return this.request<Array<{ value: string; label: string }>>('/api/v1/scripts/formats');
  }

  async getScriptLanguages() {
    return this.request<Array<{ value: string; label: string }>>('/api/v1/scripts/languages');
  }

  async exportScript(id: number, format: string = 'txt') {
    return this.request(`/api/v1/scripts/${id}/export?format=${format}`, {
      method: 'POST',
    });
  }
}

// 创建全局 API 客户端实例
const apiClient = new ApiClient(API_BASE_URL)

// 导出便捷方法
export const authAPI = {
  login: apiClient.login.bind(apiClient),
  register: apiClient.register.bind(apiClient),
  logout: apiClient.logout.bind(apiClient),
  getCurrentUser: apiClient.getCurrentUser.bind(apiClient),
}

export const taskAPI = {
  getTasks: apiClient.getTasks.bind(apiClient),
  createTask: apiClient.createTask.bind(apiClient),
  getTask: apiClient.getTask.bind(apiClient),
  deleteTask: apiClient.deleteTask.bind(apiClient),
}

export const imageAPI = {
  getImages: apiClient.getImages.bind(apiClient),
  getImage: apiClient.getImage.bind(apiClient),
  deleteImage: apiClient.deleteImage.bind(apiClient),
  uploadImage: apiClient.uploadImage.bind(apiClient),
}

export const virtualIPAPI = {
  getVirtualIPs: apiClient.getVirtualIPs.bind(apiClient),
  getVirtualIP: apiClient.getVirtualIP.bind(apiClient),
  createVirtualIP: apiClient.createVirtualIP.bind(apiClient),
  updateVirtualIP: apiClient.updateVirtualIP.bind(apiClient),
  deleteVirtualIP: apiClient.deleteVirtualIP.bind(apiClient),
  getVirtualIPImages: apiClient.getVirtualIPImages.bind(apiClient),
  uploadVirtualIPImage: apiClient.uploadVirtualIPImage.bind(apiClient),
  deleteVirtualIPImage: apiClient.deleteVirtualIPImage.bind(apiClient),
  setDefaultVirtualIPImage: apiClient.setDefaultVirtualIPImage.bind(apiClient),
}

export const storyAPI = {
  getStories: apiClient.getStories.bind(apiClient),
  getStory: apiClient.getStory.bind(apiClient),
  generateStory: apiClient.generateStory.bind(apiClient),
  updateStory: apiClient.updateStory.bind(apiClient),
  deleteStory: apiClient.deleteStory.bind(apiClient),
  getStoryCharacters: apiClient.getStoryCharacters.bind(apiClient),
  getStoryGenres: apiClient.getStoryGenres.bind(apiClient),
}

export const episodeAPI = {
  getEpisodes: apiClient.getEpisodes.bind(apiClient),
  getEpisode: apiClient.getEpisode.bind(apiClient),
  generateEpisodes: apiClient.generateEpisodes.bind(apiClient),
  updateEpisode: apiClient.updateEpisode.bind(apiClient),
  deleteEpisode: apiClient.deleteEpisode.bind(apiClient),
  getStoryEpisodes: apiClient.getStoryEpisodes.bind(apiClient),
  regenerateEpisode: apiClient.regenerateEpisode.bind(apiClient),
}

export const scriptAPI = {
  getScripts: apiClient.getScripts.bind(apiClient),
  getScript: apiClient.getScript.bind(apiClient),
  generateScript: apiClient.generateScript.bind(apiClient),
  updateScript: apiClient.updateScript.bind(apiClient),
  deleteScript: apiClient.deleteScript.bind(apiClient),
  getEpisodeScripts: apiClient.getEpisodeScripts.bind(apiClient),
  regenerateScript: apiClient.regenerateScript.bind(apiClient),
  getScriptFormats: apiClient.getScriptFormats.bind(apiClient),
  getScriptLanguages: apiClient.getScriptLanguages.bind(apiClient),
  exportScript: apiClient.exportScript.bind(apiClient),
}

// 虚拟IP图像管理API
export const virtualIPImageAPI = {
  // 获取虚拟IP图像列表
  getImages: async (virtualIPId: number, category?: string): Promise<VirtualIPImage[]> => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    
    const response = await fetch(`${API_BASE_URL}/virtual-ips/${virtualIPId}/images?${params}`);
    if (!response.ok) throw new Error('获取图像列表失败');
    return response.json();
  },

  // 上传图像
  uploadImage: async (
    virtualIPId: number, 
    file: File, 
    category: string = 'portrait',
    tags: string = '',
    isDefault: boolean = false
  ): Promise<VirtualIPImage> => {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('category', category);
    formData.append('tags', tags);
    formData.append('is_default', isDefault.toString());

    const response = await fetch(`${API_BASE_URL}/virtual-ips/${virtualIPId}/images`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('上传图像失败');
    return response.json();
  },

  // AI生成图像
  generateImage: async (
    virtualIPId: number,
    request: AIImageGenerationRequest
  ): Promise<VirtualIPImage> => {
    const formData = new FormData();
    formData.append('style', request.style);
    formData.append('category', request.category);
    formData.append('additional_prompts', request.additional_prompts);
    formData.append('is_default', request.is_default.toString());

    const response = await fetch(`${API_BASE_URL}/virtual-ips/${virtualIPId}/images/generate`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('AI图像生成失败');
    return response.json();
  },

  // 更新图像信息
  updateImage: async (
    virtualIPId: number,
    imageId: number,
    update: VirtualIPImageUpdate
  ): Promise<VirtualIPImage> => {
    const response = await fetch(`${API_BASE_URL}/virtual-ips/${virtualIPId}/images/${imageId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(update),
    });
    if (!response.ok) throw new Error('更新图像失败');
    return response.json();
  },

  // 删除图像
  deleteImage: async (virtualIPId: number, imageId: number): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/virtual-ips/${virtualIPId}/images/${imageId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('删除图像失败');
  },

  // 设置默认图像
  setDefaultImage: async (virtualIPId: number, imageId: number): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/virtual-ips/${virtualIPId}/images/${imageId}/set-default`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('设置默认图像失败');
  },

  // 获取图像分类
  getCategories: async (virtualIPId: number): Promise<string[]> => {
    const response = await fetch(`${API_BASE_URL}/virtual-ips/${virtualIPId}/images/categories`);
    if (!response.ok) throw new Error('获取图像分类失败');
    return response.json();
  },
};

export default apiClient 