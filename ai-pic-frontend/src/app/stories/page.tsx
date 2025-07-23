'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { storyAPI, virtualIPAPI } from '@/utils/api';
import { Story, VirtualIP, StoryGenerationRequest } from '@/utils/api';

export default function StoriesPage() {
  const router = useRouter();
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
    tags: []
  });

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

  useEffect(() => {
    loadData();
  }, [selectedGenre, selectedStatus]);

  const loadData = async () => {
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
      alert('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateStory = async () => {
    if (!generateForm.title || generateForm.character_ids.length === 0) {
      alert('请填写标题并选择至少一个角色');
      return;
    }

    try {
      setGenerating(true);
      const response = await storyAPI.generateStory(generateForm);
      
      if (response.success && response.data) {
        setStories(prev => [response.data!, ...prev]);
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
          tags: []
        });
        alert('故事生成成功！');
      } else {
        alert('故事生成失败：' + (response.error || '未知错误'));
      }
    } catch (error) {
      console.error('故事生成失败:', error);
      alert('故事生成失败');
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteStory = async (storyId: number) => {
    if (!confirm('确定要删除这个故事吗？')) return;

    try {
      const response = await storyAPI.deleteStory(storyId);
      if (response.success) {
        setStories(prev => prev.filter(story => story.id !== storyId));
        alert('故事删除成功');
      } else {
        alert('删除失败：' + (response.error || '未知错误'));
      }
    } catch (error) {
      console.error('删除故事失败:', error);
      alert('删除故事失败');
    }
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

        {/* AI生成表单 */}
        {showGenerateForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">🤖 AI故事生成</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
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
            </div>

            {/* 角色选择 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                选择角色 * (至少选择一个)
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 max-h-48 overflow-y-auto">
                {virtualIPs.map(ip => (
                  <label key={ip.id} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={generateForm.character_ids.includes(ip.id)}
                      onChange={() => handleCharacterToggle(ip.id)}
                      className="mr-3"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{ip.name}</div>
                      <div className="text-sm text-gray-500 truncate">{ip.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
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

            <div className="mb-4">
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

            <div className="mb-4">
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

            <div className="flex gap-2">
              <button
                onClick={handleGenerateStory}
                disabled={generating}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {generating ? '生成中...' : '开始生成'}
              </button>
              <button
                onClick={() => setShowGenerateForm(false)}
                className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600"
              >
                取消
              </button>
            </div>
          </div>
        )}

        {/* 故事列表 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stories.map((story) => (
            <div key={story.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900 truncate">{story.title}</h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    story.status === 'published' ? 'bg-green-100 text-green-800' :
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
                    onClick={() => router.push(`/stories/${story.id}`)}
                    className="flex-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700"
                  >
                    查看详情
                  </button>
                  <button
                    onClick={() => handleDeleteStory(story.id)}
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
    </div>
  );
} 