"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  OperatorAdminShell,
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import { adminAPI } from "@/utils/api/endpoints";
import type { UserStatsResponse } from "@/utils/api/types";

const statItems = (stats: UserStatsResponse) => [
  { label: "总用户数", value: stats.total_users, href: "/admin/users" },
  { label: "活跃用户", value: stats.active_users, href: "/admin/users?status=approved" },
  { label: "待审批", value: stats.pending_approval, href: "/admin/users?status=pending", tone: "amber" as const },
  { label: "暂停用户", value: stats.suspended_users, href: "/admin/users?status=suspended", tone: "red" as const },
  { label: "管理员", value: stats.admin_users, href: "/admin/users?role=admin", tone: "blue" as const },
  { label: "最近注册", value: stats.recent_registrations, tone: "green" as const },
];

export default function AdminStatsPage() {
  const [stats, setStats] = useState<UserStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await adminAPI.getUserStats();
      if (response.success && response.data) setStats(response.data);
      else setError(response.error || "获取统计数据失败");
    } catch (err) {
      console.error("加载统计数据失败:", err);
      setError("网络错误，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadStats();
  }, []);

  return (
    <OperatorAdminShell title="统计数据" subtitle="用户和审批运行概览">
      <div className="space-y-4">
        <OperatorPanel>
          <OperatorSectionHeader
            title="用户统计"
            subtitle="账号、审批和权限分布"
            action={
              <button
                type="button"
                onClick={() => void loadStats()}
                className={operatorButtonClass("secondary")}
              >
                刷新
              </button>
            }
          />
          {loading ? <div className="p-4"><OperatorState title="加载统计数据..." /></div> : null}
          {error ? <div className="p-4"><OperatorState title={error} tone="red" /></div> : null}
          {stats ? (
            <div className="grid gap-3 p-4 md:grid-cols-3">
              {statItems(stats).map((item) => {
                const card = (
                  <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-xs text-gray-500">{item.label}</span>
                      <StatusPill tone={item.tone || "gray"}>{item.value}</StatusPill>
                    </div>
                    <div className="mt-3 text-2xl font-semibold text-gray-950">
                      {item.value.toLocaleString()}
                    </div>
                  </div>
                );
                return item.href ? (
                  <Link key={item.label} href={item.href} className="block hover:opacity-90">
                    {card}
                  </Link>
                ) : (
                  <div key={item.label}>{card}</div>
                );
              })}
            </div>
          ) : null}
        </OperatorPanel>
        {stats ? (
          <OperatorPanel>
            <OperatorSectionHeader title="快速操作" subtitle="从统计跳转到用户处理面" />
            <div className="grid gap-3 p-4 md:grid-cols-3">
              <QuickLink href="/admin/users?status=pending" label="处理待审批" detail={`${stats.pending_approval} 个待处理`} />
              <QuickLink href="/admin/users" label="管理用户" detail="查看全部账号" />
              <QuickLink href="/admin/users?role=admin" label="管理员权限" detail={`${stats.admin_users} 个管理员账号`} />
            </div>
          </OperatorPanel>
        ) : null}
      </div>
    </OperatorAdminShell>
  );
}

function QuickLink({
  href,
  label,
  detail,
}: {
  href: string;
  label: string;
  detail: string;
}) {
  return (
    <Link
      href={href}
      className="rounded-md border border-gray-200 bg-white p-4 text-sm hover:border-gray-300 hover:bg-gray-50"
    >
      <div className="font-medium text-gray-950">{label}</div>
      <div className="mt-1 text-xs text-gray-500">{detail}</div>
    </Link>
  );
}
