"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AuthGuard,
  OperatorPanel,
  OperatorSectionHeader,
  OperatorShell,
  operatorButtonClass,
} from "@/components/shared";
import {
  EnvironmentCreateOverlay,
  EnvironmentList,
} from "@/components/features";
import { storyStructureAPI } from "@/utils/api/endpoints";
import type { Environment } from "@/utils/api/types";
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
    <OperatorShell
      title="环境资产"
      subtitle="为 IP、故事和剧集场景维护可复用环境"
      breadcrumb={["IP 中心", "环境资产"]}
    >
      <OperatorPanel className="mb-5">
        <OperatorSectionHeader
          title="环境资产"
          subtitle="可直接接入 IP 环境池，也可在剧集时间轴绑定到场景"
          action={
            <div className="flex gap-2">
              <button
                onClick={() => setShowCreateForm(true)}
                className={operatorButtonClass("primary")}
              >
                创建环境
              </button>
              <button
                onClick={() => void load()}
                className={operatorButtonClass("secondary")}
              >
                刷新
              </button>
            </div>
          }
        />
      </OperatorPanel>

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
    </OperatorShell>
  );
}

export default function EnvironmentsPage() {
  return (
    <AuthGuard>
      <EnvironmentsPageContent />
    </AuthGuard>
  );
}
