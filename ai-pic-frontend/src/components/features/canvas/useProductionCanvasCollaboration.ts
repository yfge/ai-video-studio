import { useCallback, useEffect, useState } from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import type {
  ProductionCanvasCollaborationResponse,
  ProductionCanvasCollaboratorRequest,
  ProductionCanvasCommentRequest,
} from "@/utils/api/types";

export function useProductionCanvasCollaboration(runId: string) {
  const [data, setData] =
    useState<ProductionCanvasCollaborationResponse | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apply = useCallback(
    (response: {
      success: boolean;
      data?: ProductionCanvasCollaborationResponse;
      error?: string;
    }) => {
      if (!response.success || !response.data) {
        throw new Error(response.error || "协作数据更新失败");
      }
      setData(response.data);
      return response.data;
    },
    [],
  );

  const load = useCallback(async () => {
    if (!runId) {
      setData(null);
      return;
    }
    setBusy("load");
    setError(null);
    try {
      apply(await productionCanvasAPI.getCollaboration(runId));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(null);
    }
  }, [apply, runId]);

  useEffect(() => {
    void load();
  }, [load]);

  const mutate = async (
    key: string,
    request: () => Promise<{
      success: boolean;
      data?: ProductionCanvasCollaborationResponse;
      error?: string;
    }>,
  ) => {
    if (!runId || busy) return null;
    setBusy(key);
    setError(null);
    try {
      return apply(await request());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      return null;
    } finally {
      setBusy(null);
    }
  };

  return {
    addComment: (request: ProductionCanvasCommentRequest) =>
      mutate("comment", () => productionCanvasAPI.addComment(runId, request)),
    busy,
    data,
    error,
    load,
    removeCollaborator: (userId: number) =>
      mutate(`remove:${userId}`, () =>
        productionCanvasAPI.removeCollaborator(runId, userId),
      ),
    upsertCollaborator: (request: ProductionCanvasCollaboratorRequest) =>
      mutate(`member:${request.username}`, () =>
        productionCanvasAPI.upsertCollaborator(runId, request),
      ),
  };
}
