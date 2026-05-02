from __future__ import annotations

import html

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from taskmind.fitsquad.db import SessionLocal
from taskmind.fitsquad.models import EmailLog, Reservation
from taskmind.fitsquad.schemas import ReservationCreate, ReservationStatusUpdate
from taskmind.fitsquad.service import (
    create_reservation,
    get_package_by_slug,
    get_reservation_by_code,
    list_packages,
    list_reservations,
    remaining_spots,
    update_reservation_status,
)

router = APIRouter(prefix="/fitsquad", tags=["fitsquad"])


def euro(amount: int) -> str:
    return f"EUR {amount}"


def layout(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)}</title>
    <style>
      :root {{
        --bg: #f5efe4;
        --panel: rgba(255,255,255,.78);
        --line: rgba(22,42,32,.12);
        --text: #182117;
        --muted: #526155;
        --brand: #1f6b52;
        --accent: #d78d37;
        --soft: #e8dac4;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(215,141,55,.18), transparent 28%),
          radial-gradient(circle at top right, rgba(31,107,82,.18), transparent 26%),
          linear-gradient(180deg, #f7f2e8 0%, var(--bg) 100%);
      }}
      a {{ color: inherit; text-decoration: none; }}
      .wrap {{ max-width: 1180px; margin: 0 auto; padding: 28px 18px 60px; }}
      .nav {{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:28px; }}
      .nav-links {{ display:flex; gap:14px; flex-wrap:wrap; font-family: ui-sans-serif, system-ui, sans-serif; }}
      .brand {{ font-size: 28px; letter-spacing: .03em; }}
      .hero {{
        display:grid;
        grid-template-columns: 1.15fr .85fr;
        gap: 20px;
        align-items: stretch;
        margin-bottom: 28px;
      }}
      .panel {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 24px;
        backdrop-filter: blur(10px);
        box-shadow: 0 14px 40px rgba(20,30,25,.08);
      }}
      .hero-copy {{ padding: 32px; }}
      .eyebrow {{
        display:inline-block;
        margin-bottom:12px;
        padding: 8px 12px;
        border-radius: 999px;
        font-family: ui-sans-serif, system-ui, sans-serif;
        background: rgba(31,107,82,.08);
        color: var(--brand);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: .14em;
      }}
      h1, h2, h3 {{ margin: 0 0 12px; line-height: 1.05; }}
      h1 {{ font-size: clamp(40px, 6vw, 72px); }}
      h2 {{ font-size: clamp(28px, 4vw, 44px); }}
      h3 {{ font-size: 24px; }}
      p, li {{ line-height: 1.65; color: var(--muted); }}
      .hero-image {{
        min-height: 320px;
        border-radius: 24px;
        background-size: cover;
        background-position: center;
        position: relative;
        overflow: hidden;
      }}
      .hero-image::after {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,.35) 100%);
      }}
      .grid {{
        display:grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 18px;
      }}
      .card {{ padding: 20px; }}
      .package-image {{
        height: 220px;
        border-radius: 18px;
        background-size: cover;
        background-position: center;
        margin-bottom: 16px;
      }}
      .meta {{
        display:flex;
        gap:10px;
        flex-wrap:wrap;
        font-family: ui-sans-serif, system-ui, sans-serif;
        font-size: 13px;
        color: var(--muted);
      }}
      .pill {{
        display:inline-flex;
        align-items:center;
        gap:6px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,.82);
        border: 1px solid var(--line);
      }}
      .cta-row {{ display:flex; gap:12px; flex-wrap:wrap; margin-top: 18px; }}
      .button {{
        display:inline-flex;
        align-items:center;
        justify-content:center;
        gap:8px;
        border-radius: 999px;
        padding: 12px 18px;
        border: 1px solid var(--brand);
        background: var(--brand);
        color: white;
        font-family: ui-sans-serif, system-ui, sans-serif;
        font-weight: 600;
        cursor: pointer;
      }}
      .button.secondary {{
        background: transparent;
        color: var(--brand);
      }}
      .section {{ margin-top: 26px; }}
      .detail-grid {{
        display:grid;
        grid-template-columns: 1.2fr .8fr;
        gap: 20px;
      }}
      .stack {{ display:grid; gap:16px; }}
      .gallery {{
        display:grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
      }}
      .gallery-item {{
        min-height: 160px;
        border-radius: 16px;
        background-size: cover;
        background-position: center;
      }}
      .stats {{
        display:grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
      }}
      .stat {{
        padding: 16px;
        border-radius: 16px;
        background: rgba(31,107,82,.06);
        border: 1px solid var(--line);
      }}
      .stat strong {{
        display:block;
        margin-top: 6px;
        color: var(--text);
        font-size: 22px;
      }}
      label {{
        display:block;
        margin-bottom: 6px;
        font-family: ui-sans-serif, system-ui, sans-serif;
        font-size: 13px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: .08em;
      }}
      input, select, textarea {{
        width: 100%;
        border-radius: 14px;
        border: 1px solid var(--line);
        padding: 12px 14px;
        font-family: ui-sans-serif, system-ui, sans-serif;
        background: rgba(255,255,255,.92);
      }}
      .form-grid {{
        display:grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }}
      .full {{ grid-column: 1 / -1; }}
      .notice {{
        padding: 14px 16px;
        border-radius: 16px;
        font-family: ui-sans-serif, system-ui, sans-serif;
        background: rgba(215,141,55,.14);
        border: 1px solid rgba(215,141,55,.25);
        color: #70440e;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }}
      th, td {{
        padding: 12px 10px;
        border-bottom: 1px solid var(--line);
        text-align: left;
        vertical-align: top;
      }}
      th {{
        color: var(--muted);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: .08em;
      }}
      .status {{
        font-family: ui-sans-serif, system-ui, sans-serif;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: .08em;
        color: var(--brand);
      }}
      @media (max-width: 900px) {{
        .hero, .detail-grid {{ grid-template-columns: 1fr; }}
        .gallery {{ grid-template-columns: 1fr; }}
        .form-grid {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="nav">
        <a class="brand" href="/fitsquad">FitSquad</a>
        <div class="nav-links">
          <a href="/fitsquad">Trips</a>
          <a href="/fitsquad/admin">Admin</a>
        </div>
      </div>
      {body}
    </div>
  </body>
</html>"""
    )


def serialize_package(travel_package, remaining: int) -> dict:
    return {
        "slug": travel_package.slug,
        "title": travel_package.title,
        "location": travel_package.location,
        "summary": travel_package.summary,
        "description": travel_package.description,
        "dates_label": travel_package.dates_label,
        "price_full_eur": travel_package.price_full_eur,
        "deposit_eur": travel_package.deposit_eur,
        "capacity": travel_package.capacity,
        "hero_image": travel_package.hero_image,
        "gallery_images": travel_package.gallery_images,
        "itinerary_days": travel_package.itinerary_days,
        "remaining_spots": remaining,
    }


def serialize_reservation(reservation: Reservation) -> dict:
    return {
        "id": reservation.id,
        "reservation_code": reservation.reservation_code,
        "package_slug": reservation.travel_package.slug,
        "package_title": reservation.travel_package.title,
        "client_name": reservation.client_name,
        "email": reservation.email,
        "phone": reservation.phone,
        "participants": reservation.participants,
        "payment_option": reservation.payment_option,
        "payment_status": reservation.payment_status,
        "reservation_status": reservation.reservation_status,
        "created_at": reservation.created_at.isoformat(),
    }


@router.get("/", response_class=HTMLResponse)
def fitsquad_home() -> HTMLResponse:
    with SessionLocal() as session:
        packages = list_packages(session)
        cards = []
        for travel_package in packages:
            cards.append(
                f"""
                <article class="panel card">
                  <div class="package-image" style="background-image:url('{html.escape(travel_package.hero_image)}')"></div>
                  <div class="meta">
                    <span class="pill">{html.escape(travel_package.location)}</span>
                    <span class="pill">{html.escape(travel_package.dates_label)}</span>
                    <span class="pill">{remaining_spots(session, travel_package)} spots left</span>
                  </div>
                  <h3 style="margin-top:16px;">{html.escape(travel_package.title)}</h3>
                  <p>{html.escape(travel_package.summary)}</p>
                  <div class="cta-row">
                    <a class="button" href="/fitsquad/packages/{html.escape(travel_package.slug)}">View package</a>
                    <span class="pill">{euro(travel_package.deposit_eur)} deposit</span>
                    <span class="pill">{euro(travel_package.price_full_eur)} full</span>
                  </div>
                </article>
                """
            )

    body = f"""
      <section class="hero">
        <div class="panel hero-copy">
          <span class="eyebrow">Phase 1 MVP</span>
          <h1>Trips people can book without the rest of the machine.</h1>
          <p>
            FitSquad Phase 1 is deliberately narrow: fixed travel packages, basic reservation flow,
            deposit-or-full payment choice, simple availability protection, and a minimal admin view.
          </p>
          <div class="cta-row">
            <a class="button" href="/fitsquad/admin">Open admin view</a>
            <a class="button secondary" href="#packages">Browse packages</a>
          </div>
        </div>
        <div class="hero-image panel" style="background-image:url('https://images.unsplash.com/photo-1517639493569-5666a7b2f494?auto=format&fit=crop&w=1600&q=80')"></div>
      </section>
      <section class="section">
        <div class="panel card">
          <h2 id="packages">Current packages</h2>
          <p>Fixed inventory, no multi-step booking maze, no hidden scope.</p>
          <div class="grid">{''.join(cards)}</div>
        </div>
      </section>
    """
    return layout("FitSquad Trips", body)


@router.get("/packages/{slug}", response_class=HTMLResponse)
def package_detail(slug: str) -> HTMLResponse:
    with SessionLocal() as session:
        travel_package = get_package_by_slug(session, slug)
        if travel_package is None:
            raise HTTPException(status_code=404, detail="Package not found")
        remaining = remaining_spots(session, travel_package)
        is_sold_out = remaining <= 0
        participant_input_max = max(1, remaining)
        itinerary = "".join(
            f"<li><strong>{html.escape(item['day'])}:</strong> {html.escape(item['title'])} — {html.escape(item['details'])}</li>"
            for item in travel_package.itinerary_days
        )
        gallery = "".join(
            f"<div class='gallery-item' style=\"background-image:url('{html.escape(image)}')\"></div>"
            for image in travel_package.gallery_images
        )

    body = f"""
      <section class="detail-grid">
        <div class="stack">
          <div class="panel hero-copy">
            <span class="eyebrow">{html.escape(travel_package.location)}</span>
            <h2>{html.escape(travel_package.title)}</h2>
            <p>{html.escape(travel_package.description)}</p>
            <div class="stats">
              <div class="stat"><span class="status">Dates</span><strong>{html.escape(travel_package.dates_label)}</strong></div>
              <div class="stat"><span class="status">Spots left</span><strong>{remaining}</strong></div>
              <div class="stat"><span class="status">Deposit</span><strong>{euro(travel_package.deposit_eur)}</strong></div>
              <div class="stat"><span class="status">Full price</span><strong>{euro(travel_package.price_full_eur)}</strong></div>
            </div>
          </div>
          <div class="panel card">
            <h3>Itinerary</h3>
            <ul>{itinerary}</ul>
          </div>
          <div class="panel card">
            <h3>Gallery</h3>
            <div class="gallery">{gallery}</div>
          </div>
        </div>
        <div class="stack">
          <div class="panel card">
            <h3>Reserve a spot</h3>
            <p>This Phase 1 flow captures the reservation and tracks the payment choice in one step.</p>
            <div class="notice">Remaining payments after a deposit stay outside the system in Phase 1.</div>
            <div class="form-grid" style="margin-top:16px;">
              <div class="full">
                <label for="client_name">Name</label>
                <input id="client_name" />
              </div>
              <div>
                <label for="email">Email</label>
                <input id="email" type="email" />
              </div>
              <div>
                <label for="phone">Phone</label>
                <input id="phone" />
              </div>
              <div>
                <label for="participants">Participants</label>
                <input id="participants" type="number" min="1" max="{participant_input_max}" value="1" {'disabled' if is_sold_out else ''} />
              </div>
              <div>
                <label for="payment_option">Payment option</label>
                <select id="payment_option" {'disabled' if is_sold_out else ''}>
                  <option value="deposit">Deposit now ({euro(travel_package.deposit_eur)})</option>
                  <option value="full">Pay full amount ({euro(travel_package.price_full_eur)})</option>
                </select>
              </div>
            </div>
            <div class="cta-row">
              <button class="button" type="button" onclick="submitReservation()" {'disabled' if is_sold_out else ''}>Reserve</button>
            </div>
            <p id="reservation-message" class="notice" style="display:{'block' if is_sold_out else 'none'};">{'This package is currently sold out.' if is_sold_out else ''}</p>
          </div>
        </div>
      </section>
      <script>
        async function submitReservation() {{
          const payload = {{
            client_name: document.getElementById('client_name').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            participants: Number(document.getElementById('participants').value),
            payment_option: document.getElementById('payment_option').value
          }};
          const response = await fetch('/fitsquad/api/packages/{html.escape(slug)}/reservations', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(payload),
          }});
          const body = await response.json();
          const message = document.getElementById('reservation-message');
          message.style.display = 'block';
          if (!response.ok) {{
            message.textContent = body.detail || body.message || 'Reservation failed.';
            return;
          }}
          window.location.href = `/fitsquad/reservations/${{body.reservation_code}}`;
        }}
      </script>
    """
    return layout(travel_package.title, body)


@router.get("/reservations/{reservation_code}", response_class=HTMLResponse)
def reservation_confirmation(reservation_code: str) -> HTMLResponse:
    with SessionLocal() as session:
        reservation = get_reservation_by_code(session, reservation_code)
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        package_title = reservation.travel_package.title
        email_logs = list(session.scalars(
            session.query(EmailLog).where(EmailLog.reservation_id == reservation.id).statement
        ))
        email_items = "".join(
            f"<li><strong>{html.escape(item.email_type)}</strong>: {html.escape(item.subject)}</li>"
            for item in email_logs
        )
        reservation_code_value = reservation.reservation_code
        participants = reservation.participants
        payment_status = reservation.payment_status
        reservation_status = reservation.reservation_status
        email = reservation.email

    body = f"""
      <section class="panel hero-copy">
        <span class="eyebrow">Reservation captured</span>
        <h2>You're on the list.</h2>
        <p>
          Reservation <strong>{html.escape(reservation_code_value)}</strong> is recorded for
          <strong>{html.escape(package_title)}</strong>.
        </p>
        <div class="stats">
          <div class="stat"><span class="status">Participants</span><strong>{participants}</strong></div>
          <div class="stat"><span class="status">Payment status</span><strong>{html.escape(payment_status.replace('_', ' '))}</strong></div>
          <div class="stat"><span class="status">Reservation status</span><strong>{html.escape(reservation_status)}</strong></div>
          <div class="stat"><span class="status">Contact</span><strong>{html.escape(email)}</strong></div>
        </div>
      </section>
      <section class="section panel card">
        <h3>Automatic emails generated</h3>
        <ul>{email_items}</ul>
      </section>
    """
    return layout("Reservation confirmed", body)


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard() -> HTMLResponse:
    with SessionLocal() as session:
        reservations = list_reservations(session)
        rows = []
        for reservation in reservations:
            rows.append(
                f"""
                <tr>
                  <td>{html.escape(reservation.reservation_code)}</td>
                  <td>{html.escape(reservation.client_name)}<br /><span class="status">{html.escape(reservation.email)}</span></td>
                  <td>{html.escape(reservation.travel_package.title)}</td>
                  <td>{reservation.participants}</td>
                  <td>{html.escape(reservation.payment_status)}</td>
                  <td>
                    <select id="status-{reservation.id}">
                      <option value="pending" {'selected' if reservation.reservation_status == 'pending' else ''}>pending</option>
                      <option value="confirmed" {'selected' if reservation.reservation_status == 'confirmed' else ''}>confirmed</option>
                      <option value="cancelled" {'selected' if reservation.reservation_status == 'cancelled' else ''}>cancelled</option>
                    </select>
                  </td>
                  <td><button class="button secondary" type="button" onclick="updateStatus({reservation.id})">Save</button></td>
                </tr>
                """
            )

    body = f"""
      <section class="panel hero-copy">
        <span class="eyebrow">Admin MVP</span>
        <h2>Reservations</h2>
        <p>Minimal operations only: inspect reservations, see payment state, and update reservation status.</p>
      </section>
      <section class="section panel card">
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Client</th>
              <th>Package</th>
              <th>Participants</th>
              <th>Payment</th>
              <th>Reservation</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>{''.join(rows) or '<tr><td colspan="7">No reservations yet.</td></tr>'}</tbody>
        </table>
        <p id="admin-message" class="notice" style="display:none; margin-top:16px;"></p>
      </section>
      <script>
        async function updateStatus(id) {{
          const status = document.getElementById(`status-${{id}}`).value;
          const response = await fetch(`/fitsquad/api/admin/reservations/${{id}}`, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ reservation_status: status }}),
          }});
          const body = await response.json();
          const message = document.getElementById('admin-message');
          message.style.display = 'block';
          message.textContent = response.ok ? `Updated reservation to ${{body.reservation_status}}.` : (body.detail || 'Update failed.');
        }}
      </script>
    """
    return layout("FitSquad Admin", body)


@router.get("/api/packages")
def packages_api():
    with SessionLocal() as session:
        return [serialize_package(package, remaining_spots(session, package)) for package in list_packages(session)]


@router.get("/api/packages/{slug}")
def package_api(slug: str):
    with SessionLocal() as session:
        travel_package = get_package_by_slug(session, slug)
        if travel_package is None:
            raise HTTPException(status_code=404, detail="Package not found")
        return serialize_package(travel_package, remaining_spots(session, travel_package))


@router.post("/api/packages/{slug}/reservations")
def create_reservation_api(slug: str, payload: ReservationCreate):
    with SessionLocal() as session:
        travel_package = get_package_by_slug(session, slug)
        if travel_package is None:
            raise HTTPException(status_code=404, detail="Package not found")
        try:
            reservation = create_reservation(session, travel_package, payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(serialize_reservation(reservation))


@router.get("/api/admin/reservations")
def admin_reservations_api():
    with SessionLocal() as session:
        return [serialize_reservation(reservation) for reservation in list_reservations(session)]


@router.post("/api/admin/reservations/{reservation_id}")
def update_reservation_api(reservation_id: int, payload: ReservationStatusUpdate):
    with SessionLocal() as session:
        try:
            reservation = update_reservation_status(session, reservation_id, payload.reservation_status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return JSONResponse(serialize_reservation(reservation))


@router.get("")
def fitsquad_redirect():
    return RedirectResponse(url="/fitsquad/")
