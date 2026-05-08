"use client";

import { useState } from "react";
import {
  OperatorAuthFrame,
  OperatorPanel,
  OperatorSectionHeader,
  operatorButtonClass,
} from "@/components/shared";

export default function TestAuth() {
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const testProtectedEndpoint = async (token: string) => {
    try {
      const response = await fetch("/api/v1/virtual-ips/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setResult((prev) => `${prev}\n受保护接口成功，返回 ${data.data?.length || 0} 条`);
      } else {
        setResult((prev) => `${prev}\n受保护接口失败: ${response.status}`);
      }
    } catch (error) {
      setResult((prev) => `${prev}\n受保护接口异常: ${error}`);
    }
  };

  const testLogin = async () => {
    setLoading(true);
    setResult("开始测试登录...");
    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "username=admin&password=Ai7dio",
      });
      const data = await response.json();
      if (response.ok) {
        setResult(`登录成功。Token: ${data.access_token.substring(0, 50)}...`);
        localStorage.setItem("auth_token", data.access_token);
        await testProtectedEndpoint(data.access_token);
      } else {
        setResult(`登录失败: ${data.detail || "Unknown error"}`);
      }
    } catch (error) {
      setResult(`请求异常: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const testApiClient = async () => {
    setLoading(true);
    setResult("测试 API 客户端...");
    try {
      const { authAPI } = await import("@/utils/api/endpoints");
      const response = await authAPI.login({ email: "admin", password: "Ai7dio" });
      if (response.success && response.data) {
        setResult(
          `API 客户端登录成功。Token: ${response.data.access_token.substring(0, 50)}...`,
        );
      } else {
        setResult(`API 客户端登录失败: ${response.error}`);
      }
    } catch (error) {
      setResult(`API 客户端异常: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <OperatorAuthFrame
      title="认证诊断"
      subtitle="验证登录接口和受保护接口"
      switchLabel="返回"
      switchHref="/login"
      switchText="登录页"
    >
      <OperatorPanel>
        <OperatorSectionHeader title="诊断操作" subtitle="fetch 与 API client" />
        <div className="space-y-3 p-4">
          <button
            type="button"
            onClick={testLogin}
            disabled={loading}
            className={operatorButtonClass("primary", "w-full")}
          >
            {loading ? "测试中..." : "测试直接 fetch 登录"}
          </button>
          <button
            type="button"
            onClick={testApiClient}
            disabled={loading}
            className={operatorButtonClass("secondary", "w-full")}
          >
            {loading ? "测试中..." : "测试 API 客户端登录"}
          </button>
          <div className="min-h-32 rounded-md border border-gray-200 bg-gray-50 p-3">
            <h3 className="mb-2 text-xs font-semibold text-gray-500">测试结果</h3>
            <pre className="whitespace-pre-wrap text-xs text-gray-700">
              {result || "点击按钮开始测试..."}
            </pre>
          </div>
        </div>
      </OperatorPanel>
    </OperatorAuthFrame>
  );
}
