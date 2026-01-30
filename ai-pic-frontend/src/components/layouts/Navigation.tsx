"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useState, useEffect } from "react";

interface NavigationProps {
  title?: string;
}

export default function Navigation({
  title = "AI短剧制作工作流平台",
}: NavigationProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    const userInfo = localStorage.getItem("user_info");

    if (token && userInfo) {
      setIsLoggedIn(true);
      try {
        const user = JSON.parse(userInfo);
        setUsername(user.username || "");
      } catch (e) {
        console.error("解析用户信息失败:", e);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_info");
    setIsLoggedIn(false);
    setUsername("");
    router.push("/");
  };

  const isActivePath = (path: string) => {
    return pathname === path || pathname.startsWith(path + "/");
  };

  const navItems = [
    { href: "/", label: "首页", icon: "🏠" },
    { href: "/virtual-ip", label: "虚拟IP", icon: "🎭" },
    { href: "/environments", label: "环境资产", icon: "🌆" },
    { href: "/stories", label: "故事创作", icon: "📚" },
    { href: "/tasks", label: "任务管理", icon: "✅" },
  ];

  return (
    <header className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          {/* Left side - Logo and Navigation */}
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-2">
              <span className="text-2xl">🎬</span>
              <h1 className="text-xl font-bold text-gray-900 hidden sm:block">
                {title}
              </h1>
            </Link>

            {/* Main Navigation */}
            {isLoggedIn && (
              <nav className="hidden md:flex space-x-1">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActivePath(item.href)
                        ? "bg-blue-100 text-blue-700 border-b-2 border-blue-600"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                    }`}
                  >
                    <span className="text-base">{item.icon}</span>
                    <span>{item.label}</span>
                  </Link>
                ))}
              </nav>
            )}
          </div>

          {/* Right side - User actions */}
          <div className="flex items-center space-x-4">
            {isLoggedIn ? (
              <>
                {/* User info */}
                <div className="hidden sm:flex items-center space-x-2 text-sm text-gray-600">
                  <span className="text-base">👤</span>
                  <span>欢迎, {username}</span>
                </div>

                {/* Mobile menu button */}
                <div className="md:hidden">
                  <button
                    type="button"
                    className="text-gray-600 hover:text-gray-900 p-2"
                    onClick={() => {
                      // You can implement mobile menu toggle here
                    }}
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 6h16M4 12h16M4 18h16"
                      />
                    </svg>
                  </button>
                </div>

                {/* Logout button */}
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  title="退出登录"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    />
                  </svg>
                  <span className="hidden sm:inline">退出</span>
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  登录
                </Link>
                <Link
                  href="/register"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  注册
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isLoggedIn && (
          <div className="md:hidden border-t border-gray-200 py-2">
            <nav className="flex flex-wrap gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActivePath(item.href)
                      ? "bg-blue-100 text-blue-700"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              ))}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
