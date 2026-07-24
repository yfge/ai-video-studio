import type {
  StorySeedStructuredChapter,
  StorySeedStructuredOutline,
  StorySeedThreadPayoff,
} from "@/utils/api/types";

const pendingChapter = (position: number): StorySeedStructuredChapter => ({
  position,
  title: `第 ${position} 章`,
  goal: "待补充情节目标",
  key_events: ["待补充关键事件"],
  character_focus: [],
  open_threads: [],
  end_state: "待补充章末状态",
});

export function renumberOutlineChapters(
  chapters: StorySeedStructuredChapter[],
) {
  return chapters.map((chapter, index) => ({
    ...chapter,
    position: index + 1,
  }));
}

export function appendOutlineChapter(chapters: StorySeedStructuredChapter[]) {
  return renumberOutlineChapters([
    ...chapters,
    pendingChapter(chapters.length + 1),
  ]);
}

export function removeOutlineChapter(
  chapters: StorySeedStructuredChapter[],
  index: number,
) {
  if (chapters.length <= 1) return chapters;
  return renumberOutlineChapters(chapters.filter((_, row) => row !== index));
}

export function moveOutlineChapter(
  chapters: StorySeedStructuredChapter[],
  from: number,
  to: number,
) {
  if (
    from === to ||
    from < 0 ||
    to < 0 ||
    from >= chapters.length ||
    to >= chapters.length
  ) {
    return chapters;
  }
  const next = [...chapters];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved);
  return renumberOutlineChapters(next);
}

export function moveOutlinePosition(
  position: number,
  from: number,
  to: number,
) {
  const source = from + 1;
  const target = to + 1;
  if (position === source) return target;
  if (from < to && position > source && position <= target) return position - 1;
  if (to < from && position >= target && position < source) return position + 1;
  return position;
}

export function replaceOutlineChapters(
  outline: StorySeedStructuredOutline,
  chapters: StorySeedStructuredChapter[],
  mapPayoff: (payoff: StorySeedThreadPayoff) => number | null = (payoff) =>
    payoff.payoff_position,
) {
  const thread_payoffs = outline.thread_payoffs.flatMap((payoff) => {
    const payoff_position = mapPayoff(payoff);
    return payoff_position ? [{ ...payoff, payoff_position }] : [];
  });
  return { ...outline, status: "draft" as const, chapters, thread_payoffs };
}

export function splitOutlineChapter(
  chapters: StorySeedStructuredChapter[],
  index: number,
) {
  const chapter = chapters[index];
  if (!chapter) return chapters;
  const splitAt = Math.ceil(chapter.key_events.length / 2);
  const firstEvents = chapter.key_events.slice(0, splitAt);
  const secondEvents = chapter.key_events.slice(splitAt);
  const halves: StorySeedStructuredChapter[] = [
    {
      ...chapter,
      title: `${chapter.title}（上）`,
      key_events: firstEvents.length ? firstEvents : ["待补充关键事件"],
      end_state: "推进到本章下半部分",
    },
    {
      ...chapter,
      title: `${chapter.title}（下）`,
      key_events: secondEvents.length ? secondEvents : ["待补充关键事件"],
      open_threads: [],
    },
  ];
  return renumberOutlineChapters([
    ...chapters.slice(0, index),
    ...halves,
    ...chapters.slice(index + 1),
  ]);
}

const unique = (items: string[]) => Array.from(new Set(items.filter(Boolean)));
const payoffEvidencePrefix = (threadId: string) =>
  `关于“${threadId}”的最终证据确认：`;

export function mergeOutlineChapterWithNext(
  chapters: StorySeedStructuredChapter[],
  index: number,
) {
  const current = chapters[index];
  const next = chapters[index + 1];
  if (!current || !next) return chapters;
  const merged: StorySeedStructuredChapter = {
    ...current,
    title: `${current.title} / ${next.title}`,
    goal: unique([current.goal, next.goal]).join("；"),
    key_events: unique([...current.key_events, ...next.key_events]),
    character_focus: unique([
      ...current.character_focus,
      ...next.character_focus,
    ]),
    open_threads: unique([...current.open_threads, ...next.open_threads]),
    end_state: next.end_state,
  };
  return renumberOutlineChapters([
    ...chapters.slice(0, index),
    merged,
    ...chapters.slice(index + 2),
  ]);
}

export function validateStructuredOutline(outline: StorySeedStructuredOutline) {
  if (!outline.chapters.length) return "结构化大纲至少需要一章";
  for (const [index, chapter] of outline.chapters.entries()) {
    if (chapter.position !== index + 1) return "章节编号必须从 1 连续排列";
    if (!chapter.title.trim()) return `第 ${index + 1} 章缺少标题`;
    if (!chapter.goal.trim()) return `第 ${index + 1} 章缺少情节目标`;
    if (!chapter.key_events.some((item) => item.trim())) {
      return `第 ${index + 1} 章至少需要一个关键事件`;
    }
    if (!chapter.end_state.trim()) return `第 ${index + 1} 章缺少章末状态`;
  }
  if (outline.thread_schedule_version !== 1) {
    if ((outline.thread_payoffs ?? []).length) {
      return "v0 大纲不得携带伏笔回收记录";
    }
    if (outline.chapters.some((chapter) => chapter.open_threads.length)) {
      return "伏笔回收合同为 v0，需重新结构化后才能确认";
    }
    return null;
  }
  return validateThreadPayoffs(outline);
}

function validateThreadPayoffs(outline: StorySeedStructuredOutline) {
  const opened = new Map<string, number>();
  for (const chapter of outline.chapters) {
    for (const threadId of chapter.open_threads) {
      if (!threadId.trim()) return `第 ${chapter.position} 章包含空伏笔 ID`;
      if (
        ["；", ";", "、", "以及"].some((marker) => threadId.includes(marker))
      ) {
        return `伏笔 ID 必须只表达一个原子问题：${threadId}`;
      }
      if (opened.has(threadId)) return `伏笔 ID 全书重复：${threadId}`;
      opened.set(threadId, chapter.position);
    }
  }
  const seen = new Set<string>();
  const counts = new Map<number, number>();
  const chapters = new Map(
    outline.chapters.map((item) => [item.position, item]),
  );
  for (const payoff of outline.thread_payoffs ?? []) {
    const opening = opened.get(payoff.thread_id);
    if (opening === undefined) return `回收表包含未知伏笔：${payoff.thread_id}`;
    if (seen.has(payoff.thread_id)) return `伏笔重复回收：${payoff.thread_id}`;
    seen.add(payoff.thread_id);
    const target = chapters.get(payoff.payoff_position);
    if (!Number.isInteger(payoff.payoff_position) || !target) {
      return `伏笔 ${payoff.thread_id} 的回收章节无效`;
    }
    if (payoff.payoff_position <= opening) {
      return `伏笔 ${payoff.thread_id} 必须在第 ${opening} 章之后回收`;
    }
    if (!target.key_events.includes(payoff.evidence_key_event)) {
      return `伏笔 ${payoff.thread_id} 的回收证据必须逐字属于第 ${target.position} 章关键事件`;
    }
    const prefix = payoffEvidencePrefix(payoff.thread_id);
    if (
      !payoff.evidence_key_event.startsWith(prefix) ||
      payoff.evidence_key_event.length <= prefix.length
    ) {
      return `伏笔 ${payoff.thread_id} 的回收事件必须使用显式问题标签并给出答案`;
    }
    const count = (counts.get(target.position) ?? 0) + 1;
    if (count > 3) return `第 ${target.position} 章最多回收 3 条伏笔`;
    counts.set(target.position, count);
  }
  const missing = [...opened.keys()].filter((threadId) => !seen.has(threadId));
  if (missing.length) return `伏笔回收合同遗漏：${missing.join("、")}`;
  return null;
}

export const outlineLines = (value: string) =>
  value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
