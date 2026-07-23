import { operatorButtonClass, operatorInputClass } from "@/components/shared";
import type {
  DramaticState,
  DramaticStateResponse,
  ExpressionPolicy,
} from "@/utils/api/types";

export function DramaticStateForm({
  data,
  draft,
  setDraft,
  onSave,
  onSuggest,
}: {
  data: DramaticStateResponse | null;
  draft: DramaticState;
  setDraft: (value: DramaticState) => void;
  onSave: () => void;
  onSuggest: () => void;
}) {
  const updateIntent = (index: number, patch: Record<string, string>) => {
    const intents = [...draft.character_intents];
    intents[index] = { ...intents[index], ...patch };
    setDraft({ ...draft, character_intents: intents });
  };
  return (
    <>
      <TextField
        label="场景表层目标"
        value={draft.scene_objective || ""}
        onChange={(value) => setDraft({ ...draft, scene_objective: value })}
      />
      {draft.character_intents.map((intent, index) => (
        <div
          key={index}
          className="space-y-2 rounded-md border border-gray-200 p-3"
        >
          <TextField
            label="角色 business ID"
            value={intent.character_business_id}
            onChange={(value) =>
              updateIntent(index, { character_business_id: value })
            }
          />
          <TextField
            label="表层行动"
            value={intent.surface_action}
            onChange={(value) => updateIntent(index, { surface_action: value })}
          />
          <TextField
            label="隐藏目标"
            value={intent.hidden_goal || ""}
            onChange={(value) => updateIntent(index, { hidden_goal: value })}
          />
          <TextField
            label="真实情绪"
            value={intent.emotional_truth || ""}
            onChange={(value) =>
              updateIntent(index, { emotional_truth: value })
            }
          />
          <label className="block text-xs text-gray-600">
            表达限制
            <select
              value={intent.expression_policy}
              onChange={(event) =>
                updateIntent(index, {
                  expression_policy: event.target.value as ExpressionPolicy,
                })
              }
              className={operatorInputClass("mt-1 w-full")}
            >
              <option value="sayable">可直说</option>
              <option value="subtext_only">只可暗示</option>
              <option value="must_not_reveal">禁止透露</option>
            </select>
          </label>
        </div>
      ))}
      <button
        type="button"
        onClick={() =>
          setDraft({
            ...draft,
            character_intents: [
              ...draft.character_intents,
              {
                character_business_id: "",
                surface_action: "",
                expression_policy: "sayable",
              },
            ],
          })
        }
        className={operatorButtonClass("secondary")}
      >
        添加角色意图
      </button>
      <TextAreaList
        label="必须出现的暗示"
        values={draft.must_hint}
        onChange={(values) => setDraft({ ...draft, must_hint: values })}
      />
      <TextAreaList
        label="禁止提前透露"
        values={draft.must_not_reveal}
        onChange={(values) => setDraft({ ...draft, must_not_reveal: values })}
      />
      {data?.suggestion ? (
        <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-xs">
          AI 建议基于 v{data.suggestion_based_on_version}，尚未覆盖人工内容。
          <button
            type="button"
            onClick={() => setDraft(data.suggestion as DramaticState)}
            className={operatorButtonClass("secondary", "mt-2")}
          >
            采用到编辑草稿
          </button>
        </div>
      ) : null}
      <details className="text-xs text-gray-600">
        <summary className="cursor-pointer">当前角色可用记忆预览</summary>
        <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap rounded bg-gray-50 p-2">
          {JSON.stringify(data?.available_memory_preview || [], null, 2)}
        </pre>
      </details>
      <div className="grid gap-2">
        <button
          type="button"
          onClick={onSave}
          className={operatorButtonClass("primary")}
        >
          保存潜台词（不调用模型）
        </button>
        <button
          type="button"
          onClick={onSuggest}
          className={operatorButtonClass("secondary")}
        >
          AI 建议潜台词（可能调用模型）
        </button>
      </div>
    </>
  );
}

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block text-xs text-gray-600">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={operatorInputClass("mt-1 w-full")}
      />
    </label>
  );
}

function TextAreaList({
  label,
  values,
  onChange,
}: {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
}) {
  return (
    <label className="block text-xs text-gray-600">
      {label}
      <textarea
        value={values.join("\n")}
        onChange={(event) =>
          onChange(
            event.target.value
              .split("\n")
              .map((item) => item.trim())
              .filter(Boolean),
          )
        }
        rows={3}
        className={operatorInputClass("mt-1 w-full")}
      />
    </label>
  );
}
