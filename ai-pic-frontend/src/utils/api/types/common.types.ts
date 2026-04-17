/**
 * Common API types shared across all domains.
 */

// API base URL configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export interface ApiTraceMeta {
  clientRequestId?: string;
  harnessRunId?: string;
  requestId?: string;
}

// Generic API response wrapper
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  trace?: ApiTraceMeta;
}

// Pagination response
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Generic ID types
export type BusinessId = string;
export type NumericId = number;
