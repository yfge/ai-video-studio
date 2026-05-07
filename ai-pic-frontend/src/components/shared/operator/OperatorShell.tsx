"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { operatorButtonClass, operatorInputClass } from "./OperatorPrimitives";

const navItems = [
  { href: "/", label: "工作台", mark: "W" },
  { href: "/virtual-ip", label: "IP 项目", mark: "I" },
  { href: "/stories", label: "故事生产", mark: "S" },
  { href: "/tasks", label: "任务", mark: "T" },
  { href: "/environments", label: "环境迁移", mark: "E" },
];

export function OperatorShell({
  children,
  title,
  subtitle,
}: {
  children: ReactNode;
  title?: string;
  subtitle?: string;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [username, setUsername] = useState("operator");

  useEffect(() => {
    const raw = localStorage.getItem("user_info");
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as { username?: string };
      setUsername(parsed.username || "operator");
    } catch {
      setUsername("operator");
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_info");
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-[#f5f6f8] text-gray-950">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-60 border-r border-gray-200 bg-white lg:block">
        <div className="flex h-16 items-center border-b border-gray-200 px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gray-950 text-sm font-semibold text-white">
            AI
          </div>
          <div className="ml-3">
            <div className="text-sm font-semibold">短剧制作台</div>
            <div className="text-xs text-gray-500">Operator Console</div>
          </div>
        </div>
        <nav className="space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "border-blue-100 bg-blue-50 text-blue-700"
                    : "border-transparent text-gray-600 hover:border-gray-100 hover:bg-gray-50 hover:text-gray-950"
                }`}
              >
                <span className="flex h-6 w-6 items-center justify-center rounded-md border border-current/20 text-[11px]">
                  {item.mark}
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className="lg:pl-60">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-gray-200 bg-white/95 px-4 backdrop-blur sm:px-6">
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-gray-950">
              {title || "生产工作台"}
            </div>
            {subtitle ? (
              <div className="truncate text-xs text-gray-500">{subtitle}</div>
            ) : null}
          </div>
          <div className="flex items-center gap-3">
            <div className={operatorInputClass("hidden w-44 text-gray-500 md:block lg:w-56")}>
              搜索 IP、故事、剧集
            </div>
            <span className="rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-600">
              {username}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className={operatorButtonClass("secondary")}
            >
              退出
            </button>
          </div>
        </header>
        <main className="px-4 py-5 sm:px-6">{children}</main>
      </div>
    </div>
  );
}
