import Link from "next/link";
import type { ReactNode } from "react";
import { OperatorPanel } from "./OperatorPrimitives";

export function OperatorAuthFrame({
  title,
  subtitle,
  switchLabel,
  switchHref,
  switchText,
  children,
}: {
  title: string;
  subtitle?: string;
  switchLabel?: string;
  switchHref?: string;
  switchText?: string;
  children: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-[#f5f6f8] px-4 py-10 text-gray-950">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl items-center">
        <div className="grid w-full gap-6 lg:grid-cols-[minmax(0,1fr)_420px]">
          <section className="hidden flex-col justify-between border-l border-gray-300 pl-6 lg:flex">
            <div>
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-gray-950 text-sm font-semibold text-white">
                AI
              </div>
              <h1 className="mt-5 text-2xl font-semibold">IP 中心制作台</h1>
              <p className="mt-2 max-w-xl text-sm leading-6 text-gray-600">
                统一管理 IP、环境、故事、剧集、时间轴与生成任务。
              </p>
            </div>
            <div className="grid max-w-xl grid-cols-3 gap-3 text-xs text-gray-500">
              <span className="rounded-md border border-gray-200 bg-white px-3 py-2">
                IP 资产
              </span>
              <span className="rounded-md border border-gray-200 bg-white px-3 py-2">
                Timeline
              </span>
              <span className="rounded-md border border-gray-200 bg-white px-3 py-2">
                任务审计
              </span>
            </div>
          </section>
          <OperatorPanel className="p-6">
            <div className="mb-6">
              <div className="text-xs font-medium text-gray-500">
                Operator Access
              </div>
              <h2 className="mt-1 text-lg font-semibold text-gray-950">
                {title}
              </h2>
              {subtitle ? (
                <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
              ) : null}
              {switchHref && switchText ? (
                <p className="mt-3 text-xs text-gray-500">
                  {switchLabel}{" "}
                  <Link
                    href={switchHref}
                    className="font-medium text-blue-700 hover:text-blue-800"
                  >
                    {switchText}
                  </Link>
                </p>
              ) : null}
            </div>
            {children}
          </OperatorPanel>
        </div>
      </div>
    </main>
  );
}
