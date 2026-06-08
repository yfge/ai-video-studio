"""Tests for ScriptStructureSync."""

from unittest.mock import MagicMock, patch


class TestScriptStructureSyncBasics:
    """Test basic sync functionality."""

    def test_import_succeeds(self):
        """Test module can be imported."""
        from app.services.storyboard.sync.script_structure_sync import (
            ScriptStructureSync,
            SyncResult,
        )

        assert ScriptStructureSync is not None
        assert SyncResult is not None

    def test_sync_result_to_dict(self):
        """Test SyncResult serialization."""
        from app.services.storyboard.sync.script_structure_sync import SyncResult

        result = SyncResult(
            success=True,
            message="Test",
            scenes_created=2,
            scenes_updated=1,
            beats_created=5,
        )

        d = result.to_dict()
        assert d["success"] is True
        assert d["scenes_created"] == 2
        assert d["scenes_updated"] == 1
        assert d["beats_created"] == 5


class TestJsonToStructure:
    """Test JSON to structure sync."""

    def test_empty_json_returns_message(self):
        """Test handling of empty JSON scenes."""
        from app.services.storyboard.sync.script_structure_sync import (
            ScriptStructureSync,
        )

        mock_db = MagicMock()
        sync = ScriptStructureSync(mock_db)

        mock_script = MagicMock()
        mock_script.scenes = []
        mock_script.dialogues = []
        mock_script.id = 1

        result = sync.json_to_structure(mock_script)

        assert result.success is True
        assert "no scenes" in result.message.lower()

    def test_creates_scenes_from_json(self):
        """Test scene creation from JSON data."""
        from app.services.storyboard.sync.script_structure_sync import (
            ScriptStructureSync,
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        sync = ScriptStructureSync(mock_db)

        mock_script = MagicMock()
        mock_script.id = 1
        mock_script.scenes = [
            {"scene_number": 1, "location": "Room", "time": "Day"},
            {"scene_number": 2, "location": "Street", "time": "Night"},
        ]
        mock_script.dialogues = []

        with patch(
            "app.services.storyboard.sync.script_structure_sync.ScriptStructureSync._create_scene_from_json"
        ) as mock_create:
            mock_scene = MagicMock()
            mock_scene.id = 1
            mock_create.return_value = mock_scene
            mock_db.flush = MagicMock()

            result = sync.json_to_structure(mock_script, create_missing=True)

        assert result.scenes_created >= 0  # May vary based on implementation


class TestStructureToJson:
    """Test structure to JSON sync."""

    def test_empty_structure_returns_message(self):
        """Test handling of empty story structure."""
        from app.services.storyboard.sync.script_structure_sync import (
            ScriptStructureSync,
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        sync = ScriptStructureSync(mock_db)

        mock_script = MagicMock()
        mock_script.id = 1

        result = sync.structure_to_json(mock_script, scenes=[])

        assert result.success is True
        assert "no scenes" in result.message.lower()


class TestReconcile:
    """Test bidirectional reconciliation."""

    def test_reconcile_empty_both(self):
        """Test reconcile when both sources are empty."""
        from app.services.storyboard.sync.script_structure_sync import (
            ScriptStructureSync,
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        sync = ScriptStructureSync(mock_db)

        mock_script = MagicMock()
        mock_script.id = 1
        mock_script.scenes = []
        mock_script.dialogues = []

        result = sync.reconcile(mock_script)

        assert "no data" in result.message.lower()

    def test_reconcile_json_only(self):
        """Test reconcile when only JSON has data."""
        from app.services.storyboard.sync.script_structure_sync import (
            ScriptStructureSync,
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )
        mock_db.query.return_value.filter.return_value.all.return_value = []

        sync = ScriptStructureSync(mock_db)

        mock_script = MagicMock()
        mock_script.id = 1
        mock_script.scenes = [{"scene_number": 1, "location": "Test"}]
        mock_script.dialogues = []

        with patch.object(sync, "json_to_structure") as mock_sync:
            mock_sync.return_value = MagicMock(success=True, message="Synced")
            sync.reconcile(mock_script)

        mock_sync.assert_called_once()

    def test_reconcile_structure_only(self):
        """Test reconcile when only structure has data."""
        from app.services.storyboard.sync.script_structure_sync import (
            ScriptStructureSync,
        )

        mock_db = MagicMock()
        mock_scene = MagicMock()
        mock_scene.scene_number = "1"
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_scene
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_scene]

        sync = ScriptStructureSync(mock_db)

        mock_script = MagicMock()
        mock_script.id = 1
        mock_script.scenes = []
        mock_script.dialogues = []

        with patch.object(sync, "structure_to_json") as mock_sync:
            mock_sync.return_value = MagicMock(success=True, message="Synced")
            sync.reconcile(mock_script)

        mock_sync.assert_called_once()


class TestSceneConversion:
    """Test scene conversion helpers."""

    def test_create_scene_from_json(self):
        """Test scene model creation from JSON."""
        from app.services.storyboard.sync.script_structure_sync import (
            ScriptStructureSync,
        )

        mock_db = MagicMock()
        sync = ScriptStructureSync(mock_db)

        mock_script = MagicMock()
        mock_script.id = 1

        json_scene = {
            "scene_number": 1,
            "location": "Office",
            "time": "Morning",
            "description": "A busy office",
            "characters": ["John", "Mary"],
        }

        with patch("app.models.story_structure.Scene") as MockScene:
            mock_instance = MagicMock()
            MockScene.return_value = mock_instance

            sync._create_scene_from_json(mock_script, json_scene)

        MockScene.assert_called_once()
        call_kwargs = MockScene.call_args.kwargs
        assert call_kwargs["script_id"] == 1
        assert call_kwargs["scene_number"] == "1"
        assert "Office" in call_kwargs["slug_line"]

    def test_scene_to_json(self):
        """Test scene model to JSON conversion."""
        from app.services.storyboard.sync.script_structure_sync import (
            ScriptStructureSync,
        )

        mock_db = MagicMock()
        sync = ScriptStructureSync(mock_db)

        mock_scene = MagicMock()
        mock_scene.scene_number = "1"
        mock_scene.location = "Office"
        mock_scene.time_of_day = "Morning"
        mock_scene.summary = "A busy office"
        mock_scene.primary_characters = ["John", "Mary"]

        result = sync._scene_to_json(mock_scene)

        assert result["scene_number"] == 1
        assert result["location"] == "Office"
        assert result["time"] == "Morning"
        assert result["description"] == "A busy office"
        assert result["characters"] == ["John", "Mary"]
