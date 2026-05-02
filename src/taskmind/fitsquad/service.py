from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmind.fitsquad.models import EmailLog, Reservation, TravelPackage
from taskmind.fitsquad.schemas import ReservationCreate


def list_packages(session: Session) -> list[TravelPackage]:
    return list(session.scalars(select(TravelPackage).order_by(TravelPackage.id.asc())))


def get_package_by_slug(session: Session, slug: str) -> TravelPackage | None:
    return session.scalars(select(TravelPackage).where(TravelPackage.slug == slug)).first()


def list_reservations(session: Session) -> list[Reservation]:
    return list(session.scalars(select(Reservation).order_by(Reservation.created_at.desc())))


def get_reservation_by_code(session: Session, code: str) -> Reservation | None:
    return session.scalars(select(Reservation).where(Reservation.reservation_code == code)).first()


def remaining_spots(session: Session, travel_package: TravelPackage) -> int:
    held_statuses = {"pending", "confirmed"}
    reservations = session.scalars(
        select(Reservation).where(
            Reservation.package_id == travel_package.id,
            Reservation.reservation_status.in_(held_statuses),
        )
    ).all()
    used = sum(reservation.participants for reservation in reservations)
    return max(travel_package.capacity - used, 0)


def create_reservation(session: Session, travel_package: TravelPackage, payload: ReservationCreate) -> Reservation:
    if payload.payment_option not in {"deposit", "full"}:
        raise ValueError("Payment option must be 'deposit' or 'full'.")

    available = remaining_spots(session, travel_package)
    if payload.participants > available:
        raise ValueError(f"Only {available} spots remain for this package.")

    payment_status = "deposit_paid" if payload.payment_option == "deposit" else "fully_paid"
    reservation = Reservation(
        package_id=travel_package.id,
        client_name=payload.client_name.strip(),
        email=payload.email.strip(),
        phone=payload.phone.strip(),
        participants=payload.participants,
        payment_option=payload.payment_option,
        payment_status=payment_status,
        reservation_status="pending",
    )
    session.add(reservation)
    session.flush()

    confirmation_subject = f"FitSquad reservation confirmed for {travel_package.title}"
    confirmation_body = (
        f"Hi {reservation.client_name},\n\n"
        f"Your reservation for {travel_package.title} is recorded for {reservation.participants} participant(s).\n"
        f"Payment status: {reservation.payment_status.replace('_', ' ')}.\n"
        "Our team will follow up manually with any remaining logistics.\n"
    )
    payment_subject = f"FitSquad payment confirmation for {travel_package.title}"
    payment_body = (
        f"Payment option selected: {reservation.payment_option}.\n"
        f"Tracked payment status: {reservation.payment_status}.\n"
        "Remaining payment handling stays outside the system in Phase 1.\n"
    )

    session.add(
        EmailLog(
            reservation_id=reservation.id,
            email_type="reservation_confirmation",
            recipient=reservation.email,
            subject=confirmation_subject,
            body=confirmation_body,
        )
    )
    session.add(
        EmailLog(
            reservation_id=reservation.id,
            email_type="payment_confirmation",
            recipient=reservation.email,
            subject=payment_subject,
            body=payment_body,
        )
    )
    session.commit()
    session.refresh(reservation)
    return reservation


def update_reservation_status(session: Session, reservation_id: int, reservation_status: str) -> Reservation | None:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        return None
    if reservation_status not in {"pending", "confirmed", "cancelled"}:
        raise ValueError("Unsupported reservation status.")
    reservation.reservation_status = reservation_status
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation
