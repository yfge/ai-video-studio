/**
 * User-related type definitions.
 */

// Base user interface
export interface User {
  id: number;
  business_id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  is_admin: boolean;
  is_approved: boolean;
  email_verified: boolean;
  last_login_at?: string;
  failed_login_attempts: number;
  is_account_locked: boolean;
  language?: string;
  timezone?: string;
  created_at: string;
  updated_at?: string;
}

// Extended admin user with additional fields
export interface AdminUser extends User {
  approved_at?: string;
  approved_by_user_id?: number;
  activation_token_expires?: string;
  account_locked_until?: string;
}

// User list response with pagination
export interface UserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// User statistics for admin dashboard
export interface UserStatsResponse {
  total_users: number;
  active_users: number;
  pending_approval: number;
  suspended_users: number;
  admin_users: number;
  recent_registrations: number;
}

// User approval request
export interface UserApprovalRequest {
  action: "approve" | "reject";
  reason?: string;
}

// User audit log entry
export interface UserAuditLog {
  id: number;
  user_id: number;
  admin_user_id?: number;
  action: string;
  old_values?: string;
  new_values?: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

// Authentication requests
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}
