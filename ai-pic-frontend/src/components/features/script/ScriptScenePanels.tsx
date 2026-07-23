import { OperatorState } from "@/components/shared";
import type {
  NormalizedScene,
  NormalizedShot,
  SceneBeat,
} from "@/utils/api/types";

export function ScriptContentBlock({
  title,
  items,
  empty,
}: {
  title: string;
  items: Array<string | { character?: string; content?: string }>;
  empty: string;
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
      <div className="mt-2 space-y-2">
        {items.length ? (
          items.map((item, index) => (
            <div
              key={index}
              className="rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700"
            >
              {typeof item === "string"
                ? item
                : `${item.character || "角色"}：${item.content || ""}`}
            </div>
          ))
        ) : (
          <div className="rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-500">
            {empty}
          </div>
        )}
      </div>
    </div>
  );
}

export function ScriptStructureSummary({
  scene,
  beats,
  shots,
}: {
  scene?: NormalizedScene;
  beats?: SceneBeat[];
  shots?: NormalizedShot[];
}) {
  if (!scene) {
    return <OperatorState title="未匹配规范化场景" tone="amber" />;
  }
  return (
    <div className="space-y-3">
      <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
        <div className="text-sm font-medium text-gray-950">
          {scene.slug_line || `场景 ${scene.scene_number}`}
        </div>
        <div className="mt-1 text-xs text-gray-500">
          节拍 {beats?.length || 0} · 镜头 {shots?.length || 0}
        </div>
      </div>
    </div>
  );
}
