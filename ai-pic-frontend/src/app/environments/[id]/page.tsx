"use client";

import { AuthGuard } from "@/components/shared";
import { EnvironmentDetailView } from "@/components/features/environments/EnvironmentDetailView";

export default function EnvironmentDetailPage() {
  return (
    <AuthGuard>
      <EnvironmentDetailView />
    </AuthGuard>
  );
}
