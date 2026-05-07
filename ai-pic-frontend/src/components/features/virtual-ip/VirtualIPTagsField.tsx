"use client";

interface VirtualIPTagsFieldProps {
  tags: string[];
  addTag: (tag: string) => void;
  removeTag: (tag: string) => void;
}

export function VirtualIPTagsField({
  tags,
  addTag,
  removeTag,
}: VirtualIPTagsFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        标签
      </label>
      <div className="flex flex-wrap gap-2 mb-2">
        {tags.map((tag) => (
          <span
            key={tag}
            className="flex items-center rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-xs text-blue-700"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              className="ml-1 text-blue-500 hover:text-blue-700"
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="输入标签"
          onKeyPress={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              const input = e.target as HTMLInputElement;
              addTag(input.value.trim());
              input.value = "";
            }
          }}
          className="h-8 flex-1 rounded-md border border-gray-200 px-3 text-xs focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
        />
        <button
          type="button"
          onClick={(e) => {
            const input = e.currentTarget
              .previousElementSibling as HTMLInputElement;
            addTag(input.value.trim());
            input.value = "";
          }}
          className="h-8 rounded-md border border-gray-200 bg-white px-3 text-xs text-gray-700 hover:bg-gray-50"
        >
          添加
        </button>
      </div>
    </div>
  );
}
