"use client";

import { useEffect, useState } from "react";
import { storyStructureAPI } from "@/utils/api/endpoints";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  operatorButtonClass,
} from "@/components/shared";

export type SceneNode = {
  id: number;
  scene_number: string;
  slug_line?: string;
  location?: string;
  time_of_day?: string;
  status?: string;
  beats: BeatNode[];
  shots: ShotNode[];
};

type BeatNode = {
  id: number;
  order_index: number;
  beat_summary?: string;
};

type ShotNode = {
  id: number;
  shot_number: string;
  shot_type?: string;
  scene_beat_id?: number;
};

type StructureApi = {
  getNormalizedScenes: (scriptId: number) => Promise<ApiResult<SceneNode[]>>;
  getNormalizedSceneBeats: (sceneId: number) => Promise<ApiResult<BeatNode[]>>;
  getNormalizedSceneShots: (sceneId: number) => Promise<ApiResult<ShotNode[]>>;
  createScene: (
    scriptId: number,
    payload: { script_id: number; scene_number: string; slug_line: string; status?: string },
  ) => Promise<ApiResult<unknown>>;
  createSceneBeat: (
    sceneId: number,
    payload: { scene_id: number; order_index: number; beat_summary?: string },
  ) => Promise<ApiResult<unknown>>;
  createSceneShot: (
    sceneId: number,
    payload: { scene_id: number; shot_number: string; scene_beat_id?: number; shot_type?: string },
  ) => Promise<ApiResult<unknown>>;
  updateSceneBeat: (beatId: number, payload: Partial<{ order_index: number }>) => Promise<ApiResult<unknown>>;
  updateSceneShot: (shotId: number, payload: Partial<{ shot_number: string }>) => Promise<ApiResult<unknown>>;
  deleteSceneBeat: (beatId: number) => Promise<ApiResult<unknown>>;
  deleteSceneShot: (shotId: number) => Promise<ApiResult<unknown>>;
};

type ApiResult<T> = {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
};

export function SceneStructurePanel({
  scriptId,
  canEdit,
  onStructureLoaded,
  apiOverride,
}: {
  scriptId: number;
  canEdit: boolean;
  onStructureLoaded?: (scenes: SceneNode[]) => void;
  apiOverride?: StructureApi;
}) {
  const { showAlert } = useAlertModal();
  const client: StructureApi = (apiOverride ?? storyStructureAPI) as StructureApi;
  const [scenes, setScenes] = useState<SceneNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStructure = async () => {
    setLoading(true);
    setError(null);
    try {
      const sceneRes = await client.getNormalizedScenes(scriptId);
      if (!sceneRes.success || !sceneRes.data) {
        throw new Error(sceneRes.message || sceneRes.error || "加载场景失败");
      }
      const hydrated = await Promise.all(
        sceneRes.data.map(async (scene) => {
          const [beatsRes, shotsRes] = await Promise.all([
            client.getNormalizedSceneBeats(scene.id),
            client.getNormalizedSceneShots(scene.id),
          ]);
          return {
            ...scene,
            beats: beatsRes.data || [],
            shots: shotsRes.data || [],
          };
        }),
      );
      setScenes(hydrated);
      onStructureLoaded?.(hydrated);
    } catch (err) {
      const message = err instanceof Error ? err.message : "加载结构失败";
      setError(message);
      showAlert({ message, variant: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadStructure();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scriptId]);

  const addScene = async () => {
    if (!canEdit) {
      showAlert({ message: "当前为只读模式，需管理员权限", variant: "warning" });
      return;
    }
    const sceneNo = String(scenes.length + 1);
    const res = await client.createScene(scriptId, {
      script_id: scriptId,
      scene_number: sceneNo,
      slug_line: `SCENE ${sceneNo}`,
      status: "draft",
    });
    if (!res.success) setError(res.message || "创建场景失败");
    await loadStructure();
  };

  const addBeat = async (scene: SceneNode) => {
    if (!canEdit) return;
    const order = scene.beats.length + 1;
    await client.createSceneBeat(scene.id, {
      scene_id: scene.id,
      order_index: order,
      beat_summary: `节拍 ${order}`,
    });
    await loadStructure();
  };

  const addShot = async (scene: SceneNode) => {
    if (!canEdit) return;
    await client.createSceneShot(scene.id, {
      scene_id: scene.id,
      shot_number: String(scene.shots.length + 1),
      scene_beat_id: scene.beats[0]?.id,
      shot_type: "WS",
    });
    await loadStructure();
  };

  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="结构化场景 / 镜头"
        subtitle="同步 scenes / beats / shots"
        action={
          <div className="flex gap-2">
            {!canEdit ? (
              <span className="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-[11px] text-gray-500">
                只读 · 需管理员权限
              </span>
            ) : null}
            <button
              type="button"
              onClick={() => void loadStructure()}
              disabled={loading}
              className={operatorButtonClass("secondary")}
            >
              刷新
            </button>
            {canEdit ? (
              <button
                type="button"
                onClick={() => void addScene()}
                disabled={loading}
                className={operatorButtonClass("primary")}
              >
                新增场景
              </button>
            ) : null}
          </div>
        }
      />
      <div className="space-y-3 p-4">
        {error ? <OperatorState title={error} tone="red" /> : null}
        {loading ? <OperatorState title="加载结构中..." /> : null}
        {!loading && scenes.length === 0 ? <OperatorState title="暂无结构化场景。" /> : null}
        {scenes.map((scene) => (
          <div key={scene.id} className="rounded-md border border-gray-200 bg-gray-50 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-medium text-gray-950">
                  场景 {scene.scene_number} · {scene.slug_line || "未命名"}
                </div>
                <div className="mt-1 text-xs text-gray-500">
                  {scene.location || "未设地点"} · {scene.time_of_day || "未设时间"}
                </div>
              </div>
              {canEdit ? (
                <div className="flex gap-2">
                  <button type="button" onClick={() => void addBeat(scene)} className={operatorButtonClass("secondary")}>
                    + 节拍
                  </button>
                  <button type="button" onClick={() => void addShot(scene)} className={operatorButtonClass("secondary")}>
                    + 镜头
                  </button>
                </div>
              ) : null}
            </div>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              <NodeList title={`节拍 (${scene.beats.length})`} items={scene.beats.map((beat) => `#${beat.order_index} ${beat.beat_summary || ""}`)} />
              <NodeList title={`镜头 (${scene.shots.length})`} items={scene.shots.map((shot) => `${shot.shot_number} ${shot.shot_type || ""}`)} />
            </div>
          </div>
        ))}
      </div>
    </OperatorPanel>
  );
}

function NodeList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md border border-gray-200 bg-white p-2">
      <div className="mb-2 text-xs font-medium text-gray-600">{title}</div>
      <div className="space-y-1">
        {items.length ? (
          items.map((item, index) => (
            <div key={index} className="rounded border border-gray-100 bg-gray-50 px-2 py-1 text-xs text-gray-700">
              {item || "-"}
            </div>
          ))
        ) : (
          <div className="text-xs text-gray-400">暂无数据</div>
        )}
      </div>
    </div>
  );
}
