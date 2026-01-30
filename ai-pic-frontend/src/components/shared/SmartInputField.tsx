"use client";

import React, { useState } from "react";
import { virtualIPAPI } from "@/utils/api";

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
      const basicParts: string[] = [];
      if (contextData.basicInfo) {
        basicParts.push(contextData.basicInfo);
      }
      if (contextData.description) {
        basicParts.push(`角色描述：${contextData.description}`);
      }
      if (value) {
        basicParts.push(`${label}：${value}`);
      }
      const basicInfo = basicParts.join("\n").trim() || undefined;

      const response = await virtualIPAPI.generateAIContent({
        name: contextData.name,
        basic_info: basicInfo,
        style_preference: "现代风格",
        image_category: "portrait",
      });

      if (response.success && response.data) {
        const suggestion = response.data[aiSuggestType];
        setAiSuggestion(suggestion);
        setShowSuggestion(true);
      }
    } catch (error) {
      console.error("AI助手失败:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAcceptSuggestion = () => {
    onChange(aiSuggestion);
    setShowSuggestion(false);
  };

  const handleMergeSuggestion = () => {
    const merged = value ? `${value}\n\n${aiSuggestion}` : aiSuggestion;
    onChange(merged);
    setShowSuggestion(false);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
        {showAIAssist && aiSuggestType && contextData?.name && (
          <button
            type="button"
            onClick={handleAIAssist}
            disabled={isGenerating}
            className="flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800 disabled:opacity-50 transition-colors"
          >
            {isGenerating ? (
              <>
                <svg
                  className="animate-spin w-3 h-3"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                生成中...
              </>
            ) : (
              <>
                <svg
                  className="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
                AI助手
              </>
            )}
          </button>
        )}
      </div>

      {type === "textarea" ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          rows={rows}
          placeholder={placeholder}
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          placeholder={placeholder}
        />
      )}

      {showSuggestion && aiSuggestion && (
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-4 space-y-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                <svg
                  className="w-3 h-3 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <span className="text-sm font-medium text-purple-800">
                AI建议
              </span>
            </div>
            <button
              onClick={() => setShowSuggestion(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div className="bg-white rounded p-3 text-sm text-gray-700 border border-purple-100">
            {aiSuggestion}
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleAcceptSuggestion}
              className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-3 py-2 rounded text-xs font-medium hover:from-purple-600 hover:to-pink-600 transition-all duration-200"
            >
              采用建议
            </button>
            {value && (
              <button
                onClick={handleMergeSuggestion}
                className="flex-1 bg-purple-100 text-purple-700 px-3 py-2 rounded text-xs font-medium hover:bg-purple-200 transition-colors"
              >
                合并内容
              </button>
            )}
            <button
              onClick={() => setShowSuggestion(false)}
              className="px-3 py-2 text-xs text-gray-600 hover:text-gray-800 transition-colors"
            >
              忽略
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
