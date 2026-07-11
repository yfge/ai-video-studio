import { OperatorPanel } from "@/components/shared";

export function ProductionCanvasInfoPanels() {
  return (
    <div className="grid gap-3 lg:grid-cols-3">
      <OperatorPanel className="p-4">
        <div className="text-xs font-semibold text-gray-950">引用对象</div>
        <p className="mt-2 text-xs leading-5 text-gray-600">
          IP / Story / Episode / Task / Artifact
        </p>
      </OperatorPanel>
      <OperatorPanel className="p-4">
        <div className="text-xs font-semibold text-gray-950">执行层</div>
        <p className="mt-2 text-xs leading-5 text-gray-600">
          Existing API / Skill Invocation / Artifact Run
        </p>
      </OperatorPanel>
      <OperatorPanel className="p-4">
        <div className="text-xs font-semibold text-gray-950">证据出口</div>
        <p className="mt-2 text-xs leading-5 text-gray-600">
          Quality Gate / Cost / Failure / Provider Lineage
        </p>
      </OperatorPanel>
    </div>
  );
}
