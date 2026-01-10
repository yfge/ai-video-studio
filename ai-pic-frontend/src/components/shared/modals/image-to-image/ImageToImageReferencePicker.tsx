"use client";

import Image from "next/image";

import type { ReferenceSection } from "./types";

interface ImageToImageReferencePickerProps {
  referenceSections: ReferenceSection[];
  selectedRefs: string[];
  lockSelection: boolean;
  onToggle: (url: string) => void;
  onPreview: (url: string) => void;
}

export function ImageToImageReferencePicker({
  referenceSections,
  selectedRefs,
  lockSelection,
  onToggle,
  onPreview,
}: ImageToImageReferencePickerProps) {
  if (referenceSections.length === 0) return null;

  return (
    <div className="mt-4 space-y-3">
      {referenceSections.map((section, idx) => (
        <div key={idx}>
          {section.title ? (
            <div className="text-xs font-medium text-gray-700 mb-2">
              {section.title}
            </div>
          ) : null}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {section.images.map((url) => {
              const selected = selectedRefs.includes(url);
              return (
                <div
                  key={url}
                  className={`relative overflow-hidden rounded border ${
                    selected ? "ring-2 ring-blue-500" : "border-gray-200"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => onToggle(url)}
                    disabled={lockSelection}
                    className="relative block w-full disabled:cursor-not-allowed"
                  >
                    <div className="relative h-28 w-full">
                      <Image
                        src={url}
                        alt={section.title || "参考图"}
                        fill
                        sizes="100%"
                        className="object-cover"
                        unoptimized
                      />
                    </div>
                    {selected ? (
                      <div className="absolute inset-0 bg-blue-500/30 flex items-center justify-center text-white text-xs">
                        已选
                      </div>
                    ) : null}
                  </button>
                  <button
                    type="button"
                    onClick={() => onPreview(url)}
                    className="absolute right-2 top-2 rounded bg-black/60 px-2 py-1 text-[11px] text-white hover:bg-black/80"
                  >
                    预览
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
