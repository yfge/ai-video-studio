'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { storyAPI, episodeAPI } from '@/utils/api';
import { Story, Episode, EpisodeGenerationRequest } from '@/utils/api';

export default function StoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const storyId = Number(params.id);

  const [story, setStory] = useState<Story | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showGenerateForm, setShowGenerateForm] = useState(false);

  // 剧集生成表单状态
  const [generateForm, setGenerateForm] = useState<EpisodeGenerationRequest>({
    story_id: storyId,
    episode_count: 5,
    episode_duration: 30,
    focus_characters: [],
    plot_complexity: 'medium',
    pacing: 'medium',
    additional_requirements: '',
    style_preferences: []
  });

  useEffect(() => {
    loadData();
  }, [storyId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [storyResponse, episodesResponse] = await Promise.all([
        storyAPI.getStory(storyId),
        episodeAPI.getStoryEpisodes(storyId)
      ]);

      if (storyResponse.success && storyResponse.data) {
        setStory(storyResponse.data);
      }
      if (episodesResponse.success && episodesResponse.data) {
        setEpisodes(episodesResponse.data);
      }
    } catch (error) {
      console.error('加载数据失败:', error);
      alert('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateEpisodes = async () => {
    try {
      setGenerating(true);
      const response = await episodeAPI.generateEpisodes(generateForm);
      
      if (response.success && response.data) {
        setEpisodes(prev => [...prev, ...response.data!]);
        setShowGenerateForm(false);
        alert(`成功生成${response.data.length}集剧集！`);
      } else {
        alert('剧集生成失败：' + (response.error || '未知错误'));
      }
    } catch (error) {
      console.error('剧集生成失败:', error);
      alert('剧集生成失败');
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteEpisode = async (episodeId: number) => {
    if (!confirm('确定要删除这个剧集吗？')) return;

    try {
      const response = await episodeAPI.deleteEpisode(episodeId);
      if (response.success) {
        setEpisodes(prev => prev.filter(episode => episode.id !== episodeId));
        alert('剧集删除成功');
      } else {
        alert('删除失败：' + (response.error || '未知错误'));
      }
    } catch (error) {
      console.error('删除剧集失败:', error);
      alert('删除剧集失败');
    }
  };

  const handleRegenerateEpisode = async (episodeId: number) => {
    if (!confirm('确定要重新生成这个剧集吗？')) return;

    try {
      const response = await episodeAPI.regenerateEpisode(episodeId);
      if (response.success && response.data) {
        setEpisodes(prev => prev.map(ep => 
          ep.id === episodeId ? response.data! : ep
        ));
        alert('剧集重新生成成功');
      } else {
        alert('重新生成失败：' + (response.error || '未知错误'));
      }
    } catch (error) {
      console.error('重新生成剧集失败:', error);
      alert('重新生成剧集失败');
    }
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

  if (!story) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">故事不存在</h2>
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 头部 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{story.title}</h1>
              <p className="mt-2 text-gray-600">
                {story.genre} • {story.theme} • {story.duration_minutes}分钟
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push('/stories')}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                返回列表
              </button>
              <button
                onClick={() => setShowGenerateForm(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                生成剧集
              </button>
            </div>
          </div>
        </div>

        {/* 故事信息 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">故事概要</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">故事前提</h3>
              <p className="text-gray-600 mb-4">{story.premise || '暂无'}</p>
              
              <h3 className="font-medium text-gray-900 mb-2">主要冲突</h3>
              <p className="text-gray-600 mb-4">{story.main_conflict || '暂无'}</p>
              
              <h3 className="font-medium text-gray-900 mb-2">解决方案</h3>
              <p className="text-gray-600">{story.resolution || '暂无'}</p>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900 mb-2">详细概要</h3>
              <p className="text-gray-600 mb-4">{story.synopsis || '暂无'}</p>
              
              <h3 className="font-medium text-gray-900 mb-2">设定信息</h3>
              <div className="space-y-2 text-sm">
                <div><span className="font-medium">时间:</span> {story.setting_time || '现代'}</div>
                <div><span className="font-medium">地点:</span> {story.setting_location || '待定'}</div>
                <div><span className="font-medium">目标受众:</span> {story.target_audience || '普通观众'}</div>
              </div>
              
              {story.world_building && (
                <>
                  <h3 className="font-medium text-gray-900 mb-2 mt-4">世界观设定</h3>
                  <p className="text-gray-600 text-sm">{story.world_building}</p>
                </>
              )}
            </div>
          </div>
        </div>

        {/* 剧集生成表单 */}
        {showGenerateForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">🎬 生成剧集</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  剧集数量
                </label>
                <input
                  type="number"
                  value={generateForm.episode_count}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, episode_count: parseInt(e.target.value) || 5 }))}
                  min="1"
                  max="50"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  每集时长（分钟）
                </label>
                <input
                  type="number"
                  value={generateForm.episode_duration}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, episode_duration: parseInt(e.target.value) || 30 }))}
                  min="1"
                  max="120"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  情节复杂度
                </label>
                <select
                  value={generateForm.plot_complexity}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, plot_complexity: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="simple">简单</option>
                  <option value="medium">中等</option>
                  <option value="complex">复杂</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  节奏
                </label>
                <select
                  value={generateForm.pacing}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, pacing: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="slow">慢节奏</option>
                  <option value="medium">中等节奏</option>
                  <option value="fast">快节奏</option>
                </select>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                额外要求
              </label>
              <textarea
                value={generateForm.additional_requirements}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, additional_requirements: e.target.value }))}
                placeholder="对剧集生成的特殊要求"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleGenerateEpisodes}
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

        {/* 剧集列表 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">剧集列表</h2>
            <span className="text-sm text-gray-500">共 {episodes.length} 集</span>
          </div>

          {episodes.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-4">🎬</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">暂无剧集</h3>
              <p className="text-gray-600 mb-4">开始生成您的第一个剧集吧！</p>
              <button
                onClick={() => setShowGenerateForm(true)}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
              >
                生成剧集
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {episodes.map((episode) => (
                <div key={episode.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                          第{episode.episode_number}集
                        </span>
                        <h3 className="font-medium text-gray-900">{episode.title}</h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          episode.status === 'published' ? 'bg-green-100 text-green-800' :
                          episode.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {episode.status === 'published' ? '已发布' :
                           episode.status === 'approved' ? '已批准' : '草稿'}
                        </span>
                      </div>
                      
                      <p className="text-gray-600 text-sm mb-2 line-clamp-2">
                        {episode.summary || '暂无概要'}
                      </p>
                      
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>时长: {episode.duration_minutes || '--'}分钟</span>
                        <span>场景: {episode.scene_count || '--'}个</span>
                        <span>创建: {new Date(episode.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => router.push(`/episodes/${episode.id}`)}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        查看详情
                      </button>
                      <button
                        onClick={() => handleRegenerateEpisode(episode.id)}
                        className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                      >
                        重新生成
                      </button>
                      <button
                        onClick={() => handleDeleteEpisode(episode.id)}
                        className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 