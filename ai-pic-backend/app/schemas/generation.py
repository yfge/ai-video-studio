from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class CharacterInfo(BaseModel):
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述或定位")
    role: Optional[str] = Field(None, description="角色类型/职责")


class PlotStructure(BaseModel):
    act1: Optional[str] = None
    act2: Optional[str] = None
    act3: Optional[str] = None


class StoryOutlineModel(BaseModel):
    premise: str = Field(..., description="故事前提/核心概念")
    synopsis: str = Field(..., description="详细故事概要")
    main_conflict: Optional[str] = Field(None, description="主要冲突")
    resolution: Optional[str] = Field(None, description="解决方案/结局")
    character_relationships: Optional[Dict[str, Any]] = Field(None, description="角色关系网")
    main_characters: Optional[List[CharacterInfo]] = Field(None, description="主要角色")
    plot_structure: Optional[PlotStructure] = Field(None, description="三幕式结构")
    core_values: Optional[str] = Field(None, description="核心价值")
    visual_style: Optional[str] = Field(None, description="视觉风格建议")
    selling_points: Optional[List[str]] = Field(None, description="营销卖点")


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


class ScriptModel(BaseModel):
    content: str
    scenes: Optional[List[SceneItem]] = None
    dialogues: Optional[List[DialogueItem]] = None
    stage_directions: Optional[List[StageDirectionItem]] = None
    metadata: Optional[ScriptMetadata] = None

# 分镜（Storyboard）
class StoryboardFrame(BaseModel):
    # Accept any string id; default to a UUID string when absent.
    frame_id: str = Field(default_factory=lambda: str(uuid4()), description="分镜帧唯一标识（字符串）")
    frame_number: Optional[int] = None
    scene_number: Optional[int] = None
    scene_index: Optional[int] = Field(None, description="在剧本场景列表中的索引（从1开始）")
    shot_type: Optional[str] = Field(None, description="景别：远景/中景/近景/特写 等")
    camera_movement: Optional[str] = Field(None, description="运镜：推/拉/摇/移/跟/变焦 等")
    composition: Optional[str] = Field(None, description="构图：三分法/对称/前后景 等")
    description: str = Field(..., description="画面描述与动作")
    duration_seconds: Optional[float] = Field(None, description="建议时长（秒）")
    ai_prompt: Optional[str] = Field(None, description="用于生成图像/视频的提示词")
    reference_images: Optional[List[str]] = Field(None, description="参考图 URL 列表")
    image_url: Optional[str] = Field(None, description="生成的分镜图像URL（生成后回填）")
    video_url: Optional[str] = Field(None, description="生成的视频URL（生成后回填）")
    generation_source: Optional[str] = Field(None, description="生成来源：ai/manual/import/legacy")
    generation_model: Optional[str] = Field(None, description="生成所用模型标识")
    generation_method: Optional[str] = Field(None, description="生成方式：direct/plan/fallback 等")
    status: Optional[str] = Field(None, description="状态：draft/confirmed/locked 等")
    generated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="生成时间")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="最后更新时间")


class StoryboardModel(BaseModel):
    frames: List[StoryboardFrame]


# 剧集规划（Episode Plan）
class PlotPoint(BaseModel):
    description: str
    timing: Optional[str] = Field(None, description="出现时段：开场/中段/结尾等")
    purpose: Optional[str] = Field(None, description="该情节点的叙事目的")
    escalation: Optional[str] = Field(None, description="冲突/张力如何升级")


class ConflictItem(BaseModel):
    description: str
    intensity: Optional[str] = Field(None, description="强度：low/medium/high")
    parties: Optional[List[str]] = Field(None, description="冲突双方/多方")


class EpisodePlanItem(BaseModel):
    episode_number: int
    title: str
    summary: str
    plot_points: Optional[List[PlotPoint]] = None
    character_arcs: Optional[Dict[str, Any]] = None
    conflicts: Optional[List[ConflictItem]] = None
    scene_count: Optional[int] = None


class EpisodePlanModel(BaseModel):
    episodes: List[EpisodePlanItem]


# 分镜规划（Storyboard Plan）
class StoryboardPlanFrameOutline(BaseModel):
    shot_type: Optional[str] = Field(None, description="景别：远景/中景/近景/特写")
    camera_movement: Optional[str] = Field(None, description="运镜：固定/推/拉/摇/移/跟/变焦")
    composition: Optional[str] = Field(None, description="构图：三分法/对称/前后景")
    intent: Optional[str] = Field(None, description="画面意图/叙事作用（简短）")


class StoryboardPlanScene(BaseModel):
    scene_number: int
    target_frames: int = Field(..., ge=1, le=20)
    frames: List[StoryboardPlanFrameOutline]


class StoryboardPlanModel(BaseModel):
    scenes: List[StoryboardPlanScene]
