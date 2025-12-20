'use client'

interface VirtualIPTagsFieldProps {
  tags: string[]
  addTag: (tag: string) => void
  removeTag: (tag: string) => void
}

export function VirtualIPTagsField({ tags, addTag, removeTag }: VirtualIPTagsFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">标签</label>
      <div className="flex flex-wrap gap-2 mb-2">
        {tags.map((tag) => (
          <span
            key={tag}
            className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full flex items-center"
          >
            {tag}
            <button type="button" onClick={() => removeTag(tag)} className="ml-1 text-blue-600 hover:text-blue-800">
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
            if (e.key === 'Enter') {
              e.preventDefault()
              const input = e.target as HTMLInputElement
              addTag(input.value.trim())
              input.value = ''
            }
          }}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          type="button"
          onClick={(e) => {
            const input = e.currentTarget.previousElementSibling as HTMLInputElement
            addTag(input.value.trim())
            input.value = ''
          }}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
        >
          添加
        </button>
      </div>
    </div>
  )
}
