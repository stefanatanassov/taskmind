from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _reservation_code() -> str:
    return uuid4().hex[:10].upper()


class Base(DeclarativeBase):
    pass


class TravelPackage(Base):
    __tablename__ = "fitsquad_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    dates_label: Mapped[str] = mapped_column(String(255), nullable=False)
    price_full_eur: Mapped[int] = mapped_column(Integer, nullable=False)
    deposit_eur: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    hero_image: Mapped[str] = mapped_column(Text, nullable=False)
    gallery_images: Mapped[list[str]] = mapped_column(JSON, default=list)
    itinerary_days: Mapped[list[dict]] = mapped_column(JSON, default=list)
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="travel_package")


class Reservation(Base):
    __tablename__ = "fitsquad_reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reservation_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, default=_reservation_code)
    package_id: Mapped[int] = mapped_column(ForeignKey("fitsquad_packages.id"), nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(80), nullable=False)
    participants: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_option: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False)
    reservation_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    travel_package: Mapped[TravelPackage] = relationship(back_populates="reservations")
    emails: Mapped[list["EmailLog"]] = relationship(back_populates="reservation")


class EmailLog(Base):
    __tablename__ = "fitsquad_email_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("fitsquad_reservations.id"), nullable=False)
    email_type: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    reservation: Mapped[Reservation] = relationship(back_populates="emails")
