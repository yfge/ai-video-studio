/**
 * Common API types shared across all domains.
 */

export interface ApiTraceMeta {
  clientRequestId?: string;
  harnessRunId?: string;
  requestId?: string;
}

// Generic API response wrapper
export interface ApiResponse<T = unknown> {
  success: boolean;
  status?: number;
  data?: T;
  message?: string;
  error?: string;
  trace?: ApiTraceMeta;
}
