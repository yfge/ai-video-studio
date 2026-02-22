/**
 * @deprecated Legacy compatibility entrypoint.
 * Import from:
 * - '@/utils/api/client'
 * - '@/utils/api/types'
 * - '@/utils/api/endpoints'
 */

export {
  httpClient,
  http,
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  type HttpClientOptions,
  type HttpResponse,
} from "./api/client";

export * from "./api/types";
export * from "./api/endpoints";
