from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StyleUniverse(str, Enum):
    JAPANESE_ANIME = "japanese_anime"
    CHINESE_COMIC = "chinese_comic"
    CHINESE_INK = "chinese_ink"
    CHINESE_NATIONAL_TREND = "chinese_national_trend"
    WESTERN_COMIC = "western_comic"
    WESTERN_CARTOON = "western_cartoon"
    DARK_FANTASY = "dark_fantasy"
    SCI_FI = "sci_fi"
    CYBERPUNK = "cyberpunk"
    STEAMPUNK = "steampunk"
    FANTASY_MAGIC = "fantasy_magic"
    EXPERIMENTAL_ART = "experimental_art"


class CharacterProportion(str, Enum):
    CHIBI_2_HEAD = "chibi_2_head"
    SUPER_DEFORMED_3_HEAD = "super_deformed_3_head"
    ANIME_5_HEAD = "anime_5_head"
    STANDARD_6_HEAD = "standard_6_head"
    REALISTIC_7_HEAD = "realistic_7_head"
    CINEMATIC_REALISTIC = "cinematic_realistic"


class CharacterFaceStyle(str, Enum):
    ANIME_BIG_EYE = "anime_big_eye"
    ANIME_LIGHT_REAL = "anime_light_real"
    CHINESE_REALISTIC = "chinese_realistic"
    WESTERN_REALISTIC = "western_realistic"
    CARTOON_EXAGGERATED = "cartoon_exaggerated"
    MINIMALIST_FLAT = "minimalist_flat"
    CUTE_ROUND = "cute_round"


class LineArtStyle(str, Enum):
    NO_LINE_ART = "no_line_art"
    THIN_CLEAN_LINE = "thin_clean_line"
    BOLD_OUTLINE = "bold_outline"
    SKETCHY_LINE = "sketchy_line"
    BROKEN_LINE = "broken_line"
    INK_BRUSH_LINE = "ink_brush_line"


class ColorRenderStyle(str, Enum):
    FLAT_COLOR = "flat_color"
    CELL_SHADING = "cell_shading"
    SOFT_SHADING = "soft_shading"
    SEMI_PAINTERLY = "semi_painterly"
    FULL_PAINTERLY = "full_painterly"
    WATERCOLOR = "watercolor"
    INK_WASH = "ink_wash"


class LightingStyle(str, Enum):
    NO_SHADOW = "no_shadow"
    SINGLE_SHADOW = "single_shadow"
    SOFT_LIGHT = "soft_light"
    HARD_LIGHT = "hard_light"
    CINEMATIC_LIGHT = "cinematic_light"
    DRAMATIC_CONTRAST = "dramatic_contrast"
    BACKLIGHT_RIM = "backlight_rim"


class ColorMood(str, Enum):
    BRIGHT_VIVID = "bright_vivid"
    SOFT_PASTEL = "soft_pastel"
    WARM_TONE = "warm_tone"
    COOL_TONE = "cool_tone"
    LOW_SATURATION = "low_saturation"
    MONOCHROME = "monochrome"
    HIGH_CONTRAST = "high_contrast"
    CINEMATIC_LUT = "cinematic_lut"


class ShotStoryboardStyle(str, Enum):
    ANIME_DYNAMIC = "anime_dynamic"
    CINEMATIC_FILM = "cinematic_film"
    STATIC_COMIC_PANEL = "static_comic_panel"
    VERTICAL_WEBTOON = "vertical_webtoon"
    PPT_STORYBOARD = "ppt_storyboard"
    MOTION_COMIC = "motion_comic"


class CompositionStyle(str, Enum):
    CLOSE_UP = "close_up"
    MEDIUM_SHOT = "medium_shot"
    WIDE_SHOT = "wide_shot"
    EXTREME_WIDE = "extreme_wide"
    PORTRAIT_FOCUS = "portrait_focus"
    ENVIRONMENT_FOCUS = "environment_focus"
    NEGATIVE_SPACE = "negative_space"


class BackgroundDetailLevel(str, Enum):
    NO_BACKGROUND = "no_background"
    SIMPLE_GRADIENT = "simple_gradient"
    STYLIZED_BACKGROUND = "stylized_background"
    DETAILED_BACKGROUND = "detailed_background"
    CINEMATIC_ENVIRONMENT = "cinematic_environment"


class EmotionActionLevel(str, Enum):
    CALM_STATIC = "calm_static"
    LIGHT_EXPRESSION = "light_expression"
    CLEAR_EMOTION = "clear_emotion"
    DRAMATIC_ACTION = "dramatic_action"
    EXTREME_EMOTION = "extreme_emotion"


class StyleLockLevel(str, Enum):
    FREE = "free"
    SCENE_CONSISTENT = "scene_consistent"
    CHARACTER_CONSISTENT = "character_consistent"
    EPISODE_CONSISTENT = "episode_consistent"
    FULL_PROJECT_LOCK = "full_project_lock"


class OutputTarget(str, Enum):
    SHORT_VIDEO = "short_video"
    LONG_SERIAL = "long_serial"
    SOCIAL_MEDIA = "social_media"
    IP_DESIGN = "ip_design"
    COMMERCIAL_AD = "commercial_ad"
    CONCEPT_ART = "concept_art"


class StyleSpec(BaseModel):
    """Platform-ready style schema; all fields are optional to allow partial overrides."""

    model_config = ConfigDict(extra="forbid")

    style_universe: Optional[StyleUniverse] = Field(default=None)
    character_proportion: Optional[CharacterProportion] = Field(default=None)
    character_face_style: Optional[CharacterFaceStyle] = Field(default=None)
    line_art_style: Optional[LineArtStyle] = Field(default=None)
    color_render_style: Optional[ColorRenderStyle] = Field(default=None)
    lighting_style: Optional[LightingStyle] = Field(default=None)
    color_mood: Optional[ColorMood] = Field(default=None)
    shot_storyboard_style: Optional[ShotStoryboardStyle] = Field(default=None)
    composition_style: Optional[CompositionStyle] = Field(default=None)
    background_detail_level: Optional[BackgroundDetailLevel] = Field(default=None)
    emotion_action_level: Optional[EmotionActionLevel] = Field(default=None)
    style_lock_level: Optional[StyleLockLevel] = Field(default=None)
    output_target: Optional[OutputTarget] = Field(default=None)


class StyleOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str
    label: str


class StylePreset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preset_id: str
    label: str
    description: Optional[str] = None
    spec: StyleSpec


class StyleSchemaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimensions: dict[str, list[StyleOption]]
    defaults: StyleSpec
