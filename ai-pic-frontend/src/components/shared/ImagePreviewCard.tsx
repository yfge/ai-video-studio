"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

type Badge = { label: string; tone?: "blue" | "green" | "red" | "gray" };
type Action = {
  label: string;
  onClick: () => void;
  tone?: "default" | "primary" | "danger";
};

interface ImagePreviewCardProps {
  src: string;
  alt?: string;
  fallbackSrc?: string;
  aspectClass?: string;
  badges?: Badge[];
  actions?: Action[];
  onPreview?: () => void;
  onImg2Img?: () => void;
  onDelete?: () => void;
  img2imgLabel?: string;
  deleteLabel?: string;
  footer?: React.ReactNode;
  showActionsOnHover?: boolean;
}

const toneStyles: Record<NonNullable<Badge["tone"]>, string> = {
  blue: "bg-blue-600 text-white",
  green: "bg-green-600 text-white",
  red: "bg-red-600 text-white",
  gray: "bg-gray-700 text-white",
};

const actionStyles: Record<NonNullable<Action["tone"]>, string> = {
  default: "bg-black/60 hover:bg-black/80 text-white",
  primary: "bg-blue-600 hover:bg-blue-700 text-white",
  danger: "bg-red-600 hover:bg-red-700 text-white",
};

export function ImagePreviewCard({
  src,
  alt,
  fallbackSrc,
  aspectClass = "aspect-square",
  badges = [],
  actions = [],
  onPreview,
  onImg2Img,
  onDelete,
  img2imgLabel = "图生图",
  deleteLabel = "删除",
  footer,
  showActionsOnHover = true,
}: ImagePreviewCardProps) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(src);
  const [imageFailed, setImageFailed] = useState(!src);

  useEffect(() => {
    setCurrentSrc(src);
    setImageFailed(!src);
  }, [src]);

  const handlePreview = () => {
    if (onPreview) {
      onPreview();
    } else {
      setPreviewOpen(true);
    }
  };

  const allActions: Action[] = [
    ...(onImg2Img
      ? [{ label: img2imgLabel, onClick: onImg2Img, tone: "primary" as const }]
      : []),
    ...(onDelete
      ? [{ label: deleteLabel, onClick: onDelete, tone: "danger" as const }]
      : []),
    ...actions,
  ];

  return (
    <div className="relative rounded-lg border border-gray-100 bg-white shadow-sm">
      <div
        className={`relative overflow-hidden ${aspectClass} cursor-zoom-in group`}
        onClick={handlePreview}
      >
        {imageFailed ? (
          <div className="flex h-full w-full items-center justify-center bg-gray-50 text-xs text-gray-400">
            图片不可用
          </div>
        ) : (
          <Image
            src={currentSrc}
            alt={alt || "图片"}
            fill
            sizes="100%"
            className="object-cover"
            unoptimized
            onError={() => {
              if (fallbackSrc && currentSrc !== fallbackSrc) {
                setCurrentSrc(fallbackSrc);
                return;
              }
              setImageFailed(true);
            }}
          />
        )}
        {badges.length > 0 && (
          <div className="absolute left-2 top-2 flex flex-wrap gap-1">
            {badges.map((b, idx) => (
              <span
                key={`${b.label}-${idx}`}
                className={`rounded px-2 py-1 text-[11px] ${
                  toneStyles[b.tone || "gray"]
                }`}
              >
                {b.label}
              </span>
            ))}
          </div>
        )}
        {allActions.length > 0 && (
          <div
            className={`absolute inset-x-0 bottom-0 flex flex-wrap gap-2 p-2 ${
              showActionsOnHover ? "opacity-0 group-hover:opacity-100" : ""
            } transition-opacity`}
          >
            {allActions.map((action, idx) => (
              <button
                key={`${action.label}-${idx}`}
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  action.onClick();
                }}
                className={`rounded px-3 py-1 text-xs font-medium ${
                  actionStyles[action.tone || "default"]
                }`}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
      {footer ? <div className="p-3">{footer}</div> : null}

      {previewOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
          <div className="relative max-h-[90vh] max-w-6xl w-full">
            <button
              type="button"
              onClick={() => setPreviewOpen(false)}
              className="absolute right-3 top-3 z-10 rounded bg-black/70 px-3 py-1 text-sm text-white hover:bg-black/90"
            >
              关闭
            </button>
            <div className="relative w-full" style={{ paddingBottom: "60%" }}>
              <Image
                src={currentSrc}
                alt={alt || "预览图"}
                fill
                className="object-contain"
                unoptimized
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
