"use client";

import { useParams } from "next/navigation";
import { AuthGuard, OperatorShell } from "@/components/shared";
import { StoryProductionDetail } from "@/components/features/stories/StoryProductionDetail";

function StoryDetailPageContent() {
  const params = useParams();
  const storyKey = params?.id?.toString() || "";

  return (
    <OperatorShell
      title="故事生产"
      subtitle="故事详情、剧集和生成准备"
      breadcrumb={["IP 中心", "故事生产", storyKey]}
    >
      <StoryProductionDetail storyKey={storyKey} />
    </OperatorShell>
  );
}

export default function StoryDetailPage() {
  return (
    <AuthGuard>
      <StoryDetailPageContent />
    </AuthGuard>
  );
}
