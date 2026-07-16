import { useEffect, useMemo, useState } from "react";
import {
  OperatorPanel,
  OperatorTabs,
  operatorButtonClass,
} from "@/components/shared";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import type {
  ProductionCanvasAccessRole,
  ProductionCanvasMediaCandidate,
} from "@/utils/api/types";
import {
  productionCanvasCapabilities,
  productionCanvasRoleLabel,
} from "./productionCanvasAccess";
import {
  CollaborationMembers,
  collaboratorRoles,
} from "./ProductionCanvasCollaborationMembers";
import {
  CollaborationActivity,
  CollaborationComments,
  type CommentTarget,
} from "./ProductionCanvasCollaborationViews";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import type { ProductionCanvasSection } from "./productionCanvasSectionModel";
import { useProductionCanvasCollaboration } from "./useProductionCanvasCollaboration";

type CollaborationTab = "comments" | "activity" | "members";

function edgeTarget(edge: ProductionCanvasEdge): CommentTarget {
  const id = edge.edgeId || `${edge.from}->${edge.to}`;
  return {
    id,
    key: `edge:${id}`,
    label: `连线 · ${edge.from} → ${edge.to}`,
    type: "edge",
  };
}

export function ProductionCanvasCollaborationPanel({
  accessRole,
  edges,
  node,
  nodes,
  runId,
  sections,
}: {
  accessRole: ProductionCanvasAccessRole | null;
  edges: ProductionCanvasEdge[];
  node?: ProductionCanvasNode;
  nodes: ProductionCanvasNode[];
  runId: string;
  sections: ProductionCanvasSection[];
}) {
  const collaboration = useProductionCanvasCollaboration(runId);
  const [tab, setTab] = useState<CollaborationTab>("comments");
  const [body, setBody] = useState("");
  const [targetKey, setTargetKey] = useState("");
  const [username, setUsername] = useState("");
  const [role, setRole] =
    useState<(typeof collaboratorRoles)[number]>("viewer");
  const [candidates, setCandidates] = useState<
    ProductionCanvasMediaCandidate[]
  >([]);
  const effectiveRole = collaboration.data?.access_role || accessRole;
  const capabilities = productionCanvasCapabilities(effectiveRole);
  const nodeId = node?.id;

  useEffect(() => {
    let active = true;
    setCandidates([]);
    if (
      !runId ||
      !node ||
      ![
        "image.candidates",
        "storyboard.candidates",
        "video.candidates",
      ].includes(node.skill || "")
    ) {
      return () => {
        active = false;
      };
    }
    void productionCanvasAPI
      .getNodeCandidates(runId, node.id)
      .then((response) => {
        if (active && response.success && response.data) {
          setCandidates(response.data.candidates || []);
        }
      });
    return () => {
      active = false;
    };
  }, [node, runId]);

  const targets = useMemo<CommentTarget[]>(
    () => [
      ...nodes.map((item) => ({
        id: item.id,
        key: `node:${item.id}`,
        label: `节点 · ${item.label}`,
        type: "node" as const,
      })),
      ...candidates.map((item) => ({
        id: String(item.asset_id),
        key: `candidate:${item.asset_id}`,
        label: `${item.media_type === "image" ? "图片" : "视频"}候选 · #${
          item.asset_id
        }`,
        type: "candidate" as const,
      })),
      ...edges.map(edgeTarget),
      ...sections.map((item) => ({
        id: item.id,
        key: `section:${item.id}`,
        label: `分区 · ${item.title}`,
        type: "section" as const,
      })),
    ],
    [candidates, edges, nodes, sections],
  );

  useEffect(() => {
    setTargetKey((current) =>
      targets.some((item) => item.key === current)
        ? current
        : nodeId
        ? `node:${nodeId}`
        : targets[0]?.key || "",
    );
  }, [nodeId, targets]);

  useEffect(() => {
    if (nodeId) setTargetKey(`node:${nodeId}`);
  }, [nodeId]);

  if (!runId) return null;
  const target = targets.find((item) => item.key === targetKey);
  const comments = (collaboration.data?.comments || []).filter(
    (item) =>
      item.target_type === target?.type && item.target_id === target?.id,
  );
  const submitComment = async () => {
    if (!target || !body.trim()) return;
    const updated = await collaboration.addComment({
      target_type: target.type,
      target_id: target.id,
      body: body.trim(),
    });
    if (updated) setBody("");
  };

  return (
    <OperatorPanel className="overflow-hidden">
      <div className="flex items-center justify-between gap-2 px-4 pt-4">
        <div>
          <div className="text-sm font-semibold text-gray-950">协作</div>
          <div className="mt-1 text-[11px] text-gray-500">
            {effectiveRole
              ? productionCanvasRoleLabel[effectiveRole]
              : "正在确认权限"}
          </div>
        </div>
        <button
          type="button"
          className={operatorButtonClass("ghost", "h-7 px-2 text-xs")}
          disabled={Boolean(collaboration.busy)}
          onClick={() => void collaboration.load()}
        >
          刷新
        </button>
      </div>
      <OperatorTabs
        active={tab}
        onChange={setTab}
        tabs={[
          { key: "comments", label: "评论" },
          { key: "activity", label: "活动" },
          { key: "members", label: "成员" },
        ]}
      />
      <div className="p-4">
        {tab === "comments" ? (
          <CollaborationComments
            body={body}
            busy={Boolean(collaboration.busy)}
            canComment={capabilities.comment}
            comments={comments}
            onBodyChange={setBody}
            onSubmit={() => void submitComment()}
            onTargetChange={setTargetKey}
            target={target}
            targetKey={targetKey}
            targets={targets}
          />
        ) : null}
        {tab === "activity" ? (
          <CollaborationActivity
            activity={collaboration.data?.activity || []}
          />
        ) : null}
        {tab === "members" ? (
          <CollaborationMembers
            capabilities={capabilities}
            collaboration={collaboration}
            role={role}
            setRole={setRole}
            setUsername={setUsername}
            username={username}
          />
        ) : null}
        {collaboration.error ? (
          <p className="mt-3 text-xs leading-5 text-red-600" role="alert">
            {collaboration.error}
          </p>
        ) : null}
      </div>
    </OperatorPanel>
  );
}
