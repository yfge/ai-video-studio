"use client";

import { useParams } from "next/navigation";
import { OperatorShell } from "@/components/shared";
import { StoryMemoryWorkspace } from "@/components/features/story-memory/StoryMemoryWorkspace";

export default function StoryMemoryPage() {
  const params = useParams();
  const storyId = String(params?.id || "");
  return (
    <OperatorShell
      title="叙事记忆"
      subtitle="Story 私有事件、角色记忆、成长轨迹与审核"
      breadcrumb={["IP 中心", "故事", "叙事记忆"]}
    >
      <StoryMemoryWorkspace storyId={storyId} />
    </OperatorShell>
  );
}
