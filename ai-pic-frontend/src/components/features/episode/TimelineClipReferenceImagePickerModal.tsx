"use client";

import { useEffect, useMemo, useState } from "react";
import { Modal } from "@/components/ui/Modal";
import type { StoryboardReferenceImageOption } from "./TimelineClipStoryboardReferenceImagesModel";

export type ReferenceImagePickerSection = {
  key: string;
  title: string;
  options: StoryboardReferenceImageOption[];
};

export type ReferenceImagePickerGroup = {
  key: string;
  title: string;
  sections: ReferenceImagePickerSection[];
};

export function ReferenceImagePickerModal({
  title,
  ariaPrefix,
  altPrefix,
  groups,
  selectedUrls,
  isOpen,
  onClose,
  onApply,
}: {
  title: string;
  ariaPrefix: string;
  altPrefix: string;
  groups: ReferenceImagePickerGroup[];
  selectedUrls: string[];
  isOpen: boolean;
  onClose: () => void;
  onApply: (urls: string[]) => void;
}) {
  const allOptions = useMemo(
    () => groups.flatMap((group) => group.sections.flatMap((s) => s.options)),
    [groups],
  );
  const allUrls = useMemo(
    () => dedupeUrls(allOptions.map((option) => option.url)),
    [allOptions],
  );
  const [draftUrls, setDraftUrls] = useState<string[]>([]);

  useEffect(() => {
    if (!isOpen) return;
    const allowed = new Set(allUrls);
    setDraftUrls(dedupeUrls(selectedUrls.filter((url) => allowed.has(url))));
  }, [allUrls, isOpen, selectedUrls]);

  const selectedCount = allOptions.filter((option) =>
    draftUrls.includes(option.url),
  ).length;

  const applyDraft = () => {
    onApply(dedupeUrls(draftUrls));
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      maxWidth="max-w-5xl"
      className="max-h-[88vh]"
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-700 hover:bg-white"
          >
            取消
          </button>
          <button
            type="button"
            onClick={() => setDraftUrls([])}
            className="rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-700 hover:bg-white"
          >
            清空
          </button>
          <button
            type="button"
            onClick={applyDraft}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            应用选择
          </button>
        </>
      }
    >
      <div className="sticky top-0 z-10 -mx-6 -mt-6 border-b border-slate-200 bg-white px-6 py-3">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          <span className="font-medium text-slate-700">
            已选 {selectedCount}/{allOptions.length}
          </span>
          <span className="flex items-center gap-3">
            <button
              type="button"
              aria-label={`${title}全选`}
              className="text-blue-600 hover:underline"
              onClick={() => setDraftUrls(allUrls)}
            >
              全选
            </button>
            <button
              type="button"
              aria-label={`${title}清空`}
              className="text-slate-500 hover:underline"
              onClick={() => setDraftUrls([])}
            >
              清空
            </button>
          </span>
        </div>
      </div>
      <div className="mt-4 grid gap-5">
        {groups.length ? (
          groups.map((group) => (
            <section key={group.key} className="grid gap-3">
              <h3 className="text-sm font-semibold text-slate-900">
                {group.title}
              </h3>
              {group.sections.map((section) => (
                <div key={section.key} className="grid gap-2">
                  <div className="text-xs font-medium text-slate-500">
                    {section.title}
                  </div>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
                    {section.options.map((option) => {
                      const selected = draftUrls.includes(option.url);
                      return (
                        <button
                          key={option.url}
                          type="button"
                          aria-pressed={selected}
                          aria-label={`${ariaPrefix} ${option.label}`}
                          onClick={() =>
                            setDraftUrls((prev) =>
                              toggleUrl(prev, option.url, !selected),
                            )
                          }
                          className={[
                            "overflow-hidden rounded-md border bg-white text-left shadow-sm",
                            selected
                              ? "border-blue-500 ring-2 ring-blue-100"
                              : "border-slate-200 hover:border-slate-300",
                          ].join(" ")}
                        >
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={option.url}
                            alt={`${altPrefix} ${option.label}`}
                            className="aspect-square w-full object-cover"
                          />
                          <span className="block truncate px-1.5 py-1 text-[11px] text-slate-600">
                            {option.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </section>
          ))
        ) : (
          <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-8 text-center text-sm text-slate-500">
            暂无可选图片
          </div>
        )}
      </div>
    </Modal>
  );
}

function toggleUrl(previous: string[], url: string, checked: boolean) {
  if (checked) return dedupeUrls([...previous, url]);
  return previous.filter((item) => item !== url);
}

function dedupeUrls(values: string[]) {
  const next: string[] = [];
  for (const value of values) {
    if (!value || next.includes(value)) continue;
    next.push(value);
  }
  return next;
}
