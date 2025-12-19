/**
 * API Module
 *
 * Exports HTTP client utilities, types, and domain-specific endpoints.
 *
 * Usage:
 * ```typescript
 * import { http, getAuthToken } from '@/utils/api'
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
} from './client';

// Type definitions
export * from './types';

// Domain-specific API endpoints (new modular structure)
export * from './endpoints';

// Re-export apiClient from legacy api.ts for backward compatibility
// Note: Domain-specific API objects (authAPI, storyAPI, etc.) are now
// provided by ./endpoints which uses the new httpClient-based approach.
// The legacy apiClient is kept for components that directly use it.
export { apiClient } from '../api';
