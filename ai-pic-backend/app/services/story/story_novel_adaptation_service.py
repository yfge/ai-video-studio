from __future__ import annotations

from typing import Any

from app.models.script import Episode
from app.models.story_structure import StoryStepOutline, StoryTreatment
from app.models.user import User
from app.repositories.story_novel_repository import StoryNovelRepository
from app.schemas.story_novel_export import AdaptationPlanEpisode
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .story_novel_domain import active_chapters, sha256_text
from .story_novel_revision_service import StoryNovelRevisionService


class StoryNovelAdaptationService:
    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user
        self.repo = StoryNovelRepository(db)
        self.revisions = StoryNovelRevisionService(db, user)

    def save_plan(self, revision_id: str, request):
        revision = self._approved_canonical(revision_id)
        if revision.adaptation_plan_status in {"approved", "applied"}:
            raise HTTPException(status_code=409, detail="已审批或已应用计划不可编辑")
        current = dict(revision.adaptation_plan or {})
        current_version = int(current.get("version") or 1)
        if current and request.expected_version != current_version:
            raise HTTPException(status_code=409, detail="改编计划已被其他窗口更新")
        episodes = [item.model_dump() for item in request.episodes]
        self._validate_episode_rows(revision, episodes)
        revision.adaptation_plan = {
            "version": current_version + (1 if current else 0),
            "novel_content_hash": revision.content_hash,
            "episodes": episodes,
        }
        revision.adaptation_plan_status = "draft"
        self.db.commit()
        return revision

    def approve_plan(self, revision_id: str, expected_version: int):
        revision = self._approved_canonical(revision_id)
        plan = dict(revision.adaptation_plan or {})
        if int(plan.get("version") or 0) != expected_version:
            raise HTTPException(status_code=409, detail="改编计划已被其他窗口更新")
        self._validate_episode_rows(revision, plan.get("episodes") or [])
        if plan.get("novel_content_hash") != revision.content_hash:
            revision.adaptation_plan_status = "stale"
            self.db.commit()
            raise HTTPException(
                status_code=409, detail="小说内容已变化，改编计划已过期"
            )
        revision.adaptation_plan_status = "approved"
        self.db.commit()
        return revision

    def apply_plan(self, revision_id: str) -> list[Episode]:
        revision = self.repo.accessible_revision(
            revision_id, self.user, for_update=True
        )
        if not revision:
            raise HTTPException(status_code=404, detail="小说版本不存在")
        self._ensure_approved_canonical(revision)
        plan = dict(revision.adaptation_plan or {})
        applied_ids = [int(value) for value in plan.get("applied_episode_ids") or []]
        if revision.adaptation_plan_status == "applied" and applied_ids:
            return self.repo.episodes_by_ids(applied_ids)
        if revision.adaptation_plan_status != "approved":
            raise HTTPException(status_code=409, detail="改编计划尚未审批或已过期")
        rows = plan.get("episodes") or []
        self._validate_episode_rows(revision, rows)
        story = revision.story
        chapters = {row.business_id: row for row in active_chapters(revision)}
        treatment = StoryTreatment(
            story_id=story.id,
            revision_number=self.repo.next_treatment_revision_number(story.id),
            status="approved",
            title=f"{story.title} · 小说改编计划 v{plan.get('version', 1)}",
            logline=story.premise,
            theme_summary=story.theme,
            act_structure={"episodes": rows},
            created_by=self.user.id,
            approved_by=self.user.id,
            extra_metadata={
                "source_novel_business_id": revision.business_id,
                "source_novel_content_hash": revision.content_hash,
                "adaptation_plan_version": plan.get("version", 1),
            },
        )
        self.db.add(treatment)
        self.db.flush()
        episodes: list[Episode] = []
        for row in rows:
            refs = [
                self._chapter_ref(chapters[value])
                for value in row["source_chapter_business_ids"]
            ]
            episode = Episode(
                story_id=story.id,
                story_business_id=story.business_id,
                episode_number=row["episode_number"],
                title=row["title"],
                summary=row["summary"],
                plot_points=[
                    {"description": value} for value in row.get("plot_points") or []
                ],
                conflicts=[
                    {"description": value} for value in row.get("conflicts") or []
                ],
                character_arcs=row.get("character_arcs") or {},
                duration_minutes=max(
                    1, round((story.duration_minutes or len(rows) * 3) / len(rows))
                ),
                aspect_ratio=story.default_aspect_ratio,
                source_novel_export_id=revision.id,
                source_novel_export_business_id=revision.business_id,
                source_chapter_refs=refs,
                generation_params={
                    "source": "novel_adaptation_v1",
                    "adaptation_plan_version": plan.get("version", 1),
                },
                extra_metadata={
                    "adaptation_goal": row["adaptation_goal"],
                    "cliffhanger": row.get("cliffhanger"),
                    "source_novel_content_hash": revision.content_hash,
                },
            )
            self.db.add(episode)
            self.db.flush()
            episodes.append(episode)
            beats = row.get("plot_points") or [row["summary"]]
            for sequence, beat in enumerate(beats, start=1):
                self.db.add(
                    StoryStepOutline(
                        story_id=story.id,
                        story_business_id=story.business_id,
                        episode_id=episode.id,
                        episode_business_id=episode.business_id,
                        story_treatment_id=treatment.id,
                        story_treatment_business_id=treatment.business_id,
                        sequence_number=sequence,
                        beat_title=f"情节点 {sequence}",
                        beat_summary=beat,
                        dramatic_question=row["adaptation_goal"],
                        status="approved",
                        created_by=self.user.id,
                        extra_metadata={"source_chapter_refs": refs},
                    )
                )
        plan["applied_episode_ids"] = [episode.id for episode in episodes]
        plan["application_hash"] = sha256_text(
            str(plan.get("version")) + revision.content_hash
        )
        revision.adaptation_plan = plan
        revision.adaptation_plan_status = "applied"
        self.db.commit()
        for episode in episodes:
            self.db.refresh(episode)
        return episodes

    def _approved_canonical(self, revision_id: str):
        revision = self.revisions.revision(revision_id)
        self._ensure_approved_canonical(revision)
        return revision

    @staticmethod
    def _ensure_approved_canonical(revision) -> None:
        if revision.lifecycle_status != "approved":
            raise HTTPException(status_code=409, detail="小说版本尚未审批")
        if revision.story.canonical_novel_export_id != revision.id:
            raise HTTPException(status_code=409, detail="仅当前 canonical 小说可改编")

    @staticmethod
    def _chapter_ref(chapter) -> dict[str, Any]:
        return {
            "business_id": chapter.business_id,
            "position": chapter.position,
            "title": chapter.title,
            "summary": chapter.summary or chapter.content_text[:500],
            "content_hash": chapter.content_hash,
        }

    @staticmethod
    def _validate_episode_rows(revision, rows: list[dict[str, Any]]) -> None:
        if not rows:
            raise HTTPException(status_code=400, detail="改编计划不能为空")
        chapter_ids = {row.business_id for row in active_chapters(revision)}
        numbers: list[int] = []
        for raw in rows:
            item = AdaptationPlanEpisode.model_validate(raw)
            numbers.append(item.episode_number)
            if not set(item.source_chapter_business_ids).issubset(chapter_ids):
                raise HTTPException(status_code=400, detail="改编计划包含无效章节引用")
        if sorted(numbers) != list(range(1, len(rows) + 1)):
            raise HTTPException(status_code=400, detail="集数必须从 1 连续编号")
