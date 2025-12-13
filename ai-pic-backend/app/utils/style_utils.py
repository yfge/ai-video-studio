from __future__ import annotations

from typing import Any, Mapping, Optional

from app.schemas.style import (
    BackgroundDetailLevel,
    CharacterFaceStyle,
    CharacterProportion,
    ColorMood,
    ColorRenderStyle,
    CompositionStyle,
    EmotionActionLevel,
    LightingStyle,
    LineArtStyle,
    OutputTarget,
    ShotStoryboardStyle,
    StyleLockLevel,
    StyleOption,
    StylePreset,
    StyleSpec,
    StyleUniverse,
)


STYLE_DIMENSIONS: dict[str, type] = {
    "style_universe": StyleUniverse,
    "character_proportion": CharacterProportion,
    "character_face_style": CharacterFaceStyle,
    "line_art_style": LineArtStyle,
    "color_render_style": ColorRenderStyle,
    "lighting_style": LightingStyle,
    "color_mood": ColorMood,
    "shot_storyboard_style": ShotStoryboardStyle,
    "composition_style": CompositionStyle,
    "background_detail_level": BackgroundDetailLevel,
    "emotion_action_level": EmotionActionLevel,
    "style_lock_level": StyleLockLevel,
    "output_target": OutputTarget,
}


def humanize_style_value(value: str) -> str:
    return value.replace("_", " ").strip()


STYLE_OPTION_LABELS_ZH: dict[str, dict[str, str]] = {
    "style_universe": {
        "japanese_anime": "日系动漫",
        "chinese_comic": "国漫",
        "chinese_ink": "水墨国风",
        "chinese_national_trend": "国潮",
        "western_comic": "欧美漫画",
        "western_cartoon": "欧美卡通",
        "dark_fantasy": "暗黑奇幻",
        "sci_fi": "科幻",
        "cyberpunk": "赛博朋克",
        "steampunk": "蒸汽朋克",
        "fantasy_magic": "奇幻魔法",
        "experimental_art": "实验艺术",
    },
    "character_proportion": {
        "chibi_2_head": "Q版（2头身）",
        "super_deformed_3_head": "超Q（3头身）",
        "anime_5_head": "动漫（5头身）",
        "standard_6_head": "标准（6头身）",
        "realistic_7_head": "写实（7头身）",
        "cinematic_realistic": "电影写实",
    },
    "character_face_style": {
        "anime_big_eye": "大眼动漫",
        "anime_light_real": "轻写实动漫",
        "chinese_realistic": "国风写实",
        "western_realistic": "欧美写实",
        "cartoon_exaggerated": "夸张卡通",
        "minimalist_flat": "极简扁平",
        "cute_round": "可爱圆润",
    },
    "line_art_style": {
        "no_line_art": "无线稿",
        "thin_clean_line": "细线干净",
        "bold_outline": "粗线勾边",
        "sketchy_line": "草图线",
        "broken_line": "断线",
        "ink_brush_line": "墨刷线",
    },
    "color_render_style": {
        "flat_color": "平涂",
        "cell_shading": "赛璐璐",
        "soft_shading": "柔和上色",
        "semi_painterly": "半厚涂",
        "full_painterly": "厚涂",
        "watercolor": "水彩",
        "ink_wash": "水墨晕染",
    },
    "lighting_style": {
        "no_shadow": "无阴影",
        "single_shadow": "单层阴影",
        "soft_light": "柔光",
        "hard_light": "硬光",
        "cinematic_light": "电影光",
        "dramatic_contrast": "戏剧对比",
        "backlight_rim": "逆光轮廓光",
    },
    "color_mood": {
        "bright_vivid": "明亮鲜艳",
        "soft_pastel": "柔和粉彩",
        "warm_tone": "暖色调",
        "cool_tone": "冷色调",
        "low_saturation": "低饱和",
        "monochrome": "黑白/单色",
        "high_contrast": "高对比",
        "cinematic_lut": "电影LUT",
    },
    "shot_storyboard_style": {
        "anime_dynamic": "动漫动态",
        "cinematic_film": "电影镜头",
        "static_comic_panel": "静态漫画分镜",
        "vertical_webtoon": "竖屏条漫",
        "ppt_storyboard": "PPT分镜",
        "motion_comic": "动态漫画",
    },
    "composition_style": {
        "close_up": "特写",
        "medium_shot": "中景",
        "wide_shot": "全景",
        "extreme_wide": "远景",
        "portrait_focus": "人物肖像",
        "environment_focus": "环境为主",
        "negative_space": "留白构图",
    },
    "background_detail_level": {
        "no_background": "无背景",
        "simple_gradient": "简单渐变",
        "stylized_background": "风格化背景",
        "detailed_background": "细节背景",
        "cinematic_environment": "电影级环境",
    },
    "emotion_action_level": {
        "calm_static": "平静静态",
        "light_expression": "轻表情",
        "clear_emotion": "情绪明确",
        "dramatic_action": "强动作",
        "extreme_emotion": "极致情绪",
    },
    "style_lock_level": {
        "free": "自由",
        "scene_consistent": "场景一致",
        "character_consistent": "角色一致",
        "episode_consistent": "单集一致",
        "full_project_lock": "全项目锁定",
    },
    "output_target": {
        "short_video": "短视频",
        "long_serial": "长连载",
        "social_media": "社交媒体",
        "ip_design": "IP设计",
        "commercial_ad": "商业广告",
        "concept_art": "概念设定",
    },
}


STYLE_PROMPT_LABELS: dict[str, str] = {
    "style_universe": "style universe",
    "character_proportion": "character proportion",
    "character_face_style": "face style",
    "line_art_style": "line art",
    "color_render_style": "color render",
    "lighting_style": "lighting",
    "color_mood": "color mood",
    "shot_storyboard_style": "shot/storyboard",
    "composition_style": "composition",
    "background_detail_level": "background detail",
    "emotion_action_level": "emotion/action",
    "style_lock_level": "style lock",
    "output_target": "output target",
}


def build_style_prompt(spec: StyleSpec) -> str:
    """Convert a resolved StyleSpec into a prompt suffix (stable, engineering-oriented)."""

    # Use JSON mode to get enum values (strings) instead of Enum reprs.
    data = spec.model_dump(mode="json", exclude_none=True)
    if not data:
        return ""

    # Prefer explicit labels to reduce ambiguity across providers.
    parts: list[str] = []
    for key, value in data.items():
        label = STYLE_PROMPT_LABELS.get(key, key)
        parts.append(f"{label}: {humanize_style_value(str(value))}")
    return "STYLE_SPEC => " + "; ".join(parts)


def derive_legacy_image_style(spec: StyleSpec) -> str:
    """Map StyleSpec to the platform legacy `style` string (realistic/anime/cartoon/portrait)."""

    if spec.composition_style == CompositionStyle.PORTRAIT_FOCUS:
        return "portrait"

    if spec.style_universe in {
        StyleUniverse.JAPANESE_ANIME,
        StyleUniverse.CHINESE_COMIC,
        StyleUniverse.WESTERN_COMIC,
        StyleUniverse.FANTASY_MAGIC,
        StyleUniverse.SCI_FI,
        StyleUniverse.CYBERPUNK,
        StyleUniverse.STEAMPUNK,
        StyleUniverse.DARK_FANTASY,
        StyleUniverse.CHINESE_NATIONAL_TREND,
    }:
        return "anime"

    if spec.style_universe in {StyleUniverse.WESTERN_CARTOON}:
        return "cartoon"

    if (
        spec.line_art_style == LineArtStyle.NO_LINE_ART
        and spec.character_face_style
        in {CharacterFaceStyle.CHINESE_REALISTIC, CharacterFaceStyle.WESTERN_REALISTIC}
    ):
        return "realistic"

    return "realistic"


def derive_openai_image_style(spec: StyleSpec, *, fallback: str = "realistic") -> str:
    """Map StyleSpec to OpenAI image `style` ('vivid'|'natural')."""

    if spec.color_mood in {ColorMood.LOW_SATURATION, ColorMood.MONOCHROME}:
        return "natural"
    if spec.color_mood in {
        ColorMood.BRIGHT_VIVID,
        ColorMood.HIGH_CONTRAST,
        ColorMood.CINEMATIC_LUT,
    }:
        return "vivid"
    return "natural" if fallback == "realistic" else "vivid"


DEFAULT_STYLE_SPEC = StyleSpec(
    style_universe=StyleUniverse.JAPANESE_ANIME,
    character_proportion=CharacterProportion.ANIME_5_HEAD,
    character_face_style=CharacterFaceStyle.ANIME_BIG_EYE,
    line_art_style=LineArtStyle.THIN_CLEAN_LINE,
    color_render_style=ColorRenderStyle.CELL_SHADING,
    lighting_style=LightingStyle.SOFT_LIGHT,
    color_mood=ColorMood.BRIGHT_VIVID,
    shot_storyboard_style=ShotStoryboardStyle.ANIME_DYNAMIC,
    composition_style=CompositionStyle.MEDIUM_SHOT,
    background_detail_level=BackgroundDetailLevel.STYLIZED_BACKGROUND,
    emotion_action_level=EmotionActionLevel.CLEAR_EMOTION,
    style_lock_level=StyleLockLevel.CHARACTER_CONSISTENT,
    output_target=OutputTarget.LONG_SERIAL,
)


STYLE_PRESETS: dict[str, StylePreset] = {
    "default_manga": StylePreset(
        preset_id="default_manga",
        label="默认漫画",
        description="基础漫画预设（通用、均衡）。",
        spec=DEFAULT_STYLE_SPEC,
    ),
    "romance_anime_soft": StylePreset(
        preset_id="romance_anime_soft",
        label="恋爱动漫·柔和",
        description="恋爱向日系动漫（粉彩、柔光、温柔氛围）。",
        spec=StyleSpec(
            style_universe=StyleUniverse.JAPANESE_ANIME,
            character_proportion=CharacterProportion.ANIME_5_HEAD,
            character_face_style=CharacterFaceStyle.ANIME_BIG_EYE,
            line_art_style=LineArtStyle.THIN_CLEAN_LINE,
            color_render_style=ColorRenderStyle.CELL_SHADING,
            lighting_style=LightingStyle.SOFT_LIGHT,
            color_mood=ColorMood.SOFT_PASTEL,
            shot_storyboard_style=ShotStoryboardStyle.ANIME_DYNAMIC,
            composition_style=CompositionStyle.PORTRAIT_FOCUS,
            background_detail_level=BackgroundDetailLevel.STYLIZED_BACKGROUND,
            emotion_action_level=EmotionActionLevel.CLEAR_EMOTION,
            style_lock_level=StyleLockLevel.CHARACTER_CONSISTENT,
            output_target=OutputTarget.LONG_SERIAL,
        ),
    ),
    "dark_fantasy_dramatic": StylePreset(
        preset_id="dark_fantasy_dramatic",
        label="暗黑奇幻·戏剧光影",
        description="暗黑奇幻（电影光、强对比、戏剧张力）。",
        spec=StyleSpec(
            style_universe=StyleUniverse.DARK_FANTASY,
            character_proportion=CharacterProportion.STANDARD_6_HEAD,
            character_face_style=CharacterFaceStyle.ANIME_LIGHT_REAL,
            line_art_style=LineArtStyle.BOLD_OUTLINE,
            color_render_style=ColorRenderStyle.SEMI_PAINTERLY,
            lighting_style=LightingStyle.DRAMATIC_CONTRAST,
            color_mood=ColorMood.HIGH_CONTRAST,
            shot_storyboard_style=ShotStoryboardStyle.CINEMATIC_FILM,
            composition_style=CompositionStyle.WIDE_SHOT,
            background_detail_level=BackgroundDetailLevel.CINEMATIC_ENVIRONMENT,
            emotion_action_level=EmotionActionLevel.DRAMATIC_ACTION,
            style_lock_level=StyleLockLevel.EPISODE_CONSISTENT,
            output_target=OutputTarget.LONG_SERIAL,
        ),
    ),
    "chinese_ink_minimal": StylePreset(
        preset_id="chinese_ink_minimal",
        label="国风水墨·极简",
        description="水墨晕染（极简线条、黑白/单色情绪）。",
        spec=StyleSpec(
            style_universe=StyleUniverse.CHINESE_INK,
            character_proportion=CharacterProportion.STANDARD_6_HEAD,
            character_face_style=CharacterFaceStyle.MINIMALIST_FLAT,
            line_art_style=LineArtStyle.INK_BRUSH_LINE,
            color_render_style=ColorRenderStyle.INK_WASH,
            lighting_style=LightingStyle.SOFT_LIGHT,
            color_mood=ColorMood.MONOCHROME,
            shot_storyboard_style=ShotStoryboardStyle.STATIC_COMIC_PANEL,
            composition_style=CompositionStyle.NEGATIVE_SPACE,
            background_detail_level=BackgroundDetailLevel.STYLIZED_BACKGROUND,
            emotion_action_level=EmotionActionLevel.CALM_STATIC,
            style_lock_level=StyleLockLevel.SCENE_CONSISTENT,
            output_target=OutputTarget.CONCEPT_ART,
        ),
    ),
    "cyberpunk_neon": StylePreset(
        preset_id="cyberpunk_neon",
        label="赛博朋克·霓虹",
        description="赛博霓虹（逆光轮廓光、电影LUT、环境氛围强）。",
        spec=StyleSpec(
            style_universe=StyleUniverse.CYBERPUNK,
            character_proportion=CharacterProportion.REALISTIC_7_HEAD,
            character_face_style=CharacterFaceStyle.WESTERN_REALISTIC,
            line_art_style=LineArtStyle.NO_LINE_ART,
            color_render_style=ColorRenderStyle.SEMI_PAINTERLY,
            lighting_style=LightingStyle.BACKLIGHT_RIM,
            color_mood=ColorMood.CINEMATIC_LUT,
            shot_storyboard_style=ShotStoryboardStyle.MOTION_COMIC,
            composition_style=CompositionStyle.ENVIRONMENT_FOCUS,
            background_detail_level=BackgroundDetailLevel.CINEMATIC_ENVIRONMENT,
            emotion_action_level=EmotionActionLevel.CLEAR_EMOTION,
            style_lock_level=StyleLockLevel.EPISODE_CONSISTENT,
            output_target=OutputTarget.SHORT_VIDEO,
        ),
    ),
    "western_cartoon_bright": StylePreset(
        preset_id="western_cartoon_bright",
        label="欧美卡通·明亮",
        description="欧美卡通（粗线勾边、平涂、明亮色彩）。",
        spec=StyleSpec(
            style_universe=StyleUniverse.WESTERN_CARTOON,
            character_proportion=CharacterProportion.STANDARD_6_HEAD,
            character_face_style=CharacterFaceStyle.CARTOON_EXAGGERATED,
            line_art_style=LineArtStyle.BOLD_OUTLINE,
            color_render_style=ColorRenderStyle.FLAT_COLOR,
            lighting_style=LightingStyle.SINGLE_SHADOW,
            color_mood=ColorMood.BRIGHT_VIVID,
            shot_storyboard_style=ShotStoryboardStyle.STATIC_COMIC_PANEL,
            composition_style=CompositionStyle.MEDIUM_SHOT,
            background_detail_level=BackgroundDetailLevel.SIMPLE_GRADIENT,
            emotion_action_level=EmotionActionLevel.DRAMATIC_ACTION,
            style_lock_level=StyleLockLevel.CHARACTER_CONSISTENT,
            output_target=OutputTarget.SOCIAL_MEDIA,
        ),
    ),
    "realistic_cinematic": StylePreset(
        preset_id="realistic_cinematic",
        label="写实·电影感",
        description="电影写实（无线稿、柔和上色、电影灯光）。",
        spec=StyleSpec(
            style_universe=StyleUniverse.EXPERIMENTAL_ART,
            character_proportion=CharacterProportion.CINEMATIC_REALISTIC,
            character_face_style=CharacterFaceStyle.WESTERN_REALISTIC,
            line_art_style=LineArtStyle.NO_LINE_ART,
            color_render_style=ColorRenderStyle.SOFT_SHADING,
            lighting_style=LightingStyle.CINEMATIC_LIGHT,
            color_mood=ColorMood.CINEMATIC_LUT,
            shot_storyboard_style=ShotStoryboardStyle.CINEMATIC_FILM,
            composition_style=CompositionStyle.MEDIUM_SHOT,
            background_detail_level=BackgroundDetailLevel.CINEMATIC_ENVIRONMENT,
            emotion_action_level=EmotionActionLevel.CLEAR_EMOTION,
            style_lock_level=StyleLockLevel.CHARACTER_CONSISTENT,
            output_target=OutputTarget.COMMERCIAL_AD,
        ),
    ),
    "portrait_realistic": StylePreset(
        preset_id="portrait_realistic",
        label="写实·肖像",
        description="写实肖像（干净背景、柔光、人物聚焦）。",
        spec=StyleSpec(
            style_universe=StyleUniverse.EXPERIMENTAL_ART,
            character_proportion=CharacterProportion.CINEMATIC_REALISTIC,
            character_face_style=CharacterFaceStyle.WESTERN_REALISTIC,
            line_art_style=LineArtStyle.NO_LINE_ART,
            color_render_style=ColorRenderStyle.SOFT_SHADING,
            lighting_style=LightingStyle.SOFT_LIGHT,
            color_mood=ColorMood.WARM_TONE,
            shot_storyboard_style=ShotStoryboardStyle.CINEMATIC_FILM,
            composition_style=CompositionStyle.PORTRAIT_FOCUS,
            background_detail_level=BackgroundDetailLevel.SIMPLE_GRADIENT,
            emotion_action_level=EmotionActionLevel.LIGHT_EXPRESSION,
            style_lock_level=StyleLockLevel.CHARACTER_CONSISTENT,
            output_target=OutputTarget.IP_DESIGN,
        ),
    ),
}


def build_style_schema_options() -> dict[str, list[StyleOption]]:
    dimensions: dict[str, list[StyleOption]] = {}
    for key, enum_cls in STYLE_DIMENSIONS.items():
        options: list[StyleOption] = []
        zh_map = STYLE_OPTION_LABELS_ZH.get(key, {})
        for item in enum_cls:  # type: ignore[assignment]
            value = str(item.value)
            label = zh_map.get(value) or humanize_style_value(value)
            options.append(
                StyleOption(value=value, label=label)
            )
        dimensions[key] = options
    return dimensions


def list_style_presets() -> list[StylePreset]:
    return list(STYLE_PRESETS.values())


def get_style_preset(preset_id: str) -> Optional[StylePreset]:
    return STYLE_PRESETS.get(preset_id)


LEGACY_STYLE_PRESET_MAP: dict[str, str] = {
    "anime": "default_manga",
    "cartoon": "western_cartoon_bright",
    "realistic": "realistic_cinematic",
    "portrait": "portrait_realistic",
}


def resolve_style_spec(
    *,
    style_spec: StyleSpec | Mapping[str, Any] | None = None,
    style_preset_id: str | None = None,
    legacy_style: str | None = None,
    fill_defaults: bool = True,
) -> tuple[StyleSpec, dict[str, Any]]:
    """Resolve a full StyleSpec from optional preset + partial overrides + legacy style.

    - Frontend may send partial `style_spec` depending on the feature area.
    - Backend remains the source of truth by filling missing fields from preset/defaults.
    - `legacy_style` is supported for backward compatibility.
    """

    meta: dict[str, Any] = {
        "preset_id": None,
        "legacy_style": None,
        "filled_defaults": fill_defaults,
    }

    preset_id = (style_preset_id or "").strip() or None
    if not preset_id and legacy_style:
        mapped = LEGACY_STYLE_PRESET_MAP.get(str(legacy_style).strip().lower())
        if mapped:
            preset_id = mapped
            meta["legacy_style"] = str(legacy_style).strip().lower()

    base = StyleSpec()
    if preset_id:
        preset = get_style_preset(preset_id)
        if preset:
            base = preset.spec
            meta["preset_id"] = preset_id
        else:
            meta["preset_id"] = preset_id
            meta["preset_missing"] = True

    overrides = StyleSpec()
    if isinstance(style_spec, StyleSpec):
        overrides = style_spec
    elif isinstance(style_spec, Mapping):
        overrides = StyleSpec.model_validate(dict(style_spec))

    if fill_defaults:
        resolved = DEFAULT_STYLE_SPEC.model_copy(deep=True)
        resolved = resolved.model_copy(update=base.model_dump(exclude_none=True))
    else:
        resolved = base.model_copy(deep=True)

    resolved = resolved.model_copy(update=overrides.model_dump(exclude_none=True))
    return resolved, meta


def summarize_style_spec(spec: StyleSpec) -> str:
    data = spec.model_dump(mode="json", exclude_none=True)
    if not data:
        return ""
    parts = [f"{k}={v}" for k, v in data.items()]
    return "; ".join(parts)
