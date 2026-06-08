"use client";

import { useCallback, useEffect, useState } from "react";
import { adminAPI } from "@/utils/api/endpoints";
import type { AdminUser } from "@/utils/api/types";
import RoleManagementModal from "./RoleManagementModal";

// Icons
const XIcon = ({ className = "" }) => (
  <svg
    className={className}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M6 18L18 6M6 6l12 12"
    />
  </svg>
);

const UserIcon = ({ className = "" }) => (
  <svg
    className={className}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
    />
  </svg>
);

const ClockIcon = ({ className = "" }) => (
  <svg
    className={className}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

const ShieldIcon = ({ className = "" }) => (
  <svg
    className={className}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
    />
  </svg>
);

const ExclamationIcon = ({ className = "" }) => (
  <svg
    className={className}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
    />
  </svg>
);

interface UserAuditLog {
  id: number;
  user_id: number;
  admin_user_id?: number;
  action: string;
  old_values?: string | null;
  new_values?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
}

interface UserDetailsModalProps {
  user: AdminUser | null;
  isOpen: boolean;
  onClose: () => void;
  onUserUpdate: (user: AdminUser) => void;
}

export default function UserDetailsModal({
  user,
  isOpen,
  onClose,
  onUserUpdate,
}: UserDetailsModalProps) {
  const [auditLogs, setAuditLogs] = useState<UserAuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"details" | "audit" | "security">(
    "details",
  );
  const [isPerformingAction, setIsPerformingAction] = useState(false);
  const [showRoleModal, setShowRoleModal] = useState(false);

  const loadAuditLogs = useCallback(async () => {
    if (!user) return;

    setLoading(true);
    try {
      const response = await adminAPI.getUserAuditLogs(user.id);
      if (response.success && response.data) {
        setAuditLogs(response.data);
      }
    } catch (error) {
      console.error("Failed to load audit logs:", error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Load audit logs when modal opens
  useEffect(() => {
    if (isOpen && user) {
      void loadAuditLogs();
    }
  }, [isOpen, user, loadAuditLogs]);

  const handleApproveUser = async () => {
    if (!user) return;

    setIsPerformingAction(true);
    try {
      const response = await adminAPI.approveUser(user.id, {
        action: "approve",
        reason: "Approved via user details modal",
      });

      if (response.success && response.data) {
        onUserUpdate(response.data);
        await loadAuditLogs(); // Refresh audit logs
      }
    } catch (error) {
      console.error("Failed to approve user:", error);
    } finally {
      setIsPerformingAction(false);
    }
  };

  const handleRejectUser = async () => {
    if (!user) return;

    setIsPerformingAction(true);
    try {
      const response = await adminAPI.approveUser(user.id, {
        action: "reject",
        reason: "Rejected via user details modal",
      });

      if (response.success && response.data) {
        onUserUpdate(response.data);
        await loadAuditLogs(); // Refresh audit logs
      }
    } catch (error) {
      console.error("Failed to reject user:", error);
    } finally {
      setIsPerformingAction(false);
    }
  };

  const handleSuspendUser = async () => {
    if (!user) return;

    setIsPerformingAction(true);
    try {
      const response = await adminAPI.suspendUser(user.id, {
        reason: "Suspended via user details modal",
      });

      if (response.success && response.data) {
        onUserUpdate(response.data);
        await loadAuditLogs(); // Refresh audit logs
      }
    } catch (error) {
      console.error("Failed to suspend user:", error);
    } finally {
      setIsPerformingAction(false);
    }
  };

  const handleReactivateUser = async () => {
    if (!user) return;

    setIsPerformingAction(true);
    try {
      const response = await adminAPI.reactivateUser(user.id);

      if (response.success && response.data) {
        onUserUpdate(response.data);
        await loadAuditLogs(); // Refresh audit logs
      }
    } catch (error) {
      console.error("Failed to reactivate user:", error);
    } finally {
      setIsPerformingAction(false);
    }
  };

  const handleRoleUpdate = (updatedUser: AdminUser) => {
    onUserUpdate(updatedUser);
    setShowRoleModal(false);
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleString("zh-CN");
  };

  const getStatusBadge = (user: AdminUser) => {
    if (!user.is_active) {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
          已停用
        </span>
      );
    }
    if (!user.is_approved) {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
          待审批
        </span>
      );
    }
    if (!user.email_verified) {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
          邮箱未验证
        </span>
      );
    }
    return (
      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
        正常
      </span>
    );
  };

  const getRoleBadge = (user: AdminUser) => {
    if (user.is_admin) {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
          管理员
        </span>
      );
    }
    return (
      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
        用户
      </span>
    );
  };

  const getActionIcon = (action: string) => {
    switch (action.toLowerCase()) {
      case "approved":
        return <ShieldIcon className="h-4 w-4 text-green-500" />;
      case "rejected":
      case "suspended":
        return <ExclamationIcon className="h-4 w-4 text-red-500" />;
      case "reactivated":
        return <UserIcon className="h-4 w-4 text-blue-500" />;
      default:
        return <ClockIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  if (!isOpen || !user) return null;

  const tabs = [
    { id: "details", name: "基本信息" },
    { id: "audit", name: "操作记录" },
    { id: "security", name: "安全信息" },
  ] as const;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
              <UserIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                {user.full_name || user.username}
              </h3>
              <p className="text-sm text-gray-500">用户ID: {user.id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === "details" && (
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 基本信息 */}
                <div className="space-y-4">
                  <h4 className="text-md font-medium text-gray-900">
                    基本信息
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        用户名
                      </label>
                      <p className="mt-1 text-sm text-gray-900">
                        {user.username}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        邮箱地址
                      </label>
                      <p className="mt-1 text-sm text-gray-900">{user.email}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        全名
                      </label>
                      <p className="mt-1 text-sm text-gray-900">
                        {user.full_name || "-"}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        用户状态
                      </label>
                      <div className="mt-1">{getStatusBadge(user)}</div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        用户角色
                      </label>
                      <div className="mt-1">{getRoleBadge(user)}</div>
                    </div>
                  </div>
                </div>

                {/* 时间信息 */}
                <div className="space-y-4">
                  <h4 className="text-md font-medium text-gray-900">
                    时间信息
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        注册时间
                      </label>
                      <p className="mt-1 text-sm text-gray-900">
                        {formatDateTime(user.created_at)}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        最后更新
                      </label>
                      <p className="mt-1 text-sm text-gray-900">
                        {formatDateTime(user.updated_at)}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">
                        最后登录
                      </label>
                      <p className="mt-1 text-sm text-gray-900">
                        {user.last_login_at
                          ? formatDateTime(user.last_login_at)
                          : "从未登录"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* 操作按钮 */}
              <div className="mt-8 flex flex-wrap gap-3">
                {!user.is_approved && (
                  <>
                    <button
                      onClick={handleApproveUser}
                      disabled={isPerformingAction}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
                    >
                      批准用户
                    </button>
                    <button
                      onClick={handleRejectUser}
                      disabled={isPerformingAction}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 disabled:opacity-50"
                    >
                      拒绝用户
                    </button>
                  </>
                )}

                {user.is_approved && user.is_active && (
                  <button
                    onClick={handleSuspendUser}
                    disabled={isPerformingAction}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    暂停用户
                  </button>
                )}

                {!user.is_active && (
                  <button
                    onClick={handleReactivateUser}
                    disabled={isPerformingAction}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    重新激活
                  </button>
                )}

                <button
                  onClick={() => setShowRoleModal(true)}
                  disabled={isPerformingAction}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  <ShieldIcon className="h-4 w-4 mr-2" />
                  管理角色
                </button>
              </div>
            </div>
          )}

          {activeTab === "audit" && (
            <div className="p-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">
                操作记录
              </h4>

              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : auditLogs.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  暂无操作记录
                </div>
              ) : (
                <div className="space-y-3">
                  {auditLogs.map((log) => (
                    <div
                      key={log.id}
                      className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex-shrink-0 mt-1">
                        {getActionIcon(log.action)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900">
                            {log.action}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatDateTime(log.created_at)}
                          </p>
                        </div>
                        <p className="text-sm text-gray-600">
                          操作人:{" "}
                          {log.admin_user_id
                            ? `管理员 ID: ${log.admin_user_id}`
                            : "系统"}
                        </p>
                        {(log.old_values || log.new_values) && (
                          <p className="text-sm text-gray-500 mt-1">
                            {log.old_values && `原值: ${log.old_values}`}
                            {log.new_values && ` → 新值: ${log.new_values}`}
                          </p>
                        )}
                        {log.ip_address && (
                          <p className="text-xs text-gray-400 mt-1">
                            IP: {log.ip_address}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "security" && (
            <div className="p-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">
                安全信息
              </h4>

              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-sm font-medium text-gray-500">
                      邮箱验证状态
                    </label>
                    <div className="mt-1">
                      {user.email_verified ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          ✓ 已验证
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          ✗ 未验证
                        </span>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-500">
                      登录失败次数
                    </label>
                    <p className="mt-1 text-sm text-gray-900">
                      {user.failed_login_attempts || 0} 次
                    </p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-500">
                      账户锁定状态
                    </label>
                    <div className="mt-1">
                      {user.account_locked_until ? (
                        <div>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            🔒 已锁定
                          </span>
                          <p className="text-xs text-gray-500 mt-1">
                            锁定至: {formatDateTime(user.account_locked_until)}
                          </p>
                        </div>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          🔓 正常
                        </span>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-500">
                      账户权限
                    </label>
                    <div className="mt-1 space-x-2">
                      {user.is_active && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          活跃
                        </span>
                      )}
                      {user.is_approved && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          已审批
                        </span>
                      )}
                      {user.is_admin && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                          管理员
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end px-6 py-4 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            关闭
          </button>
        </div>
      </div>

      {/* 角色管理模态框 */}
      <RoleManagementModal
        user={user}
        isOpen={showRoleModal}
        onClose={() => setShowRoleModal(false)}
        onRoleUpdate={handleRoleUpdate}
      />
    </div>
  );
}
