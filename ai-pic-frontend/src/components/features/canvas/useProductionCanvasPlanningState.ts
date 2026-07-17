import { useState } from "react";
import type { ProductionCanvasProductionContext } from "@/utils/api/types";
import {
  initialProductionCanvasPlanningSettings,
  type ProductionCanvasPlanningSettings,
} from "./productionCanvasPlanningSettings";

export function useProductionCanvasPlanningState() {
  const [promptValue, setPromptValue] = useState("");
  const [planningSettingsValue, setPlanningSettingsValue] =
    useState<ProductionCanvasPlanningSettings>(
      initialProductionCanvasPlanningSettings,
    );
  const [clarificationAnswers, setClarificationAnswers] = useState<
    Record<string, string>
  >({});
  const [productionContext, setProductionContext] =
    useState<ProductionCanvasProductionContext | null>(null);

  const resetPlanningContext = () => {
    setProductionContext(null);
    setClarificationAnswers({});
  };

  return {
    clarificationAnswers,
    onClarificationAnswer: (id: string, value: string) =>
      setClarificationAnswers((current) => ({ ...current, [id]: value })),
    planningSettings: planningSettingsValue,
    productionContext,
    prompt: promptValue,
    resetPlanningContext,
    setPlanningSettings: (patch: Partial<ProductionCanvasPlanningSettings>) => {
      setPlanningSettingsValue((current) => ({ ...current, ...patch }));
      resetPlanningContext();
    },
    setProductionContext,
    setPrompt: (value: string) => {
      setPromptValue(value);
      resetPlanningContext();
    },
  };
}
