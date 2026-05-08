"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { adminAPI, authAPI } from "@/utils/api/endpoints";
import type { User, UserStatsResponse } from "@/utils/api/types";
import { hasPendingApprovals, isAdmin } from "@/utils/auth";
import { OperatorShell } from "./OperatorShell";
import { OperatorState, operatorButtonClass } from "./OperatorPrimitives";

export function OperatorAdminShell({
  children,
  title,
  subtitle,
}: {
  children: ReactNode;
  title: string;
  subtitle?: string;
}) {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [stats, setStats] = useState<UserStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userResponse = await authAPI.getCurrentUser();
        if (!userResponse.success || !userResponse.data) {
          router.push("/login");
          return;
        }
        if (!isAdmin(userResponse.data)) {
          router.push("/");
          return;
        }
        setCurrentUser(userResponse.data);
        const statsResponse = await adminAPI.getUserStats();
        if (statsResponse.success && statsResponse.data) {
          setStats(statsResponse.data);
        }
      } finally {
        setLoading(false);
      }
    };
    void checkAuth();
  }, [router]);

  const handleLogout = async () => {
    await authAPI.logout();
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_info");
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f5f6f8]">
        <OperatorState title="加载管理控制台..." />
      </div>
    );
  }

  if (!currentUser) return null;

  return (
    <OperatorShell
      mode="admin"
      title={title}
      subtitle={subtitle}
      breadcrumb={["IP 中心", "管理控制台"]}
      userLabel={currentUser.username}
      onLogout={() => void handleLogout()}
      rightSlot={
        hasPendingApprovals(stats) ? (
          <a
            href="/admin/users?status=pending"
            className={operatorButtonClass("secondary")}
          >
            待审批 {stats?.pending_approval}
          </a>
        ) : undefined
      }
    >
      {children}
    </OperatorShell>
  );
}
