from app.models.script import Story, StoryCharacter
from app.models.task import Task, TaskType
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.schemas.generation_requests import StoryNovelExportRequest
from app.services.story.story_novel_canon_service import CANON_GATE_VERSION
from app.services.story.story_novel_revision_service import StoryNovelRevisionService


def _setup(db_session, *, with_character=False):
    user = User(
        username="longform-owner",
        email="longform-owner@example.com",
        hashed_password="not-used",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    virtual_ip = None
    if with_character:
        virtual_ip = VirtualIP(user_id=user.id, name="长篇主角")
        db_session.add(virtual_ip)
        db_session.flush()
    story = Story(
        user_id=user.id,
        title="大纲驱动测试",
        genre="drama",
        workflow_mode="novel_adaptation_v1",
        story_seed={
            "schema": "story_seed_v1",
            "title": "大纲驱动测试",
            "premise": "守门人发现城门后的真相",
            "outline": "发现裂缝，追查来源，付出代价后封住裂缝。",
            "protagonists": [
                {
                    "virtual_ip_business_id": (
                        virtual_ip.business_id if virtual_ip else "vip-placeholder"
                    ),
                    "initial_state": "只相信规则",
                }
            ],
            "world_constraints": ["裂缝只在午夜出现"],
            "central_conflict": "真相与秩序冲突",
            "ending_direction": "主角重写规则",
            "content_constraints": [],
        },
        story_seed_status="confirmed",
        shared_memory_baseline={"version": 0, "characters": []},
    )
    db_session.add(story)
    db_session.flush()
    character = None
    if virtual_ip:
        character = StoryCharacter(
            story_id=story.id,
            story_business_id=story.business_id,
            virtual_ip_id=virtual_ip.id,
            virtual_ip_business_id=virtual_ip.business_id,
            character_name="长篇主角",
        )
        db_session.add(character)
    db_session.commit()
    service = StoryNovelRevisionService(db_session, user)
    revision = service.create_draft(
        story.business_id, StoryNovelExportRequest(style="prose")
    )
    db_session.commit()
    task = Task(title="长篇任务", task_type=TaskType.TEXT_GENERATION, user_id=user.id)
    db_session.add(task)
    db_session.commit()
    return user, story, service, revision, task, virtual_ip, character


def _plan_row(position=1):
    timeline_refs = ["time-1"] if position == 1 else []
    return {
        "position": position,
        "title": f"第{position}章",
        "goal": "推进核心冲突",
        "key_events": ["第一日，发现线索"] if position == 1 else ["发现线索"],
        "character_focus": ["主角"],
        "open_threads": [],
        "end_state": "主角决定追查",
        "target_chars": 3000,
        "preconditions": [],
        "required_event_ids": [f"event-{position}"],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "forbidden_event_ids": [],
        "payoffs_due": [],
        "canon_refs": ["char-a", *timeline_refs],
        "timeline_event_bindings": ({"time-1": "event-1"} if position == 1 else {}),
    }


def _canon():
    return {
        "gate_version": CANON_GATE_VERSION,
        "timeline": [
            {
                "id": "time-1",
                "label": "第一日，发现线索",
                "order": 1,
                "story_time": "第一日",
                "immutable": True,
                "source_chapter_position": 1,
                "source_key_event": "第一日，发现线索",
            }
        ],
        "entities": [
            {
                "id": "char-a",
                "kind": "character",
                "name": "主角",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-gate",
                "kind": "location",
                "name": "城门",
                "aliases": [],
                "attributes": {},
            },
        ],
        "world_rules": [],
        "milestones": [],
        "character_arcs": [
            {
                "character_id": "char-a",
                "start_state": "守规",
                "checkpoints": [],
                "end_state": "重写规则",
            }
        ],
        "initial_state": {
            "char-a": {
                "location": "loc-gate",
                "knowledge": [],
                "status": "守规",
            }
        },
    }
