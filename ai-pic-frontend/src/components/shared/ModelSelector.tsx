import { useEffect, useMemo, useState } from "react";

import type {
  AIModel,
  ApiResponse,
  AvailableModelsResponse,
} from "@/utils/api/types";
import { useAvailableModels } from "@/hooks/useAvailableModels";

interface ModelSelectorProps {
  value: string;
  onChange: (modelId: string) => void;
  label?: string;
  helperText?: string;
  allowAuto?: boolean;
  autoLabel?: string;
  modelType?: string;
  fetcher?: () => Promise<ApiResponse<AvailableModelsResponse>>;
  cacheKey?: string;
  disabled?: boolean;
  autoSelectDefault?: boolean;
  onModelsLoaded?: (models: AIModel[], defaultModel: string) => void;
  className?: string;
  filterModels?: (model: AIModel) => boolean;
}

export function ModelSelector({
  value,
  onChange,
  label,
  helperText,
  allowAuto = true,
  autoLabel = "自动（推荐）",
  modelType = "text",
  fetcher,
  cacheKey,
  disabled = false,
  autoSelectDefault = false,
  onModelsLoaded,
  className,
  filterModels,
}: ModelSelectorProps) {
  const { models, defaultModel, loading, error, refresh } = useAvailableModels({
    modelType,
    fetcher,
    cacheKey,
    enabled: !disabled,
  });
  const [provider, setProvider] = useState<string>("all");

  useEffect(() => {
    if (onModelsLoaded) {
      onModelsLoaded(models, defaultModel);
    }
  }, [models, defaultModel, onModelsLoaded]);

  useEffect(() => {
    if (!autoSelectDefault) {
      return;
    }
    if (!value && defaultModel) {
      onChange(defaultModel);
    }
  }, [autoSelectDefault, defaultModel, onChange, value]);

  const filtered = filterModels ? models.filter(filterModels) : models;
  // 若过滤后为空，回退到原始列表，避免 UI 出现空下拉
  const visibleModels = filtered.length > 0 ? filtered : models;
  const providers = useMemo(() => {
    const ps = new Set<string>();
    visibleModels.forEach((model) => {
      if (model.provider) ps.add(model.provider);
    });
    return Array.from(ps).sort();
  }, [visibleModels]);

  useEffect(() => {
    // 当 models 或默认值变化时，推断当前 provider
    if (providers.length === 0) return;
    const valueProvider = value ? value.split(":")[0] : "";
    const defaultProvider = defaultModel ? defaultModel.split(":")[0] : "";
    const target =
      valueProvider && providers.includes(valueProvider)
        ? valueProvider
        : defaultProvider && providers.includes(defaultProvider)
        ? defaultProvider
        : providers[0];
    setProvider((prev) => (providers.includes(prev) ? prev : target));
  }, [providers, value, defaultModel]);

  const modelsByProvider =
    provider === "all"
      ? visibleModels
      : visibleModels.filter((model) => model.provider === provider);

  return (
    <div className={className}>
      {label ? (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
      ) : null}
      <div className="grid gap-2 sm:grid-cols-2">
        <select
          value={provider}
          onChange={(event) => {
            const next = event.target.value;
            setProvider(next);
            // 如果当前模型不属于新 provider，清空选择以防展示溢出
            if (next !== "all" && value && !value.startsWith(`${next}:`)) {
              onChange("");
            }
          }}
          disabled={disabled || loading || providers.length === 0}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">全部提供商</option>
          {providers.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <select
          value={value ?? ""}
          onChange={(event) => onChange(event.target.value)}
          disabled={disabled || loading || modelsByProvider.length === 0}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {allowAuto ? <option value="">{autoLabel}</option> : null}
          {modelsByProvider.map((model) => (
            <option key={model.model_id} value={model.model_id}>
              {(model.name || model.id || model.model_id) ?? model.model_id} —{" "}
              {model.provider}
            </option>
          ))}
        </select>
      </div>
      <div className="mt-1 text-xs text-gray-500 space-y-1">
        {helperText ? <p>{helperText}</p> : null}
        {loading ? <p>模型加载中...</p> : null}
        {error ? (
          <button
            type="button"
            onClick={() => {
              void refresh();
            }}
            className="text-red-600 hover:underline"
          >
            模型加载失败，点击重试
          </button>
        ) : null}
      </div>
    </div>
  );
}
