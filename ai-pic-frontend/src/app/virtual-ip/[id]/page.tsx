"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorShell,
  OperatorState,
  operatorButtonClass,
} from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  VirtualIPAdditionalInfoSection,
  VirtualIPInfoSection,
  VirtualIPImageManager,
  VoiceSettingsPanel,
} from "@/components/features";
import { useVirtualIPDetail } from "@/hooks/useVirtualIPDetail";
import {
  ReadinessRow,
  VirtualIPBackgroundStorySection,
  VirtualIPMetaStrip,
  VirtualIPMigrationNotice,
} from "./VirtualIPDetailPageParts";

export default function VirtualIPDetail() {
  const params = useParams();
  const router = useRouter();
  const { showAlert } = useAlertModal();
  const ipKey = params?.id?.toString() || "";
  const editFormId = "virtual-ip-edit-form";
  const state = useVirtualIPDetail({ ipKey, showAlert, router });
  const {
    virtualIP,
    loading,
    editing,
    setEditing,
    editForm,
    setEditForm,
    voiceEnums,
    voiceTypeFilter,
    setVoiceTypeFilter,
    voiceSettings,
    setVoiceSettings,
    voicePreviewText,
    setVoicePreviewText,
    voiceLoading,
    previewLoading,
    previewAudioUrl,
    voiceOptions,
    handleUpdateIP,
    handleDeleteIP,
    addTag,
    removeTag,
    handlePreviewVoice,
  } = state;

  if (loading) {
    return (
      <OperatorShell title="IP 详情" subtitle="加载 IP 资产...">
        <OperatorState title="加载 IP 资产..." />
      </OperatorShell>
    );
  }

  if (!virtualIP) {
    return (
      <OperatorShell
        title="IP 详情"
        subtitle="IP 资产是故事、剧集和生成任务的入口"
      >
        <OperatorState
          title="未找到 IP"
          tone="red"
          action={
            <Link
              href="/virtual-ip"
              className={operatorButtonClass("secondary")}
            >
              返回 IP 项目
            </Link>
          }
        />
      </OperatorShell>
    );
  }

  return (
    <OperatorShell
      title="IP 详情"
      subtitle="IP 资产是故事、剧集和生成任务的入口"
    >
      <div className="space-y-5">
        <VirtualIPMigrationNotice />

        <div className="grid gap-5 2xl:grid-cols-[minmax(0,1fr)_360px]">
          <OperatorPanel>
            <VirtualIPInfoSection
              virtualIP={virtualIP}
              editing={editing}
              editForm={editForm}
              setEditForm={setEditForm}
              onSubmit={handleUpdateIP}
              addTag={addTag}
              removeTag={removeTag}
              formId={editFormId}
            />
            <VirtualIPBackgroundStorySection
              virtualIP={virtualIP}
              editing={editing}
              editForm={editForm}
              setEditForm={setEditForm}
            />
            <VirtualIPAdditionalInfoSection
              virtualIP={virtualIP}
              editing={editing}
              editForm={editForm}
              setEditForm={setEditForm}
            />
            <VoiceSettingsPanel
              editing={editing}
              voiceEnums={voiceEnums}
              voiceTypeFilter={voiceTypeFilter}
              setVoiceTypeFilter={setVoiceTypeFilter}
              voiceSettings={voiceSettings}
              setVoiceSettings={setVoiceSettings}
              voicePreviewText={voicePreviewText}
              setVoicePreviewText={setVoicePreviewText}
              voiceLoading={voiceLoading}
              previewLoading={previewLoading}
              previewAudioUrl={previewAudioUrl}
              voiceOptions={voiceOptions}
              onPreviewVoice={handlePreviewVoice}
            />
            <VirtualIPMetaStrip virtualIP={virtualIP} />
          </OperatorPanel>

          <aside className="space-y-5">
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
                <a
                  href="#ip-images"
                  className={operatorButtonClass("secondary", "w-full")}
                >
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
                  onClick={handleDeleteIP}
                  className="h-8 rounded-md px-2 text-xs font-medium text-red-600 hover:bg-red-50"
                >
                  删除 IP
                </button>
              </div>
            </OperatorPanel>
          </aside>
        </div>

        <VirtualIPImageManager virtualIPKey={ipKey} virtualIP={virtualIP} />
      </div>
    </OperatorShell>
  );
}
