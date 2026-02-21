import { useEffect, useMemo, useState } from "react";

import { useAvailableModels } from "@/hooks/useAvailableModels";
import {
  AIModelType,
  type AIModel,
  type ApiResponse,
  type AvailableModelsResponse,
} from "@/utils/api/types";

// 简化的模型类型映射，兼容旧代码
const LEGACY_TYPE_MAP: Record<string, string> = {
  text: AIModelType.Text,
  image: AIModelType.Image,
  video: AIModelType.Video,
  audio: AIModelType.Audio,
};

interface MultiModelSelectorProps {
  value: string[];
  onChange: (value: string[]) => void;
  modelType?: string; // 现在推荐传入 AIModelType 枚举值，但也兼容 'text'/'image' 等简写
  cacheKey?: string;
  label?: string;
  helperText?: string;
  disabled?: boolean;
  filterModels?: (model: AIModel) => boolean;
  onModelsLoaded?: (models: AIModel[], defaultModel: string) => void;
  allowAuto?: boolean;
  autoLabel?: string;
  autoSelectDefault?: boolean;
  multiple?: boolean;
  className?: string;
  fetcher?: () => Promise<ApiResponse<AvailableModelsResponse>>;
}

const providerLabel = (provider: string) => {
  const map: Record<string, string> = {
    openai: "OpenAI",
    volcengine: "火山引擎",
    deepseek: "DeepSeek",
    keling: "可灵",
    jimeng: "即梦",
    google: "Google",
    gpt: "GPT",
  };
  return map[provider] ?? provider;
};

const matchesModelType = (model: AIModel, targetType: string) => {
  if (!targetType) return true;
  const t = targetType.toLowerCase();
  const mtype = (model.type || "").toLowerCase();
  if (mtype === t) return true;
  // 兼容 image <-> image_to_image
  if (t === AIModelType.Image.toLowerCase() || t === "image") {
    return ["image_to_image", "text_to_image"].includes(mtype);
  }
  if (t === AIModelType.ImageToImage.toLowerCase() || t === "image_to_image") {
    return (
      ["image", "text_to_image"].includes(mtype) ||
      mtype === AIModelType.Image.toLowerCase()
    );
  }
  return false;
};

export function MultiModelSelector({
  value,
  onChange,
  modelType = AIModelType.Text,
  cacheKey,
  label,
  helperText,
  disabled = false,
  filterModels,
  onModelsLoaded,
  allowAuto = true,
  autoLabel = "自动（推荐）",
  autoSelectDefault = false,
  multiple = true,
  className,
  fetcher,
}: MultiModelSelectorProps) {
  // 解析实际的 filter type
  const actualModelType = LEGACY_TYPE_MAP[modelType] || modelType;

  const { models, defaultModel, loading, error, refresh } = useAvailableModels({
    modelType: actualModelType, // 传给 hook 的也应该是转换后的标准类型
    cacheKey,
    enabled: !disabled,
    fetcher,
  });
  const [provider, setProvider] = useState<string>("all");

  // 1. 过滤模型：先按 Type 再按自定义 filter
  const filteredModels = useMemo(() => {
    let result = models;
    // 严格类型过滤
    if (actualModelType) {
      result = result.filter((m) => matchesModelType(m, actualModelType));
    }
    // 自定义过滤
    if (filterModels) {
      result = result.filter(filterModels);
    }
    return result;
  }, [models, actualModelType, filterModels]);

  // 2. 分组逻辑
  const grouped = useMemo<Record<string, AIModel[]>>(() => {
    const groupedModels: Record<string, AIModel[]> = {};
    filteredModels.forEach((model) => {
      const provider = model.provider || "unknown";
      if (!groupedModels[provider]) groupedModels[provider] = [];
      groupedModels[provider].push(model);
    });

    // 排序：OpenAI 优先，其他字母序
    const ordered: Record<string, AIModel[]> = {};
    const providers = Object.keys(groupedModels).sort((a, b) => {
      if (a === "openai") return -1;
      if (b === "openai") return 1;
      return a.localeCompare(b);
    });

    providers.forEach((p) => {
      ordered[p] = groupedModels[p];
    });
    return ordered;
  }, [filteredModels]);

  const providers = useMemo(() => {
    const ps = new Set<string>();
    filteredModels.forEach((model) => {
      if (model.provider) ps.add(model.provider);
    });
    return Array.from(ps).sort();
  }, [filteredModels]);

  // 3. 初始加载回调 & 默认选中逻辑
  useEffect(() => {
    if (!loading && models.length > 0) {
      onModelsLoaded?.(models, defaultModel);

      // 当允许自动选择时，只在当前没有选中值的情况下选中默认模型
      if (value.length === 0 && defaultModel && autoSelectDefault) {
        onChange([defaultModel]);
      }
    }
    // 明确依赖 onChange/onModelsLoaded/value.length，避免闭包用旧值
  }, [
    loading,
    models,
    defaultModel,
    autoSelectDefault,
    value.length,
    onChange,
    onModelsLoaded,
  ]);

  useEffect(() => {
    if (providers.length === 0) return;
    const currentProvider = value[0]?.split(":")[0] || "";
    const defaultProvider = defaultModel ? defaultModel.split(":")[0] : "";
    const target =
      currentProvider && providers.includes(currentProvider)
        ? currentProvider
        : defaultProvider && providers.includes(defaultProvider)
        ? defaultProvider
        : providers[0];
    setProvider((prev) => (providers.includes(prev) ? prev : target));
  }, [providers, value, defaultModel]);

  const modelsByProvider =
    provider === "all"
      ? filteredModels
      : filteredModels.filter((model) => model.provider === provider);

  const toggle = (modelId: string) => {
    if (multiple) {
      if (value.includes(modelId)) {
        onChange(value.filter((m) => m !== modelId));
      } else {
        onChange([...value, modelId]);
      }
    } else {
      if (!modelId && allowAuto) {
        onChange([]);
        return;
      }
      onChange(modelId ? [modelId] : []);
    }
  };

  return (
    <div className={className}>
      {label ? (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      ) : null}
      {helperText ? (
        <p className="text-xs text-gray-500 mb-1">{helperText}</p>
      ) : null}
      {loading ? <p className="text-sm text-gray-500">模型加载中...</p> : null}
      {error ? (
        <div className="text-sm text-red-600 flex items-center gap-2">
          <span>{error}</span>
          <button
            type="button"
            className="text-blue-600 underline"
            onClick={() => refresh()}
          >
            重试
          </button>
        </div>
      ) : null}
      {!loading && !error && Object.keys(grouped).length === 0 ? (
        <p className="text-sm text-gray-500">
          暂无可用模型，请检查提供商配置或刷新。
        </p>
      ) : null}

      {/* 单选模式：改为提供商 + 模型两级下拉，避免长列表溢出 */}
      {!multiple ? (
        <div className="space-y-2">
          <div className="grid gap-2 sm:grid-cols-2">
            <select
              value={provider}
              onChange={(event) => {
                const next = event.target.value;
                setProvider(next);
                if (
                  next !== "all" &&
                  value[0] &&
                  !value[0].startsWith(`${next}:`)
                ) {
                  onChange([]);
                }
                if (!multiple && next !== "all") {
                  const first = filteredModels.find(
                    (model) => model.provider === next,
                  );
                  if (first) {
                    onChange([first.model_id]);
                  }
                }
              }}
              disabled={disabled || loading || providers.length === 0}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部提供商</option>
              {providers.map((p) => (
                <option key={p} value={p}>
                  {providerLabel(p)}
                </option>
              ))}
            </select>
            <select
              value={value[0] ?? ""}
              onChange={(event) =>
                onChange(event.target.value ? [event.target.value] : [])
              }
              disabled={disabled || loading || modelsByProvider.length === 0}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {allowAuto ? <option value="">{autoLabel}</option> : null}
              {modelsByProvider.map((model) => (
                <option key={model.model_id} value={model.model_id}>
                  {(model.name || model.id || model.model_id) ?? model.model_id}{" "}
                  — {providerLabel(model.provider || "")}
                </option>
              ))}
            </select>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {!multiple && allowAuto ? (
            <div className="border border-gray-200 rounded-lg p-3">
              <button
                type="button"
                className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                  value.length === 0
                    ? "bg-blue-500 text-white border-blue-500"
                    : "bg-white text-gray-700 border-gray-300 hover:border-blue-300"
                }`}
                onClick={() => toggle("")}
                disabled={disabled}
              >
                {autoLabel}
              </button>
            </div>
          ) : null}
          {Object.entries(grouped)
            .sort(([a], [b]) =>
              providerLabel(a).localeCompare(providerLabel(b)),
            )
            .map(([providerKey, items]) => (
              <div
                key={providerKey}
                className="border border-gray-200 rounded-lg p-3"
              >
                <h4 className="font-medium text-gray-900 mb-2 text-sm">
                  {providerLabel(providerKey)}
                </h4>
                <div className="flex flex-wrap gap-2">
                  {items.map((model) => {
                    const labelText = model.name || model.id || model.model_id;
                    const selected = value.includes(model.model_id);
                    return (
                      <button
                        key={model.model_id}
                        type="button"
                        onClick={() => toggle(model.model_id)}
                        className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                          selected
                            ? "bg-blue-500 text-white border-blue-500"
                            : "bg-white text-gray-700 border-gray-300 hover:border-blue-300"
                        }`}
                        title={providerLabel(model.provider)}
                        disabled={disabled}
                      >
                        {labelText}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
        </div>
      )}

      {value.length > 0 ? (
        <div className="mt-3">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            已选模型
          </label>
          <div className="flex flex-wrap gap-2">
            {value.map((modelId) => {
              const model = filteredModels.find((m) => m.model_id === modelId);
              const provider =
                model?.provider || modelId.split(":")[0] || "模型";
              const labelText = model?.name || model?.id || modelId;
              return (
                <span
                  key={modelId}
                  className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs flex items-center"
                >
                  {providerLabel(provider)} — {labelText}
                  <button
                    type="button"
                    className="ml-1 text-blue-500 hover:text-blue-700"
                    onClick={() => toggle(modelId)}
                    disabled={disabled}
                  >
                    ×
                  </button>
                </span>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
