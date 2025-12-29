"""
Duration Orchestrator 常量配置

所有时长相关的阈值、容差、速率等配置集中管理。
"""

# =============================================================================
# 时长容差配置
# =============================================================================

# 场景级时长容差 (±15%)
DURATION_TOLERANCE_SCENE_LOW = 0.85
DURATION_TOLERANCE_SCENE_HIGH = 1.15
DURATION_TOLERANCE_SCENE = (DURATION_TOLERANCE_SCENE_LOW, DURATION_TOLERANCE_SCENE_HIGH)

# 剧集级时长容差 (±10%)
DURATION_TOLERANCE_EPISODE_LOW = 0.90
DURATION_TOLERANCE_EPISODE_HIGH = 1.10
DURATION_TOLERANCE_EPISODE = (DURATION_TOLERANCE_EPISODE_LOW, DURATION_TOLERANCE_EPISODE_HIGH)

# TTS 估算容差 (使用实际时长时 ±20%，估算时长时 ±40%)
TTS_TOLERANCE_ACTUAL = (0.80, 1.20)
TTS_TOLERANCE_ESTIMATED = (0.60, 1.40)

# =============================================================================
# 重试配置
# =============================================================================

# 单场景最大重试次数
MAX_RETRY_ATTEMPTS = 3

# TTS 采样估算时的样本数量
TTS_SAMPLE_COUNT = 3

# 对白数量阈值：低于此值时全量 TTS，否则采样
TTS_FULL_GENERATION_THRESHOLD = 5

# =============================================================================
# 语速与字数配置
# =============================================================================

# 中文 TTS 语速 (字/秒)
#
# 重要：这里的“字”按代码实现约定等同于 `len(text)` 的字符数（中文为主）。
# 早期采用 2.25 字/秒（135 字/分钟）会显著高估对白时长，导致：
# - 生成阶段对白字数偏少
# - 后续对白音频/时间轴出现明显“音频过短、间隙过大”的漂移
#
# 实测校准：基于 MySQL `scene_beats` 中 `beat_type='dialogue'` 的统计，
# 平均语速约 4.7 字/秒（≈282 字/分钟）。
WORDS_PER_SECOND_SLOW = 3.8
WORDS_PER_SECOND_NORMAL = 4.7
WORDS_PER_SECOND_FAST = 5.6
WORDS_PER_SECOND = WORDS_PER_SECOND_NORMAL  # 默认使用正常语速（与线上数据校准）

# 每字平均 TTS 时长 (毫秒)
MS_PER_CHAR_DEFAULT = 150

# 每句对白平均字数
WORDS_PER_DIALOGUE = 25

# =============================================================================
# 预算分配配置
# =============================================================================

# 预留 buffer 比例 (用于场景间过渡、空镜头、动作等非对白时间)
# 0.05 = 5% - 太少，实际短剧中非对白时间约占 15-25%
# 0.15 = 15% - 平衡：给转场、BGM 留空间，但保证足够对白
# 0.30 = 30% - 太多，导致对白不足
BUFFER_RATIO = 0.15

# 对白密度因子 (用于计算目标字数)
# 即使是对白场景，也不是 100% 都在说话，需要考虑：
# - 停顿、语气词、情绪表达
# - 角色反应时间
# - 环境音/BGM 段落
# 0.90 = 90% 的时间用于对白朗读（短剧节奏快，对白密集）
DIALOGUE_DENSITY_FACTOR = 0.90

# 默认场景时长 (秒)，当场景无 estimated_duration_seconds 时使用
DEFAULT_SCENE_DURATION_SECONDS = 30

# 最小场景时长 (秒)
MIN_SCENE_DURATION_SECONDS = 10

# 最大场景时长 (秒)
MAX_SCENE_DURATION_SECONDS = 120

# =============================================================================
# 调整建议配置
# =============================================================================

# 调整建议中每句对白的平均字数
ADJUSTMENT_WORDS_PER_DIALOGUE = 20

# 时长不足时的最小增加字数
MIN_WORD_ADJUSTMENT = 20

# 时长过长时的最小删减字数
MIN_WORD_REDUCTION = 20
