import {
  operatorButtonClass,
  operatorInputClass,
  operatorSelectClass,
} from "@/components/shared";
import type { ProductionCanvasCollaborator } from "@/utils/api/types";
import type { ProductionCanvasCapabilities } from "./productionCanvasAccess";
import { productionCanvasRoleLabel } from "./productionCanvasAccess";
import type { useProductionCanvasCollaboration } from "./useProductionCanvasCollaboration";

export const collaboratorRoles = [
  "viewer",
  "commenter",
  "editor",
  "approver",
] as const;

type Collaboration = ReturnType<typeof useProductionCanvasCollaboration>;

export function CollaborationMembers({
  capabilities,
  collaboration,
  role,
  setRole,
  setUsername,
  username,
}: {
  capabilities: ProductionCanvasCapabilities;
  collaboration: Collaboration;
  role: ProductionCanvasCollaborator["role"];
  setRole: (role: ProductionCanvasCollaborator["role"]) => void;
  setUsername: (username: string) => void;
  username: string;
}) {
  const members = collaboration.data?.collaborators || [];
  return (
    <div className="space-y-3">
      {capabilities.manage ? (
        <div className="grid gap-2 border-b border-gray-100 pb-3">
          <input
            aria-label="协作者用户名"
            className={operatorInputClass("w-full")}
            placeholder="用户名"
            value={username}
            onChange={(event) => setUsername(event.currentTarget.value)}
            onInput={(event) => setUsername(event.currentTarget.value)}
          />
          <div className="flex gap-2">
            <select
              aria-label="协作者角色"
              className={operatorSelectClass("min-w-0 flex-1")}
              value={role}
              onChange={(event) =>
                setRole(event.currentTarget.value as typeof role)
              }
            >
              {collaboratorRoles.map((item) => (
                <option key={item} value={item}>
                  {productionCanvasRoleLabel[item]}
                </option>
              ))}
            </select>
            <button
              type="button"
              className={operatorButtonClass("primary")}
              disabled={!username.trim() || Boolean(collaboration.busy)}
              onClick={() =>
                void collaboration
                  .upsertCollaborator({ username: username.trim(), role })
                  .then((updated) => updated && setUsername(""))
              }
            >
              添加
            </button>
          </div>
        </div>
      ) : null}
      {members.map((member) => (
        <div key={member.user_id} className="flex items-center gap-2">
          <div className="min-w-0 flex-1 truncate text-xs font-semibold text-gray-800">
            {member.username}
          </div>
          {capabilities.manage ? (
            <select
              aria-label={`${member.username} 角色`}
              className={operatorSelectClass("w-24")}
              disabled={Boolean(collaboration.busy)}
              value={member.role}
              onChange={(event) =>
                void collaboration.upsertCollaborator({
                  username: member.username,
                  role: event.currentTarget.value as typeof member.role,
                })
              }
            >
              {collaboratorRoles.map((item) => (
                <option key={item} value={item}>
                  {productionCanvasRoleLabel[item]}
                </option>
              ))}
            </select>
          ) : (
            <span className="text-[11px] text-gray-500">
              {productionCanvasRoleLabel[member.role]}
            </span>
          )}
          {capabilities.manage ? (
            <button
              type="button"
              aria-label={`移除 ${member.username}`}
              className={operatorButtonClass(
                "ghost",
                "h-7 px-2 text-xs text-red-600",
              )}
              disabled={Boolean(collaboration.busy)}
              onClick={() =>
                void collaboration.removeCollaborator(member.user_id)
              }
            >
              移除
            </button>
          ) : null}
        </div>
      ))}
      {!members.length ? (
        <p className="text-xs text-gray-400">暂无协作者</p>
      ) : null}
    </div>
  );
}
