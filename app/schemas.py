from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    client_name: str
    event_type: str
    event_date: date


class EventResponse(BaseModel):
    event_id: int

    model_config = ConfigDict(from_attributes=True)


class EventDetailResponse(BaseModel):
    event_id: int
    client_name: str
    event_type: str
    event_date: date
    created_at: datetime
    photo_count: int


class PhotoUploadResponse(BaseModel):
    photo_id: str
    event_id: int
    message: str
    original_s3_key: str
    polaroid_s3_key: str