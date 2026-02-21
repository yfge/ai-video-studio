/**
 * API Module
 *
 * Exports HTTP client utilities, types, and domain-specific endpoints.
 *
 * Usage:
 * ```typescript
 * import { http, getAuthToken } from '@/utils/api/client'
 * import type { User, ApiResponse } from '@/utils/api/types'
 * import { authAPI, storyAPI } from '@/utils/api/endpoints'
 * ```
 */

// HTTP client utilities
export {
  httpClient,
  http,
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  type HttpClientOptions,
  type HttpResponse,
} from "./client";

// Type definitions
export * from "./types";

// Domain-specific API endpoints (new modular structure)
export * from "./endpoints";

// Do not export legacy apiClient from this module.
