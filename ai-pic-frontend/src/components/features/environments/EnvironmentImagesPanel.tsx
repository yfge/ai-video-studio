import { ImagePreviewCard } from "@/components/shared";
import type { EnvironmentImage } from "./types";

interface EnvironmentImagesPanelProps {
  envName: string;
  images: EnvironmentImage[];
  imageSrc: (url: string) => string;
  onImg2Img: (image: EnvironmentImage) => void;
  onDelete: (url: string) => void;
  variant?: "card" | "embedded";
}

export function EnvironmentImagesPanel({
  envName,
  images,
  imageSrc,
  onImg2Img,
  onDelete,
  variant = "card",
}: EnvironmentImagesPanelProps) {
  const containerClassName =
    variant === "embedded"
      ? "space-y-4"
      : "bg-white rounded-2xl shadow-sm ring-1 ring-gray-200 p-6 space-y-4 lg:col-span-2";

  return (
    <div className={containerClassName}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">参考图</h3>
        <span className="text-sm text-gray-500">共 {images.length} 张</span>
      </div>
      {images.length === 0 ? (
        <div className="py-8 text-center text-gray-500">
          还没有参考图，上传或生成一张试试。
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {images.map((img) => (
            <ImagePreviewCard
              key={img.url}
              src={imageSrc(img.url)}
              alt={envName}
              showActionsOnHover
              onImg2Img={() => onImg2Img(img)}
              onDelete={() => onDelete(img.url)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
