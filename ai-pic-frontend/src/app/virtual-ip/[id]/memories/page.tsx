"use client";

import { useParams } from "next/navigation";
import { OperatorShell } from "@/components/shared";
import { VirtualIPMemoryWorkspace } from "@/components/features/virtual-ip-memory/VirtualIPMemoryWorkspace";

export default function VirtualIPMemoriesPage() {
  const params = useParams();
  return (
    <OperatorShell
      title="角色公共记忆"
      subtitle="人工提炼、版本化和 Story 基线隔离"
      breadcrumb={["IP 中心", "Virtual IP", "公共记忆"]}
    >
      <VirtualIPMemoryWorkspace virtualIpId={String(params?.id || "")} />
    </OperatorShell>
  );
}
