"use client";

import { useEffect, useMemo, useState } from "react";
import { listNovelLengthProfiles } from "@/utils/api/endpoints";
import type {
  NovelChapterLengthOverrides,
  NovelLengthProfile,
  NovelLengthRange,
  Story,
  StoryNovelCreateRevisionPayload,
  StoryNovelRevision,
  StoryNovelUpdateLengthSpecPayload,
} from "@/utils/api/types";
import {
  DEFAULT_CUSTOM_LENGTH,
  plannedLengthTotals,
  validateLengthOverrides,
  validateLengthRange,
} from "./storyNovelLengthPlan";

export interface StoryNovelLengthPanelProps {
  story: Story;
  revision: StoryNovelRevision | null;
  locked: boolean;
  busy: boolean;
  onCreate: (payload: StoryNovelCreateRevisionPayload) => Promise<boolean>;
  onUpdate: (
    revisionId: string,
    payload: StoryNovelUpdateLengthSpecPayload,
  ) => Promise<boolean>;
}

function useNovelLengthProfiles() {
  const [profiles, setProfiles] = useState<NovelLengthProfile[]>([]);
  const [profileError, setProfileError] = useState("");
  useEffect(() => {
    let mounted = true;
    void listNovelLengthProfiles().then((response) => {
      if (!mounted) return;
      if (!response.success || !response.data) {
        setProfileError(response.error || "加载长度规格失败");
        return;
      }
      setProfiles(response.data.items);
    });
    return () => {
      mounted = false;
    };
  }, []);
  return { profiles, profileError };
}

function useNovelLengthSelection(
  story: Story,
  revision: StoryNovelRevision | null,
  profiles: NovelLengthProfile[],
) {
  const [profileId, setProfileId] = useState("");
  const [custom, setCustom] = useState(DEFAULT_CUSTOM_LENGTH);
  const [overrides, setOverrides] = useState<NovelChapterLengthOverrides>({});
  const [planningModel, setPlanningModel] = useState("");
  const [proseModel, setProseModel] = useState("");
  const [auditModel, setAuditModel] = useState("");
  const policyPlanningModel =
    revision?.generation_plan?.model_policy?.planning_model || "";
  const policyProseModel =
    revision?.generation_plan?.model_policy?.prose_model || "";
  const policyAuditModel =
    revision?.generation_plan?.model_policy?.audit_model || "";
  const seedPlanningModel =
    story.story_seed?.schema === "story_seed_v2"
      ? story.story_seed.structured_outline.planning_model || ""
      : "";
  useEffect(() => {
    setProfileId((value) => value || profiles[0]?.profile_id || "");
  }, [profiles]);
  useEffect(() => {
    setPlanningModel(policyPlanningModel || seedPlanningModel);
    setProseModel(policyProseModel || revision?.model || "");
    setAuditModel(policyAuditModel);
  }, [
    policyAuditModel,
    policyPlanningModel,
    policyProseModel,
    revision?.business_id,
    revision?.model,
    seedPlanningModel,
  ]);
  useEffect(() => {
    const profile = revision?.generation_plan?.length_profile;
    if (!profile) return;
    setProfileId(profile.profile_id);
    setCustom({
      min_chars: profile.default_min_chars,
      target_chars: profile.default_target_chars,
      max_chars: profile.default_max_chars,
    });
    setOverrides(revision?.generation_plan?.chapter_length_overrides || {});
  }, [
    revision?.business_id,
    revision?.generation_plan?.chapter_length_overrides,
    revision?.generation_plan?.length_profile,
  ]);
  return {
    profileId,
    setProfileId,
    custom,
    setCustom,
    overrides,
    setOverrides,
    planningModel,
    setPlanningModel,
    proseModel,
    setProseModel,
    auditModel,
    setAuditModel,
  };
}

export function useStoryNovelLengthPanelState(
  story: Story,
  revision: StoryNovelRevision | null,
) {
  const { profiles, profileError } = useNovelLengthProfiles();
  const selection = useNovelLengthSelection(story, revision, profiles);
  const chapters = useMemo(
    () =>
      story.story_seed?.schema === "story_seed_v2"
        ? story.story_seed.structured_outline.chapters
        : [],
    [story.story_seed],
  );
  const selected = profiles.find(
    ({ profile_id }) => profile_id === selection.profileId,
  );
  const defaults: NovelLengthRange =
    selection.profileId === "custom"
      ? selection.custom
      : selected || DEFAULT_CUSTOM_LENGTH;
  const totals = useMemo(
    () =>
      plannedLengthTotals(
        chapters.map(({ position }) => position),
        defaults,
        selection.overrides,
      ),
    [chapters, defaults, selection.overrides],
  );
  const validation =
    (!selection.profileId && "请选择长度规格") ||
    (!chapters.length && "冻结的结构化大纲至少需要一章") ||
    validateLengthRange(defaults) ||
    validateLengthOverrides(selection.overrides);
  return {
    ...selection,
    profiles,
    profileError,
    chapters,
    defaults,
    totals,
    validation,
  };
}
