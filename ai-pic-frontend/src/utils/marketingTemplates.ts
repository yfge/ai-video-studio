export type HookBeat = {
  beat_type?: string;
  description: string;
  timing?: string;
  intensity?: string;
};

export type HookPlan = {
  opening_hook?: string;
  escalation_plan?: string;
  payoff_plan?: string;
  key_reversals?: HookBeat[];
};

export type AdSnippet = {
  duration_seconds?: number;
  hook: string;
  visual_summary?: string;
  call_to_action?: string;
};

export type PacingTemplate = {
  id: string;
  label: string;
  description: string;
  hookPlan: HookPlan;
  twistDensity?: string;
  cliffhangerPlan?: string[];
  adSnippets?: AdSnippet[];
};

export const MARKET_REGIONS = [
  { value: "NA", label: "北美", description: "复仇流、狼人、黑帮皮肤更顺畅" },
  { value: "LATAM", label: "拉美", description: "家族纠葛、情感拉扯接受度高" },
  {
    value: "SEA",
    label: "东南亚",
    description: "霸总/契约婚姻、校园情感表现稳定",
  },
  { value: "MENA", label: "中东", description: "家族权力、财产继承线更稳妥" },
  { value: "KRJP", label: "日韩", description: "偶像、校园、职场情感更易转化" },
  { value: "GLOBAL", label: "全球", description: "保守模板，便于跨区复用" },
];

export const MICRO_GENRES = [
  { value: "mafia-revenge", label: "黑帮复仇" },
  { value: "werewolf-mate", label: "狼人/命定伴侣" },
  { value: "billionaire-identity", label: "霸总/隐藏身份" },
  { value: "secret-baby", label: "秘密孩子/继承人" },
  { value: "contract-marriage", label: "契约婚姻" },
  { value: "campus-revenge", label: "校园逆袭" },
  { value: "idol-scandal", label: "偶像丑闻恋爱" },
  { value: "family-intrigue", label: "豪门家族斗争" },
];

export const PACING_TEMPLATES: PacingTemplate[] = [
  {
    id: "fast-hook",
    label: "快钩子冲刺",
    description:
      "开场5秒爆点 + 30秒内完成第一次反转，结尾以明确悬念锁住下一集。",
    hookPlan: {
      opening_hook: "用一条台词/动作在5秒内引爆冲突。",
      escalation_plan: "20-40秒快速拉高羞辱/背叛情绪。",
      payoff_plan: "结尾2-3秒给出关键反击或身份反转。",
      key_reversals: [
        {
          beat_type: "reversal",
          description: "身份/立场反转，推动复仇节奏",
          timing: "中段",
          intensity: "high",
        },
      ],
    },
    twistDensity: "1-2/集",
    cliffhangerPlan: ["结尾3秒揭示关键身份或威胁"],
    adSnippets: [
      {
        duration_seconds: 15,
        hook: "开场被羞辱 -> 霸气反击",
        visual_summary: "近景表情+反手打脸镜头",
        call_to_action: "想看她怎么翻盘？继续追剧",
      },
      {
        duration_seconds: 30,
        hook: "身份反转 + 冲突升级",
        visual_summary: "权力登场+对手崩溃",
        call_to_action: "下一集揭晓真相",
      },
    ],
  },
  {
    id: "twist-heavy",
    label: "高密度反转",
    description: "每集至少2个反转，情绪高频起伏，用反应镜头加速爽点释放。",
    hookPlan: {
      opening_hook: "开场直接给出冲突结果或爆点画面。",
      escalation_plan: "每20秒插入反转/误会/揭穿。",
      payoff_plan: "尾声用二次反转制造错愕感。",
      key_reversals: [
        {
          beat_type: "hook",
          description: "开场先给出不可逆的冲突结果",
          timing: "开场",
          intensity: "high",
        },
        {
          beat_type: "reversal",
          description: "中段双重反转",
          timing: "中段",
          intensity: "high",
        },
      ],
    },
    twistDensity: "2+/集",
    cliffhangerPlan: ["用未揭开的秘密作为下一集引子"],
    adSnippets: [
      {
        duration_seconds: 15,
        hook: "连续反转制造错愕",
        visual_summary: "切换表情+迅速切镜",
        call_to_action: "别眨眼，反转还没完",
      },
      {
        duration_seconds: 60,
        hook: "多段反转串联",
        visual_summary: "多场景快速剪辑",
        call_to_action: "立即解锁后续剧情",
      },
    ],
  },
  {
    id: "slow-burn",
    label: "情绪递进",
    description: "前期埋伏笔，情绪积压到60-80秒集中释放，适合感情线推进。",
    hookPlan: {
      opening_hook: "开场点出关键关系与禁忌。",
      escalation_plan: "逐步加深误会与情绪压力。",
      payoff_plan: "末尾给出情绪释放或关键决断。",
      key_reversals: [
        {
          beat_type: "payoff",
          description: "情绪释放/告白",
          timing: "结尾",
          intensity: "medium",
        },
      ],
    },
    twistDensity: "1/集",
    cliffhangerPlan: ["以情感选择作为吊点"],
    adSnippets: [
      {
        duration_seconds: 30,
        hook: "情绪压抑 -> 终于爆发",
        visual_summary: "对视、转身、泪点",
        call_to_action: "结局马上揭晓",
      },
    ],
  },
];
