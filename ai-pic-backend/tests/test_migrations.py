"""
数据库迁移测试
"""

import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.models.script import Episode, Story
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker


class TestMigrations:
    """迁移测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建临时数据库
        self.db_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_url = f"sqlite:///{self.db_file.name}"

        # 创建引擎
        self.engine = create_engine(self.db_url, echo=False)

        # 创建会话
        self.SessionLocal = sessionmaker(bind=self.engine)

        # 配置Alembic
        self.alembic_cfg = Config("alembic.ini")
        self.alembic_cfg.set_main_option("sqlalchemy.url", self.db_url)

    def teardown_method(self):
        """每个测试方法后的清理"""
        self.engine.dispose()
        Path(self.db_file.name).unlink(missing_ok=True)

    def test_migration_creates_all_tables(self):
        """测试迁移创建所有表"""
        # 运行迁移
        command.upgrade(self.alembic_cfg, "head")

        # 检查表是否存在
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "users",
            "virtual_ips",
            "virtual_ip_images",
            "stories",
            "episodes",
            "scripts",
            "story_characters",
            "script_templates",
            "alembic_version",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found"

    def test_migration_creates_correct_columns(self):
        """测试迁移创建正确的列"""
        # 运行迁移
        command.upgrade(self.alembic_cfg, "head")

        inspector = inspect(self.engine)

        # 检查用户表列
        user_columns = [col["name"] for col in inspector.get_columns("users")]
        expected_user_columns = [
            "id",
            "username",
            "email",
            "hashed_password",
            "full_name",
            "is_active",
            "is_superuser",
            "created_at",
            "updated_at",
        ]
        for col in expected_user_columns:
            assert col in user_columns, f"Column {col} not found in users table"

        # 检查虚拟IP表列
        vip_columns = [col["name"] for col in inspector.get_columns("virtual_ips")]
        expected_vip_columns = [
            "id",
            "name",
            "description",
            "tags",
            "background_story",
            "style_prompt",
            "style_reference_images",
            "default_avatar_url",
            "is_active",
            "is_public",
            "created_at",
            "updated_at",
        ]
        for col in expected_vip_columns:
            assert col in vip_columns, f"Column {col} not found in virtual_ips table"

        # 检查故事表列
        story_columns = [col["name"] for col in inspector.get_columns("stories")]
        expected_story_columns = [
            "id",
            "title",
            "genre",
            "theme",
            "target_audience",
            "duration_minutes",
            "premise",
            "synopsis",
            "main_conflict",
            "resolution",
            "main_characters",
            "character_relationships",
            "setting_time",
            "setting_location",
            "world_building",
            "generation_prompt",
            "ai_model",
            "generation_params",
            "status",
            "is_public",
            "tags",
            "extra_metadata",
            "created_at",
            "updated_at",
        ]
        for col in expected_story_columns:
            assert col in story_columns, f"Column {col} not found in stories table"

    def test_migration_creates_indexes(self):
        """测试迁移创建索引"""
        # 运行迁移
        command.upgrade(self.alembic_cfg, "head")

        inspector = inspect(self.engine)

        # 检查用户表索引
        user_indexes = inspector.get_indexes("users")
        index_names = [idx["name"] for idx in user_indexes]

        expected_indexes = ["ix_users_id", "ix_users_username", "ix_users_email"]
        for idx in expected_indexes:
            assert idx in index_names, f"Index {idx} not found in users table"

    def test_migration_creates_foreign_keys(self):
        """测试迁移创建外键"""
        # 运行迁移
        command.upgrade(self.alembic_cfg, "head")

        inspector = inspect(self.engine)

        # 检查虚拟IP图像表外键
        vip_image_fks = inspector.get_foreign_keys("virtual_ip_images")
        assert (
            len(vip_image_fks) > 0
        ), "No foreign keys found in virtual_ip_images table"

        # 检查剧集表外键
        episode_fks = inspector.get_foreign_keys("episodes")
        assert len(episode_fks) > 0, "No foreign keys found in episodes table"

        # 检查剧本表外键
        script_fks = inspector.get_foreign_keys("scripts")
        assert len(script_fks) > 0, "No foreign keys found in scripts table"

    def test_migration_sqlite_compatibility(self):
        """测试迁移与SQLite兼容性"""
        # 运行迁移
        command.upgrade(self.alembic_cfg, "head")

        # 测试基本的CRUD操作
        session = self.SessionLocal()

        try:
            # 创建用户
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed_password",
                full_name="Test User",
            )
            session.add(user)
            session.commit()

            # 查询用户
            queried_user = (
                session.query(User).filter(User.username == "testuser").first()
            )
            assert queried_user is not None
            assert queried_user.email == "test@example.com"

            # 创建虚拟IP
            virtual_ip = VirtualIP(
                name="Test IP",
                description="Test description",
                tags=["test", "ip"],
                is_active=True,
            )
            session.add(virtual_ip)
            session.commit()

            # 创建虚拟IP图像
            vip_image = VirtualIPImage(
                virtual_ip_id=virtual_ip.id,
                filename="test.jpg",
                original_filename="test.jpg",
                file_path="/uploads/test.jpg",
                file_size=1024,
                mime_type="image/jpeg",
                category="avatar",
            )
            session.add(vip_image)
            session.commit()

            # 测试关系
            assert virtual_ip.images[0] == vip_image
            assert vip_image.virtual_ip == virtual_ip

        finally:
            session.close()

    def test_migration_downgrade(self):
        """测试迁移回退"""
        # 运行迁移
        command.upgrade(self.alembic_cfg, "head")

        # 检查表存在
        inspector = inspect(self.engine)
        tables_before = inspector.get_table_names()
        assert "users" in tables_before

        # 回退迁移
        command.downgrade(self.alembic_cfg, "base")

        # 检查表被删除
        inspector = inspect(self.engine)
        tables_after = inspector.get_table_names()

        # 只应该剩下alembic_version表
        assert "users" not in tables_after
        assert "virtual_ips" not in tables_after
        assert "stories" not in tables_after

    def test_migration_idempotent(self):
        """测试迁移幂等性"""
        # 运行迁移两次
        command.upgrade(self.alembic_cfg, "head")
        command.upgrade(self.alembic_cfg, "head")

        # 检查表仍然存在且结构正确
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "users",
            "virtual_ips",
            "virtual_ip_images",
            "stories",
            "episodes",
            "scripts",
            "story_characters",
            "script_templates",
            "alembic_version",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found after second migration"

    def test_migration_version_tracking(self):
        """测试迁移版本追踪"""
        # 运行迁移
        command.upgrade(self.alembic_cfg, "head")

        # 检查版本表
        session = self.SessionLocal()
        try:
            result = session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            assert version is not None, "No version found in alembic_version table"

            # 检查版本格式
            assert len(version) == 12, f"Invalid version format: {version}"

        finally:
            session.close()

    def test_migration_script_syntax(self):
        """测试迁移脚本语法"""
        # 检查迁移脚本目录
        script_dir = ScriptDirectory.from_config(self.alembic_cfg)

        # 获取所有迁移脚本
        revisions = script_dir.get_revisions("head", "base")

        assert len(revisions) > 0, "No migration scripts found"

        # 检查每个脚本的语法
        for revision in revisions:
            assert (
                revision.revision is not None
            ), f"Revision {revision} has no revision ID"
            assert revision.doc is not None, f"Revision {revision} has no description"

    def test_migration_json_columns(self):
        """测试JSON列的SQLite兼容性"""
        # 运行迁移
        command.upgrade(self.alembic_cfg, "head")

        session = self.SessionLocal()
        try:
            # 测试JSON列
            virtual_ip = VirtualIP(
                name="Test IP",
                description="Test description",
                tags=["tag1", "tag2"],
                style_reference_images=["http://example.com/image1.jpg"],
                is_active=True,
            )
            session.add(virtual_ip)
            session.commit()

            # 查询并验证JSON数据
            queried_ip = (
                session.query(VirtualIP).filter(VirtualIP.name == "Test IP").first()
            )
            assert queried_ip.tags == ["tag1", "tag2"]
            assert queried_ip.style_reference_images == [
                "http://example.com/image1.jpg"
            ]

        finally:
            session.close()


@pytest.mark.integration
class TestMigrationIntegration:
    """迁移集成测试"""

    def test_full_migration_workflow(self):
        """测试完整的迁移工作流"""
        # 创建临时数据库
        with tempfile.NamedTemporaryFile(delete=False) as db_file:
            db_url = f"sqlite:///{db_file.name}"

            # 配置Alembic
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)

            try:
                # 1. 运行迁移
                command.upgrade(alembic_cfg, "head")

                # 2. 创建引擎和会话
                engine = create_engine(db_url, echo=False)
                SessionLocal = sessionmaker(bind=engine)
                session = SessionLocal()

                # 3. 创建测试数据
                user = User(
                    username="testuser",
                    email="test@example.com",
                    hashed_password="hashed_password",
                    full_name="Test User",
                )
                session.add(user)

                virtual_ip = VirtualIP(
                    name="Test IP",
                    description="Test description",
                    tags=["test"],
                    is_active=True,
                )
                session.add(virtual_ip)

                story = Story(
                    title="Test Story",
                    genre="Romance",
                    premise="A test story",
                    synopsis="Test synopsis",
                    main_characters=[{"name": "Character1"}],
                    character_relationships={},
                    generation_params={"temperature": 0.7},
                )
                session.add(story)

                session.commit()

                # 4. 验证数据
                assert session.query(User).count() == 1
                assert session.query(VirtualIP).count() == 1
                assert session.query(Story).count() == 1

                # 5. 测试关系
                story_with_episodes = Story(
                    title="Story with Episodes",
                    genre="Action",
                    premise="Test premise",
                    synopsis="Test synopsis",
                    main_characters=[],
                    character_relationships={},
                    generation_params={},
                )
                session.add(story_with_episodes)
                session.commit()

                episode = Episode(
                    story_id=story_with_episodes.id,
                    episode_number=1,
                    title="Episode 1",
                    summary="Test episode",
                    duration_minutes=10,
                    scene_descriptions=[],
                    character_arcs={},
                    key_events=[],
                    emotional_beats=[],
                    generation_params={},
                )
                session.add(episode)
                session.commit()

                # 验证关系
                assert len(story_with_episodes.episodes) == 1
                assert episode.story == story_with_episodes

                session.close()
                engine.dispose()

            finally:
                Path(db_file.name).unlink(missing_ok=True)
