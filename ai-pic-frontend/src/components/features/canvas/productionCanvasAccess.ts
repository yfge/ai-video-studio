import type { ProductionCanvasAccessRole } from "@/utils/api/types";

export type ProductionCanvasCapabilities = {
  approve: boolean;
  comment: boolean;
  edit: boolean;
  execute: boolean;
  manage: boolean;
  view: boolean;
};

const none: ProductionCanvasCapabilities = {
  approve: false,
  comment: false,
  edit: false,
  execute: false,
  manage: false,
  view: false,
};

export function productionCanvasCapabilities(
  role: ProductionCanvasAccessRole | null,
): ProductionCanvasCapabilities {
  if (!role) return none;
  return {
    approve: role === "owner" || role === "approver",
    comment: role !== "viewer",
    edit: role === "owner" || role === "editor",
    execute: role === "owner",
    manage: role === "owner",
    view: true,
  };
}

export const productionCanvasRoleLabel: Record<
  ProductionCanvasAccessRole,
  string
> = {
  owner: "所有者",
  viewer: "查看者",
  commenter: "评论者",
  editor: "编辑者",
  approver: "审批者",
};
