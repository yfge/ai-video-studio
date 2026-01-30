"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";

type ImagePreviewModalProps = {
  open: boolean;
  src: string;
  alt?: string;
  onClose: () => void;
  description?: string;
};

/**
 * Lightweight image preview overlay used across grids (虚拟IP / 环境 / 分镜).
 */
export function ImagePreviewModal({
  open,
  src,
  alt,
  onClose,
  description,
}: ImagePreviewModalProps) {
  const backdropRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4"
      onClick={(e) => {
        if (e.target === backdropRef.current) {
          onClose();
        }
      }}
    >
      <div className="relative max-h-[90vh] max-w-6xl w-full">
        <button
          aria-label="关闭预览"
          onClick={onClose}
          className="absolute right-2 top-2 z-10 rounded-full bg-black/60 px-3 py-1 text-sm text-white hover:bg-black/80"
        >
          关闭
        </button>
        <div className="overflow-hidden rounded-lg bg-gray-900 shadow-2xl">
          <div className="relative w-full" style={{ aspectRatio: "3 / 2" }}>
            <Image
              src={src}
              alt={alt || "图片预览"}
              fill
              className="object-contain"
              sizes="100vw"
              unoptimized
            />
          </div>
          {description && (
            <div className="bg-black/70 px-4 py-3 text-sm text-gray-100">
              {description}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
