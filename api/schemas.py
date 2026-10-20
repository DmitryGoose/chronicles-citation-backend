from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChronicleListItem(BaseModel):
    id: int
    name: str
    short_description: str | None
    authorship_year: int | None
    start_year: int | None
    image_url: str
    video_url: str
    is_owner: int = Field(ge=0, le=1)


class ChronicleFeedItem(ChronicleListItem):
    likes_count: int
    is_liked: int = Field(ge=0, le=1)


class ChronicleDraft(BaseModel):
    id: int
    name: str
    short_description: str | None
    authorship_year: int | None
    start_year: int | None
    image_url: str
    video_url: str
    created_at: datetime


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PublishChronicleRequest(StrictRequest):
    short_description: str = Field(min_length=1)
    authorship_year: int = Field(ge=1, le=2100)
    start_year: int = Field(ge=1, le=2100)


class LikeRequest(StrictRequest):
    value: int = Field(ge=0, le=1)


class UserRegistrationRequest(StrictRequest):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class UserAuthenticationRequest(StrictRequest):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str


class AuthenticationResponse(UserResponse):
    message: str
    expires_in: int


class MessageResponse(BaseModel):
    message: str
