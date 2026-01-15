"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { storyStructureAPI } from "@/utils/api/endpoints";

import type { EnvironmentImage } from "./types";

interface EnvironmentReferenceImagesFieldProps {
  envKey: string;
  value: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
}

const resolveImageSrc = (url: string): string => {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  const apiBase = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");
  return `${apiBase}${url.startsWith("/") ? url : `/${url}`}`;
};

export function EnvironmentReferenceImagesField({
  envKey,
  value,
  onChange,
  disabled = false,
}: EnvironmentReferenceImagesFieldProps) {
  const [images, setImages] = useState<EnvironmentImage[]>([]);
  const [loading, setLoading] = useState(false);

  const selected = useMemo(() => new Set(value), [value]);

  const loadImages = useCallback(async () => {
    if (!envKey) return;
    try {
      setLoading(true);
      const res = await storyStructureAPI.listEnvironmentImages(envKey);
      if (res.success && res.data) {
        setImages(res.data.images || []);
      } else {
        setImages([]);
      }
    } finally {
      setLoading(false);
    }
  }, [envKey]);

  useEffect(() => {
    void loadImages();
  }, [loadImages]);

  const toggle = (url: string) => {
    if (!url || disabled) return;
    const next = new Set(value);
    if (next.has(url)) next.delete(url);
    else next.add(url);
    onChange(Array.from(next));
  };

  return (
    <div className="md:col-span-2 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            参考图（可选）
          </label>
          <p className="text-xs text-gray-500">
            仅对支持 reference_images 的模型生效（将作为参考而非基准图）
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
            const url = img.url;
            const isSelected = selected.has(url);
            return (
              <button
                key={url}
                type="button"
                onClick={() => toggle(url)}
                disabled={disabled}
                className={[
                  "relative overflow-hidden rounded border",
                  isSelected ? "border-blue-600 ring-2 ring-blue-200" : "border-gray-200",
                  disabled ? "opacity-60 cursor-not-allowed" : "hover:border-gray-400",
                ].join(" ")}
              >
                <img
                  src={resolveImageSrc(url)}
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

