import type { Environment } from '@/utils/api'

interface EnvironmentHeaderProps {
  env: Environment
  onBack: () => void
}

export function EnvironmentHeader({ env, onBack }: EnvironmentHeaderProps) {
  return (
    <div className="flex items-start justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{env.name}</h1>
        <p className="text-sm text-gray-500 mt-1">
          类别：{env.category || '未指定'} · 创建于{' '}
          {new Date(env.created_at).toLocaleString()}
        </p>
        {env.tags && env.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {env.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        {env.description && (
          <p className="mt-3 text-gray-700 whitespace-pre-wrap">
            {env.description}
          </p>
        )}
      </div>
      <button
        onClick={onBack}
        className="text-blue-600 hover:text-blue-800"
      >
        返回列表
      </button>
    </div>
  )
}
