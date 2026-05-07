"use client";

import { getCategoryLabel } from "./categoryLabel";

interface CategoryFilterProps {
  categories: string[];
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
}

export function CategoryFilter({
  categories,
  selectedCategory,
  onSelectCategory,
}: CategoryFilterProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <h3 className="mb-3 text-sm font-semibold text-gray-950">图片分类</h3>
      <div className="space-y-1">
        <button
          type="button"
          onClick={() => onSelectCategory("")}
          className={`flex h-8 w-full items-center justify-between rounded-md px-2 text-xs font-medium ${
            selectedCategory === ""
              ? "bg-blue-50 text-blue-700"
              : "text-gray-600 hover:bg-gray-50"
          }`}
        >
          全部
        </button>
        {categories.map((category) => (
          <button
            key={category}
            type="button"
            onClick={() => onSelectCategory(category)}
            className={`flex h-8 w-full items-center justify-between rounded-md px-2 text-xs font-medium ${
              selectedCategory === category
                ? "bg-blue-50 text-blue-700"
                : "text-gray-600 hover:bg-gray-50"
            }`}
          >
            {getCategoryLabel(category)}
          </button>
        ))}
      </div>
    </div>
  );
}
