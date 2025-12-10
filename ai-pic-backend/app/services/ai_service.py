import httpx
import asyncio
import base64
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import (
    StoryOutlineModel,
    ScriptModel,
    EpisodePlanModel,
    StoryboardModel,
    StoryboardPlanModel,
    StoryboardPlanScene,
)
from app.services.storyboard_reasoner import (
    StoryboardReActReasoner,
    LANGGRAPH_AVAILABLE,
)
from app.services.episode_agent import EpisodeLangGraphAgent
from app.services.script_agent import ScriptLangGraphAgent
from app.services.story_agent import StoryLangGraphAgent
from app.utils.json_utils import extract_json_block

# 尝试导入AI服务管理器，如果失败则使用None
try:
    from .ai_service_manager import (
        AIServiceManager,
        AIServiceConfig,
        ProviderWeight,
        ProviderPriority,
    )
    from .providers.base import ProviderConfig, AIModelType

    AI_MANAGER_AVAILABLE = True
except ImportError as e:
    logger = get_logger()
    logger.warning(f"AI服务管理器导入失败，将使用fallback模式: {e}")
    AIServiceManager = None
    AIServiceConfig = None
    ProviderWeight = None
    ProviderPriority = None
    ProviderConfig = None
    AI_MANAGER_AVAILABLE = False
from .storage.oss_service import oss_service


def _trim_text(value: str | None, limit: int = 160) -> str:
    if not value:
        return ""
    text = str(value).replace("\n", " ").strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def _to_int_safe(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _collect_scene_dialogues(
    script: Dict[str, Any], scene_number: Optional[int], limit: int = 2
) -> List[str]:
    dialogues = []
    for item in script.get("dialogues") or []:
        if isinstance(item, dict):
            sn = _to_int_safe(item.get("scene_number"))
            content = item.get("content") or item.get("text") or item.get("line")
        else:
            sn = None
            content = str(item)
        if scene_number is not None and sn != scene_number:
            continue
        if not content:
            continue
        dialogues.append(_trim_text(content, 80))
        if len(dialogues) >= limit:
            break
    return dialogues


def _collect_stage_notes(
    script: Dict[str, Any], scene_number: Optional[int], limit: int = 2
) -> List[str]:
    notes = []
    for item in script.get("stage_directions") or []:
        if isinstance(item, dict):
            sn = _to_int_safe(item.get("scene_number"))
            content = (
                item.get("content") or item.get("direction") or item.get("description")
            )
        else:
            sn = None
            content = str(item)
        if scene_number is not None and sn != scene_number:
            continue
        if not content:
            continue
        notes.append(_trim_text(content, 80))
        if len(notes) >= limit:
            break
    return notes


def _build_storyboard_context(script: Dict[str, Any]) -> str:
    story = script.get("story") or {}
    episode = script.get("episode") or {}
    scenes = script.get("scenes") or []
    scene_indices = script.get("scene_indices") or []

    sections: List[str] = []
    if story:
        story_bits = []
        if story.get("title"):
            story_bits.append(str(story["title"]))
        if story.get("genre"):
            story_bits.append(f"类型:{story['genre']}")
        if story.get("theme"):
            story_bits.append(f"主题:{_trim_text(story['theme'], 80)}")
        if story.get("world_building"):
            story_bits.append(f"设定:{_trim_text(story['world_building'], 100)}")
        if story_bits:
            sections.append("故事背景：" + "，".join(story_bits))

    if episode:
        epi_bits = []
        if episode.get("episode_number"):
            epi_bits.append(f"第{episode['episode_number']}集")
        if episode.get("title"):
            epi_bits.append(str(episode["title"]))
        if episode.get("summary"):
            epi_bits.append(f"概要:{_trim_text(episode['summary'], 120)}")
        if episode.get("duration_minutes"):
            epi_bits.append(f"时长:{episode['duration_minutes']}分钟")
        if episode.get("scene_count"):
            epi_bits.append(f"场景数:{episode['scene_count']}")
        if epi_bits:
            sections.append("剧集信息：" + "，".join(epi_bits))

    for idx, raw_scene in enumerate(scenes):
        if isinstance(raw_scene, dict):
            scene_dict = raw_scene
            description = scene_dict.get("description")
            location = scene_dict.get("location") or scene_dict.get("place")
            time = scene_dict.get("time") or scene_dict.get("period")
            characters = scene_dict.get("characters") or scene_dict.get("cast")
            notes = scene_dict.get("notes")
        else:
            scene_dict = {}
            description = str(raw_scene)
            location = time = characters = notes = None

        scene_no = scene_indices[idx] if idx < len(scene_indices) else idx + 1
        heading = f"场景 {scene_no}"
        details: List[str] = []
        if location:
            details.append(f"地点:{_trim_text(location, 50)}")
        if time:
            details.append(f"时间:{_trim_text(time, 40)}")
        if characters:
            if isinstance(characters, list):
                details.append(f"角色:{_trim_text(', '.join(map(str, characters)), 80)}")
            else:
                details.append(f"角色:{_trim_text(str(characters), 80)}")
        if notes:
            details.append(f"备注:{_trim_text(notes, 80)}")
        details.append(f"描述:{_trim_text(description, 120)}")

        dialogues = _collect_scene_dialogues(script, scene_no)
        if dialogues:
            details.append("对白:" + " / ".join(dialogues))
        stage_notes = _collect_stage_notes(script, scene_no)
        if stage_notes:
            details.append("舞台:" + " / ".join(stage_notes))

        sections.append(f"{heading} -> " + "；".join(details))

    content_excerpt = _trim_text(script.get("content"), 400)
    if content_excerpt:
        sections.append(f"剧本文本片段：{content_excerpt}")

    context = "\n".join(sections)
    return context[:4000]


class AIService:
    """AI服务接口 - 集成新的多提供商系统"""

    def __init__(self):
        self.logger = get_logger()
        self.logger.info("Initializing AI Service")

        # 保持向后兼容的配置
        self.base_url = settings.AI_SERVICE_URL
        self.api_key = settings.AI_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.stability_api_key = settings.STABILITY_API_KEY

        # 初始化多提供商AI服务管理器
        self.ai_manager = self._initialize_ai_manager()
        self.storyboard_reasoner = (
            StoryboardReActReasoner(self) if LANGGRAPH_AVAILABLE else None
        )
        self.episode_agent = (
            EpisodeLangGraphAgent(self) if LANGGRAPH_AVAILABLE else None
        )
        self.script_agent = ScriptLangGraphAgent(self) if LANGGRAPH_AVAILABLE else None
        self.story_agent = StoryLangGraphAgent(self) if LANGGRAPH_AVAILABLE else None

    def _initialize_ai_manager(self) -> Optional[AIServiceManager]:
        """初始化AI服务管理器"""
        if not AI_MANAGER_AVAILABLE:
            self.logger.warning("AI服务管理器不可用，使用fallback模式")
            return None

        try:
            # 构建提供商配置
            providers = {}
            provider_weights = {}

            # OpenAI配置
            if self.openai_api_key:
                providers["openai"] = ProviderConfig(
                    name="openai",
                    api_key=self.openai_api_key,
                    base_url="https://api.openai.com/v1",
                    timeout=120.0,
                )
                provider_weights["openai"] = ProviderWeight(
                    provider_name="openai",
                    weight=1.0,
                    priority=ProviderPriority.HIGH,
                    enabled=True,
                    max_requests_per_minute=100,
                )

            # 其他提供商配置（支持双密钥认证）
            # 可灵AI（快手）
            if settings.KELING_API_KEY and settings.KELING_SECRET_KEY:
                providers["keling"] = ProviderConfig(
                    name="keling",
                    api_key=settings.KELING_API_KEY,
                    api_secret=settings.KELING_SECRET_KEY,
                    base_url="https://klingai.com/api/v1",
                    timeout=120.0,
                )
                provider_weights["keling"] = ProviderWeight(
                    provider_name="keling",
                    weight=0.8,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=60,
                )

            # 即梦AI
            if settings.JIMENG_API_KEY and settings.JIMENG_SECRET_KEY:
                providers["jimeng"] = ProviderConfig(
                    name="jimeng",
                    api_key=settings.JIMENG_API_KEY,
                    api_secret=settings.JIMENG_SECRET_KEY,
                    base_url="https://api.jimeng.ai/v1",
                    timeout=120.0,
                )
                provider_weights["jimeng"] = ProviderWeight(
                    provider_name="jimeng",
                    weight=0.8,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=60,
                )

            # DeepSeek（单密钥）
            if settings.DEEPSEEK_API_KEY:
                providers["deepseek"] = ProviderConfig(
                    name="deepseek",
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url="https://api.deepseek.com/v1",
                    timeout=120.0,
                )
                provider_weights["deepseek"] = ProviderWeight(
                    provider_name="deepseek",
                    weight=0.8,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=60,
                )

            # 火山引擎（Ark Seedream / 文本 & 图片）
            if settings.VOLCENGINE_API_KEY:
                providers["volcengine"] = ProviderConfig(
                    name="volcengine",
                    api_key=settings.VOLCENGINE_API_KEY,
                    api_secret=settings.VOLCENGINE_SECRET_KEY,
                    timeout=120.0,
                )
                provider_weights["volcengine"] = ProviderWeight(
                    provider_name="volcengine",
                    weight=0.7,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=50,
                )

            # Google Gemini / Vertex AI 文本模型
            if settings.GOOGLE_API_KEY:
                providers["google"] = ProviderConfig(
                    name="google",
                    api_key=settings.GOOGLE_API_KEY,
                    # 使用 Generative Language API (不是 Vertex AI)
                    base_url="https://generativelanguage.googleapis.com",
                    timeout=120.0,
                    default_model=settings.GOOGLE_DEFAULT_MODEL,
                )
                provider_weights["google"] = ProviderWeight(
                    provider_name="google",
                    weight=0.8,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=60,
                )

            # 如果没有配置任何provider，返回None
            if not providers:
                # self.logger.warning("警告: 没有配置任何AI服务提供商，将使用fallback模式")
                print("警告: 没有配置任何AI服务提供商，将使用fallback模式")
                return None

            # 创建AI服务配置
            config = AIServiceConfig(
                providers=providers,
                provider_weights=provider_weights,
                enable_fallback=True,
                enable_load_balancing=True,
                default_timeout=120.0,
                max_retries=3,
            )

            return AIServiceManager(config)
        except Exception as e:
            # self.logger.error(f"AI服务管理器初始化失败: {e}")
            print(f"AI服务管理器初始化失败: {e}")
            return None

    async def generate_story_outline(
        self,
        title: str,
        genre: str,
        characters: List[Dict[str, Any]],
        theme: Optional[str] = None,
        target_audience: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        setting_time: Optional[str] = None,
        setting_location: Optional[str] = None,
        world_building: Optional[str] = None,
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
        content_restrictions: Optional[List[str]] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        prefer_provider: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """生成故事概要"""

        # 使用提示词管理器渲染模板
        try:

            def _parse_story_json(payload: str | None) -> Optional[Dict[str, Any]]:
                try:
                    data = extract_json_block(payload)
                    if not data:
                        return None
                    StoryOutlineModel.model_validate(data)
                    return data
                except Exception:
                    return None

            variables = {
                "title": title,
                "genre": genre,
                "characters": characters,
                "theme": theme,
                "target_audience": target_audience,
                "duration_minutes": duration_minutes,
                "setting_time": setting_time,
                "setting_location": setting_location,
                "world_building": world_building,
                "additional_requirements": additional_requirements,
                "style_preferences": style_preferences or [],
                "content_restrictions": content_restrictions or [],
            }

            story_schema = StoryOutlineModel.model_json_schema()

            if self.story_agent:
                lg = await self.story_agent.generate(
                    title=title,
                    genre=genre,
                    characters=characters,
                    theme=theme,
                    target_audience=target_audience,
                    duration_minutes=duration_minutes,
                    setting_time=setting_time,
                    setting_location=setting_location,
                    world_building=world_building,
                    additional_requirements=additional_requirements,
                    style_preferences=style_preferences,
                    content_restrictions=content_restrictions,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                )
                if lg:
                    return lg

            prompt = prompt_manager.render_prompt(
                PromptTemplate.STORY_OUTLINE.value, variables
            )

            # 优先使用新的AI服务管理器；如果失败则尝试兜底。
            if self.ai_manager:
                try:
                    response = await self.ai_manager.generate_text(
                        prompt=prompt,
                        temperature=temperature,
                        model=model,
                        json_schema={"name": "story_outline", "schema": story_schema},
                        prefer_provider=prefer_provider,
                        system_prompt=prompt_manager.render_prompt(
                            PromptTemplate.SYSTEM_PROMPT_STORY.value, {}
                        ),
                    )

                    if isinstance(response.data, str):
                        content_text = response.data
                    elif response.data is not None:
                        content_text = str(response.data)
                    else:
                        content_text = ""
                    normalized = _parse_story_json(content_text)

                    if response.success:
                        if not normalized:
                            # 简单重试一次，提示严格JSON
                            retry_prompt = (
                                prompt + "\n\n请严格按JSON Schema返回，且只返回JSON，不要代码块。"
                            )
                            retry = await self.ai_manager.generate_text(
                                prompt=retry_prompt,
                                temperature=temperature,
                                model=model,
                                json_schema={
                                    "name": "story_outline",
                                    "schema": story_schema,
                                },
                                prefer_provider=prefer_provider,
                                system_prompt=prompt_manager.render_prompt(
                                    PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
                                ),
                            )
                            if retry.success:
                                content_text = (
                                    retry.data
                                    if isinstance(retry.data, str)
                                    else str(retry.data)
                                )
                                normalized = _parse_story_json(content_text)
                                provider_used = retry.provider
                                model_used = retry.model
                                usage = retry.usage
                            else:
                                provider_used = response.provider
                                model_used = response.model
                                usage = response.usage
                        else:
                            provider_used = response.provider
                            model_used = response.model
                            usage = response.usage

                        if content_text:
                            return {
                                "content": content_text,
                                "normalized": normalized,
                                "prompt": prompt,
                                "generation_method": f"ai_{provider_used}",
                                "template_used": PromptTemplate.STORY_OUTLINE.value,
                                "provider_used": provider_used,
                                "model_used": model_used,
                                "usage": usage,
                            }
                    else:
                        self.logger.warning(
                            "AI故事概要生成失败，将尝试回退",
                            extra={
                                "provider": response.provider,
                                "error": response.error or response.data,
                            },
                        )
                        if content_text:
                            return {
                                "content": content_text,
                                "normalized": normalized,
                                "prompt": prompt,
                                "generation_method": f"ai_{response.provider}_error",
                                "template_used": PromptTemplate.STORY_OUTLINE.value,
                                "provider_used": response.provider,
                                "model_used": response.model,
                                "usage": response.usage,
                            }
                except Exception as e:
                    self.logger.warning(f"AI服务管理器故事生成失败，尝试回退: {e}")

            # 兜底：使用文本生成服务链（最终会回退到mock）
            fallback_content = await self._call_text_generation_service(
                prompt, "story_outline"
            )
            if fallback_content:
                normalized = _parse_story_json(fallback_content)
                return {
                    "content": fallback_content,
                    "normalized": normalized,
                    "prompt": prompt,
                    "generation_method": "ai_fallback",
                    "template_used": PromptTemplate.STORY_OUTLINE.value,
                    "provider_used": "fallback",
                    "model_used": "mock",
                    "usage": {},
                }
        except Exception as e:
            print(f"故事概要生成失败: {e}")

        return None

    async def generate_episodes(
        self,
        story: Dict[str, Any],
        episode_count: int,
        episode_duration: Optional[int] = None,
        focus_characters: Optional[List[Dict[str, Any]]] = None,
        plot_complexity: str = "medium",
        pacing: str = "medium",
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """基于故事概要生成剧集"""
        # 优先尝试 LangGraph agent
        if self.episode_agent:
            try:
                lg_result = await self.episode_agent.generate(
                    story=story,
                    episode_count=episode_count,
                    episode_duration=episode_duration,
                    focus_characters=focus_characters,
                    plot_complexity=plot_complexity,
                    pacing=pacing,
                    additional_requirements=additional_requirements,
                    style_preferences=style_preferences,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                )
                if lg_result:
                    return lg_result
            except Exception as e:
                self.logger.warning(f"LangGraph episode agent failed: {e}")

        # 首先尝试使用AI服务管理器
        if self.ai_manager:
            try:
                direct_result = await self._call_ai_manager_episode(
                    story=story,
                    episode_count=episode_count,
                    episode_duration=episode_duration,
                    focus_characters=focus_characters,
                    plot_complexity=plot_complexity,
                    pacing=pacing,
                    additional_requirements=additional_requirements,
                    style_preferences=style_preferences,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                )
                if direct_result:
                    return direct_result
            except Exception as e:
                print(f"AI服务管理器剧集生成失败: {e}")

        # 如果AI服务管理器失败，尝试传统方法
        try:
            prompt = self._build_episode_generation_prompt(
                story,
                episode_count,
                episode_duration,
                focus_characters,
                plot_complexity,
                pacing,
                additional_requirements,
                style_preferences,
            )

            result = await self._call_text_generation_service(
                prompt, "episode_generation"
            )
            if result:
                return {
                    "content": result,
                    "prompt": prompt,
                    "generation_method": "ai_fallback",
                    "template_used": "manual_prompt",
                    "provider_used": "fallback",
                    "model_used": "unknown",
                    "usage": {},
                }
        except Exception as e:
            print(f"传统剧集生成方法失败: {e}")

        # 最终回退到模拟服务
        return await self._generate_mock_episodes(
            story, episode_count, episode_duration
        )

    async def _call_ai_manager_episode(
        self,
        *,
        story: Dict[str, Any],
        episode_count: int,
        episode_duration: Optional[int],
        focus_characters: Optional[List[Dict[str, Any]]],
        plot_complexity: str,
        pacing: str,
        additional_requirements: Optional[str],
        style_preferences: Optional[List[str]],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
    ) -> Optional[Dict[str, Any]]:
        """直接通过 AI 管理器生成剧集（带 JSON schema 校验）。"""
        if not self.ai_manager:
            return None

        variables = {
            "story": story,
            "episode_count": episode_count,
            "episode_duration": episode_duration,
            "focus_characters": focus_characters or [],
            "plot_complexity": plot_complexity,
            "pacing": pacing,
            "additional_requirements": additional_requirements,
            "style_preferences": style_preferences or [],
        }

        prompt = prompt_manager.render_prompt(
            PromptTemplate.EPISODE_GENERATION.value,
            variables,
        )

        plan_schema = EpisodePlanModel.model_json_schema()

        def _parse_episode_json(payload: str | None) -> Optional[Dict[str, Any]]:
            data = extract_json_block(payload)
            if not data:
                return None
            try:
                EpisodePlanModel.model_validate(data)
                return data
            except Exception:
                return None

        response = await self.ai_manager.generate_text(
            prompt=prompt,
            temperature=temperature,
            model=model,
            prefer_provider=prefer_provider,
            json_schema={"name": "episode_plan", "schema": plan_schema},
            system_prompt=prompt_manager.render_prompt(
                PromptTemplate.SYSTEM_PROMPT_SCRIPT.value, {}
            ),
        )

        if not response.success:
            return None

        content_text = (
            response.data if isinstance(response.data, str) else str(response.data)
        )
        normalized = _parse_episode_json(content_text)
        if not normalized:
            retry_prompt = prompt + "\n\n请严格按JSON Schema返回，且只返回JSON，不要代码块。"
            retry = await self.ai_manager.generate_text(
                prompt=retry_prompt,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                json_schema={"name": "episode_plan", "schema": plan_schema},
                system_prompt=prompt_manager.render_prompt(
                    PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
                ),
            )
            if not retry.success:
                return None
            content_text = (
                retry.data if isinstance(retry.data, str) else str(retry.data)
            )
            normalized = _parse_episode_json(content_text)
            provider_used = retry.provider
            model_used = retry.model
            usage = retry.usage
        else:
            provider_used = response.provider
            model_used = response.model
            usage = response.usage

        return {
            "content": content_text,
            "normalized": normalized,
            "prompt": prompt,
            "generation_method": f"ai_{provider_used}",
            "template_used": PromptTemplate.EPISODE_GENERATION.value,
            "provider_used": provider_used,
            "model_used": model_used,
            "usage": usage,
        }

    def _build_episode_generation_prompt(
        self,
        story,
        episode_count,
        episode_duration,
        focus_characters,
        plot_complexity,
        pacing,
        additional_requirements,
        style_preferences,
    ) -> str:
        """构建剧集生成提示词"""
        return prompt_manager.render_prompt(
            PromptTemplate.EPISODE_LIST.value,
            {
                "episode_count": episode_count,
                "story": story,
                "episode_duration": episode_duration,
                "focus_characters": focus_characters,
                "plot_complexity": plot_complexity,
                "pacing": pacing,
                "additional_requirements": additional_requirements,
            },
        )

    async def _generate_mock_episodes(
        self, story: Dict[str, Any], episode_count: int, episode_duration: Optional[int]
    ) -> Dict[str, Any]:
        """生成模拟剧集内容"""
        await asyncio.sleep(1)  # 模拟处理时间

        episodes = []
        story_title = story.get("title", "未命名故事")

        for i in range(episode_count):
            episode_num = i + 1
            episodes.append(
                {
                    "episode_number": episode_num,
                    "title": f"第{episode_num}集" if episode_num > 1 else "初始篇章",
                    "summary": f"这是{story_title}第{episode_num}集的内容概要。本集将继续推进故事发展，展现角色成长。",
                    "plot_points": [
                        {"description": f"第{episode_num}集开场情节", "timing": "开场"},
                        {"description": f"第{episode_num}集发展情节", "timing": "中段"},
                        {"description": f"第{episode_num}集结尾情节", "timing": "结尾"},
                    ],
                    "character_arcs": {"protagonist": f"第{episode_num}集的角色发展"},
                    "conflicts": [
                        {
                            "description": f"第{episode_num}集的主要冲突",
                            "intensity": "medium",
                        }
                    ],
                    "scene_count": 4 + (episode_num % 3),  # 4-6个场景
                    "scenes": [
                        {
                            "scene_number": 1,
                            "slug_line": f"INT. 主要场景 {episode_num} - DAY",
                            "location": "主要地点",
                            "time_of_day": "day",
                            "summary": "开场铺垫，呈现本集冲突或目标",
                        },
                        {
                            "scene_number": 2,
                            "slug_line": f"EXT. 发展场景 {episode_num} - DUSK",
                            "location": "次要地点",
                            "time_of_day": "dusk",
                            "summary": "推进矛盾或关系，加深角色动机",
                        },
                    ],
                }
            )

        content = json.dumps({"episodes": episodes}, ensure_ascii=False, indent=2)

        return {
            "content": content,
            "prompt": "模拟剧集生成提示词",
            "generation_method": "mock_service",
            "template_used": "mock_template",
            "provider_used": "mock",
            "model_used": "mock_model",
            "usage": {},
        }

    async def _generate_mock_script(
        self,
        episode: Dict[str, Any],
        story: Dict[str, Any],
        format_type: str,
        language: str,
        dialogue_style: str,
        scene_detail_level: str,
        additional_requirements: Optional[str],
        style_preferences: Optional[List[str]],
    ) -> Dict[str, Any]:
        """生成模拟剧本内容，保证无外部模型时的回退体验"""
        await asyncio.sleep(1)

        # 优先使用已生成的场景，保持与剧集一致；否则退回 plot_points
        base_scenes = episode.get("scenes") or []
        plot_points = episode.get("plot_points") or []
        if not base_scenes and not plot_points:
            summary = episode.get("summary") or story.get("synopsis") or "角色在本集中推进剧情。"
            plot_points = [{"description": summary, "timing": "中段"}]

        focus_characters: List[str] = []
        for char in story.get("main_characters") or []:
            name = char.get("name")
            if name and name not in focus_characters:
                focus_characters.append(name)
        focus_characters = focus_characters[:3]

        scenes: List[Dict[str, Any]] = []
        dialogues: List[Dict[str, Any]] = []
        stage_directions: List[Dict[str, Any]] = []
        script_sections: List[str] = [f"# {episode.get('title', '未命名剧集')}"]

        default_locations = ["教室", "校园花园", "图书馆", "操场"]
        default_times = ["DAY", "EVENING", "NIGHT"]

        # 若有真实场景，按场景生成；否则使用情节点生成
        if base_scenes:
            iterable = list(base_scenes)
        else:
            iterable = plot_points

        for idx, item in enumerate(iterable, start=1):
            if base_scenes:
                location = (
                    item.get("location")
                    or item.get("place")
                    or default_locations[(idx - 1) % len(default_locations)]
                )
                time_of_day = (
                    item.get("time_of_day")
                    or item.get("time")
                    or default_times[(idx - 1) % len(default_times)]
                )
                slug_line = item.get("slug_line") or f"INT. {location} - {time_of_day}"
                description = (
                    item.get("summary") or item.get("description") or f"场景 {idx}"
                )
                story_beat = item.get("story_beat") or item.get("timing") or "beat"
            else:
                location = default_locations[(idx - 1) % len(default_locations)]
                time_of_day = default_times[(idx - 1) % len(default_times)]
                slug_line = f"INT. {location.upper()} - {time_of_day}"
                description = item.get("description") or f"故事在第{idx}个阶段推进。"
                story_beat = item.get("timing") or "beat"

            scenes.append(
                {
                    "scene_number": idx,
                    "slug_line": slug_line,
                    "summary": description,
                    "description": description,
                    "focus_characters": focus_characters,
                    "story_beat": story_beat,
                    "location": location,
                    "time_of_day": time_of_day,
                }
            )

            dialogues.append(
                {
                    "scene_number": idx,
                    "character": focus_characters[0] if focus_characters else "旁白",
                    "content": f"（{dialogue_style}）我们正在面对：{description}",
                }
            )

            stage_directions.append(
                {
                    "scene_number": idx,
                    "content": f"镜头捕捉角色与场景，突出：{description}",
                    "camera_suggestion": "中景",
                    "lighting": "自然光",
                }
            )

            section_lines = [
                f"场景 {idx}: {location} - {time_of_day}",
                description,
                "",
            ]
            for dialog in [d for d in dialogues if d["scene_number"] == idx]:
                line_text = dialog.get("content") or dialog.get("line") or ""
                section_lines.append(f"{dialog.get('character', '旁白')}: {line_text}")
            script_sections.append("\n".join(section_lines))

        if additional_requirements:
            script_sections.append(f"\n【制作要求】{additional_requirements}")

        script_text = "\n\n".join(script_sections)

        return {
            "content": {
                "content": script_text,
                "scenes": scenes,
                "dialogues": dialogues,
                "stage_directions": stage_directions,
                "metadata": {
                    "story_title": story.get("title"),
                    "episode_title": episode.get("title"),
                    "generator": "mock_script",
                    "language": language,
                    "format_type": format_type,
                    "scene_detail_level": scene_detail_level,
                    "style_preferences": style_preferences or [],
                },
            },
            "prompt": "模拟剧本生成提示词",
            "generation_method": "mock_service",
            "template_used": "mock_script_template",
            "provider_used": "mock",
            "model_used": "mock_script_model",
            "usage": {},
        }

    async def generate_script(
        self,
        episode: Dict[str, Any],
        story: Dict[str, Any],
        format_type: str = "screenplay",
        language: str = "zh-CN",
        dialogue_style: str = "natural",
        scene_detail_level: str = "medium",
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """基于剧集信息生成详细剧本"""
        # 1) LangGraph agent
        if self.script_agent:
            try:
                lg = await self.script_agent.generate(
                    episode=episode,
                    story=story,
                    format_type=format_type,
                    language=language,
                    dialogue_style=dialogue_style,
                    scene_detail_level=scene_detail_level,
                    additional_requirements=additional_requirements,
                    style_preferences=style_preferences,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                )
                if lg and lg.get("content"):
                    # 组装 content 文本
                    assembled = self._build_script_text(
                        lg["content"].get("scenes") or [],
                        lg["content"].get("dialogues") or [],
                        lg["content"].get("stage_directions") or [],
                        format_type=format_type,
                        language=language,
                    )
                    lg["content"]["content"] = assembled
                    return lg
            except Exception as e:
                self.logger.warning(f"LangGraph script agent failed: {e}")

        # 2) AI 管理器直接生成
        direct = await self._call_ai_manager_script(
            episode=episode,
            story=story,
            format_type=format_type,
            language=language,
            dialogue_style=dialogue_style,
            scene_detail_level=scene_detail_level,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences,
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
        )
        if direct:
            # 尝试解析填充 content 以便前端展示
            parsed = direct.get("normalized") if isinstance(direct, dict) else None
            if not parsed:
                raw_content = (
                    direct.get("content") if isinstance(direct, dict) else None
                )
                if isinstance(raw_content, dict):
                    parsed = raw_content
                elif isinstance(raw_content, str):
                    parsed = extract_json_block(raw_content)

            if isinstance(parsed, dict):
                assembled = self._build_script_text(
                    parsed.get("scenes") or [],
                    parsed.get("dialogues") or [],
                    parsed.get("stage_directions") or [],
                    format_type=format_type,
                    language=language,
                )
                parsed["content"] = assembled
                direct["content"] = parsed
                direct["normalized"] = parsed
            return direct

        # 3) Mock 回退
        return await self._generate_mock_script(
            episode=episode,
            story=story,
            format_type=format_type,
            language=language,
            dialogue_style=dialogue_style,
            scene_detail_level=scene_detail_level,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences,
        )

    async def _call_ai_manager_script(
        self,
        *,
        episode: Dict[str, Any],
        story: Dict[str, Any],
        format_type: str,
        language: str,
        dialogue_style: str,
        scene_detail_level: str,
        additional_requirements: Optional[str],
        style_preferences: Optional[List[str]],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
    ) -> Optional[Dict[str, Any]]:
        """AI 管理器直接生成剧本的兜底实现（结构化 JSON）。"""
        if not self.ai_manager:
            return None

        scenes = episode.get("scenes") or []
        prompt = prompt_manager.render_prompt(
            PromptTemplate.SCRIPT_DIALOGUES.value,
            {
                "episode": episode,
                "story": story,
                "scenes": scenes,
                "dialogue_style": dialogue_style,
                "language": language,
                "format_type": format_type,
            },
        )
        response = await self.ai_manager.generate_text(
            prompt=prompt,
            temperature=temperature,
            model=model,
            prefer_provider=prefer_provider,
            json_schema={
                "name": "script_dialogues",
                "schema": {
                    "type": "object",
                    "properties": {
                        "dialogues": {"type": "array"},
                        "stage_directions": {"type": "array"},
                        "scenes": {"type": "array"},
                    },
                },
            },
            system_prompt="你是专业的剧本对白与舞台指示写手，请严格按 JSON 返回。",
        )
        if not response.success:
            return None

        raw = response.data if isinstance(response.data, str) else str(response.data)
        parsed = extract_json_block(raw)
        if not parsed:
            return None

        script_scenes = (
            parsed.get("scenes")
            if isinstance(parsed, dict) and isinstance(parsed.get("scenes"), list)
            else scenes
        )
        dialogues = (
            parsed.get("dialogues")
            if isinstance(parsed, dict) and isinstance(parsed.get("dialogues"), list)
            else []
        )
        stage_dir = (
            parsed.get("stage_directions")
            if isinstance(parsed, dict)
            and isinstance(parsed.get("stage_directions"), list)
            else []
        )

        payload = {
            "content": "",
            "scenes": script_scenes,
            "dialogues": dialogues,
            "stage_directions": stage_dir,
            "metadata": {
                "story_title": story.get("title"),
                "episode_title": episode.get("title"),
                "generator": f"ai_manager:{response.provider}",
                "language": language,
                "format_type": format_type,
                "scene_detail_level": scene_detail_level,
                "style_preferences": style_preferences or [],
            },
        }

        payload["content"] = self._build_script_text(
            payload.get("scenes") or [],
            payload.get("dialogues") or [],
            payload.get("stage_directions") or [],
            format_type=format_type,
            language=language,
        )

        return {
            "content": payload,
            "normalized": payload,
            "prompt": prompt,
            "generation_method": f"ai_manager_{response.provider}",
            "template_used": "script_dialogues",
            "provider_used": response.provider,
            "model_used": response.model,
            "usage": response.usage,
        }

    def _build_script_text(
        self,
        scenes: List[Dict[str, Any]],
        dialogues: List[Dict[str, Any]],
        stage_directions: List[Dict[str, Any]],
        format_type: str,
        language: str,
    ) -> str:
        """简单拼装剧本文本，便于前端展示；真实文本可后续细化。"""
        lines: List[str] = [f"# {format_type} ({language})"]
        if scenes:
            lines.append("## 场景")
            for sc in scenes:
                slug = sc.get("slug_line") or f"Scene {sc.get('scene_number')}"
                summary = sc.get("summary") or sc.get("description") or ""
                lines.append(f"- {slug}: {summary}")
        if dialogues:
            lines.append("\n## 对白")
            for dlg in dialogues[:200]:
                scene_no = dlg.get("scene_number") or "-"
                char = dlg.get("character") or "旁白"
                content = dlg.get("content") or dlg.get("line") or dlg.get("text") or ""
                lines.append(f"[场景 {scene_no}] {char}: {content}")
        if stage_directions:
            lines.append("\n## 舞台指示")
            for sd in stage_directions[:200]:
                scene_no = sd.get("scene_number") or "-"
                content = (
                    sd.get("content")
                    or sd.get("direction")
                    or sd.get("description")
                    or ""
                )
                timing = sd.get("timing") or ""
                lines.append(f"[场景 {scene_no}][{timing}] {content}")
        return "\n".join(lines)

    async def _call_text_generation_service(
        self, prompt: str, task_type: str
    ) -> Optional[str]:
        """调用文本生成服务"""

        # 尝试不同的AI服务
        services = [
            self._generate_with_openai_gpt,
            self._generate_with_custom_service,
            self._generate_with_mock_service,  # 添加模拟服务作为后备
        ]

        for service in services:
            try:
                result = await service(prompt, task_type)
                if result:
                    return result
            except Exception as e:
                print(f"服务 {service.__name__} 失败: {e}")
                continue

        return None

    async def generate_storyboard(
        self,
        script: Dict[str, Any],
        style_preferences: Optional[List[str]] = None,
        additional_requirements: Optional[str] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
        frames_per_scene: int = 3,
        max_frames: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """基于剧本信息生成分镜（Storyboard）"""
        if self.ai_manager:
            try:
                variables = {
                    "script": script,
                    "style_preferences": style_preferences or [],
                    "additional_requirements": additional_requirements or "",
                }
                # 构造更强提示词，包含故事/剧集上下文与场景角色信息
                context = {
                    "story": (script or {}).get("story"),
                    "episode": (script or {}).get("episode"),
                    "scenes_count": len((script or {}).get("scenes") or []),
                }
                context_text = _build_storyboard_context(script)
                prompt = (
                    "你是具备导演、摄影与美术能力的专业分镜师。请采用 ReAct 思考流程：先在内心推理每个场景应该呈现的节奏与视觉差异，再输出最终JSON。\n"
                    "必须遵循：\n"
                    f"- 每个场景生成约 {frames_per_scene} 个分镜，保证镜头间明显差异（景别/运镜/构图/叙事重点不得重复）\n"
                    f"- 总数不超过 {max_frames if max_frames else '合理范围'}\n"
                    "- 每个分镜必须包含且不为空：scene_number, shot_type, camera_movement, composition, description, duration_seconds, ai_prompt\n"
                    "- shot_type 需覆盖远景/中景/近景/特写等不同镜别，避免同一场景内重复\n"
                    "- camera_movement 应在固定/推/拉/摇/移/跟/变焦等之间切换，体现叙事意图\n"
                    "- composition 要在三分法/对称/前后景/对角线/中心对称等方案中选择，突出叙事重点\n"
                    "- description 要结合人物/动作/情绪/光线，避免模糊词语；ai_prompt 需补充画面细节与风格关键词，与 description 保持互补\n"
                    '- 仅输出严格JSON：{"frames":[...]}，禁止额外文本或思维过程\n\n'
                    "请在内部完成推理后再给出JSON结果，保证每条记录独特且自洽。\n"
                    f"剧作上下文：\n{context_text}\n"
                )
                schema = StoryboardModel.model_json_schema()
                response = await self.ai_manager.generate_text(
                    prompt=prompt,
                    temperature=temperature,
                    model=model,
                    prefer_provider=prefer_provider,
                    json_schema={"name": "storyboard", "schema": schema},
                    system_prompt="返回内容必须是严格的JSON，符合给定的Schema。",
                )
                if response.success:
                    content_text = (
                        response.data
                        if isinstance(response.data, str)
                        else str(response.data)
                    )
                    normalized = extract_json_block(content_text)
                    if normalized:
                        try:
                            StoryboardModel.model_validate(normalized)
                        except Exception:
                            normalized = None
                    if not normalized:
                        retry = await self.ai_manager.generate_text(
                            prompt=prompt + "\n\n只返回JSON，不要任何多余文本。",
                            temperature=temperature,
                            model=model,
                            prefer_provider=prefer_provider,
                            json_schema={"name": "storyboard", "schema": schema},
                            system_prompt="返回内容必须是严格的JSON，符合给定的Schema。",
                        )
                        if retry.success:
                            content_text = (
                                retry.data
                                if isinstance(retry.data, str)
                                else str(retry.data)
                            )
                            normalized = extract_json_block(content_text)
                            if normalized:
                                try:
                                    StoryboardModel.model_validate(normalized)
                                except Exception:
                                    normalized = None
                    return {
                        "content": content_text,
                        "normalized": normalized,
                        "prompt": prompt,
                        "generation_method": f"ai_{response.provider}",
                        "template_used": "storyboard_generation",
                        "provider_used": response.provider,
                        "model_used": response.model,
                        "usage": response.usage,
                    }
            except Exception as e:
                print(f"分镜生成失败: {e}")
        return None

    async def generate_storyboard_plan(
        self,
        script: Dict[str, Any],
        frames_per_scene: int = 7,
        selected_scenes: Optional[List[int]] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Optional[Dict[str, Any]]:
        """先生成分镜规划：每个场景的帧数与每帧的镜别/运镜/构图/意图。"""
        if not self.ai_manager:
            return None
        try:
            scenes = (script or {}).get("scenes") or []
            target_scenes = selected_scenes or list(range(1, len(scenes) + 1))
            context = {
                "story": (script or {}).get("story"),
                "episode": (script or {}).get("episode"),
                "scenes_count": len(scenes),
                "selected_scenes": target_scenes,
            }
            prompt = (
                "你是专业分镜导演。请采用 ReAct 风格在心中完成推理，最终只输出JSON。\n"
                "步骤：首先构思每个场景的节奏与冲突，再给出多样化的镜头规划。\n"
                '必须返回严格JSON：{"scenes":[{"scene_number":int,"target_frames":int,"frames":[{"shot_type":str,"camera_movement":str,"composition":str,"intent":str}...]}...]}。\n'
                "要求：shot_type 覆盖远景/中景/近景/特写；camera_movement 在固定/推/拉/摇/移/跟/变焦中多样化；composition 在三分法/对称/前后景/对角线/中心对称中选择；intent 需说明情绪或叙事作用。\n"
                f"每个选定场景 target_frames={frames_per_scene}，不足也尽量给足，禁止镜头意图重复。\n"
                f"上下文（截断）：{json.dumps(context, ensure_ascii=False)[:1200]}\n"
                f"剧本（截断）：{json.dumps(script, ensure_ascii=False)[:2500]}"
            )
            schema = StoryboardPlanModel.model_json_schema()
            response = await self.ai_manager.generate_text(
                prompt=prompt,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                json_schema={"name": "storyboard_plan", "schema": schema},
                system_prompt="只返回严格JSON，符合给定的Schema",
            )
            if response.success:
                content_text = (
                    response.data
                    if isinstance(response.data, str)
                    else str(response.data)
                )
                data = extract_json_block(content_text)
                if not data:
                    return None
                try:
                    StoryboardPlanModel.model_validate(data)
                except Exception:
                    return None
                return {
                    "content": content_text,
                    "normalized": data,
                    "provider_used": response.provider,
                    "model_used": response.model,
                    "usage": response.usage,
                }
        except Exception as e:
            print(f"分镜规划生成失败: {e}")
        return None

    async def generate_storyboard_from_plan_for_scene(
        self,
        script: Dict[str, Any],
        scene_plan: StoryboardPlanScene,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
        max_frames: Optional[int] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """根据某一场景的规划，细化生成该场景的分镜帧（一次一场景）。"""
        if not self.ai_manager:
            return None
        try:
            script_brief = {
                "story": (script or {}).get("story"),
                "episode": (script or {}).get("episode"),
                "scene": (
                    (script or {}).get("scenes")[scene_plan.scene_number - 1]
                    if (script or {}).get("scenes")
                    and 0 < scene_plan.scene_number <= len((script or {}).get("scenes"))
                    else None
                ),
            }
            prompt = (
                "你是专业分镜师。请先在心中分析规划中每条镜头的差异化表达，再生成最终分镜帧列表。\n"
                '必须返回严格JSON：{"frames":[{scene_number, shot_type, camera_movement, composition, description, duration_seconds, ai_prompt, reference_images}...]}。\n'
                "字段要求与取值范围同前，且 description、shot_type、camera_movement、composition 在同一场景内要有明显差异；duration_seconds 取 2–12 之间并根据节奏适度变化。\n"
                "ai_prompt 需要补充画面细节、光线、情绪、材质等元素，避免与 description 完全重复。\n"
                f"规划（仅此场景）：{json.dumps(scene_plan.dict(), ensure_ascii=False)}\n"
                f"上下文（截断）：{json.dumps(script_brief, ensure_ascii=False)[:1500]}\n"
                f"若有 max_frames 限制，总数不超过 {max_frames if max_frames else '合理范围'}。"
            )
            schema = StoryboardModel.model_json_schema()
            response = await self.ai_manager.generate_text(
                prompt=prompt,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                json_schema={"name": "storyboard", "schema": schema},
                system_prompt="只返回严格JSON，符合Schema。",
            )
            if response.success:
                content_text = (
                    response.data
                    if isinstance(response.data, str)
                    else str(response.data)
                )
                data = extract_json_block(content_text)
                if not data:
                    return None
                try:
                    StoryboardModel.model_validate(data)
                except Exception:
                    return None
                frames = data.get("frames") or []
                # 统一 scene_number
                for fr in frames:
                    fr["scene_number"] = scene_plan.scene_number
                return frames
        except Exception as e:
            print(f"基于规划生成分镜失败: {e}")
        return None

    async def _generate_with_openai_gpt(
        self, prompt: str, task_type: str
    ) -> Optional[str]:
        """使用OpenAI GPT生成文本"""
        if not self.openai_api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {
                                "role": "system",
                                "content": prompt_manager.render_prompt(
                                    PromptTemplate.SYSTEM_PROMPT_STORY.value, {}
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                    },
                    timeout=120.0,
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI GPT生成失败: {e}")
            return None

    async def _generate_with_custom_service(
        self, prompt: str, task_type: str
    ) -> Optional[str]:
        """使用自定义文本生成服务"""
        if not self.base_url or not self.api_key:
            return None

        payload = {
            "prompt": prompt,
            "task_type": task_type,
            "parameters": {"temperature": 0.7, "format": "json"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate-text",
                    json=payload,
                    headers=headers,
                    timeout=120.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("text")
        except Exception as e:
            print(f"自定义文本生成服务失败: {e}")
            return None

    async def _generate_with_mock_service(
        self, prompt: str, task_type: str
    ) -> Optional[str]:
        """模拟AI服务（用于测试和演示）"""
        await asyncio.sleep(1)  # 模拟处理时间

        if task_type == "story_outline":
            return """{
                "premise": "这是一个关于友情与成长的现代都市故事。",
                "synopsis": "主人公们在面临生活挑战时，通过相互支持和理解，最终实现了个人成长和友谊的升华。故事通过日常生活中的小事件，展现了现代年轻人的生活态度和价值观。",
                "main_conflict": "主人公面临职业选择和人际关系的双重困扰，需要在理想与现实之间找到平衡。",
                "resolution": "通过朋友们的帮助和自我反思，主人公找到了适合自己的道路，同时加深了与朋友们的友谊。",
                "character_relationships": {
                    "protagonist_friend": "深厚的友谊，相互支持",
                    "group_dynamics": "团结互助的友好关系"
                },
                "main_characters": [
                    {
                        "name": "主人公A",
                        "role": "protagonist",
                        "description": "积极向上的年轻人"
                    },
                    {
                        "name": "主人公B", 
                        "role": "supporting",
                        "description": "智慧可靠的朋友"
                    }
                ]
            }"""
        elif task_type == "episode_generation":
            return """{
                "episodes": [
                    {
                        "episode_number": 1,
                        "title": "新的开始",
                        "summary": "介绍主要角色和背景设定",
                        "plot_points": [
                            {"description": "角色出场", "timing": "开场"},
                            {"description": "背景介绍", "timing": "前10分钟"},
                            {"description": "冲突铺垫", "timing": "中段"}
                        ],
                        "character_arcs": {"protagonist": "初始状态展示"},
                        "conflicts": [
                            {"description": "内心困扰的初步展现", "intensity": "low"}
                        ],
                        "scene_count": 5
                    }
                ]
            }"""
        elif task_type == "script_generation":
            return """{
                "content": "FADE IN:\\n\\nINT. 客厅 - 日\\n\\n主人公坐在沙发上，思考着什么...\\n\\n主人公\\n（自言自语）\\n今天又是新的一天呢。\\n\\nFADE OUT.",
                "scenes": [
                    {"scene_number": 1, "location": "客厅", "time": "日", "description": "主人公独自思考"}
                ],
                "dialogues": [
                    {"character": "主人公", "content": "今天又是新的一天呢。", "emotion": "thoughtful"}
                ],
                "stage_directions": ["主人公坐在沙发上，思考着什么"]
            }"""

        return "这是一个模拟的AI生成内容，用于测试和演示目的。"

    # 保持原有的图像生成功能
    async def generate_virtual_ip_image(
        self,
        ip_name: str,
        description: str,
        style: str = "realistic",
        category: str = "portrait",
        model: str = "dalle-3",
        additional_prompts: List[str] = None,
        background_story: str = None,
        count: int = 1,
        size: str | None = None,
    ) -> Optional[Dict[str, Any]]:
        """为虚拟IP生成图像"""

        raw_model = model or "dalle-3"
        provider_hint: str | None = None
        pure_model = raw_model
        if ":" in raw_model:
            parts = raw_model.split(":", 1)
            if len(parts) == 2 and parts[0] and parts[1]:
                provider_hint, pure_model = parts[0], parts[1]

        # 使用提示词管理器生成专业提示词
        try:
            variables = {
                "character_name": ip_name,
                "character_description": description,
                "background_story": background_story,
                "style": style,
                "category": category,
                "additional_prompts": additional_prompts or [],
                "is_default": category == "portrait",
            }

            # 生成AI图像提示词
            prompt_result = prompt_manager.render_prompt(
                PromptTemplate.IMAGE_GENERATION.value, variables
            )

            # 使用简单的提示词，避免复杂的AI管理器调用
            if category == "portrait":
                final_prompt = f"A professional {style} portrait of {ip_name}, {description}"
            else:
                final_prompt = f"A professional {style} {category} of {ip_name}, {description}"
            if additional_prompts:
                final_prompt += f", {', '.join(additional_prompts)}"

            self.logger.info(f"生成图像提示词: {final_prompt[:200]}...")
            self.logger.info(
                "使用模型: %s (provider_hint=%s), 风格: %s, 类别: %s",
                pure_model,
                provider_hint,
                style,
                category,
            )

            # 根据模型选择不同的AI服务
            provider_used = "openai"
            generation_method = "openai_dalle"
            image_url = None

            normalized_model = pure_model.lower()
            if (
                normalized_model.startswith("keling-")
                or normalized_model.startswith("kling-")
                or normalized_model in {"keling", "kling"}
            ):
                # 使用可灵AI生成图像
                image_url = await self._generate_with_keling_image(
                    final_prompt, style, category, pure_model
                )
                provider_used = "keling"
                generation_method = "keling_image"
            elif normalized_model.startswith("dall-e") or normalized_model.startswith(
                "dalle"
            ):
                # 使用 OpenAI DALL-E 直连 API，并支持按官方 size 选项控制分辨率
                image_url = await self._generate_with_openai_dalle(
                    final_prompt,
                    style,
                    category,
                    size=size or "1024x1024",
                )
                provider_used = "openai"
                generation_method = "openai_dalle"
            elif self.ai_manager:
                # 使用AI管理器的其他服务（根据模型名偏向特定提供商）
                prefer_provider = provider_hint
                if normalized_model.startswith(
                    "seedream"
                ) or normalized_model.startswith("volcengine"):
                    prefer_provider = "volcengine"
                elif normalized_model.startswith("deepseek"):
                    prefer_provider = "deepseek"
                elif normalized_model.startswith("google"):
                    prefer_provider = "google"
                response = await self.ai_manager.generate_image(
                    prompt=final_prompt,
                    width=1024,
                    height=1024,
                    style=style,
                    model=pure_model,
                    n=count or 1,
                    prefer_provider=prefer_provider,
                    # 对火山 Ark Seedream，size 由 VolcengineProvider 映射为 Ark 的 size 字段（例如 \"2K\"）
                    size=size if prefer_provider == "volcengine" else None,
                )
                if response.success:
                    images = response.data.get("images", [])
                    image_url = images[0] if images else None
                    provider_used = response.provider or provider_used
                    generation_method = f"ai_{provider_used}"
                else:
                    self.logger.error(f"AI管理器图像生成失败: {response.error}")
                    image_url = None
            else:
                # 默认使用OpenAI DALL-E（保持向后兼容）
                image_url = await self._generate_with_openai_dalle(
                    final_prompt, style, category
                )
                provider_used = "openai"
                generation_method = "openai_dalle"

            if image_url:
                try:
                    stored = await self._persist_generated_image(
                        image_url,
                        ip_name=ip_name,
                        category=category,
                        prefix="ai-generated/virtual-ip",
                        metadata={
                            "ip_name": ip_name,
                            "style": style,
                            "category": category,
                            "provider": provider_used,
                            "model": model,
                        },
                    )
                except Exception as exc:
                    self.logger.error(f"图像保存/上传失败: {exc}")
                    return None

                final_image_url = stored.get("oss_url") or stored.get("relative_path")

                return {
                    "image_url": final_image_url,
                    "oss_url": stored.get("oss_url"),
                    "local_file_path": stored.get("local_file_path"),
                    "relative_path": stored.get("relative_path"),
                    "original_image_url": image_url,
                    "oss_upload": stored.get("oss_upload"),
                    "prompt": final_prompt,
                    "style": style,
                    "category": category,
                    "generation_method": generation_method,
                    "template_used": PromptTemplate.IMAGE_GENERATION.value,
                    "provider_used": provider_used,
                    "model_used": model,
                    "usage": {},
                }

        except Exception as e:
            print(f"图像生成失败: {e}")

        return None

    async def _download_image(
        self, image_data: str, ip_name: str, category: str
    ) -> Optional[str]:
        """处理图像数据（URL或base64）并保存到本地"""
        import os
        import uuid
        import aiofiles
        import base64

        try:
            # 生成唯一文件名
            file_extension = ".png"  # OpenAI DALL-E默认返回PNG
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"

            # 确保目录存在
            upload_dir = settings.UPLOAD_DIR
            os.makedirs(upload_dir, exist_ok=True)

            local_file_path = os.path.join(upload_dir, unique_filename)

            # 判断是base64数据还是URL
            if image_data.startswith("data:image"):
                # 处理base64数据
                self.logger.info("处理base64图像数据")
                base64_data = image_data.split(",")[1]  # 移除data:image/png;base64,前缀
                image_bytes = base64.b64decode(base64_data)

                # 直接保存base64数据
                async with aiofiles.open(local_file_path, "wb") as f:
                    await f.write(image_bytes)
            else:
                # 处理URL（之前的逻辑）
                self.logger.info(f"下载图像URL: {image_data[:100]}...")
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_data, timeout=60.0)
                    response.raise_for_status()

                    # 保存到本地文件
                    async with aiofiles.open(local_file_path, "wb") as f:
                        await f.write(response.content)

            self.logger.info(f"图像已保存到: {local_file_path}")
            return local_file_path

        except Exception as e:
            self.logger.error(f"图像处理失败: {e}")
            return None

    async def _upload_local_image_to_oss(
        self,
        local_file_path: str,
        *,
        prefix: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """将本地已下载的图片上传至 OSS，失败则抛出异常。"""
        if not oss_service:
            raise RuntimeError("OSS 服务未配置，无法上传图像")

        try:
            with open(local_file_path, "rb") as f:
                file_content = f.read()
        except Exception as exc:  # pragma: no cover - IO guard
            raise RuntimeError(f"读取本地图像失败: {exc}") from exc

        filename = os.path.basename(local_file_path)
        oss_result = await oss_service.upload_file_content(
            file_content=file_content,
            filename=filename,
            file_type="image",
            prefix=prefix,
            metadata=metadata,
        )
        if not oss_result or not oss_result.get("success"):
            raise RuntimeError(f"OSS 上传失败: {oss_result}")
        return oss_result

    async def _persist_generated_image(
        self,
        image_data: str,
        *,
        ip_name: str,
        category: str,
        prefix: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """下载/保存生成图像，并在配置 OSS 时上传，返回路径与元数据。"""
        local_file_path = await self._download_image(image_data, ip_name, category)
        if not local_file_path:
            raise RuntimeError("图像下载失败")

        file_size = os.path.getsize(local_file_path)
        filename = os.path.basename(local_file_path)
        relative_path = f"/uploads/{filename}"

        oss_result = None
        oss_url = None
        if oss_service:
            oss_result = await self._upload_local_image_to_oss(
                local_file_path,
                prefix=prefix,
                metadata=metadata or {},
            )
            oss_url = oss_result.get("file_url")

        return {
            "local_file_path": local_file_path,
            "relative_path": relative_path,
            "file_size": file_size,
            "filename": filename,
            "oss_url": oss_url,
            "oss_upload": oss_result,
        }

    async def generate_video(
        self,
        prompt: str = None,
        image_url: str = None,
        duration: int = 5,
        fps: int = 24,
        resolution: str = "1280x720",
        style: str = "realistic",
        prefer_provider: str = None,
    ) -> Optional[Dict[str, Any]]:
        """生成视频"""
        try:
            response = await self.ai_manager.generate_video(
                prompt=prompt,
                image_url=image_url,
                duration=duration,
                fps=fps,
                resolution=resolution,
                prefer_provider=prefer_provider,
            )

            if response.success:
                original_video_url = response.data.get("video_url")
                original_thumbnail_url = response.data.get("thumbnail_url")

                # 自动上传视频到OSS
                video_oss_result = None
                thumbnail_oss_result = None

                if original_video_url and oss_service:
                    try:
                        video_oss_result = await oss_service.upload_from_url(
                            url=original_video_url,
                            file_type="video",
                            prefix="ai-generated/videos",
                            metadata={
                                "prompt": prompt or "image_to_video",
                                "duration": str(duration),
                                "fps": str(fps),
                                "resolution": resolution,
                                "provider": response.provider,
                                "model": response.model,
                                "generation_time": datetime.now().isoformat(),
                            },
                        )
                    except Exception as e:
                        print(f"视频OSS上传失败: {e}")

                if original_thumbnail_url and oss_service:
                    try:
                        thumbnail_oss_result = await oss_service.upload_from_url(
                            url=original_thumbnail_url,
                            file_type="image",
                            prefix="ai-generated/thumbnails",
                            metadata={
                                "type": "video_thumbnail",
                                "prompt": prompt or "image_to_video",
                                "provider": response.provider,
                                "generation_time": datetime.now().isoformat(),
                            },
                        )
                    except Exception as e:
                        print(f"缩略图OSS上传失败: {e}")

                return {
                    "video_url": (
                        video_oss_result.get("file_url")
                        if video_oss_result and video_oss_result.get("success")
                        else original_video_url
                    ),
                    "thumbnail_url": (
                        thumbnail_oss_result.get("file_url")
                        if thumbnail_oss_result and thumbnail_oss_result.get("success")
                        else original_thumbnail_url
                    ),
                    "original_video_url": original_video_url,
                    "original_thumbnail_url": original_thumbnail_url,
                    "video_oss_upload": video_oss_result,
                    "thumbnail_oss_upload": thumbnail_oss_result,
                    "duration": response.data.get("duration", duration),
                    "prompt": prompt,
                    "image_url": image_url,
                    "generation_method": f"ai_{response.provider}",
                    "provider_used": response.provider,
                    "model_used": response.model,
                    "metadata": response.metadata,
                }
        except Exception as e:
            print(f"视频生成失败: {e}")

        return None

    async def generate_speech(
        self,
        text: str,
        voice_type: str = None,
        speed: float = 1.0,
        prefer_provider: str = None,
    ) -> Optional[Dict[str, Any]]:
        """生成语音"""
        try:
            response = await self.ai_manager.text_to_speech(
                text=text,
                voice_type=voice_type,
                speed=speed,
                prefer_provider=prefer_provider,
            )

            if response.success:
                original_audio_url = response.data.get("audio_url")

                # 自动上传音频到OSS
                audio_oss_result = None
                if original_audio_url and oss_service:
                    try:
                        audio_oss_result = await oss_service.upload_from_url(
                            url=original_audio_url,
                            file_type="audio",
                            prefix="ai-generated/audio",
                            metadata={
                                "text": (
                                    text[:100] + "..." if len(text) > 100 else text
                                ),  # 限制长度
                                "voice_type": voice_type or "default",
                                "speed": str(speed),
                                "provider": response.provider,
                                "model": response.model,
                                "generation_time": datetime.now().isoformat(),
                            },
                        )
                    except Exception as e:
                        print(f"音频OSS上传失败: {e}")

                return {
                    "audio_url": (
                        audio_oss_result.get("file_url")
                        if audio_oss_result and audio_oss_result.get("success")
                        else original_audio_url
                    ),
                    "original_audio_url": original_audio_url,
                    "audio_oss_upload": audio_oss_result,
                    "duration": response.data.get("duration"),
                    "text": text,
                    "voice_type": voice_type,
                    "speed": speed,
                    "generation_method": f"ai_{response.provider}",
                    "provider_used": response.provider,
                    "model_used": response.model,
                    "metadata": response.metadata,
                }
        except Exception as e:
            print(f"语音生成失败: {e}")

        return None

    def get_ai_providers_status(self) -> Dict[str, Any]:
        """获取AI提供商状态"""
        if not self.ai_manager:
            return {}
        return self.ai_manager.get_provider_status()

    async def list_models(
        self,
        model_type_alias: Optional[str] = None,
        source: str = "auto",
    ) -> List[Dict[str, Any]]:
        """
        统一列出模型，支持按类型和来源过滤。

        model_type_alias:
          - 'text' / 'text_generation'
          - 'image' / 'text_to_image'
          - 'video' / 'text_to_video'
          - 'tts' / 'text_to_speech'
        source:
          - 'static' | 'remote' | 'auto'
        """
        if not self.ai_manager:
            return []

        aliases = {
            "text": AIModelType.TEXT_GENERATION,
            "text_generation": AIModelType.TEXT_GENERATION,
            "image": AIModelType.TEXT_TO_IMAGE,
            "text_to_image": AIModelType.TEXT_TO_IMAGE,
            "image_to_image": AIModelType.IMAGE_TO_IMAGE,
            "img2img": AIModelType.IMAGE_TO_IMAGE,
            "video": AIModelType.TEXT_TO_VIDEO,
            "text_to_video": AIModelType.TEXT_TO_VIDEO,
            "tts": AIModelType.TEXT_TO_SPEECH,
            "text_to_speech": AIModelType.TEXT_TO_SPEECH,
        }
        mt = aliases.get(model_type_alias, None)
        return await self.ai_manager.list_models(model_type=mt, source=source)

    def update_provider_config(
        self,
        provider_name: str,
        enabled: bool = None,
        weight: float = None,
        priority: str = None,
        max_requests_per_minute: int = None,
    ):
        """更新提供商配置"""
        priority_enum = None
        if priority:
            priority_map = {
                "high": ProviderPriority.HIGH,
                "medium": ProviderPriority.MEDIUM,
                "low": ProviderPriority.LOW,
            }
            priority_enum = priority_map.get(priority.lower())

        self.ai_manager.update_provider_config(
            provider_name=provider_name,
            enabled=enabled,
            weight=weight,
            priority=priority_enum,
            max_requests_per_minute=max_requests_per_minute,
        )

    async def _generate_with_keling_image(
        self, prompt: str, style: str, category: str, model: str = "kling-image"
    ) -> Optional[str]:
        """使用可灵AI生成图像"""
        if not self.ai_manager:
            self.logger.warning("AI管理器未初始化，无法使用可灵AI")
            return None

        try:
            self.logger.info(f"使用可灵AI生成图像: {model}")

            response = await self.ai_manager.generate_image(
                prompt=prompt,
                width=1024,
                height=1024,
                style=style,
                model=model,
                prefer_provider="keling",
            )

            if response.success:
                images = response.data.get("images", [])
                if images:
                    image_url = images[0]
                    self.logger.info(
                        f"可灵AI图像生成成功: {image_url[:100] if isinstance(image_url, str) else str(image_url)[:100]}..."
                    )
                    return image_url
                else:
                    self.logger.error("可灵AI返回了空的图像列表")
                    return None
            else:
                self.logger.error(f"可灵AI图像生成失败: {response.error}")
                return None

        except Exception as e:
            self.logger.error(f"可灵AI图像生成异常: {e}")
            return None

    async def _generate_with_openai_dalle(
        self,
        prompt: str,
        style: str,
        category: str,
        size: str | None = None,
    ) -> Optional[str]:
        """使用OpenAI DALL-E生成图像"""
        if not self.openai_api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt[:1000],  # DALL-E 3提示词限制在1000字符内
                        "n": 1,
                        "size": size or "1024x1024",
                        "quality": "hd",
                        "style": "vivid" if style != "realistic" else "natural",
                        "response_format": "b64_json",  # 使用base64格式避免URL过期问题
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()

                # 处理base64数据
                if "b64_json" in result["data"][0]:
                    base64_data = result["data"][0]["b64_json"]
                    self.logger.info(f"获取到OpenAI base64图像数据，长度: {len(base64_data)}")
                    return f"data:image/png;base64,{base64_data}"
                else:
                    # 兼容URL格式
                    image_url = result["data"][0]["url"]
                    self.logger.info(f"获取到OpenAI图像URL: {image_url[:100]}...")
                    return image_url
        except Exception as e:
            self.logger.error(f"OpenAI DALL-E生成失败: {e}")
            if hasattr(e, "response"):
                try:
                    error_detail = e.response.json()
                    self.logger.error(f"OpenAI API错误详情: {error_detail}")
                except:
                    self.logger.error(f"OpenAI API响应: {e.response.text}")
            return None

    async def _generate_with_stability(
        self, prompt: str, style: str, category: str
    ) -> Optional[str]:
        """使用Stability AI生成图像"""
        if not self.stability_api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    headers={
                        "Authorization": f"Bearer {self.stability_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "text_prompts": [{"text": prompt, "weight": 1}],
                        "cfg_scale": 7,
                        "height": 1024,
                        "width": 1024,
                        "samples": 1,
                        "steps": 30,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()
                # Stability AI返回base64编码的图像
                image_data = result["artifacts"][0]["base64"]
                # 这里需要将base64转换为文件并保存
                return await self._save_base64_image(image_data, "stability")
        except Exception as e:
            print(f"Stability AI生成失败: {e}")
            return None

    async def _generate_with_custom_image_service(
        self, prompt: str, style: str, category: str
    ) -> Optional[str]:
        """使用自定义AI服务生成图像"""
        if not self.base_url or not self.api_key:
            return None

        payload = {
            "prompt": prompt,
            "parameters": {
                "style": style,
                "category": category,
                "width": 1024,
                "height": 1024,
                "quality": "high",
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    headers=headers,
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("image_url")
        except Exception as e:
            print(f"自定义AI服务生成失败: {e}")
            return None

    async def _save_base64_image(self, base64_data: str, source: str) -> str:
        """保存base64编码的图像"""
        import os
        from datetime import datetime

        # 解码base64数据
        image_bytes = base64.b64decode(base64_data)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_{source}_{timestamp}.png"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)

        # 保存文件
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # 返回相对路径
        return f"/uploads/{filename}"

    async def generate_image(
        self, prompt: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """生成图片（保持向后兼容）"""
        if not self.base_url or not self.api_key:
            raise ValueError("AI服务配置不完整")

        payload = {"prompt": prompt, "parameters": parameters or {}}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    headers=headers,
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("image_url")
        except Exception as e:
            print(f"AI服务调用失败: {e}")
            return None

    async def edit_image(
        self, image_path: str, prompt: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """编辑图片"""
        if not self.base_url or not self.api_key:
            raise ValueError("AI服务配置不完整")

        # 这里应该实现图片上传和编辑逻辑
        # 具体实现取决于AI服务的API
        pass

    async def enhance_image(
        self, image_path: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """增强图片"""
        if not self.base_url or not self.api_key:
            raise ValueError("AI服务配置不完整")

        # 这里应该实现图片增强逻辑
        # 具体实现取决于AI服务的API
        pass


# 创建全局AI服务实例
ai_service = AIService()
