# GetHiredWithAI 🚀

AI-powered resume optimization and job matching platform. Upload your resume once, get personalized versions for every job application.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 What It Does

- **Smart Resume Parsing** — AI extracts skills, experience, and achievements from your resume
- **Job Matching** — Scores jobs based on your profile compatibility (0-100%)
- **Resume Customization** — GPT-4 rewrites your resume for each specific job
- **ATS Optimization** — Formats resumes to pass applicant tracking systems
- **Application Tracking** — Track all your job applications in one place

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| AI/LLM | OpenAI GPT-4, GPT-3.5 |
| Database | Supabase (PostgreSQL) |
| Auth | Custom session tokens |
| Job APIs | JSearch (RapidAPI), Adzuna |
| Hosting | Railway |
| Domain | Namecheap |

## 🚀 Live Demo

**[https://www.gethiredwithai.co](https://www.gethiredwithai.co)**

## 📸 Screenshots

| Home | Job Search | Resume Customization |
|------|------------|---------------------|
| Modern landing page | AI-matched jobs with scores | GPT-4 powered rewrites |

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key
- Supabase account
- RapidAPI key (for job search)

### Installation

```bash
# Clone repository
git clone https://github.com/jpsahoo1609/GetHiredWIthAI.git
cd GetHiredWIthAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run locally
streamlit run script.py
```

### Environment Variables

```env
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
RAPID_API_KEY=xxx
ADZUNA_APP_ID=xxx
ADZUNA_APP_KEY=xxx
```

## 📁 Project Structure

```
GetHiredWIthAI/
├── script.py              # Main Streamlit application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── databricks_testNotebook.py  # AI function testing
├── README.md
├── SETUP.md
├── LICENSE
└── .gitignore
```

## 🔧 Features Breakdown

### 1. Resume Parsing (GPT-3.5)
- Extracts skills, experience, companies, education
- Cost: ~$0.0015 per resume
- Speed: ~2 seconds

### 2. Job Matching (Batch Scoring)
- Scores multiple jobs in single API call
- 80% cost savings vs individual scoring
- Cost: ~$0.015 for 20 jobs

### 3. Resume Customization (GPT-4)
- Rewrites resume for specific job descriptions
- Maintains truthfulness while optimizing keywords
- Cost: ~$0.045 per customization

### 4. Database Schema

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    name TEXT,
    location TEXT,
    experience TEXT,
    target_roles TEXT
);

-- Resumes table
CREATE TABLE resumes (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    original_text TEXT,
    parsed_skills TEXT,
    parsed_experience INTEGER
);

-- Applied jobs table
CREATE TABLE applied_jobs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    job_title TEXT,
    job_company TEXT,
    match_score FLOAT
);

-- Sessions table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    token TEXT UNIQUE,
    expires_at TIMESTAMP
);
```

## 💰 Cost Analysis (1000 Users/Month)

| Service | Cost |
|---------|------|
| OpenAI API | ~$15 |
| Supabase | $0 (free tier) |
| Railway | $5 |
| Domain | $2/month |
| **Total** | **~$22/month** |

## 🚢 Deployment

### Railway (Recommended)

1. Connect GitHub repo to Railway
2. Add environment variables
3. Deploy automatically on push

### Docker

```bash
docker build -t gethiredwithai .
docker run -p 8080:8080 gethiredwithai
```

## 🗺️ Roadmap

- [x] User authentication
- [x] Resume parsing
- [x] Job search integration
- [x] AI resume customization
- [x] PDF download
- [ ] Email notifications
- [ ] Chrome extension
- [ ] Mobile app
- [ ] Interview preparation AI

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 👨‍💻 Author

**JP Sahoo**
- GitHub: [@jpsahoo1609](https://github.com/jpsahoo1609)
- Website: [gethiredwithai.co](https://www.gethiredwithai.co)

## 🙏 Acknowledgments

- OpenAI for GPT models
- Streamlit for the amazing framework
- Railway for easy deployment
- JSearch & Adzuna for job APIs

---

⭐ **Star this repo if it helped you land a job!**
