"use client";

import type { Story } from "@/utils/api";

interface AdditionalInfoSectionProps {
  story: Story;
}

export function AdditionalInfoSection({ story }: AdditionalInfoSectionProps) {
  const extra =
    story.extra_metadata && typeof story.extra_metadata === "object"
      ? (story.extra_metadata as Record<string, unknown>)
      : {};

  const plotStructure =
    extra && typeof extra.plot_structure === "object"
      ? (extra.plot_structure as Record<string, string>)
      : null;

  const sellingPoints = Array.isArray(extra?.selling_points)
    ? (extra.selling_points as string[])
    : [];

  const coreValues = typeof extra?.core_values === "string" ? extra.core_values : "";
  const visualStyle = typeof extra?.visual_style === "string" ? extra.visual_style : "";

  if (!plotStructure && !coreValues && !visualStyle && sellingPoints.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4">附加信息</h2>
      {plotStructure && (
        <div className="mb-3">
          <h3 className="text-lg font-medium text-gray-800">情节结构</h3>
          <div className="text-sm text-gray-700 whitespace-pre-wrap mt-1 space-y-1">
            {plotStructure.act1 && (
              <div>
                <span className="font-medium">Act 1：</span>
                {plotStructure.act1}
              </div>
            )}
            {plotStructure.act2 && (
              <div>
                <span className="font-medium">Act 2：</span>
                {plotStructure.act2}
              </div>
            )}
            {plotStructure.act3 && (
              <div>
                <span className="font-medium">Act 3：</span>
                {plotStructure.act3}
              </div>
            )}
          </div>
        </div>
      )}
      {coreValues && (
        <div className="mb-3">
          <h3 className="text-lg font-medium text-gray-800">核心价值</h3>
          <div className="text-sm text-gray-700 whitespace-pre-wrap mt-1">
            {coreValues}
          </div>
        </div>
      )}
      {visualStyle && (
        <div className="mb-3">
          <h3 className="text-lg font-medium text-gray-800">视觉风格</h3>
          <div className="text-sm text-gray-700 whitespace-pre-wrap mt-1">
            {visualStyle}
          </div>
        </div>
      )}
      {sellingPoints.length > 0 && (
        <div className="mb-3">
          <h3 className="text-lg font-medium text-gray-800">营销卖点</h3>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            {sellingPoints.map((point, idx) => (
              <li key={idx}>{point}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
