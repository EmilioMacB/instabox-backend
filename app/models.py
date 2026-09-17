import uuid
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    client_name = Column(String(120), nullable=False)
    event_type = Column(String(60), nullable=False)
    event_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

    photos = relationship(
        "Photo",
        back_populates="event",
        cascade="all, delete-orphan"
    )


class Photo(Base):
    __tablename__ = "photos"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message = Column(String(255), nullable=False)
    original_s3_key = Column(String(255), nullable=False)
    polaroid_s3_key = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="photos")