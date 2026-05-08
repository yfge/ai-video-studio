"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  UserApprovalModal,
  UserDetailsModal,
} from "@/components/shared/modals";
import {
  OperatorAdminShell,
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  operatorButtonClass,
  operatorInputClass,
  operatorSelectClass,
} from "@/components/shared";
import { adminAPI } from "@/utils/api/endpoints";
import type { AdminUser, UserListResponse } from "@/utils/api/types";
import { AdminUserPagination, AdminUserRow } from "./AdminUsersRows";

type UserFilters = {
  page: number;
  size: number;
  status_filter?: string;
  role_filter?: string;
  search?: string;
};

export function AdminUsersContent() {
  const searchParams = useSearchParams();
  const [userList, setUserList] = useState<UserListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingUsers, setProcessingUsers] = useState<Set<number>>(new Set());
  const [detailUser, setDetailUser] = useState<AdminUser | null>(null);
  const [approvalUser, setApprovalUser] = useState<AdminUser | null>(null);
  const [filters, setFilters] = useState<UserFilters>({
    page: 1,
    size: 20,
    status_filter: searchParams.get("status") || undefined,
    role_filter: searchParams.get("role") || undefined,
  });

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await adminAPI.getUsers(filters);
      if (response.success && response.data) setUserList(response.data);
      else setError(response.error || "获取用户列表失败");
    } catch (err) {
      console.error("加载用户列表失败:", err);
      setError("网络错误，请稍后重试");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  const verifyEmail = async (user: AdminUser) => {
    setProcessingUsers((prev) => new Set(prev).add(user.id));
    try {
      const response = await adminAPI.updateUserAdmin(user.id, {
        email_verified: true,
      });
      if (response.success) await loadUsers();
      else setError(response.error || "操作失败");
    } finally {
      setProcessingUsers((prev) => {
        const next = new Set(prev);
        next.delete(user.id);
        return next;
      });
    }
  };

  const updateUser = (updated: AdminUser) => {
    setUserList((prev) =>
      prev
        ? { ...prev, users: prev.users.map((user) => (user.id === updated.id ? updated : user)) }
        : prev,
    );
    setDetailUser((prev) => (prev?.id === updated.id ? updated : prev));
  };

  return (
    <OperatorAdminShell title="用户管理" subtitle="注册、审批和权限状态">
      <div className="space-y-4">
        <OperatorPanel>
          <OperatorSectionHeader
            title="筛选"
            subtitle={userList ? `共 ${userList.total} 个用户` : "加载用户数据"}
            action={
              <button
                type="button"
                onClick={() => void loadUsers()}
                className={operatorButtonClass("secondary")}
              >
                刷新
              </button>
            }
          />
          <div className="grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_160px_160px]">
            <input
              value={filters.search || ""}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, page: 1, search: event.target.value || undefined }))
              }
              className={operatorInputClass("w-full")}
              placeholder="搜索用户名、邮箱或姓名"
            />
            <select
              value={filters.status_filter || ""}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, page: 1, status_filter: event.target.value || undefined }))
              }
              className={operatorSelectClass("w-full")}
            >
              <option value="">所有状态</option>
              <option value="pending">待审批</option>
              <option value="approved">已审批</option>
              <option value="suspended">已暂停</option>
              <option value="locked">已锁定</option>
            </select>
            <select
              value={filters.role_filter || ""}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, page: 1, role_filter: event.target.value || undefined }))
              }
              className={operatorSelectClass("w-full")}
            >
              <option value="">所有角色</option>
              <option value="admin">管理员</option>
              <option value="superuser">超级用户</option>
              <option value="user">普通用户</option>
            </select>
          </div>
        </OperatorPanel>

        {error ? <OperatorState title={error} tone="red" /> : null}
        {loading && !userList ? <OperatorState title="加载用户列表..." /> : null}

        <OperatorPanel>
          <OperatorSectionHeader title="用户列表" subtitle="审批、邮箱验证和详情管理" />
          <div className="divide-y divide-gray-100">
            {userList?.users.length ? (
              userList.users.map((user) => (
                <AdminUserRow
                  key={user.id}
                  user={user}
                  processing={processingUsers.has(user.id)}
                  onApprove={() => setApprovalUser(user)}
                  onVerifyEmail={() => void verifyEmail(user)}
                  onDetails={() => setDetailUser(user)}
                />
              ))
            ) : (
              <div className="p-6 text-sm text-gray-500">没有符合条件的用户。</div>
            )}
          </div>
          {userList && userList.pages > 1 ? (
            <AdminUserPagination
              page={filters.page}
              pages={userList.pages}
              total={userList.total}
              onPage={(page) => setFilters((prev) => ({ ...prev, page }))}
            />
          ) : null}
        </OperatorPanel>
      </div>

      <UserDetailsModal
        user={detailUser}
        isOpen={Boolean(detailUser)}
        onClose={() => setDetailUser(null)}
        onUserUpdate={updateUser}
      />
      <UserApprovalModal
        user={approvalUser}
        isOpen={Boolean(approvalUser)}
        onClose={() => setApprovalUser(null)}
        onApprovalComplete={(user) => updateUser(user)}
      />
    </OperatorAdminShell>
  );
}
