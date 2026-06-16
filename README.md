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

## 🚨 REQUIRED: Database Setup (DO THIS FIRST!)

**Before you can save any expenses, you MUST set up the database tables in Supabase:**

1. Go to: https://supabase.com/dashboard/project/zgnnxujzbjohaovsfuhj/sql/new
2. Open the **SQL Editor** and create a new query
3. Copy the entire contents of `schema.sql` from this project
4. Paste it into the Supabase SQL Editor and click **Run**
5. Go to **Authentication → Providers** and find **Email**
   - Disable "Confirm email" (uncheck the toggle) so users can sign in immediately
6. ✅ Your database is now ready!

**Without these steps, you'll get a "Not Authenticated" error when trying to save expenses.**

---

## Local Development

### Start Backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

API available at: http://localhost:8000/docs

### Start Frontend

```bash
cd frontend
python -m http.server 3000
```

Frontend available at: http://localhost:3000

**To use locally:**
1. Sign up for a new account (this creates a Supabase user)
2. Log in
3. Add expenses — they'll be saved to your Supabase database!

---

## Backend Configuration Details

The backend uses the `.env` file for configuration. Key variables:
- `SUPABASE_URL` — your Supabase project URL
- `SUPABASE_ANON_KEY` — public anon key (for client auth)
- `SUPABASE_SERVICE_ROLE_KEY` — admin key (optional, for server-side operations)
- `ALLOWED_ORIGINS` — CORS whitelist

---

## Local Development (Detailed)

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
