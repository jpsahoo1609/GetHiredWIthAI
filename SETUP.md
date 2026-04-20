# Setup Guide

Complete setup instructions for GetHiredWithAI.

## Prerequisites

- Python 3.10 or higher
- Git
- Code editor (VS Code recommended)

## Step 1: Clone Repository

```bash
git clone https://github.com/jpsahoo1609/GetHiredWIthAI.git
cd GetHiredWIthAI
```

## Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Get API Keys

### OpenAI API Key
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up / Login
3. Go to API Keys → Create new secret key
4. Copy the key (starts with `sk-`)

### Supabase
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Go to Settings → API
4. Copy **Project URL** and **anon/public key**

### RapidAPI (Job Search)
1. Go to [rapidapi.com](https://rapidapi.com)
2. Subscribe to **JSearch API**
3. Copy your API key

### Adzuna (Job Search)
1. Go to [developer.adzuna.com](https://developer.adzuna.com)
2. Create account → Get App ID and App Key

## Step 5: Set Environment Variables

### Option A: Railway/Production
Add these in Railway dashboard → Variables:
```
OPENAI_API_KEY=sk-proj-xxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx
RAPID_API_KEY=xxx
ADZUNA_APP_ID=xxx
ADZUNA_APP_KEY=xxx
```

### Option B: Local Development
Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` with your keys.

Or create `.streamlit/secrets.toml`:
```toml
openai_api_key = "sk-proj-xxx"
supabase_url = "https://xxx.supabase.co"
supabase_key = "eyJxxx"
rapid_api_key = "xxx"
adzuna_app_id = "xxx"
adzuna_app_key = "xxx"
```

## Step 6: Setup Database

Run these SQL commands in Supabase SQL Editor:

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    password TEXT,
    name TEXT,
    age INTEGER,
    gender TEXT,
    location TEXT,
    experience TEXT,
    target_roles TEXT,
    employment_type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Resumes table
CREATE TABLE resumes (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    original_text TEXT,
    parsed_skills TEXT,
    parsed_experience INTEGER,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Applied jobs table
CREATE TABLE applied_jobs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    job_id TEXT,
    job_title TEXT,
    job_company TEXT,
    match_score FLOAT,
    applied_at TIMESTAMP DEFAULT NOW()
);

-- Sessions table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- Indexes
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
```

## Step 7: Run Locally

```bash
streamlit run script.py
```

Open browser: `http://localhost:8501`

## Step 8: Deploy to Railway

1. Push code to GitHub
2. Go to [railway.app](https://railway.app)
3. New Project → Deploy from GitHub
4. Select your repo
5. Add environment variables
6. Deploy!

## Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt --upgrade
```

### "API key not found" error
- Check environment variables are set correctly
- Restart terminal after setting variables

### "Supabase connection failed"
- Verify SUPABASE_URL and SUPABASE_KEY
- Check if tables are created

### Port already in use
```bash
streamlit run script.py --server.port 8502
```

## Need Help?

Open an issue on GitHub or contact the author.
