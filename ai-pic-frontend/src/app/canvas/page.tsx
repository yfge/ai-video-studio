"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AuthGuard } from "@/components/shared";
import { ProductionCanvasBoard } from "@/components/features/canvas/ProductionCanvasBoard";

function CanvasPageContent() {
  const runId = useSearchParams().get("run_id");
  return (
    <AuthGuard>
      <ProductionCanvasBoard initialRunId={runId} />
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
