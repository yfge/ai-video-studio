import { StatusPill, operatorButtonClass } from "@/components/shared";
import type { AdminUser } from "@/utils/api/types";
import { formatRelativeTime, getUserRole, getUserStatus } from "@/utils/auth";

const statusTone = (user: AdminUser) => {
  if (!user.is_approved) return "amber";
  if (user.is_active === false) return "red";
  return "green";
};

export function AdminUserRow({
  user,
  processing,
  onApprove,
  onVerifyEmail,
  onDetails,
}: {
  user: AdminUser;
  processing: boolean;
  onApprove: () => void;
  onVerifyEmail: () => void;
  onDetails: () => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 px-4 py-3">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-gray-950">
            {user.full_name || user.username}
          </span>
          <StatusPill tone={statusTone(user)}>{getUserStatus(user)}</StatusPill>
          <StatusPill tone={user.is_superuser ? "blue" : "gray"}>
            {getUserRole(user)}
          </StatusPill>
        </div>
        <p className="mt-1 truncate text-xs text-gray-500">
          {user.email} · 注册 {formatRelativeTime(user.created_at)}
          {user.last_login_at
            ? ` · 最后登录 ${formatRelativeTime(user.last_login_at)}`
            : ""}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {!user.is_approved ? (
          <button
            type="button"
            onClick={onApprove}
            disabled={processing}
            className={operatorButtonClass("secondary")}
          >
            处理审批
          </button>
        ) : null}
        {!user.email_verified && user.is_approved ? (
          <button
            type="button"
            onClick={onVerifyEmail}
            disabled={processing}
            className={operatorButtonClass("primary")}
          >
            验证邮箱
          </button>
        ) : null}
        <button
          type="button"
          onClick={onDetails}
          className={operatorButtonClass("ghost")}
        >
          详情
        </button>
      </div>
    </div>
  );
}

export function AdminUserPagination({
  page,
  pages,
  total,
  onPage,
}: {
  page: number;
  pages: number;
  total: number;
  onPage: (page: number) => void;
}) {
  return (
    <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3 text-xs text-gray-500">
      <span>
        第 {page} / {pages} 页 · 共 {total} 个结果
      </span>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => onPage(Math.max(1, page - 1))}
          className={operatorButtonClass("secondary")}
        >
          上一页
        </button>
        <button
          type="button"
          disabled={page >= pages}
          onClick={() => onPage(Math.min(pages, page + 1))}
          className={operatorButtonClass("secondary")}
        >
          下一页
        </button>
      </div>
    </div>
  );
}
