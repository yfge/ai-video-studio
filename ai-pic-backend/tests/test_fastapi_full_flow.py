import pytest
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.virtual_ip import VirtualIPImage, VirtualIP
from app.models.user import User
from app.core.security import get_password_hash

@pytest.mark.asyncio
async def test_fastapi_full_image_generation_flow(client, db_session, skip_if_no_openai):
    """测试FastAPI应用的完整图像生成流程"""
    
    print(f"\n🧪 测试FastAPI完整图像生成流程")
    
    # 0. 创建测试用户和虚拟IP
    print(f"   创建测试数据...")
    
    # 创建用户
    test_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("Ai7dio"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)
    print(f"   创建用户: {test_user.username}")
    
    # 创建虚拟IP
    test_virtual_ip = VirtualIP(
        name="小雅",
        description="一个活泼可爱的年轻女孩，充满好奇心和冒险精神",
        tags=["test", "ai"],
        background_story="这是一个测试用的虚拟IP角色",
        style_prompt="realistic, professional",
        is_active=True,
        is_public=False
    )
    db_session.add(test_virtual_ip)
    db_session.commit() 
    db_session.refresh(test_virtual_ip)
    print(f"   创建虚拟IP: {test_virtual_ip.name} (ID: {test_virtual_ip.id})")
    
    # 1. 登录获取认证头
    login_data = {
        "username": "admin",
        "password": "Ai7dio"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    print(f"   用户登录: {response.status_code}")
    assert response.status_code == 200, f"登录失败: {response.text}"
    
    token = response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    
    virtual_ip_id = test_virtual_ip.id
    virtual_ip_name = test_virtual_ip.name
    
    # 2. 检查生成前的图像数量
    initial_count = db_session.query(VirtualIPImage).filter(
        VirtualIPImage.virtual_ip_id == virtual_ip_id
    ).count()
    print(f"   生成前图像数量: {initial_count}")
    
    # 3. 调用图像生成API
    generation_data = {
        "style": "realistic",
        "category": "portrait", 
        "model": "dall-e-3",
        "additional_prompts": "test image generation",
        "is_default": False
    }
    
    print(f"   开始调用图像生成API...")
    print(f"   参数: {generation_data}")
    
    response = client.post(
        f"/api/v1/virtual-ips/{virtual_ip_id}/images/generate",
        data=generation_data,
        headers=auth_headers,
        timeout=120  # 设置120秒超时
    )
    
    print(f"   API响应状态: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   API错误响应: {response.text}")
        # 如果是500错误，不要直接失败，而是显示详细信息
        if response.status_code == 500:
            error_detail = response.json().get("detail", "未知错误")
            print(f"   错误详情: {error_detail}")
        
    assert response.status_code == 200, f"API调用失败: {response.status_code} - {response.text}"
    
    result = response.json()
    print(f"   API响应字段: {list(result.keys())}")
    
    # 4. 验证响应数据
    assert "id" in result, "响应应包含图像ID"
    assert "file_path" in result, "响应应包含文件路径"
    assert "filename" in result, "响应应包含文件名"
    
    image_id = result["id"]
    file_path = result["file_path"]
    filename = result["filename"]
    
    print(f"   生成的图像ID: {image_id}")
    print(f"   文件路径: {file_path}")
    print(f"   文件名: {filename}")
    
    # 5. 检查数据库中的记录
    final_count = db_session.query(VirtualIPImage).filter(
        VirtualIPImage.virtual_ip_id == virtual_ip_id
    ).count()
    print(f"   生成后图像数量: {final_count}")
    assert final_count == initial_count + 1, "数据库中应该新增一条图像记录"
    
    # 6. 检查具体的数据库记录
    db_image = db_session.query(VirtualIPImage).filter(
        VirtualIPImage.id == image_id
    ).first()
    
    assert db_image is not None, "数据库中应该找到对应的图像记录"
    print(f"   数据库记录: ID={db_image.id}, 路径={db_image.file_path}")
    print(f"   提示词: {db_image.prompt[:100]}...")
    print(f"   AI模型: {db_image.ai_model}")
    print(f"   文件大小: {db_image.file_size} bytes")
    
    # 7. 检查本地文件是否存在
    if file_path.startswith("/uploads/"):
        # 相对路径，拼接完整路径
        full_file_path = os.path.join("./uploads", filename)
    else:
        full_file_path = file_path
    
    print(f"   检查本地文件: {full_file_path}")
    file_exists = os.path.exists(full_file_path)
    print(f"   文件存在: {file_exists}")
    
    if file_exists:
        file_size = os.path.getsize(full_file_path)
        print(f"   实际文件大小: {file_size} bytes")
        assert file_size > 1000, "生成的图像文件应该有实质内容"
        assert file_size == db_image.file_size, "数据库记录的文件大小应与实际文件大小匹配"
    else:
        print(f"   ⚠️ 本地文件不存在，但数据库有记录")
    
    # 8. 检查OSS上传状态（如果有metadata）
    if db_image.metadata and "oss_upload" in db_image.metadata:
        oss_result = db_image.metadata["oss_upload"]
        print(f"   OSS上传结果: {oss_result}")
    
    print(f"   ✅ 全流程测试完成")