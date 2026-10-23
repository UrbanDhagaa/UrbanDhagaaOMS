# UrbanDhagaa — Order Management System (OMS)

A production-grade, modular monolith designed for corporate merchandise, branded apparel, employee welcome kits, and corporate gifting.

---

## 🏛️ System Architecture

- **Backend**: Python 3.15 + FastAPI modular application
- **Database Layer**: SQLAlchemy 2.x async ORM with Alembic migrations
  - Built-in connection pool pre-ping & Supabase connection pooler (PgBouncer) compatibility (`statement_cache_size=0`)
  - Automatic database schema bootstrapping on first run
- **Authentication & RBAC**: JWT (HMAC-SHA256) with native bcrypt password hashing & role-based access control (`ADMIN`, `SALES`, `OPERATIONS`, `DESIGNER`, `PROCUREMENT`, `ACCOUNTS`, `READ_ONLY`)
- **Frontend**: React 18 + Vite with clean minimalist styling, dynamic KPI summaries, and responsive desktop/mobile layouts
- **Repository Structure**: Monorepo with both `/backend` and `/frontend` in a single repository for unified versioning and simplified deployments.

---

## 💡 Monorepo Deployment: Do You Need 2 Separate Repositories?

**No.** A single repository contains both `/backend` and `/frontend` and is the recommended industry standard:
- **Vercel** allows you to select `frontend` as the **Root Directory**, automatically building and deploying only the frontend whenever you push changes.
- **Render** allows you to deploy the backend directly from the same repository (via root or `backend` directory, or automatically using the included `render.yaml` blueprint).

---

## 🚀 Production Deployment Guide

### Part 1: Deploy Backend on Render.com

#### Option A: Using Render Blueprint (`render.yaml`) — Recommended
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** → **Blueprint**.
3. Connect your GitHub repository: `https://github.com/UrbanDhagaa/UrbanDhagaaOMS.git`.
4. Render will automatically detect `render.yaml`.
5. Enter your `DATABASE_URL` (Supabase connection string) when prompted.
6. Click **Apply**. Render will automatically provision the service, install dependencies, and start the app.

#### Option B: Manual Web Service Setup on Render
1. Click **New +** → **Web Service**.
2. Connect your GitHub repository: `https://github.com/UrbanDhagaa/UrbanDhagaaOMS.git`.
3. Configure the following service settings:
   - **Name**: `urbandhagaa-oms-backend`
   - **Runtime**: `Python 3`
   - **Branch**: `main` (or `master`)
   - **Root Directory**: Leave blank (or enter `backend` if deploying only from subfolder)
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT --workers 2`
   - **Health Check Path**: `/api/v1/health`
4. Add the following **Environment Variables**:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `ENVIRONMENT` | `production` | Enables production mode |
   | `DEBUG` | `false` | Disables debug logs |
   | `DATABASE_URL` | `postgresql+asyncpg://postgres:[PASS]@[HOST]:5432/postgres` | Your Supabase connection string |
   | `SECRET_KEY` | *(Click "Generate" or enter a secure 64+ char random string)* | Used for JWT encryption |
   | `CORS_ORIGINS` | `https://your-frontend.vercel.app` *(or `*` during initial testing)* | Allowed origins for API requests |
5. Click **Create Web Service**.
6. Once deployed, note down your Render service URL (e.g., `https://urbandhagaa-oms-backend.onrender.com`).

---

### Part 2: Deploy Frontend on Vercel

1. Log in to [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** → **Project**.
3. Import your GitHub repository: `https://github.com/UrbanDhagaa/UrbanDhagaaOMS.git`.
4. Configure the project:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select `frontend` (crucial!)
   - **Build Command**: `npm run build` (detected automatically)
   - **Output Directory**: `dist` (detected automatically)
5. Under **Environment Variables**, add:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `VITE_API_BASE_URL` | `https://urbandhagaa-oms-backend.onrender.com` | Your deployed Render backend URL (no trailing slash) |
6. Click **Deploy**.
7. Once deployed, copy your production Vercel domain (e.g., `https://urbandhagaa-oms.vercel.app`).
8. *(Optional)* Return to Render and update `CORS_ORIGINS` to match your Vercel URL: `https://urbandhagaa-oms.vercel.app`.

---

## 🗄️ Supabase PostgreSQL Setup

1. Create a project on [Supabase](https://supabase.com/).
2. Under **Project Settings** → **Database** → **Connection string**:
   - Select **URI** (or **Session Pooler**).
   - Format: `postgresql+asyncpg://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres`
   *(Note: The backend automatically normalizes `postgres://` or `postgresql://` to `postgresql+asyncpg://`).*
3. The application automatically creates all tables and seeds the initial default administrator on first startup.
4. *(Optional)* If you prefer manual Alembic migrations:
   ```bash
   export PYTHONPATH=backend
   alembic upgrade head
   ```

---

## 🔑 Default Administrator Credentials

Upon first startup, the database automatically seeds the root administrator account:
- **Email**: `admin@urbandhagaa.com`
- **Password**: `Admin@12345`

*Note: Change the default admin password immediately in production.*

---

## 💻 Local Development Setup

### Backend
```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Run FastAPI server
python backend/run.py
```
Backend will be live at `http://127.0.0.1:8000` (`/docs` for Swagger UI).

### Frontend
```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```
Frontend will be live at `http://localhost:5173`. In development, requests to `/api` are automatically proxied to `http://127.0.0.1:8000`.

### Running Automated Tests
```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\pytest -v backend\tests
```
