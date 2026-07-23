"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { narrativeMemoryAPI, storyAPI } from "@/utils/api/endpoints";
import type {
  CharacterMemory,
  MemorySummary,
  NarrativeAnchor,
  NarrativeEvent,
  Story,
} from "@/utils/api/types";

export type MemoryWorkspaceTab = "events" | "memories" | "growth" | "review";
export type MemoryWorkspaceItem = NarrativeEvent | CharacterMemory;

export function useStoryMemoryWorkspace(storyId: string) {
  const [story, setStory] = useState<Story | null>(null);
  const [summary, setSummary] = useState<MemorySummary | null>(null);
  const [events, setEvents] = useState<NarrativeEvent[]>([]);
  const [memories, setMemories] = useState<CharacterMemory[]>([]);
  const [anchors, setAnchors] = useState<NarrativeAnchor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [taskMessage, setTaskMessage] = useState("");
  const [tab, setTab] = useState<MemoryWorkspaceTab>("events");
  const [characterId, setCharacterId] = useState("");
  const [status, setStatus] = useState("");
  const [eventType, setEventType] = useState("");
  const [disclosure, setDisclosure] = useState("");
  const [selectedId, setSelectedId] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [storyResponse, summaryResponse, eventResponse, anchorResponse] =
        await Promise.all([
          storyAPI.getStory(storyId),
          narrativeMemoryAPI.getSummary(storyId),
          narrativeMemoryAPI.getEvents(storyId),
          narrativeMemoryAPI.getAnchors(storyId),
        ]);
      if (!storyResponse.success || !storyResponse.data) {
        throw new Error(storyResponse.error || "故事不存在或无权访问");
      }
      const nextStory = storyResponse.data;
      setStory(nextStory);
      setSummary(summaryResponse.data || null);
      setEvents(eventResponse.data || []);
      setAnchors(anchorResponse.data || []);
      const characters =
        nextStory.story_characters || nextStory.characters || [];
      const memoryResponses = await Promise.all(
        characters.map((item) =>
          narrativeMemoryAPI.getCharacterMemories(storyId, item.business_id),
        ),
      );
      setMemories(memoryResponses.flatMap((item) => item.data || []));
      if (characters[0]) {
        setCharacterId((current) => current || characters[0].business_id);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setLoading(false);
    }
  }, [storyId]);

  useEffect(() => {
    void load();
  }, [load]);

  const filteredEvents = useMemo(
    () =>
      events.filter(
        (item) =>
          (!status || item.status === status) &&
          (!eventType || item.event_type === eventType) &&
          (!disclosure || item.audience_disclosure === disclosure) &&
          (!characterId ||
            item.participant_character_ids.includes(characterId)),
      ),
    [characterId, disclosure, eventType, events, status],
  );
  const filteredMemories = useMemo(
    () =>
      memories.filter(
        (item) =>
          (!status || item.status === status) &&
          (!characterId || item.character_business_id === characterId),
      ),
    [characterId, memories, status],
  );
  const reviewItems = useMemo(
    () =>
      [...events, ...memories].filter((item) =>
        ["candidate", "stale"].includes(item.status),
      ),
    [events, memories],
  );
  const selected = useMemo(
    () =>
      [...events, ...memories].find(
        (item) => item.business_id === selectedId,
      ) || null,
    [events, memories, selectedId],
  );

  const review = async (
    item: MemoryWorkspaceItem,
    action: "approve" | "reject",
  ) => {
    const response = await narrativeMemoryAPI.reviewCandidate(
      storyId,
      item.business_id,
      action,
      item.version,
    );
    if (!response.success)
      throw new Error(response.error || "审核失败或内容已变化");
    await load();
  };

  const save = async (item: MemoryWorkspaceItem, text: string) => {
    const isEvent = "event_type" in item;
    const response = await narrativeMemoryAPI.updateCandidate(
      storyId,
      item.business_id,
      {
        expected_version: item.version,
        [isEvent ? "summary" : "content"]: text,
      },
    );
    if (!response.success)
      throw new Error(response.error || "保存失败或内容已变化");
    await load();
  };

  const extract = async (source: "story_seed" | "canonical_novel") => {
    const response = await narrativeMemoryAPI.extractCandidates(
      storyId,
      source,
    );
    if (!response.success || !response.data) {
      throw new Error(response.error || "提取任务创建失败");
    }
    setTaskMessage(
      `提取任务 #${response.data.task_id} 已提交；正文内容保持不变。`,
    );
  };

  const split = async (item: MemoryWorkspaceItem, contents: string[]) => {
    const response = await narrativeMemoryAPI.splitCandidate(
      storyId,
      item.business_id,
      item.version,
      contents,
    );
    if (!response.success)
      throw new Error(response.error || "拆分失败或候选已变化");
    setSelectedId("");
    await load();
  };

  const merge = async (
    item: MemoryWorkspaceItem,
    targetBusinessId: string,
    mergedContent?: string,
  ) => {
    const target = [...events, ...memories].find(
      (candidate) => candidate.business_id === targetBusinessId,
    );
    if (!target) throw new Error("未找到要合并的候选 business ID");
    const response = await narrativeMemoryAPI.mergeCandidates(
      storyId,
      [item, target],
      mergedContent,
    );
    if (!response.success)
      throw new Error(response.error || "合并失败或候选已变化");
    setSelectedId("");
    await load();
  };

  const promote = async (
    item: MemoryWorkspaceItem,
    candidateContent: string,
  ) => {
    if ("event_type" in item)
      throw new Error("客观事件不能直接提升为角色公共记忆");
    const response = await narrativeMemoryAPI.createPromotion(
      item,
      candidateContent,
    );
    if (!response.success)
      throw new Error(response.error || "公共记忆候选提交失败");
    setTaskMessage(
      "已提交角色公共记忆提升候选；必须在 Virtual IP 页面人工编辑或批准。",
    );
  };

  return {
    story,
    summary,
    events: filteredEvents,
    memories: filteredMemories,
    anchors,
    reviewItems,
    selected,
    loading,
    error,
    taskMessage,
    tab,
    setTab,
    characterId,
    setCharacterId,
    status,
    setStatus,
    eventType,
    setEventType,
    disclosure,
    setDisclosure,
    setSelectedId,
    review,
    save,
    split,
    merge,
    promote,
    extract,
    refresh: load,
  };
}
