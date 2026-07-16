"use client";

import Image from "next/image";
import Link from "next/link";
import {
  OperatorPanel,
  OperatorPagination,
  OperatorSectionHeader,
  OperatorState,
  type OperatorPaginationModel,
  operatorButtonClass,
  operatorInputClass,
} from "@/components/shared";
import type { VirtualIP } from "@/utils/api/types";
import { resolveCreatorLabel } from "@/utils/creator";

interface VirtualIPListSectionProps {
  loading: boolean;
  virtualIPs: VirtualIP[];
  searchTerm: string;
  onSearchTermChange: (value: string) => void;
  allTags: string[];
  selectedTags: string[];
  onToggleTag: (tag: string) => void;
  onOpenCreate: () => void;
  onDelete: (bizId: string) => void;
  pagination?: OperatorPaginationModel;
}

export function VirtualIPListSection({
  loading,
  virtualIPs,
  searchTerm,
  onSearchTermChange,
  allTags,
  selectedTags,
  onToggleTag,
  onOpenCreate,
  onDelete,
  pagination,
}: VirtualIPListSectionProps) {
  return (
    <div className="space-y-5">
      <OperatorPanel>
        <OperatorSectionHeader
          title="IP 资产筛选"
          subtitle={`${pagination?.total ?? virtualIPs.length} 个可用 IP 项目`}
          action={
            <button
              type="button"
              onClick={onOpenCreate}
              className={operatorButtonClass("primary")}
            >
              创建 IP
            </button>
          }
        />
        <div className="space-y-3 p-4">
          <input
            type="text"
            placeholder="搜索 IP 名称、标签、创作者"
            value={searchTerm}
            onChange={(event) => onSearchTermChange(event.target.value)}
            className={operatorInputClass("w-full md:w-80")}
          />
          {allTags.length ? (
            <div className="flex flex-wrap gap-2">
              {allTags.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => onToggleTag(tag)}
                  className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                    selectedTags.includes(tag)
                      ? "border-blue-200 bg-blue-50 text-blue-700"
                      : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </OperatorPanel>

      {loading ? (
        <OperatorState title="加载 IP 资产..." />
      ) : virtualIPs.length === 0 ? (
        <OperatorState
          title="暂无 IP 项目"
          detail="先创建一个 IP，再从故事生产链路选择角色资产。"
          action={
            <button
              type="button"
              onClick={onOpenCreate}
              className={operatorButtonClass("primary")}
            >
              创建 IP
            </button>
          }
        />
      ) : (
        <>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {virtualIPs.map((ip) => (
              <IPProjectCard key={ip.business_id} ip={ip} onDelete={onDelete} />
            ))}
          </div>
          {pagination ? (
            <OperatorPagination {...pagination} itemLabel="IP 项目" />
          ) : null}
        </>
      )}
    </div>
  );
}

function IPProjectCard({
  ip,
  onDelete,
}: {
  ip: VirtualIP;
  onDelete: (bizId: string) => void;
}) {
  const createdAt = new Date(ip.created_at).toLocaleDateString("zh-CN");
  return (
    <article className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <IPAvatar ip={ip} />
          <div className="min-w-0">
            <h3 className="truncate text-sm font-semibold text-gray-950">
              {ip.name}
            </h3>
            <p className="mt-1 text-xs text-gray-500">
              {resolveCreatorLabel(ip.creator)} · {createdAt}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 gap-2">
          <Link
            href={`/virtual-ip/${ip.business_id}`}
            className={operatorButtonClass("ghost")}
          >
            详情
          </Link>
          <button
            type="button"
            onClick={() => onDelete(ip.business_id)}
            className="h-8 rounded-md px-2 text-xs font-medium text-red-600 hover:bg-red-50 whitespace-nowrap"
          >
            删除
          </button>
        </div>
      </div>

      {ip.description ? (
        <p className="mt-4 line-clamp-3 text-sm leading-6 text-gray-600">
          {ip.description}
        </p>
      ) : (
        <p className="mt-4 text-sm text-gray-400">暂无 IP 简介</p>
      )}

      <TagList tags={ip.tags ?? []} />

      <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-3 text-xs text-gray-500">
        <span>{ip.background_story ? "背景故事已补充" : "背景故事待补充"}</span>
        <Link
          href={`/virtual-ip/${ip.business_id}`}
          className="font-medium text-blue-600 hover:text-blue-700"
        >
          查看详情
        </Link>
      </div>
    </article>
  );
}

function IPAvatar({ ip }: { ip: VirtualIP }) {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-gray-200 bg-gray-50 text-xs font-semibold text-gray-500">
      {ip.default_avatar_url ? (
        <Image
          src={ip.default_avatar_url}
          alt={ip.name}
          width={40}
          height={40}
          className="h-10 w-10 rounded-md object-cover"
          unoptimized
        />
      ) : (
        ip.name.slice(0, 1).toUpperCase()
      )}
    </div>
  );
}

function TagList({ tags }: { tags: string[] }) {
  if (!tags.length) return null;
  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {tags.slice(0, 5).map((tag) => (
        <span
          key={tag}
          className="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-600"
        >
          {tag}
        </span>
      ))}
    </div>
  );
}
