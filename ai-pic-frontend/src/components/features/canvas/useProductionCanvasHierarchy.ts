import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Story } from "@/utils/api/types";
import {
  mergeHierarchyGraphs,
  projectVisibleHierarchy,
  type HierarchyGraph,
  type HierarchyNode,
} from "./productionCanvasHierarchyModel";
import {
  loadHierarchyBranch,
  loadHierarchyStories,
} from "./productionCanvasHierarchyLoader";
import {
  revealProductionCanvasHierarchy,
  type ProductionCanvasHierarchySyncContext,
} from "./productionCanvasHierarchyReveal";

const emptyGraph: HierarchyGraph = { edges: [], nodes: [] };

export function useProductionCanvasHierarchy() {
  const alive = useRef(true);
  const epoch = useRef(0);
  const inFlight = useRef(new Map<string, number>());
  const rootRequest = useRef(0);
  const stories = useRef<{ epoch: number; items: Story[] } | null>(null);
  const storiesRequest = useRef<{
    epoch: number;
    promise: Promise<Story[]>;
  } | null>(null);
  const [graph, setGraph] = useState<HierarchyGraph>(emptyGraph);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [loadedIds, setLoadedIds] = useState<Set<string>>(new Set());
  const [loadingIds, setLoadingIds] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [rootError, setRootError] = useState<string | null>(null);
  const [rootLoading, setRootLoading] = useState(false);
  const [warning, setWarning] = useState<string | null>(null);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const loadStories = useCallback(async (requestEpoch: number) => {
    if (stories.current?.epoch === requestEpoch) return stories.current.items;
    if (storiesRequest.current?.epoch === requestEpoch) {
      return storiesRequest.current.promise;
    }
    const promise = loadHierarchyStories().then((result) => {
      if (alive.current && epoch.current === requestEpoch) {
        stories.current = { epoch: requestEpoch, items: result.items };
        if (result.warning) setWarning(result.warning);
      }
      return result.items;
    });
    storiesRequest.current = { epoch: requestEpoch, promise };
    const clearRequest = () => {
      if (storiesRequest.current?.promise === promise)
        storiesRequest.current = null;
    };
    void promise.then(clearRequest, clearRequest);
    return promise;
  }, []);

  const loadBranch = useCallback(
    async (node: HierarchyNode) => {
      const requestEpoch = epoch.current;
      if (
        node.empty ||
        !node.expandable ||
        inFlight.current.get(node.id) === requestEpoch
      )
        return;
      inFlight.current.set(node.id, requestEpoch);
      setLoadingIds((current) => new Set(current).add(node.id));
      setErrors((current) => {
        const next = { ...current };
        delete next[node.id];
        return next;
      });
      try {
        const result = await loadHierarchyBranch(node, () =>
          loadStories(requestEpoch),
        );
        if (!alive.current || epoch.current !== requestEpoch) return;
        setGraph((current) => mergeHierarchyGraphs(current, result.branch));
        setLoadedIds((current) => new Set(current).add(node.id));
        setExpandedIds((current) => new Set(current).add(node.id));
        if (result.warning) {
          setErrors((current) => ({ ...current, [node.id]: result.warning! }));
        }
      } catch (error) {
        if (alive.current && epoch.current === requestEpoch) {
          setErrors((current) => ({
            ...current,
            [node.id]: error instanceof Error ? error.message : String(error),
          }));
        }
      } finally {
        if (inFlight.current.get(node.id) === requestEpoch) {
          inFlight.current.delete(node.id);
        }
        if (alive.current && epoch.current === requestEpoch) {
          setLoadingIds((current) => {
            const next = new Set(current);
            next.delete(node.id);
            return next;
          });
        }
      }
    },
    [loadStories],
  );

  const toggleNode = useCallback(
    (nodeId: string) => {
      const node = graph.nodes.find((item) => item.id === nodeId);
      if (!node || !node.expandable || node.empty) return;
      if (expandedIds.has(nodeId)) {
        setExpandedIds((current) => {
          const next = new Set(current);
          next.delete(nodeId);
          return next;
        });
        return;
      }
      if (loadedIds.has(nodeId)) {
        setExpandedIds((current) => new Set(current).add(nodeId));
        return;
      }
      void loadBranch(node);
    },
    [expandedIds, graph.nodes, loadBranch, loadedIds],
  );

  const cancelPendingReveal = useCallback(() => {
    epoch.current += 1;
    rootRequest.current += 1;
    inFlight.current.clear();
    setLoadingIds(new Set());
    setRootLoading(false);
  }, []);

  const refreshAndReveal = useCallback(
    async (context: ProductionCanvasHierarchySyncContext) => {
      const requestEpoch = epoch.current + 1;
      epoch.current = requestEpoch;
      rootRequest.current += 1;
      stories.current = null;
      storiesRequest.current = null;
      inFlight.current.clear();
      setRootLoading(true);
      setRootError(null);
      setErrors({});
      try {
        const result = await revealProductionCanvasHierarchy(context);
        if (!alive.current || epoch.current !== requestEpoch) return null;
        setGraph(result.graph);
        setExpandedIds(result.expandedIds);
        setLoadedIds(result.loadedIds);
        setLoadingIds(new Set());
        setWarning(result.warning);
        return result.targetNodeId;
      } catch (error) {
        if (alive.current && epoch.current === requestEpoch) {
          setRootError(error instanceof Error ? error.message : String(error));
        }
        return null;
      } finally {
        if (alive.current && epoch.current === requestEpoch) {
          setRootLoading(false);
        }
      }
    },
    [],
  );

  const projection = useMemo(
    () => projectVisibleHierarchy(graph, expandedIds),
    [expandedIds, graph],
  );

  return {
    cancelPendingReveal,
    errors,
    expandedIds,
    graph,
    loadingIds,
    projection,
    refreshAndReveal,
    rootError,
    rootLoading,
    toggleNode,
    warning,
  };
}
