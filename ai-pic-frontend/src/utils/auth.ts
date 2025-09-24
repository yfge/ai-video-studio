// 认证工具函数
import { User } from './api'

export interface AuthUser {
  username: string;
  token: string;
}

/**
 * 检查用户是否已登录
 */
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  
  const token = localStorage.getItem('auth_token');
  const userInfo = localStorage.getItem('user_info');
  
  return !!(token && userInfo);
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser(): AuthUser | null {
  if (typeof window === 'undefined') return null;
  
  const token = localStorage.getItem('auth_token');
  const userInfo = localStorage.getItem('user_info');
  
  if (!token || !userInfo) return null;
  
  try {
    const user = JSON.parse(userInfo);
    return {
      username: user.username,
      token: token
    };
  } catch (error) {
    console.error('解析用户信息失败:', error);
    return null;
  }
}

/**
 * 获取认证token
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  
  return localStorage.getItem('auth_token');
}

/**
 * 清除认证信息
 */
export function clearAuth(): void {
  if (typeof window === 'undefined') return;
  
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user_info');
}

/**
 * 重定向到登录页面
 */
export function redirectToLogin(): void {
  if (typeof window === 'undefined') return;
  
  window.location.href = '/login';
}

/**
 * 检查并要求认证
 * 如果未登录则重定向到登录页面
 */
export function requireAuth(): boolean {
  const authenticated = isAuthenticated();
  
  if (!authenticated) {
    redirectToLogin();
    return false;
  }
  
  return true;
}

/**
 * 检查用户是否有管理员权限
 */
export const isAdmin = (user: User | null): boolean => {
  return user ? (user.is_admin || user.is_superuser) : false
}

/**
 * 检查用户是否为超级用户
 */
export const isSuperUser = (user: User | null): boolean => {
  return user ? user.is_superuser : false
}

/**
 * 检查用户是否已激活且被批准
 */
export const isActiveUser = (user: User | null): boolean => {
  return user ? (user.is_active && user.is_approved && user.email_verified) : false
}

/**
 * 获取用户状态显示文本
 */
export const getUserStatus = (user: User): string => {
  if (!user.email_verified) return '待验证邮箱'
  if (!user.is_approved) return '待审批'
  if (!user.is_active) return '已停用'
  if (user.is_account_locked) return '已锁定'
  return '正常'
}

/**
 * 获取用户状态颜色
 */
export const getUserStatusColor = (user: User): string => {
  if (!user.email_verified || !user.is_approved) return 'text-yellow-600'
  if (!user.is_active || user.is_account_locked) return 'text-red-600'
  return 'text-green-600'
}

/**
 * 获取用户角色显示文本
 */
export const getUserRole = (user: User): string => {
  if (user.is_superuser) return '超级管理员'
  if (user.is_admin) return '管理员'
  return '普通用户'
}

/**
 * 获取用户角色颜色
 */
export const getUserRoleColor = (user: User): string => {
  if (user.is_superuser) return 'text-purple-600'
  if (user.is_admin) return 'text-blue-600'
  return 'text-gray-600'
}

/**
 * 格式化时间显示
 */
export const formatDateTime = (dateString?: string): string => {
  if (!dateString) return '-'
  
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

/**
 * 格式化相对时间
 */
export const formatRelativeTime = (dateString?: string): string => {
  if (!dateString) return '-'
  
  const date = new Date(dateString)
  const now = new Date()
  const diffInMs = now.getTime() - date.getTime()
  
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60))
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60))
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))
  
  if (diffInMinutes < 1) return '刚刚'
  if (diffInMinutes < 60) return `${diffInMinutes}分钟前`
  if (diffInHours < 24) return `${diffInHours}小时前`
  if (diffInDays < 7) return `${diffInDays}天前`
  
  return formatDateTime(dateString)
}

/**
 * 检查是否有待处理的用户审批
 */
export const hasPendingApprovals = (stats: { pending_approval: number } | null): boolean => {
  return stats ? stats.pending_approval > 0 : false
}