from app.models.narrative_memory import (
    CharacterMemory,
    CharacterMemorySnapshot,
    NarrativeAnchor,
    NarrativeEvent,
)
from app.models.script import Episode, Script, Story, StoryCharacter
from app.models.story_novel_export import StoryNovelChapter, StoryNovelExport
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload


class NarrativeMemoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_owned_story(self, business_id: str, user: User) -> Story | None:
        query = self.session.query(Story).filter(
            Story.business_id == business_id,
            Story.is_deleted.is_(False),
        )
        if not user.is_admin and not user.is_superuser:
            query = query.filter(Story.user_id == user.id)
        return query.first()

    def get_story_character(
        self, story_id: int, character_business_id: str
    ) -> StoryCharacter | None:
        return (
            self.session.query(StoryCharacter)
            .options(joinedload(StoryCharacter.virtual_ip))
            .filter(
                StoryCharacter.story_id == story_id,
                StoryCharacter.business_id == character_business_id,
                StoryCharacter.is_deleted.is_(False),
            )
            .first()
        )

    def list_story_characters(self, story_id: int) -> list[StoryCharacter]:
        return (
            self.session.query(StoryCharacter)
            .options(joinedload(StoryCharacter.virtual_ip))
            .filter(
                StoryCharacter.story_id == story_id,
                StoryCharacter.is_deleted.is_(False),
            )
            .order_by(StoryCharacter.importance.desc(), StoryCharacter.id)
            .all()
        )

    def get_virtual_ip(self, business_id: str) -> VirtualIP | None:
        return (
            self.session.query(VirtualIP)
            .filter(
                VirtualIP.business_id == business_id,
                VirtualIP.is_deleted.is_(False),
            )
            .first()
        )

    def create_anchor(self, **data) -> NarrativeAnchor:
        anchor = NarrativeAnchor(**data)
        self.session.add(anchor)
        return anchor

    def get_anchor(self, story_id: int, business_id: str) -> NarrativeAnchor | None:
        return (
            self.session.query(NarrativeAnchor)
            .filter(
                NarrativeAnchor.story_id == story_id,
                NarrativeAnchor.business_id == business_id,
                NarrativeAnchor.is_deleted.is_(False),
                NarrativeAnchor.status == "active",
            )
            .first()
        )

    def list_anchors(self, story_id: int) -> list[NarrativeAnchor]:
        return (
            self.session.query(NarrativeAnchor)
            .filter(
                NarrativeAnchor.story_id == story_id,
                NarrativeAnchor.is_deleted.is_(False),
                NarrativeAnchor.status == "active",
            )
            .order_by(NarrativeAnchor.narrative_sequence, NarrativeAnchor.id)
            .all()
        )

    def create_event(self, **data) -> NarrativeEvent:
        event = NarrativeEvent(**data)
        self.session.add(event)
        return event

    def get_event(self, story_id: int, business_id: str) -> NarrativeEvent | None:
        return (
            self.session.query(NarrativeEvent)
            .filter(
                NarrativeEvent.story_id == story_id,
                NarrativeEvent.business_id == business_id,
                NarrativeEvent.is_deleted.is_(False),
            )
            .first()
        )

    def list_events(
        self,
        story_id: int,
        *,
        status: str | None = None,
        event_type: str | None = None,
        disclosure: str | None = None,
    ) -> list[NarrativeEvent]:
        query = self.session.query(NarrativeEvent).filter(
            NarrativeEvent.story_id == story_id,
            NarrativeEvent.is_deleted.is_(False),
        )
        if status:
            query = query.filter(NarrativeEvent.status == status)
        if event_type:
            query = query.filter(NarrativeEvent.event_type == event_type)
        if disclosure:
            query = query.filter(NarrativeEvent.audience_disclosure == disclosure)
        return query.order_by(NarrativeEvent.id).all()

    def create_memory(self, **data) -> CharacterMemory:
        memory = CharacterMemory(**data)
        self.session.add(memory)
        return memory

    def get_memory(self, story_id: int, business_id: str) -> CharacterMemory | None:
        return (
            self.session.query(CharacterMemory)
            .filter(
                CharacterMemory.story_id == story_id,
                CharacterMemory.business_id == business_id,
                CharacterMemory.scope == "story_private",
                CharacterMemory.is_deleted.is_(False),
            )
            .first()
        )

    def get_owned_private_memory(
        self, business_id: str, user: User
    ) -> CharacterMemory | None:
        query = (
            self.session.query(CharacterMemory)
            .join(Story, CharacterMemory.story_id == Story.id)
            .filter(
                CharacterMemory.business_id == business_id,
                CharacterMemory.scope == "story_private",
                CharacterMemory.is_deleted.is_(False),
                Story.is_deleted.is_(False),
            )
        )
        if not user.is_admin and not user.is_superuser:
            query = query.filter(Story.user_id == user.id)
        return query.first()

    def list_character_memories(
        self,
        story_id: int,
        character_business_id: str,
        *,
        status: str | None = None,
    ) -> list[CharacterMemory]:
        query = self.session.query(CharacterMemory).filter(
            CharacterMemory.story_id == story_id,
            CharacterMemory.character_business_id == character_business_id,
            CharacterMemory.scope == "story_private",
            CharacterMemory.is_deleted.is_(False),
        )
        if status:
            query = query.filter(CharacterMemory.status == status)
        return query.order_by(CharacterMemory.id).all()

    def list_private_memories(
        self, story_id: int, *, status: str | None = None
    ) -> list[CharacterMemory]:
        query = self.session.query(CharacterMemory).filter(
            CharacterMemory.story_id == story_id,
            CharacterMemory.scope == "story_private",
            CharacterMemory.is_deleted.is_(False),
        )
        if status:
            query = query.filter(CharacterMemory.status == status)
        return query.order_by(CharacterMemory.id).all()

    def create_snapshot(self, **data) -> CharacterMemorySnapshot:
        snapshot = CharacterMemorySnapshot(**data)
        self.session.add(snapshot)
        return snapshot

    def latest_snapshot(
        self, story_id: int, character_business_id: str | None = None
    ) -> CharacterMemorySnapshot | None:
        query = self.session.query(CharacterMemorySnapshot).filter(
            CharacterMemorySnapshot.story_id == story_id,
            CharacterMemorySnapshot.is_deleted.is_(False),
        )
        if character_business_id:
            query = query.filter(
                CharacterMemorySnapshot.character_business_id == character_business_id
            )
        return query.order_by(CharacterMemorySnapshot.id.desc()).first()

    def list_snapshots(self, story_id: int) -> list[CharacterMemorySnapshot]:
        return (
            self.session.query(CharacterMemorySnapshot)
            .filter(
                CharacterMemorySnapshot.story_id == story_id,
                CharacterMemorySnapshot.is_deleted.is_(False),
            )
            .all()
        )

    def list_story_episodes(self, story_id: int) -> list[Episode]:
        return (
            self.session.query(Episode)
            .filter(Episode.story_id == story_id, Episode.is_deleted.is_(False))
            .all()
        )

    def list_story_scripts(self, story_id: int) -> list[Script]:
        return (
            self.session.query(Script)
            .join(Episode, Script.episode_id == Episode.id)
            .filter(
                Episode.story_id == story_id,
                Episode.is_deleted.is_(False),
                Script.is_deleted.is_(False),
            )
            .all()
        )

    def canonical_novel(self, story: Story) -> StoryNovelExport | None:
        if not story.canonical_novel_export_id:
            return None
        return (
            self.session.query(StoryNovelExport)
            .options(joinedload(StoryNovelExport.chapters))
            .filter(
                StoryNovelExport.id == story.canonical_novel_export_id,
                StoryNovelExport.is_deleted.is_(False),
            )
            .first()
        )

    def novel_chapter(self, story: Story, business_id: str) -> StoryNovelChapter | None:
        return (
            self.session.query(StoryNovelChapter)
            .join(
                StoryNovelExport,
                StoryNovelChapter.novel_export_id == StoryNovelExport.id,
            )
            .filter(
                StoryNovelExport.story_id == story.id,
                StoryNovelChapter.business_id == business_id,
                StoryNovelChapter.is_deleted.is_(False),
                StoryNovelExport.is_deleted.is_(False),
            )
            .first()
        )

    def count_events(self, story_id: int, status: str) -> int:
        return int(
            self.session.query(func.count(NarrativeEvent.id))
            .filter(
                NarrativeEvent.story_id == story_id,
                NarrativeEvent.status == status,
                NarrativeEvent.is_deleted.is_(False),
            )
            .scalar()
            or 0
        )

    def count_memories(self, story_id: int, status: str | None = None) -> int:
        query = self.session.query(func.count(CharacterMemory.id)).filter(
            CharacterMemory.story_id == story_id,
            CharacterMemory.scope == "story_private",
            CharacterMemory.is_deleted.is_(False),
        )
        if status:
            query = query.filter(CharacterMemory.status == status)
        return int(query.scalar() or 0)

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def refresh(self, entity) -> None:
        self.session.refresh(entity)
