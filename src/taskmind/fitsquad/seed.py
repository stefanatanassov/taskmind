from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmind.fitsquad.models import TravelPackage


PACKAGE_SEEDS = [
    {
        "slug": "bansko-performance-camp",
        "title": "Bansko Performance Camp",
        "location": "Bansko, Bulgaria",
        "summary": "A mountain-based training and recovery week for active travelers.",
        "description": (
            "A seven-day camp that combines guided workouts, recovery sessions, "
            "and curated local experiences for small groups."
        ),
        "dates_label": "14 Sep 2026 - 20 Sep 2026",
        "price_full_eur": 940,
        "deposit_eur": 240,
        "capacity": 18,
        "hero_image": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1501554728187-ce583db33af7?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1200&q=80",
        ],
        "itinerary_days": [
            {"day": "Day 1", "title": "Arrival and check-in", "details": "Airport pickup, chalet check-in, and welcome dinner."},
            {"day": "Day 2", "title": "Mobility and trails", "details": "Morning mobility session followed by guided mountain hiking."},
            {"day": "Day 3", "title": "Strength focus", "details": "Partner strength session, recovery lunch, and spa access."},
            {"day": "Day 4", "title": "Adventure day", "details": "Half-day local excursion with optional bike ride."},
            {"day": "Day 5", "title": "Performance workshop", "details": "Nutrition talk, circuit training, and team dinner."},
            {"day": "Day 6", "title": "Open training", "details": "Flexible skill sessions, photo content, and local market visit."},
            {"day": "Day 7", "title": "Wrap-up", "details": "Closing brunch and departures."},
        ],
    },
    {
        "slug": "thassos-reset-weekend",
        "title": "Thassos Reset Weekend",
        "location": "Thassos, Greece",
        "summary": "A short-format seaside reset with movement, food, and community.",
        "description": "A four-day wellness retreat designed for small teams and solo travelers who want a lighter schedule.",
        "dates_label": "08 Oct 2026 - 11 Oct 2026",
        "price_full_eur": 520,
        "deposit_eur": 150,
        "capacity": 12,
        "hero_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1473116763249-2faaef81ccda?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1493558103817-58b2924bce98?auto=format&fit=crop&w=1200&q=80",
        ],
        "itinerary_days": [
            {"day": "Day 1", "title": "Arrival and sunset flow", "details": "Coastal check-in and light evening session."},
            {"day": "Day 2", "title": "Beach training", "details": "Morning conditioning, brunch, and free swim block."},
            {"day": "Day 3", "title": "Island loop", "details": "Boat outing, recovery session, and shared dinner."},
            {"day": "Day 4", "title": "Departure", "details": "Closing breakfast and return transfers."},
        ],
    },
]


def seed_packages(session: Session) -> None:
    existing = session.scalars(select(TravelPackage.id).limit(1)).first()
    if existing is not None:
        return

    for payload in PACKAGE_SEEDS:
        session.add(TravelPackage(**payload))
    session.commit()
