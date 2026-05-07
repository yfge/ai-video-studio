import Link from "next/link";
import type { Dispatch, SetStateAction } from "react";

import {
  OperatorPanel,
  OperatorSectionHeader,
  StatusPill,
  operatorButtonClass,
  operatorInputClass,
} from "@/components/shared";
import { CollapsibleText } from "@/components/ui";
import type { EditFormState } from "@/hooks/useVirtualIPDetail";
import type { VirtualIP } from "@/utils/api/types";
import { resolveCreatorLabel } from "@/utils/creator";

export function VirtualIPMigrationNotice() {
  return (
    <OperatorPanel className="p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs text-blue-700">
          IP 资产已接入新的生产工作台，部分字段仍可编辑。
        </div>
        <Link href="/virtual-ip" className={operatorButtonClass("ghost")}>
          返回 IP 项目
        </Link>
      </div>
    </OperatorPanel>
  );
}

export function VirtualIPBackgroundStorySection({
  virtualIP,
  editing,
  editForm,
  setEditForm,
}: {
  virtualIP: VirtualIP;
  editing: boolean;
  editForm: EditFormState;
  setEditForm: Dispatch<SetStateAction<EditFormState>>;
}) {
  if (!editing && !virtualIP.background_story) return null;
  return (
    <div className="border-b border-gray-100 p-5">
      <h3 className="mb-3 text-sm font-semibold text-gray-950">背景故事</h3>
      {editing ? (
        <textarea
          value={editForm.background_story}
          onChange={(event) =>
            setEditForm({ ...editForm, background_story: event.target.value })
          }
          className={operatorInputClass("h-auto min-h-36 w-full py-2 text-sm")}
          rows={6}
        />
      ) : virtualIP.background_story ? (
        <CollapsibleText text={virtualIP.background_story} collapsedLines={4} />
      ) : (
        <p className="text-sm text-gray-400">未填写</p>
      )}
    </div>
  );
}

export function VirtualIPMetaStrip({ virtualIP }: { virtualIP: VirtualIP }) {
  return (
    <div className="bg-gray-50/60 p-5">
      <div className="grid gap-3 text-xs text-gray-600 md:grid-cols-3">
        <MetaItem label="创建者" value={resolveCreatorLabel(virtualIP.creator)} />
        <MetaItem label="创建时间" value={formatDate(virtualIP.created_at)} />
        <MetaItem
          label="更新时间"
          value={virtualIP.updated_at ? formatDate(virtualIP.updated_at) : "-"}
        />
      </div>
    </div>
  );
}

export function ReadinessRow({
  label,
  ready,
}: {
  label: string;
  ready: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-gray-600">{label}</span>
      <StatusPill tone={ready ? "green" : "amber"}>
        {ready ? "已通过" : "待补充"}
      </StatusPill>
    </div>
  );
}

export function VirtualIPInspectorPanel({
  virtualIP,
  editing,
  editFormId,
  setEditing,
  onDelete,
}: {
  virtualIP: VirtualIP;
  editing: boolean;
  editFormId: string;
  setEditing: (editing: boolean) => void;
  onDelete: () => void;
}) {
  return (
    <aside className="space-y-5 xl:sticky xl:top-20 xl:self-start">
      <OperatorPanel>
        <OperatorSectionHeader title="生产就绪检查" />
        <div className="space-y-3 p-4 text-sm">
          <ReadinessRow label="IP 资料" ready={Boolean(virtualIP.name)} />
          <ReadinessRow
            label="背景故事"
            ready={Boolean(virtualIP.background_story)}
          />
          <ReadinessRow
            label="声音"
            ready={Boolean(virtualIP.voice_config?.voice_id)}
          />
          <ReadinessRow
            label="形象素材"
            ready={Boolean(virtualIP.default_avatar_url)}
          />
        </div>
      </OperatorPanel>
      <OperatorPanel>
        <OperatorSectionHeader title="资产管理" />
        <div className="space-y-3 p-4">
          <a href="#ip-images" className={operatorButtonClass("secondary", "w-full")}>
            图片管理
          </a>
          {editing ? (
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setEditing(false)}
                className={operatorButtonClass("secondary")}
              >
                取消编辑
              </button>
              <button
                type="submit"
                form={editFormId}
                className={operatorButtonClass("primary")}
              >
                保存
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className={operatorButtonClass("primary", "w-full")}
            >
              编辑 IP
            </button>
          )}
          <button
            type="button"
            onClick={onDelete}
            className="h-8 rounded-md px-2 text-xs font-medium text-red-600 hover:bg-red-50"
          >
            删除 IP
          </button>
        </div>
      </OperatorPanel>
    </aside>
  );
}

const formatDate = (value: string) => new Date(value).toLocaleString("zh-CN");

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="font-medium">{label}：</span>
      {value}
    </div>
  );
}
