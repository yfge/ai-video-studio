"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/shared";
import { Navigation } from "@/components/layouts";
import {
  EnvironmentCreateOverlay,
  EnvironmentList,
} from "@/components/features";
import { storyStructureAPI, type Environment } from "@/utils/api";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";

function EnvironmentsPageContent() {
  const router = useRouter();
  const { showAlert } = useAlertModal();
  const [list, setList] = useState<Environment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await storyStructureAPI.listEnvironments();
      if (res.success && res.data) {
        setList(res.data);
      } else {
        showAlert({ message: res.error || "加载环境失败", variant: "error" });
      }
    } catch (e) {
      console.error(e);
      showAlert({ message: "加载环境失败", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [showAlert]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleDelete = (env: Environment) => {
    showAlert({
      title: "确认删除环境",
      message: "删除后引用该环境的场景将失去关联，确定删除吗？",
      variant: "warning",
      confirmText: "删除",
      onConfirm: async () => {
        try {
          const res = await storyStructureAPI.deleteEnvironment(env.id);
          if (res.success) {
            setList((prev) => prev.filter((item) => item.id !== env.id));
            showAlert({ message: "删除成功", variant: "success" });
          } else {
            showAlert({ message: res.error || "删除失败", variant: "error" });
          }
        } catch (e) {
          console.error(e);
          showAlert({ message: "删除失败", variant: "error" });
        }
      },
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation title="环境资产管理" />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">环境资产</h2>
            <p className="text-sm text-gray-500">
              列表仅展示概要信息，图片在详情内管理
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-lg hover:from-blue-700 hover:to-purple-700 shadow"
            >
              创建环境资产
            </button>
            <button
              onClick={() => void load()}
              className="border border-gray-300 px-4 py-2 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              刷新列表
            </button>
          </div>
        </div>

        <EnvironmentList
          loading={loading}
          list={list}
          onRefresh={() => void load()}
          onManage={(env) =>
            router.push(`/environments/${env.business_id || env.id}`)
          }
          onDelete={handleDelete}
        />

        <EnvironmentCreateOverlay
          open={showCreateForm}
          onClose={() => setShowCreateForm(false)}
          onCreated={(env) => setList((prev) => [env, ...prev])}
        />
      </main>
    </div>
  );
}

export default function EnvironmentsPage() {
  return (
    <AuthGuard>
      <EnvironmentsPageContent />
    </AuthGuard>
  );
}
