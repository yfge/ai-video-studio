"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  VirtualIPDetailHeader,
  VirtualIPAdditionalInfoSection,
  VirtualIPInfoSection,
  VirtualIPImageManager,
  VoiceSettingsPanel,
} from "@/components/features";
import { useVirtualIPDetail } from "@/hooks/useVirtualIPDetail";
import { CollapsibleText } from "@/components/ui";
import { resolveCreatorLabel } from "@/utils/creator";

export default function VirtualIPDetail() {
  const params = useParams();
  const router = useRouter();
  const { showAlert } = useAlertModal();
  const ipKey = params?.id?.toString() || "";

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
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!virtualIP) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">未找到虚拟IP</h2>
          <Link href="/virtual-ip" className="text-blue-600 hover:text-blue-800">
            返回虚拟IP列表
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <VirtualIPDetailHeader
        ipKey={ipKey}
        businessId={virtualIP.business_id}
        editing={editing}
        setEditing={setEditing}
        onDelete={handleDeleteIP}
      />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="bg-white shadow-sm ring-1 ring-gray-200 rounded-2xl overflow-hidden">
          <VirtualIPInfoSection
            virtualIP={virtualIP}
            editing={editing}
            editForm={editForm}
            setEditForm={setEditForm}
            onSubmit={handleUpdateIP}
            onCancel={() => setEditing(false)}
            addTag={addTag}
            removeTag={removeTag}
          />

          {(editing || virtualIP.background_story) && (
            <div className="p-6 sm:p-8 border-b border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">背景故事</h3>
              {editing ? (
                <textarea
                  value={editForm.background_story}
                  onChange={(e) => setEditForm({ ...editForm, background_story: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={6}
                />
              ) : (
                <div className="prose max-w-none">
                  {virtualIP.background_story ? (
                    <CollapsibleText text={virtualIP.background_story} collapsedLines={4} />
                  ) : (
                    <p className="text-sm text-gray-400">未填写</p>
                  )}
                </div>
              )}
            </div>
          )}

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

          <div className="p-6 sm:p-8 bg-gray-50/60">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
              <div>
                <span className="font-medium">创建者：</span>{" "}
                {resolveCreatorLabel(virtualIP.creator)}
              </div>
              <div>
                <span className="font-medium">创建时间：</span>{" "}
                {new Date(virtualIP.created_at).toLocaleString()}
              </div>
              {virtualIP.updated_at && (
                <div>
                  <span className="font-medium">更新时间：</span>{" "}
                  {new Date(virtualIP.updated_at).toLocaleString()}
                </div>
              )}
            </div>
          </div>
        </div>

        <VirtualIPImageManager virtualIPKey={ipKey} virtualIP={virtualIP} />
      </main>
    </div>
  );
}
