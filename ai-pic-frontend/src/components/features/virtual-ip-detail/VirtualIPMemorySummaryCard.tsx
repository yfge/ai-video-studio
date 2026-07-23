"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  OperatorPanel,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import { narrativeMemoryAPI } from "@/utils/api/endpoints";

export function VirtualIPMemorySummaryCard({
  virtualIpId,
}: {
  virtualIpId: string;
}) {
  const [counts, setCounts] = useState<{
    memories: number;
    pending: number;
    branch: string;
    lastApproval?: string;
  } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    void Promise.all([
      narrativeMemoryAPI.getSharedMemories(virtualIpId),
      narrativeMemoryAPI.getPromotions(virtualIpId),
    ]).then(([memories, promotions]) => {
      if (!active) return;
      if (!memories.success || !promotions.success) {
        setError(memories.error || promotions.error || "公共记忆加载失败");
        return;
      }
      const approved = (promotions.data || [])
        .filter((item) => item.approved_at)
        .sort((a, b) =>
          String(b.approved_at).localeCompare(String(a.approved_at)),
        )[0];
      setCounts({
        memories: memories.data?.length || 0,
        pending: (promotions.data || []).filter(
          (item) => item.status === "pending",
        ).length,
        branch: memories.data?.[0]?.canon_branch_id || "main",
        lastApproval: approved?.approved_at || undefined,
      });
    });
    return () => {
      active = false;
    };
  }, [virtualIpId]);
  return (
    <OperatorPanel className="p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold">角色公共记忆</h2>
          <p className="mt-1 text-xs text-gray-500">
            只影响新 Story；不会自动修改在制 Story 的冻结基线。
          </p>
        </div>
        <Link
          href={`/virtual-ip/${virtualIpId}/memories`}
          className={operatorButtonClass("secondary")}
        >
          管理公共记忆
        </Link>
      </div>
      {counts ? (
        <div className="mt-3 flex gap-2">
          <StatusPill tone="green">已审批 {counts.memories}</StatusPill>
          <StatusPill tone={counts.pending ? "amber" : "gray"}>
            待人工提炼 {counts.pending}
          </StatusPill>
          <StatusPill tone="blue">branch {counts.branch}</StatusPill>
          {counts.lastApproval ? (
            <StatusPill tone="gray">
              最近审批 {new Date(counts.lastApproval).toLocaleDateString()}
            </StatusPill>
          ) : null}
        </div>
      ) : (
        <p
          className={`mt-3 text-xs ${error ? "text-red-700" : "text-gray-500"}`}
          role={error ? "alert" : "status"}
        >
          {error || "加载公共记忆摘要…"}
        </p>
      )}
    </OperatorPanel>
  );
}
