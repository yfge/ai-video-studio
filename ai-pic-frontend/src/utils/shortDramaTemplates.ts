export type ShortDramaStoryTemplate = {
  id: string;
  label: string;
  description: string;
  defaults: {
    genre?: string;
    market_region?: string;
    micro_genre?: string;
    pacing_template?: string;
    theme?: string;
    target_audience?: string;
    duration_minutes?: number;
    setting_time?: string;
    setting_location?: string;
    world_building?: string;
    additional_requirements?: string;
  };
};

export const SHORT_DRAMA_STORY_TEMPLATES: ShortDramaStoryTemplate[] = [
  {
    id: "engagement-betrayal-revenge",
    label: "订婚宴背叛·复仇反击",
    description:
      "开场社死背叛 -> 中段证据翻盘 -> 结尾更大阴谋卡点；适合职场/豪门复仇线。",
    defaults: {
      genre: "drama",
      market_region: "SEA",
      micro_genre: "豪门家族斗争 / 职场复仇",
      pacing_template: "twist-heavy",
      theme: "背叛与复仇、身份反转、正义反击",
      target_audience: "女性向/爽剧受众",
      duration_minutes: 30,
      setting_time: "现代",
      setting_location: "一线城市/国际化都市",
      world_building:
        "豪门与职场权力交织：订婚宴、公司项目、资本暗流；证据链与身份线贯穿。",
      additional_requirements:
        "硬性：每集必须有1个可拍爽点（打脸/反击/揭露/惩罚/逆转/救援/告白）+ 结尾卡点升级；每集3-6场景，优先复用主要地点；对白短促高信息密度，避免空话套话。",
    },
  },
];

export type ShortDramaScriptTemplate = {
  id: string;
  label: string;
  description: string;
  defaults: {
    dialogue_style?: string;
    scene_detail_level?: string;
    additional_requirements?: string;
  };
};

export const SHORT_DRAMA_SCRIPT_TEMPLATES: ShortDramaScriptTemplate[] = [
  {
    id: "hit-structure",
    label: "爆款结构（HOOK→升级→PAYOFF→CLIFFHANGER）",
    description:
      "强制开场钩子、爽点落点与结尾卡点，并要求 scenes.notes 标注 HOOK/PAYOFF/CLIFFHANGER。",
    defaults: {
      dialogue_style: "natural",
      scene_detail_level: "medium",
      additional_requirements:
        "请按短剧爆款结构输出：开场10秒必须爆点（HOOK），中段快速升级，末段必须出现1个明确可拍的爽点事件（PAYOFF），最后一个场景必须留下更大悬念/危机升级（CLIFFHANGER）。在 scenes[].notes 明确标注 HOOK/PAYOFF/CLIFFHANGER。对白必须短、信息密度高、带动作与情绪，不要空话套话，不要用“……”省略台词。",
    },
  },
];

