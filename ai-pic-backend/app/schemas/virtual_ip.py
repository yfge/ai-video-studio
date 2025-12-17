from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class VirtualIPImageBase(BaseModel):
    category: str
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = []
    prompt: Optional[str] = None
    ai_model: Optional[str] = None
    generation_params: Optional[Dict[str, Any]] = None
    is_default: bool = False
    is_public: bool = True


class VirtualIPImageCreate(VirtualIPImageBase):
    virtual_ip_id: int
    file_path: str
    oss_url: Optional[str] = None
    filename: Optional[str] = None
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = "image/png"
    metadata: Optional[Dict[str, Any]] = None


class VirtualIPImageUpdate(VirtualIPImageBase):
    pass


class VirtualIPImageResponse(VirtualIPImageBase):
    id: int
    business_id: str
    virtual_ip_id: int
    virtual_ip_business_id: Optional[str] = None
    filename: str
    original_filename: str
    file_path: str
    oss_url: Optional[str] = None
    file_size: int
    mime_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class VirtualIPBase(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    background_story: Optional[str] = None
    biography: Optional[str] = None
    style_prompt: Optional[str] = None
    style_reference_images: Optional[List[str]] = []
    voice_config: Optional[Dict[str, Any]] = None
    is_active: bool = True
    is_public: bool = False


class VirtualIPCreate(VirtualIPBase):
    pass


class VirtualIPUpdate(VirtualIPBase):
    pass


class VirtualIPResponse(VirtualIPBase):
    id: int
    business_id: str
    default_avatar_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    images: Optional[List[VirtualIPImageResponse]] = []

    class Config:
        from_attributes = True


class VirtualIPListResponse(BaseModel):
    virtual_ips: List[VirtualIPResponse]
    total: int
    page: int
    size: int


class VirtualIPAICreateRequest(BaseModel):
    """AI增强创建虚拟IP的请求"""

    name: str
    basic_info: Optional[str] = None  # 用户提供的基本信息
    style_preference: Optional[str] = None  # 风格偏好
    tags: Optional[List[str]] = []
    is_active: bool = True
    is_public: bool = False


class VirtualIPAIGenerationResponse(BaseModel):
    """AI生成内容的响应"""

    description: str
    background_story: str
    biography: str
    style_prompt: str


class AIGenerationDetails(BaseModel):
    """AI生成详情"""

    model: str
    temperature: float
    prompts_used: List[str]
    tokens_used: int
    generation_time: float
    steps: List[str]


class VirtualIPAIGenerationDetailedResponse(BaseModel):
    """AI生成内容的详细响应"""

    description: str
    background_story: str
    biography: str
    style_prompt: str
    generation_details: AIGenerationDetails


class VirtualIPAIGenerationRequest(BaseModel):
    """AI生成内容的请求"""

    name: str
    basic_info: Optional[str] = None
    style_preference: Optional[str] = None
    image_category: str = "portrait"
