"use client";

import type { Script } from "@/utils/api";
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

  const marketRegion = getValue(extra, params, "market_region") as
    | string
    | undefined;
  const microGenre = getValue(extra, params, "micro_genre") as
    | string
    | undefined;
  const twistDensity = getValue(extra, params, "twist_density") as
    | string
    | undefined;
  const cliffhangerPlan = toStringList(
    getValue(extra, params, "cliffhanger_plan"),
  );

  const hookPlanRaw = getValue(extra, params, "hook_plan");
  const hookPlan = toHookPlan(hookPlanRaw);
  const hookPlanText =
    typeof hookPlanRaw === "string" ? hookPlanRaw : undefined;

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

  const dimensionScores = asRecord(
    scorecard?.dimension_scores ?? scorecard?.scores,
  );
  const strengths = toStringList(
    scorecard?.strengths ?? getValue(extra, params, "strengths"),
  );
  const risks = toStringList(
    scorecard?.risks ?? getValue(extra, params, "risk_notes"),
  );
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
    const csv = buildCsv(rows);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `traffic-sheet-${script.business_id || script.id}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="text-xs text-slate-500">市场/微类型</div>
          <div className="mt-2 text-sm font-medium text-slate-800">
            {marketRegion || "未指定"}
          </div>
          <div className="text-xs text-slate-600">{microGenre || "未指定"}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="text-xs text-slate-500">反转密度</div>
          <div className="mt-2 text-sm font-medium text-slate-800">
            {twistDensity || "—"}
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="text-xs text-slate-500">总体评分</div>
          <div className="mt-2 text-2xl font-semibold text-slate-800">
            {overallScore != null ? overallScore.toFixed(2) : "—"}
          </div>
          <div className="text-xs text-slate-500">爽点/风险综合</div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="text-sm font-semibold text-slate-800 mb-3">
            爽点评分
          </div>
          {dimensionScores ? (
            <div className="space-y-2 text-sm">
              {Object.entries(dimensionScores).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-slate-600">{key}</span>
                  <span className="font-medium text-slate-800">
                    {toNumber(value)?.toFixed(2) ?? String(value)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-slate-500">暂无评分明细</div>
          )}
          {strengths.length > 0 && (
            <div className="mt-3">
              <div className="text-xs text-slate-500">优势</div>
              <ul className="list-disc pl-4 text-xs text-slate-700">
                {strengths.map((item, idx) => (
                  <li key={`strength-${idx}`}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="text-sm font-semibold text-slate-800 mb-3">
            风险提示
          </div>
          {risks.length > 0 ? (
            <ul className="list-disc pl-4 text-sm text-slate-700">
              {risks.map((risk, idx) => (
                <li key={`risk-${idx}`}>{risk}</li>
              ))}
            </ul>
          ) : (
            <div className="text-sm text-slate-500">暂无风险提示</div>
          )}
          {rewriteGuidance.length > 0 && (
            <div className="mt-3">
              <div className="text-xs text-slate-500">修订建议</div>
              <ul className="list-disc pl-4 text-xs text-slate-700">
                {rewriteGuidance.map((item, idx) => (
                  <li key={`rewrite-${idx}`}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold text-slate-800">
            Hook/节奏规划
          </div>
          <span className="text-xs text-slate-500">
            来自生成参数或额外元数据
          </span>
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-3 text-sm">
          <div>
            <div className="text-xs text-slate-500">开场钩子</div>
            <div>{hookPlan?.opening_hook || hookPlanText || "—"}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">情绪升级</div>
            <div>{hookPlan?.escalation_plan || "—"}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">释放节点</div>
            <div>{hookPlan?.payoff_plan || "—"}</div>
          </div>
        </div>
        {hookPlan?.key_reversals?.length ? (
          <ul className="mt-3 list-disc pl-4 text-sm text-slate-700">
            {hookPlan.key_reversals.map((beat, idx) => (
              <li key={`beat-${idx}`}>
                {beat.description} {beat.timing ? `(${beat.timing})` : ""}
              </li>
            ))}
          </ul>
        ) : null}
        {cliffhangerPlan.length > 0 && (
          <div className="mt-3">
            <div className="text-xs text-slate-500">悬念/卡点</div>
            <ul className="list-disc pl-4 text-sm text-slate-700">
              {cliffhangerPlan.map((item, idx) => (
                <li key={`cliff-${idx}`}>{item}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold text-slate-800">
            投流素材清单
          </div>
          <button
            type="button"
            onClick={handleExport}
            disabled={adSnippets.length === 0}
            className="text-xs rounded-md border border-slate-200 px-3 py-1 text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
          >
            导出 CSV
          </button>
        </div>
        {adSnippets.length === 0 ? (
          <div className="mt-3 text-sm text-slate-500">暂无投流素材数据</div>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500">
                  <th className="pb-2">时长</th>
                  <th className="pb-2">核心钩子</th>
                  <th className="pb-2">画面摘要</th>
                  <th className="pb-2">CTA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {adSnippets.map((snippet, idx) => (
                  <tr key={`snippet-${idx}`} className="text-slate-700">
                    <td className="py-2 pr-4">
                      {snippet.duration_seconds || "—"}s
                    </td>
                    <td className="py-2 pr-4">{snippet.hook}</td>
                    <td className="py-2 pr-4">
                      {snippet.visual_summary || "—"}
                    </td>
                    <td className="py-2">{snippet.call_to_action || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
