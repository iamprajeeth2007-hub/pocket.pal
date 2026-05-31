import os
from fastapi import FastAPI, Depends, HTTPException, Security, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from supabase import create_client, Client

from config import settings
from ml_engine import categorize_expense, predict_future_spending
from analytics import calculate_financial_health_score
from pdf_generator import generate_pdf_report
from csv_parser import parse_bank_statement_csv

app = FastAPI(
    title="PocketPal API",
    description="AI-powered personal finance management API",
    version="1.0.0"
)

# CORS — allow configured origins (set ALLOWED_ORIGINS env var in production)
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Supabase clients ──────────────────────────────────────────────────────────
# Public client (anon key) — for auth token verification
supabase: Optional[Client] = None
# Admin client (service role key) — used where elevated permissions are needed
supabase_admin: Optional[Client] = None

try:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
except Exception as e:
    print(f"[WARN] Supabase anon client init failed: {e}")

if settings.SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase_admin = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        print(f"[WARN] Supabase admin client init failed: {e}")

# Use admin client when available (bypasses RLS for server-side ops), else fall back to anon
def get_db() -> Client:
    return supabase_admin if supabase_admin else supabase

# ── Auth ──────────────────────────────────────────────────────────────────────
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify Supabase JWT and return the authenticated user."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase backend is not configured.")
    token = credentials.credentials
    try:
        user_res = supabase.auth.get_user(token)
        if not user_res or not user_res.user:
            raise HTTPException(status_code=401, detail="Invalid or expired session token.")
        return user_res.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# ── Request Models ────────────────────────────────────────────────────────────
VALID_CATEGORIES = ["Food", "Travel", "Shopping", "Recharge", "Petrol", "Others"]

class CategorizeRequest(BaseModel):
    description: str

class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0)
    description: str
    category: str
    date: str  # YYYY-MM-DD

class DebtCreate(BaseModel):
    type: str = Field(..., pattern="^(borrowed|lent)$")
    person: str
    amount: float = Field(..., gt=0)
    note: Optional[str] = None
    due_date: Optional[str] = None

class BudgetLimitSet(BaseModel):
    category: str
    limit_amount: float = Field(..., ge=0)

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "PocketPal API is running. Visit /docs for Swagger documentation."}

@app.get("/health")
def health_check():
    return {"status": "ok", "supabase_connected": supabase is not None}

# Smart Categorization
@app.post("/api/expenses/categorize")
def api_categorize_expense(req: CategorizeRequest):
    category = categorize_expense(req.description)
    return {"category": category}

# ── Expenses CRUD ─────────────────────────────────────────────────────────────

@app.get("/api/expenses")
async def get_expenses(
    user=Depends(get_current_user),
    month: Optional[str] = Query(None, description="Filter by month, format YYYY-MM")
):
    try:
        db = get_db()
        query = db.table("expenses").select("*").eq("user_id", user.id)
        if month:
            query = query.like("date", f"{month}%")
        response = query.order("date", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/expenses")
async def create_expense(expense: ExpenseCreate, user=Depends(get_current_user)):
    try:
        # Auto-categorize if category is Others or empty
        category = expense.category
        if not category or category == "Others":
            category = categorize_expense(expense.description)

        record = {
            "user_id": user.id,
            "amount": expense.amount,
            "description": expense.description,
            "category": category,
            "date": expense.date
        }
        db = get_db()
        response = db.table("expenses").insert(record).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to save expense.")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/expenses/{expense_id}")
async def update_expense(expense_id: str, expense: ExpenseCreate, user=Depends(get_current_user)):
    try:
        record = {
            "amount": expense.amount,
            "description": expense.description,
            "category": expense.category,
            "date": expense.date
        }
        db = get_db()
        response = db.table("expenses").update(record).eq("id", expense_id).eq("user_id", user.id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Expense not found or unauthorized.")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/expenses/{expense_id}")
async def delete_expense(expense_id: str, user=Depends(get_current_user)):
    try:
        db = get_db()
        response = db.table("expenses").delete().eq("id", expense_id).eq("user_id", user.id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Expense not found or unauthorized.")
        return {"status": "success", "message": "Expense deleted."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Debts CRUD ────────────────────────────────────────────────────────────────

@app.get("/api/debts")
async def get_debts(user=Depends(get_current_user)):
    try:
        db = get_db()
        response = db.table("debts").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/debts")
async def create_debt(debt: DebtCreate, user=Depends(get_current_user)):
    try:
        record = {
            "user_id": user.id,
            "type": debt.type,
            "person": debt.person,
            "amount": debt.amount,
            "note": debt.note,
            "due_date": debt.due_date,
            "status": "pending"
        }
        db = get_db()
        response = db.table("debts").insert(record).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to save debt record.")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/debts/{debt_id}")
async def update_debt(debt_id: str, debt: DebtCreate, user=Depends(get_current_user)):
    try:
        record = {
            "type": debt.type,
            "person": debt.person,
            "amount": debt.amount,
            "note": debt.note,
            "due_date": debt.due_date
        }
        db = get_db()
        response = db.table("debts").update(record).eq("id", debt_id).eq("user_id", user.id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Debt record not found or unauthorized.")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/debts/{debt_id}/toggle-status")
async def toggle_debt_status(debt_id: str, user=Depends(get_current_user)):
    try:
        db = get_db()
        debt_res = db.table("debts").select("status").eq("id", debt_id).eq("user_id", user.id).execute()
        if not debt_res.data:
            raise HTTPException(status_code=404, detail="Debt record not found.")
        current_status = debt_res.data[0]["status"]
        new_status = "paid" if current_status == "pending" else "pending"
        response = db.table("debts").update({"status": new_status}).eq("id", debt_id).eq("user_id", user.id).execute()
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/debts/{debt_id}")
async def delete_debt(debt_id: str, user=Depends(get_current_user)):
    try:
        db = get_db()
        response = db.table("debts").delete().eq("id", debt_id).eq("user_id", user.id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Debt record not found or unauthorized.")
        return {"status": "success", "message": "Debt record deleted."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Budget Limits ─────────────────────────────────────────────────────────────

@app.get("/api/budgets")
async def get_budgets(user=Depends(get_current_user)):
    try:
        db = get_db()
        response = db.table("budget_limits").select("*").eq("user_id", user.id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/budgets")
async def set_budget_limit(limit: BudgetLimitSet, user=Depends(get_current_user)):
    try:
        if limit.category not in VALID_CATEGORIES:
            raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}")
        record = {
            "user_id": user.id,
            "category": limit.category,
            "limit_amount": limit.limit_amount
        }
        db = get_db()
        response = db.table("budget_limits").upsert(record, on_conflict="user_id,category").execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to save budget limit.")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/budgets/{category}")
async def delete_budget_limit(category: str, user=Depends(get_current_user)):
    try:
        db = get_db()
        db.table("budget_limits").delete().eq("category", category).eq("user_id", user.id).execute()
        return {"status": "success", "message": f"Budget limit for {category} deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Analytics ─────────────────────────────────────────────────────────────────

@app.get("/api/analytics/predict")
async def get_expense_prediction(user=Depends(get_current_user)):
    try:
        db = get_db()
        expenses_res = db.table("expenses").select("*").eq("user_id", user.id).execute()
        prediction = predict_future_spending(expenses_res.data)
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML Predictor Error: {str(e)}")

@app.get("/api/analytics/health-score")
async def get_health_score(
    income: float = Query(50000.0, description="User monthly income"),
    user=Depends(get_current_user)
):
    try:
        db = get_db()
        expenses_res = db.table("expenses").select("*").eq("user_id", user.id).execute()
        limits_res = db.table("budget_limits").select("*").eq("user_id", user.id).execute()
        score_data = calculate_financial_health_score(expenses_res.data, limits_res.data, income)
        return score_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health Score Error: {str(e)}")

# ── PDF Report ────────────────────────────────────────────────────────────────

@app.get("/api/reports/pdf")
async def download_pdf_report(
    month: str = Query(..., description="Format YYYY-MM"),
    income: float = Query(50000.0, description="Monthly income"),
    user=Depends(get_current_user)
):
    try:
        db = get_db()
        expenses_res = db.table("expenses").select("*").eq("user_id", user.id).execute()
        limits_res = db.table("budget_limits").select("*").eq("user_id", user.id).execute()
        health_score_data = calculate_financial_health_score(expenses_res.data, limits_res.data, income)
        pdf_stream = generate_pdf_report(expenses_res.data, limits_res.data, income, health_score_data, month)
        filename = f"pocketpal_report_{month}.pdf"
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Generation Error: {str(e)}")

# ── CSV Upload ────────────────────────────────────────────────────────────────

@app.post("/api/upload-csv")
async def upload_bank_statement(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    try:
        file_bytes = await file.read()
        parsed_expenses = parse_bank_statement_csv(file_bytes)

        if not parsed_expenses:
            return {"status": "success", "message": "No valid records found in CSV.", "added_count": 0}

        for exp in parsed_expenses:
            exp["user_id"] = user.id

        db = get_db()
        response = db.table("expenses").insert(parsed_expenses).execute()
        return {
            "status": "success",
            "message": f"Successfully imported {len(response.data)} expenses.",
            "added_count": len(response.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV Upload failed: {str(e)}")
