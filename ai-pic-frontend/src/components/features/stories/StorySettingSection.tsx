"use client";

import type { Dispatch, SetStateAction } from "react";
import type { VirtualIP } from "@/utils/api/types";
import type { StoryGenerationForm } from "@/utils/storyOptions";
import { CharacterSelector } from "./CharacterSelector";

interface StorySettingSectionProps {
  virtualIPs: VirtualIP[];
  generateForm: StoryGenerationForm;
  setGenerateForm: Dispatch<SetStateAction<StoryGenerationForm>>;
  onCharacterToggle: (characterId: number) => void;
  onNavigateToVirtualIP: () => void;
}

export function StorySettingSection(props: StorySettingSectionProps) {
  const { virtualIPs, generateForm, setGenerateForm } = props;
  return (
    <section className="space-y-4" aria-labelledby="story-seed-setting">
      <div>
        <h2
          id="story-seed-setting"
          className="text-sm font-semibold text-gray-900"
        >
          角色与世界边界
        </h2>
        <p className="mt-1 text-xs text-gray-500">
          创建时冻结所选角色当前公共记忆；不会读取其他 Story 的私有经历。
        </p>
      </div>
      <CharacterSelector
        virtualIPs={virtualIPs}
        selectedIds={generateForm.character_ids}
        onToggle={props.onCharacterToggle}
        onNavigateToVirtualIP={props.onNavigateToVirtualIP}
      />
      <div className="grid gap-4 md:grid-cols-2">
        <TextField
          label="时代"
          value={generateForm.setting_time || ""}
          placeholder="例如：近未来"
          onChange={(setting_time) =>
            setGenerateForm((prev) => ({ ...prev, setting_time }))
          }
        />
        <TextField
          label="地点"
          value={generateForm.setting_location || ""}
          placeholder="例如：沿海工业城"
          onChange={(setting_location) =>
            setGenerateForm((prev) => ({ ...prev, setting_location }))
          }
        />
      </div>
      <TextArea
        label="不可违反的世界规则"
        value={generateForm.world_building || ""}
        placeholder="写清能力、制度、时代或空间限制"
        onChange={(world_building) =>
          setGenerateForm((prev) => ({ ...prev, world_building }))
        }
      />
      <TextArea
        label="内容与合规边界（每行一条）"
        value={(generateForm.content_restrictions || []).join("\n")}
        placeholder="例如：不得美化违法行为"
        onChange={(value) =>
          setGenerateForm((prev) => ({
            ...prev,
            content_restrictions: value
              .split("\n")
              .map((item) => item.trim())
              .filter(Boolean),
          }))
        }
      />
    </section>
  );
}

function TextField(props: {
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-sm font-medium text-gray-700">
      {props.label}
      <input
        value={props.value}
        onChange={(event) => props.onChange(event.target.value)}
        placeholder={props.placeholder}
        className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
      />
    </label>
  );
}

function TextArea(props: {
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block text-sm font-medium text-gray-700">
      {props.label}
      <textarea
        value={props.value}
        onChange={(event) => props.onChange(event.target.value)}
        placeholder={props.placeholder}
        rows={3}
        className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
      />
    </label>
  );
}
