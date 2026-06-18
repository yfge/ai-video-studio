"use client";

import { AuthGuard } from "@/components/shared";
import { ProductionCanvasBoard } from "@/components/features/canvas/ProductionCanvasBoard";

export default function CanvasPage() {
  return (
    <AuthGuard>
      <ProductionCanvasBoard />
    </AuthGuard>
  );
}
