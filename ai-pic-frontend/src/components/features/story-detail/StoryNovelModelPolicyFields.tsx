import { ModelSelector } from "@/components/shared";

interface StoryNovelModelPolicyFieldsProps {
  planningModel: string;
  proseModel: string;
  auditModel: string;
  disabled: boolean;
  onPlanningModel: (value: string) => void;
  onProseModel: (value: string) => void;
  onAuditModel: (value: string) => void;
}

export function StoryNovelModelPolicyFields({
  planningModel,
  proseModel,
  auditModel,
  disabled,
  onPlanningModel,
  onProseModel,
  onAuditModel,
}: StoryNovelModelPolicyFieldsProps) {
  return (
    <div className="grid gap-3 lg:grid-cols-3">
      <ModelSelector
        value={planningModel}
        onChange={onPlanningModel}
        label="章前规划模型"
        helperText="默认沿用 StorySeed 规划模型；负责 Canon、章节计划和逐章 brief。"
        autoLabel="使用 StorySeed 规划模型"
        modelType="text"
        disabled={disabled}
        cacheKey="story-novel-planning-models"
      />
      <ModelSelector
        value={proseModel}
        onChange={onProseModel}
        label="正文生成模型（可选）"
        helperText="只负责按当前章 brief 生成正文，不读取原始事件或人物记忆。"
        autoLabel="使用服务端默认正文模型"
        modelType="text"
        disabled={disabled}
        cacheKey="story-novel-prose-models"
      />
      <ModelSelector
        value={auditModel}
        onChange={onAuditModel}
        label="状态审计模型（可选）"
        helperText="负责状态、未来剧情和证据审计；留空使用系统默认。"
        autoLabel="使用系统默认审计模型"
        modelType="text"
        disabled={disabled}
        cacheKey="story-novel-audit-models"
      />
    </div>
  );
}
