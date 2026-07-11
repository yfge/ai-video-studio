import {
  operatorButtonClass,
  operatorInputClass,
  operatorSelectClass,
} from "@/components/shared";
import type {
  ProductionCanvasActivity,
  ProductionCanvasComment,
  ProductionCanvasCommentTargetType,
} from "@/utils/api/types";

export type CommentTarget = {
  id: string;
  key: string;
  label: string;
  type: ProductionCanvasCommentTargetType;
};

const activityLabels: Record<string, string> = {
  "candidate.approved": "选用候选",
  "candidate.branched": "提交候选分支",
  "candidate.rejected": "拒绝候选",
  "collaborator.removed": "移除协作者",
  "collaborator.updated": "更新协作者",
  "comment.added": "发表评论",
  "definition.saved": "保存图定义",
  "node.executed": "执行节点",
  "run.cancel": "取消运行",
  "run.resume": "继续运行",
  "run.retry": "重试节点",
  "run.run_ready": "运行就绪节点",
  "timeline.placed": "回填 Timeline",
};

function timeLabel(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
}

export function CollaborationComments({
  body,
  busy,
  canComment,
  comments,
  onBodyChange,
  onSubmit,
  onTargetChange,
  target,
  targetKey,
  targets,
}: {
  body: string;
  busy: boolean;
  canComment: boolean;
  comments: ProductionCanvasComment[];
  onBodyChange: (value: string) => void;
  onSubmit: () => void;
  onTargetChange: (value: string) => void;
  target?: CommentTarget;
  targetKey: string;
  targets: CommentTarget[];
}) {
  return (
    <div className="space-y-3">
      <select
        aria-label="评论目标"
        className={operatorSelectClass("w-full")}
        value={targetKey}
        onChange={(event) => onTargetChange(event.currentTarget.value)}
      >
        {targets.map((item) => (
          <option key={item.key} value={item.key}>
            {item.label}
          </option>
        ))}
      </select>
      <div className="max-h-52 space-y-2 overflow-y-auto">
        {comments.map((comment) => (
          <div
            key={comment.comment_id}
            className="border-l-2 border-blue-300 pl-3"
          >
            <div className="flex items-center justify-between gap-2 text-[11px] text-gray-500">
              <span className="font-semibold text-gray-700">
                {comment.author_username}
              </span>
              <span>{timeLabel(comment.created_at)}</span>
            </div>
            <p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-gray-700">
              {comment.body}
            </p>
          </div>
        ))}
        {!comments.length ? (
          <p className="text-xs text-gray-400">当前目标暂无评论</p>
        ) : null}
      </div>
      {canComment ? (
        <div className="space-y-2 border-t border-gray-100 pt-3">
          <textarea
            aria-label="协作评论"
            className={`${operatorInputClass(
              "min-h-20 w-full resize-y py-2",
            )} h-auto`}
            maxLength={2000}
            placeholder="添加评审意见"
            value={body}
            onChange={(event) => onBodyChange(event.currentTarget.value)}
            onInput={(event) => onBodyChange(event.currentTarget.value)}
          />
          <button
            type="button"
            className={operatorButtonClass("primary", "w-full")}
            disabled={!target || !body.trim() || busy}
            onClick={onSubmit}
          >
            发表评论
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function CollaborationActivity({
  activity,
}: {
  activity: ProductionCanvasActivity[];
}) {
  return (
    <div className="max-h-72 space-y-3 overflow-y-auto">
      {[...activity].reverse().map((item) => (
        <div
          key={item.activity_id}
          className="border-b border-gray-100 pb-2 text-xs"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="font-semibold text-gray-800">
              {item.actor_username}
            </span>
            <span className="text-[11px] text-gray-400">
              {timeLabel(item.created_at)}
            </span>
          </div>
          <div className="mt-1 text-gray-600">
            {activityLabels[item.action] || item.action}
          </div>
          {item.detail ? (
            <div className="mt-1 break-words text-gray-500">{item.detail}</div>
          ) : null}
        </div>
      ))}
      {!activity.length ? (
        <p className="text-xs text-gray-400">暂无活动记录</p>
      ) : null}
    </div>
  );
}
