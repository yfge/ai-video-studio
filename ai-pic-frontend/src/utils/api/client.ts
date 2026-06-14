import { applyTraceHeaders, readTraceHeaders } from "@/utils/api/trace";
import type { ApiTraceMeta } from "@/utils/api/types";
import {
  buildLoginPathForReturn,
  currentBrowserReturnPath,
} from "@/utils/authReturnPath";

export interface HttpClientOptions extends RequestInit {
  /**
   * Skip automatic auth token (default: false)
   */
  skipAuth?: boolean;
  /**
   * Automatic retry on 401/403 (default: false)
   */
  retry?: boolean;
  /**
   * Custom error handler
   */
  onError?: (error: Error) => void;
}

export interface HttpResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  trace?: ApiTraceMeta;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

export function setAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("auth_token", token);
}

export function clearAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("auth_token");
}

function buildHeaders(options: HttpClientOptions = {}): HeadersInit {
  const { skipAuth, body } = options;

  // Handle FormData (don't set Content-Type, let browser set it with boundary)
  const isFormData =
    typeof FormData !== "undefined" && body instanceof FormData;

  const headers: Record<string, string> = isFormData
    ? {}
    : { "Content-Type": "application/json" };

  // Merge custom headers
  if (options.headers) {
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => {
        headers[key] = value;
      });
    } else if (Array.isArray(options.headers)) {
      options.headers.forEach(([key, value]) => {
        headers[key] = value;
      });
    } else {
      Object.assign(headers, options.headers);
    }
  }

  // Add auth token unless explicitly skipped
  if (!skipAuth) {
    const token = getAuthToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  applyTraceHeaders(headers);
  return headers;
}

export async function httpClient<T = unknown>(
  endpoint: string,
  options: HttpClientOptions = {},
): Promise<HttpResponse<T>> {
  const { onError, skipAuth, retry, ...fetchOptions } = options;
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = buildHeaders({ skipAuth, ...options });
  const trace = {
    clientRequestId: (headers as Record<string, string>)["X-Client-Request-ID"],
    harnessRunId: (headers as Record<string, string>)["X-Harness-Run-ID"],
  };

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    });

    // Handle 401 Unauthorized with optional retry
    if (response.status === 401 && retry !== false) {
      // Clear invalid token
      clearAuthToken();

      // Redirect to login if not already there
      if (
        typeof window !== "undefined" &&
        !window.location.pathname.includes("/login")
      ) {
        window.location.href = buildLoginPathForReturn(
          currentBrowserReturnPath(),
        );
      }

      return {
        success: false,
        error: "登录已过期，请重新登录",
        trace,
      };
    }

    // Parse JSON response
    let data: HttpResponse<T>;

    // Handle empty responses (204 No Content, etc.)
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      const json = await response.json();

      // If backend returns standard {success, data} format, use it
      if (json.hasOwnProperty("success")) {
        data = json;
      } else {
        // Otherwise, wrap in standard format
        data = {
          success: response.ok,
          data: json as T,
        };
      }
      data.trace = readTraceHeaders(response, trace);
    } else {
      // Non-JSON response
      data = {
        success: response.ok,
        data: undefined as unknown as T,
        trace: readTraceHeaders(response, trace),
      };
    }

    // Handle HTTP errors
    if (!response.ok) {
      const errorMessage =
        data.error ||
        data.message ||
        `HTTP ${response.status}: ${response.statusText}`;
      const error = new Error(errorMessage);

      if (onError) {
        onError(error);
      }

      return {
        ...data,
        success: false,
        error: errorMessage,
        trace: readTraceHeaders(response, trace),
      };
    }

    return { ...data, trace: readTraceHeaders(response, trace) };
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err));

    if (onError) {
      onError(error);
    }

    return {
      success: false,
      error: error.message,
      trace,
    };
  }
}
