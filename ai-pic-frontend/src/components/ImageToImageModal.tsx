'use client';

import Image from 'next/image';
import { useEffect, useMemo, useState, type ReactNode } from 'react';

import { MultiModelSelector } from '@/components/MultiModelSelector';
import { StyleSpecAdvancedPanel, type StyleSpecField } from '@/components/StyleSpecAdvancedPanel';
import { useStylePresets } from '@/hooks/useStylePresets';
import {
  AIModelType,
  type AIModel,
  type ApiResponse,
  type AvailableModelsResponse,
  type StyleSpec,
} from '@/utils/api';

type ReferenceSection = {
  title?: string;
  images: string[];
};

type ResolutionOption = {
  value: string;
  label: string;
  width?: number;
  height?: number;
};

interface ImageToImageModalProps {
  open: boolean;
  title?: string;
  description?: string;
  referenceSections?: ReferenceSection[];
  defaultSelected?: string[];
  lockSelection?: boolean;
  defaultPrompt?: string;
  defaultModel?: string;
  defaultCount?: number;
  defaultSize?: string;
  defaultStyle?: string;
  defaultStylePresetId?: string;
  defaultWidth?: number;
  defaultHeight?: number;
  minCount?: number;
  maxCount?: number;
  modelType?: string;
  modelFetcher?: () => Promise<ApiResponse<AvailableModelsResponse>>;
  modelCacheKey?: string;
  resolutionOptions?: ResolutionOption[];
  styleOptions?: { value: string; label: string }[];
  showStylePreset?: boolean;
  styleSpecFields?: StyleSpecField[];
  defaultStyleSpec?: StyleSpec;
  useDimensions?: boolean;
  extraContent?: ReactNode;
  submitting?: boolean;
  onClose: () => void;
  onSubmit: (payload: {
    prompt: string;
    model?: string;
    count: number;
    size?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: StyleSpec;
    width?: number;
    height?: number;
    referenceImages: string[];
  }) => Promise<void>;
}

const deriveResolutionOptions = (model?: AIModel): ResolutionOption[] => {
  if (!model) return [];
  const modelId = model.model_id || model.id || '';
  const provider = model.provider || modelId.split(':')[0] || '';

  if (provider === 'openai') {
    if (modelId.includes('dall-e-3')) {
      return [
        { value: '1024x1024', label: '1024 × 1024', width: 1024, height: 1024 },
        { value: '1024x1792', label: '1024 × 1792（竖版）', width: 1024, height: 1792 },
        { value: '1792x1024', label: '1792 × 1024（横版）', width: 1792, height: 1024 },
      ];
    }
    if (modelId.includes('dall-e-2')) {
      return [
        { value: '256x256', label: '256 × 256', width: 256, height: 256 },
        { value: '512x512', label: '512 × 512', width: 512, height: 512 },
        { value: '1024x1024', label: '1024 × 1024', width: 1024, height: 1024 },
      ];
    }
  }

  if (provider === 'volcengine' && modelId.includes('seedream-4.5')) {
    return [{ value: '2K', label: '2K（Seedream 推荐）' }];
  }

  return [];
};

export function ImageToImageModal({
  open,
  title = '图生图',
  description,
  referenceSections = [],
  defaultSelected = [],
  lockSelection = false,
  defaultPrompt = '',
  defaultModel = '',
  defaultCount = 1,
  defaultSize = '',
  defaultStyle = 'realistic',
  defaultStylePresetId = '',
  defaultStyleSpec,
  defaultWidth = 1024,
  defaultHeight = 1024,
  minCount = 1,
  maxCount = 4,
  modelType = AIModelType.ImageToImage,
  modelFetcher,
  modelCacheKey,
  resolutionOptions,
  styleOptions,
  showStylePreset = true,
  styleSpecFields,
  useDimensions = false,
  extraContent,
  submitting = false,
  onClose,
  onSubmit,
}: ImageToImageModalProps) {
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [loadedDefaultModel, setLoadedDefaultModel] = useState<string>('');
  const [selectedRefs, setSelectedRefs] = useState<string[]>(defaultSelected);
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [modelIds, setModelIds] = useState<string[]>(defaultModel ? [defaultModel] : []);
  const [count, setCount] = useState(defaultCount);
  const [size, setSize] = useState(defaultSize);
  const [style, setStyle] = useState(defaultStyle);
  const [stylePresetId, setStylePresetId] = useState(defaultStylePresetId);
  const [styleSpec, setStyleSpec] = useState<StyleSpec>(defaultStyleSpec ?? {});
  const [width, setWidth] = useState(defaultWidth);
  const [height, setHeight] = useState(defaultHeight);

  const { presets: stylePresets } = useStylePresets({ enabled: showStylePreset });
  const selectedStylePreset = useMemo(() => {
    if (!stylePresetId) return undefined;
    return stylePresets.find(p => p.preset_id === stylePresetId);
  }, [stylePresets, stylePresetId]);

  useEffect(() => {
    if (!open) return;
    setSelectedRefs(defaultSelected);
    setPrompt(defaultPrompt);
    setModelIds(defaultModel ? [defaultModel] : []);
    setCount(defaultCount);
    setSize(defaultSize);
    setStyle(defaultStyle);
    setStylePresetId(defaultStylePresetId);
    setStyleSpec(defaultStyleSpec ?? {});
    setWidth(defaultWidth);
    setHeight(defaultHeight);
  }, [
    open,
    defaultSelected,
    defaultPrompt,
    defaultModel,
    defaultCount,
    defaultSize,
    defaultStyle,
    defaultStylePresetId,
    defaultStyleSpec,
    defaultWidth,
    defaultHeight,
  ]);

  useEffect(() => {
    if (modelIds.length === 0 && loadedDefaultModel) {
      setModelIds([loadedDefaultModel]);
    }
  }, [loadedDefaultModel, modelIds.length]);

  const selectedModel = useMemo(() => {
    if (!modelIds[0]) return undefined;
    return availableModels.find(m => m.model_id === modelIds[0]);
  }, [availableModels, modelIds]);

  const derivedResolutionOptions = useMemo(() => {
    if (resolutionOptions && resolutionOptions.length > 0) {
      return resolutionOptions;
    }
    return deriveResolutionOptions(selectedModel);
  }, [resolutionOptions, selectedModel]);

  const toggleReference = (url: string) => {
    if (lockSelection) return;
    setSelectedRefs(prev =>
      prev.includes(url) ? prev.filter(item => item !== url) : [...prev, url],
    );
  };

  const handleResolutionPreset = (value: string) => {
    setSize(value);
    const option = derivedResolutionOptions.find(opt => opt.value === value);
    if (option?.width && option.height) {
      setWidth(option.width);
      setHeight(option.height);
    }
  };

  const handleSubmit = async () => {
    const refs = referenceSections.length > 0 ? selectedRefs : [];
    await onSubmit({
      prompt: prompt.trim(),
      model: modelIds[0],
      count: Math.max(minCount, Math.min(maxCount, count || minCount)),
      size: useDimensions ? undefined : size || undefined,
      style: style || undefined,
      style_preset_id: stylePresetId || undefined,
      style_spec: styleSpec && Object.keys(styleSpec).length > 0 ? styleSpec : undefined,
      width: useDimensions ? width || defaultWidth : undefined,
      height: useDimensions ? height || defaultHeight : undefined,
      referenceImages: refs,
    });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-3 py-6">
      <div className="w-full max-w-5xl overflow-auto rounded-xl bg-white p-5 shadow-2xl max-h-full">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            {description ? (
              <p className="mt-1 text-xs text-gray-600">{description}</p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            关闭
          </button>
        </div>

        {referenceSections.length > 0 && (
          <div className="mt-4 space-y-3">
            {referenceSections.map((section, idx) => (
              <div key={idx}>
                {section.title ? (
                  <div className="text-xs font-medium text-gray-700 mb-2">
                    {section.title}
                  </div>
                ) : null}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {section.images.map(url => {
                    const selected = selectedRefs.includes(url);
                    return (
                      <button
                        key={url}
                        type="button"
                        onClick={() => toggleReference(url)}
                        className={`relative overflow-hidden rounded border ${
                          selected ? 'ring-2 ring-blue-500' : 'border-gray-200'
                        }`}
                      >
                        <div className="relative h-28 w-full">
                          <Image
                            src={url}
                            alt={section.title || '参考图'}
                            fill
                            sizes="100%"
                            className="object-cover"
                            unoptimized
                          />
                        </div>
                        {selected && (
                          <div className="absolute inset-0 bg-blue-500/30 flex items-center justify-center text-white text-xs">
                            已选
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                提示词
              </label>
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                rows={4}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="描述想要的变体效果，例如背面照、全身照、不同光线等"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                模型
              </label>
              <MultiModelSelector
                value={modelIds}
                onChange={ids => setModelIds(ids.slice(0, 1))}
                modelType={modelType}
                cacheKey={modelCacheKey || `image-to-image:${modelType}`}
                multiple={false}
                allowAuto={false}
                autoSelectDefault
                fetcher={modelFetcher}
                helperText="选择支持图生图的模型"
                onModelsLoaded={(loaded, defaultModelId) => {
                  setAvailableModels(loaded);
                  setLoadedDefaultModel(defaultModelId);
                  if (modelIds.length === 0 && defaultModelId) {
                    setModelIds([defaultModelId]);
                  } else if (modelIds.length === 0 && loaded.length > 0) {
                    setModelIds([loaded[0].model_id]);
                  }
                }}
              />
              {selectedModel?.capabilities?.length ? (
                <p className="mt-1 text-xs text-gray-500">
                  能力：{selectedModel.capabilities.join(', ')}
                </p>
              ) : null}
            </div>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  生成张数
                </label>
                <input
                  type="number"
                  min={minCount}
                  max={maxCount}
                  value={count}
                  onChange={e => setCount(parseInt(e.target.value, 10) || minCount)}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="mt-1 text-[11px] text-gray-500">
                  一次最多 {maxCount} 张，部分模型会返回多张候选。
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  风格
                </label>
                <select
                  value={style}
                  onChange={e => setStyle(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {(styleOptions && styleOptions.length > 0
                    ? styleOptions
                    : [
                        { value: 'realistic', label: '写实' },
                        { value: 'anime', label: '二次元' },
                        { value: 'cinematic', label: '电影感' },
                        { value: 'sketch', label: '素描' },
                      ]
                  ).map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {showStylePreset ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  风格预设
                </label>
                <select
                  value={stylePresetId}
                  onChange={e => setStylePresetId(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">（不使用预设）</option>
                  {stylePresets.map(preset => (
                    <option key={preset.preset_id} value={preset.preset_id}>
                      {preset.label || preset.preset_id}
                    </option>
                  ))}
                </select>
                {selectedStylePreset?.description ? (
                  <p className="mt-1 text-[11px] text-gray-500">
                    {selectedStylePreset.description}
                  </p>
                ) : null}
              </div>
            ) : null}

            {styleSpecFields && styleSpecFields.length > 0 ? (
              <StyleSpecAdvancedPanel
                fields={styleSpecFields}
                value={styleSpec}
                onChange={setStyleSpec}
              />
            ) : null}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                分辨率
              </label>
              {useDimensions ? (
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">宽</span>
                    <input
                      type="number"
                      min={64}
                      max={2048}
                      value={width}
                      onChange={e => setWidth(parseInt(e.target.value, 10) || defaultWidth)}
                      className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">高</span>
                    <input
                      type="number"
                      min={64}
                      max={2048}
                      value={height}
                      onChange={e => setHeight(parseInt(e.target.value, 10) || defaultHeight)}
                      className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>
              ) : (
                <select
                  value={size}
                  onChange={e => handleResolutionPreset(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">自动（模型默认）</option>
                  {derivedResolutionOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              )}
              {!useDimensions && derivedResolutionOptions.length > 0 ? (
                <p className="mt-1 text-[11px] text-gray-500">
                  选项基于当前模型文档（OpenAI / 火山方舟等）。
                </p>
              ) : null}
            </div>
          </div>
        </div>

        {extraContent ? <div className="mt-4 border-t pt-4">{extraContent}</div> : null}

        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-2 text-sm rounded border border-gray-300 text-gray-700 hover:bg-gray-50"
            disabled={submitting}
          >
            取消
          </button>
          <button
            type="button"
            onClick={() => void handleSubmit()}
            disabled={submitting || (referenceSections.length > 0 && selectedRefs.length === 0)}
            className="px-4 py-2 text-sm font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {submitting ? '提交中...' : '提交图生图任务'}
          </button>
        </div>
      </div>
    </div>
  );
}
