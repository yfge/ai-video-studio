from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ImageBase(BaseModel):
    description: Optional[str] = None
    prompt: Optional[str] = None

class ImageCreate(ImageBase):
    pass

class ImageResponse(ImageBase):
    id: int
    business_id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ImageList(BaseModel):
    images: list[ImageResponse]
    total: int
    page: int
    size: int 
