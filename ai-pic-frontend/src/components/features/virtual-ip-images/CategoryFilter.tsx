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
    <div className="mb-6">
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => onSelectCategory("")}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${
            selectedCategory === ""
              ? "bg-blue-600 text-white"
              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
          }`}
        >
          全部
        </button>
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => onSelectCategory(category)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              selectedCategory === category
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            {getCategoryLabel(category)}
          </button>
        ))}
      </div>
    </div>
  );
}
