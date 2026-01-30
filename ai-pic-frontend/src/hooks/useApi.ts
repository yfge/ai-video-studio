/**
 * useApi Hook
 *
 * Provides fetch wrapper with automatic auth token and error handling.
 *
 * Usage:
 * ```tsx
 * const api = useApi()
 *
 * async function loadUsers() {
 *   const response = await api.get<User[]>('/api/v1/users')
 *   if (response.success) {
 *     setUsers(response.data)
 *   }
 * }
 *
 * async function createUser(data: CreateUserRequest) {
 *   const response = await api.post<User>('/api/v1/users', data)
 *   return response
 * }
 * ```
 */

import { useCallback } from "react";
import type { ApiResponse } from "@/utils/api";

export interface UseApiRequestOptions extends RequestInit {
  /**
   * Skip automatic auth token (default: false)
   */
  skipAuth?: boolean;
  /**
   * Custom error handler
   */
  onError?: (error: Error) => void;
}

export interface UseApiReturn {
  /**
   * GET request
   */
  get: <T>(
    endpoint: string,
    options?: UseApiRequestOptions,
  ) => Promise<ApiResponse<T>>;
  /**
   * POST request
   */
  post: <T>(
    endpoint: string,
    data?: unknown,
    options?: UseApiRequestOptions,
  ) => Promise<ApiResponse<T>>;
  /**
   * PUT request
   */
  put: <T>(
    endpoint: string,
    data?: unknown,
    options?: UseApiRequestOptions,
  ) => Promise<ApiResponse<T>>;
  /**
   * DELETE request
   */
  del: <T>(
    endpoint: string,
    options?: UseApiRequestOptions,
  ) => Promise<ApiResponse<T>>;
  /**
   * PATCH request
   */
  patch: <T>(
    endpoint: string,
    data?: unknown,
    options?: UseApiRequestOptions,
  ) => Promise<ApiResponse<T>>;
  /**
   * Generic request with custom method
   */
  request: <T>(
    endpoint: string,
    options?: UseApiRequestOptions,
  ) => Promise<ApiResponse<T>>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

/**
 * Get auth token from localStorage
 */
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

/**
 * Build headers with auth token
 */
function buildHeaders(options: UseApiRequestOptions = {}): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Add auth token unless explicitly skipped
  if (!options.skipAuth) {
    const token = getAuthToken();
    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }
  }

  return headers;
}

/**
 * Hook for API requests with auth and error handling
 *
 * @returns API request methods
 *
 * @example
 * const api = useApi()
 *
 * // GET request
 * const users = await api.get<User[]>('/api/v1/users')
 *
 * @example
 * // POST request
 * const api = useApi()
 * const newUser = await api.post<User>('/api/v1/users', {
 *   username: 'john',
 *   email: 'john@example.com'
 * })
 *
 * @example
 * // With custom error handling
 * const api = useApi()
 * const response = await api.get<User>('/api/v1/users/123', {
 *   onError: (err) => console.error('Failed to load user:', err)
 * })
 *
 * @example
 * // Skip auth for public endpoints
 * const api = useApi()
 * const models = await api.get<Model[]>('/api/v1/public/models', {
 *   skipAuth: true
 * })
 */
export function useApi(): UseApiReturn {
  const request = useCallback(
    async <T>(
      endpoint: string,
      options: UseApiRequestOptions = {},
    ): Promise<ApiResponse<T>> => {
      const { onError, skipAuth, ...fetchOptions } = options;

      const url = `${API_BASE_URL}${endpoint}`;
      const headers = buildHeaders({ skipAuth, ...options });

      try {
        const response = await fetch(url, {
          ...fetchOptions,
          headers,
        });

        // Parse JSON response
        let data: ApiResponse<T>;

        // Handle empty responses
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          data = await response.json();
        } else {
          // Non-JSON response (e.g., 204 No Content)
          data = {
            success: response.ok,
            data: undefined as unknown as T,
          };
        }

        // Handle HTTP errors
        if (!response.ok) {
          const error = new Error(
            data.message ||
              data.error ||
              `HTTP ${response.status}: ${response.statusText}`,
          );

          if (onError) {
            onError(error);
          }

          // Return error response (data might already have success: false)
          return {
            ...data,
            success: false,
            error: error.message,
          };
        }

        return data;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));

        if (onError) {
          onError(error);
        }

        return {
          success: false,
          error: error.message,
        };
      }
    },
    [],
  );

  const get = useCallback(
    <T>(endpoint: string, options?: UseApiRequestOptions) => {
      return request<T>(endpoint, { ...options, method: "GET" });
    },
    [request],
  );

  const post = useCallback(
    <T>(endpoint: string, data?: unknown, options?: UseApiRequestOptions) => {
      return request<T>(endpoint, {
        ...options,
        method: "POST",
        body: data ? JSON.stringify(data) : undefined,
      });
    },
    [request],
  );

  const put = useCallback(
    <T>(endpoint: string, data?: unknown, options?: UseApiRequestOptions) => {
      return request<T>(endpoint, {
        ...options,
        method: "PUT",
        body: data ? JSON.stringify(data) : undefined,
      });
    },
    [request],
  );

  const del = useCallback(
    <T>(endpoint: string, options?: UseApiRequestOptions) => {
      return request<T>(endpoint, { ...options, method: "DELETE" });
    },
    [request],
  );

  const patch = useCallback(
    <T>(endpoint: string, data?: unknown, options?: UseApiRequestOptions) => {
      return request<T>(endpoint, {
        ...options,
        method: "PATCH",
        body: data ? JSON.stringify(data) : undefined,
      });
    },
    [request],
  );

  return {
    get,
    post,
    put,
    del,
    patch,
    request,
  };
}
