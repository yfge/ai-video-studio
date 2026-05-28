from __future__ import annotations

from app.prompts.templates import (
    DialogueStyle,
    ImageCategory,
    ImageStyle,
    Pacing,
    PlotComplexity,
    PromptTemplate,
    ScriptFormat,
)

DEFAULT_GENERATION_PARAMS = {
    "story_outline": {
        "target_audience": "普通观众",
        "duration_minutes": 90,
        "style_preferences": ["正能量", "有趣"],
        "content_restrictions": ["暴力", "色情"],
    },
    "episode_generation": {
        "episode_duration": 30,
        "plot_complexity": PlotComplexity.MEDIUM.value,
        "pacing": Pacing.MEDIUM.value,
    },
    "script_generation": {
        "format_type": ScriptFormat.TELEPLAY.value,
        "language": "zh-CN",
        "dialogue_style": DialogueStyle.NATURAL.value,
        "scene_detail_level": "medium",
    },
    "image_generation": {
        "style": ImageStyle.REALISTIC.value,
        "category": ImageCategory.PORTRAIT.value,
        "resolution": "512x768",
        "quality": "high",
    },
}

QUALITY_ENHANCERS = {
    "image": {
        "general": ["high quality", "detailed", "masterpiece", "best quality"],
        "realistic": [
            "photorealistic",
            "8k",
            "ultra-detailed",
            "professional photography",
        ],
        "anime": ["anime masterpiece", "detailed anime", "high resolution anime"],
        "artistic": [
            "trending on artstation",
            "award-winning art",
            "professional illustration",
        ],
    },
    "text": {
        "creativity": ["创意", "原创", "有趣"],
        "quality": ["专业", "精彩", "引人入胜"],
        "structure": ["结构完整", "逻辑清晰", "层次分明"],
    },
}

NEGATIVE_PROMPTS = {
    "image": {
        "common": ["low quality", "blurry", "distorted", "bad anatomy"],
        "faces": ["bad face", "ugly face", "asymmetrical eyes"],
        "hands": ["bad hands", "missing fingers", "extra fingers"],
        "general": ["worst quality", "low resolution", "jpeg artifacts"],
    },
    "text": {
        "content": ["暴力", "色情", "政治敏感"],
        "quality": ["低质量", "逻辑混乱", "表达不清"],
    },
}

TEMPLATE_EXAMPLES = {
    PromptTemplate.VIRTUAL_IP_CREATION: {
        "name": "小雅",
        "description": "一个活泼可爱的年轻女孩",
        "age": "22岁",
        "gender": "女性",
        "personality_traits": ["活泼", "好奇", "乐观"],
        "style_preference": "现代时尚",
        "target_audience": "年轻人",
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
            {"name": "李明", "description": "内向的程序员"},
        ],
    },
    PromptTemplate.IMAGE_GENERATION: {
        "character_name": "小雅",
        "character_description": "22岁活泼女孩",
        "style": "realistic",
        "category": "portrait",
    },
}
