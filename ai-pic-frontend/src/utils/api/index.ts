/**
 * API Module
 *
 * Exports HTTP client utilities and types.
 *
 * Usage:
 * ```typescript
 * import { http, getAuthToken } from '@/utils/api'
 * import type { User, ApiResponse } from '@/utils/api/types'
 * ```
 */

export {
  httpClient,
  http,
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  type HttpClientOptions,
  type HttpResponse,
} from './client'

// Keep api.ts exports for backward compatibility (../api.ts from here)
export * from '../api'
