"use client";

import React from "react";
import { AdminLayout } from "@/components/layouts";

// 简单的图标组件
const CogIcon = ({ className = "" }) => (
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
      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
    />
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
    />
  </svg>
);

export default function AdminSettingsPage() {
  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* 页面头部 */}
        <div className="sm:flex sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">系统设置</h1>
            <p className="mt-2 text-sm text-gray-700">管理系统配置和偏好设置</p>
          </div>
        </div>

        {/* 设置功能占位 */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="text-center py-12">
              <CogIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                系统设置
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                系统配置功能正在开发中
              </p>
              <div className="mt-6">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {[
                    "用户注册设置",
                    "邮件通知配置",
                    "安全策略设置",
                    "系统日志配置",
                    "备份设置",
                    "性能监控",
                  ].map((setting) => (
                    <div
                      key={setting}
                      className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm hover:border-gray-400"
                    >
                      <div className="text-sm font-medium text-gray-900">
                        {setting}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">即将推出</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
