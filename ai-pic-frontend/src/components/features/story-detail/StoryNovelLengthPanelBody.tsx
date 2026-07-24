import { operatorButtonClass, operatorInputClass } from "@/components/shared";
import type {
  StoryNovelCreateRevisionPayload,
  StoryNovelRevision,
  StoryNovelUpdateLengthSpecPayload,
} from "@/utils/api/types";
import { StoryNovelChapterLengthOverrides } from "./StoryNovelChapterLengthOverrides";
import { StoryNovelLengthRangeFields } from "./StoryNovelLengthRangeFields";
import { formatCharacterCount } from "./storyNovelLengthPlan";
import type { useStoryNovelLengthPanelState } from "./useStoryNovelLengthPanelState";

type State = ReturnType<typeof useStoryNovelLengthPanelState>;
interface BodyProps {
  state: State;
  locked: boolean;
  busy: boolean;
  revision: StoryNovelRevision | null;
  onCreate: (payload: StoryNovelCreateRevisionPayload) => Promise<boolean>;
  onUpdate: (
    revisionId: string,
    payload: StoryNovelUpdateLengthSpecPayload,
  ) => Promise<boolean>;
}

export function StoryNovelLengthPanelBody(props: BodyProps) {
  return (
    <div className="space-y-4 p-5">
      <LengthProfileInputs state={props.state} locked={props.locked} />
      <LengthDefaults state={props.state} locked={props.locked} />
      <StoryNovelChapterLengthOverrides
        chapters={props.state.chapters}
        defaults={props.state.defaults}
        overrides={props.state.overrides}
        disabled={props.locked}
        onChange={props.state.setOverrides}
      />
      <LengthTotals state={props.state} />
      {props.state.profileError || props.state.validation ? (
        <p role="alert" className="text-xs text-red-600">
          {props.state.profileError || props.state.validation}
        </p>
      ) : null}
      <LengthActions {...props} />
    </div>
  );
}

function LengthProfileInputs({
  state,
  locked,
}: {
  state: State;
  locked: boolean;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <label className="text-xs font-medium text-gray-600">
        长度预设
        <select
          aria-label="长度预设"
          value={state.profileId}
          disabled={locked}
          onChange={(event) => state.setProfileId(event.target.value)}
          className={operatorInputClass("mt-1 w-full")}
        >
          <option value="">请选择</option>
          {state.profiles.map((profile) => (
            <option key={profile.profile_id} value={profile.profile_id}>
              {profile.name}
            </option>
          ))}
          <option value="custom">自定义</option>
        </select>
      </label>
      <label className="text-xs font-medium text-gray-600">
        生成模型（可选）
        <input
          aria-label="生成模型（可选）"
          value={state.model}
          disabled={locked}
          onChange={(event) => state.setModel(event.target.value)}
          className={operatorInputClass("mt-1 w-full")}
          placeholder="使用服务端默认模型"
        />
      </label>
    </div>
  );
}

function LengthDefaults({ state, locked }: { state: State; locked: boolean }) {
  return state.profileId === "custom" ? (
    <StoryNovelLengthRangeFields
      value={state.custom}
      disabled={locked}
      onChange={state.setCustom}
    />
  ) : (
    <p className="text-xs text-gray-500">
      默认每章 {state.defaults.min_chars}–{state.defaults.max_chars} 字符，目标{" "}
      {state.defaults.target_chars}
    </p>
  );
}

function LengthTotals({ state }: { state: State }) {
  return (
    <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-900">
      计划章节：{state.chapters.length} 章 · 预计目标：
      {formatCharacterCount(state.totals.target_chars)} 字 · 允许范围：
      {formatCharacterCount(state.totals.min_chars)}–
      {formatCharacterCount(state.totals.max_chars)} 字
    </div>
  );
}

function LengthActions(props: BodyProps) {
  const { state, revision } = props;
  const disabled = props.locked || props.busy || Boolean(state.validation);
  const spec = {
    length_profile_id: state.profileId,
    custom_length_profile: state.profileId === "custom" ? state.custom : null,
    chapter_length_overrides: state.overrides,
  };
  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        disabled={disabled}
        onClick={() =>
          void props.onCreate({
            style: "prose",
            ...spec,
            ...(state.model.trim() ? { model: state.model.trim() } : {}),
          })
        }
        className={operatorButtonClass("primary")}
      >
        创建新平台版本
      </button>
      {revision?.lifecycle_status === "draft" ? (
        <button
          type="button"
          disabled={disabled}
          onClick={() =>
            void props.onUpdate(revision.business_id, {
              ...spec,
              expected_plan_version: revision.generation_plan?.version || 1,
              model: state.model.trim() || null,
            })
          }
          className={operatorButtonClass("secondary")}
        >
          保存到当前版本
        </button>
      ) : null}
    </div>
  );
}
