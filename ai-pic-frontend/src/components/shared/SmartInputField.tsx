"use client";

import { useState } from "react";
import { virtualIPAPI } from "@/utils/api/endpoints";
import {
  OperatorPanel,
  OperatorSectionHeader,
  operatorButtonClass,
  operatorInputClass,
  operatorTextareaClass,
} from "./operator";

interface SmartInputFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  type?: "input" | "textarea";
  rows?: number;
  aiSuggestType?: "description" | "background_story" | "biography";
  contextData?: {
    name?: string;
    description?: string;
    basicInfo?: string;
  };
  showAIAssist?: boolean;
}

export default function SmartInputField({
  label,
  value,
  onChange,
  placeholder,
  type = "input",
  rows = 3,
  aiSuggestType,
  contextData,
  showAIAssist = true,
}: SmartInputFieldProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState("");
  const [showSuggestion, setShowSuggestion] = useState(false);

  const handleAIAssist = async () => {
    if (!contextData?.name?.trim() || !aiSuggestType) return;
    setIsGenerating(true);
    try {
      const basicParts = [
        contextData.basicInfo,
        contextData.description ? `角色描述：${contextData.description}` : "",
        value ? `${label}：${value}` : "",
      ].filter(Boolean);
      const response = await virtualIPAPI.generateAIContent({
        name: contextData.name,
        basic_info: basicParts.join("\n").trim() || undefined,
        style_preference: "现代风格",
        image_category: "portrait",
      });
      if (response.success && response.data) {
        setAiSuggestion(response.data[aiSuggestType]);
        setShowSuggestion(true);
      }
    } catch (error) {
      console.error("AI助手失败:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  const field = type === "textarea" ? (
    <textarea
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={operatorTextareaClass("w-full")}
      rows={rows}
      placeholder={placeholder}
    />
  ) : (
    <input
      type="text"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={operatorInputClass("w-full")}
      placeholder={placeholder}
    />
  );

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <label className="block text-sm font-medium text-gray-700">{label}</label>
        {showAIAssist && aiSuggestType && contextData?.name ? (
          <button
            type="button"
            onClick={handleAIAssist}
            disabled={isGenerating}
            className={operatorButtonClass("ghost")}
          >
            {isGenerating ? "生成中..." : "AI 助手"}
          </button>
        ) : null}
      </div>
      {field}
      {showSuggestion && aiSuggestion ? (
        <OperatorPanel>
          <OperatorSectionHeader
            title="AI 建议"
            subtitle="可替换或合并到当前字段"
            action={
              <button
                type="button"
                onClick={() => setShowSuggestion(false)}
                className={operatorButtonClass("ghost")}
              >
                关闭
              </button>
            }
          />
          <div className="space-y-3 p-3">
            <div className="rounded-md border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">
              {aiSuggestion}
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  onChange(aiSuggestion);
                  setShowSuggestion(false);
                }}
                className={operatorButtonClass("primary", "flex-1")}
              >
                采用建议
              </button>
              {value ? (
                <button
                  type="button"
                  onClick={() => {
                    onChange(`${value}\n\n${aiSuggestion}`);
                    setShowSuggestion(false);
                  }}
                  className={operatorButtonClass("secondary", "flex-1")}
                >
                  合并内容
                </button>
              ) : null}
              <button
                type="button"
                onClick={() => setShowSuggestion(false)}
                className={operatorButtonClass("ghost")}
              >
                忽略
              </button>
            </div>
          </div>
        </OperatorPanel>
      ) : null}
    </div>
  );
}
