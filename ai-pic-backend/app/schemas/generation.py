from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.schemas.script_scoring import ScriptScoreDimensions as ScriptScoreDimensions
from app.schemas.script_scoring import ScriptScoreResult as ScriptScoreResult
from app.schemas.script_scoring import TrafficSheet as TrafficSheet
from app.schemas.script_scoring import TrafficSheetAsset as TrafficSheetAsset
from pydantic import BaseModel, Field


class CharacterInfo(BaseModel):
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述或定位")
    role: Optional[str] = Field(None, description="角色类型/职责")


class PlotStructure(BaseModel):
    act1: Optional[str] = None
    act2: Optional[str] = None
    act3: Optional[str] = None


class HookBeat(BaseModel):
    beat_type: Optional[str] = Field(
        None, description="钩子类型：hook/reversal/payoff 等"
    )
    description: str = Field(..., description="钩子/反转描述")
    timing: Optional[str] = Field(None, description="出现时机：开场/中段/结尾等")
    intensity: Optional[str] = Field(None, description="强度：low/medium/high")


class HookPlan(BaseModel):
    opening_hook: Optional[str] = Field(None, description="开场钩子设计")
    escalation_plan: Optional[str] = Field(None, description="情绪积压/升级节奏")
    payoff_plan: Optional[str] = Field(None, description="释放/回收节点规划")
    key_reversals: Optional[List[HookBeat]] = Field(None, description="关键反转列表")


class AdSnippet(BaseModel):
    duration_seconds: Optional[int] = Field(None, description="素材时长（秒）")
    hook: str = Field(..., description="素材核心钩子")
    visual_summary: Optional[str] = Field(None, description="素材画面摘要")
    call_to_action: Optional[str] = Field(None, description="引导文案/CTA")


class StoryOutlineModel(BaseModel):
    premise: str = Field(..., description="故事前提/核心概念")
    synopsis: str = Field(..., description="详细故事概要")
    main_conflict: Optional[str] = Field(None, description="主要冲突")
    resolution: Optional[str] = Field(None, description="解决方案/结局")
    character_relationships: Optional[Dict[str, Any]] = Field(
        None, description="角色关系网"
    )
    main_characters: Optional[List[CharacterInfo]] = Field(None, description="主要角色")
    plot_structure: Optional[PlotStructure] = Field(None, description="三幕式结构")
    core_values: Optional[str] = Field(None, description="核心价值")
    visual_style: Optional[str] = Field(None, description="视觉风格建议")
    selling_points: Optional[List[str]] = Field(None, description="营销卖点")
    market_region: Optional[str] = Field(None, description="目标市场/地区")
    micro_genre: Optional[str] = Field(None, description="微类型/细分题材")
    hook_plan: Optional[HookPlan] = Field(None, description="爽点/钩子节奏规划")
    twist_density: Optional[str] = Field(None, description="反转密度目标")
    cliffhanger_plan: Optional[List[str]] = Field(None, description="悬念/卡点规划")
    ad_snippets: Optional[List[AdSnippet]] = Field(None, description="投流素材建议")
    structured_story_contract: Optional[Dict[str, Any]] = Field(
        None, description="生产级短剧故事合同（仅 production 生成要求）"
    )


class SceneItem(BaseModel):
    scene_number: Optional[int] = None
    location: Optional[str] = None
    time: Optional[str] = None
    description: Optional[str] = None
    characters: Optional[List[str]] = None
    props: Optional[List[str]] = None
    notes: Optional[str] = None


class DialogueItem(BaseModel):
    scene_number: Optional[int] = None
    character: Optional[str] = None
    content: str
    emotion: Optional[str] = None
    action: Optional[str] = None
    notes: Optional[str] = None


class StageDirectionItem(BaseModel):
    scene_number: Optional[int] = None
    timing: Optional[str] = None
    content: str
    type: Optional[str] = None


class ScriptMetadata(BaseModel):
    total_scenes: Optional[int] = None
    total_dialogues: Optional[int] = None
    estimated_duration: Optional[str] = None
    shooting_locations: Optional[List[str]] = None
    main_characters: Optional[List[str]] = None
    special_effects: Optional[List[str]] = None
    market_region: Optional[str] = Field(None, description="目标市场/地区")
    micro_genre: Optional[str] = Field(None, description="微类型/细分题材")
    hook_plan: Optional[HookPlan] = Field(None, description="爽点/钩子节奏规划")
    twist_density: Optional[str] = Field(None, description="反转密度目标")
    cliffhanger_plan: Optional[List[str]] = Field(None, description="悬念/卡点规划")
    ad_snippets: Optional[List[AdSnippet]] = Field(None, description="投流素材建议")


class ScriptModel(BaseModel):
    content: str
    scenes: Optional[List[SceneItem]] = None
    dialogues: Optional[List[DialogueItem]] = None
    stage_directions: Optional[List[StageDirectionItem]] = None
    metadata: Optional[ScriptMetadata] = None


class StoryboardFrame(BaseModel):
    # Accept any string id; default to a UUID string when absent.
    frame_id: str = Field(
        default_factory=lambda: str(uuid4()), description="分镜帧唯一标识（字符串）"
    )
    frame_number: Optional[int] = None
    scene_number: Optional[int] = None
    scene_index: Optional[int] = Field(
        None, description="在剧本场景列表中的索引（从1开始）"
    )
    shot_type: Optional[str] = Field(None, description="景别：远景/中景/近景/特写 等")
    camera_movement: Optional[str] = Field(
        None, description="运镜：推/拉/摇/移/跟/变焦 等"
    )
    composition: Optional[str] = Field(None, description="构图：三分法/对称/前后景 等")
    description: str = Field(..., description="画面描述与动作")
    duration_seconds: Optional[float] = Field(None, description="建议时长（秒）")
    start_ms: Optional[int] = Field(None, description="时间轴起点（毫秒）")
    end_ms: Optional[int] = Field(None, description="时间轴终点（毫秒）")
    ai_prompt: Optional[str] = Field(None, description="用于生成图像/视频的提示词")
    hook_tag: Optional[str] = Field(None, description="对应爽点/钩子标签（可选）")
    ad_snippet: Optional[AdSnippet] = Field(None, description="关联投流素材（可选）")
    reference_images: Optional[List[str]] = Field(None, description="参考图 URL 列表")
    image_url: Optional[str] = Field(
        None, description="生成的分镜图像URL（生成后回填）"
    )
    start_image_url: Optional[str] = Field(
        None, description="分镜首帧关键帧URL（生成后回填）"
    )
    start_image_urls: Optional[List[str]] = Field(
        None, description="分镜首帧关键帧URL列表（生成后回填）"
    )
    end_image_url: Optional[str] = Field(
        None, description="分镜尾帧关键帧URL（生成后回填）"
    )
    end_image_urls: Optional[List[str]] = Field(
        None, description="分镜尾帧关键帧URL列表（生成后回填）"
    )
    start_keyframe_prompt: Optional[str] = Field(
        None, description="分镜首帧关键帧提示词（生成时填充）"
    )
    end_keyframe_prompt: Optional[str] = Field(
        None, description="分镜尾帧关键帧提示词（生成时填充）"
    )
    video_url: Optional[str] = Field(None, description="生成的视频URL（生成后回填）")
    video_url_original: Optional[str] = Field(
        None, description="生成视频的原始URL（未上传OSS时的路径）"
    )
    video_urls: Optional[List[str]] = Field(
        None, description="生成的视频URL列表（回填历史记录，去重）"
    )
    video_thumbnail_url: Optional[str] = Field(
        None, description="视频封面/缩略图URL（生成后回填）"
    )
    video_thumbnail_url_original: Optional[str] = Field(
        None, description="视频封面原始URL（未上传OSS时的路径）"
    )
    video_thumbnail_urls: Optional[List[str]] = Field(
        None, description="视频封面/缩略图URL列表（回填历史记录，去重）"
    )
    video_last_frame_url: Optional[str] = Field(
        None, description="视频尾帧URL（return_last_frame=true 时回填）"
    )
    video_last_frame_url_original: Optional[str] = Field(
        None, description="视频尾帧原始URL（未上传OSS时的路径）"
    )
    video_last_frame_urls: Optional[List[str]] = Field(
        None, description="视频尾帧URL列表（回填历史记录，去重）"
    )
    video_generation: Optional[Dict[str, Any]] = Field(
        None, description="视频生成元数据（模型/参数/锚点等）"
    )
    generation_source: Optional[str] = Field(
        None, description="生成来源：ai/manual/import/legacy"
    )
    generation_model: Optional[str] = Field(None, description="生成所用模型标识")
    generation_method: Optional[str] = Field(
        None, description="生成方式：direct/plan/fallback 等"
    )
    status: Optional[str] = Field(None, description="状态：draft/confirmed/locked 等")
    generated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="生成时间"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="最后更新时间"
    )


class StoryboardModel(BaseModel):
    frames: List[StoryboardFrame]


class PlotPoint(BaseModel):
    description: str
    timing: Optional[str] = Field(None, description="出现时段：开场/中段/结尾等")
    purpose: Optional[str] = Field(None, description="该情节点的叙事目的")
    escalation: Optional[str] = Field(None, description="冲突/张力如何升级")


class ConflictItem(BaseModel):
    description: str
    intensity: Optional[str] = Field(None, description="强度：low/medium/high")
    parties: Optional[List[str]] = Field(None, description="冲突双方/多方")


class EpisodeBeat(BaseModel):
    sequence_number: int = Field(..., ge=1, description="顺序编号，从1开始")
    beat_title: str = Field(..., description="情节点标题")
    beat_summary: str = Field(..., description="情节点摘要")
    act_label: Optional[str] = Field(None, description="所在幕：ACT I/II/III 等")
    dramatic_question: Optional[str] = Field(None, description="悬念/戏剧问题")
    characters_involved: Optional[List[str]] = Field(
        None, description="参与角色名称列表"
    )
    location_hint: Optional[str] = Field(None, description="场景/地点提示")
    duration_estimate_minutes: Optional[float] = Field(
        None, ge=0, description="预估时长（分钟）"
    )


class EpisodeStepOutlineItem(BaseModel):
    episode_number: int
    title: Optional[str] = None
    logline: Optional[str] = None
    beats: Optional[List[EpisodeBeat]] = None
    structured_episode_contract: Optional[Dict[str, Any]] = Field(
        None, description="生产级剧集合同摘要（仅 production 生成要求）"
    )


class EpisodeStepOutlineModel(BaseModel):
    episodes: List[EpisodeStepOutlineItem]


class EpisodePlanItem(BaseModel):
    episode_number: int
    title: str
    summary: str
    market_region: Optional[str] = Field(None, description="目标市场/地区")
    micro_genre: Optional[str] = Field(None, description="微类型/细分题材")
    hook_plan: Optional[HookPlan] = Field(None, description="爽点/钩子节奏规划")
    twist_density: Optional[str] = Field(None, description="反转密度目标")
    cliffhanger_plan: Optional[List[str]] = Field(None, description="悬念/卡点规划")
    ad_snippets: Optional[List[AdSnippet]] = Field(None, description="投流素材建议")
    plot_points: Optional[List[PlotPoint]] = None
    character_arcs: Optional[Dict[str, Any]] = None
    conflicts: Optional[List[ConflictItem]] = None
    scene_count: Optional[int] = None
    scenes: Optional[List[Dict[str, Any]]] = None
    payoff: Optional[str] = Field(None, description="本集具体爽点/收获点")
    cliffhanger: Optional[str] = Field(None, description="本集结尾卡点")
    structured_episode_contract: Optional[Dict[str, Any]] = Field(
        None, description="生产级单集合同（仅 production 生成要求）"
    )


class EpisodePlanModel(BaseModel):
    episodes: List[EpisodePlanItem]


class StoryboardPlanFrameOutline(BaseModel):
    shot_type: Optional[str] = Field(None, description="景别：远景/中景/近景/特写")
    camera_movement: Optional[str] = Field(
        None, description="运镜：固定/推/拉/摇/移/跟/变焦"
    )
    composition: Optional[str] = Field(None, description="构图：三分法/对称/前后景")
    intent: Optional[str] = Field(None, description="画面意图/叙事作用（简短）")


class StoryboardPlanScene(BaseModel):
    scene_number: int
    target_frames: int = Field(..., ge=1, le=20)
    frames: List[StoryboardPlanFrameOutline]
    environment_id: Optional[int] = None
    character_ids: Optional[List[int]] = None


class StoryboardPlanModel(BaseModel):
    scenes: List[StoryboardPlanScene]
