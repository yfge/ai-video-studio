"""
API端点测试
"""
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import (
    UserFactory, VirtualIPFactory, VirtualIPImageFactory,
    StoryFactory, EpisodeFactory, ScriptFactory,
    setup_factories
)


@pytest.mark.integration
class TestVirtualIPAPI:
    """虚拟IP API测试"""
    
    def test_create_virtual_ip(self, client: TestClient, db_session: Session):
        """测试创建虚拟IP"""
        setup_factories(db_session)
        
        data = {
            "name": "Test Virtual IP",
            "description": "A test virtual IP",
            "tags": ["test", "virtual", "ip"],
            "background_story": "Test background story",
            "style_prompt": "Test style prompt",
            "is_public": True
        }
        
        response = client.post("/api/v1/virtual-ips/", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == data["name"]
        assert result["description"] == data["description"]
        assert result["tags"] == data["tags"]
        assert result["is_public"] == data["is_public"]
    
    def test_get_virtual_ip(self, client: TestClient, db_session: Session):
        """测试获取虚拟IP"""
        setup_factories(db_session)
        
        virtual_ip = VirtualIPFactory()
        
        response = client.get(f"/api/v1/virtual-ips/{virtual_ip.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == virtual_ip.id
        assert result["name"] == virtual_ip.name
        assert result["description"] == virtual_ip.description
    
    def test_get_virtual_ip_not_found(self, client: TestClient, db_session: Session):
        """测试获取不存在的虚拟IP"""
        response = client.get("/api/v1/virtual-ips/999")
        
        assert response.status_code == 404
    
    def test_list_virtual_ips(self, client: TestClient, db_session: Session):
        """测试列出虚拟IP"""
        setup_factories(db_session)
        
        vip1 = VirtualIPFactory()
        vip2 = VirtualIPFactory()
        
        response = client.get("/api/v1/virtual-ips/")
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
        assert any(item["id"] == vip1.id for item in result)
        assert any(item["id"] == vip2.id for item in result)
    
    def test_update_virtual_ip(self, client: TestClient, db_session: Session):
        """测试更新虚拟IP"""
        setup_factories(db_session)
        
        virtual_ip = VirtualIPFactory()
        
        update_data = {
            "name": "Updated Virtual IP",
            "description": "Updated description",
            "tags": ["updated", "test"],
            "is_public": True
        }
        
        response = client.put(f"/api/v1/virtual-ips/{virtual_ip.id}", json=update_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == update_data["name"]
        assert result["description"] == update_data["description"]
        assert result["tags"] == update_data["tags"]
        assert result["is_public"] == update_data["is_public"]
    
    def test_delete_virtual_ip(self, client: TestClient, db_session: Session):
        """测试删除虚拟IP"""
        setup_factories(db_session)
        
        virtual_ip = VirtualIPFactory()
        
        response = client.delete(f"/api/v1/virtual-ips/{virtual_ip.id}")
        
        assert response.status_code == 204
        
        # 验证删除
        response = client.get(f"/api/v1/virtual-ips/{virtual_ip.id}")
        assert response.status_code == 404
    
    def test_generate_virtual_ip_image(self, client: TestClient, db_session: Session, mock_ai_service):
        """测试生成虚拟IP图像"""
        setup_factories(db_session)
        
        virtual_ip = VirtualIPFactory()
        
        data = {
            "prompt": "A beautiful portrait",
            "style": "realistic",
            "category": "portrait",
            "ai_service": "openai"
        }
        
        response = client.post(f"/api/v1/virtual-ips/{virtual_ip.id}/generate-image", json=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "image_url" in result

    def test_generate_virtual_ip_image_variant(
        self,
        client: TestClient,
        db_session: Session,
        monkeypatch,
    ):
        """测试基于已有虚拟IP图像生成变体（图生图）"""
        setup_factories(db_session)

        virtual_ip = VirtualIPFactory()

        # 手动创建一条基础图像记录，避免依赖过时的工厂字段
        from app.models.virtual_ip import VirtualIPImage

        base_image = VirtualIPImage(
            virtual_ip_id=virtual_ip.id,
            filename="base_test.png",
            original_filename="base_test.png",
            file_path="/uploads/base_test.png",
            file_size=1024,
            mime_type="image/png",
            category="portrait",
            subcategory=None,
            tags=["test", "base"],
            is_default=True,
            is_public=True,
        )
        db_session.add(base_image)
        db_session.commit()
        db_session.refresh(base_image)

        payload = {
            "prompt": "为当前角色生成不同视角/姿态的图像，如背面照或全身照",
            "model": "google:gemini-3-pro-image-preview",
            "count": 1,
        }

        # 为本测试用例注入最小的 ai_service mock，避免真实外部调用
        from app.api.v1.endpoints import virtual_ip_images as vip_images_module

        class _DummyResp:
            def __init__(self) -> None:
                self.success = True
                self.data = {"images": ["https://example.com/mock-img2img.png"]}
                self.provider = "mock-provider"
                self.model = "mock-model"
                self.usage = {}

        class _DummyAIManager:
            async def image_to_image(
                self,
                image_url: str,
                prompt: str,
                model: str | None = None,
                prefer_provider: str | None = None,
                count: int = 1,
                size: str | None = None,
                **_: str,
            ):
                return _DummyResp()

        class _DummyAIService:
            def __init__(self) -> None:
                self.ai_manager = _DummyAIManager()

            async def _persist_generated_image(
                self,
                image_data: str,
                *,
                ip_name: str,
                category: str,
                prefix: str,
                metadata: dict | None = None,
                require_upload: bool = False,
            ) -> dict:
                filename = "variant_test.png"
                return {
                    "local_file_path": f"/tmp/{filename}",
                    "relative_path": f"/uploads/{filename}",
                    "file_size": 1024,
                    "filename": filename,
                    "oss_url": "https://oss.example.com/ai-generated/virtual-ip/image/variant_test.png"
                    if require_upload
                    else None,
                    "oss_upload": {
                        "success": True,
                        "file_url": "https://oss.example.com/ai-generated/virtual-ip/image/variant_test.png",
                    }
                    if require_upload
                    else None,
                    "metadata": metadata or {},
                    "ip_name": ip_name,
                    "category": category,
                    "prefix": prefix,
                    "source_image": image_data,
                }

        dummy_service = _DummyAIService()
        monkeypatch.setattr(vip_images_module, "ai_service", dummy_service)
        # 避免真实文件系统依赖
        monkeypatch.setattr(vip_images_module.os.path, "exists", lambda _: True)
        monkeypatch.setattr(vip_images_module.os.path, "getsize", lambda _: 1024)

        response = client.post(
            f"/api/v1/virtual-ips/{virtual_ip.id}/images/{base_image.id}/variants",
            json=payload,
        )

        # 如果失败，在断言消息中带上响应内容便于调试
        assert response.status_code == 200, response.text
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == 1
        image_item = result[0]
        assert image_item["virtual_ip_id"] == virtual_ip.id
        assert image_item["file_path"].startswith("/uploads/")


@pytest.mark.integration
class TestStoryAPI:
    """故事API测试"""
    
    def test_create_story(self, client: TestClient, db_session: Session):
        """测试创建故事"""
        setup_factories(db_session)
        
        data = {
            "title": "Test Story",
            "genre": "Romance",
            "theme": "Love conquers all",
            "target_audience": "Young Adult",
            "duration_minutes": 120,
            "premise": "A test story premise",
            "synopsis": "A test story synopsis",
            "main_conflict": "Test conflict",
            "resolution": "Test resolution",
            "main_characters": [{"name": "Character1", "role": "protagonist"}],
            "character_relationships": {"Character1": {"Character2": "friend"}},
            "setting_time": "Modern",
            "setting_location": "New York",
            "world_building": "Test world building",
            "tags": ["test", "story"]
        }
        
        response = client.post("/api/v1/stories/", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["title"] == data["title"]
        assert result["genre"] == data["genre"]
        assert result["premise"] == data["premise"]
    
    def test_get_story(self, client: TestClient, db_session: Session):
        """测试获取故事"""
        setup_factories(db_session)
        
        story = StoryFactory()
        
        response = client.get(f"/api/v1/stories/{story.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == story.id
        assert result["title"] == story.title
        assert result["genre"] == story.genre
    
    def test_list_stories(self, client: TestClient, db_session: Session):
        """测试列出故事"""
        setup_factories(db_session)
        
        story1 = StoryFactory()
        story2 = StoryFactory()
        
        response = client.get("/api/v1/stories/")
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
        assert any(item["id"] == story1.id for item in result)
        assert any(item["id"] == story2.id for item in result)
    
    def test_generate_story_outline(self, client: TestClient, db_session: Session, mock_ai_service):
        """测试生成故事概要"""
        setup_factories(db_session)
        
        virtual_ip1 = VirtualIPFactory()
        virtual_ip2 = VirtualIPFactory()
        
        data = {
            "title": "Story Outline Title",
            "character_ids": [virtual_ip1.id, virtual_ip2.id],
            "genre": "Romance",
            "theme": "Love conquers all",
            "target_audience": "Young Adult",
            "duration_minutes": 120,
            "setting_time": "Modern",
            "setting_location": "New York",
        }
        
        response = client.post("/api/v1/stories/generate", json=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        story_payload = result["data"]
        assert story_payload["title"] == data["title"]
        extra_meta = story_payload.get("extra_metadata") or {}
        agent_run = extra_meta.get("agent_run") or {}
        # LangGraph / 管理器可能不同实现，这里仅校验字段存在与方法标记
        assert "generation_method" in agent_run
    
    def test_update_story(self, client: TestClient, db_session: Session):
        """测试更新故事"""
        setup_factories(db_session)
        
        story = StoryFactory()
        
        update_data = {
            "title": "Updated Story Title",
            "genre": "Action",
            "premise": "Updated premise",
            "synopsis": "Updated synopsis"
        }
        
        response = client.put(f"/api/v1/stories/{story.id}", json=update_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == update_data["title"]
        assert result["genre"] == update_data["genre"]
        assert result["premise"] == update_data["premise"]
    
    def test_delete_story(self, client: TestClient, db_session: Session):
        """测试删除故事"""
        setup_factories(db_session)
        
        story = StoryFactory()
        
        response = client.delete(f"/api/v1/stories/{story.id}")
        
        assert response.status_code == 204
        
        # 验证删除
        response = client.get(f"/api/v1/stories/{story.id}")
        assert response.status_code == 404


@pytest.mark.integration
class TestEpisodeAPI:
    """剧集API测试"""
    
    def test_create_episode(self, client: TestClient, db_session: Session):
        """测试创建剧集"""
        setup_factories(db_session)
        
        story = StoryFactory()
        
        data = {
            "story_id": story.id,
            "episode_number": 1,
            "title": "Test Episode",
            "summary": "Test episode summary",
            "duration_minutes": 15,
            "scene_descriptions": [{"scene": 1, "description": "Opening scene"}],
            "character_arcs": {"Character1": "Development arc"},
            "key_events": ["Event1", "Event2"],
            "emotional_beats": ["Happy", "Sad"],
            "scene_count": 5
        }
        
        response = client.post("/api/v1/episodes/", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["story_id"] == data["story_id"]
        assert result["episode_number"] == data["episode_number"]
        assert result["title"] == data["title"]
    
    def test_get_episode(self, client: TestClient, db_session: Session):
        """测试获取剧集"""
        setup_factories(db_session)
        
        episode = EpisodeFactory()
        
        response = client.get(f"/api/v1/episodes/{episode.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == episode.id
        assert result["title"] == episode.title
        assert result["story_id"] == episode.story_id
    
    def test_generate_episodes(self, client: TestClient, db_session: Session, mock_ai_service):
        """测试生成剧集"""
        setup_factories(db_session)
        
        story = StoryFactory()
        
        data = {
            "story_id": story.id,
            "episode_count": 3,
            "episode_duration": 15,
        }
        
        response = client.post("/api/v1/episodes/generate", json=data)
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == data["episode_count"]
        first = result[0]
        assert first["story_id"] == story.id
        extra_meta = first.get("extra_metadata") or {}
        agent_run = extra_meta.get("agent_run") or {}
        assert "generation_method" in agent_run


@pytest.mark.integration
class TestScriptAPI:
    """剧本API测试"""
    
    def test_create_script(self, client: TestClient, db_session: Session):
        """测试创建剧本"""
        setup_factories(db_session)
        
        episode = EpisodeFactory()
        
        data = {
            "episode_id": episode.id,
            "title": "Test Script",
            "content": "Test script content",
            "format_type": "standard",
            "scene_headings": ["INT. ROOM - DAY"],
            "character_list": ["Character1", "Character2"],
            "dialogue_count": 20,
            "action_count": 10,
            "word_count": 1000,
            "character_count": 5000
        }
        
        response = client.post("/api/v1/scripts/", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["episode_id"] == data["episode_id"]
        assert result["title"] == data["title"]
        assert result["content"] == data["content"]
    
    def test_get_script(self, client: TestClient, db_session: Session):
        """测试获取剧本"""
        setup_factories(db_session)
        
        script = ScriptFactory()
        
        response = client.get(f"/api/v1/scripts/{script.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == script.id
        assert result["title"] == script.title
        assert result["episode_id"] == script.episode_id
    
    def test_generate_script(self, client: TestClient, db_session: Session, mock_ai_service):
        """测试生成剧本"""
        setup_factories(db_session)
        
        episode = EpisodeFactory()
        
        data = {
            "episode_id": episode.id,
            "format_type": "screenplay",
            "language": "zh-CN",
            "dialogue_style": "natural",
            "scene_detail_level": "medium",
        }
        
        response = client.post("/api/v1/scripts/generate", json=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["episode_id"] == episode.id
        extra_meta = result.get("extra_metadata") or {}
        agent_run = extra_meta.get("agent_run") or {}
        assert "generation_method" in agent_run
    
    def test_export_script(self, client: TestClient, db_session: Session):
        """测试导出剧本"""
        setup_factories(db_session)
        
        script = ScriptFactory()
        
        # 测试导出为文本
        response = client.get(f"/api/v1/scripts/{script.id}/export?format=txt")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # 测试导出为PDF
        response = client.get(f"/api/v1/scripts/{script.id}/export?format=pdf")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


@pytest.mark.integration
class TestAPIValidation:
    """API验证测试"""
    
    def test_create_virtual_ip_validation(self, client: TestClient, db_session: Session):
        """测试虚拟IP创建验证"""
        # 测试缺少必需字段
        data = {
            "description": "Test description"
            # 缺少name字段
        }
        
        response = client.post("/api/v1/virtual-ips/", json=data)
        
        assert response.status_code == 422
        result = response.json()
        assert "detail" in result
    
    def test_create_story_validation(self, client: TestClient, db_session: Session):
        """测试故事创建验证"""
        # 测试无效的类型
        data = {
            "title": "Test Story",
            "genre": "Romance",
            "duration_minutes": "invalid"  # 应该是整数
        }
        
        response = client.post("/api/v1/stories/", json=data)
        
        assert response.status_code == 422
        result = response.json()
        assert "detail" in result
    
    def test_pagination(self, client: TestClient, db_session: Session):
        """测试分页"""
        setup_factories(db_session)
        
        # 创建多个虚拟IP
        for i in range(15):
            VirtualIPFactory()
        
        # 测试分页
        response = client.get("/api/v1/virtual-ips/?skip=0&limit=10")
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 10
        
        # 测试第二页
        response = client.get("/api/v1/virtual-ips/?skip=10&limit=10")
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 5
    
    def test_search_filtering(self, client: TestClient, db_session: Session):
        """测试搜索和过滤"""
        setup_factories(db_session)
        
        # 创建特定名称的虚拟IP
        VirtualIPFactory(name="SearchableIP")
        VirtualIPFactory(name="AnotherIP")
        
        # 测试搜索
        response = client.get("/api/v1/virtual-ips/?search=Searchable")
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["name"] == "SearchableIP"


@pytest.mark.integration
class TestAPIErrorHandling:
    """API错误处理测试"""
    
    def test_404_error(self, client: TestClient, db_session: Session):
        """测试404错误"""
        response = client.get("/api/v1/virtual-ips/999")
        
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
    
    def test_500_error_handling(self, client: TestClient, db_session: Session, mocker):
        """测试500错误处理"""
        # 模拟数据库错误
        mocker.patch('app.api.v1.endpoints.virtual_ips.get_virtual_ip', side_effect=Exception("Database error"))
        
        response = client.get("/api/v1/virtual-ips/1")
        
        assert response.status_code == 500
        result = response.json()
        assert "detail" in result
    
    def test_validation_error_details(self, client: TestClient, db_session: Session):
        """测试验证错误详情"""
        data = {
            "name": "",  # 空字符串
            "description": "A" * 1000,  # 太长
            "tags": "not_a_list"  # 错误类型
        }
        
        response = client.post("/api/v1/virtual-ips/", json=data)
        
        assert response.status_code == 422
        result = response.json()
        assert "detail" in result
        assert isinstance(result["detail"], list)
        assert len(result["detail"]) > 0


@pytest.mark.e2e
class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    def test_complete_story_creation_workflow(self, client: TestClient, db_session: Session, mock_ai_service):
        """测试完整的故事创建工作流"""
        setup_factories(db_session)
        
        # 1. 创建虚拟IP
        vip_data = {
            "name": "Test Character",
            "description": "A test character",
            "tags": ["test", "character"],
            "is_active": True
        }
        
        vip_response = client.post("/api/v1/virtual-ips/", json=vip_data)
        assert vip_response.status_code == 201
        virtual_ip = vip_response.json()
        
        # 2. 生成故事
        story_data = {
            "character_ids": [virtual_ip["id"]],
            "genre": "Romance",
            "theme": "Love conquers all",
            "target_audience": "Young Adult",
            "duration_minutes": 120,
            "setting_time": "Modern",
            "setting_location": "New York",
            "ai_service": "openai"
        }
        
        story_response = client.post("/api/v1/stories/generate", json=story_data)
        assert story_response.status_code == 200
        story_result = story_response.json()
        assert story_result["success"] is True
        
        # 3. 创建故事
        create_story_data = {
            "title": "Generated Story",
            "genre": "Romance",
            "premise": "Test premise",
            "synopsis": "Test synopsis",
            "main_characters": [{"name": "Character1"}],
            "character_relationships": {},
            "generation_params": {}
        }
        
        create_story_response = client.post("/api/v1/stories/", json=create_story_data)
        assert create_story_response.status_code == 201
        story = create_story_response.json()
        
        # 4. 生成剧集
        episode_data = {
            "story_id": story["id"],
            "episode_count": 2,
            "episode_duration": 15,
            "ai_service": "openai"
        }
        
        episode_response = client.post("/api/v1/episodes/generate", json=episode_data)
        assert episode_response.status_code == 200
        episode_result = episode_response.json()
        assert episode_result["success"] is True
        
        # 5. 创建剧集
        create_episode_data = {
            "story_id": story["id"],
            "episode_number": 1,
            "title": "Episode 1",
            "summary": "First episode",
            "duration_minutes": 15,
            "scene_descriptions": [],
            "character_arcs": {},
            "key_events": [],
            "emotional_beats": [],
            "generation_params": {}
        }
        
        create_episode_response = client.post("/api/v1/episodes/", json=create_episode_data)
        assert create_episode_response.status_code == 201
        episode = create_episode_response.json()
        
        # 6. 生成剧本
        script_data = {
            "episode_id": episode["id"],
            "format_type": "standard",
            "style_requirements": "Romantic and emotional",
            "ai_service": "openai"
        }
        
        script_response = client.post("/api/v1/scripts/generate", json=script_data)
        assert script_response.status_code == 200
        script_result = script_response.json()
        assert script_result["success"] is True
        
        # 7. 验证整个工作流
        story_detail = client.get(f"/api/v1/stories/{story['id']}")
        assert story_detail.status_code == 200
        
        episode_detail = client.get(f"/api/v1/episodes/{episode['id']}")
        assert episode_detail.status_code == 200 
