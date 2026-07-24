from __future__ import annotations

from app.models.script import Episode
from app.models.story_structure import StoryStepOutline, StoryTreatment
from app.models.user import User
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.story_novel_repository import StoryNovelRepository
from app.services.narrative_memory.generation_context_service import (
    NarrativeGenerationContextService,
)
from app.services.narrative_memory.source_hash import artifact_hash
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .story_novel_downstream_gate import (
    chapter_source_evidence,
    freeze_adaptation_plan,
    require_adaptation_plan,
    require_canonical_revision,
)
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
        revision.adaptation_plan = freeze_adaptation_plan(
            revision,
            version=current_version + (1 if current else 0),
            rows=episodes,
        )
        revision.adaptation_plan_status = "draft"
        self.db.commit()
        return revision

    def approve_plan(self, revision_id: str, expected_version: int):
        revision = self._approved_canonical(revision_id)
        plan = dict(revision.adaptation_plan or {})
        if int(plan.get("version") or 0) != expected_version:
            raise HTTPException(status_code=409, detail="改编计划已被其他窗口更新")
        if plan.get("novel_content_hash") != revision.content_hash:
            revision.adaptation_plan_status = "stale"
            self.db.commit()
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "ADAPTATION_PLAN_STALE",
                    "message": "小说内容已变化，改编计划已过期",
                },
            )
        revision.adaptation_plan = freeze_adaptation_plan(
            revision,
            version=expected_version,
            rows=plan.get("episodes") or [],
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
        plan, chapter_rows = require_adaptation_plan(revision)
        applied_ids = [int(value) for value in plan.get("applied_episode_ids") or []]
        if revision.adaptation_plan_status == "applied" and applied_ids:
            return self.repo.episodes_by_ids(applied_ids)
        rows = plan.get("episodes") or []
        story = revision.story
        chapters = {row.business_id: row for row in chapter_rows}
        lineage = self._lineage(revision, plan)
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
            extra_metadata=lineage,
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
                    **lineage,
                },
                extra_metadata={
                    "adaptation_goal": row["adaptation_goal"],
                    "cliffhanger": row.get("cliffhanger"),
                    **lineage,
                },
            )
            self.db.add(episode)
            self.db.flush()
            NarrativeGenerationContextService(
                NarrativeMemoryRepository(self.db)
            ).freeze_episode(
                story,
                episode,
                adaptation_plan_version=int(plan.get("version") or 1),
                commit=False,
            )
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
                        extra_metadata={
                            "source_chapter_refs": refs,
                            **lineage,
                        },
                    )
                )
        plan["applied_episode_ids"] = [episode.id for episode in episodes]
        plan["application_hash"] = artifact_hash(
            {
                "adaptation_plan_hash": plan["plan_hash"],
                "applied_episode_ids": plan["applied_episode_ids"],
            }
        )
        revision.adaptation_plan = plan
        revision.adaptation_plan_status = "applied"
        self.db.commit()
        for episode in episodes:
            self.db.refresh(episode)
        return episodes

    def _approved_canonical(self, revision_id: str):
        revision = self.revisions.revision(revision_id)
        require_canonical_revision(revision)
        return revision

    @staticmethod
    def _chapter_ref(chapter):
        return chapter_source_evidence(chapter)

    @staticmethod
    def _lineage(revision, plan) -> dict:
        return {
            "source_novel_business_id": revision.business_id,
            "source_novel_content_hash": revision.content_hash,
            "generation_plan_version": plan["generation_plan_version"],
            "generation_plan_hash": plan["generation_plan_hash"],
            "adaptation_plan_version": plan["version"],
            "adaptation_plan_hash": plan["plan_hash"],
        }
