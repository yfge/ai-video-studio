import type { Story } from "../src/utils/api/types";

function profileResponse() {
  return new Response(
    JSON.stringify({
      success: true,
      data: {
        items: [
          {
            profile_id: "commercial_serial",
            name: "商业网文短章",
            min_chars: 2000,
            target_chars: 2500,
            max_chars: 3000,
          },
          {
            profile_id: "standard_serial",
            name: "标准连载",
            min_chars: 3000,
            target_chars: 4000,
            max_chars: 5000,
          },
          {
            profile_id: "short_serial",
            name: "短章连载",
            min_chars: 1500,
            target_chars: 2200,
            max_chars: 3000,
          },
        ],
      },
    }),
    { headers: { "content-type": "application/json" } },
  );
}

export function frontendResponse(input: string | URL | Request) {
  return String(input).includes("/ai/models/available")
    ? new Response(
        JSON.stringify({
          success: true,
          data: {
            models: [
              {
                model_id: "codex:gpt-5.6",
                id: "gpt-5.6",
                name: "GPT-5.6",
                provider: "codex",
                type: "text_generation",
                capabilities: ["text_generation"],
              },
            ],
          },
        }),
        { headers: { "content-type": "application/json" } },
      )
    : profileResponse();
}

export const story = {
  id: 1,
  business_id: "story-business-id",
  story_seed_status: "confirmed",
  story_seed: {
    schema: "story_seed_v2",
    structured_outline: {
      status: "confirmed",
      version: 7,
      planning_model: "codex:gpt-5.6",
      thread_schedule_version: 1,
      thread_payoffs: [],
      chapters: [
        {
          position: 1,
          title: "第一章",
          goal: "发现线索",
          key_events: ["发现红尘"],
          character_focus: ["褚蓝"],
          open_threads: [],
          end_state: "保存样本",
        },
        {
          position: 2,
          title: "第二章",
          goal: "追查来源",
          key_events: ["检查暗渠"],
          character_focus: ["褚蓝"],
          open_threads: [],
          end_state: "锁定入口",
        },
      ],
    },
  },
} as unknown as Story;
