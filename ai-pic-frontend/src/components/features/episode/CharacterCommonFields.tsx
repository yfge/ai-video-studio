"use client";

import type { Dispatch, SetStateAction } from "react";
import type {
  EpisodeCharacterCreate,
  EpisodeCharacterUpdate,
} from "@/utils/api/types";

export function CharacterCommonFields<
  T extends EpisodeCharacterCreate | EpisodeCharacterUpdate,
>({
  formData,
  setFormData,
}: {
  formData: T;
  setFormData: Dispatch<SetStateAction<T>>;
}) {
  return (
    <>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          角色名称 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          required
          value={formData.character_name || ""}
          onChange={(e) =>
            setFormData({ ...formData, character_name: e.target.value })
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="例如：快递员、医生、路人甲"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            角色类型
          </label>
          <select
            value={formData.role_type || "temporary"}
            onChange={(e) =>
              setFormData({ ...formData, role_type: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="temporary">临时角色</option>
            <option value="guest">客串</option>
            <option value="extra">群众演员</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            重要度 (1-5)
          </label>
          <input
            type="number"
            min="1"
            max="5"
            value={formData.importance || 1}
            onChange={(e) =>
              setFormData({
                ...formData,
                importance: Number(e.target.value),
              })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          性格描述
        </label>
        <textarea
          value={formData.personality || ""}
          onChange={(e) =>
            setFormData({ ...formData, personality: e.target.value })
          }
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="例如：热情、乐观、工作认真"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          背景故事
        </label>
        <textarea
          value={formData.background || ""}
          onChange={(e) =>
            setFormData({ ...formData, background: e.target.value })
          }
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="例如：快递公司员工，负责本小区配送"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          外观补充描述
        </label>
        <textarea
          value={formData.appearance_override || ""}
          onChange={(e) =>
            setFormData({ ...formData, appearance_override: e.target.value })
          }
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="例如：穿着统一制服，背着快递包"
        />
      </div>
    </>
  );
}
