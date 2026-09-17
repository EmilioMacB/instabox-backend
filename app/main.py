import uuid
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.database import get_db
from app.models import Event, Photo
from app.schemas import EventCreate, EventResponse, EventDetailResponse, PhotoUploadResponse
from app.image_service import resize_original_image, create_polaroid
from app.s3_service import upload_bytes_to_s3, create_zip_package

app = FastAPI(
    title="InstaBox Backend API",
    description="Servicio backend para procesamiento y empaquetado de fotos Polaroid de eventos.",
    version="1.0.0"
)


class FinishRequest(BaseModel):
    event_id: int


@app.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    new_event = Event(
        client_name=payload.client_name,
        event_type=payload.event_type,
        event_date=payload.event_date
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return EventResponse(event_id=new_event.id)


@app.post("/upload", response_model=PhotoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    event_id: int = Form(...),
    message: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El evento con ID {event_id} no existe."
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo proporcionado está vacío."
        )

    photo_uuid = str(uuid.uuid4())
    original_key = f"pictures/{photo_uuid}.jpg"
    polaroid_key = f"polaroids/{photo_uuid}.png"

    # 1. Redimensionar foto a 128x128 y subir a pictures/
    resized_bytes = resize_original_image(file_bytes)
    upload_bytes_to_s3(resized_bytes, original_key, "image/jpeg")

    # 2. Componer marco Polaroid y subir a polaroids/
    polaroid_bytes = create_polaroid(file_bytes, message)
    upload_bytes_to_s3(polaroid_bytes, polaroid_key, "image/png")

    # 3. Guardar registro en RDS
    new_photo = Photo(
        id=photo_uuid,
        event_id=event_id,
        message=message,
        original_s3_key=original_key,
        polaroid_s3_key=polaroid_key
    )
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)

    return PhotoUploadResponse(
        photo_id=new_photo.id,
        event_id=new_photo.event_id,
        message=new_photo.message,
        original_s3_key=new_photo.original_s3_key,
        polaroid_s3_key=new_photo.polaroid_s3_key
    )


@app.get("/events/{event_id}", response_model=EventDetailResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El evento con ID {event_id} no existe."
        )

    photo_count = db.query(func.count(Photo.id)).filter(Photo.event_id == event_id).scalar() or 0

    return EventDetailResponse(
        event_id=event.id,
        client_name=event.client_name,
        event_type=event.event_type,
        event_date=event.event_date,
        created_at=event.created_at,
        photo_count=photo_count
    )


@app.post("/finish")
def finish_event(payload: FinishRequest, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == payload.event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El evento con ID {payload.event_id} no existe."
        )

    photos = db.query(Photo).filter(Photo.event_id == payload.event_id).all()
    if not photos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El evento {payload.event_id} no tiene fotos asociadas para generar el álbum."
        )

    polaroid_keys = [photo.polaroid_s3_key for photo in photos]
    zip_buffer = create_zip_package(polaroid_keys)

    filename = f"polaroids_event_{payload.event_id}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )