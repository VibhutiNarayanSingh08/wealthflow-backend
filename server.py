"""
WealthFlow FastAPI Backend — Production Ready
JWT Auth, user-scoped data, PWA static files.
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import bcrypt
import jwt
import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

import database

load_dotenv()

# Startup diagnostics
print(f"[WealthFlow] DATABASE_URL set: {bool(os.getenv('DATABASE_URL'))}")
print(f"[WealthFlow] Using PostgreSQL: {database.USE_POSTGRES}")

app = FastAPI(title="WealthFlow API")

# CORS: restrict to your frontend domains in production
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()

BASE_DIR = Path(__file__).parent
INDSTOCKS_TOKEN = os.getenv("INDSTOCKS_TOKEN", "")
INDSTOCKS_BASE = "https://api.indstocks.com"
MFAPI_BASE = "https://api.mfapi.in"
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGO = "HS256"
JWT_EXPIRE_HOURS = 168  # 7 days

security = HTTPBearer(auto_error=False)


# ==================== AUTH UTILS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": str(user_id), "exp": exp}, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return decode_token(credentials.credentials)


# ==================== AUTH MODELS & ENDPOINTS ====================

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    token: str
    user: dict


@app.post("/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    existing = database.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = database.create_user(req.email, hash_password(req.password), req.name)
    token = create_token(user["id"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"]}}


@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    user = database.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["id"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"]}}


@app.get("/auth/me")
def me(user_id: int = Depends(get_current_user)):
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ==================== HEALTH ====================

@app.get("/api/health")
def health():
    db_ok = False
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_ok = True
        conn.close()
    except Exception as e:
        print(f"[Health] DB check failed: {e}")
    return {
        "status": "ok",
        "db_connected": db_ok,
        "db_type": "postgres" if database.USE_POSTGRES else "sqlite",
        "indstocks_connected": bool(INDSTOCKS_TOKEN)
    }


# ==================== INDSTOCKS PROXY ====================

@app.get("/api/portfolio")
def get_portfolio(user_id: int = Depends(get_current_user)):
    if not INDSTOCKS_TOKEN:
        raise HTTPException(status_code=400, detail="INDSTOCKS_TOKEN not configured")
    headers = {"Authorization": INDSTOCKS_TOKEN, "Content-Type": "application/json"}
    try:
        holdings_resp = requests.get(f"{INDSTOCKS_BASE}/portfolio/holdings", headers=headers, timeout=10)
        positions_resp = requests.get(f"{INDSTOCKS_BASE}/portfolio/positions", headers=headers, timeout=10)
        funds_resp = requests.get(f"{INDSTOCKS_BASE}/funds", headers=headers, timeout=10)
        return {
            "holdings": holdings_resp.json() if holdings_resp.ok else {},
            "positions": positions_resp.json() if positions_resp.ok else {},
            "funds": funds_resp.json() if funds_resp.ok else {}
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"IndStocks API error: {str(e)}")


@app.get("/api/quotes/ltp")
def get_ltp(scrip_codes: str, user_id: int = Depends(get_current_user)):
    if not INDSTOCKS_TOKEN:
        raise HTTPException(status_code=400, detail="INDSTOCKS_TOKEN not configured")
    headers = {"Authorization": INDSTOCKS_TOKEN, "Content-Type": "application/json"}
    try:
        resp = requests.get(f"{INDSTOCKS_BASE}/market/quotes/ltp", headers=headers, params={"scrip-codes": scrip_codes}, timeout=10)
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/quotes/full")
def get_quotes_full(scrip_codes: str, user_id: int = Depends(get_current_user)):
    if not INDSTOCKS_TOKEN:
        raise HTTPException(status_code=400, detail="INDSTOCKS_TOKEN not configured")
    headers = {"Authorization": INDSTOCKS_TOKEN, "Content-Type": "application/json"}
    try:
        resp = requests.get(f"{INDSTOCKS_BASE}/market/quotes/full", headers=headers, params={"scrip-codes": scrip_codes}, timeout=10)
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/user/profile")
def get_user_profile(user_id: int = Depends(get_current_user)):
    if not INDSTOCKS_TOKEN:
        raise HTTPException(status_code=400, detail="INDSTOCKS_TOKEN not configured")
    headers = {"Authorization": INDSTOCKS_TOKEN, "Content-Type": "application/json"}
    try:
        resp = requests.get(f"{INDSTOCKS_BASE}/user/profile", headers=headers, timeout=10)
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))


# ==================== MUTUAL FUNDS ====================

@app.get("/api/mf/schemes")
def mf_schemes(user_id: int = Depends(get_current_user)):
    try:
        resp = requests.get(f"{MFAPI_BASE}/mf", timeout=10)
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/mf/nav/{scheme_code}")
def mf_nav(scheme_code: str, user_id: int = Depends(get_current_user)):
    try:
        resp = requests.get(f"{MFAPI_BASE}/mf/{scheme_code}", timeout=10)
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/mf/history/{scheme_code}")
def mf_history(scheme_code: str, user_id: int = Depends(get_current_user)):
    try:
        resp = requests.get(f"{MFAPI_BASE}/mf/{scheme_code}", timeout=10)
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))


# ==================== INVESTMENTS ====================

class Investment(BaseModel):
    id: float
    name: str
    type: str
    invested: float
    current_value: float
    date: str
    note: Optional[str] = ""


@app.get("/api/investments")
def list_investments(user_id: int = Depends(get_current_user)):
    return database.get_investments(user_id)


@app.post("/api/investments")
def create_investment(inv: Investment, user_id: int = Depends(get_current_user)):
    data = inv.model_dump()
    data["user_id"] = user_id
    database.add_investment(data)
    return {"status": "ok"}


@app.delete("/api/investments/{inv_id}")
def remove_investment(inv_id: float, user_id: int = Depends(get_current_user)):
    database.delete_investment(inv_id, user_id)
    return {"status": "deleted"}


# ==================== EXPENSES ====================

class Expense(BaseModel):
    id: float
    description: str
    amount: float
    date: str
    category: str
    payment_method: Optional[str] = "upi"
    note: Optional[str] = ""


@app.get("/api/expenses")
def list_expenses(user_id: int = Depends(get_current_user)):
    return database.get_expenses(user_id)


@app.post("/api/expenses")
def create_expense(exp: Expense, user_id: int = Depends(get_current_user)):
    data = exp.model_dump()
    data["user_id"] = user_id
    database.add_expense(data)
    return {"status": "ok"}


@app.post("/api/expenses/bulk")
def create_expenses_bulk(exps: List[Expense], user_id: int = Depends(get_current_user)):
    for exp in exps:
        data = exp.model_dump()
        data["user_id"] = user_id
        database.add_expense(data)
    return {"status": "ok", "count": len(exps)}


@app.delete("/api/expenses/{exp_id}")
def remove_expense(exp_id: float, user_id: int = Depends(get_current_user)):
    database.delete_expense(exp_id, user_id)
    return {"status": "deleted"}


# ==================== RECURRING ====================

class RecurringExpense(BaseModel):
    id: float
    name: str
    amount: float
    category: str
    frequency: Optional[str] = "monthly"
    day_of_month: Optional[int] = 1
    active: Optional[int] = 1
    last_paid: Optional[str] = ""


@app.get("/api/recurring")
def list_recurring(user_id: int = Depends(get_current_user)):
    return database.get_recurring_expenses(user_id)


@app.post("/api/recurring")
def create_recurring(rec: RecurringExpense, user_id: int = Depends(get_current_user)):
    data = rec.model_dump()
    data["user_id"] = user_id
    database.add_recurring_expense(data)
    return {"status": "ok"}


@app.delete("/api/recurring/{rec_id}")
def remove_recurring(rec_id: float, user_id: int = Depends(get_current_user)):
    database.delete_recurring_expense(rec_id, user_id)
    return {"status": "deleted"}


@app.post("/api/recurring/{rec_id}/paid")
def mark_recurring_paid(rec_id: float, user_id: int = Depends(get_current_user)):
    today = datetime.now().strftime("%Y-%m-%d")
    database.update_recurring_last_paid(rec_id, user_id, today)
    return {"status": "ok", "last_paid": today}


# ==================== BUDGETS ====================

class Budget(BaseModel):
    id: float
    category: str
    limit: float


@app.get("/api/budgets")
def list_budgets(user_id: int = Depends(get_current_user)):
    rows = database.get_budgets(user_id)
    for row in rows:
        row["limit"] = row.pop("limit_amount")
    return rows


@app.post("/api/budgets")
def create_budget(budget: Budget, user_id: int = Depends(get_current_user)):
    data = budget.model_dump()
    data["user_id"] = user_id
    data["limit_amount"] = data.pop("limit")
    database.add_budget(data)
    return {"status": "ok"}


@app.delete("/api/budgets/{budget_id}")
def remove_budget(budget_id: float, user_id: int = Depends(get_current_user)):
    database.delete_budget(budget_id, user_id)
    return {"status": "deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
