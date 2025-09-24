"""
提示词管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.models.user import User
from app.core.middleware import get_current_active_user
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate, PromptCategory
from pydantic import BaseModel

router = APIRouter()

class PromptTemplateInfo(BaseModel):
    """提示词模板信息"""
    name: str
    description: str
    category: str
    version: str
    author: str
    variables: List[str]
    created_at: str
    updated_at: str

class PromptRenderRequest(BaseModel):
    """提示词渲染请求"""
    template_name: str
    variables: Dict[str, Any]

class PromptRenderResponse(BaseModel):
    """提示词渲染响应"""
    rendered_prompt: str
    template_name: str
    validation_result: Dict[str, Any]

class PromptCreateRequest(BaseModel):
    """创建提示词模板请求"""
    template_name: str
    content: str
    metadata: Dict[str, Any]

@router.get("/templates", response_model=List[PromptTemplateInfo])
async def list_templates(
    category: Optional[str] = Query(None, description="模板类别过滤"),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有可用的提示词模板"""
    try:
        templates = prompt_manager.list_templates(category)
        return [
            PromptTemplateInfo(
                name=template['name'],
                description=template['description'],
                category=template['category'],
                version=template['version'],
                author=template['author'],
                variables=template['variables'],
                created_at=template.get('created_at', ''),
                updated_at=template.get('updated_at', '')
            )
            for template in templates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")

@router.get("/categories")
async def list_categories(
    current_user: User = Depends(get_current_active_user)
):
    """获取所有模板类别"""
    try:
        categories = prompt_manager.get_categories()
        return {
            "success": True,
            "data": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取类别列表失败: {str(e)}")

@router.get("/templates/{template_name}")
async def get_template_info(
    template_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取指定模板的详细信息"""
    try:
        info = prompt_manager.get_template_info(template_name)
        return {
            "success": True,
            "data": info
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"模板不存在: {str(e)}")

@router.post("/render", response_model=PromptRenderResponse)
async def render_prompt(
    request: PromptRenderRequest,
    current_user: User = Depends(get_current_active_user)
):
    """渲染提示词模板"""
    try:
        # 验证模板变量
        validation_result = prompt_manager.validate_template(
            request.template_name, 
            request.variables
        )
        
        if not validation_result['valid']:
            raise HTTPException(
                status_code=400,
                detail=f"模板变量验证失败: {validation_result}"
            )
        
        # 渲染提示词
        rendered_prompt = prompt_manager.render_prompt(
            request.template_name,
            request.variables
        )
        
        return PromptRenderResponse(
            rendered_prompt=rendered_prompt,
            template_name=request.template_name,
            validation_result=validation_result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"渲染失败: {str(e)}")

@router.post("/templates")
async def create_template(
    request: PromptCreateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """创建新的提示词模板"""
    try:
        success = prompt_manager.create_template(
            request.template_name,
            request.content,
            request.metadata
        )
        
        if success:
            return {
                "success": True,
                "message": f"模板 {request.template_name} 创建成功"
            }
        else:
            raise HTTPException(status_code=500, detail="模板创建失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")

@router.post("/validate")
async def validate_template_variables(
    template_name: str,
    variables: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """验证模板变量"""
    try:
        validation_result = prompt_manager.validate_template(template_name, variables)
        return {
            "success": True,
            "data": validation_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")

# 预定义的提示词模板枚举端点
@router.get("/enums/templates")
async def get_template_enums():
    """获取所有预定义的模板枚举"""
    templates = [
        {
            "name": template.value,
            "display_name": template.name,
            "category": template.name.split('_')[0].lower()
        }
        for template in PromptTemplate
    ]
    return {
        "success": True,
        "data": templates
    }

@router.get("/enums/categories")
async def get_category_enums():
    """获取所有预定义的类别枚举"""
    categories = [
        {
            "name": category.value,
            "display_name": category.name
        }
        for category in PromptCategory
    ]
    return {
        "success": True,
        "data": categories
    }

# 特定工作流的提示词生成API
@router.post("/generate/character")
async def generate_character_prompt(
    name: str,
    description: Optional[str] = None,
    age: Optional[str] = None,
    gender: Optional[str] = None,
    personality_traits: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user)
):
    """生成角色创建提示词"""
    try:
        variables = {
            "name": name,
            "description": description,
            "age": age,
            "gender": gender,
            "personality_traits": personality_traits or []
        }
        
        prompt = prompt_manager.render_prompt(
            PromptTemplate.VIRTUAL_IP_CREATION.value,
            variables
        )
        
        return {
            "success": True,
            "data": {
                "prompt": prompt,
                "template": PromptTemplate.VIRTUAL_IP_CREATION.value,
                "variables": variables
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成角色提示词失败: {str(e)}")

@router.post("/generate/story")
async def generate_story_prompt(
    title: str,
    genre: str,
    characters: List[Dict[str, Any]],
    theme: Optional[str] = None,
    target_audience: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """生成故事大纲提示词"""
    try:
        variables = {
            "title": title,
            "genre": genre,
            "characters": characters,
            "theme": theme,
            "target_audience": target_audience
        }
        
        prompt = prompt_manager.render_prompt(
            PromptTemplate.STORY_OUTLINE.value,
            variables
        )
        
        return {
            "success": True,
            "data": {
                "prompt": prompt,
                "template": PromptTemplate.STORY_OUTLINE.value,
                "variables": variables
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成故事提示词失败: {str(e)}")

@router.post("/generate/image")
async def generate_image_prompt(
    character_name: str,
    style: str,
    category: str,
    character_description: Optional[str] = None,
    additional_prompts: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user)
):
    """生成图像生成提示词"""
    try:
        variables = {
            "character_name": character_name,
            "character_description": character_description,
            "style": style,
            "category": category,
            "additional_prompts": additional_prompts or [],
            "is_default": category == "portrait"
        }
        
        prompt = prompt_manager.render_prompt(
            PromptTemplate.IMAGE_GENERATION.value,
            variables
        )
        
        return {
            "success": True,
            "data": {
                "prompt": prompt,
                "template": PromptTemplate.IMAGE_GENERATION.value,
                "variables": variables
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成图像提示词失败: {str(e)}")