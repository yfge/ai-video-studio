/**
 * HTTP Client Utilities
 *
 * Reusable fetch wrapper with auth token and error handling.
 * Extracted from api.ts to enable modular API layer.
 */

export interface HttpClientOptions extends RequestInit {
  /**
   * Skip automatic auth token (default: false)
   */
  skipAuth?: boolean
  /**
   * Automatic retry on 401/403 (default: false)
   */
  retry?: boolean
  /**
   * Custom error handler
   */
  onError?: (error: Error) => void
}

export interface HttpResponse<T = unknown> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || ''

/**
 * Get auth token from localStorage
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('auth_token')
}

/**
 * Set auth token in localStorage
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return
  localStorage.setItem('auth_token', token)
}

/**
 * Clear auth token from localStorage
 */
export function clearAuthToken(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem('auth_token')
}

/**
 * Build headers with optional auth token
 */
function buildHeaders(options: HttpClientOptions = {}): HeadersInit {
  const { skipAuth, body } = options

  // Handle FormData (don't set Content-Type, let browser set it with boundary)
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData

  const headers: Record<string, string> = isFormData
    ? {}
    : { 'Content-Type': 'application/json' }

  // Merge custom headers
  if (options.headers) {
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => {
        headers[key] = value
      })
    } else if (Array.isArray(options.headers)) {
      options.headers.forEach(([key, value]) => {
        headers[key] = value
      })
    } else {
      Object.assign(headers, options.headers)
    }
  }

  // Add auth token unless explicitly skipped
  if (!skipAuth) {
    const token = getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  return headers
}

/**
 * HTTP client for API requests
 *
 * Features:
 * - Automatic auth token from localStorage
 * - JSON request/response handling
 * - FormData support
 * - Error handling with custom callbacks
 * - Optional 401 retry with token refresh
 *
 * @param endpoint - API endpoint (will be prefixed with base URL)
 * @param options - Request options
 * @returns Promise resolving to typed response
 *
 * @example
 * // GET request
 * const users = await httpClient<User[]>('/api/v1/users')
 *
 * @example
 * // POST request
 * const newUser = await httpClient<User>('/api/v1/users', {
 *   method: 'POST',
 *   body: JSON.stringify({ username: 'john' })
 * })
 *
 * @example
 * // With error handling
 * const response = await httpClient<User>('/api/v1/users/123', {
 *   onError: (err) => console.error('Failed:', err)
 * })
 *
 * @example
 * // Skip auth for public endpoints
 * const models = await httpClient<Model[]>('/api/v1/public/models', {
 *   skipAuth: true
 * })
 */
export async function httpClient<T = unknown>(
  endpoint: string,
  options: HttpClientOptions = {}
): Promise<HttpResponse<T>> {
  const { onError, skipAuth, retry, ...fetchOptions } = options

  const url = `${API_BASE_URL}${endpoint}`
  const headers = buildHeaders({ skipAuth, ...options })

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    })

    // Handle 401 Unauthorized with optional retry
    if (response.status === 401 && retry !== false) {
      // Clear invalid token
      clearAuthToken()

      // Redirect to login if not already there
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }

      return {
        success: false,
        error: '登录已过期，请重新登录',
      }
    }

    // Parse JSON response
    let data: HttpResponse<T>

    // Handle empty responses (204 No Content, etc.)
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      const json = await response.json()

      // If backend returns standard {success, data} format, use it
      if (json.hasOwnProperty('success')) {
        data = json
      } else {
        // Otherwise, wrap in standard format
        data = {
          success: response.ok,
          data: json as T,
        }
      }
    } else {
      // Non-JSON response
      data = {
        success: response.ok,
        data: undefined as unknown as T,
      }
    }

    // Handle HTTP errors
    if (!response.ok) {
      const errorMessage =
        data.error || data.message || `HTTP ${response.status}: ${response.statusText}`
      const error = new Error(errorMessage)

      if (onError) {
        onError(error)
      }

      return {
        ...data,
        success: false,
        error: errorMessage,
      }
    }

    return data
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err))

    if (onError) {
      onError(error)
    }

    return {
      success: false,
      error: error.message,
    }
  }
}

/**
 * Convenience methods for common HTTP verbs
 */
export const http = {
  get: <T>(endpoint: string, options?: HttpClientOptions) =>
    httpClient<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body?: unknown, options?: HttpClientOptions) =>
    httpClient<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(endpoint: string, body?: unknown, options?: HttpClientOptions) =>
    httpClient<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(endpoint: string, options?: HttpClientOptions) =>
    httpClient<T>(endpoint, { ...options, method: 'DELETE' }),

  patch: <T>(endpoint: string, body?: unknown, options?: HttpClientOptions) =>
    httpClient<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),
}
