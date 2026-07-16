"use client";

import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  operatorButtonClass,
  operatorSelectClass,
} from "@/components/shared";
import { GENRES, STATUSES } from "@/hooks/useStories";
import type { Story } from "@/utils/api/types";
import { StoryProjectCard } from "./StoryProjectCard";

interface StoryListSectionProps {
  stories: Story[];
  loading: boolean;
  selectedGenre: string;
  onSelectedGenreChange: (value: string) => void;
  selectedStatus: string;
  onSelectedStatusChange: (value: string) => void;
  onOpenSingleVideoForm: () => void;
  onOpenGenerateForm: () => void;
  onDelete: (businessId: string) => void;
}

export function StoryListSection({
  stories,
  loading,
  selectedGenre,
  onSelectedGenreChange,
  selectedStatus,
  onSelectedStatusChange,
  onOpenSingleVideoForm,
  onOpenGenerateForm,
  onDelete,
}: StoryListSectionProps) {
  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="项目列表"
        subtitle={`${stories.length} 个项目`}
        action={
          <StoryFilters
            selectedGenre={selectedGenre}
            onSelectedGenreChange={onSelectedGenreChange}
            selectedStatus={selectedStatus}
            onSelectedStatusChange={onSelectedStatusChange}
          />
        }
      />

      {loading ? (
        <div className="p-4">
          <OperatorState title="加载故事列表..." />
        </div>
      ) : stories.length === 0 ? (
        <StoryEmptyState
          onOpenSingleVideoForm={onOpenSingleVideoForm}
          onOpenGenerateForm={onOpenGenerateForm}
        />
      ) : (
        <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">
          {stories.map((story) => (
            <StoryProjectCard
              key={story.business_id || story.id}
              story={story}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </OperatorPanel>
  );
}

function StoryFilters({
  selectedGenre,
  onSelectedGenreChange,
  selectedStatus,
  onSelectedStatusChange,
}: {
  selectedGenre: string;
  onSelectedGenreChange: (value: string) => void;
  selectedStatus: string;
  onSelectedStatusChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <select
        value={selectedGenre}
        onChange={(event) => onSelectedGenreChange(event.target.value)}
        className={operatorSelectClass("w-32")}
        aria-label="按类型筛选故事"
      >
        <option value="">全部类型</option>
        {GENRES.map((genre) => (
          <option key={genre.value} value={genre.value}>
            {genre.label}
          </option>
        ))}
      </select>
      <select
        value={selectedStatus}
        onChange={(event) => onSelectedStatusChange(event.target.value)}
        className={operatorSelectClass("w-32")}
        aria-label="按状态筛选故事"
      >
        <option value="">全部状态</option>
        {STATUSES.map((status) => (
          <option key={status.value} value={status.value}>
            {status.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function StoryEmptyState({
  onOpenSingleVideoForm,
  onOpenGenerateForm,
}: {
  onOpenSingleVideoForm: () => void;
  onOpenGenerateForm: () => void;
}) {
  return (
    <div className="p-4">
      <OperatorState
        title="暂无视频项目"
        detail="直接创建 3–5 分钟单条视频，或从 IP 开始制作系列内容。"
        action={
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onOpenSingleVideoForm}
              className={operatorButtonClass("primary")}
            >
              创建单条视频
            </button>
            <button
              type="button"
              onClick={onOpenGenerateForm}
              className={operatorButtonClass("secondary")}
            >
              创建系列故事
            </button>
          </div>
        }
      />
    </div>
  );
}
