# Project Structure

```
GetHiredWIthAI/
│
├── 📄 script.py                    # Main Streamlit application
│   ├── Authentication (Login/Signup)
│   ├── Profile Management
│   ├── Resume Upload & Parsing
│   ├── Job Search & Matching
│   └── Resume Customization & Download
│
├── 📄 requirements.txt             # Python dependencies
│   ├── streamlit==1.31.0
│   ├── openai==1.3.5
│   ├── supabase==2.0.0
│   ├── requests==2.31.0
│   ├── PyPDF2==3.0.1
│   ├── reportlab==4.0.7
│   └── ...
│
├── 🐳 Dockerfile                   # Container configuration
│   └── Python 3.10 slim + Streamlit
│
├── 📁 .streamlit/
│   ├── config.toml                 # Streamlit settings
│   └── secrets.toml                # Local secrets (gitignored)
│
├── 📄 databricks_testNotebook.py   # AI function testing
│   ├── Resume parsing tests
│   ├── Job scoring tests
│   ├── Customization tests
│   └── Cost analysis
│
├── 📄 README.md                    # Project documentation
├── 📄 SETUP.md                     # Installation guide
├── 📄 LICENSE                      # MIT License
├── 📄 .gitignore                   # Ignored files
└── 📄 .env.example                 # Environment template
```

## Core Components

### 1. Authentication System
```
Location: script.py (lines 50-150)
├── hash_password()          # SHA-256 password hashing
├── check_user_exists()      # Email lookup
├── verify_login()           # Credential validation
├── create_session_token()   # 30-day JWT-like tokens
└── validate_session_token() # Token verification
```

### 2. Database Layer (Supabase)
```
Tables:
├── users                    # User profiles
├── resumes                  # Uploaded resumes
├── applied_jobs             # Job applications
└── sessions                 # Auth tokens
```

### 3. Job Search APIs
```
├── fetch_jobs_indeed()      # JSearch RapidAPI
├── fetch_jobs_adzuna()      # Adzuna API
└── fetch_jobs_multi()       # Combined search
```

### 4. AI Functions (OpenAI)
```
├── GPT-3.5-Turbo
│   ├── Resume parsing
│   └── Batch job scoring
│
└── GPT-4o
    └── Resume customization
```

### 5. UI Pages
```
├── Home                     # Landing page
├── Login                    # User login
├── Signup                   # Registration
├── Profile                  # User profile
├── Upload                   # Resume upload
├── Search                   # Job search
└── Personalize              # Resume customization
```

## Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│  Streamlit  │────▶│  Supabase   │
│  (Browser)  │◀────│   (UI)      │◀────│  (Database) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   OpenAI    │
                    (GPT-3.5-Turbo)   │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐     ┌─────────────────────┐ 
                    │  Job APIs   │────▶│Resume Customization│
                    │ (JSearch)   │◀────│     (GPT-4o)       │
                    └─────────────┘     └─────────────────────┘
```

## Environment Variables

```
Production (Railway):
├── OPENAI_API_KEY          # OpenAI API
├── SUPABASE_URL            # Database URL
├── SUPABASE_KEY            # Database key
├── RAPID_API_KEY           # JSearch API
├── ADZUNA_APP_ID           # Adzuna ID
└── ADZUNA_APP_KEY          # Adzuna key

Local (.streamlit/secrets.toml):
├── openai_api_key
├── supabase_url
├── supabase_key
├── rapid_api_key
├── adzuna_app_id
└── adzuna_app_key
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Railway                          │
│  ┌───────────────────────────────────────────────┐  │
│  │              Docker Container                 │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │         Streamlit App (Port 8080)       │  │  │
│  │  │              script.py                  │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
│                        │                            │
│                        ▼                            │
│  ┌───────────────────────────────────────────────┐  │
│  │            Custom Domain                      │  │
│  │         www.gethiredwithai.co                │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
      ┌─────────┐  ┌──────────┐  ┌──────────┐
      │ Supabase│  │  OpenAI  │  │ RapidAPI │
      │   DB    │  │   GPT    │  │  JSearch │
      └─────────┘  └──────────┘  └──────────┘
```
