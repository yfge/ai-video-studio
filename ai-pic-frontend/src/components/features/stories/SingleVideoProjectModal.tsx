"use client";

import { useState, type FormEvent } from "react";
import {
  OperatorModalFrame,
  operatorButtonClass,
  operatorInputClass,
  operatorSelectClass,
  operatorTextareaClass,
} from "@/components/shared";
import { storyAPI } from "@/utils/api/endpoints";
import type { SingleVideoProjectResponse } from "@/utils/api/types";
import { singleVideoProjectTitle } from "@/utils/singleVideoProject";

const initialForm = {
  title: "",
  prompt: "",
  duration_minutes: 3 as 3 | 5,
  aspect_ratio: "9:16" as "9:16" | "16:9",
  style: "",
};

export function SingleVideoProjectModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (project: SingleVideoProjectResponse) => void;
}) {
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const close = () => {
    if (submitting) return;
    setForm(initialForm);
    setError(null);
    onClose();
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const prompt = form.prompt.trim();
    if (!prompt) {
      setError("请先描述要制作的视频");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const response = await storyAPI.createSingleVideoProject({
        title: singleVideoProjectTitle(form.title, prompt),
        prompt,
        duration_minutes: form.duration_minutes,
        aspect_ratio: form.aspect_ratio,
        style: form.style.trim() || undefined,
        start_generation: true,
      });
      if (!response.success || !response.data) {
        setError(response.error || "单条视频创建失败");
        return;
      }
      const project = response.data;
      setForm(initialForm);
      onClose();
      onCreated(project);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <OperatorModalFrame
      title="创建单条视频"
      subtitle="直接生成剧本与 Timeline；Story / Episode 仅作为内部兼容结构。"
      footer={
        <>
          <button
            type="button"
            className={operatorButtonClass("ghost")}
            disabled={submitting}
            onClick={close}
          >
            取消
          </button>
          <button
            type="submit"
            form="single-video-project-form"
            className={operatorButtonClass("primary")}
            disabled={submitting}
          >
            {submitting ? "创建中" : "创建并生成"}
          </button>
        </>
      }
    >
      <form
        id="single-video-project-form"
        className="space-y-3"
        onSubmit={submit}
      >
        <label className="block">
          <span className="text-xs font-semibold text-gray-700">
            视频标题（可选）
          </span>
          <input
            aria-label="视频标题（可选）"
            className={operatorInputClass("mt-1 w-full")}
            placeholder="留空时从描述自动提取"
            value={form.title}
            onChange={(event) => {
              const title = event.target.value;
              setForm((current) => ({ ...current, title }));
            }}
            onInput={(event) => {
              const title = event.currentTarget.value;
              setForm((current) => ({ ...current, title }));
            }}
          />
        </label>
        <label className="block">
          <span className="text-xs font-semibold text-gray-700">视频描述</span>
          <textarea
            aria-label="视频描述"
            className={operatorTextareaClass("mt-1 w-full")}
            placeholder="例如：用轻快科技感介绍一款桌面机器人，包含开场钩子、三项卖点和结尾行动号召"
            value={form.prompt}
            onChange={(event) => {
              const prompt = event.target.value;
              setForm((current) => ({ ...current, prompt }));
            }}
            onInput={(event) => {
              const prompt = event.currentTarget.value;
              setForm((current) => ({ ...current, prompt }));
            }}
          />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label>
            <span className="text-xs font-semibold text-gray-700">时长</span>
            <select
              aria-label="视频时长"
              className={operatorSelectClass("mt-1 w-full")}
              value={form.duration_minutes}
              onChange={(event) => {
                const duration_minutes = Number(event.target.value) as 3 | 5;
                setForm((current) => ({ ...current, duration_minutes }));
              }}
            >
              <option value={3}>3 分钟</option>
              <option value={5}>5 分钟</option>
            </select>
          </label>
          <label>
            <span className="text-xs font-semibold text-gray-700">画幅</span>
            <select
              aria-label="视频画幅"
              className={operatorSelectClass("mt-1 w-full")}
              value={form.aspect_ratio}
              onChange={(event) => {
                const aspect_ratio = event.target.value as "9:16" | "16:9";
                setForm((current) => ({ ...current, aspect_ratio }));
              }}
            >
              <option value="9:16">9:16 竖屏</option>
              <option value="16:9">16:9 横屏</option>
            </select>
          </label>
        </div>
        <label className="block">
          <span className="text-xs font-semibold text-gray-700">
            风格（可选）
          </span>
          <input
            aria-label="视频风格（可选）"
            className={operatorInputClass("mt-1 w-full")}
            placeholder="例如：明亮科技感、纪实、二维动画"
            value={form.style}
            onChange={(event) => {
              const style = event.target.value;
              setForm((current) => ({ ...current, style }));
            }}
            onInput={(event) => {
              const style = event.currentTarget.value;
              setForm((current) => ({ ...current, style }));
            }}
          />
        </label>
        {error ? (
          <div className="text-xs text-red-600" role="alert">
            {error}
          </div>
        ) : null}
      </form>
    </OperatorModalFrame>
  );
}
