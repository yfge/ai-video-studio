"use client";

import { AuthGuard } from "@/components/shared";
import { WorkbenchDashboard } from "@/components/features";

export default function Home() {
  return (
    <AuthGuard>
      <WorkbenchDashboard />
    </AuthGuard>
  );
}
