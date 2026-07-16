export type ProductionCanvasPlannerMode =
  | "autonomous"
  | "deterministic_fallback";

export interface ProductionCanvasPlannerEvidence {
  mode: ProductionCanvasPlannerMode;
  version: string;
  objective: string;
  selected_skills: string[];
  rationale?: string[];
  assumptions?: string[];
  warnings?: string[];
  validation_errors?: string[];
  provider?: string | null;
  model?: string | null;
  repair_count?: number;
  fallback_reason?: string | null;
}
