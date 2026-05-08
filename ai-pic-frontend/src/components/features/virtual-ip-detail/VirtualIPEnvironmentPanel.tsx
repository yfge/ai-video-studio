"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  StatusPill,
  operatorButtonClass,
  operatorInputClass,
  operatorSelectClass,
} from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals";
import { storyStructureAPI, virtualIPAPI } from "@/utils/api/endpoints";
import type {
  Environment,
  VirtualIP,
  VirtualIPEnvironmentLink,
} from "@/utils/api/types";
import { availableEnvironmentOptions } from "./virtualIPEnvironmentModel";

interface VirtualIPEnvironmentPanelProps {
  virtualIP: VirtualIP;
  onLinkedCountChange?: (count: number) => void;
}

export function VirtualIPEnvironmentPanel({
  virtualIP,
  onLinkedCountChange,
}: VirtualIPEnvironmentPanelProps) {
  const { showAlert } = useAlertModal();
  const ipKey = virtualIP.business_id || virtualIP.id;
  const [links, setLinks] = useState<VirtualIPEnvironmentLink[]>([]);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [loading, setLoading] = useState(true);
  const [linking, setLinking] = useState(false);
  const [selectedEnvId, setSelectedEnvId] = useState("");
  const [quickName, setQuickName] = useState("");
  const [quickCategory, setQuickCategory] = useState("indoor");

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [linksRes, envRes] = await Promise.all([
        virtualIPAPI.listVirtualIPEnvironments(ipKey),
        storyStructureAPI.listEnvironments(),
      ]);
      if (linksRes.success && linksRes.data) {
        setLinks(linksRes.data);
        onLinkedCountChange?.(linksRes.data.length);
      } else {
        showAlert({ message: linksRes.error || "加载 IP 环境失败", variant: "error" });
      }
      setEnvironments(envRes.success && envRes.data ? envRes.data : []);
    } finally {
      setLoading(false);
    }
  }, [ipKey, onLinkedCountChange, showAlert]);

  useEffect(() => {
    void load();
  }, [load]);

  const availableEnvironments = useMemo(
    () => availableEnvironmentOptions(environments, links),
    [environments, links],
  );

  const refreshLinks = (next: VirtualIPEnvironmentLink[]) => {
    setLinks(next);
    onLinkedCountChange?.(next.length);
  };

  const handleLinkExisting = async () => {
    const environmentId = Number(selectedEnvId);
    if (!environmentId) return;
    setLinking(true);
    try {
      const res = await virtualIPAPI.linkVirtualIPEnvironment(ipKey, {
        environment_id: environmentId,
      });
      if (res.success && res.data) {
        refreshLinks([...links.filter((item) => item.environment_id !== environmentId), res.data]);
        setSelectedEnvId("");
        showAlert({ message: "环境已接入 IP", variant: "success" });
      } else {
        showAlert({ message: res.error || "关联环境失败", variant: "error" });
      }
    } finally {
      setLinking(false);
    }
  };

  const handleQuickCreate = async () => {
    const name = quickName.trim();
    if (!name) return;
    setLinking(true);
    try {
      const created = await storyStructureAPI.createEnvironment({
        name,
        category: quickCategory,
      });
      if (!created.success || !created.data) {
        showAlert({ message: created.error || "创建环境失败", variant: "error" });
        return;
      }
      const linked = await virtualIPAPI.linkVirtualIPEnvironment(ipKey, {
        environment_id: created.data.id,
      });
      if (linked.success && linked.data) {
        refreshLinks([linked.data, ...links]);
        setEnvironments((prev) => [created.data!, ...prev]);
        setQuickName("");
        showAlert({ message: "环境已创建并接入 IP", variant: "success" });
      } else {
        showAlert({ message: linked.error || "环境创建成功，关联失败", variant: "error" });
      }
    } finally {
      setLinking(false);
    }
  };

  const handleUnlink = async (link: VirtualIPEnvironmentLink) => {
    const res = await virtualIPAPI.unlinkVirtualIPEnvironment(ipKey, link.environment_id);
    if (res.success) {
      refreshLinks(links.filter((item) => item.id !== link.id));
      showAlert({ message: "已从 IP 移除环境关联", variant: "success" });
    } else {
      showAlert({ message: res.error || "移除关联失败", variant: "error" });
    }
  };

  return (
    <OperatorPanel id="ip-environments">
      <OperatorSectionHeader
        title="环境资产"
        subtitle="接入当前 IP 的可复用场景、地点和背景图池"
        action={<StatusPill tone={links.length ? "green" : "amber"}>{links.length} 个</StatusPill>}
      />
      <div className="space-y-4 p-4">
        {loading ? (
          <OperatorState title="加载 IP 环境资产..." />
        ) : links.length ? (
          <div className="grid gap-3 md:grid-cols-2">
            {links.map((link) => (
              <div key={link.id} className="rounded-lg border border-gray-200 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-gray-950">
                      {link.environment.name}
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      {link.environment.category || "未分类"} · {link.usage_type}
                    </div>
                  </div>
                  <StatusPill tone={link.is_default ? "blue" : "gray"}>
                    {link.is_default ? "默认" : "已接入"}
                  </StatusPill>
                </div>
                {link.environment.description ? (
                  <p className="mt-2 line-clamp-2 text-xs text-gray-600">
                    {link.environment.description}
                  </p>
                ) : null}
                <div className="mt-3 flex gap-2">
                  <Link
                    href={`/environments/${link.environment.business_id || link.environment_id}`}
                    className={operatorButtonClass("secondary")}
                  >
                    管理图片
                  </Link>
                  <button
                    type="button"
                    onClick={() => void handleUnlink(link)}
                    className={operatorButtonClass("ghost")}
                  >
                    移除关联
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <OperatorState
            tone="amber"
            title="环境待接入"
            detail="关联环境后，故事、Timeline 和分镜会优先使用当前 IP 的环境池。"
          />
        )}

        <div className="grid gap-3 border-t border-gray-100 pt-4 lg:grid-cols-2">
          <div className="flex gap-2">
            <select
              value={selectedEnvId}
              onChange={(event) => setSelectedEnvId(event.target.value)}
              className={operatorSelectClass("min-w-0 flex-1")}
            >
              <option value="">选择已有环境</option>
              {availableEnvironments.map((env) => (
                <option key={env.id} value={env.id}>
                  {env.name}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={!selectedEnvId || linking}
              onClick={() => void handleLinkExisting()}
              className={operatorButtonClass("primary")}
            >
              接入
            </button>
          </div>
          <div className="flex gap-2">
            <input
              value={quickName}
              onChange={(event) => setQuickName(event.target.value)}
              placeholder="新环境名称"
              className={operatorInputClass("min-w-0 flex-1")}
            />
            <select
              value={quickCategory}
              onChange={(event) => setQuickCategory(event.target.value)}
              className={operatorSelectClass("w-24")}
            >
              <option value="indoor">室内</option>
              <option value="outdoor">室外</option>
              <option value="other">其他</option>
            </select>
            <button
              type="button"
              disabled={!quickName.trim() || linking}
              onClick={() => void handleQuickCreate()}
              className={operatorButtonClass("secondary")}
            >
              创建并接入
            </button>
          </div>
        </div>
      </div>
    </OperatorPanel>
  );
}
