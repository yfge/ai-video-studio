"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AuthGuard } from "@/components/shared";
import { ProductionCanvasShell } from "@/components/features/canvas/ProductionCanvasShell";

function CanvasPageContent() {
  const runId = useSearchParams().get("run_id");
  return (
    <AuthGuard>
      <ProductionCanvasShell initialRunId={runId} />
    </AuthGuard>
  );
}

export default function CanvasPage() {
  return (
    <Suspense fallback={null}>
      <CanvasPageContent />
    </Suspense>
  );
}
