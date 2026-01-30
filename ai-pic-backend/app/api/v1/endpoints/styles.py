from __future__ import annotations

from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.style import StylePreset, StyleSchemaResponse
from app.utils.style_utils import (
    DEFAULT_STYLE_SPEC,
    build_style_schema_options,
    get_style_preset,
    list_style_presets,
)
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


@router.get("/schema", response_model=StyleSchemaResponse)
async def get_style_schema(current_user: User = Depends(get_current_active_user)):
    _ = current_user  # auth guard
    return StyleSchemaResponse(
        dimensions=build_style_schema_options(),
        defaults=DEFAULT_STYLE_SPEC,
    )


@router.get("/presets", response_model=list[StylePreset])
async def get_style_presets(current_user: User = Depends(get_current_active_user)):
    _ = current_user  # auth guard
    return list_style_presets()


@router.get("/presets/{preset_id}", response_model=StylePreset)
async def get_style_preset_detail(
    preset_id: str, current_user: User = Depends(get_current_active_user)
):
    _ = current_user  # auth guard
    preset = get_style_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="风格预设不存在")
    return preset
