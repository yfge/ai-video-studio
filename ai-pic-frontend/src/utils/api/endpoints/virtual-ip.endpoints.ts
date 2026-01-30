/**
 * Virtual IP (Character) API endpoints.
 */

import { httpClient } from "../client";
import type {
  VirtualIP,
  CreateVirtualIPRequest,
  UpdateVirtualIPRequest,
  VirtualIPAICreateRequest,
  VirtualIPAIGenerationRequest,
  VirtualIPAIGenerationResponse,
  VirtualIPAIGenerationDetailedResponse,
} from "../types/virtual-ip.types";
import type { ApiResponse } from "../types/common.types";

// Helper to check if value is a business ID (string with 16+ chars or non-numeric)
function isBusinessIdentifier(value: number | string): boolean {
  if (typeof value === "number") return false;
  const raw = String(value || "").trim();
  if (!raw) return false;
  const isDigitsOnly = /^\d+$/.test(raw);
  return !isDigitsOnly || raw.length >= 16;
}

// Helper to build virtual IP path
function virtualIPPath(
  ipIdOrBiz: number | string,
  suffix: string = "",
): string {
  const base = isBusinessIdentifier(ipIdOrBiz)
    ? `/api/v1/virtual-ips/business/${ipIdOrBiz}`
    : `/api/v1/virtual-ips/${ipIdOrBiz}`;
  return `${base}${suffix}`;
}

/**
 * Get list of virtual IPs.
 */
export async function getVirtualIPs(params?: {
  search?: string;
  tags?: string[];
  page?: number;
  limit?: number;
}): Promise<ApiResponse<VirtualIP[]>> {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.append("search", params.search);
  if (params?.tags)
    params.tags.forEach((tag) => searchParams.append("tags", tag));
  if (params?.page) searchParams.append("page", params.page.toString());
  if (params?.limit) searchParams.append("limit", params.limit.toString());

  const queryString = searchParams.toString();
  const endpoint = queryString
    ? `/api/v1/virtual-ips/?${queryString}`
    : "/api/v1/virtual-ips/";

  return httpClient<VirtualIP[]>(endpoint);
}

/**
 * Get a specific virtual IP by ID or business ID.
 */
export async function getVirtualIP(
  id: number | string,
): Promise<ApiResponse<VirtualIP>> {
  return httpClient<VirtualIP>(virtualIPPath(id));
}

/**
 * Create a new virtual IP.
 */
export async function createVirtualIP(
  data: CreateVirtualIPRequest,
): Promise<ApiResponse<VirtualIP>> {
  return httpClient<VirtualIP>("/api/v1/virtual-ips/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update a virtual IP.
 */
export async function updateVirtualIP(
  id: number | string,
  data: UpdateVirtualIPRequest,
): Promise<ApiResponse<VirtualIP>> {
  return httpClient<VirtualIP>(virtualIPPath(id), {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a virtual IP.
 */
export async function deleteVirtualIP(
  id: number | string,
): Promise<ApiResponse<void>> {
  return httpClient<void>(virtualIPPath(id), { method: "DELETE" });
}

/**
 * Generate AI content for virtual IP (description, backstory, etc.).
 */
export async function generateAIContent(
  data: VirtualIPAIGenerationRequest,
): Promise<ApiResponse<VirtualIPAIGenerationResponse>> {
  return httpClient<VirtualIPAIGenerationResponse>(
    "/api/v1/virtual-ips/generate-ai-content",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

/**
 * Generate AI content with detailed generation info.
 */
export async function generateAIContentDetailed(
  data: VirtualIPAIGenerationRequest,
): Promise<ApiResponse<VirtualIPAIGenerationDetailedResponse>> {
  return httpClient<VirtualIPAIGenerationDetailedResponse>(
    "/api/v1/virtual-ips/generate-ai-content-detailed",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

/**
 * Create virtual IP with AI-generated content.
 */
export async function createVirtualIPWithAI(
  data: VirtualIPAICreateRequest,
): Promise<ApiResponse<VirtualIP>> {
  return httpClient<VirtualIP>("/api/v1/virtual-ips/create-with-ai", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Virtual IP API namespace.
 */
export const virtualIPAPI = {
  getVirtualIPs,
  getVirtualIP,
  createVirtualIP,
  updateVirtualIP,
  deleteVirtualIP,
  generateAIContent,
  generateAIContentDetailed,
  createVirtualIPWithAI,
};
