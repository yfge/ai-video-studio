import {
  OperatorPanel,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import type { StoryNovelContinuityReport } from "@/utils/api/types";

const SCORE_LABELS: Record<string, string> = {
  structure: "结构",
  character: "人物",
  prose: "文笔",
  world: "世界观",
  emotion: "情绪",
  originality: "原创性",
  adaptation: "改编价值",
};

export function StoryNovelQualityPanel({
  report,
  onAcceptIssue,
}: {
  report: StoryNovelContinuityReport;
  onAcceptIssue: (issueId: string) => void;
}) {
  const metrics = Object.entries(report.hard_metrics || {});
  const scores = Object.entries(report.quality_scores || {});
  const issues = report.issues || [];
  return (
    <OperatorPanel>
      <div className="border-b border-gray-100 p-5">
        <h3 className="text-sm font-semibold">连续性与全书质量</h3>
        {report.summary ? (
          <p className="mt-2 text-xs text-gray-600">{report.summary}</p>
        ) : null}
      </div>
      {metrics.length ? (
        <div className="border-b border-gray-100 p-5">
          <h4 className="text-xs font-semibold">确定性门禁</h4>
          <div className="mt-3 flex flex-wrap gap-2">
            {metrics.map(([key, value]) => (
              <StatusPill
                key={key}
                tone={
                  key === "chapter_repair_rate" || value === 0 ? "green" : "red"
                }
              >
                {key} · {value}
              </StatusPill>
            ))}
          </div>
        </div>
      ) : null}
      {scores.length ? (
        <div className="grid gap-3 border-b border-gray-100 p-5 sm:grid-cols-2">
          {scores.map(([key, value]) => (
            <div key={key} className="rounded-md border border-gray-200 p-3">
              <div className="flex items-center justify-between text-xs font-medium">
                <span>{SCORE_LABELS[key] || key}</span>
                <span>{value.score.toFixed(1)}/10</span>
              </div>
              <p className="mt-2 text-xs text-gray-500">{value.rationale}</p>
            </div>
          ))}
          <p className="text-xs text-gray-500 sm:col-span-2">
            编辑评分用于判断修改方向，不参与 canonical 审批硬门禁。
          </p>
        </div>
      ) : null}
      {issues.length ? (
        <div className="p-5">
          <h4 className="text-xs font-semibold">问题清单</h4>
          <div className="mt-3 space-y-2">
            {issues.map((issue) => (
              <div
                key={issue.id}
                className="rounded-md border border-gray-200 p-3 text-xs"
              >
                <div className="flex items-center gap-2">
                  <StatusPill
                    tone={issue.severity === "blocking" ? "red" : "amber"}
                  >
                    {issue.severity}
                  </StatusPill>
                  <span>{issue.message}</span>
                </div>
                {issue.suggestion ? (
                  <p className="mt-2 text-gray-500">{issue.suggestion}</p>
                ) : null}
                {issue.severity === "blocking" && !issue.accepted_reason ? (
                  <button
                    type="button"
                    onClick={() => onAcceptIssue(issue.id)}
                    className={operatorButtonClass("secondary", "mt-2")}
                  >
                    填写接受理由
                  </button>
                ) : null}
                {issue.accepted_reason ? (
                  <p className="mt-2 text-green-700">
                    已接受：{issue.accepted_reason}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </OperatorPanel>
  );
}
