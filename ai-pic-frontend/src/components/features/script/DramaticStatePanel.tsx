"use client";

import { useEffect, useState } from "react";
import { OperatorState, StatusPill } from "@/components/shared";
import { narrativeMemoryAPI } from "@/utils/api/endpoints";
import type { DramaticState, DramaticStateResponse } from "@/utils/api/types";
import { DramaticStateForm } from "./DramaticStateForm";

const emptyState = (): DramaticState => ({
  schema: "dramatic_state.v1",
  scene_objective: "",
  character_intents: [],
  audience_goal: "",
  audience_disclosure: "revealed",
  must_hint: [],
  must_not_reveal: [],
});

export function DramaticStatePanel({
  scriptId,
  sceneId,
}: {
  scriptId: string;
  sceneId?: string;
}) {
  const [data, setData] = useState<DramaticStateResponse | null>(null);
  const [draft, setDraft] = useState<DramaticState>(emptyState());
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let active = true;
    if (!sceneId) return;
    setLoading(true);
    void narrativeMemoryAPI
      .getDramaticState(scriptId, sceneId)
      .then((response) => {
        if (!active) return;
        if (response.success && response.data) {
          setData(response.data);
          setDraft(response.data.dramatic_state);
          setMessage("");
        } else {
          setMessage(response.error || "场景潜台词加载失败");
        }
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [sceneId, scriptId]);

  if (!sceneId) return <OperatorState title="选择场景后编辑潜台词" />;
  if (loading) return <OperatorState title="加载场景意图…" />;

  const save = async () => {
    if (!data) return;
    const response = await narrativeMemoryAPI.updateDramaticState(
      scriptId,
      sceneId,
      data.version,
      draft,
    );
    if (!response.success || !response.data) {
      setMessage(response.error || "保存失败；内容可能已被其他窗口更新");
      return;
    }
    setData(response.data);
    setDraft(response.data.dramatic_state);
    setMessage("场景意图已本地保存；未调用模型。");
  };

  const suggest = async () => {
    const response = await narrativeMemoryAPI.suggestDramaticState(
      scriptId,
      sceneId,
      data?.version || 0,
    );
    setMessage(
      response.success && response.data
        ? `AI 建议任务 #${response.data.task_id} 已提交；不会覆盖人工内容。完成后刷新场景查看。`
        : response.error || "AI 建议任务创建失败",
    );
  };

  return (
    <section className="mt-5 space-y-4 border-t border-gray-200 pt-4">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">场景意图与潜台词</h3>
        <StatusPill tone={data?.quality_gate.passed ? "green" : "red"}>
          {data?.quality_gate.passed ? "叙事检查通过" : "存在阻断"}
        </StatusPill>
      </div>
      <DramaticStateForm
        data={data}
        draft={draft}
        setDraft={setDraft}
        onSave={() => void save()}
        onSuggest={() => void suggest()}
      />
      <p className="text-xs text-gray-500" aria-live="polite">
        {message}
      </p>
    </section>
  );
}
