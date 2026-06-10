"use client";

import { useState } from "react";

import { operatorButtonClass } from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals";
import {
  GenerationTaskStatusLine,
  useToast,
} from "@/components/shared/notifications";
import { useGenerationTaskTracker } from "@/hooks/useGenerationTaskTracker";
import { storyStructureAPI } from "@/utils/api/endpoints";

import { EnvironmentGenerationFields } from "./EnvironmentGenerationFields";
import { EMPTY_GENERATION, type GenerationFormState } from "./types";

interface EnvironmentSidePanelProps {
  envKey: string;
  onImageUploaded: (imageUrl: string) => void;
  onImagesGenerated?: () => void | Promise<void>;
  variant?: "card" | "embedded";
}

export function EnvironmentSidePanel({
  envKey,
  onImageUploaded,
  onImagesGenerated,
  variant = "card",
}: EnvironmentSidePanelProps) {
  const { showAlert } = useAlertModal();
  const { notify } = useToast();
  const tracker = useGenerationTaskTracker<"environment-images">({
    labels: { "environment-images": "环境参考图" },
    onCompleted: () => onImagesGenerated?.(),
    onNotify: notify,
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [generation, setGeneration] = useState<GenerationFormState>({
    ...EMPTY_GENERATION,
    enabled: true,
  });
  const [generating, setGenerating] = useState(false);

  const handleUpload = async () => {
    if (!selectedFile || !envKey) {
      showAlert({ message: "请选择图片文件", variant: "warning" });
      return;
    }
    try {
      setUploading(true);
      const res = await storyStructureAPI.uploadEnvironmentImage(
        envKey,
        selectedFile,
      );
      if (res.success && res.data) {
        onImageUploaded(res.data.url);
        setSelectedFile(null);
        showAlert({ message: "上传成功", variant: "success" });
      } else {
        showAlert({ message: res.error || "上传失败", variant: "error" });
      }
    } catch (error) {
      console.error(error);
      showAlert({ message: "上传失败", variant: "error" });
    } finally {
      setUploading(false);
    }
  };

  const handleGenerate = async () => {
    if (!envKey) {
      showAlert({ message: "环境信息缺失", variant: "warning" });
      return;
    }
    try {
      setGenerating(true);
      const res = await storyStructureAPI.generateEnvironmentImagesAsync(
        envKey,
        {
          prompt: generation.prompt || undefined,
          model: generation.model || undefined,
          generation_profile: generation.generation_profile || undefined,
          count: generation.count,
          size: generation.size || undefined,
          aspect_ratio: generation.aspect_ratio || undefined,
          seed: generation.seed,
          steps: generation.steps,
          cfg_scale: generation.cfg_scale,
          negative_prompt: generation.negative_prompt || undefined,
          style: generation.style || undefined,
          reference_images:
            generation.reference_images.length > 0
              ? generation.reference_images
              : undefined,
        },
      );
      if (res.success && res.data) {
        notify(
          `环境参考图任务已提交 #${res.data.task_id}，完成后自动刷新图片列表`,
          "info",
        );
        tracker.track("environment-images", res.data.task_id);
      } else {
        showAlert({ message: res.error || "生成失败", variant: "error" });
      }
    } catch (error) {
      console.error(error);
      showAlert({ message: "生成失败", variant: "error" });
    } finally {
      setGenerating(false);
    }
  };

  const containerClassName =
    variant === "embedded"
      ? "space-y-5"
      : "space-y-5 rounded-lg border border-gray-200 bg-white p-4";

  return (
    <div className={containerClassName}>
      <div className="min-w-0">
        <h3 className="text-sm font-semibold text-gray-950">上传参考图</h3>
        <p className="mt-0.5 text-xs text-gray-500">
          支持常见图片格式，自动走 OSS 持久化。
        </p>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
          className="mt-3 w-full text-xs text-gray-600"
        />
        <button
          type="button"
          onClick={handleUpload}
          disabled={uploading || !selectedFile}
          className={operatorButtonClass("primary", "mt-3 w-full")}
        >
          {uploading ? "上传中..." : "上传图片"}
        </button>
      </div>

      <div className="min-w-0 space-y-3 border-t border-gray-200 pt-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-950">AI 生成参考图</h3>
          <p className="mt-0.5 text-xs text-gray-500">
            可选提示词，不填则按环境描述生成。
          </p>
        </div>
        <EnvironmentGenerationFields
          envKey={envKey}
          generation={generation}
          setGeneration={setGeneration}
          compact
          showToggle={false}
          withDivider={false}
        />
        <button
          type="button"
          onClick={handleGenerate}
          disabled={generating}
          className={operatorButtonClass("primary", "w-full")}
        >
          {generating ? "提交任务中..." : "创建生成任务"}
        </button>
        <GenerationTaskStatusLine
          label="环境参考图"
          task={tracker.tasks["environment-images"]}
        />
      </div>
    </div>
  );
}
