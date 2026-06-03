"use client";

import type { VirtualIP, VirtualIPImage } from "@/utils/api/types";
import { ImagePreviewCard, OperatorState } from "@/components/shared";
import { resolveImageUrl } from "@/hooks/useVirtualIPImages";
import { getCategoryLabel } from "./categoryLabel";

interface ImageGridProps {
  images: VirtualIPImage[];
  virtualIP: VirtualIP;
  onPreview: (image: VirtualIPImage) => void;
  onImg2Img: (image: VirtualIPImage) => void;
  onDelete: (imageId: number) => void;
  onSetDefault: (imageId: number) => void;
}

export function ImageGrid({
  images,
  virtualIP,
  onPreview,
  onImg2Img,
  onDelete,
  onSetDefault,
}: ImageGridProps) {
  const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

  if (images.length === 0) {
    return <OperatorState title="暂无图片" detail="开始上传或生成图片。" />;
  }

  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(min(11rem,100%),1fr))] gap-3">
      {images.map((image) => {
        const primarySrc = resolveImageUrl(image);
        const fallbackSrc = (() => {
          const fp = image.file_path || "";
          return fp ? `${API_BASE}${fp.startsWith("/") ? "" : "/"}${fp}` : "";
        })();
        const isAiGenerated = Boolean(
          (image.metadata as { generation_method?: string } | null | undefined)
            ?.generation_method,
        );

        return (
          <div
            key={image.id}
            className="overflow-hidden rounded-lg border border-gray-200 bg-white"
          >
            <ImagePreviewCard
              src={primarySrc}
              fallbackSrc={fallbackSrc}
              alt={`${virtualIP.name} - ${getCategoryLabel(image.category)}`}
              aspectClass="aspect-[3/4]"
              showActionsOnHover
              badges={[
                ...(image.is_default
                  ? [{ label: "默认", tone: "green" as const }]
                  : []),
                ...(isAiGenerated
                  ? [{ label: "AI生成", tone: "blue" as const }]
                  : []),
              ]}
              onPreview={() => onPreview(image)}
              onImg2Img={() => onImg2Img(image)}
              onDelete={() => onDelete(image.id)}
              actions={
                image.is_default
                  ? []
                  : [
                      {
                        label: "设为默认",
                        onClick: () => onSetDefault(image.id),
                        tone: "primary",
                      },
                    ]
              }
            />
            <div className="p-2.5">
              <div className="mb-1.5 flex items-center justify-between gap-2">
                <span className="truncate text-xs font-semibold text-gray-900">
                  {getCategoryLabel(image.category)}
                </span>
                <span className="shrink-0 text-[11px] text-gray-500">
                  {new Date(image.created_at).toLocaleDateString()}
                </span>
              </div>
              {image.tags.length > 0 && (
                <div className="mb-2">
                  <div className="flex flex-wrap gap-1">
                    {image.tags.slice(0, 2).map((tag, index) => (
                      <span
                        key={index}
                        className="rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 text-[11px] text-gray-600"
                      >
                        {tag}
                      </span>
                    ))}
                    {image.tags.length > 2 && (
                      <span className="text-[11px] text-gray-500">
                        +{image.tags.length - 2}
                      </span>
                    )}
                  </div>
                </div>
              )}
              <StyleDetailsSection generationParams={image.generation_params} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface StyleDetailsSectionProps {
  generationParams?: Record<string, unknown> | null;
}

function StyleDetailsSection({ generationParams }: StyleDetailsSectionProps) {
  if (!generationParams || Object.keys(generationParams).length === 0)
    return null;

  const presetId =
    typeof generationParams.style_preset_id === "string"
      ? generationParams.style_preset_id
      : null;
  const spec = generationParams.style_spec;
  const resolution = generationParams.style_spec_resolution;

  if (!presetId && !spec && !resolution) return null;

  return (
    <details className="mb-3 rounded border border-gray-200 bg-gray-50 p-2 text-[11px] text-gray-700">
      <summary className="cursor-pointer select-none text-xs font-medium text-gray-700">
        风格详情
      </summary>
      <div className="mt-2 break-all">预设：{presetId || "—"}</div>
      <div className="mt-1 break-all">规格：{JSON.stringify(spec ?? null)}</div>
      <div className="mt-1 break-all">
        分辨率：{JSON.stringify(resolution ?? null)}
      </div>
    </details>
  );
}
