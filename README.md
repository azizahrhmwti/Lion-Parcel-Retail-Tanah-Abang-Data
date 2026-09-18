# Lion Parcel Tanah Abang Leads

Aplikasi internal untuk pendataan leads toko Tanah Abang, pengaturan routing visit, dan assignment sales. Dibangun dengan FastAPI, Jinja2, SQLAlchemy, dan SQLite.

## Fitur

- Login berbasis role: `Data Entry`, `Admin`, `Router`, dan `Sales`.
- Input data kunjungan: timestamp, identitas toko, blok/lantai/los/nomor toko, PIC, profil kiriman, ekspedisi, lokasi tujuan, dan estimasi kg.
- Database leads dengan pencarian dan filter status.
- Routing visit per tanggal dengan rekomendasi urutan berdasarkan blok, lantai, los, dan nomor toko.
- Assignment rute ke Sales serta aksi menandai kunjungan selesai.
- Admin dapat menambah user dan mengatur role tim.
- Responsive interface untuk laptop dan layar mobile.

## Menjalankan secara lokal

Prasyarat: Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\\Scripts\\activate    # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Buka `http://127.0.0.1:8000`.

### Demo login

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Data Entry | `entry` | `entry123` |
| Router | `router` | `router123` |
| Sales | `sales` | `sales123` |

Akun demo dibuat otomatis ketika aplikasi pertama kali start. Ganti password dan `APP_SECRET_KEY` sebelum dipakai di lingkungan bersama/produksi.

## Struktur singkat

```text
app/
├── main.py              # routes, role guards, seed data
├── models.py            # User dan Lead SQLAlchemy models
├── database.py          # engine dan session
├── auth.py              # hash dan session helper
├── templates/           # halaman Jinja2
└── static/style.css     # interface responsive
```

## Catatan routing

Router memilih beberapa leads yang belum dirouting, memilih tanggal dan Sales, lalu aplikasi mengurutkannya dengan kunci lokasi: `block`, `floor`, `store_number`, dan `stall`. Ini adalah baseline rekomendasi berbasis data lokasi toko. Untuk tahap lanjutan dapat ditambah master koordinat toko, peta denah, drag-and-drop route, export Excel, audit log, dan integrasi WhatsApp/CRM.

## Testing

```bash
pytest
```

Database SQLite lokal tersimpan sebagai `lion_parcel.db` dan diabaikan oleh Git.

## Deploy ke Vercel

Project ini sudah memiliki `vercel.json` dan entrypoint `api/index.py` untuk Vercel.

```bash
npm install -g vercel
vercel login
vercel
```

Sebelum deploy production, tambahkan Environment Variables di Vercel:

- `APP_SECRET_KEY`: secret random yang panjang.
- `DATABASE_URL`: URL database PostgreSQL managed, misalnya Neon, Supabase, atau Vercel Postgres.

Jangan memakai `sqlite:///./lion_parcel.db` untuk production Vercel karena filesystem serverless tidak persisten. SQLite tetap digunakan untuk development lokal. Setelah environment variable disimpan, jalankan deploy production:

```bash
vercel --prod
```
