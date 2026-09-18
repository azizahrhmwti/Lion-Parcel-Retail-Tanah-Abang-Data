from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .auth import current_user, hash_password, verify_password
from .database import Base, SessionLocal, engine, get_db
from .models import Lead, LeadStatus, Role, User

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Lion Parcel Tanah Abang Leads")
app.add_middleware(SessionMiddleware, secret_key=__import__("os").getenv("APP_SECRET_KEY", "dev-only-change-me"))
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

EXPEDITIONS = ["Lion Parcel", "Rayspeed Asia", "TLX", "JNT", "JNE", "Sicepat", "Lainnya"]
SHIPMENT_TYPES = ["Domestik", "International", "Keduanya", "Tidak Sama Sekali"]

SEED_LOCATIONS = [
    ("B", "SLG", "H", 69, "Blok B Lantai SLG Los H no. 69-71", "6281391486992"),
    ("B", "SLG", "E", 155, "Blok B Lantai SLG Los E no. 155-157", "6281286255005"),
    ("B", "SLG", "A", 128, "Blok B Lantai SLG Los A no. 128", "6285693381973"),
    ("B", "SLG", "E", 47, "Blok B Lantai SLG Los E no. 47", "628561236780"),
    ("B", "SLG", "C", 26, "Blok B Lantai SLG Los C no. 26-28", "628128042707"),
    ("B", "LG", "C", 31, "Blok B Lantai LG Los C no. 31", "6285110364703"),
    ("B", "LG", "H", 22, "Blok B Lantai LG Los H no. 22", "6285867953778"),
    ("B", "LG", "F", 123, "Blok B Lantai LG Los F no. 123", "6282123252626"),
    ("B", "LG", "H", 117, "Blok B Lantai LG Los H no. 117-118", "6285219901219"),
    ("B", "LG", "E", 100, "Blok B Lantai LG Los E no. 100-101", "6289637591988"),
    ("B", "G", "E", 107, "Blok B Lantai G Los E no. 107", "6281274902815"),
    ("B", "G", "B", 138, "Blok B Lantai G Los B no. 138", "6285892655324"),
    ("B", "G", "F", 27, "Blok B Lantai G Los F no. 27", "6281282705634"),
    ("B", "G", "D", 7, "Blok B Lantai G Los D no. 7-8", "6282124830098"),
    ("B", "G", "F", 5, "Blok B Lantai G Los F no. 5-6", "6282171100330"),
    ("B", "1", "G", 41, "Blok B Lantai 1 Los G no. 41-42", "6285251519810"),
    ("B", "1", "D", 42, "Blok B Lantai 1 Los D no. 42-48", "6281527272727"),
    ("B", "1", "E", 153, "Blok B Lantai 1 Los E no. 153", "6282124828826"),
    ("B", "1", "F", 66, "Blok B Lantai 1 Los F no. 66", "6285365895189"),
    ("B", "1", "G", 30, "Blok B Lantai 1 Los G no. 30", "6289604002903"),
    ("B", "2", "G", 130, "Blok B Lantai 2 Los G no. 130", "6282113842288"),
    ("B", "2", "F", 20, "Blok B Lantai 2 Los F no. 20", "6282211921627"),
    ("B", "2", "G", 141, "Blok B Lantai 2 Los G no. 141-142", "6285212795643"),
    ("B", "2", "H", 40, "Blok B Lantai 2 Los H no. 40", "6282122798957"),
    ("B", "2", "D", 46, "Blok B Lantai 2 Los D no. 46-47", "6281808470839"),
    ("B", "3", "C", 103, "Blok B Lantai 3 Los C no. 103-105", "6285773333370"),
    ("B", "3", "B", 57, "Blok B Lantai 3 Los B no. 57", "6285762705501"),
    ("B", "3", "F", 117, "Blok B Lantai 3 Los F no. 117", "6285782747911"),
    ("B", "3", "D", 146, "Blok B Lantai 3 Los D no. 146-147", "6287878958303"),
    ("B", "3", "G", 30, "Blok B Lantai 3 Los G no. 30", "6287744588126"),
    ("B", "3", "D", 133, "Blok B Lantai 3 Los D no. 133", "6281510577756"),
    ("B", "B1", "G", 92, "Blok B Lantai B1 Los G no. 92-93", "6287760171456"),
    ("B", "B1", "B", 88, "Blok B Lantai B1 Los B no. 88", "6281290108168"),
    ("B", "B1", "A", 11, "Blok B Lantai B1 Los A no. 11", "6282254527519"),
    ("B", "B1", "D", 16, "Blok B Lantai B1 Los D no. 16-17", "6285880522021"),
    ("B", "B1", "C", 153, "Blok B Lantai B1 Los C no. 153", "6282113367875"),
]

# Additional deterministic demo rows make the routing screen useful on first launch.
for block in ("A", "C", "D", "E"):
    for index in range(1, 11):
        floor_label = ("LG", "G", "1", "2")[index % 4]
        stall = "ABCDEFGH"[index % 8]
        store_number = 10 + index * 7
        phone = f"628110{ord(block) - 64:02d}{index:05d}"
        detail = f"Blok {block} Lantai {floor_label} Los {stall} no. {store_number}"
        SEED_LOCATIONS.append((block, floor_label, stall, store_number, detail, phone))

FLOOR_ORDER = {"B1": -1, "SLG": 0, "LG": 1, "G": 2, "1": 3, "2": 4, "3": 5}


def seed_database() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalar(select(func.count(User.id))) == 0:
            users = [
                User(name="Admin Utama", username="admin", password_hash=hash_password("admin123"), role=Role.ADMIN.value),
                User(name="Data Entry Demo", username="entry", password_hash=hash_password("entry123"), role=Role.DATA_ENTRY.value),
                User(name="Router Demo", username="router", password_hash=hash_password("router123"), role=Role.ROUTER.value),
                User(name="Sales Demo", username="sales", password_hash=hash_password("sales123"), role=Role.SALES.value),
            ]
            db.add_all(users)
            db.commit()
        data_entry = db.scalar(select(User).where(User.username == "entry"))
        if data_entry:
            existing_phones = set(db.scalars(select(Lead.phone)).all())
            for index, (block, floor_label, stall, store_number, detail, phone) in enumerate(SEED_LOCATIONS, start=1):
                if phone in existing_phones:
                    continue
                db.add(Lead(
                    visited_at=datetime.now() - timedelta(days=index % 14),
                    store_name=f"Toko {block}-{index:03d}",
                    block=block,
                    floor=FLOOR_ORDER[floor_label],
                    stall=stall,
                    store_number=store_number,
                    pic_name="PIC Operasional",
                    pic_position="Owner / Staff",
                    phone=phone,
                    shipment_type=SHIPMENT_TYPES[index % len(SHIPMENT_TYPES)],
                    expedition=EXPEDITIONS[index % len(EXPEDITIONS)],
                    top_country="Indonesia" if index % 3 else "Singapore",
                    top_city=("Jakarta", "Bandung", "Surabaya", "Medan")[index % 4],
                    potential_kg=float(15 + (index * 11) % 135),
                    notes=f"Seed data lokasi: {detail}",
                    data_entry_id=data_entry.id,
                ))
                existing_phones.add(phone)
            db.commit()
        sales = db.scalar(select(User).where(User.username == "sales"))
        routed_seed_count = db.scalar(select(func.count(Lead.id)).where(
            Lead.status == LeadStatus.ROUTED.value,
            Lead.notes.like("Seed data lokasi:%"),
        )) or 0
        if sales and routed_seed_count == 0:
            route_leads = db.scalars(select(Lead).where(
                Lead.status == LeadStatus.NEW.value,
                Lead.notes.like("Seed data lokasi: Blok B%"),
            ).order_by(Lead.block, Lead.floor, Lead.stall, Lead.store_number).limit(36)).all()
            for index, lead in enumerate(route_leads):
                lead.sales_id = sales.id
                lead.visit_date = date.today() + timedelta(days=index // 12)
                lead.visit_order = (index % 12) + 1
                lead.status = LeadStatus.ROUTED.value
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    seed_database()


def page_context(request: Request, db: Session, **values: object) -> dict[str, object]:
    return {"request": request, "user": current_user(request, db), **values}


def require_roles(request: Request, db: Session, roles: set[str]) -> User | RedirectResponse:
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if user.role not in roles:
        return RedirectResponse("/?error=Akses+tidak+diizinkan", status_code=303)
    return user


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if current_user(request, db):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": request.query_params.get("error")})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == username.strip()))
    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse("/login?error=Username+atau+password+salah", status_code=303)
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    leads_query = select(Lead)
    if user.role == Role.SALES.value:
        leads_query = leads_query.where(Lead.sales_id == user.id)
    recent_leads = db.scalars(leads_query.order_by(Lead.visited_at.desc()).limit(8)).all()
    stats = {"total": db.scalar(select(func.count(Lead.id))) or 0, "new": db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.NEW.value)) or 0, "routed": db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.ROUTED.value)) or 0, "kg": db.scalar(select(func.coalesce(func.sum(Lead.potential_kg), 0))) or 0}
    return templates.TemplateResponse("dashboard.html", page_context(request, db, stats=stats, recent_leads=recent_leads))


@app.get("/leads", response_class=HTMLResponse)
def leads(request: Request, q: str = "", status: str = "", db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    query = select(Lead).order_by(Lead.visited_at.desc())
    if user.role == Role.SALES.value:
        query = query.where(Lead.sales_id == user.id)
    if q:
        query = query.where(or_(Lead.store_name.ilike(f"%{q}%"), Lead.block.ilike(f"%{q}%"), Lead.pic_name.ilike(f"%{q}%")))
    if status:
        query = query.where(Lead.status == status)
    return templates.TemplateResponse("leads.html", page_context(request, db, leads=db.scalars(query).all(), q=q, status=status))


@app.get("/leads/new", response_class=HTMLResponse)
def lead_form(request: Request, db: Session = Depends(get_db)):
    result = require_roles(request, db, {Role.DATA_ENTRY.value, Role.ADMIN.value})
    if isinstance(result, RedirectResponse):
        return result
    return templates.TemplateResponse("lead_form.html", page_context(request, db, shipments=SHIPMENT_TYPES, expeditions=EXPEDITIONS, error=request.query_params.get("error")))


@app.post("/leads")
def create_lead(request: Request, visited_at: str = Form(...), store_name: str = Form(...), block: str = Form(...), floor: int = Form(...), stall: str = Form(""), store_number: str = Form(""), pic_name: str = Form(...), pic_position: str = Form(...), phone: str = Form(...), shipment_type: str = Form(...), expedition: str = Form(...), top_country: str = Form(""), top_city: str = Form(""), potential_kg: float = Form(...), notes: str = Form(""), db: Session = Depends(get_db)):
    result = require_roles(request, db, {Role.DATA_ENTRY.value, Role.ADMIN.value})
    if isinstance(result, RedirectResponse):
        return result
    try:
        parsed_visit = datetime.fromisoformat(visited_at)
        numeric_store = int(store_number) if store_number.strip() else None
    except ValueError:
        return RedirectResponse("/leads/new?error=Format+tanggal+atau+nomor+toko+tidak+valid", status_code=303)
    lead = Lead(visited_at=parsed_visit, store_name=store_name, block=block.upper(), floor=floor, stall=stall or None, store_number=numeric_store, pic_name=pic_name, pic_position=pic_position, phone=phone, shipment_type=shipment_type, expedition=expedition, top_country=top_country or None, top_city=top_city or None, potential_kg=potential_kg, notes=notes or None, data_entry_id=result.id)
    db.add(lead)
    db.commit()
    return RedirectResponse("/leads", status_code=303)


@app.get("/routing", response_class=HTMLResponse)
def routing(request: Request, visit_date: str = "", db: Session = Depends(get_db)):
    result = require_roles(request, db, {Role.ROUTER.value, Role.ADMIN.value})
    if isinstance(result, RedirectResponse):
        return result
    chosen_date = date.fromisoformat(visit_date) if visit_date else date.today()
    leads = db.scalars(select(Lead).where(Lead.visit_date == chosen_date).order_by(Lead.block, Lead.floor, Lead.store_number)).all()
    unassigned = db.scalars(select(Lead).where(Lead.status == LeadStatus.NEW.value).order_by(Lead.block, Lead.floor, Lead.store_number)).all()
    sales = db.scalars(select(User).where(User.role == Role.SALES.value, User.is_active.is_(True)).order_by(User.name)).all()
    return templates.TemplateResponse("routing.html", page_context(request, db, leads=leads, unassigned=unassigned, sales=sales, visit_date=chosen_date.isoformat()))


@app.post("/routing/assign")
def assign_route(request: Request, visit_date: str = Form(...), sales_id: int = Form(...), lead_ids: list[int] = Form(...), db: Session = Depends(get_db)):
    result = require_roles(request, db, {Role.ROUTER.value, Role.ADMIN.value})
    if isinstance(result, RedirectResponse):
        return result
    selected = db.scalars(select(Lead).where(Lead.id.in_(lead_ids))).all()
    selected.sort(key=lambda lead: (lead.block, lead.floor, lead.store_number or 9999, lead.stall or ""))
    for order, lead in enumerate(selected, start=1):
        lead.sales_id, lead.visit_date, lead.visit_order, lead.status = sales_id, date.fromisoformat(visit_date), order, LeadStatus.ROUTED.value
    db.commit()
    return RedirectResponse(f"/routing?{urlencode({'visit_date': visit_date})}", status_code=303)


@app.post("/leads/{lead_id}/visited")
def mark_visited(request: Request, lead_id: int, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    lead = db.get(Lead, lead_id)
    if lead and (user.role in {Role.ADMIN.value, Role.ROUTER.value} or lead.sales_id == user.id):
        lead.status = LeadStatus.VISITED.value
        db.commit()
    return RedirectResponse(request.headers.get("referer", "/leads"), status_code=303)


@app.get("/users", response_class=HTMLResponse)
def users(request: Request, db: Session = Depends(get_db)):
    result = require_roles(request, db, {Role.ADMIN.value})
    if isinstance(result, RedirectResponse):
        return result
    return templates.TemplateResponse("users.html", page_context(request, db, users=db.scalars(select(User).order_by(User.role, User.name)).all(), roles=[r.value for r in Role]))


@app.post("/users")
def create_user(request: Request, name: str = Form(...), username: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    result = require_roles(request, db, {Role.ADMIN.value})
    if isinstance(result, RedirectResponse):
        return result
    if db.scalar(select(User).where(User.username == username.strip())):
        return RedirectResponse("/users?error=Username+sudah+digunakan", status_code=303)
    db.add(User(name=name, username=username.strip(), password_hash=hash_password(password), role=role))
    db.commit()
    return RedirectResponse("/users", status_code=303)
