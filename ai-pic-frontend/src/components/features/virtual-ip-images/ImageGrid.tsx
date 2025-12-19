"use client";

import type { VirtualIP, VirtualIPImage } from "@/utils/api";
import { ImagePreviewCard } from "@/components/shared";
import { resolveImageUrl } from "@/hooks/useVirtualIPImages";

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
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-6xl mb-4">Image</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Images</h3>
        <p className="text-gray-600">Start uploading or generating images!</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      {images.map((image) => {
        const primarySrc = resolveImageUrl(image);
        const fallbackSrc = (() => {
          const fp = image.file_path || "";
          return fp ? `${API_BASE}${fp.startsWith("/") ? "" : "/"}${fp}` : "";
        })();
        const isAiGenerated = Boolean(
          (image.metadata as { generation_method?: string } | null | undefined)?.generation_method,
        );

        return (
          <div key={image.id} className="bg-white rounded-lg shadow-md overflow-hidden">
            <ImagePreviewCard
              src={primarySrc}
              fallbackSrc={fallbackSrc}
              alt={`${virtualIP.name} - ${image.category}`}
              aspectClass="aspect-[4/5]"
              showActionsOnHover
              badges={[
                ...(image.is_default ? [{ label: "Default", tone: "green" as const }] : []),
                ...(isAiGenerated ? [{ label: "AI Generated", tone: "blue" as const }] : []),
              ]}
              onPreview={() => onPreview(image)}
              onImg2Img={() => onImg2Img(image)}
              onDelete={() => onDelete(image.id)}
              actions={
                image.is_default
                  ? []
                  : [
                      {
                        label: "Set Default",
                        onClick: () => onSetDefault(image.id),
                        tone: "primary",
                      },
                    ]
              }
            />
            <div className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">{image.category}</span>
                <span className="text-xs text-gray-500">
                  {new Date(image.created_at).toLocaleDateString()}
                </span>
              </div>
              {image.tags.length > 0 && (
                <div className="mb-3">
                  <div className="flex flex-wrap gap-1">
                    {image.tags.slice(0, 3).map((tag, index) => (
                      <span
                        key={index}
                        className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                    {image.tags.length > 3 && (
                      <span className="text-gray-500 text-xs">+{image.tags.length - 3}</span>
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
  generationParams: Record<string, unknown> | null;
}

function StyleDetailsSection({ generationParams }: StyleDetailsSectionProps) {
  if (!generationParams || Object.keys(generationParams).length === 0) return null;

  const presetId =
    typeof generationParams.style_preset_id === "string" ? generationParams.style_preset_id : null;
  const spec = generationParams.style_spec;
  const resolution = generationParams.style_spec_resolution;

  if (!presetId && !spec && !resolution) return null;

  return (
    <details className="mb-3 rounded border border-gray-200 bg-gray-50 p-2 text-[11px] text-gray-700">
      <summary className="cursor-pointer select-none text-xs font-medium text-gray-700">
        Style Details
      </summary>
      <div className="mt-2 break-all">preset: {presetId || "—"}</div>
      <div className="mt-1 break-all">spec: {JSON.stringify(spec ?? null)}</div>
      <div className="mt-1 break-all">resolution: {JSON.stringify(resolution ?? null)}</div>
    </details>
  );
}
