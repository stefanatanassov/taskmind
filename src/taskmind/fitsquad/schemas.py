from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReservationCreate(BaseModel):
    client_name: str
    email: str
    phone: str
    participants: int = Field(ge=1, le=12)
    payment_option: str


class ReservationStatusUpdate(BaseModel):
    reservation_status: str


class PackageRead(BaseModel):
    slug: str
    title: str
    location: str
    summary: str
    description: str
    dates_label: str
    price_full_eur: int
    deposit_eur: int
    capacity: int
    hero_image: str
    gallery_images: list[str]
    itinerary_days: list[dict]
    remaining_spots: int


class ReservationRead(BaseModel):
    id: int
    reservation_code: str
    package_slug: str
    package_title: str
    client_name: str
    email: str
    phone: str
    participants: int
    payment_option: str
    payment_status: str
    reservation_status: str
    created_at: datetime


class EmailLogRead(BaseModel):
    email_type: str
    recipient: str
    subject: str
    body: str
    created_at: datetime
