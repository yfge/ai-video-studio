import { useCallback, useRef, useState } from "react";
import { storyStructureAPI, virtualIPAPI } from "@/utils/api/endpoints";

export type ProductionCanvasAssetOption = { id: number; name: string };

const initialState = {
  environments: [] as ProductionCanvasAssetOption[],
  error: null as string | null,
  loading: false,
  virtualIPs: [] as ProductionCanvasAssetOption[],
};

export function useProductionCanvasAssetOptions(enabled = true) {
  const [state, setState] = useState(initialState);
  const requested = useRef(false);

  const load = useCallback(async () => {
    if (!enabled || requested.current) return;
    requested.current = true;
    setState((current) => ({ ...current, error: null, loading: true }));
    try {
      const [virtualIPs, environments] = await Promise.all([
        virtualIPAPI.getVirtualIPs({ limit: 100 }),
        storyStructureAPI.listEnvironments(),
      ]);
      const errors = [
        !virtualIPs.success ? virtualIPs.error || "IP 资产加载失败" : "",
        !environments.success ? environments.error || "环境资产加载失败" : "",
      ].filter(Boolean);
      setState({
        environments:
          environments.success && Array.isArray(environments.data)
            ? environments.data
            : [],
        error: errors.join("；") || null,
        loading: false,
        virtualIPs:
          virtualIPs.success && Array.isArray(virtualIPs.data)
            ? virtualIPs.data
            : [],
      });
      if (errors.length) requested.current = false;
    } catch (error) {
      requested.current = false;
      setState({
        ...initialState,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }, [enabled]);

  return { ...state, load };
}
