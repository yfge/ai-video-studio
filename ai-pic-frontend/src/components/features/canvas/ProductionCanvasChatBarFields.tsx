import {
  productionCanvasContextFields,
  type ProductionCanvasContextDraft,
  type ProductionCanvasContextKey,
} from "./productionCanvasContext";
import type { ProductionCanvasSingleVideoDraft } from "./productionCanvasCreation";
import type { ProductionCanvasAssetOption } from "./useProductionCanvasAssetOptions";

const fieldClass =
  "mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 disabled:bg-gray-50 disabled:text-gray-400";
const digitsOnly = (value: string) => value.replace(/\D/g, "");

export type ProductionCanvasChatBarAssetOptions = {
  environments: ProductionCanvasAssetOption[];
  episodes?: ProductionCanvasAssetOption[];
  error: string | null;
  load?: () => Promise<void>;
  loadScripts?: (episodeId: string) => Promise<void>;
  loading: boolean;
  scripts?: ProductionCanvasAssetOption[];
  scriptsLoading?: boolean;
  virtualIPs: ProductionCanvasAssetOption[];
};

type CommonProps = {
  assetOptions: ProductionCanvasChatBarAssetOptions;
  context: ProductionCanvasContextDraft;
  onContextChange: (key: ProductionCanvasContextKey, value: string) => void;
};

function AssetSelect({
  assetOptions,
  context,
  field,
  label,
  options,
  onContextChange,
}: CommonProps & {
  field: "virtual_ip_id" | "environment_id";
  label: string;
  options: ProductionCanvasAssetOption[];
}) {
  return (
    <label className="min-w-0">
      <span className="text-[11px] font-semibold text-gray-600">{label}</span>
      <select
        aria-label={label}
        value={context[field]}
        disabled={assetOptions.loading}
        onFocus={() => void assetOptions.load?.()}
        onChange={(event) => onContextChange(field, event.target.value)}
        className={fieldClass}
      >
        <option value="">
          {assetOptions.loading ? "加载中" : `选择${label}（可选）`}
        </option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.name} (#{option.id})
          </option>
        ))}
      </select>
    </label>
  );
}

function AssetFields(props: CommonProps) {
  return (
    <>
      <AssetSelect
        {...props}
        field="virtual_ip_id"
        label="IP 资产"
        options={props.assetOptions.virtualIPs}
      />
      <AssetSelect
        {...props}
        field="environment_id"
        label="环境资产"
        options={props.assetOptions.environments}
      />
    </>
  );
}

export function ProductionCanvasSingleVideoFields({
  assetOptions,
  context,
  draft,
  onContextChange,
  onDraftChange,
}: CommonProps & {
  draft: ProductionCanvasSingleVideoDraft;
  onDraftChange: (patch: Partial<ProductionCanvasSingleVideoDraft>) => void;
}) {
  return (
    <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
      <label className="min-w-0">
        <span className="text-[11px] font-semibold text-gray-600">
          视频标题
        </span>
        <input
          aria-label="视频标题"
          value={draft.title}
          onChange={(event) => onDraftChange({ title: event.target.value })}
          placeholder="可选，默认从目标提取"
          className={fieldClass}
        />
      </label>
      <label className="min-w-0">
        <span className="text-[11px] font-semibold text-gray-600">时长</span>
        <select
          aria-label="视频时长"
          value={draft.durationMinutes}
          onChange={(event) =>
            onDraftChange({
              durationMinutes: Number(event.target.value) as 3 | 5,
            })
          }
          className={fieldClass}
        >
          <option value={3}>3 分钟</option>
          <option value={5}>5 分钟</option>
        </select>
      </label>
      <label className="min-w-0">
        <span className="text-[11px] font-semibold text-gray-600">画幅</span>
        <select
          aria-label="视频画幅"
          value={draft.aspectRatio}
          onChange={(event) =>
            onDraftChange({
              aspectRatio: event.target.value as "9:16" | "16:9",
            })
          }
          className={fieldClass}
        >
          <option value="9:16">9:16 竖屏</option>
          <option value="16:9">16:9 横屏</option>
        </select>
      </label>
      <label className="min-w-0">
        <span className="text-[11px] font-semibold text-gray-600">风格</span>
        <input
          aria-label="视频风格"
          value={draft.style}
          onChange={(event) => onDraftChange({ style: event.target.value })}
          placeholder="可选"
          className={fieldClass}
        />
      </label>
      <AssetFields
        assetOptions={assetOptions}
        context={context}
        onContextChange={onContextChange}
      />
    </div>
  );
}

function EpisodeAndScriptFields(props: CommonProps) {
  const { assetOptions, context, onContextChange } = props;
  return (
    <>
      <label className="min-w-0">
        <span className="text-[11px] font-semibold text-gray-600">剧集</span>
        <select
          aria-label="剧集"
          value={context.episode_id}
          disabled={assetOptions.loading}
          onFocus={() => void assetOptions.load?.()}
          onChange={(event) => {
            const episodeId = event.target.value;
            onContextChange("story_id", "");
            onContextChange("episode_id", episodeId);
            void assetOptions.loadScripts?.(episodeId);
          }}
          className={fieldClass}
        >
          <option value="">
            {assetOptions.loading ? "加载中" : "选择剧集"}
          </option>
          {(assetOptions.episodes || []).map((option) => (
            <option key={option.id} value={option.id}>
              {option.name} (#{option.id})
            </option>
          ))}
        </select>
      </label>
      <label className="min-w-0">
        <span className="text-[11px] font-semibold text-gray-600">剧本</span>
        <select
          aria-label="剧本"
          value={context.script_id}
          disabled={!context.episode_id || assetOptions.scriptsLoading}
          onFocus={() => void assetOptions.loadScripts?.(context.episode_id)}
          onChange={(event) => onContextChange("script_id", event.target.value)}
          className={fieldClass}
        >
          <option value="">
            {assetOptions.scriptsLoading ? "加载中" : "选择剧本（可选）"}
          </option>
          {(assetOptions.scripts || []).map((option) => (
            <option key={option.id} value={option.id}>
              {option.name} (#{option.id})
            </option>
          ))}
        </select>
      </label>
    </>
  );
}

export function ProductionCanvasSeriesFields(props: CommonProps) {
  return (
    <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
      <AssetFields {...props} />
      <EpisodeAndScriptFields {...props} />
      {productionCanvasContextFields.slice(4).map((field) => (
        <label key={field.key} className="min-w-0">
          <span className="text-[11px] font-semibold text-gray-600">
            {field.label}
          </span>
          <input
            aria-label={field.label}
            inputMode="numeric"
            value={props.context[field.key]}
            onChange={(event) =>
              props.onContextChange(field.key, digitsOnly(event.target.value))
            }
            onInput={(event) =>
              props.onContextChange(
                field.key,
                digitsOnly(event.currentTarget.value),
              )
            }
            placeholder={field.placeholder}
            className={fieldClass}
          />
        </label>
      ))}
    </div>
  );
}
