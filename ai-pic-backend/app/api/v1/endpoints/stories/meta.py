from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/genres")
async def get_story_genres():
    """获取故事类型列表"""
    return [
        {"value": "drama", "label": "剧情"},
        {"value": "comedy", "label": "喜剧"},
        {"value": "romance", "label": "爱情"},
        {"value": "thriller", "label": "惊悚"},
        {"value": "action", "label": "动作"},
        {"value": "fantasy", "label": "奇幻"},
        {"value": "sci-fi", "label": "科幻"},
        {"value": "horror", "label": "恐怖"},
        {"value": "mystery", "label": "悬疑"},
        {"value": "historical", "label": "历史"},
        {"value": "biographical", "label": "传记"},
        {"value": "documentary", "label": "纪录片"},
    ]
