from app.models.timeline import MediaAsset
from app.repositories.timeline_repository import MediaAssetRepository


class ProductionCanvasCandidateRepository(MediaAssetRepository):
    def find_owned_by_location(
        self, *, created_by: int, asset_type: str, file_url: str
    ) -> MediaAsset | None:
        return (
            self.session.query(MediaAsset)
            .filter(MediaAsset.created_by == created_by)
            .filter(MediaAsset.asset_type == asset_type)
            .filter(MediaAsset.file_url == file_url)
            .filter(MediaAsset.is_deleted.is_(False))
            .first()
        )

    def list_history_assets(
        self, *, created_by: int, asset_type: str
    ) -> list[MediaAsset]:
        return (
            self.session.query(MediaAsset)
            .filter(MediaAsset.created_by == created_by)
            .filter(MediaAsset.asset_type == asset_type)
            .filter(MediaAsset.is_deleted.is_(False))
            .order_by(MediaAsset.created_at.asc(), MediaAsset.id.asc())
            .all()
        )
