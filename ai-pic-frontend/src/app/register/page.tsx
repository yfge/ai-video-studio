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

type RegisterForm = {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
};

const fields: Array<{
  name: keyof RegisterForm;
  label: string;
  type: string;
  autoComplete: string;
  placeholder: string;
}> = [
  { name: "username", label: "用户名", type: "text", autoComplete: "username", placeholder: "请输入用户名" },
  { name: "email", label: "邮箱地址", type: "email", autoComplete: "email", placeholder: "请输入邮箱地址" },
  { name: "password", label: "密码", type: "password", autoComplete: "new-password", placeholder: "至少 6 位" },
  { name: "confirmPassword", label: "确认密码", type: "password", autoComplete: "new-password", placeholder: "请再次输入密码" },
];

export default function Register() {
  const router = useRouter();
  const [formData, setFormData] = useState<RegisterForm>({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof RegisterForm, string>>>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [serverSuccess, setServerSuccess] = useState<string | null>(null);

  const validateForm = () => {
    const next: Partial<Record<keyof RegisterForm, string>> = {};
    if (!formData.username.trim()) next.username = "用户名不能为空";
    if (!formData.email.trim()) next.email = "邮箱不能为空";
    else if (!/\S+@\S+\.\S+/.test(formData.email)) next.email = "邮箱格式不正确";
    if (formData.password.length < 6) next.password = "密码至少6位";
    if (formData.password !== formData.confirmPassword) {
      next.confirmPassword = "两次密码不一致";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!validateForm()) return;
    setIsLoading(true);
    setServerError(null);
    try {
      const res = await authAPI.register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        full_name: formData.username,
      });
      if (res.success) {
        setServerSuccess("注册成功，即将跳转登录页");
        router.push("/login?registered=1");
      } else {
        setServerError(res.message || "注册失败，请稍后重试");
      }
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "注册失败，请稍后重试");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const name = event.target.name as keyof RegisterForm;
    setFormData((prev) => ({ ...prev, [name]: event.target.value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  return (
    <OperatorAuthFrame
      title="创建操作员账户"
      subtitle="注册后进入统一 IP 中心工作台"
      switchLabel="已有账户？"
      switchHref="/login"
      switchText="登录"
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        {serverError ? <OperatorState title={serverError} tone="red" /> : null}
        {serverSuccess ? <OperatorState title={serverSuccess} tone="green" /> : null}
        {fields.map((field) => (
          <label key={field.name} className="block text-xs font-medium text-gray-600">
            {field.label}
            <input
              id={field.name}
              name={field.name}
              type={field.type}
              autoComplete={field.autoComplete}
              required
              className={operatorInputClass("mt-1 w-full")}
              placeholder={field.placeholder}
              value={formData[field.name]}
              onChange={handleChange}
            />
            {errors[field.name] ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors[field.name]}
              </span>
            ) : null}
          </label>
        ))}
        <button
          type="submit"
          disabled={isLoading}
          className={operatorButtonClass("primary", "w-full")}
        >
          {isLoading ? "注册中..." : "注册"}
        </button>
      </form>
    </OperatorAuthFrame>
  );
}
