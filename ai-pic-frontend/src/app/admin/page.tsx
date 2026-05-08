"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { OperatorState } from "@/components/shared";

export default function AdminPage() {
  const router = useRouter();

  useEffect(() => {
    // 重定向到用户管理页面
    router.replace("/admin/users");
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f5f6f8]">
      <OperatorState title="进入管理控制台..." />
    </div>
  );
}
