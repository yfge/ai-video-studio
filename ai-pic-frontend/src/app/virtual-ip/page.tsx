"use client";

import { AuthGuard, OperatorPanel, OperatorShell } from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  VirtualIPCreateModal,
  VirtualIPListSection,
} from "@/components/features/virtual-ip";
import { useVirtualIPCreateForm } from "@/hooks/useVirtualIPCreateForm";
import { useVirtualIPList } from "@/hooks/useVirtualIPList";

function VirtualIPListContent() {
  const { showAlert } = useAlertModal();
  const {
    virtualIPs,
    loading,
    searchTerm,
    setSearchTerm,
    selectedTags,
    toggleTag,
    allTags,
    handleDeleteIP,
    prependVirtualIP,
  } = useVirtualIPList({ showAlert });

  const {
    showCreateForm,
    setShowCreateForm,
    aiGenerating,
    aiBrief,
    setAiBrief,
    formState,
    setFormState,
    handleCreateIP,
    addTag,
    removeTag,
    runGenerateAllAI,
    handleCloseCreateForm,
  } = useVirtualIPCreateForm({ showAlert, onCreated: prependVirtualIP });

  return (
    <OperatorShell
      title="IP 项目"
      subtitle="IP 资产是故事、剧集和生成任务的入口"
      breadcrumb={["IP 中心", "IP 项目"]}
    >
      <OperatorPanel className="mb-5 p-4">
        <h2 className="text-sm font-semibold text-gray-950">生产入口</h2>
        <p className="mt-1 text-xs text-gray-500">
          IP 资产用于组织角色、故事和剧集；新故事优先从这里选择角色资产。
        </p>
      </OperatorPanel>

      <VirtualIPListSection
        loading={loading}
        virtualIPs={virtualIPs}
        searchTerm={searchTerm}
        onSearchTermChange={setSearchTerm}
        allTags={allTags}
        selectedTags={selectedTags}
        onToggleTag={toggleTag}
        onOpenCreate={() => setShowCreateForm(true)}
        onDelete={handleDeleteIP}
      />

      <VirtualIPCreateModal
        open={showCreateForm}
        onClose={handleCloseCreateForm}
        onSubmit={handleCreateIP}
        showAlert={showAlert}
        aiBrief={aiBrief}
        setAiBrief={setAiBrief}
        aiGenerating={aiGenerating}
        onGenerateAI={runGenerateAllAI}
        formState={formState}
        setFormState={setFormState}
        addTag={addTag}
        removeTag={removeTag}
      />
    </OperatorShell>
  );
}

export default function VirtualIPList() {
  return (
    <AuthGuard>
      <VirtualIPListContent />
    </AuthGuard>
  );
}
