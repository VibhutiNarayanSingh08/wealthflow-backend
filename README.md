# WealthFlow Backend

FastAPI backend with JWT auth, user-scoped data, and PostgreSQL/SQLite support.

## Features

- JWT authentication (login/register)
- User-scoped CRUD for expenses, investments, budgets, recurring
- IndStocks broker API proxy
- Mutual fund NAV lookup via mfapi.in
- SQLite (dev) / PostgreSQL (prod)

## Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env
cp .env.example .env
# Edit .env and set JWT_SECRET

# 3. Run server
python server.py

# Server runs on http://localhost:8000
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | **Yes** | 64+ char secret for JWT tokens |
| `DATABASE_URL` | No | PostgreSQL URL (Render provides this) |
| `CORS_ORIGINS` | No | Comma-separated allowed origins. Default: `*` |
| `INDSTOCKS_TOKEN` | No | IndStocks broker API token |

## Deploy to Render (Recommended Free Tier)

1. Push this `backend/` folder to a GitHub repo
2. Create a new **Web Service** on [render.com](https://render.com)
3. Connect your GitHub repo
4. Set environment variables in Render dashboard:
   - `JWT_SECRET` → `openssl rand -hex 32`
   - `CORS_ORIGINS` → your frontend URL (e.g., `https://wealthflow.vercel.app`)
5. Deploy

### With PostgreSQL on Render

1. Create a **PostgreSQL** database on Render (free tier available)
2. Copy the **Internal Database URL** to your web service's `DATABASE_URL` env var
3. Redeploy — the app automatically uses PostgreSQL when `DATABASE_URL` is set

## Deploy to Fly.io

```bash
# 1. Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
# 2. Launch
fly launch

# 3. Set secrets
fly secrets set JWT_SECRET=$(openssl rand -hex 32)

# 4. Deploy
fly deploy
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Create account |
| POST | `/auth/login` | No | Get JWT token |
| GET | `/auth/me` | Yes | Current user |
| GET | `/api/expenses` | Yes | List expenses |
| POST | `/api/expenses` | Yes | Add expense |
| DELETE | `/api/expenses/{id}` | Yes | Delete expense |
| GET | `/api/investments` | Yes | List investments |
| POST | `/api/investments` | Yes | Add investment |
| GET | `/api/budgets` | Yes | List budgets |
| POST | `/api/budgets` | Yes | Set budget |
| GET | `/api/recurring` | Yes | List recurring |
| POST | `/api/recurring` | Yes | Add recurring |
| GET | `/api/portfolio` | Yes | Broker holdings |
| GET | `/api/mf/nav/{code}` | Yes | MF NAV |

## Project Structure

```
backend/
├── server.py          # FastAPI app, all endpoints
├── database.py        # SQLite/PostgreSQL abstraction
├── requirements.txt   # Python deps
├── Dockerfile         # Container build
├── render.yaml        # Render deploy config
├── fly.toml           # Fly.io deploy config
└── .env.example       # Env template
```
