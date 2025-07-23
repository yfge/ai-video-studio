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
    pass

class VirtualIPImageUpdate(VirtualIPImageBase):
    pass

class VirtualIPImageResponse(VirtualIPImageBase):
    id: int
    virtual_ip_id: int
    filename: str
    original_filename: str
    file_path: str
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
    style_prompt: Optional[str] = None
    style_reference_images: Optional[List[str]] = []
    is_active: bool = True
    is_public: bool = False

class VirtualIPCreate(VirtualIPBase):
    pass

class VirtualIPUpdate(VirtualIPBase):
    pass

class VirtualIPResponse(VirtualIPBase):
    id: int
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