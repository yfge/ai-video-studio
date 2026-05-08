"use client";

import {
  OperatorAdminShell,
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
} from "@/components/shared";

export default function AdminSettingsPage() {
  return (
    <OperatorAdminShell title="系统设置" subtitle="运行策略和系统配置">
      <div className="space-y-6">
        <OperatorPanel>
          <OperatorSectionHeader title="系统设置" subtitle="配置项占位和后续接入入口" />
          <div className="p-4">
            <OperatorState title="系统配置功能正在开发中" detail="当前页面保留为管理配置入口。" />
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
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
                  className="rounded-md border border-gray-200 bg-gray-50 px-4 py-3"
                >
                  <div className="text-sm font-medium text-gray-900">
                    {setting}
                  </div>
                  <div className="mt-1 text-xs text-gray-500">待接入</div>
                </div>
              ))}
            </div>
          </div>
        </OperatorPanel>
      </div>
    </OperatorAdminShell>
  );
}
