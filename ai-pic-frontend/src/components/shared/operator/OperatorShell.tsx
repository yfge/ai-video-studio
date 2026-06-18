"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { operatorButtonClass, operatorInputClass } from "./OperatorPrimitives";
import {
  OperatorShellNavIcon,
  type OperatorNavIconName,
} from "./OperatorShellNavIcon";
import {
  operatorShellActionsClass,
  operatorShellHeaderClass,
  operatorShellLogoutButtonClass,
  operatorShellMainClass,
  operatorShellSidebarHeaderClass,
  operatorShellTitleClass,
  operatorShellUserClass,
} from "./OperatorShellLayout";

export type OperatorNavItem = {
  href: string;
  label: string;
  icon: OperatorNavIconName;
};
type OperatorShellMode = "production" | "admin";

export const productionNavItems: OperatorNavItem[] = [
  { href: "/", label: "工作台", icon: "workspace" },
  { href: "/canvas", label: "创作画布", icon: "canvas" },
  { href: "/virtual-ip", label: "IP 项目", icon: "ip" },
  { href: "/stories", label: "故事生产", icon: "stories" },
  { href: "/environments", label: "环境资产", icon: "environments" },
  { href: "/tasks", label: "任务", icon: "tasks" },
];

const adminNavItems: OperatorNavItem[] = [
  { href: "/admin/users", label: "用户管理", icon: "users" },
  { href: "/admin/stats", label: "统计数据", icon: "stats" },
  { href: "/admin/settings", label: "系统设置", icon: "settings" },
];

export function OperatorShell({
  children,
  title,
  subtitle,
  breadcrumb,
  mode = "production",
  compactNavigation = false,
  showGlobalSearch = true,
  rightSlot,
  userLabel,
  onLogout,
}: {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  breadcrumb?: string[];
  mode?: OperatorShellMode;
  compactNavigation?: boolean;
  showGlobalSearch?: boolean;
  rightSlot?: ReactNode;
  userLabel?: string;
  onLogout?: () => void;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [username, setUsername] = useState("operator");
  const navItems = mode === "admin" ? adminNavItems : productionNavItems;
  const shellTitle = mode === "admin" ? "管理控制台" : "短剧制作台";
  const shellSubtitle = mode === "admin" ? "Admin Console" : "Operator Console";

  useEffect(() => {
    if (userLabel) {
      setUsername(userLabel);
      return;
    }
    const raw = localStorage.getItem("user_info");
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as { username?: string };
      setUsername(parsed.username || "operator");
    } catch {
      setUsername("operator");
    }
  }, [userLabel]);

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
      return;
    }
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_info");
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-[#f5f6f8] text-gray-950">
      <aside
        className={`fixed inset-y-0 left-0 z-40 hidden border-r border-gray-200 bg-white lg:block ${
          compactNavigation ? "w-14" : "w-52"
        }`}
      >
        <div className={operatorShellSidebarHeaderClass(compactNavigation)}>
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gray-950 text-xs font-semibold text-white">
            AI
          </div>
          {!compactNavigation ? (
            <div className="ml-2 min-w-0">
              <div className="text-sm font-semibold">{shellTitle}</div>
              <div className="text-xs text-gray-500">{shellSubtitle}</div>
            </div>
          ) : null}
        </div>
        <nav
          className={
            compactNavigation ? "space-y-1 px-2 py-3" : "space-y-1 px-2.5 py-3"
          }
        >
          {navItems.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                title={item.label}
                className={`flex h-9 items-center rounded-md border text-sm font-medium transition-colors ${
                  compactNavigation ? "justify-center px-0" : "gap-2.5 px-2.5"
                } ${
                  active
                    ? "border-blue-100 bg-blue-50 text-blue-700"
                    : "border-transparent text-gray-600 hover:border-gray-100 hover:bg-gray-50 hover:text-gray-950"
                }`}
              >
                <span className="flex h-6 w-6 items-center justify-center rounded-md border border-current/20">
                  <OperatorShellNavIcon name={item.icon} className="h-4 w-4" />
                </span>
                <span className={compactNavigation ? "sr-only" : undefined}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className={compactNavigation ? "lg:pl-14" : "lg:pl-52"}>
        <header className={operatorShellHeaderClass(compactNavigation)}>
          <div className={operatorShellTitleClass(compactNavigation)}>
            <div className="truncate text-sm font-semibold text-gray-950">
              {breadcrumb?.length
                ? breadcrumb.join(" / ")
                : title || "生产工作台"}
            </div>
            {title || subtitle ? (
              <div className="truncate text-xs text-gray-500">
                {breadcrumb?.length && title ? `${title} · ` : ""}
                {subtitle || ""}
              </div>
            ) : null}
          </div>
          <div className={operatorShellActionsClass(compactNavigation)}>
            {rightSlot ||
              (showGlobalSearch ? (
                <div
                  className={operatorInputClass(
                    "hidden w-44 text-gray-500 md:block lg:w-56",
                  )}
                >
                  {mode === "admin"
                    ? "搜索用户、权限、审计"
                    : "搜索 IP、故事、剧集"}
                </div>
              ) : null)}
            <span className={operatorShellUserClass(compactNavigation)}>
              {username}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className={operatorButtonClass(
                "secondary",
                operatorShellLogoutButtonClass(compactNavigation),
              )}
            >
              退出
            </button>
          </div>
        </header>
        <main className={operatorShellMainClass(compactNavigation)}>
          {children}
        </main>
      </div>
    </div>
  );
}
