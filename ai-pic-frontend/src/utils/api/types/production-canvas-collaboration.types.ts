export type ProductionCanvasAccessRole =
  | "owner"
  | "viewer"
  | "commenter"
  | "editor"
  | "approver";

export type ProductionCanvasCommentTargetType =
  | "node"
  | "candidate"
  | "edge"
  | "section";

export interface ProductionCanvasCollaborator {
  user_id: number;
  username: string;
  role: Exclude<ProductionCanvasAccessRole, "owner">;
  added_by: number;
  added_at: string;
}

export interface ProductionCanvasComment {
  comment_id: string;
  target_type: ProductionCanvasCommentTargetType;
  target_id: string;
  body: string;
  author_id: number;
  author_username: string;
  created_at: string;
}

export interface ProductionCanvasActivity {
  activity_id: string;
  action: string;
  actor_id: number;
  actor_username: string;
  target_type?: string | null;
  target_id?: string | null;
  detail?: string | null;
  created_at: string;
}

export interface ProductionCanvasCollaborationResponse {
  access_role: ProductionCanvasAccessRole;
  collaborators: ProductionCanvasCollaborator[];
  comments: ProductionCanvasComment[];
  activity: ProductionCanvasActivity[];
}

export interface ProductionCanvasCollaboratorRequest {
  username: string;
  role: ProductionCanvasCollaborator["role"];
}

export interface ProductionCanvasCommentRequest {
  target_type: ProductionCanvasCommentTargetType;
  target_id: string;
  body: string;
}
