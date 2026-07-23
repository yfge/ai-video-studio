"use client";

import { useCallback, useEffect, useState } from "react";
import {
  OperatorPanel,
  OperatorState,
  OperatorTabs,
  StatusPill,
} from "@/components/shared";
import { narrativeMemoryAPI, virtualIPAPI } from "@/utils/api/endpoints";
import type {
  CharacterMemory,
  MemoryPromotion,
  VirtualIP,
} from "@/utils/api/types";
import { PromotionCandidateList } from "./PromotionCandidateList";
import { SharedMemoryList } from "./SharedMemoryList";

type Tab = "approved" | "candidates";

export function VirtualIPMemoryWorkspace({
  virtualIpId,
}: {
  virtualIpId: string;
}) {
  const [virtualIp, setVirtualIp] = useState<VirtualIP | null>(null);
  const [memories, setMemories] = useState<CharacterMemory[]>([]);
  const [promotions, setPromotions] = useState<MemoryPromotion[]>([]);
  const [tab, setTab] = useState<Tab>("approved");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    const [ip, shared, candidates] = await Promise.all([
      virtualIPAPI.getVirtualIP(virtualIpId),
      narrativeMemoryAPI.getSharedMemories(virtualIpId, true),
      narrativeMemoryAPI.getPromotions(virtualIpId),
    ]);
    if (!ip.success || !shared.success || !candidates.success) {
      setError(
        ip.error || shared.error || candidates.error || "公共记忆加载失败",
      );
    } else {
      setVirtualIp(ip.data || null);
      setMemories(shared.data || []);
      setPromotions(candidates.data || []);
      setError("");
    }
    setLoading(false);
  }, [virtualIpId]);
  useEffect(() => void load(), [load]);

  if (loading) return <OperatorState title="加载角色公共记忆…" />;
  if (error || !virtualIp)
    return <OperatorState title={error || "Virtual IP 不存在"} tone="red" />;
  return (
    <div className="space-y-4">
      <OperatorPanel className="p-5">
        <div className="flex flex-wrap justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold">
              {virtualIp.name} · 公共记忆
            </h1>
            <p className="mt-1 text-xs text-gray-500">
              来自 Story 的内容必须人工编辑或批准；不会自动污染其他 Story。
            </p>
          </div>
          <div className="flex gap-2">
            <StatusPill tone="green">
              已审批{" "}
              {memories.filter((item) => item.status === "approved").length}
            </StatusPill>
            <StatusPill tone="amber">
              待审核{" "}
              {promotions.filter((item) => item.status === "pending").length}
            </StatusPill>
          </div>
        </div>
        <p className="mt-3 text-xs text-gray-600" aria-live="polite">
          {message}
        </p>
      </OperatorPanel>
      <OperatorPanel>
        <div className="border-b border-gray-100 p-3">
          <OperatorTabs
            tabs={[
              { key: "approved", label: "已审批公共记忆" },
              { key: "candidates", label: "Story 提升候选" },
            ]}
            active={tab}
            onChange={setTab}
          />
        </div>
        {tab === "approved" ? (
          <SharedMemoryList
            items={memories}
            virtualIpId={virtualIpId}
            onChanged={load}
            setMessage={setMessage}
          />
        ) : (
          <PromotionCandidateList
            items={promotions}
            shared={memories}
            onChanged={load}
            setMessage={setMessage}
          />
        )}
      </OperatorPanel>
    </div>
  );
}
