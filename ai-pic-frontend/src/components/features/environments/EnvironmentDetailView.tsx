"use client";

import { useParams, useRouter } from "next/navigation";

import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorShell,
  OperatorState,
} from "@/components/shared";

import { EnvironmentHeader } from "./EnvironmentHeader";
import { EnvironmentImagesPanel } from "./EnvironmentImagesPanel";
import { EnvironmentSidePanel } from "./EnvironmentSidePanel";
import { useEnvironmentDetailState } from "./EnvironmentDetailState";
import { EnvironmentVariantModal } from "./EnvironmentVariantModal";
import {
  EnvironmentAuditPanels,
  EnvironmentDetailActions,
  EnvironmentMigrationNotice,
  EnvironmentNotFound,
  EnvironmentReadinessPanel,
} from "./EnvironmentDetailViewParts";

export function EnvironmentDetailView() {
  const params = useParams();
  const router = useRouter();
  const envKey = params?.id?.toString() || "";
  const state = useEnvironmentDetailState(envKey);

  if (state.loading) {
    return (
      <OperatorShell title="环境详情" subtitle="加载环境资产">
        <OperatorState
          tone="blue"
          title="加载环境详情中"
          detail="正在读取环境资料和图片池。"
        />
      </OperatorShell>
    );
  }

  if (!state.env) {
    return (
      <OperatorShell title="环境详情" subtitle="环境资产池">
        <EnvironmentNotFound onBack={() => router.push("/environments")} />
      </OperatorShell>
    );
  }

  return (
    <OperatorShell title="环境详情" subtitle={state.env.name}>
      <div className="space-y-5">
        <EnvironmentMigrationNotice />
        <EnvironmentAuditPanels metadata={state.env.metadata} />
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
          <div className="space-y-5">
            <OperatorPanel>
              <OperatorSectionHeader
                title="基础资料"
                subtitle="分类、标签、描述和创建审计"
                action={
                  <EnvironmentDetailActions
                    editing={state.editingMeta}
                    saving={state.savingMeta}
                    onEdit={() => state.setEditingMeta(true)}
                    onCancel={state.handleCancelMeta}
                    onSave={state.handleSaveMeta}
                  />
                }
              />
              <EnvironmentHeader
                env={state.env}
                editing={state.editingMeta}
                form={state.metaForm}
                setForm={state.setMetaForm}
                addTag={state.handleAddTag}
                removeTag={state.handleRemoveTag}
              />
            </OperatorPanel>

            <OperatorPanel>
              <OperatorSectionHeader
                title="环境图片池"
                subtitle="参考图、变体生成和删除操作"
              />
              <div className="p-4">
                <EnvironmentImagesPanel
                  envName={state.env.name}
                  images={state.images}
                  imageSrc={state.imageSrc}
                  onImg2Img={(image) => state.setVariantTarget(image)}
                  onDelete={state.handleDeleteImage}
                  variant="embedded"
                />
              </div>
            </OperatorPanel>
          </div>

          <aside className="space-y-5 xl:sticky xl:top-20 xl:max-h-[calc(100vh-5rem)] xl:self-start xl:overflow-y-auto xl:overflow-x-hidden">
            <EnvironmentReadinessPanel
              imageCount={state.images.length}
              onBack={() => router.push("/environments")}
            />
            <OperatorPanel>
              <OperatorSectionHeader
                title="环境生成"
                subtitle="上传、文生图和任务提交"
              />
              <div className="p-4">
                <EnvironmentSidePanel
                  envKey={envKey}
                  onImageUploaded={state.handleImageUploaded}
                  variant="embedded"
                />
              </div>
            </OperatorPanel>
          </aside>
        </div>
      </div>
      <EnvironmentVariantModal
        envKey={envKey}
        env={state.env}
        target={state.variantTarget}
        imageSrc={state.imageSrc}
        onClose={() => state.setVariantTarget(null)}
      />
    </OperatorShell>
  );
}
