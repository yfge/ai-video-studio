"use client";

import Image from "next/image";

interface ImageToImagePreviewOverlayProps {
  src: string | null;
  onClose: () => void;
}

export function ImageToImagePreviewOverlay({
  src,
  onClose,
}: ImageToImagePreviewOverlayProps) {
  if (!src) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
      <div className="relative max-h-[90vh] max-w-5xl w-full">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-3 top-3 z-10 rounded bg-black/70 px-3 py-1 text-sm text-white hover:bg-black/90"
        >
          关闭
        </button>
        <div className="relative w-full" style={{ paddingBottom: "60%" }}>
          <Image
            src={src}
            alt="参考图预览"
            fill
            className="object-contain"
            unoptimized
          />
        </div>
      </div>
    </div>
  );
}
