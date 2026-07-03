import type { ProductionCanvasNode } from "./productionCanvasModel";

type MediaOutputValue = string | number | boolean | number[] | undefined;

function stringOutput(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "string" ? value : "";
}

function numberOutput(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "number" && Number.isFinite(value)
    ? String(value)
    : "";
}

function boolOutput(
  outputs: Record<string, unknown> | undefined,
  key: string,
  fallback: boolean,
) {
  const value = outputs?.[key];
  return typeof value === "boolean" ? value : fallback;
}

function frameIndexesText(outputs: Record<string, unknown> | undefined) {
  const value = outputs?.frame_indexes;
  return Array.isArray(value) ? value.join(", ") : "";
}

function parseFrameIndexes(value: string) {
  const indexes = value
    .split(/[,\s，、]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => (/^\d+$/.test(item) ? Number(item) : Number.NaN))
    .filter(
      (item, index, all) =>
        Number.isInteger(item) && item >= 0 && all.indexOf(item) === index,
    );
  return indexes.length ? indexes : undefined;
}

function parseNumber(value: string) {
  if (!value.trim()) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
}

function TextField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  const handleValue = (target: HTMLInputElement) => onChange(target.value);
  return (
    <label className="min-w-0">
      <span className="text-[11px] font-semibold text-gray-600">{label}</span>
      <input
        aria-label={label}
        className="mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
        value={value}
        onChange={(event) => handleValue(event.currentTarget)}
        onInput={(event) => handleValue(event.currentTarget)}
      />
    </label>
  );
}

export function ProductionCanvasMediaControls({
  node,
  onUpdateNodeOutputs,
}: {
  node?: ProductionCanvasNode;
  onUpdateNodeOutputs: (
    nodeId: string,
    patch: Record<string, MediaOutputValue>,
  ) => void;
}) {
  if (
    !node ||
    (node.skill !== "image.candidates" && node.skill !== "video.candidates")
  ) {
    return null;
  }

  const outputs = node.outputs;
  const update = (patch: Record<string, MediaOutputValue>) =>
    onUpdateNodeOutputs(node.id, patch);
  const isImage = node.skill === "image.candidates";

  return (
    <div className="border-t border-gray-100 pt-3">
      <div className="text-xs font-semibold text-gray-700">媒体执行参数</div>
      <div className="mt-2 grid gap-2">
        <TextField
          label="媒体帧索引"
          value={frameIndexesText(outputs)}
          onChange={(value) =>
            update({ frame_indexes: parseFrameIndexes(value) })
          }
        />
        <TextField
          label="媒体模型"
          value={stringOutput(outputs, "model")}
          onChange={(value) => update({ model: value.trim() || undefined })}
        />
        {isImage ? (
          <>
            <TextField
              label="图片画幅"
              value={stringOutput(outputs, "aspect_ratio")}
              onChange={(value) =>
                update({ aspect_ratio: value.trim() || undefined })
              }
            />
            <label className="flex items-center gap-2 text-xs text-gray-600">
              <input
                aria-label="要求参考图"
                type="checkbox"
                checked={boolOutput(outputs, "require_reference_images", true)}
                onChange={(event) =>
                  update({
                    require_reference_images: event.currentTarget.checked,
                  })
                }
              />
              要求参考图
            </label>
          </>
        ) : (
          <>
            <TextField
              label="视频时长"
              value={numberOutput(outputs, "duration")}
              onChange={(value) => update({ duration: parseNumber(value) })}
            />
            <TextField
              label="视频 FPS"
              value={numberOutput(outputs, "fps")}
              onChange={(value) => update({ fps: parseNumber(value) })}
            />
            <TextField
              label="视频分辨率"
              value={stringOutput(outputs, "resolution")}
              onChange={(value) =>
                update({ resolution: value.trim() || undefined })
              }
            />
            <TextField
              label="视频画幅"
              value={stringOutput(outputs, "ratio")}
              onChange={(value) => update({ ratio: value.trim() || undefined })}
            />
            <label className="flex items-center gap-2 text-xs text-gray-600">
              <input
                aria-label="固定镜头"
                type="checkbox"
                checked={boolOutput(outputs, "camera_fixed", false)}
                onChange={(event) =>
                  update({ camera_fixed: event.currentTarget.checked })
                }
              />
              固定镜头
            </label>
          </>
        )}
      </div>
    </div>
  );
}
