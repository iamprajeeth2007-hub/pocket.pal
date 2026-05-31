# PocketPal — AI-Powered Personal Finance Tracker

A full-stack personal finance web app with a Python/FastAPI backend, Supabase PostgreSQL database, and a single-file HTML frontend.

## Project Structure

```
pocket.pal/
├── frontend/
│   └── index.html          # Complete frontend (Tailwind, Chart.js, Supabase auth)
├── backend/
│   ├── main.py             # FastAPI routes
│   ├── config.py           # Settings / env vars
│   ├── ml_engine.py        # Smart categorization + spending prediction (scikit-learn)
│   ├── analytics.py        # Financial health score algorithm
│   ├── pdf_generator.py    # PDF report generation (ReportLab)
│   ├── csv_parser.py       # Bank statement CSV import
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Environment variables (do not commit)
├── schema.sql              # Supabase database schema
├── render.yaml             # Render deployment config (backend)
└── vercel.json             # Vercel deployment config (frontend)
```

---

## Supabase Setup (REQUIRED FIRST)

1. Go to: https://supabase.com/dashboard/project/zgnnxujzbjohaovsfuhj/sql/new
2. Copy and run the entire contents of `schema.sql`
3. Go to **Authentication → Providers → Email** → **disable "Confirm email"** (so users can sign in immediately)
4. Get your **Service Role Key**: Settings → API → `service_role` (secret)

---

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
# Copy .env and fill in SUPABASE_SERVICE_ROLE_KEY
cp .env .env.local
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend

Open `frontend/index.html` directly in a browser, or serve with:

```bash
npx serve frontend/
```

The `API_BASE_URL` auto-detects `localhost` and points to `http://localhost:8000`.

---

## Production Deployment

### Step 1 — Deploy Backend to Render

1. Push this repo to GitHub
2. Go to https://render.com → New Web Service → connect repo
3. Settings:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables on Render:
   - `SUPABASE_SERVICE_ROLE_KEY` = your service role key
   - `ALLOWED_ORIGINS` = `https://your-app.vercel.app`
5. After deploy, copy your Render URL e.g. `https://pocketpal-api.onrender.com`

### Step 2 — Update Frontend BACKEND_URL

In `frontend/index.html`, find line ~941:
```javascript
const BACKEND_URL = '';  // ← FILL THIS IN
```
Change to:
```javascript
const BACKEND_URL = 'https://pocketpal-api.onrender.com';
```

### Step 3 — Deploy Frontend to Vercel

1. Go to https://vercel.com → New Project → import repo
2. Framework: Other (static)
3. Root directory: leave as `/`
4. Deploy — done!

---

## Features

| Feature | Status |
|---------|--------|
| Email/Password Auth (Supabase) | ✅ |
| Expense CRUD | ✅ |
| Smart Auto-Categorization (ML) | ✅ |
| Categories: Food, Travel, Shopping, Recharge, Petrol, Others | ✅ |
| Debt Tracker (borrowed/lent) | ✅ |
| Budget Limits per Category | ✅ |
| Financial Health Score | ✅ |
| ML Spending Prediction (LinearRegression) | ✅ |
| Charts (Pie + Bar) | ✅ |
| PDF Report Download | ✅ |
| CSV Bank Statement Import | ✅ |
| Row Level Security (Supabase) | ✅ |

---

## Supabase Credentials

- **Project URL**: `https://zgnnxujzbjohaovsfuhj.supabase.co`
- **Anon Key**: already embedded in frontend and backend
- **Service Role Key**: get from Supabase dashboard (never commit this)
