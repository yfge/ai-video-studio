"""Episode render service.

Coordinates rendering of episode final videos from storyboard frames.
"""

import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.script import Episode, Script
from app.services.media import upload_bytes

from .video_concat import VideoClip, concat_video_clips

logger = get_logger()


class EpisodeRenderService:
    """Service for rendering episode final videos."""

    def __init__(self, db: Session):
        self.db = db

    def get_storyboard_clips(self, script: Script) -> List[VideoClip]:
        """Extract video clips from script storyboard.

        Returns list of VideoClip objects with video URLs and durations.
        """
        storyboard = (script.extra_metadata or {}).get("storyboard", {})
        frames = storyboard.get("frames", [])

        clips = []
        for i, frame in enumerate(frames):
            video_url = frame.get("video_url")
            if not video_url:
                logger.warning(f"Frame {i} has no video_url, skipping")
                continue

            duration = frame.get("duration_seconds", 3.0)
            if isinstance(duration, str):
                try:
                    duration = float(duration)
                except ValueError:
                    duration = 3.0

            clips.append(VideoClip(
                url=video_url,
                target_duration_seconds=duration,
                frame_number=frame.get("frame_number", i + 1),
                description=frame.get("description"),
            ))

        return clips

    def get_episode_audio_url(self, episode: Episode) -> Optional[str]:
        """Get episode dialogue audio URL.

        Looks in episode.extra_metadata for dialogue_audio.oss_url
        """
        if not episode or not episode.extra_metadata:
            return None

        dialogue_audio = episode.extra_metadata.get("dialogue_audio", {})
        return dialogue_audio.get("oss_url")

    async def render_episode(
        self,
        script_id: int,
        render_with_tts_audio: bool = True,
        render_with_video_audio: bool = True,
    ) -> Dict[str, Any]:
        """Render episode final videos.

        Args:
            script_id: Script ID to render
            render_with_tts_audio: Generate version with TTS dialogue audio
            render_with_video_audio: Generate version with original video audio

        Returns:
            Dict with render results including URLs
        """
        script = self.db.query(Script).filter(Script.id == script_id).first()
        if not script:
            return {"success": False, "error": "Script not found"}

        episode = script.episode
        if not episode:
            return {"success": False, "error": "Script has no episode"}

        # Get storyboard clips
        clips = self.get_storyboard_clips(script)
        if not clips:
            return {"success": False, "error": "No video clips in storyboard"}

        logger.info(f"Rendering episode {episode.id} with {len(clips)} clips")

        results = {
            "success": True,
            "script_id": script_id,
            "episode_id": episode.id,
            "frame_count": len(clips),
            "total_duration": sum(c.target_duration_seconds for c in clips),
            "renders": {},
        }

        # Render version with original video audio
        if render_with_video_audio:
            result = await self._render_version(
                clips=clips,
                audio_url=None,
                version_name="video_audio",
                episode=episode,
            )
            results["renders"]["video_audio"] = result

        # Render version with TTS audio
        if render_with_tts_audio:
            audio_url = self.get_episode_audio_url(episode)
            if audio_url:
                result = await self._render_version(
                    clips=clips,
                    audio_url=audio_url,
                    version_name="tts_audio",
                    episode=episode,
                )
                results["renders"]["tts_audio"] = result
            else:
                results["renders"]["tts_audio"] = {
                    "success": False,
                    "error": "No TTS audio URL found for episode",
                }

        # Update episode metadata with render results
        self._save_render_results(episode, results)

        return results

    async def _render_version(
        self,
        clips: List[VideoClip],
        audio_url: Optional[str],
        version_name: str,
        episode: Episode,
    ) -> Dict[str, Any]:
        """Render a single version of the episode."""
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".mp4", delete=False
            ) as tmp:
                output_path = tmp.name

            result = await concat_video_clips(
                clips=clips,
                output_path=output_path,
                audio_url=audio_url,
                keep_original_audio=(audio_url is None),
            )

            if not result.get("success"):
                return result

            # Upload to OSS
            with open(output_path, "rb") as f:
                video_bytes = f.read()

            upload_result = await upload_bytes(
                content=video_bytes,
                filename=f"episode_{episode.id}_{version_name}.mp4",
                media_type="video",
                prefix="episode-renders",
                metadata={
                    "episode_id": str(episode.id),
                    "version": version_name,
                    "frame_count": str(result.get("frame_count", 0)),
                    "duration_seconds": str(result.get("duration_seconds", 0)),
                    "has_replaced_audio": str(result.get("has_replaced_audio", False)),
                    "rendered_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Cleanup temp file
            import os
            if os.path.exists(output_path):
                os.unlink(output_path)

            return {
                "success": True,
                "url": upload_result.get("url"),
                "duration_seconds": result.get("duration_seconds"),
                "frame_count": result.get("frame_count"),
                "rendered_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Render version {version_name} failed: {e}")
            return {"success": False, "error": str(e)}

    def _save_render_results(
        self,
        episode: Episode,
        results: Dict[str, Any],
    ) -> None:
        """Save render results to episode metadata."""
        extra = dict(episode.extra_metadata or {})

        renders = extra.get("episode_renders", {})
        renders["latest"] = {
            "rendered_at": datetime.now(timezone.utc).isoformat(),
            "frame_count": results.get("frame_count"),
            "total_duration": results.get("total_duration"),
            "versions": {},
        }

        for version_name, version_result in results.get("renders", {}).items():
            if version_result.get("success"):
                renders["latest"]["versions"][version_name] = {
                    "url": version_result.get("url"),
                    "duration_seconds": version_result.get("duration_seconds"),
                }

        extra["episode_renders"] = renders
        episode.extra_metadata = extra
        self.db.commit()

        logger.info(f"Saved render results for episode {episode.id}")
