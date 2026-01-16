"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type { VirtualIPImage } from "@/utils/api/types";
import { virtualIPImageAPI } from "@/utils/api/endpoints";
import { resolveImageUrl } from "@/hooks/useVirtualIPImages";

interface VirtualIPReferenceImagesFieldProps {
  virtualIPId: number;
  value: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
}

const resolveReferenceValue = (image: VirtualIPImage): string => {
  if (image.oss_url) return image.oss_url;
  return image.file_path || "";
};

export function VirtualIPReferenceImagesField({
  virtualIPId,
  value,
  onChange,
  disabled = false,
}: VirtualIPReferenceImagesFieldProps) {
  const [images, setImages] = useState<VirtualIPImage[]>([]);
  const [loading, setLoading] = useState(false);

  const selected = useMemo(() => new Set(value), [value]);

  const loadImages = useCallback(async () => {
    if (!virtualIPId) return;
    try {
      setLoading(true);
      const res = await virtualIPImageAPI.getImages(virtualIPId);
      if (res.success && res.data) setImages(res.data);
      else setImages([]);
    } finally {
      setLoading(false);
    }
  }, [virtualIPId]);

  useEffect(() => {
    void loadImages();
  }, [loadImages]);

  const toggle = (ref: string) => {
    if (!ref || disabled) return;
    const next = new Set(value);
    if (next.has(ref)) next.delete(ref);
    else next.add(ref);
    onChange(Array.from(next));
  };

  return (
    <div className="md:col-span-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            参考图（可选）
          </label>
          <p className="text-xs text-gray-500">
            仅对支持 reference_images 的模型生效（将作为风格/构图参考）
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => void loadImages()}
            className="text-xs text-gray-600 hover:text-gray-900"
            disabled={loading}
          >
            刷新
          </button>
          {value.length > 0 ? (
            <button
              type="button"
              onClick={() => onChange([])}
              className="text-xs text-blue-600 hover:text-blue-800"
              disabled={disabled}
            >
              清空
            </button>
          ) : null}
        </div>
      </div>

      {loading ? (
        <p className="text-xs text-gray-500">加载参考图中...</p>
      ) : images.length === 0 ? (
        <p className="text-xs text-gray-500">暂无可选参考图</p>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
          {images.map((img) => {
            const ref = resolveReferenceValue(img);
            if (!ref) return null;
            const isSelected = selected.has(ref);
            return (
              <button
                key={`${img.id}:${ref}`}
                type="button"
                onClick={() => toggle(ref)}
                disabled={disabled}
                className={[
                  "relative overflow-hidden rounded border",
                  isSelected
                    ? "border-blue-600 ring-2 ring-blue-200"
                    : "border-gray-200",
                  disabled
                    ? "opacity-60 cursor-not-allowed"
                    : "hover:border-gray-400",
                ].join(" ")}
              >
                <img
                  src={resolveImageUrl(img)}
                  alt="reference"
                  className="h-20 w-full object-cover"
                />
                {isSelected ? (
                  <span className="absolute right-1 top-1 rounded bg-blue-600 px-1.5 py-0.5 text-[10px] text-white">
                    已选
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

