/**
 * Authentication API endpoints.
 */

import { httpClient, setAuthToken, clearAuthToken } from "../client";
import type { User, LoginRequest, RegisterRequest } from "../types/user.types";
import type { ApiResponse } from "../types/common.types";

/**
 * Login with email and password.
 * Returns access token on success.
 */
export async function login(
  credentials: LoginRequest,
): Promise<ApiResponse<{ access_token: string; token_type: string }>> {
  // Backend expects application/x-www-form-urlencoded format
  const formBody = new URLSearchParams();
  formBody.append("username", credentials.email);
  formBody.append("password", credentials.password);

  const response = await httpClient<{
    access_token: string;
    token_type: string;
  }>("/api/v1/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formBody.toString(),
    retry: false, // Don't retry on 401 for login
  });

  // Save token on successful login
  if (response.success && response.data?.access_token) {
    setAuthToken(response.data.access_token);
  }

  return response;
}

/**
 * Register a new user account.
 */
export async function register(
  userData: RegisterRequest,
): Promise<ApiResponse<User>> {
  return httpClient<User>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(userData),
  });
}

/**
 * Logout current user (clears local token).
 */
export async function logout(): Promise<ApiResponse<void>> {
  clearAuthToken();
  return { success: true };
}

/**
 * Get current authenticated user.
 */
export async function getCurrentUser(): Promise<ApiResponse<User>> {
  return httpClient<User>("/api/v1/auth/me");
}

/**
 * Auth API namespace for convenient imports.
 */
export const authAPI = {
  login,
  register,
  logout,
  getCurrentUser,
};
