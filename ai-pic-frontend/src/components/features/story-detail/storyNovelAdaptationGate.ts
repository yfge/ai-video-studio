import type { StoryNovelRevision } from "@/utils/api/types";

type FrozenAdaptationPlan = NonNullable<
  StoryNovelRevision["adaptation_plan"]
> & {
  novel_revision_business_id?: string;
  generation_plan_version?: number;
  generation_plan_hash?: string;
  plan_hash?: string;
  chapter_sources?: Array<{
    business_id?: string;
    body_hash?: string;
    source_hash?: string;
  }>;
};

export function adaptationEvidenceReady(revision: StoryNovelRevision) {
  const plan = revision.adaptation_plan as FrozenAdaptationPlan | null;
  const generationPlan = revision.generation_plan;
  if (
    !plan?.plan_hash ||
    plan.novel_revision_business_id !== revision.business_id ||
    plan.novel_content_hash !== revision.content_hash ||
    plan.generation_plan_version !== generationPlan?.version ||
    plan.generation_plan_hash !== generationPlan?.plan_hash
  ) {
    return false;
  }
  const sources = new Map(
    (plan.chapter_sources || []).map((source) => [source.business_id, source]),
  );
  const covered = new Set(
    plan.episodes.flatMap((episode) => episode.source_chapter_business_ids),
  );
  return (
    sources.size === revision.chapters.length &&
    revision.chapters.every((chapter) => {
      const source = sources.get(chapter.business_id);
      return (
        source?.body_hash === chapter.content_hash &&
        Boolean(source?.source_hash) &&
        covered.has(chapter.business_id)
      );
    })
  );
}

export function adaptationGateMessage(revision: StoryNovelRevision) {
  if (revision.lifecycle_status !== "approved") {
    return "小说修订版尚未审批，改编计划与剧集入口均锁定。";
  }
  if (
    ["approved", "applied"].includes(revision.adaptation_plan_status) &&
    !adaptationEvidenceReady(revision)
  ) {
    return "改编计划缺少当前小说、生成计划或章节 hash 证据；重新生成并审批有效 canonical 修订版前不能创建剧集。";
  }
  switch (revision.adaptation_plan_status) {
    case "draft":
      return "改编计划待审批，剧集入口锁定。";
    case "stale":
      return "小说或章节 hash 已变化，改编计划已过期；重新生成并审批前不能创建剧集。";
    case "approved":
      return "小说与改编计划均已审批，可以按冻结的章节来源创建剧集。";
    case "applied":
      return "剧集已按审批计划创建；后续剧本继续以剧集为源。";
    default:
      return "小说已审批；改编计划尚未生成，剧集入口锁定。";
  }
}
