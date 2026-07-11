import type { ProductionCanvasNode } from "./productionCanvasModel";

function formatOutputValue(value: unknown) {
  if (Array.isArray(value)) return value.join(", ");
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function ProductionCanvasDiagnostics({
  node,
}: {
  node: ProductionCanvasNode;
}) {
  const outputs = Object.entries(node.outputs || {}).filter(([, value]) => {
    if (Array.isArray(value)) return value.length > 0;
    return value !== null && value !== undefined && String(value).trim() !== "";
  });
  if (!node.reuseTargets?.length && !outputs.length) return null;

  return (
    <details className="mt-4 border-t border-gray-100 pt-3">
      <summary className="cursor-pointer text-xs font-semibold text-gray-700">
        高级诊断
      </summary>
      {node.reuseTargets?.length ? (
        <div className="mt-3">
          <div className="text-xs font-semibold text-gray-700">后台复用</div>
          <div className="mt-2 space-y-2">
            {node.reuseTargets.map((target) => (
              <div
                key={`${target.kind}-${target.target}`}
                className="rounded-md bg-gray-50 px-2 py-1.5"
              >
                <div className="text-xs font-medium text-gray-800">
                  {target.label}
                </div>
                <div className="mt-0.5 break-all text-[11px] leading-4 text-gray-500">
                  {target.target}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {outputs.length ? (
        <div className="mt-3">
          <div className="text-xs font-semibold text-gray-700">执行输出</div>
          <div className="mt-2 space-y-1 text-[11px] leading-4 text-gray-500">
            {outputs.map(([key, value]) => (
              <div key={key}>
                {key}: {formatOutputValue(value)}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </details>
  );
}
