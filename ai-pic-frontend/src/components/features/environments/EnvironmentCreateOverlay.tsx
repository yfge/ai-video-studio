"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  CreationOverlay,
  operatorButtonClass,
  operatorInputClass,
  operatorSelectClass,
} from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { storyStructureAPI } from "@/utils/api/endpoints";
import type { Environment, EnvironmentCreate } from "@/utils/api/types";

import { EnvironmentGenerationFields } from "./EnvironmentGenerationFields";
import {
  EMPTY_ENV_FORM,
  EMPTY_GENERATION,
  type EnvironmentFormState,
  type GenerationFormState,
} from "./types";

interface EnvironmentCreateOverlayProps {
  open: boolean;
  onClose: () => void;
  onCreated: (env: Environment) => void;
}

export function EnvironmentCreateOverlay({
  open,
  onClose,
  onCreated,
}: EnvironmentCreateOverlayProps) {
  const { showAlert } = useAlertModal();
  const [formState, setFormState] =
    useState<EnvironmentFormState>(EMPTY_ENV_FORM);
  const [generation, setGeneration] =
    useState<GenerationFormState>(EMPTY_GENERATION);
  const [creating, setCreating] = useState(false);

  const resetForm = useCallback(() => {
    setFormState(EMPTY_ENV_FORM);
    setGeneration(EMPTY_GENERATION);
  }, []);

  useEffect(() => {
    if (!open) {
      resetForm();
    }
  }, [open, resetForm]);

  const updateField = <K extends keyof EnvironmentFormState>(
    key: K,
    value: EnvironmentFormState[K],
  ) => {
    setFormState((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!formState.name.trim()) {
      showAlert({ message: "请填写名称", variant: "warning" });
      return;
    }

    try {
      setCreating(true);
      const payload: EnvironmentCreate = {
        name: formState.name.trim(),
        category: formState.category || undefined,
        tags: formState.tags?.filter(Boolean),
        description: formState.description?.trim() || undefined,
        reference_images: formState.reference_images?.filter(Boolean),
      };
      const res = await storyStructureAPI.createEnvironment(payload);
      if (!res.success || !res.data) {
        showAlert({ message: res.error || "创建失败", variant: "error" });
        return;
      }

      const created = res.data;
      onCreated(created);

      if (generation.enabled) {
        const envKey = created.business_id || created.id;
        const genRes = await storyStructureAPI.generateEnvironmentImagesAsync(
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
          },
        );
        if (genRes.success) {
          showAlert({
            message: "创建成功，已提交参考图生成任务",
            variant: "success",
          });
        } else {
          showAlert({
            message: `创建成功，但生成任务提交失败：${
              genRes.error || "请稍后重试"
            }`,
            variant: "warning",
          });
        }
      } else {
        showAlert({ message: "创建成功", variant: "success" });
      }

      resetForm();
      onClose();
    } catch (error) {
      console.error(error);
      showAlert({ message: "创建失败", variant: "error" });
    } finally {
      setCreating(false);
    }
  };

  return (
    <CreationOverlay
      open={open}
      title="创建环境"
      subtitle="环境资产池与 IP 生产链路迁移中"
      onClose={onClose}
      widthClassName="max-w-5xl"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
          环境资产暂未完全迁移到 IP 生产链路，创建后将先进入环境资产池。
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-700">
              名称 *
            </label>
            <input
              type="text"
              value={formState.name}
              onChange={(e) => updateField("name", e.target.value)}
              className={operatorInputClass("w-full")}
              placeholder="如：办公室、校园、商场"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-700">
              类别
            </label>
            <select
              value={formState.category}
              onChange={(e) => updateField("category", e.target.value)}
              className={operatorSelectClass("w-full")}
            >
              <option value="indoor">室内</option>
              <option value="outdoor">室外</option>
              <option value="other">其它</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-700">
              标签（逗号分隔）
            </label>
            <input
              type="text"
              value={(formState.tags || []).join(", ")}
              onChange={(e) =>
                updateField(
                  "tags",
                  e.target.value
                    .split(",")
                    .map((t) => t.trim())
                    .filter(Boolean),
                )
              }
              className={operatorInputClass("w-full")}
              placeholder="现代, 写字楼, 开放式"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-700">
              参考图 URL（逗号分隔）
            </label>
            <input
              type="text"
              value={(formState.reference_images || []).join(", ")}
              onChange={(e) =>
                updateField(
                  "reference_images",
                  e.target.value
                    .split(",")
                    .map((t) => t.trim())
                    .filter(Boolean),
                )
              }
              className={operatorInputClass("w-full")}
              placeholder="http://.../bg1.png, http://.../bg2.png"
            />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-700">
            描述
          </label>
          <textarea
            value={formState.description}
            onChange={(e) => updateField("description", e.target.value)}
            className={operatorInputClass(
              "h-auto min-h-20 w-full py-2 text-sm",
            )}
            rows={3}
            placeholder="简述环境特点、光线、风格等"
          />
        </div>

        <EnvironmentGenerationFields
          envKey=""
          generation={generation}
          setGeneration={setGeneration}
        />

        <div className="flex justify-end gap-3 border-t pt-4">
          <button
            type="button"
            onClick={() => {
              resetForm();
              onClose();
            }}
            className={operatorButtonClass("secondary")}
          >
            取消
          </button>
          <button
            type="submit"
            disabled={creating}
            className={operatorButtonClass("primary")}
          >
            {creating ? "创建中..." : "创建环境"}
          </button>
        </div>
      </form>
    </CreationOverlay>
  );
}
