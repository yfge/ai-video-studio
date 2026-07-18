"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AuthGuard } from "@/components/shared";
import { ProductionCanvasHistory } from "@/components/features/canvas/ProductionCanvasHistory";
import { ProductionCanvasShell } from "@/components/features/canvas/ProductionCanvasShell";

function CanvasPageContent() {
  const searchParams = useSearchParams();
  const runId = searchParams.get("run_id");
  const newBlankCanvas = searchParams.get("new") === "1";
  return (
    <AuthGuard>
      {runId || newBlankCanvas ? (
        <ProductionCanvasShell
          blank={newBlankCanvas && !runId}
          initialRunId={runId}
        />
      ) : (
        <ProductionCanvasHistory />
      )}
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
