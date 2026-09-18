from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="FastAPI Starter")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """Halaman utama, dirender pakai template Jinja2."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "FastAPI Starter", "message": "Halo, FastAPI berhasil jalan!"},
    )


@app.get("/api/hello")
def hello(name: str = "Dunia"):
    """Contoh endpoint JSON sederhana, coba akses /api/hello?name=Budi"""
    return {"message": f"Halo, {name}!"}


@app.get("/api/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    """Contoh endpoint dengan path parameter dan query parameter opsional."""
    return {"item_id": item_id, "q": q}