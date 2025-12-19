"use client";

interface StoriesHeaderProps {
  onGenerateClick: () => void;
}

export function StoriesHeader({ onGenerateClick }: StoriesHeaderProps) {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">故事管理</h1>
          <p className="mt-2 text-gray-600">
            管理您的短剧故事，使用AI生成创意内容
          </p>
        </div>
        <button
          onClick={onGenerateClick}
          className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
        >
          <span>🤖</span>
          AI生成故事
        </button>
      </div>
    </div>
  );
}
