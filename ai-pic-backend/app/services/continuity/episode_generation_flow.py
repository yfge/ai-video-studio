from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import EpisodePlanItem, EpisodePlanModel
from app.services.continuity.episode_continuity import (
    build_previous_episodes_context,
    extract_single_episode,
    run_episode_continuity_audit,
    run_episode_ledger_update,
    run_episode_rewrite_with_audit,
)
from app.services.episode_agent_episode_utils import (
    MAX_REACT_REGENERATE_ATTEMPTS,
    stub_episode_from_outline,
    validate_episode_duration,
    validate_episode_payload,
)
from app.utils.json_utils import extract_json_block


@dataclass(slots=True)
class EpisodeReactOutput:
    episode: Dict[str, Any]
    prompt: str
    raw: str
    provider: str | None
    model: str | None
    usage: dict | None
    fallback_from_outline: bool
    react_attempts: int
    duration_accepted: bool
    continuity_ledger: Dict[str, Any]


async def generate_episode_with_continuity_react(
    *,
    ai_manager: Any,
    story: Dict[str, Any],
    outline: Dict[str, Any],
    outline_episodes: list[Dict[str, Any]],
    continuity_ledger: Dict[str, Any],
    episode_duration: Optional[int],
    focus_characters: list[Dict[str, Any]],
    plot_complexity: str,
    pacing: str,
    additional_requirements: Optional[str],
    style_preferences: list[str],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
    progress: Callable[[str], Awaitable[None]],
    reasoning: list[str],
) -> EpisodeReactOutput:
    plan_schema = EpisodePlanModel.model_json_schema()
    ep_num = outline.get("episode_number") or 1
    previous_eps = build_previous_episodes_context(
        step_outlines=[o for o in outline_episodes if isinstance(o, dict)],
        ledger=continuity_ledger,
        current_episode_number=ep_num,
    )
    episode_obj: Dict[str, Any] | None = None
    content: str = ""
    fallback_used = False
    duration_accepted = False
    react_attempt = 0
    last_audit_issues: list[dict[str, Any]] = []
    last_rejection_reason: str | None = None
    effective_provider: str | None = prefer_provider
    effective_model: str | None = model
    prompt = ""

    while react_attempt < MAX_REACT_REGENERATE_ATTEMPTS:
        react_attempt += 1
        is_regeneration = react_attempt > 1

        if is_regeneration and episode_obj and last_rejection_reason == "duration":
            _, cur_secs, tgt_secs = validate_episode_duration(
                episode_obj, episode_duration
            )
            rejection_reason = (
                "duration_too_short" if cur_secs < tgt_secs else "duration_too_long"
            )
            await progress(
                f"生成第{ep_num}集：REACT驳回（{rejection_reason}，"
                f"{cur_secs}秒 vs 目标{tgt_secs}秒），第{react_attempt}次尝试"
            )
            reasoning.append(
                f"episode_react_reject_{ep_num}_attempt{react_attempt - 1}_"
                f"{rejection_reason}_{cur_secs}s"
            )
            prompt = prompt_manager.render_prompt(
                PromptTemplate.EPISODE_DURATION_REJECT.value,
                {
                    "story": story,
                    "outline": outline,
                    "previous_episodes": previous_eps,
                    "rejected_episode": episode_obj,
                    "target_duration_seconds": tgt_secs,
                    "current_duration_seconds": cur_secs,
                    "rejection_reason": rejection_reason,
                    "attempt_number": react_attempt,
                    "focus_characters": focus_characters,
                    "episode_duration": episode_duration,
                    "plot_complexity": plot_complexity,
                    "pacing": pacing,
                    "continuity_ledger": continuity_ledger,
                },
            )
        elif is_regeneration and episode_obj and last_rejection_reason == "continuity":
            await progress(
                f"生成第{ep_num}集：一致性审校驳回，尝试修订（第{react_attempt}次）"
            )
            reasoning.append(
                f"episode_react_reject_{ep_num}_attempt{react_attempt - 1}_continuity"
            )
            story_for_prompt = dict(story or {})
            story_for_prompt.pop("context_pack", None)
            prompt = prompt_manager.render_prompt(
                "episode_rewrite_with_audit",
                {
                    "story": story_for_prompt,
                    "outline": outline,
                    "previous_episodes_context": previous_eps,
                    "continuity_ledger": continuity_ledger,
                    "episode_plan": episode_obj,
                    "audit_issues": last_audit_issues,
                },
            )
        else:
            await progress(f"生成第{ep_num}集：调用模型")
            prompt = prompt_manager.render_prompt(
                PromptTemplate.EPISODE_FROM_OUTLINE.value,
                {
                    "story": story,
                    "outline": outline,
                    "previous_episodes": previous_eps,
                    "continuity_ledger": continuity_ledger,
                    "focus_characters": focus_characters,
                    "episode_duration": episode_duration,
                    "plot_complexity": plot_complexity,
                    "pacing": pacing,
                    "additional_requirements": additional_requirements,
                    "style_preferences": style_preferences,
                },
            )

        resp = await ai_manager.generate_text(
            prompt=prompt,
            temperature=temperature,
            model=effective_model,
            prefer_provider=effective_provider,
            json_schema={"name": "episode_plan", "schema": plan_schema},
            system_prompt=prompt_manager.render_prompt(
                PromptTemplate.SYSTEM_PROMPT_SCRIPT.value,
                {"story_format": story.get("story_format")},
            ),
        )
        if getattr(resp, "provider", None):
            effective_provider = resp.provider
        if getattr(resp, "model", None):
            effective_model = resp.model
        content = (
            resp.data
            if isinstance(resp.data, str)
            else ("" if resp.data is None else str(resp.data))
        )
        parsed = (
            extract_json_block(content)
            if isinstance(content, str)
            else (content if isinstance(content, dict) else None)
        )
        episode_obj = (
            extract_single_episode(parsed) if isinstance(parsed, dict) else None
        )

        if not episode_obj:
            fallback_used = True
            await progress(f"生成第{ep_num}集：模型输出无效，使用大纲兜底")
            episode_obj = stub_episode_from_outline(outline)
            reasoning.append(f"episode_parse_failed_{ep_num}")
            break

        episode_obj.setdefault("episode_number", outline.get("episode_number"))
        await progress(f"生成第{ep_num}集：校验中")

        try:
            EpisodePlanItem.model_validate(episode_obj)
            valid, reason = validate_episode_payload(episode_obj)
            if not valid:
                fallback_used = True
                episode_obj = stub_episode_from_outline(outline)
                reasoning.append(f"episode_invalid_{ep_num}_{reason}")
                break
        except Exception:
            fallback_used = True
            episode_obj = stub_episode_from_outline(outline)
            reasoning.append(f"episode_schema_invalid_{ep_num}")
            break

        if episode_duration:
            dur_valid, cur_secs, _ = validate_episode_duration(
                episode_obj, episode_duration
            )
            if dur_valid:
                duration_accepted = True
                reasoning.append(
                    f"episode_duration_ok_{ep_num}_attempt{react_attempt}_{cur_secs}s"
                )
                await progress(f"生成第{ep_num}集：时长验证通过（{cur_secs}秒）")
            else:
                reasoning.append(
                    f"episode_duration_bad_{ep_num}_attempt{react_attempt}_{cur_secs}s"
                )
                last_rejection_reason = "duration"
                if react_attempt >= MAX_REACT_REGENERATE_ATTEMPTS:
                    reasoning.append(
                        f"episode_duration_accepted_after_max_attempts_{ep_num}_{cur_secs}s"
                    )
                    await progress(
                        f"生成第{ep_num}集：达到最大重试次数，接受当前时长（{cur_secs}秒）"
                    )
                    break
                continue

        await progress(f"生成第{ep_num}集：一致性审校中")
        audit_result, _audit_resp = await run_episode_continuity_audit(
            ai_manager=ai_manager,
            story=story,
            outline=outline,
            previous_episodes_context=previous_eps,
            continuity_ledger=continuity_ledger,
            episode_plan=episode_obj,
            model=effective_model,
            prefer_provider=effective_provider,
            temperature=temperature,
        )
        if audit_result.verdict == "fail" and audit_result.issues:
            last_rejection_reason = "continuity"
            last_audit_issues = [issue.model_dump() for issue in audit_result.issues]
            reasoning.append(f"episode_continuity_fail_{ep_num}_attempt{react_attempt}")

            await progress(f"生成第{ep_num}集：尝试修订一致性问题")
            rewrite_payload, _rewrite_resp = await run_episode_rewrite_with_audit(
                ai_manager=ai_manager,
                story=story,
                outline=outline,
                previous_episodes_context=previous_eps,
                continuity_ledger=continuity_ledger,
                episode_plan_draft=episode_obj,
                audit_issues=last_audit_issues,
                model=effective_model,
                prefer_provider=effective_provider,
                temperature=temperature,
            )
            rewritten = extract_single_episode(rewrite_payload)
            if rewritten:
                try:
                    EpisodePlanItem.model_validate(rewritten)
                    valid, _ = validate_episode_payload(rewritten)
                    if valid:
                        episode_obj = rewritten
                        audit_after, _ = await run_episode_continuity_audit(
                            ai_manager=ai_manager,
                            story=story,
                            outline=outline,
                            previous_episodes_context=previous_eps,
                            continuity_ledger=continuity_ledger,
                            episode_plan=episode_obj,
                            model=effective_model,
                            prefer_provider=effective_provider,
                            temperature=temperature,
                        )
                        if audit_after.verdict != "fail":
                            reasoning.append(
                                f"episode_continuity_rewrite_ok_{ep_num}_attempt{react_attempt}"
                            )
                            break
                        last_audit_issues = [
                            issue.model_dump() for issue in audit_after.issues
                        ]
                        reasoning.append(
                            f"episode_continuity_rewrite_still_fail_{ep_num}_attempt{react_attempt}"
                        )
                except Exception:
                    reasoning.append(
                        f"episode_continuity_rewrite_invalid_{ep_num}_attempt{react_attempt}"
                    )

            if react_attempt >= MAX_REACT_REGENERATE_ATTEMPTS:
                reasoning.append(
                    f"episode_continuity_accepted_after_max_attempts_{ep_num}"
                )
                break
            continue

        reasoning.append(f"episode_ok_{ep_num}")
        break

    if not episode_obj:
        episode_obj = stub_episode_from_outline(outline)
        fallback_used = True

    ledger_payload, _ledger_resp = await run_episode_ledger_update(
        ai_manager=ai_manager,
        previous_ledger=continuity_ledger,
        story=story,
        outline=outline,
        episode_plan=episode_obj,
        model=effective_model,
        prefer_provider=effective_provider,
    )
    continuity_ledger = ledger_payload.ledger.model_dump()
    episode_obj["continuity_snapshot"] = ledger_payload.episode_snapshot.model_dump()

    return EpisodeReactOutput(
        episode=episode_obj,
        prompt=prompt,
        raw=content,
        provider=resp.provider if "resp" in locals() else None,  # best-effort
        model=resp.model if "resp" in locals() else None,
        usage=resp.usage if "resp" in locals() else None,
        fallback_from_outline=fallback_used,
        react_attempts=react_attempt,
        duration_accepted=duration_accepted,
        continuity_ledger=continuity_ledger,
    )
