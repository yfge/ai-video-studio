"use client";

import { useState } from "react";
import type { Script, ScriptGenerationRequest } from "@/utils/api/types";
import { ScriptOverviewTab, ScriptScenesTab } from "@/components/features";
import { OperatorPanel, OperatorSectionHeader } from "@/components/shared";
import { ScriptGenerationForm } from "./ScriptGenerationForm";
import {
  ScriptRegenerateModal,
  ScriptTabToolbar,
} from "./WorkspaceScriptTabContentParts";
import { useWorkspaceScriptStructure } from "./useWorkspaceScriptStructure";

interface WorkspaceScriptTabContentProps {
  script: Script | null;
  // Script generation props
  generateForm: ScriptGenerationRequest;
  setGenerateForm: React.Dispatch<
    React.SetStateAction<ScriptGenerationRequest>
  >;
  formats: Array<{ value: string; label: string }>;
  languages: Array<{ value: string; label: string }>;
  useAsync: boolean;
  setUseAsync: (value: boolean) => void;
  promptPreview: string;
  setPromptPreview: React.Dispatch<React.SetStateAction<string>>;
  generating: boolean;
  onGenerate: () => void;
  // Regeneration
  onRegenerateScript?: (model?: string) => void;
  regenerating?: boolean;
}

export function WorkspaceScriptTabContent({
  script,
  generateForm,
  setGenerateForm,
  formats,
  languages,
  useAsync,
  setUseAsync,
  promptPreview,
  setPromptPreview,
  generating,
  onGenerate,
  onRegenerateScript,
  regenerating,
}: WorkspaceScriptTabContentProps) {
  const [activeSubTab, setActiveSubTab] = useState<"overview" | "scenes">(
    "scenes",
  );
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [regenerateModel, setRegenerateModel] = useState<string>("");
  const structure = useWorkspaceScriptStructure(script);
  const {
    scenes,
    dialogues,
    directions,
    focusedScene,
    setFocusedScene,
    activeScene,
    selectedNormalizedScene,
    sceneBeats,
    sceneShots,
    structureLoading,
    structureError,
    showStructureEditor,
    setShowStructureEditor,
    canEditStructure,
    setStructuredScenes,
  } = structure;

  if (!script) {
    return (
      <OperatorPanel>
        <OperatorSectionHeader
          title="生成剧本"
          subtitle="请配置参数并生成剧本以继续工作流"
        />
        <div className="p-4">
          <ScriptGenerationForm
            generateForm={generateForm}
            setGenerateForm={setGenerateForm}
            formats={formats}
            languages={languages}
            useAsync={useAsync}
            setUseAsync={setUseAsync}
            promptPreview={promptPreview}
            setPromptPreview={setPromptPreview}
            generating={generating}
            onGenerate={onGenerate}
            onCancel={() => {}}
          />
        </div>
      </OperatorPanel>
    );
  }

  return (
    <div className="space-y-4">
      <ScriptTabToolbar
        activeSubTab={activeSubTab}
        setActiveSubTab={setActiveSubTab}
        onOpenRegenerate={() => setShowRegenerateModal(true)}
        regenerating={regenerating}
        canRegenerate={Boolean(onRegenerateScript)}
      />
      <ScriptRegenerateModal
        open={showRegenerateModal}
        model={regenerateModel}
        setModel={setRegenerateModel}
        regenerating={regenerating}
        onCancel={() => {
          setShowRegenerateModal(false);
          setRegenerateModel("");
        }}
        onConfirm={() => {
          setShowRegenerateModal(false);
          onRegenerateScript?.(regenerateModel || undefined);
          setRegenerateModel("");
        }}
      />

      {activeSubTab === "overview" && (
        <ScriptOverviewTab
          script={script}
          scenes={scenes}
          dialogues={dialogues}
          directions={directions}
        />
      )}

      {activeSubTab === "scenes" && (
        <ScriptScenesTab
          script={script}
          scenes={scenes}
          dialogues={dialogues}
          directions={directions}
          focusedScene={focusedScene}
          setFocusedScene={setFocusedScene}
          activeScene={activeScene}
          selectedNormalizedScene={selectedNormalizedScene}
          sceneBeats={sceneBeats}
          sceneShots={sceneShots}
          structureLoading={structureLoading}
          structureError={structureError}
          showStructureEditor={showStructureEditor}
          setShowStructureEditor={setShowStructureEditor}
          canEditStructure={canEditStructure}
          setStructuredScenes={setStructuredScenes}
        />
      )}
    </div>
  );
}
