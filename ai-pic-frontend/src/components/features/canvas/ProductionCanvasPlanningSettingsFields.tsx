import type { ProductionCanvasPlanningSettings } from "./productionCanvasPlanningSettings";

const fieldClass =
  "mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100";
const digitsOnly = (value: string) => value.replace(/\D/g, "");

export function ProductionCanvasPlanningSettingsFields({
  mode,
  onChange,
  settings,
}: {
  mode: "series" | "single_video";
  onChange: (patch: Partial<ProductionCanvasPlanningSettings>) => void;
  settings: ProductionCanvasPlanningSettings;
}) {
  const textField = (
    label: string,
    key: keyof ProductionCanvasPlanningSettings,
    placeholder: string,
  ) => (
    <label className="min-w-0" key={key}>
      <span className="text-[11px] font-semibold text-gray-600">{label}</span>
      <input
        aria-label={label}
        value={settings[key]}
        placeholder={placeholder}
        className={fieldClass}
        onChange={(event) => onChange({ [key]: event.target.value })}
      />
    </label>
  );

  return (
    <div className="mt-3 border-t border-slate-100 pt-3">
      <div className="mb-2 text-[11px] font-semibold text-slate-500">
        生产规格与模型（留空则从目标解析并自动选择）
      </div>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
        <label className="min-w-0">
          <span className="text-[11px] font-semibold text-gray-600">
            成片秒数
          </span>
          <input
            aria-label="成片秒数"
            inputMode="numeric"
            value={settings.durationSeconds}
            placeholder="自动解析"
            className={fieldClass}
            onChange={(event) =>
              onChange({ durationSeconds: digitsOnly(event.target.value) })
            }
          />
        </label>
        {mode === "series" ? (
          <label className="min-w-0">
            <span className="text-[11px] font-semibold text-gray-600">
              规划集数
            </span>
            <input
              aria-label="规划集数"
              inputMode="numeric"
              value={settings.episodeCount}
              placeholder="自动规划"
              className={fieldClass}
              onChange={(event) =>
                onChange({ episodeCount: digitsOnly(event.target.value) })
              }
            />
          </label>
        ) : null}
        <label className="min-w-0">
          <span className="text-[11px] font-semibold text-gray-600">画幅</span>
          <select
            aria-label="生产画幅"
            value={settings.aspectRatio}
            className={fieldClass}
            onChange={(event) =>
              onChange({
                aspectRatio: event.target
                  .value as ProductionCanvasPlanningSettings["aspectRatio"],
              })
            }
          >
            <option value="">自动解析</option>
            <option value="9:16">9:16 竖屏</option>
            <option value="16:9">16:9 横屏</option>
            <option value="1:1">1:1 方形</option>
          </select>
        </label>
        {textField("分辨率", "resolution", "如 1080p")}
        <label className="min-w-0">
          <span className="text-[11px] font-semibold text-gray-600">FPS</span>
          <input
            aria-label="FPS"
            inputMode="numeric"
            value={settings.fps}
            placeholder="自动选择"
            className={fieldClass}
            onChange={(event) =>
              onChange({ fps: digitsOnly(event.target.value) })
            }
          />
        </label>
        {textField("文本模型", "textModel", "自动选择")}
        {textField("图像模型", "imageModel", "自动选择")}
        {textField("视频模型", "videoModel", "自动选择")}
        {textField("视觉风格", "visualStyle", "如 3D 卡通")}
      </div>
    </div>
  );
}
