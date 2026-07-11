import { useCallback, useRef, useState } from "react";
import {
  episodeAPI,
  scriptAPI,
  storyStructureAPI,
  virtualIPAPI,
} from "@/utils/api/endpoints";

export type ProductionCanvasAssetOption = { id: number; name: string };

const initialState = {
  environments: [] as ProductionCanvasAssetOption[],
  episodes: [] as ProductionCanvasAssetOption[],
  error: null as string | null,
  loading: false,
  scripts: [] as ProductionCanvasAssetOption[],
  scriptsLoading: false,
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
      const [virtualIPs, environments, episodes] = await Promise.all([
        virtualIPAPI.getVirtualIPs({ limit: 100 }),
        storyStructureAPI.listEnvironments(),
        episodeAPI.getEpisodes({ limit: 100 }),
      ]);
      const errors = [
        !virtualIPs.success ? virtualIPs.error || "IP 资产加载失败" : "",
        !environments.success ? environments.error || "环境资产加载失败" : "",
        !episodes.success ? episodes.error || "剧集加载失败" : "",
      ].filter(Boolean);
      setState({
        environments:
          environments.success && Array.isArray(environments.data)
            ? environments.data
            : [],
        episodes:
          episodes.success && Array.isArray(episodes.data)
            ? episodes.data.map((episode) => ({
                id: episode.id,
                name: `第 ${episode.episode_number} 集 · ${episode.title}`,
              }))
            : [],
        error: errors.join("；") || null,
        loading: false,
        scripts: [],
        scriptsLoading: false,
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

  const loadScripts = useCallback(
    async (episodeId: string) => {
      const parsedEpisodeId = Number(episodeId);
      if (
        !enabled ||
        !Number.isInteger(parsedEpisodeId) ||
        parsedEpisodeId < 1
      ) {
        setState((current) => ({ ...current, scripts: [] }));
        return;
      }
      setState((current) => ({
        ...current,
        error: null,
        scripts: [],
        scriptsLoading: true,
      }));
      try {
        const response = await scriptAPI.getScripts({
          episode_id: parsedEpisodeId,
          limit: 100,
        });
        setState((current) => ({
          ...current,
          error: response.success ? null : response.error || "剧本加载失败",
          scripts:
            response.success && Array.isArray(response.data)
              ? response.data.map((script) => ({
                  id: script.id,
                  name: script.title,
                }))
              : [],
          scriptsLoading: false,
        }));
      } catch (error) {
        setState((current) => ({
          ...current,
          error: error instanceof Error ? error.message : String(error),
          scripts: [],
          scriptsLoading: false,
        }));
      }
    },
    [enabled],
  );

  return { ...state, load, loadScripts };
}
