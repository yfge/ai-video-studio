"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  OperatorAuthFrame,
  OperatorState,
  operatorButtonClass,
  operatorInputClass,
} from "@/components/shared";
import { authAPI } from "@/utils/api/endpoints";

export default function Login() {
  const router = useRouter();
  const [formData, setFormData] = useState({ username: "", password: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      const response = await authAPI.login({
        email: formData.username,
        password: formData.password,
      });
      if (!response.success || !response.data) {
        throw new Error(response.error || "登录失败");
      }
      localStorage.setItem("auth_token", response.data.access_token);
      localStorage.setItem(
        "user_info",
        JSON.stringify({
          username: formData.username,
          token: response.data.access_token,
        }),
      );
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败，请稍后重试");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [event.target.name]: event.target.value,
    }));
  };

  return (
    <OperatorAuthFrame
      title="登录到制作台"
      subtitle="使用账号进入 IP 中心生产工作流"
      switchLabel="没有账户？"
      switchHref="/register"
      switchText="注册新账户"
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        {error ? <OperatorState title={error} tone="red" /> : null}
        <label className="block text-xs font-medium text-gray-600">
          用户名
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            required
            className={operatorInputClass("mt-1 w-full")}
            placeholder="用户名"
            value={formData.username}
            onChange={handleChange}
          />
        </label>
        <label className="block text-xs font-medium text-gray-600">
          密码
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            className={operatorInputClass("mt-1 w-full")}
            placeholder="密码"
            value={formData.password}
            onChange={handleChange}
          />
        </label>
        <button
          type="submit"
          disabled={isLoading}
          className={operatorButtonClass("primary", "w-full")}
        >
          {isLoading ? "登录中..." : "登录"}
        </button>
      </form>
    </OperatorAuthFrame>
  );
}
