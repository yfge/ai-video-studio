import re
from pathlib import Path


def test_migration_environment_assets_schema():
    """Migration regression: environments + scenes.environment_id + shots.character_ids.

    Note: Our Alembic history includes operations that are not SQLite-friendly
    (e.g. adding FK constraints via ALTER TABLE). Instead of executing the full
    migration chain on SQLite, we assert the specific revision scripts exist and
    include the expected operations.
    """

    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    env_revision = versions_dir / "d1a2b3c4e5f7_add_environments_and_scene_env.py"
    shot_revision = versions_dir / "e2f4c6d8b9aa_add_character_ids_to_shots.py"
    ip_env_revision = (
        versions_dir / "4c8f2e1d9a70_add_virtual_ip_environments.py"
    )

    assert env_revision.exists(), f"Missing migration: {env_revision}"
    assert shot_revision.exists(), f"Missing migration: {shot_revision}"
    assert ip_env_revision.exists(), f"Missing migration: {ip_env_revision}"

    env_source = env_revision.read_text(encoding="utf-8")
    assert re.search(r'op\.create_table\(\s*["\']environments["\']', env_source)
    assert re.search(
        r'op\.add_column\(\s*["\']scenes["\']\s*,\s*sa\.Column\(\s*["\']environment_id["\']',
        env_source,
    )
    assert re.search(
        r'op\.create_foreign_key\(\s*["\']fk_scenes_environment_id["\']', env_source
    )

    shot_source = shot_revision.read_text(encoding="utf-8")
    assert re.search(
        r'op\.add_column\(\s*["\']shots["\']\s*,\s*sa\.Column\(\s*["\']character_ids["\']',
        shot_source,
    )

    ip_env_source = ip_env_revision.read_text(encoding="utf-8")
    assert re.search(
        r'op\.create_table\(\s*["\']virtual_ip_environments["\']',
        ip_env_source,
    )
    assert "ux_virtual_ip_environments_pair_deleted" in ip_env_source
    assert "virtual_ip_id" in ip_env_source
    assert "environment_id" in ip_env_source
