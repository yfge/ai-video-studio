/**
 * Admin/User Management API endpoints.
 */

import { httpClient } from "../client";
import type {
  AdminUser,
  UserListResponse,
  UserStatsResponse,
  UserApprovalRequest,
  UserAuditLog,
} from "../types/user.types";
import type { ApiResponse } from "../types/common.types";

/**
 * Get paginated list of users (admin only).
 */
async function getUsers(params?: {
  page?: number;
  size?: number;
  status_filter?: string;
  role_filter?: string;
  search?: string;
}): Promise<ApiResponse<UserListResponse>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.append("page", params.page.toString());
  if (params?.size) searchParams.append("size", params.size.toString());
  if (params?.status_filter)
    searchParams.append("status_filter", params.status_filter);
  if (params?.role_filter)
    searchParams.append("role_filter", params.role_filter);
  if (params?.search) searchParams.append("search", params.search);

  const queryString = searchParams.toString();
  const endpoint = queryString
    ? `/api/v1/admin/users?${queryString}`
    : "/api/v1/admin/users";

  return httpClient<UserListResponse>(endpoint);
}

/**
 * Get a specific user by ID.
 */
async function getUser(userId: number): Promise<ApiResponse<AdminUser>> {
  return httpClient<AdminUser>(`/api/v1/admin/users/${userId}`);
}

/**
 * Approve or reject a user.
 */
async function approveUser(
  userId: number,
  data: UserApprovalRequest,
): Promise<ApiResponse<AdminUser>> {
  return httpClient<AdminUser>(`/api/v1/admin/users/${userId}/approval`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Update user role (admin/superuser).
 */
async function updateUserRole(
  userId: number,
  data: {
    is_admin?: boolean;
    is_superuser?: boolean;
    role_change_reason?: string;
  },
): Promise<ApiResponse<AdminUser>> {
  const formData = new URLSearchParams();
  if (data.is_admin !== undefined)
    formData.append("is_admin", data.is_admin.toString());
  if (data.is_superuser !== undefined)
    formData.append("is_superuser", data.is_superuser.toString());
  if (data.role_change_reason)
    formData.append("reason", data.role_change_reason);

  return httpClient<AdminUser>(`/api/v1/admin/users/${userId}/role`, {
    method: "PUT",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData.toString(),
  });
}

/**
 * Suspend a user account.
 */
async function suspendUser(
  userId: number,
  data: { duration_hours?: number; reason?: string },
): Promise<ApiResponse<AdminUser>> {
  const searchParams = new URLSearchParams();
  if (data.duration_hours)
    searchParams.append("duration_hours", data.duration_hours.toString());
  if (data.reason) searchParams.append("reason", data.reason);

  const queryString = searchParams.toString();
  const endpoint = queryString
    ? `/api/v1/admin/users/${userId}/suspend?${queryString}`
    : `/api/v1/admin/users/${userId}/suspend`;

  return httpClient<AdminUser>(endpoint, { method: "PUT" });
}

/**
 * Reactivate a suspended user.
 */
async function reactivateUser(userId: number): Promise<ApiResponse<AdminUser>> {
  return httpClient<AdminUser>(`/api/v1/admin/users/${userId}/reactivate`, {
    method: "PUT",
  });
}

/**
 * Delete a user account.
 */
async function deleteUser(
  userId: number,
): Promise<ApiResponse<{ message: string; success: boolean }>> {
  return httpClient<{ message: string; success: boolean }>(
    `/api/v1/admin/users/${userId}`,
    {
      method: "DELETE",
    },
  );
}

/**
 * Get user statistics.
 */
async function getUserStats(): Promise<ApiResponse<UserStatsResponse>> {
  return httpClient<UserStatsResponse>("/api/v1/admin/stats");
}

/**
 * Get audit logs for a user.
 */
async function getUserAuditLogs(
  userId: number,
  params?: { page?: number; size?: number },
): Promise<ApiResponse<UserAuditLog[]>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.append("page", params.page.toString());
  if (params?.size) searchParams.append("size", params.size.toString());

  const queryString = searchParams.toString();
  const endpoint = queryString
    ? `/api/v1/admin/users/${userId}/audit-logs?${queryString}`
    : `/api/v1/admin/users/${userId}/audit-logs`;

  return httpClient<UserAuditLog[]>(endpoint);
}

/**
 * Reset failed login attempts for a user.
 */
async function resetUserLoginAttempts(
  userId: number,
): Promise<ApiResponse<AdminUser>> {
  return httpClient<AdminUser>(
    `/api/v1/admin/users/${userId}/reset-login-attempts`,
    {
      method: "POST",
    },
  );
}

/**
 * Generate activation token for a user.
 */
async function generateUserActivationToken(
  userId: number,
): Promise<ApiResponse<{ activation_token: string; message: string }>> {
  return httpClient<{ activation_token: string; message: string }>(
    `/api/v1/admin/users/${userId}/generate-activation-token`,
    { method: "POST" },
  );
}

/**
 * Update user admin fields.
 */
async function updateUserAdmin(
  userId: number,
  data: {
    is_active?: boolean;
    is_admin?: boolean;
    is_approved?: boolean;
    email_verified?: boolean;
    failed_login_attempts?: number;
    account_locked_until?: string;
  },
): Promise<ApiResponse<AdminUser>> {
  return httpClient<AdminUser>(`/api/v1/admin/users/${userId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Admin API namespace.
 */
export const adminAPI = {
  getUsers,
  getUser,
  approveUser,
  updateUserRole,
  suspendUser,
  reactivateUser,
  deleteUser,
  getUserStats,
  getUserAuditLogs,
  resetUserLoginAttempts,
  generateUserActivationToken,
  updateUserAdmin,
};
