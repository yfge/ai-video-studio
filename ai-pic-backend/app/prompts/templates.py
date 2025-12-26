"""
提示词模板定义

定义了各种AI任务的提示词模板常量和枚举
"""

from enum import Enum
from typing import Dict, List

class PromptCategory(Enum):
    """提示词类别枚举"""
    CHARACTER = "character"  # 角色相关
    STORY = "story"         # 故事相关  
    EPISODE = "episode"     # 剧集相关
    SCRIPT = "script"       # 剧本相关
    IMAGE = "image"         # 图像相关
    GENERAL = "general"     # 通用

class PromptTemplate(Enum):
    """提示词模板枚举"""
    # 角色相关
    VIRTUAL_IP_CREATION = "virtual_ip_creation"
    VIRTUAL_IP_STYLE_PROMPT = "virtual_ip_style_prompt"
    CHARACTER_PROFILE = "character_profile"

    # 故事相关
    STORY_OUTLINE = "story_outline"
    STORY_SUMMARY = "story_summary"

    # 剧集相关
    EPISODE_GENERATION = "episode_generation"
    EPISODE_OUTLINE = "episode_outline"
    EPISODE_STEP_OUTLINE = "episode_step_outline"
    EPISODE_STEP_OUTLINE_REPAIR = "episode_step_outline_repair"
    EPISODE_FROM_OUTLINE = "episode_from_outline"
    EPISODE_ENRICH = "episode_enrich"  # 剧集丰富（当时长不足时）
    EPISODE_DURATION_REJECT = "episode_duration_reject"  # 时长不符合要求时驳回重生成
    EPISODE_LIST = "episode_list"  # 剧集列表生成

    # 剧本相关
    SCRIPT_GENERATION = "script_generation"
    SCENE_WRITING = "scene_writing"
    DIALOGUE_WRITING = "dialogue_writing"
    SCRIPT_SCENES = "script_scenes"
    SCRIPT_DIALOGUES = "script_dialogues"
    SCRIPT_REVIEW = "script_review"  # 剧本审核（对白/舞台指示分类校正）
    SCENE_DESCRIPTION = "scene_description"  # 场景描述
    SCRIPT_WORD_COUNT_CONSTRAINT = "script_word_count_constraint"  # 剧本字数约束
    DIALOGUE_DURATION_ADJUST = "dialogue_duration_adjust"  # 对白时长调整建议

    # 分镜相关
    STORYBOARD_GENERATION = "storyboard_generation"  # 分镜生成
    STORYBOARD_SHOT = "storyboard_shot"  # 单个分镜画面
    STORYBOARD_PLAN = "storyboard_plan"  # 分镜规划
    STORYBOARD_SCENE = "storyboard_scene"  # 分镜规划场景展开
    STORYBOARD_KEYFRAME = "storyboard_keyframe"  # 分镜关键帧提示
    STORYBOARD_IMAGE_PROMPT = "storyboard_image_prompt"  # 分镜图像提示组装
    STORYBOARD_IMAGE_FALLBACK = "storyboard_image_fallback"  # 分镜图像缺省提示

    # 图像相关
    IMAGE_GENERATION = "image_generation"
    PORTRAIT_GENERATION = "portrait_generation"
    SCENE_IMAGE = "scene_image"
    ENVIRONMENT_IMAGE = "environment_image"  # 环境图像

    # 时间轴相关
    TIMELINE_GAP_REASONING = "timeline_gap_reasoning"  # 对白间隔推理
    TIMELINE_GAP_REPAIR = "timeline_gap_repair"  # 对白间隔修复

    # 系统提示词 (System Prompts)
    SYSTEM_PROMPT_STORY = "system_prompt_story"  # 故事创作系统提示
    SYSTEM_PROMPT_SCRIPT = "system_prompt_script"  # 剧本创作系统提示
    SYSTEM_PROMPT_JSON_STRICT = "system_prompt_json_strict"  # 严格JSON系统提示
    STORY_OUTLINE_REPAIR = "story_outline_repair"
    EPISODE_PLAN_REPAIR = "episode_plan_repair"

class ImageStyle(Enum):
    """图像风格枚举"""
    REALISTIC = "realistic"
    ANIME = "anime"
    CARTOON = "cartoon"
    PORTRAIT = "portrait"
    ARTISTIC = "artistic"
    SKETCH = "sketch"
    RENDER_3D = "3d"

class ImageCategory(Enum):
    """图像类别枚举"""
    PORTRAIT = "portrait"
    FULL_BODY = "full_body"
    ACTION = "action"
    EMOTION = "emotion"
    SCENE = "scene"
    CONCEPT = "concept"

class ScriptFormat(Enum):
    """剧本格式枚举"""
    SCREENPLAY = "screenplay"      # 电影剧本
    TELEPLAY = "teleplay"         # 电视剧本
    STAGE = "stage"               # 舞台剧本
    AUDIO = "audio"               # 音频剧本
    ANIMATION = "animation"       # 动画剧本

class DialogueStyle(Enum):
    """对话风格枚举"""
    NATURAL = "natural"           # 自然对话
    FORMAL = "formal"             # 正式对话
    CASUAL = "casual"             # 随意对话
    DRAMATIC = "dramatic"         # 戏剧对话
    COMEDIC = "comedic"          # 喜剧对话

class PlotComplexity(Enum):
    """情节复杂度枚举"""
    SIMPLE = "simple"             # 简单
    MEDIUM = "medium"             # 中等
    COMPLEX = "complex"           # 复杂

class Pacing(Enum):
    """节奏枚举"""
    SLOW = "slow"                 # 慢节奏
    MEDIUM = "medium"             # 中等节奏
    FAST = "fast"                 # 快节奏

# 模板分类映射
TEMPLATE_CATEGORIES: Dict[PromptTemplate, PromptCategory] = {
    PromptTemplate.VIRTUAL_IP_CREATION: PromptCategory.CHARACTER,
    PromptTemplate.VIRTUAL_IP_STYLE_PROMPT: PromptCategory.CHARACTER,
    PromptTemplate.CHARACTER_PROFILE: PromptCategory.CHARACTER,

    PromptTemplate.STORY_OUTLINE: PromptCategory.STORY,
    PromptTemplate.STORY_SUMMARY: PromptCategory.STORY,

    PromptTemplate.EPISODE_GENERATION: PromptCategory.EPISODE,
    PromptTemplate.EPISODE_OUTLINE: PromptCategory.EPISODE,
    PromptTemplate.EPISODE_STEP_OUTLINE: PromptCategory.EPISODE,
    PromptTemplate.EPISODE_STEP_OUTLINE_REPAIR: PromptCategory.EPISODE,
    PromptTemplate.EPISODE_FROM_OUTLINE: PromptCategory.EPISODE,
    PromptTemplate.EPISODE_ENRICH: PromptCategory.EPISODE,
    PromptTemplate.EPISODE_DURATION_REJECT: PromptCategory.EPISODE,
    PromptTemplate.EPISODE_LIST: PromptCategory.EPISODE,

    PromptTemplate.SCRIPT_GENERATION: PromptCategory.SCRIPT,
    PromptTemplate.SCENE_WRITING: PromptCategory.SCRIPT,
    PromptTemplate.DIALOGUE_WRITING: PromptCategory.SCRIPT,
    PromptTemplate.SCRIPT_SCENES: PromptCategory.SCRIPT,
    PromptTemplate.SCRIPT_DIALOGUES: PromptCategory.SCRIPT,
    PromptTemplate.SCRIPT_REVIEW: PromptCategory.SCRIPT,
    PromptTemplate.SCENE_DESCRIPTION: PromptCategory.SCRIPT,
    PromptTemplate.SCRIPT_WORD_COUNT_CONSTRAINT: PromptCategory.SCRIPT,
    PromptTemplate.DIALOGUE_DURATION_ADJUST: PromptCategory.SCRIPT,
    PromptTemplate.STORYBOARD_GENERATION: PromptCategory.SCRIPT,
    PromptTemplate.STORYBOARD_SHOT: PromptCategory.SCRIPT,
    PromptTemplate.STORYBOARD_PLAN: PromptCategory.SCRIPT,
    PromptTemplate.STORYBOARD_SCENE: PromptCategory.SCRIPT,
    PromptTemplate.STORYBOARD_KEYFRAME: PromptCategory.SCRIPT,
    PromptTemplate.STORYBOARD_IMAGE_PROMPT: PromptCategory.SCRIPT,
    PromptTemplate.STORYBOARD_IMAGE_FALLBACK: PromptCategory.SCRIPT,

    PromptTemplate.IMAGE_GENERATION: PromptCategory.IMAGE,
    PromptTemplate.PORTRAIT_GENERATION: PromptCategory.IMAGE,
    PromptTemplate.SCENE_IMAGE: PromptCategory.IMAGE,
    PromptTemplate.ENVIRONMENT_IMAGE: PromptCategory.IMAGE,

    PromptTemplate.SYSTEM_PROMPT_STORY: PromptCategory.GENERAL,
    PromptTemplate.SYSTEM_PROMPT_SCRIPT: PromptCategory.GENERAL,
    PromptTemplate.SYSTEM_PROMPT_JSON_STRICT: PromptCategory.GENERAL,
    PromptTemplate.STORY_OUTLINE_REPAIR: PromptCategory.GENERAL,
    PromptTemplate.EPISODE_PLAN_REPAIR: PromptCategory.GENERAL,
    PromptTemplate.EPISODE_STEP_OUTLINE_REPAIR: PromptCategory.GENERAL,

    # 时间轴相关
    PromptTemplate.TIMELINE_GAP_REASONING: PromptCategory.SCRIPT,
    PromptTemplate.TIMELINE_GAP_REPAIR: PromptCategory.SCRIPT,
}

# 默认参数配置
DEFAULT_GENERATION_PARAMS = {
    "story_outline": {
        "target_audience": "普通观众",
        "duration_minutes": 90,
        "style_preferences": ["正能量", "有趣"],
        "content_restrictions": ["暴力", "色情"]
    },
    
    "episode_generation": {
        "episode_duration": 30,
        "plot_complexity": PlotComplexity.MEDIUM.value,
        "pacing": Pacing.MEDIUM.value
    },
    
    "script_generation": {
        "format_type": ScriptFormat.TELEPLAY.value,
        "language": "zh-CN",
        "dialogue_style": DialogueStyle.NATURAL.value,
        "scene_detail_level": "medium"
    },
    
    "image_generation": {
        "style": ImageStyle.REALISTIC.value,
        "category": ImageCategory.PORTRAIT.value,
        "resolution": "512x768",
        "quality": "high"
    }
}

# 质量提升关键词
QUALITY_ENHANCERS = {
    "image": {
        "general": ["high quality", "detailed", "masterpiece", "best quality"],
        "realistic": ["photorealistic", "8k", "ultra-detailed", "professional photography"],
        "anime": ["anime masterpiece", "detailed anime", "high resolution anime"],
        "artistic": ["trending on artstation", "award-winning art", "professional illustration"]
    },
    
    "text": {
        "creativity": ["创意", "原创", "有趣"],
        "quality": ["专业", "精彩", "引人入胜"],
        "structure": ["结构完整", "逻辑清晰", "层次分明"]
    }
}

# 负面提示词
NEGATIVE_PROMPTS = {
    "image": {
        "common": ["low quality", "blurry", "distorted", "bad anatomy"],
        "faces": ["bad face", "ugly face", "asymmetrical eyes"],
        "hands": ["bad hands", "missing fingers", "extra fingers"],
        "general": ["worst quality", "low resolution", "jpeg artifacts"]
    },
    
    "text": {
        "content": ["暴力", "色情", "政治敏感"],
        "quality": ["低质量", "逻辑混乱", "表达不清"]
    }
}

# 模板使用示例
TEMPLATE_EXAMPLES = {
    PromptTemplate.VIRTUAL_IP_CREATION: {
        "name": "小雅",
        "description": "一个活泼可爱的年轻女孩",
        "age": "22岁",
        "gender": "女性",
        "personality_traits": ["活泼", "好奇", "乐观"],
        "style_preference": "现代时尚",
        "target_audience": "年轻人"
    },
    PromptTemplate.VIRTUAL_IP_STYLE_PROMPT: {
        "name": "小雅",
        "description": "22岁活泼女孩，短发，甜美笑容",
        "biography": "开朗乐观，喜欢摄影与旅行，日常休闲穿搭",
        "image_category": "portrait",
    },
    
    PromptTemplate.STORY_OUTLINE: {
        "title": "友情的力量",
        "genre": "剧情",
        "theme": "友情与成长",
        "characters": [
            {"name": "小雅", "description": "活泼的大学生"},
            {"name": "李明", "description": "内向的程序员"}
        ]
    },
    
    PromptTemplate.IMAGE_GENERATION: {
        "character_name": "小雅",
        "character_description": "22岁活泼女孩",
        "style": "realistic",
        "category": "portrait"
    }
}

def get_template_by_category(category: PromptCategory) -> List[PromptTemplate]:
    """根据类别获取模板列表"""
    return [
        template for template, cat in TEMPLATE_CATEGORIES.items() 
        if cat == category
    ]

def get_category_by_template(template: PromptTemplate) -> PromptCategory:
    """根据模板获取类别"""
    return TEMPLATE_CATEGORIES.get(template, PromptCategory.GENERAL)
