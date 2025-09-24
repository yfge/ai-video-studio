'use client';

import { useState } from 'react';

export default function TestAuth() {
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const testLogin = async () => {
    setLoading(true);
    setResult('开始测试登录...');

    try {
      // 直接使用 fetch API 测试
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'username=admin&password=Ai7dio'
      });

      const data = await response.json();

      if (response.ok) {
        setResult(`✅ 登录成功！Token: ${data.access_token.substring(0, 50)}...`);
        localStorage.setItem('auth_token', data.access_token);
        
        // 测试带token的请求
        await testProtectedEndpoint(data.access_token);
      } else {
        setResult(`❌ 登录失败: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      setResult(`💥 请求异常: ${error}`);
    }

    setLoading(false);
  };

  const testProtectedEndpoint = async (token: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/virtual-ips/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setResult(prev => prev + `\n✅ 受保护接口测试成功！返回 ${data.data?.length || 0} 条数据`);
      } else {
        setResult(prev => prev + `\n❌ 受保护接口测试失败: ${response.status}`);
      }
    } catch (error) {
      setResult(prev => prev + `\n💥 受保护接口异常: ${error}`);
    }
  };

  const testApiClient = async () => {
    setLoading(true);
    setResult('测试API客户端...');

    try {
      // 动态导入API客户端（避免SSR问题）
      const { authAPI } = await import('../../utils/api');
      
      const response = await authAPI.login({
        email: 'admin',
        password: 'Ai7dio'
      });

      if (response.success && response.data) {
        setResult(`✅ API客户端登录成功！Token: ${response.data.access_token.substring(0, 50)}...`);
      } else {
        setResult(`❌ API客户端登录失败: ${response.error}`);
      }
    } catch (error) {
      setResult(`💥 API客户端异常: ${error}`);
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">🔧 认证测试页面</h1>
        
        <div className="space-y-4 mb-6">
          <button
            onClick={testLogin}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '测试中...' : '测试直接 fetch 登录'}
          </button>

          <button
            onClick={testApiClient}
            disabled={loading}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? '测试中...' : '测试 API 客户端登录'}
          </button>
        </div>

        <div className="bg-gray-100 p-4 rounded min-h-32">
          <h3 className="font-bold mb-2">测试结果:</h3>
          <pre className="text-sm whitespace-pre-wrap">{result || '点击按钮开始测试...'}</pre>
        </div>
      </div>
    </div>
  );
}