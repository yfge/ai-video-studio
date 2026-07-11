import { operatorButtonClass } from "@/components/shared";
import {
  productionCanvasContextFields,
  type ProductionCanvasContextDraft,
  type ProductionCanvasContextKey,
} from "./productionCanvasContext";
import {
  useProductionCanvasAssetOptions,
  type ProductionCanvasAssetOption,
} from "./useProductionCanvasAssetOptions";

const digitsOnly = (value: string) => value.replace(/\D/g, "");

export function ProductionCanvasChatBar({
  assetOptions: providedAssetOptions,
  context,
  error,
  onCreate,
  onContextChange,
  onPromptChange,
  prompt,
  running,
}: {
  assetOptions?: {
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
  context: ProductionCanvasContextDraft;
  error?: string | null;
  onCreate: () => void;
  onContextChange: (key: ProductionCanvasContextKey, value: string) => void;
  onPromptChange: (value: string) => void;
  prompt: string;
  running: boolean;
}) {
  const loadedAssetOptions = useProductionCanvasAssetOptions(
    providedAssetOptions === undefined,
  );
  const assetOptions = providedAssetOptions || loadedAssetOptions;
  return (
    <div className="border-b border-gray-200 bg-white px-4 py-3">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-end">
        <label className="min-w-0 flex-1">
          <span className="text-xs font-semibold text-gray-700">生产目标</span>
          <textarea
            aria-label="生产目标"
            value={prompt}
            onChange={(event) => onPromptChange(event.target.value)}
            onInput={(event) => onPromptChange(event.currentTarget.value)}
            placeholder="例如：基于林妹妹做第 4 集，办公室轻喜剧，生成完整短剧链路"
            className="mt-1 min-h-16 w-full resize-none rounded-md border border-gray-200 bg-white px-3 py-2 text-xs leading-5 text-gray-800 placeholder:text-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          />
        </label>
        <button
          type="button"
          aria-busy={running || undefined}
          className={operatorButtonClass("primary", "lg:mb-0.5")}
          disabled={running || !prompt.trim()}
          onClick={onCreate}
        >
          {running ? "执行中" : "整体创建"}
        </button>
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
        {(
          [
            ["virtual_ip_id", "IP 资产", assetOptions.virtualIPs],
            ["environment_id", "环境资产", assetOptions.environments],
          ] as const
        ).map(([key, label, options]) => (
          <label key={key} className="min-w-0">
            <span className="text-[11px] font-semibold text-gray-600">
              {label}
            </span>
            <select
              aria-label={label}
              value={context[key]}
              disabled={assetOptions.loading}
              onFocus={() => void assetOptions.load?.()}
              onChange={(event) => onContextChange(key, event.target.value)}
              className="mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 disabled:bg-gray-50 disabled:text-gray-400"
            >
              <option value="">
                {assetOptions.loading ? "加载中" : `选择${label}`}
              </option>
              {options.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name} (#{option.id})
                </option>
              ))}
            </select>
          </label>
        ))}
        <label className="min-w-0">
          <span className="text-[11px] font-semibold text-gray-600">剧集</span>
          <select
            aria-label="剧集"
            value={context.episode_id}
            disabled={assetOptions.loading}
            onFocus={() => void assetOptions.load?.()}
            onChange={(event) => {
              const episodeId = event.target.value;
              onContextChange("episode_id", episodeId);
              onContextChange("script_id", "");
              void assetOptions.loadScripts?.(episodeId);
            }}
            className="mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 disabled:bg-gray-50 disabled:text-gray-400"
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
            onChange={(event) =>
              onContextChange("script_id", event.target.value)
            }
            className="mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 disabled:bg-gray-50 disabled:text-gray-400"
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
        {productionCanvasContextFields.slice(4).map((field) => (
          <label key={field.key} className="min-w-0">
            <span className="text-[11px] font-semibold text-gray-600">
              {field.label}
            </span>
            <input
              aria-label={field.label}
              inputMode="numeric"
              value={context[field.key]}
              onChange={(event) =>
                onContextChange(field.key, digitsOnly(event.target.value))
              }
              onInput={(event) =>
                onContextChange(
                  field.key,
                  digitsOnly(event.currentTarget.value),
                )
              }
              placeholder={field.placeholder}
              className="mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 placeholder:text-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
            />
          </label>
        ))}
      </div>
      {error || assetOptions.error ? (
        <div className="mt-2 text-xs text-red-600" role="alert">
          {error || assetOptions.error}
        </div>
      ) : null}
    </div>
  );
}
