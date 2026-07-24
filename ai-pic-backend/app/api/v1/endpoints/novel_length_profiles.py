from app.schemas.story_novel_export import NovelLengthProfileResponse
from app.services.story.story_novel_length_contract import list_length_profiles
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class NovelLengthProfileListResponse(BaseModel):
    items: list[NovelLengthProfileResponse]


@router.get("/length-profiles", response_model=NovelLengthProfileListResponse)
def get_novel_length_profiles():
    return {"items": list_length_profiles()}
