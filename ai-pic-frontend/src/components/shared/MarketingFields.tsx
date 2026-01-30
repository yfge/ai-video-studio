"use client";

import type { Dispatch, SetStateAction } from "react";
import type { AdSnippet, HookPlan } from "@/utils/api";
import {
  MARKET_REGIONS,
  MICRO_GENRES,
  PACING_TEMPLATES,
  type PacingTemplate,
} from "@/utils/marketingTemplates";

export type MarketingFormValues = {
  market_region?: string;
  micro_genre?: string;
  hook_plan?: HookPlan;
  twist_density?: string;
  cliffhanger_plan?: string[];
  ad_snippets?: AdSnippet[];
  pacing_template?: string;
};

interface MarketingFieldsProps<T extends MarketingFormValues> {
  form: T;
  setForm: Dispatch<SetStateAction<T>>;
  title?: string;
  idPrefix?: string;
}

const getTemplateById = (id?: string) =>
  PACING_TEMPLATES.find((template) => template.id === id);

const applyTemplate = <T extends MarketingFormValues>(
  template: PacingTemplate,
  setForm: Dispatch<SetStateAction<T>>,
) => {
  setForm((prev) => ({
    ...prev,
    pacing_template: template.id,
    hook_plan: template.hookPlan,
    twist_density: template.twistDensity,
    cliffhanger_plan: template.cliffhangerPlan,
    ad_snippets: template.adSnippets,
  }));
};

export function MarketingFields<T extends MarketingFormValues>({
  form,
  setForm,
  title = "市场与节奏",
  idPrefix = "marketing",
}: MarketingFieldsProps<T>) {
  const selectedTemplate = getTemplateById(form.pacing_template);

  return (
    <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="text-sm font-medium text-slate-700">{title}</div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">
            目标市场
          </label>
          <select
            value={form.market_region || ""}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                market_region: e.target.value,
              }))
            }
            className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
          >
            <option value="">未指定</option>
            {MARKET_REGIONS.map((region) => (
              <option key={region.value} value={region.value}>
                {region.label}
              </option>
            ))}
          </select>
          <p className="mt-1 text-[11px] text-slate-500">
            {MARKET_REGIONS.find(
              (region) => region.value === form.market_region,
            )?.description || "选择目标市场后将自动触发本地化提示"}
          </p>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">
            微类型
          </label>
          <input
            list={`${idPrefix}-micro-genre`}
            value={form.micro_genre || ""}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                micro_genre: e.target.value,
              }))
            }
            placeholder="例如：黑帮复仇 / 狼人命定伴侣"
            className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
          />
          <datalist id={`${idPrefix}-micro-genre`}>
            {MICRO_GENRES.map((genre) => (
              <option key={genre.value} value={genre.label} />
            ))}
          </datalist>
          <p className="mt-1 text-[11px] text-slate-500">
            选择或输入更具体的题材标签
          </p>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">
            节奏模板
          </label>
          <select
            value={form.pacing_template || ""}
            onChange={(e) => {
              const value = e.target.value;
              if (!value) {
                setForm((prev) => ({
                  ...prev,
                  pacing_template: "",
                  hook_plan: undefined,
                  twist_density: "",
                  cliffhanger_plan: [],
                  ad_snippets: [],
                }));
                return;
              }
              const template = getTemplateById(value);
              if (template) applyTemplate(template, setForm);
            }}
            className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
          >
            <option value="">自定义</option>
            {PACING_TEMPLATES.map((template) => (
              <option key={template.id} value={template.id}>
                {template.label}
              </option>
            ))}
          </select>
          <p className="mt-1 text-[11px] text-slate-500">
            自动填充钩子计划、反转密度与投流素材建议
          </p>
        </div>
      </div>
      <div className="rounded-md border border-dashed border-slate-200 bg-white p-3 text-xs text-slate-600">
        {selectedTemplate ? (
          <div className="space-y-2">
            <div className="text-sm font-medium text-slate-700">
              {selectedTemplate.label}
            </div>
            <p className="text-slate-600">{selectedTemplate.description}</p>
            <div className="grid gap-2 md:grid-cols-3">
              <div>
                <div className="text-[11px] uppercase text-slate-400">
                  开场钩子
                </div>
                <div>{selectedTemplate.hookPlan.opening_hook || "—"}</div>
              </div>
              <div>
                <div className="text-[11px] uppercase text-slate-400">
                  情绪升级
                </div>
                <div>{selectedTemplate.hookPlan.escalation_plan || "—"}</div>
              </div>
              <div>
                <div className="text-[11px] uppercase text-slate-400">
                  释放节点
                </div>
                <div>{selectedTemplate.hookPlan.payoff_plan || "—"}</div>
              </div>
            </div>
            {selectedTemplate.twistDensity && (
              <div>
                <span className="text-[11px] uppercase text-slate-400">
                  反转密度
                </span>
                <span className="ml-2 text-slate-700">
                  {selectedTemplate.twistDensity}
                </span>
              </div>
            )}
            {selectedTemplate.cliffhangerPlan?.length ? (
              <ul className="list-disc pl-4 text-slate-600">
                {selectedTemplate.cliffhangerPlan.map((item, idx) => (
                  <li key={`${selectedTemplate.id}-cliff-${idx}`}>{item}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : (
          <div className="text-slate-500">
            选择节奏模板后显示节奏与钩子说明。
          </div>
        )}
      </div>
    </div>
  );
}
