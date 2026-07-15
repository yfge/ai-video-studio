"""Database access for storyboard image reference hydration."""

from app.models.script import Episode
from app.models.story_structure import Environment, Scene, Shot
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from sqlalchemy.orm import Session


class StoryboardImageReferenceRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_scenes(self, script_id: int) -> list[Scene]:
        return self.session.query(Scene).filter(Scene.script_id == script_id).all()

    def list_environments(self, environment_ids: set[int]) -> list[Environment]:
        if not environment_ids:
            return []
        return (
            self.session.query(Environment)
            .filter(Environment.id.in_(environment_ids))
            .all()
        )

    def list_shots(self, scene_ids: list[int]) -> list[Shot]:
        if not scene_ids:
            return []
        return self.session.query(Shot).filter(Shot.scene_id.in_(scene_ids)).all()

    def get_episode(self, episode_id: int) -> Episode | None:
        return self.session.query(Episode).filter(Episode.id == episode_id).first()

    def list_virtual_ips(self, virtual_ip_ids: set[int]) -> list[VirtualIP]:
        if not virtual_ip_ids:
            return []
        return (
            self.session.query(VirtualIP).filter(VirtualIP.id.in_(virtual_ip_ids)).all()
        )

    def list_virtual_ip_images(
        self,
        virtual_ip_ids: set[int],
    ) -> list[VirtualIPImage]:
        if not virtual_ip_ids:
            return []
        return (
            self.session.query(VirtualIPImage)
            .filter(VirtualIPImage.virtual_ip_id.in_(virtual_ip_ids))
            .order_by(
                VirtualIPImage.is_default.desc(),
                VirtualIPImage.created_at.desc(),
            )
            .all()
        )
