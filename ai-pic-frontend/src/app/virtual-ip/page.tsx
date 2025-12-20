'use client'

import { AuthGuard } from '@/components/shared'
import { Navigation } from '@/components/layouts'
import { useAlertModal } from '@/components/shared/modals/AlertModalProvider'
import { VirtualIPCreateModal, VirtualIPListSection } from '@/components/features/virtual-ip'
import { useVirtualIPCreateForm } from '@/hooks/useVirtualIPCreateForm'
import { useVirtualIPList } from '@/hooks/useVirtualIPList'

function VirtualIPListContent() {
  const { showAlert } = useAlertModal()
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
  } = useVirtualIPList({ showAlert })

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
  } = useVirtualIPCreateForm({ showAlert, onCreated: prependVirtualIP })

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation title="虚拟IP管理" />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
      </main>

      <VirtualIPCreateModal
        open={showCreateForm}
        onClose={handleCloseCreateForm}
        onSubmit={handleCreateIP}
        aiBrief={aiBrief}
        setAiBrief={setAiBrief}
        aiGenerating={aiGenerating}
        onGenerateAI={runGenerateAllAI}
        formState={formState}
        setFormState={setFormState}
        addTag={addTag}
        removeTag={removeTag}
      />
    </div>
  )
}

export default function VirtualIPList() {
  return (
    <AuthGuard>
      <VirtualIPListContent />
    </AuthGuard>
  )
}
