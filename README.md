# Trip Planner (React + Django)

A full-stack app that plans a trucking trip (current → pickup → dropoff), draws the route on a Leaflet map, and overlays DOT-style driver logs on a real logbook template using HTML Canvas.

**Live:**  
Frontend (Vercel): https://trip-planner-two-ebon.vercel.app  
Backend (Render docs): https://trip-planner-t6ty.onrender.com/api/docs/

---

## ✨ Features

- **Form → Plan → Results** flow with validation
- **OpenRouteService** geocoding + directions (with **deterministic fallback** if no key / rate-limited)
- **Polyline rendering** on **Leaflet** with pickup/drop (and synthetic fuel) stops
- **DOT logs overlay** on a logbook image via `<canvas>` (anchored lanes/hours)
- **OpenAPI docs** via drf-spectacular (`/api/docs/`)
- **CORS** configured for Vercel → Render in production
- **Responsive UI** with a modern gradient background and card styling

---

## 🧱 Tech Stack

- **Frontend:** React (Vite + TypeScript), React Hook Form, React Router, Leaflet, polyline  
- **Backend:** Django REST Framework, drf-spectacular, django-cors-headers, Gunicorn  
- **Deploy:** Vercel (frontend), Render (backend)

---

## 📁 Repository Structure

```
repo/
├─ backend/
│  ├─ manage.py
│  ├─ config/ or core/      # Django project package (settings.py, wsgi.py, urls.py)
│  └─ trip/                 # serializers.py, views.py, services.py
└─ frontend/
   ├─ public/
   │  └─ log.png            # logbook template image for Canvas overlay
   └─ src/
      ├─ components/        # TripForm, MapView, LogCanvas
      ├─ pages/             # Home, Results
      ├─ lib/               # api.ts (fetch helper)
      └─ index.css          # global styles (gradient, card, inputs)
```

> If your Django package is `core` instead of `config`, use `core.wsgi:application` in Gunicorn.

---

## ⚙️ Local Development

### 1) Backend (Django)

```bash
cd backend
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# -> http://127.0.0.1:8000/api/docs/
```

### 2) Frontend (React)

```bash
cd frontend
npm install
# (create .env.local with VITE_API_URL; see below)
npm run dev
# -> http://localhost:5173
```

---

## 🔑 Environment Variables

### Backend (Render dashboard or `backend/.env` for local)

| Name                          | Example / Notes                                                                          |
|------------------------------ |-------------------------------------------------------------------------------------------|
| `DEBUG`                       | `1` locally, `0` in production                                                            |
| `SECRET_KEY`                  | long random string                                                                        |
| `ALLOWED_HOSTS`               | `.onrender.com,localhost`                                                                 |
| `ORS_API_KEY`                 | *(optional)* OpenRouteService key (falls back to synthetic route if not set)              |
| `CORS_ALLOWED_ORIGINS`        | `https://trip-planner-two-ebon.vercel.app,http://localhost:5173`                          |
| `CSRF_TRUSTED_ORIGINS`        | `https://trip-planner-two-ebon.vercel.app`                                                |
| `CORS_ALLOWED_ORIGIN_REGEXES` | *(optional for first deploy)* `^https?:\/\/.*\.vercel\.app$,^http:\/\/localhost:5173$` |

### Frontend (Vercel project or `frontend/.env.local`)

```
VITE_API_URL=https://trip-planner-t6ty.onrender.com/api
# Local example:
# VITE_API_URL=http://127.0.0.1:8000/api
```

---

## 🧪 API

### `POST /api/trip/plan/`

**Request**
```json
{
  "current_location": "Austin, TX",
  "pickup_location": "Dallas, TX",
  "dropoff_location": "Oklahoma City, OK",
  "current_cycle_used_hours": 10
}
```

**Response (shape)**
```json
{
  "distance_miles": 356.4,
  "duration_minutes": 1020,
  "polyline": "<encoded full route>",
  "polylines": ["<leg1>", "<leg2>"],
  "stops": [
    {"type":"pickup","name":"Dallas, TX","lat":32.7,"lng":-96.8,"duration_minutes":60},
    {"type":"fuel","name":"Fuel stop","lat":34.1,"lng":-97.2,"duration_minutes":15},
    {"type":"dropoff","name":"Oklahoma City, OK","lat":35.5,"lng":-97.5,"duration_minutes":60}
  ],
  "logs": [
    [
      {"status":"on_duty","start":"07:00","end":"08:00"},
      {"status":"driving","start":"08:00","end":"17:00"}
    ]
  ],
  "instructions": []
}
```

Swagger UI: `GET /api/docs/`

---

## 🚀 Deployment

### Backend → Render

1) **New Web Service**  
   - **Root Directory:** `backend` (folder with `manage.py` & `requirements.txt`)  
   - **Build Command:** `pip install -r requirements.txt`  
   - **Start Command:**  
     - `gunicorn config.wsgi:application`  
       *(or `gunicorn core.wsgi:application` if your package is `core`)*

2) **Environment variables** as above.

3) **Migrate (optional):** Render Shell → `python manage.py migrate`

4) Health endpoints:  
   - `/` → “Backend OK”  
   - `/api/docs/` → OpenAPI

### Frontend → Vercel

1) Import repo → **Framework: Vite**  
   - Install: `npm ci` (or `npm i`)  
   - Build: `vite build`  
   - Output: `dist`

2) Project env: `VITE_API_URL=https://trip-planner-t6ty.onrender.com/api`

3) Deploy → copy Vercel URL → go back to Render and **tighten CORS** to that exact origin.

---

## 🧭 Frontend Notes

- `TripForm.tsx` – react-hook-form with validation, posts to `/api/trip/plan/`, navigates with plan in state.  
- `MapView.tsx` – decodes `polyline(s)` via `polyline` lib, renders with Leaflet, fits bounds, adds markers.  
- `LogCanvas.tsx` – draws `/public/log.png` first, then hour labels + duty lines; the first row is **anchored** so changing spacing (`rowH`) won’t misalign rows.

---

## 🛟 Troubleshooting

- **CORS preflight fails (no `Access-Control-Allow-Origin`)**  
  Ensure `corsheaders.middleware.CorsMiddleware` is the **first** middleware. Set `CORS_ALLOWED_ORIGINS` to your Vercel URL and redeploy.

- **405 at `/api/trip/plan/`**  
  Expected if you send `GET`. Use `POST`.

- **500 on `/api/trip/plan/`**  
  The view wraps errors into 400 with a message. Common root causes (fixed): missing `FUEL_STOP_MIN`, missing `distribute_fuel_stops`, `directions()` not returning `coords` in fallback, or `polyline` missing from `requirements.txt`.

- **Map shows but no route**  
  Ensure you pass either `plan.polyline` or `plan.polylines` to `MapView` and Leaflet CSS is included.

- **Log overlay misaligned**  
  Tweak `left`, `top`, and `rowH` in `LogCanvas.tsx`. Anchor logic keeps row 1 centered while you tune spacing.

---

## 🗺️ Roadmap

- Stricter HOS rules (30-min break after 8h driving, 10h off-duty, 70h/8-day cycle)  
- Distance-aware fuel stop placement  
- Address autocomplete & offline caching  
- Export logs as PNG/PDF  
- Unit tests for `trip/services.py` and CORS config

---

## 📜 License

MIT © 2025 Luornor Nathan
