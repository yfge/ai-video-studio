"use client";

import { OperatorPanel, OperatorSectionHeader } from "@/components/shared";
import { StoryNovelLengthPanelBody } from "./StoryNovelLengthPanelBody";
import {
  useStoryNovelLengthPanelState,
  type StoryNovelLengthPanelProps,
} from "./useStoryNovelLengthPanelState";

export function StoryNovelLengthPanel(props: StoryNovelLengthPanelProps) {
  const state = useStoryNovelLengthPanelState(props.story, props.revision);
  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="2. 平台长度规格"
        subtitle="规格属于当前小说版本；预计总量由冻结章节计划实时汇总"
      />
      <StoryNovelLengthPanelBody
        state={state}
        locked={props.locked}
        busy={props.busy}
        revision={props.revision}
        onCreate={props.onCreate}
        onUpdate={props.onUpdate}
      />
    </OperatorPanel>
  );
}
