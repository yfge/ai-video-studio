"use client";

import { useState } from "react";
import type { TabKey } from "@/hooks/episode/useEpisodeWorkspaceController";

const timelineHeaderSupportButtonClass =
  "flex h-7 w-full items-center rounded px-2 text-left text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 hover:text-gray-950";

export function SupportViewMenu({
  onNavigateBack,
  onTabChange,
}: {
  onNavigateBack: () => void;
  onTabChange: (tab: TabKey) => void;
}) {
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);
  const navigateTab = (tab: TabKey) => {
    onTabChange(tab);
    close();
  };

  return (
    <div
      className="relative"
      onBlur={(event) => {
        const nextTarget = event.relatedTarget as Node | null;
        if (!nextTarget || !event.currentTarget.contains(nextTarget)) {
          close();
        }
      }}
    >
      <button
        type="button"
        aria-expanded={open}
        aria-label="支持视图"
        title="支持视图"
        onClick={() => setOpen((value) => !value)}
        data-support-view-trigger="icon"
        className="inline-flex h-6 w-6 items-center justify-center rounded-md text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-950 min-[760px]:h-8 min-[760px]:w-8"
      >
        <SupportViewIcon />
      </button>
      {open ? (
        <div className="absolute right-0 top-8 z-20 w-40 rounded-md border border-gray-200 bg-white p-1 shadow-lg min-[760px]:top-9">
          <button
            type="button"
            onClick={() => {
              onNavigateBack();
              close();
            }}
            className={timelineHeaderSupportButtonClass}
          >
            返回故事
          </button>
          <button
            type="button"
            onClick={() => navigateTab("script")}
            className={timelineHeaderSupportButtonClass}
          >
            剧本设置
          </button>
          <button
            type="button"
            onClick={() => navigateTab("storyboard")}
            className={timelineHeaderSupportButtonClass}
          >
            分镜参考
          </button>
          <button
            type="button"
            onClick={() => navigateTab("characters")}
            className={timelineHeaderSupportButtonClass}
          >
            临时角色/IP 绑定
          </button>
        </div>
      ) : null}
    </div>
  );
}

function SupportViewIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 20 20">
      <path
        d="M5 6h10M5 10h10M5 14h6"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.6"
      />
    </svg>
  );
}
