from __future__ import annotations

from dataclasses import dataclass

from app.models.user import User
from app.repositories.environment_repository import EnvironmentRepository
from app.repositories.virtual_ip_image_repository import VirtualIPImageRepository
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class CanvasReferenceArtifacts:
    artifacts: list[str]
    image_urls: list[str]
    unresolved: list[str]


def _clean_urls(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _append_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def resolve_canvas_reference_artifacts(
    db: Session,
    user: User,
    artifact_refs: list[str],
) -> CanvasReferenceArtifacts:
    resolved_artifacts: list[str] = []
    image_urls: list[str] = []
    unresolved: list[str] = []
    image_repo = VirtualIPImageRepository(db)
    environment_repo = EnvironmentRepository(db)

    for raw_ref in artifact_refs:
        ref = raw_ref.strip()
        parts = ref.split(":")
        urls: list[str] = []
        if len(parts) == 3 and parts[0] == "virtual_ip_image":
            try:
                virtual_ip_id, image_id = int(parts[1]), int(parts[2])
            except ValueError:
                unresolved.append(ref)
                continue
            image = image_repo.find_accessible_by_result_ref(
                image_id=image_id,
                virtual_ip_id=virtual_ip_id,
                user=user,
            )
            if image:
                url = image.oss_url or image.file_path
                urls = [url] if isinstance(url, str) and url.strip() else []
        elif len(parts) == 3 and parts[0] == "environment_images":
            try:
                environment_id, count = int(parts[1]), int(parts[2])
            except ValueError:
                unresolved.append(ref)
                continue
            environment = environment_repo.find_accessible_by_id(environment_id, user)
            if environment and count > 0:
                urls = _clean_urls(environment.reference_images)[-count:]

        if not urls:
            unresolved.append(ref)
            continue
        if ref not in resolved_artifacts:
            resolved_artifacts.append(ref)
        _append_unique(image_urls, urls)

    return CanvasReferenceArtifacts(
        artifacts=resolved_artifacts,
        image_urls=image_urls,
        unresolved=unresolved,
    )
