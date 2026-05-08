"use client";

import { Suspense } from "react";
import { OperatorAdminShell, OperatorState } from "@/components/shared";
import { AdminUsersContent } from "./AdminUsersContent";

export default function AdminUsersPage() {
  return (
    <Suspense
      fallback={
        <OperatorAdminShell title="用户管理" subtitle="注册、审批和权限状态">
          <OperatorState title="加载用户列表..." />
        </OperatorAdminShell>
      }
    >
      <AdminUsersContent />
    </Suspense>
  );
}
