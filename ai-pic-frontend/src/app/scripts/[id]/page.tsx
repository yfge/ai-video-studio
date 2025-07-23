'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { scriptAPI } from '@/utils/api';
import { Script } from '@/utils/api';

export default function ScriptDetailPage() {
  const params = useParams();
  const router = useRouter();
  const scriptId = Number(params.id);

  const [script, setScript] = useState<Script | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFullContent, setShowFullContent] = useState(false);

  useEffect(() => {
    loadScript();
  }, [scriptId]);

  const loadScript = async () => {
    try {
      setLoading(true);
      const response = await scriptAPI.getScript(scriptId);
      
      if (response.success && response.data) {
        setScript(response.data);
      } else {
        alert('加载剧本失败：' + (response.error || '未知错误'));
      }
    } catch (error) {
      console.error('加载剧本失败:', error);
      alert('加载剧本失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: string) => {
    try {
      const response = await scriptAPI.exportScript(scriptId, format);
      if (response.success) {
        alert(`剧本已导出为 ${format.toUpperCase()} 格式`);
      } else {
        alert('导出失败：' + (response.error || '未知错误'));
      }
    } catch (error) {
      console.error('导出剧本失败:', error);
      alert('导出剧本失败');
    }
  };

  const formatContent = (content: string) => {
    if (!content) return '';
    
    // 简单的格式化处理
    return content
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
      .join('\n');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!script) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">剧本不存在</h2>
          <button
            onClick={() => router.push('/stories')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            返回故事列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 头部 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{script.title}</h1>
              <p className="mt-2 text-gray-600">
                {script.format_type} • {script.language} • v{script.version}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push(`/episodes/${script.episode_id}`)}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                返回剧集
              </button>
              <div className="relative">
                <button
                  onClick={() => setShowFullContent(!showFullContent)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  导出剧本
                </button>
                {showFullContent && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10">
                    <div className="py-1">
                      <button
                        onClick={() => handleExport('txt')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        导出为 TXT
                      </button>
                      <button
                        onClick={() => handleExport('pdf')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        导出为 PDF
                      </button>
                      <button
                        onClick={() => handleExport('docx')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        导出为 DOCX
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 剧本信息 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">剧本信息</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">字数:</span>
              <span className="ml-2 text-gray-600">{script.word_count || 0}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">字符数:</span>
              <span className="ml-2 text-gray-600">{script.character_count || 0}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">页数:</span>
              <span className="ml-2 text-gray-600">{script.page_count || 0}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">状态:</span>
              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                script.status === 'published' ? 'bg-green-100 text-green-800' :
                script.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {script.status === 'published' ? '已发布' :
                 script.status === 'approved' ? '已批准' : '草稿'}
              </span>
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-500">
            <div>创建时间: {new Date(script.created_at).toLocaleString()}</div>
            <div>更新时间: {new Date(script.updated_at).toLocaleString()}</div>
          </div>
        </div>

        {/* 剧本内容 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">剧本内容</h2>
            <button
              onClick={() => setShowFullContent(!showFullContent)}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              {showFullContent ? '收起' : '展开全部'}
            </button>
          </div>

          {script.content ? (
            <div className="bg-gray-50 rounded-lg p-4">
              <pre className={`whitespace-pre-wrap text-sm leading-relaxed font-mono ${
                showFullContent ? '' : 'max-h-96 overflow-hidden'
              }`}>
                {formatContent(script.content)}
              </pre>
              {!showFullContent && script.content.length > 1000 && (
                <div className="mt-4 text-center">
                  <button
                    onClick={() => setShowFullContent(true)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    显示更多内容...
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-4">📝</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">暂无内容</h3>
              <p className="text-gray-600">剧本内容正在生成中或生成失败</p>
            </div>
          )}
        </div>

        {/* 场景和对话信息 */}
        {(script.scenes && script.scenes.length > 0) || (script.dialogues && script.dialogues.length > 0) ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            {/* 场景列表 */}
            {script.scenes && script.scenes.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-4">场景列表</h3>
                <div className="space-y-2">
                  {script.scenes.map((scene, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded text-sm">
                      <div className="font-medium text-gray-900 mb-1">
                        场景 {index + 1}
                      </div>
                      <div className="text-gray-600">
                        {typeof scene === 'string' ? scene : JSON.stringify(scene)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 对话列表 */}
            {script.dialogues && script.dialogues.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-4">主要对话</h3>
                <div className="space-y-2">
                  {script.dialogues.slice(0, 10).map((dialogue, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded text-sm">
                      <div className="text-gray-600">
                        {typeof dialogue === 'string' ? dialogue : JSON.stringify(dialogue)}
                      </div>
                    </div>
                  ))}
                  {script.dialogues.length > 10 && (
                    <div className="text-center text-gray-500 text-sm">
                      还有 {script.dialogues.length - 10} 段对话...
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : null}

        {/* 舞台指示 */}
        {script.stage_directions && script.stage_directions.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mt-6">
            <h3 className="text-lg font-semibold mb-4">舞台指示</h3>
            <div className="space-y-2">
              {script.stage_directions.map((direction, index) => (
                <div key={index} className="bg-yellow-50 p-3 rounded text-sm">
                  <div className="text-gray-600">
                    {typeof direction === 'string' ? direction : JSON.stringify(direction)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 生成信息 */}
        {script.generation_prompt && (
          <div className="bg-white rounded-lg shadow-md p-6 mt-6">
            <h3 className="text-lg font-semibold mb-4">生成信息</h3>
            <div className="space-y-3">
              <div>
                <span className="font-medium text-gray-700">AI模型:</span>
                <span className="ml-2 text-gray-600">{script.ai_model || '未知'}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">生成提示词:</span>
                <div className="mt-2 bg-gray-50 p-3 rounded text-sm text-gray-600">
                  {script.generation_prompt}
                </div>
              </div>
              {script.generation_params && (
                <div>
                  <span className="font-medium text-gray-700">生成参数:</span>
                  <div className="mt-2 bg-gray-50 p-3 rounded text-sm text-gray-600">
                    <pre>{JSON.stringify(script.generation_params, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 