from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

CanvasAccessRole = Literal["owner", "viewer", "commenter", "editor", "approver"]
CanvasCommentTarget = Literal["node", "candidate", "edge", "section"]


class ProductionCanvasCollaborator(BaseModel):
    user_id: int = Field(..., ge=1)
    username: str
    role: Literal["viewer", "commenter", "editor", "approver"]
    added_by: int = Field(..., ge=1)
    added_at: datetime


class ProductionCanvasComment(BaseModel):
    comment_id: str = Field(..., min_length=1, max_length=32)
    target_type: CanvasCommentTarget
    target_id: str = Field(..., min_length=1, max_length=160)
    body: str = Field(..., min_length=1, max_length=2000)
    author_id: int = Field(..., ge=1)
    author_username: str
    created_at: datetime


class ProductionCanvasActivity(BaseModel):
    activity_id: str = Field(..., min_length=1, max_length=32)
    action: str = Field(..., min_length=1, max_length=80)
    actor_id: int = Field(..., ge=1)
    actor_username: str
    target_type: str | None = Field(None, max_length=40)
    target_id: str | None = Field(None, max_length=160)
    detail: str | None = Field(None, max_length=500)
    created_at: datetime


class ProductionCanvasCollaborationResponse(BaseModel):
    access_role: CanvasAccessRole
    collaborators: list[ProductionCanvasCollaborator] = Field(default_factory=list)
    comments: list[ProductionCanvasComment] = Field(default_factory=list)
    activity: list[ProductionCanvasActivity] = Field(default_factory=list)


class ProductionCanvasCollaboratorRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    role: Literal["viewer", "commenter", "editor", "approver"]

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("username must not be blank")
        return value


class ProductionCanvasCommentRequest(BaseModel):
    target_type: CanvasCommentTarget
    target_id: str = Field(..., min_length=1, max_length=160)
    body: str = Field(..., min_length=1, max_length=2000)

    @field_validator("target_id", "body")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value
