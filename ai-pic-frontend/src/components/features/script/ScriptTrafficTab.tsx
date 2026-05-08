"use client";

import type { Script } from "@/utils/api/types";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  StatusPill,
  operatorButtonClass,
  operatorTableClass,
  operatorTableHeadClass,
  operatorTableRowClass,
} from "@/components/shared";
import {
  asRecord,
  buildCsv,
  getValue,
  toAdSnippets,
  toHookPlan,
  toNumber,
  toStringList,
} from "./scriptTrafficUtils";

interface ScriptTrafficTabProps {
  script: Script;
}

export function ScriptTrafficTab({ script }: ScriptTrafficTabProps) {
  const extra = asRecord(script.extra_metadata) ?? {};
  const params = asRecord(script.generation_params) ?? {};
  const scoring = asRecord(extra.scoring) ?? {};
  const marketRegion = getValue(extra, params, "market_region") as string | undefined;
  const microGenre = getValue(extra, params, "micro_genre") as string | undefined;
  const twistDensity = getValue(extra, params, "twist_density") as string | undefined;
  const cliffhangerPlan = toStringList(getValue(extra, params, "cliffhanger_plan"));
  const hookPlanRaw = getValue(extra, params, "hook_plan");
  const hookPlan = toHookPlan(hookPlanRaw);
  const hookPlanText = typeof hookPlanRaw === "string" ? hookPlanRaw : undefined;
  const adSnippets = toAdSnippets(getValue(extra, params, "ad_snippets"));
  const scorecard =
    asRecord(getValue(extra, params, "scorecard")) ||
    asRecord(getValue(extra, params, "script_score")) ||
    asRecord(getValue(extra, params, "hook_score")) ||
    asRecord(scoring.script_score);
  const overallScore = toNumber(
    scorecard?.overall_score ??
      scorecard?.score ??
      getValue(extra, params, "overall_score"),
  );
  const dimensionScores = asRecord(scorecard?.dimension_scores ?? scorecard?.scores);
  const strengths = toStringList(scorecard?.strengths ?? getValue(extra, params, "strengths"));
  const risks = toStringList(scorecard?.risks ?? getValue(extra, params, "risk_notes"));
  const rewriteGuidance = toStringList(
    scorecard?.rewrite_guidance ?? getValue(extra, params, "rewrite_guidance"),
  );

  const handleExport = () => {
    if (adSnippets.length === 0) return;
    const rows = adSnippets.map((snippet, idx) => ({
      asset_id: `asset-${idx + 1}`,
      duration_seconds: snippet.duration_seconds,
      hook: snippet.hook,
      visual_summary: snippet.visual_summary,
      call_to_action: snippet.call_to_action,
      market_region: marketRegion,
      micro_genre: microGenre,
    }));
    const blob = new Blob([buildCsv(rows)], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `traffic-sheet-${script.business_id || script.id}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <OperatorPanel>
        <OperatorSectionHeader title="投流评分" subtitle="市场、微类型和爽点评分" />
        <div className="grid gap-3 p-4 md:grid-cols-3">
          <Metric label="市场/微类型" value={marketRegion || "未指定"} sub={microGenre || "未指定"} />
          <Metric label="反转密度" value={twistDensity || "—"} />
          <Metric label="总体评分" value={overallScore != null ? overallScore.toFixed(2) : "—"} />
        </div>
      </OperatorPanel>

      <div className="grid gap-4 lg:grid-cols-2">
        <OperatorPanel>
          <OperatorSectionHeader title="评分明细" subtitle="维度分和优势" />
          <div className="space-y-3 p-4">
            {dimensionScores ? (
              Object.entries(dimensionScores).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{key}</span>
                  <StatusPill tone="blue">{toNumber(value)?.toFixed(2) ?? String(value)}</StatusPill>
                </div>
              ))
            ) : (
              <OperatorState title="暂无评分明细" />
            )}
            <TextList title="优势" items={strengths} />
          </div>
        </OperatorPanel>
        <OperatorPanel>
          <OperatorSectionHeader title="风险提示" subtitle="风险和修订建议" />
          <div className="space-y-3 p-4">
            <TextList title="风险" items={risks} empty="暂无风险提示" />
            <TextList title="修订建议" items={rewriteGuidance} />
          </div>
        </OperatorPanel>
      </div>

      <OperatorPanel>
        <OperatorSectionHeader title="Hook/节奏规划" subtitle="生成参数和额外元数据" />
        <div className="grid gap-3 p-4 md:grid-cols-3">
          <Metric label="开场钩子" value={hookPlan?.opening_hook || hookPlanText || "—"} />
          <Metric label="情绪升级" value={hookPlan?.escalation_plan || "—"} />
          <Metric label="释放节点" value={hookPlan?.payoff_plan || "—"} />
        </div>
        <div className="space-y-3 px-4 pb-4">
          <TextList
            title="关键反转"
            items={(hookPlan?.key_reversals || []).map((beat) =>
              `${beat.description}${beat.timing ? ` (${beat.timing})` : ""}`,
            )}
          />
          <TextList title="悬念/卡点" items={cliffhangerPlan} />
        </div>
      </OperatorPanel>

      <OperatorPanel>
        <OperatorSectionHeader
          title="投流素材清单"
          subtitle={`共 ${adSnippets.length} 条`}
          action={
            <button
              type="button"
              onClick={handleExport}
              disabled={adSnippets.length === 0}
              className={operatorButtonClass("secondary")}
            >
              导出 CSV
            </button>
          }
        />
        {adSnippets.length === 0 ? (
          <div className="p-4"><OperatorState title="暂无投流素材数据" /></div>
        ) : (
          <div className="overflow-x-auto p-4">
            <table className={operatorTableClass}>
              <thead className={operatorTableHeadClass}>
                <tr>
                  <th className="px-3 py-2 text-left">时长</th>
                  <th className="px-3 py-2 text-left">核心钩子</th>
                  <th className="px-3 py-2 text-left">画面摘要</th>
                  <th className="px-3 py-2 text-left">CTA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {adSnippets.map((snippet, idx) => (
                  <tr key={idx} className={operatorTableRowClass}>
                    <td className="px-3 py-2">{snippet.duration_seconds || "—"}s</td>
                    <td className="px-3 py-2">{snippet.hook}</td>
                    <td className="px-3 py-2">{snippet.visual_summary || "—"}</td>
                    <td className="px-3 py-2">{snippet.call_to_action || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </OperatorPanel>
    </div>
  );
}

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="mt-2 text-sm font-medium text-gray-950">{value}</div>
      {sub ? <div className="mt-1 text-xs text-gray-500">{sub}</div> : null}
    </div>
  );
}

function TextList({ title, items, empty }: { title: string; items: string[]; empty?: string }) {
  if (!items.length && !empty) return null;
  return (
    <div>
      <div className="mb-2 text-xs font-medium text-gray-500">{title}</div>
      {items.length ? (
        <div className="space-y-1">
          {items.map((item, idx) => (
            <div key={idx} className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-700">
              {item}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-gray-500">{empty}</div>
      )}
    </div>
  );
}
