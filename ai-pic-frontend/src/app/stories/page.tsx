'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { storyAPI, virtualIPAPI } from '@/utils/api';
import type { Story, VirtualIP, StoryGenerationRequest } from '@/utils/api';
import { AIModelType } from '@/utils/api';
import Navigation from '@/components/Navigation';
import AuthGuard from '@/components/AuthGuard';
import { useAlertModal } from '@/components/AlertModalProvider';
import { MultiModelSelector } from '@/components/MultiModelSelector';
import { CreationOverlay } from '@/components/CreationOverlay';

function StoriesPageContent() {
  const router = useRouter();
  const { showAlert } = useAlertModal();
  const [stories, setStories] = useState<Story[]>([]);
  const [virtualIPs, setVirtualIPs] = useState<VirtualIP[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showGenerateForm, setShowGenerateForm] = useState(false);

  // 筛选状态
  const [selectedGenre, setSelectedGenre] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  // 生成表单状态
  const [generateForm, setGenerateForm] = useState<StoryGenerationRequest>({
    title: '',
    genre: 'drama',
    theme: '',
    target_audience: '',
    duration_minutes: 30,
    character_ids: [],
    setting_time: '',
    setting_location: '',
    world_building: '',
    additional_requirements: '',
    style_preferences: [],
    content_restrictions: [],
    tags: [],
    model: '',
    temperature: 0.7
  });
  const [promptPreview, setPromptPreview] = useState<string>('');
  const [showPromptPreview, setShowPromptPreview] = useState<boolean>(false);
  const [useAsync, setUseAsync] = useState<boolean>(true);

  const genres = [
    { value: 'drama', label: '剧情' },
    { value: 'comedy', label: '喜剧' },
    { value: 'romance', label: '爱情' },
    { value: 'thriller', label: '惊悚' },
    { value: 'action', label: '动作' },
    { value: 'fantasy', label: '奇幻' },
    { value: 'sci-fi', label: '科幻' },
    { value: 'horror', label: '恐怖' },
    { value: 'mystery', label: '悬疑' },
    { value: 'historical', label: '历史' }
  ];

  const statuses = [
    { value: '', label: '全部状态' },
    { value: 'draft', label: '草稿' },
    { value: 'approved', label: '已批准' },
    { value: 'published', label: '已发布' }
  ];

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [storiesResponse, virtualIPsResponse] = await Promise.all([
        storyAPI.getStories({
          genre: selectedGenre || undefined,
          status: selectedStatus || undefined,
          limit: 50
        }),
        virtualIPAPI.getVirtualIPs()
      ]);

      if (storiesResponse.success && storiesResponse.data) {
        setStories(storiesResponse.data);
      }
      if (virtualIPsResponse.success && virtualIPsResponse.data) {
        setVirtualIPs(virtualIPsResponse.data);
      }
    } catch (error) {
      console.error('加载数据失败:', error);
      showAlert({ message: '加载数据失败', variant: 'error' });
    } finally {
      setLoading(false);
    }
  }, [selectedGenre, selectedStatus, showAlert]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleGenerateStory = async () => {
    if (!generateForm.title || generateForm.character_ids.length === 0) {
      showAlert({ message: '请填写标题并选择至少一个角色', variant: 'warning' });
      return;
    }

    try {
      setGenerating(true);
      if (useAsync) {
        const response = await storyAPI.generateStoryAsync(generateForm);
        if (response.success) {
          showAlert({ message: '已创建异步任务，稍后在任务页查看进度', variant: 'info' });
        } else {
          showAlert({ message: `故事生成失败：${response.error || '未知错误'}`, variant: 'error' });
        }
      } else {
        const response = await storyAPI.generateStory(generateForm);
        if (response.success && response.data) {
          setStories(prev => [response.data as Story, ...prev]);
        } else {
          showAlert({ message: `故事生成失败：${response.error || '未知错误'}`, variant: 'error' });
        }
      }
        setShowGenerateForm(false);
        setGenerateForm({
          title: '',
          genre: 'drama',
          theme: '',
          target_audience: '',
          duration_minutes: 30,
          character_ids: [],
          setting_time: '',
          setting_location: '',
          world_building: '',
          additional_requirements: '',
          style_preferences: [],
          content_restrictions: [],
          tags: [],
          model: '',
          temperature: 0.7
        });
        setPromptPreview('');
        showAlert({ message: '故事生成成功！', variant: 'success' });
    } catch (error) {
      console.error('故事生成失败:', error);
      showAlert({ message: '故事生成失败', variant: 'error' });
    } finally {
      setGenerating(false);
    }
  };

  const performDeleteStory = async (storyBusinessId: string) => {
    try {
      const response = await storyAPI.deleteStory(storyBusinessId);
      if (response.success) {
        setStories(prev => prev.filter(story => story.business_id !== storyBusinessId));
        showAlert({ message: '故事删除成功', variant: 'success' });
      } else {
        showAlert({ message: `删除失败：${response.error || '未知错误'}`, variant: 'error' });
      }
    } catch (error) {
      console.error('删除故事失败:', error);
      showAlert({ message: '删除故事失败', variant: 'error' });
    }
  };

  const handleDeleteStory = (storyBusinessId: string) => {
    showAlert({
      title: '确认删除',
      message: '确定要删除这个故事吗？',
      variant: 'warning',
      confirmText: '删除',
      onConfirm: () => {
        void performDeleteStory(storyBusinessId);
      },
    });
  };

  const handleCharacterToggle = (characterId: number) => {
    setGenerateForm(prev => ({
      ...prev,
      character_ids: prev.character_ids.includes(characterId)
        ? prev.character_ids.filter(id => id !== characterId)
        : [...prev.character_ids, characterId]
    }));
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation title="故事管理" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 头部 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">故事管理</h1>
              <p className="mt-2 text-gray-600">管理您的短剧故事，使用AI生成创意内容</p>
            </div>
            <button
              onClick={() => setShowGenerateForm(true)}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <span>🤖</span>
              AI生成故事
            </button>
          </div>
        </div>

        {/* 筛选器 */}
        <div className="mb-6 flex gap-4 flex-wrap">
          <select
            value={selectedGenre}
            onChange={(e) => setSelectedGenre(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部类型</option>
            {genres.map(genre => (
              <option key={genre.value} value={genre.value}>
                {genre.label}
              </option>
            ))}
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {statuses.map(status => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
        </div>

        {/* 故事列表 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stories.map((story) => (
            <div key={story.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900 truncate">{story.title}</h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${story.status === 'published' ? 'bg-green-100 text-green-800' :
                    story.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                    {story.status === 'published' ? '已发布' :
                      story.status === 'approved' ? '已批准' : '草稿'}
                  </span>
                </div>

                <div className="mb-3">
                  <span className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
                    {genres.find(g => g.value === story.genre)?.label || story.genre}
                  </span>
                  {story.theme && (
                    <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full ml-2">
                      {story.theme}
                    </span>
                  )}
                </div>

                <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                  {story.synopsis || story.premise || '暂无概要'}
                </p>

                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  <span>时长: {story.duration_minutes || '--'}分钟</span>
                  <span>{new Date(story.created_at).toLocaleDateString()}</span>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => router.push(`/stories/${story.business_id}`)}
                    className="flex-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700"
                  >
                    查看详情
                  </button>
                  <button
                    onClick={() => handleDeleteStory(story.business_id)}
                    className="bg-red-600 text-white px-3 py-2 rounded text-sm hover:bg-red-700"
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {stories.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📚</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无故事</h3>
            <p className="text-gray-600 mb-4">开始创作您的第一个故事吧！</p>
            <button
              onClick={() => setShowGenerateForm(true)}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
            >
              AI生成故事
            </button>
          </div>
        )}
      </div>

      <CreationOverlay
        open={showGenerateForm}
        title="AI生成故事"
        subtitle="与环境/虚拟IP一致的创建面板，补充角色与设定后提交生成"
        onClose={() => setShowGenerateForm(false)}
        icon={<span className="text-lg">📚</span>}
        widthClassName="max-w-5xl"
      >
        <form className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                故事标题 *
              </label>
              <input
                type="text"
                value={generateForm.title}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, title: e.target.value }))}
                placeholder="输入故事标题"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                故事类型
              </label>
              <select
                value={generateForm.genre}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, genre: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {genres.map(genre => (
                  <option key={genre.value} value={genre.value}>
                    {genre.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                故事主题
              </label>
              <input
                type="text"
                value={generateForm.theme}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, theme: e.target.value }))}
                placeholder="例如：友情、成长、冒险"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                目标受众
              </label>
              <input
                type="text"
                value={generateForm.target_audience}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, target_audience: e.target.value }))}
                placeholder="例如：青少年、成人、儿童"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                预计总时长（分钟）
              </label>
              <input
                type="number"
                value={generateForm.duration_minutes}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, duration_minutes: parseInt(e.target.value) || 30 }))}
                min="1"
                max="300"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <MultiModelSelector
              label="选择模型"
              value={generateForm.model ? [generateForm.model] : []}
              onChange={ids => setGenerateForm(prev => ({ ...prev, model: ids[0] || '' }))}
              modelType={AIModelType.Text}
              multiple={false}
              helperText="为空将由后端自动挑选最佳提供商与模型（故事生成推荐使用支持 JSON Schema 的模型）"
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                温度（0.0 - 1.5）
              </label>
              <input
                type="range"
                min="0"
                max="1.5"
                step="0.1"
                value={generateForm.temperature ?? 0.7}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                className="w-full"
              />
              <div className="text-sm text-gray-600">当前温度：{generateForm.temperature?.toFixed(1)}</div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              选择角色 * (至少选择一个)
              <span className="text-blue-600 ml-2">
                已选择: {generateForm.character_ids.length} 个
              </span>
            </label>

            {virtualIPs.length === 0 ? (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <div className="text-gray-400 text-4xl mb-2">👥</div>
                <p className="text-gray-600 mb-2">暂无可用角色</p>
                <p className="text-sm text-gray-500 mb-4">
                  请先创建虚拟IP角色，然后再生成故事
                </p>
                <button
                  type="button"
                  onClick={() => router.push('/virtual-ip')}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  创建虚拟IP
                </button>
              </div>
            ) : (
              <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto">
                  {virtualIPs.map(ip => (
                    <label
                      key={ip.id}
                      className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-all ${generateForm.character_ids.includes(ip.id)
                        ? 'border-blue-500 bg-blue-50 shadow-md'
                        : 'border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300'
                        }`}
                    >
                      <input
                        type="checkbox"
                        checked={generateForm.character_ids.includes(ip.id)}
                        onChange={() => handleCharacterToggle(ip.id)}
                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 mr-3"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">{ip.name}</div>
                        <div className="text-sm text-gray-500 line-clamp-2">{ip.description}</div>
                        {ip.tags && ip.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {ip.tags.slice(0, 2).map((tag, index) => (
                              <span key={index} className="inline-block bg-gray-200 text-gray-700 text-xs px-1 py-0.5 rounded">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </label>
                  ))}
                </div>

                {generateForm.character_ids.length > 0 && (
                  <div className="mt-3 p-2 bg-blue-100 rounded-lg">
                    <p className="text-sm text-blue-800">
                      ✅ 已选择角色: {generateForm.character_ids.map(id => {
                        const ip = virtualIPs.find(v => v.id === id);
                        return ip?.name;
                      }).filter(Boolean).join(', ')}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                时间设定
              </label>
              <input
                type="text"
                value={generateForm.setting_time}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, setting_time: e.target.value }))}
                placeholder="例如：现代、古代、未来"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                地点设定
              </label>
              <input
                type="text"
                value={generateForm.setting_location}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, setting_location: e.target.value }))}
                placeholder="例如：学校、城市、乡村"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              世界观设定
            </label>
            <textarea
              value={generateForm.world_building}
              onChange={(e) => setGenerateForm(prev => ({ ...prev, world_building: e.target.value }))}
              placeholder="描述故事的世界观和背景设定"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              额外要求
            </label>
            <textarea
              value={generateForm.additional_requirements}
              onChange={(e) => setGenerateForm(prev => ({ ...prev, additional_requirements: e.target.value }))}
              placeholder="其他特殊要求或偏好"
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <button
              type="button"
              onClick={async () => {
                try {
                  if (!generateForm.title || generateForm.character_ids.length === 0) {
                    setShowPromptPreview(true);
                    setPromptPreview('请填写标题并至少选择一个角色后再预览提示词');
                    return;
                  }
                  setShowPromptPreview(true);
                  setPromptPreview('加载中...');
                  const res = await storyAPI.previewStoryPrompt(generateForm);
                  if (res.success && res.data) {
                    setPromptPreview(res.data.prompt ?? '（空内容）');
                  } else {
                    setPromptPreview('生成提示词失败');
                  }
                } catch {
                  setPromptPreview('预览出错');
                }
              }}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
            >
              生成提示词预览
            </button>
            {showPromptPreview && (
              <div className="mt-3 p-3 border rounded bg-gray-50 max-h-64 overflow-auto">
                <pre className="whitespace-pre-wrap break-words text-sm font-mono text-gray-800">{promptPreview}</pre>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <input
              id="asyncToggle"
              type="checkbox"
              checked={useAsync}
              onChange={(e) => setUseAsync(e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="asyncToggle" className="text-sm text-gray-700">使用异步任务（推荐，支持队列）</label>
          </div>

          <div className="flex justify-end gap-3 border-t pt-4">
            <button
              type="button"
              onClick={() => setShowGenerateForm(false)}
              className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600"
            >
              取消
            </button>
            <button
              type="button"
              onClick={handleGenerateStory}
              disabled={generating}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {generating ? '生成中...' : (useAsync ? '创建异步任务' : '开始生成')}
            </button>
          </div>
        </form>
      </CreationOverlay>
    </div>
  );
}

export default function StoriesPage() {
  return (
    <AuthGuard>
      <StoriesPageContent />
    </AuthGuard>
  )
}
