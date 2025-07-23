'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { virtualIPAPI, virtualIPImageAPI } from '@/utils/api';
import { VirtualIP, VirtualIPImage, AIImageGenerationRequest } from '@/utils/api';

export default function VirtualIPImagesPage() {
  const params = useParams();
  const router = useRouter();
  const virtualIPId = Number(params.id);

  const [virtualIP, setVirtualIP] = useState<VirtualIP | null>(null);
  const [images, setImages] = useState<VirtualIPImage[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [uploading, setUploading] = useState(false);

  // AI生成表单状态
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [generateForm, setGenerateForm] = useState<AIImageGenerationRequest>({
    style: 'realistic',
    category: 'portrait',
    additional_prompts: '',
    is_default: false
  });

  // 上传表单状态
  const [uploadForm, setUploadForm] = useState({
    file: null as File | null,
    category: 'portrait',
    tags: '',
    is_default: false
  });

  useEffect(() => {
    loadData();
  }, [virtualIPId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [ipResponse, imagesData, categoriesData] = await Promise.all([
        virtualIPAPI.getVirtualIP(virtualIPId),
        virtualIPImageAPI.getImages(virtualIPId),
        virtualIPImageAPI.getCategories(virtualIPId)
      ]);
      
      if (ipResponse.success && ipResponse.data) {
        setVirtualIP(ipResponse.data);
      }
      setImages(imagesData);
      setCategories(categoriesData);
    } catch (error) {
      console.error('加载数据失败:', error);
      alert('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateImage = async () => {
    try {
      setGenerating(true);
      const newImage = await virtualIPImageAPI.generateImage(virtualIPId, generateForm);
      setImages(prev => [newImage, ...prev]);
      setShowGenerateForm(false);
      setGenerateForm({
        style: 'realistic',
        category: 'portrait',
        additional_prompts: '',
        is_default: false
      });
      alert('AI图像生成成功！');
    } catch (error) {
      console.error('AI图像生成失败:', error);
      alert('AI图像生成失败');
    } finally {
      setGenerating(false);
    }
  };

  const handleUploadImage = async () => {
    if (!uploadForm.file) {
      alert('请选择文件');
      return;
    }

    try {
      setUploading(true);
      const newImage = await virtualIPImageAPI.uploadImage(
        virtualIPId,
        uploadForm.file,
        uploadForm.category,
        uploadForm.tags,
        uploadForm.is_default
      );
      setImages(prev => [newImage, ...prev]);
      setUploadForm({
        file: null,
        category: 'portrait',
        tags: '',
        is_default: false
      });
      alert('图像上传成功！');
    } catch (error) {
      console.error('图像上传失败:', error);
      alert('图像上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteImage = async (imageId: number) => {
    if (!confirm('确定要删除这张图像吗？')) return;

    try {
      await virtualIPImageAPI.deleteImage(virtualIPId, imageId);
      setImages(prev => prev.filter(img => img.id !== imageId));
      alert('图像删除成功');
    } catch (error) {
      console.error('删除图像失败:', error);
      alert('删除图像失败');
    }
  };

  const handleSetDefault = async (imageId: number) => {
    try {
      await virtualIPImageAPI.setDefaultImage(virtualIPId, imageId);
      setImages(prev => prev.map(img => ({
        ...img,
        is_default: img.id === imageId
      })));
      alert('默认图像设置成功');
    } catch (error) {
      console.error('设置默认图像失败:', error);
      alert('设置默认图像失败');
    }
  };

  const filteredImages = selectedCategory 
    ? images.filter(img => img.category === selectedCategory)
    : images;

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

  if (!virtualIP) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">虚拟IP不存在</h2>
          <button
            onClick={() => router.push('/virtual-ip')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            返回列表
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
              <h1 className="text-3xl font-bold text-gray-900">
                {virtualIP.name} - 图像管理
              </h1>
              <p className="mt-2 text-gray-600">{virtualIP.description}</p>
            </div>
            <button
              onClick={() => router.push(`/virtual-ip/${virtualIPId}`)}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
            >
              返回详情
            </button>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="mb-6 flex gap-4">
          <button
            onClick={() => setShowGenerateForm(true)}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <span>🤖</span>
            AI生成图像
          </button>
          <button
            onClick={() => setShowGenerateForm(false)}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <span>📁</span>
            上传图像
          </button>
        </div>

        {/* AI生成表单 */}
        {showGenerateForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">🤖 AI图像生成</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  生成风格
                </label>
                <select
                  value={generateForm.style}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, style: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="realistic">写实风格</option>
                  <option value="anime">动漫风格</option>
                  <option value="cartoon">卡通风格</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  图像类别
                </label>
                <select
                  value={generateForm.category}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="portrait">肖像</option>
                  <option value="full_body">全身像</option>
                  <option value="scene">场景</option>
                  <option value="action">动作</option>
                  <option value="emotion">表情</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  额外提示词（可选，用逗号分隔）
                </label>
                <input
                  type="text"
                  value={generateForm.additional_prompts}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, additional_prompts: e.target.value }))}
                  placeholder="例如：微笑，阳光，户外"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={generateForm.is_default}
                    onChange={(e) => setGenerateForm(prev => ({ ...prev, is_default: e.target.checked }))}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">设为默认图像</span>
                </label>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={handleGenerateImage}
                disabled={generating}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {generating ? '生成中...' : '开始生成'}
              </button>
              <button
                onClick={() => setShowGenerateForm(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
              >
                取消
              </button>
            </div>
          </div>
        )}

        {/* 上传表单 */}
        {!showGenerateForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">📁 上传图像</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择文件
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setUploadForm(prev => ({ ...prev, file: e.target.files?.[0] || null }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  图像类别
                </label>
                <select
                  value={uploadForm.category}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="portrait">肖像</option>
                  <option value="full_body">全身像</option>
                  <option value="scene">场景</option>
                  <option value="action">动作</option>
                  <option value="emotion">表情</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  标签（可选，用逗号分隔）
                </label>
                <input
                  type="text"
                  value={uploadForm.tags}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, tags: e.target.value }))}
                  placeholder="例如：微笑，阳光，户外"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={uploadForm.is_default}
                    onChange={(e) => setUploadForm(prev => ({ ...prev, is_default: e.target.checked }))}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">设为默认图像</span>
                </label>
              </div>
            </div>
            <div className="mt-4">
              <button
                onClick={handleUploadImage}
                disabled={uploading || !uploadForm.file}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {uploading ? '上传中...' : '上传图像'}
              </button>
            </div>
          </div>
        )}

        {/* 分类筛选 */}
        <div className="mb-6">
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setSelectedCategory('')}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                selectedCategory === '' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              全部
            </button>
            {categories.map(category => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  selectedCategory === category 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* 图像网格 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredImages.map((image) => (
            <div key={image.id} className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="relative">
                <img
                  src={image.file_path}
                  alt={`${virtualIP.name} - ${image.category}`}
                  className="w-full h-48 object-cover"
                />
                {image.is_default && (
                  <div className="absolute top-2 left-2 bg-green-500 text-white px-2 py-1 rounded text-xs">
                    默认
                  </div>
                )}
                {image.metadata?.generation_method && (
                  <div className="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 rounded text-xs">
                    AI生成
                  </div>
                )}
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900">{image.category}</span>
                  <span className="text-xs text-gray-500">
                    {new Date(image.created_at).toLocaleDateString()}
                  </span>
                </div>
                {image.tags.length > 0 && (
                  <div className="mb-3">
                    <div className="flex flex-wrap gap-1">
                      {image.tags.slice(0, 3).map((tag, index) => (
                        <span
                          key={index}
                          className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                      {image.tags.length > 3 && (
                        <span className="text-gray-500 text-xs">+{image.tags.length - 3}</span>
                      )}
                    </div>
                  </div>
                )}
                <div className="flex gap-2">
                  {!image.is_default && (
                    <button
                      onClick={() => handleSetDefault(image.id)}
                      className="flex-1 bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                    >
                      设默认
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteImage(image.id)}
                    className="flex-1 bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredImages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">🖼️</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无图像</h3>
            <p className="text-gray-600">
              {selectedCategory ? `该分类下暂无图像` : '开始上传或生成图像吧！'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
} 