import streamlit as st
import json
from openai import OpenAI
import time
import requests
from math import ceil
import uuid
from supabase import create_client, Client
from datetime import datetime
import hashlib

st.set_page_config(page_title="AI Resume Agent", layout="wide", initial_sidebar_state="collapsed")

openai_api_key = st.secrets.get("openai_api_key")
rapid_api_key = st.secrets.get("rapid_api_key")
adzuna_app_id = st.secrets.get("adzuna_app_id")
adzuna_app_key = st.secrets.get("adzuna_app_key")
supabase_url = st.secrets.get("supabase_url")
supabase_key = st.secrets.get("supabase_key")

client = OpenAI(api_key=openai_api_key)
supabase: Client = create_client(supabase_url, supabase_key)

st.markdown("""<style>
    .main { background: #0f1419; }
    .stButton > button { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important; color: white !important; border: none !important; padding: 12px 24px !important; border-radius: 8px !important; font-weight: 600 !important; transition: all 0.3s !important; }
    .stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4) !important; }
    .stButton > button:disabled { opacity: 0.5 !important; cursor: not-allowed !important; }
    h1 { color: #ffffff !important; font-weight: 800 !important; }
    h2 { color: #ffffff !important; font-weight: 700 !important; }
    h3 { color: #a8c5ff !important; font-weight: 600 !important; }
    p { color: #e0e0e0 !important; }
    .metric-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; padding: 15px !important; border-radius: 12px !important; text-align: center; }
    .metric-box h3 { color: white !important; font-size: 12px; }
    .metric-box .value { font-size: 28px; font-weight: bold; color: white !important; }
    .job-card { background: #1a1f2e; border-radius: 12px; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; }
    .info-box { background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%); padding: 12px; border-radius: 8px; border-left: 4px solid #667eea; }
    .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 50px; border-radius: 16px; box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3); }
    .tab-bright { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important; color: white !important; }
    .tab-faded { background: rgba(102, 126, 234, 0.2) !important; color: #888888 !important; }
</style>""", unsafe_allow_html=True)

for key in ["user_id", "user_email", "is_logged_in", "profile", "parsed_resume", "resume_text", "selected_job", "current_page", "all_scored_jobs", "customized", "progress_level", "cached_raw_jobs"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False

def validate_session_token(token):
    """Check if token is valid and not expired - returns user_id or None"""
    try:
        response = supabase.table("sessions").select("user_id,expires_at").eq("token", token).execute()
        if response.data and len(response.data) > 0:
            session = response.data[0]
            try:
                expires_at = datetime.fromisoformat(session['expires_at'])
                if expires_at > datetime.now():
                    return session['user_id']
            except:
                pass
        return None
    except:
        return None

def create_session_token(user_id):
    """Create and store session token - valid for 30 days"""
    import secrets
    from datetime import datetime, timedelta
    try:
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        supabase.table("sessions").insert({
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at,
        }).execute()
        return token
    except:
        return None

def get_user_latest_resume(user_id):
    try:
        response = supabase.table("resumes").select("original_text,parsed_skills,parsed_experience").eq("user_id", user_id).order("uploaded_at", desc=True).limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        return None

def verify_login(email, password):
    exists, user = check_user_exists(email)
    if exists and user['password'] == hash_password(password):
        return user
    return None

def check_user_exists(email):
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        return len(response.data) > 0, response.data[0] if response.data else None
    except:
        return False, None

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# Auto-login with session token from URL
if not st.session_state.is_logged_in:
    token = st.query_params.get("token", None)
    page_param = st.query_params.get("page", None)
    
    # Keep Login/Signup pages on refresh
    if st.session_state.page in ["Login", "Signup"] and not page_param:
        page_param = st.session_state.page
    
    # Always restore page from URL if present
    if page_param and page_param in ["Login", "Signup", "Home"]:
        st.session_state.page = page_param
    
    if token:
        user_id = validate_session_token(token)
        if user_id:
            try:
                response = supabase.table("users").select("*").eq("id", user_id).execute()
                if response.data:
                    user = response.data[0]
                    st.session_state.is_logged_in = True
                    st.session_state.user_id = user['id']
                    st.session_state.user_email = user['email']
                    st.session_state.profile = {
                        "name": user['name'], "age": user['age'], "location": user['location'],
                        "experience": user['experience'],
                        "roles": user['target_roles'].split(',') if user['target_roles'] else [],
                        "emp_type": user['employment_type'].split(',') if user['employment_type'] else [],
                        "gender": user.get('gender', ''),
                    }
                    latest = get_user_latest_resume(user['id'])
                    if latest:
                        parsed_skills = latest.get('parsed_skills', '')
                        original_text = latest.get('original_text', '')
                        parsed_exp = latest.get('parsed_experience', 0)
                        if parsed_skills and parsed_skills.strip():
                            skills_list = [s.strip() for s in parsed_skills.split(',') if s.strip()]
                            exp_val = int(parsed_exp) if parsed_exp else 0
                            st.session_state.parsed_resume = {
                                "skills": skills_list,
                                "experience": exp_val,
                            }
                            st.session_state.resume_text = original_text
                            st.session_state.progress_level = 3
                    st.session_state.page = page_param
            except:
                pass
if "progress_level" not in st.session_state:
    st.session_state.progress_level = 0


def format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%d %B %Y')
    except:
        return date_str


def create_user(email, password, profile_data):
    try:
        user_id = str(uuid.uuid4())
        supabase.table("users").insert({
            "id": user_id, "email": email, "password": hash_password(password),
            "name": profile_data.get('name'), "age": profile_data.get('age'),
            "location": profile_data.get('location'), "experience": profile_data.get('experience'),
            "target_roles": ",".join(profile_data.get('roles', [])),
            "employment_type": ",".join(profile_data.get('emp_type', [])),
        }).execute()
        return user_id
    except:
        return None




def update_user_profile(user_id, profile_data):
    try:
        supabase.table("users").update({
            "name": profile_data.get('name'), "age": profile_data.get('age'), "gender": profile_data.get('gender'),
            "location": profile_data.get('location'), "experience": profile_data.get('experience'),
            "target_roles": ",".join(profile_data.get('roles', [])),
            "employment_type": ",".join(profile_data.get('emp_type', [])),
        }).eq("id", user_id).execute()
        return True
    except:
        return False

def save_resume_to_db(user_id, resume_text, parsed_data):
    try:
        resume_id = str(uuid.uuid4())
        result = supabase.table("resumes").insert({
            "id": resume_id, "user_id": user_id, "original_text": resume_text,
            "parsed_skills": ",".join(parsed_data.get('skills', [])),
            "parsed_experience": parsed_data.get('experience', 0),
        }).execute()
        st.success("✓ Resume saved to database")
        return True
    except Exception as e:
        st.error(f"Database save error: {str(e)}")
        return False


def save_applied_job(user_id, job_data, match_score):
    try:
        applied_id = str(uuid.uuid4())
        supabase.table("applied_jobs").insert({
            "id": applied_id, "user_id": user_id, "job_id": job_data['id'],
            "job_title": job_data['title'], "job_company": job_data['company'],
            "match_score": float(match_score),
        }).execute()
        return True
    except:
        return False

def get_user_applied_jobs(user_id):
    try:
        response = supabase.table("applied_jobs").select("job_title,match_score").eq("user_id", user_id).execute()
        return response.data
    except:
        return []

def fetch_jobs_indeed(query, country=""):
    jobs = []
    try:
        for page in [1, 2]:
            params = {"query": query, "page": page}
            if country:
                params["location"] = country
            r = requests.get("https://jsearch.p.rapidapi.com/search", params=params, 
                           headers={"X-RapidAPI-Key": rapid_api_key, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"}, timeout=60)
            if r.status_code == 200:
                for i, job in enumerate(r.json().get('data', [])[:8]):
                    jobs.append({
                        "id": f"indeed_{page}_{i}", "title": job.get('job_title', 'N/A'),
                        "company": job.get('employer_name', 'N/A'), "description": job.get('job_description', '')[:400],
                        "location": job.get('job_location', 'Remote'), "url": job.get('job_apply_link', ''),
                        "posted": job.get('job_posted_at_datetime_utc', 'N/A'), "source": "Indeed"
                    })
            time.sleep(0.5)
    except:
        pass
    return jobs

def fetch_jobs_adzuna(query, country=""):
    jobs = []
    try:
        country_code = "in" if country == "India" else "us"
        url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
        params = {"app_id": adzuna_app_id, "app_key": adzuna_app_key, "what": query, "results_per_page": 10}
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 200:
            for i, job in enumerate(r.json().get('results', [])):
                jobs.append({
                    "id": f"adzuna_{i}", "title": job.get('title', 'N/A'),
                    "company": job.get('company', {}).get('display_name', 'N/A'),
                    "description": job.get('description', '')[:400],
                    "location": job.get('location', {}).get('display_name', 'Remote'),
                    "url": job.get('redirect_url', ''), "posted": job.get('created', 'N/A'),
                    "source": "Adzuna"
                })
    except:
        pass
    return jobs

def fetch_jobs_multi(query, country=""):
    all_jobs = fetch_jobs_indeed(query, country) + fetch_jobs_adzuna(query, country)
    seen, unique = set(), []
    for j in all_jobs:
        key = (j['title'], j['company'])
        if key not in seen:
            seen.add(key)
            unique.append(j)
    return sorted(unique, key=lambda x: str(x.get('posted') or ''), reverse=True)

def render_progress_tabs():
    """Render tabs with progress tracking - non-clickable"""
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    tabs_info = [
        ("Home", 1, col1),
        ("Profile", 2, col2),
        ("Resume", 3, col3),
        ("Jobs", 4, col4),
        ("Personalize", 5, col5),
        ("Logout", 6, col6)
    ]
    
    for tab_name, tab_level, col in tabs_info:
        with col:
            if tab_name == "Logout":
                if st.button(tab_name, use_container_width=True, key=f"nav_{tab_name}"):
                    st.session_state.is_logged_in = False
                    st.session_state.user_id = None
                    st.session_state.page = "Home"
                    st.session_state.progress_level = 0
                    st.query_params["page"] = "Home"
                    st.rerun()
            else:
                is_bright = st.session_state.progress_level >= tab_level
                button_class = "tab-bright" if is_bright else "tab-faded"
                st.markdown(f"""<div style='color: {"white" if is_bright else "#888888"}; font-weight: 600; padding: 12px; border-radius: 8px; background: {"linear-gradient(90deg, #667eea 0%, #764ba2 100%)" if is_bright else "rgba(102, 126, 234, 0.2)"}; text-align: center;'>{tab_name}</div>""", unsafe_allow_html=True)

# HOME PAGE
if st.session_state.page == "Home":
    st.markdown("""<div style='text-align: center; padding: 30px 0;'><h2 style='color: #a8c5ff; font-size: 28px;'>Welcome Hustler 👋</h2><p style='color: #e0e0e0;'>You landed on the right website.</p></div>""", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""<div class='hero' style='color: white;'><h1 style='font-size: 48px; margin: 0; color: white;'>Get Hired with AI</h1><p style='font-size: 18px; color: #e0e0e0; margin-top: 10px;'>Your resume. Perfectly tailored. Every time.</p></div>""", unsafe_allow_html=True)
        st.markdown("""<div style='font-size: 15px; line-height: 1.8; margin: 40px 0;'>
<h2>Why Recruiters Skip Your Resume</h2>
<p>You spend hours crafting the perfect resume, but recruiters scan it in 7 seconds. They're hunting for specific keywords and metrics matching the job description. Your resume that lands interviews for one role becomes invisible to another company with slightly different language.</p>
<p style='color: #888; margin-top: 10px;'><b>Result:</b> 1000s of applications, 10s of callbacks, 0 offers.</p>

<h2 style='margin-top: 30px;'>The Problem Solved</h2>
<p>Stop rewriting your resume 50 times. Upload once. Our AI instantly rewrites it for each job—finding exact keywords recruiters search for, reframing experience to match JD, adding metrics, optimizing for ATS systems.</p>

<h2 style='margin-top: 30px;'>What You Get</h2>
<p style='margin: 8px 0;'><b>✓ Upload Once, Customize Infinitely</b> — Apply to 100 jobs with 100 custom resumes</p>
<p style='margin: 8px 0;'><b>✓ Smart Job Matching</b> — AI ranks 50K+ positions by compatibility in seconds</p>
<p style='margin: 8px 0;'><b>✓ ATS-Optimized Formatting</b> — Beat applicant tracking systems. Pass 99% of filters</p>
<p style='margin: 8px 0;'><b>✓ GPT-4 Powered Rewrites</b> — Professional resume in seconds, one-click downloads</p>
<p style='margin: 8px 0;'><b>✓ Track Every Application</b> — See match %, know which jobs fit best</p>

<h2 style='margin-top: 30px;'>How It Works</h2>
<p style='margin: 5px 0;'><b>1. Upload</b> your resume (PDF or TXT)</p>
<p style='margin: 5px 0;'><b>2. Find</b> AI-matched jobs sorted by fit</p>
<p style='margin: 5px 0;'><b>3. Customize</b> by clicking to rewrite for any position</p>
<p style='margin: 5px 0;'><b>4. Download</b> professional, recruiter-ready PDF</p>
<p style='margin: 5px 0;'><b>5. Apply</b> and track success rates</p>

<p style='margin-top: 20px; color: #a8c5ff;'><b>Ready to actually get hired?</b></p>
</div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("")
        st.markdown("<p style='text-align: center; color: white; font-size: 14px; font-weight: 600;'>Start Now</p>", unsafe_allow_html=True)
        if st.button("LogIn", use_container_width=True, key="home_login"):
            st.session_state.page = "Login"
            st.query_params["page"] = "Login"
            st.rerun()
        st.markdown("")
        if st.button("Create Account (2 mins)", use_container_width=True, key="home_signup"):
            st.session_state.page = "Signup"
            st.query_params["page"] = "Signup"
            st.rerun()

elif st.session_state.page == "Login":
    st.title("LogIn")
    st.markdown("<p style='color: #a8c5ff;'>Email</p>", unsafe_allow_html=True)
    email = st.text_input("", placeholder="your@email.com", key="login_email")
    st.markdown("<p style='color: #a8c5ff;'>Password</p>", unsafe_allow_html=True)
    password = st.text_input("", type="password", key="login_pwd")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("LogIn", use_container_width=True, key="login_submit"):
            user = verify_login(email, password)
            if user:
                st.session_state.is_logged_in = True
                st.session_state.user_id = user['id']
                st.session_state.user_email = user['email']
                st.session_state.profile = {
                    "name": user['name'], "age": user['age'], "gender": user.get('gender', ''), "location": user['location'],
                    "experience": user['experience'],
                    "roles": user['target_roles'].split(',') if user['target_roles'] else [],
                    "emp_type": user['employment_type'].split(',') if user['employment_type'] else [],
                }
                latest = get_user_latest_resume(user['id'])
                if latest:
                    parsed_skills = latest.get('parsed_skills', '')
                    original_text = latest.get('original_text', '')
                    parsed_exp = latest.get('parsed_experience', 0)
                    
                    if parsed_skills and parsed_skills.strip():
                        skills_list = [s.strip() for s in parsed_skills.split(',') if s.strip()]
                        exp_val = int(parsed_exp) if parsed_exp else 0
                        st.session_state.parsed_resume = {
                            "skills": skills_list,
                            "experience": exp_val,
                        }
                        st.session_state.resume_text = original_text
                        st.session_state.progress_level = 3
                    else:
                        st.session_state.progress_level = 1
                else:
                    st.session_state.progress_level = 1
                st.session_state.page = "Profile"
                # Set token in URL for persistence across refreshes
                token = create_session_token(user['id'])
                if token:
                    st.query_params["token"] = token
                    st.query_params["page"] = "Profile"
                st.rerun()
            else:
                st.error("Invalid email or password")
    with col2:
        if st.button("Back", use_container_width=True, key="login_back"):
            st.session_state.page = "Home"
            st.query_params["page"] = "Home"
            st.rerun()

elif st.session_state.page == "Signup":
    st.title("Create Account (2 mins)")
    
    # Initialize variables
    signup_email = st.session_state.get("signup_email_val", "")
    signup_pwd = st.session_state.get("signup_pwd_val", "")
    name = st.session_state.get("signup_name_val", "")
    
    st.markdown("<p style='color: #a8c5ff;'>Email</p>", unsafe_allow_html=True)
    signup_email = st.text_input("", placeholder="your@email.com", key="signup_email")
    st.markdown("<p style='color: #a8c5ff;'>Password</p>", unsafe_allow_html=True)
    signup_pwd = st.text_input("", type="password", key="signup_pwd")
    st.markdown("<p style='color: #a8c5ff;'>Full Name</p>", unsafe_allow_html=True)
    name = st.text_input("", key="signup_name")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p style='color: #a8c5ff;'>Age</p>", unsafe_allow_html=True)
        age = st.number_input("", 18, 80, 25, key="signup_age")
    with col2:
        st.markdown("<p style='color: #a8c5ff;'>Gender</p>", unsafe_allow_html=True)
        selected_gender = st.selectbox("", ["Male", "Female", "Other", "Prefer not to say"], key="signup_gender")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p style='color: #a8c5ff;'>Location</p>", unsafe_allow_html=True)
        location = st.selectbox("", ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune", "Chennai", "Kolkata", "Remote"], key="signup_loc")
    with col2:
        pass
    st.markdown("<p style='color: #a8c5ff;'>Experience</p>", unsafe_allow_html=True)
    experience = st.selectbox("", ["Fresher (0 years)", "0-2 years", "2-5 years", "5-10 years", "10+ years"], key="signup_exp")
    roles = ["Frontend Developer", "Backend Developer", "Full Stack Developer", "Data Scientist", "DevOps Engineer", "Mobile Developer", "QA Engineer", "Product Manager", "AI Engineer", "Data Analyst", "Cloud Architect", "Machine Learning Engineer", "Platform Engineer", "SRE", "DevSecOps Engineer", "Solutions Architect", "Infrastructure Engineer", "Kubernetes Engineer", "Security Engineer", "Generative AI Engineer", "Engineering Manager", "Technical Lead", "Scrum Master", "HR Manager", "Recruitment Specialist", "Business Analyst", "Systems Analyst", "Database Administrator", "Network Engineer", "IT Manager"]
    st.markdown("<p style='color: #a8c5ff;'>Target Roles</p>", unsafe_allow_html=True)
    selected_roles = st.multiselect("", roles, default=[], key="signup_roles")
    st.markdown("<p style='color: #a8c5ff;'>Employment Type</p>", unsafe_allow_html=True)
    emp_type = st.multiselect("", ["Full-time", "Part-time", "Contractor"], default=['Full-time'], key="signup_emp")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Account", use_container_width=True, key="signup_submit"):
            if not signup_email.strip() or not signup_pwd.strip() or not name.strip():
                st.error("Fill email, password, and name")
            else:
                exists, _ = check_user_exists(signup_email)
                if exists:
                    st.error("Email already registered")
                else:
                    st.markdown("<p style='color: white;'>Creating...</p>", unsafe_allow_html=True)
                    time.sleep(1)
                    profile_data = {"name": name, "age": age, "gender": selected_gender, "location": location, "experience": experience, "roles": selected_roles, "emp_type": emp_type}
                    user_id = create_user(signup_email, signup_pwd, profile_data)
                    if user_id:
                        st.session_state.is_logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.user_email = signup_email
                        st.session_state.profile = profile_data
                        st.session_state.parsed_resume = None  # Clear cache for new users
                        st.session_state.resume_text = None
                        st.session_state.progress_level = 1
                        st.session_state.page = "Profile"
                        # Create session token for signup users
                        token = create_session_token(user_id)
                        st.markdown("<p style='color: white;'>Account created!</p>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.query_params["page"] = "Profile"
                        if token:
                            st.query_params["token"] = token
                        st.rerun()
    with col2:
        if st.button("Back", use_container_width=True, key="signup_back"):
            st.session_state.page = "Home"
            st.query_params["page"] = "Home"
            st.rerun()

if st.session_state.is_logged_in and st.session_state.page not in ["Login", "Signup", "Home"]:
    st.markdown(f"""<div style='padding: 10px 0; border-bottom: 1px solid #667eea; margin-bottom: 15px;'>
    <p style='margin: 0; color: #a8c5ff; font-size: 14px;'>👤 {st.session_state.profile.get('name', 'User')}</p>
    </div>""", unsafe_allow_html=True)
    
    render_progress_tabs()
    st.markdown("---")

    if st.session_state.page == "Profile":
        st.title("My Profile")
        profile = st.session_state.profile
        st.markdown("<p style='color: #a8c5ff;'>Email (Read-only)</p>", unsafe_allow_html=True)
        st.text_input("", value=st.session_state.user_email, disabled=True, key="profile_email")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<p style='color: #a8c5ff;'>Full Name</p>", unsafe_allow_html=True)
            name = st.text_input("", value=profile['name'], key="profile_name")
            st.markdown("<p style='color: #a8c5ff;'>Age</p>", unsafe_allow_html=True)
            age = st.number_input("", 18, 80, profile['age'], key="profile_age")
        with col2:
            st.markdown("<p style='color: #a8c5ff;'>Gender</p>", unsafe_allow_html=True)
            genders = ["Male", "Female", "Other", "Prefer not to say"]
            gender_idx = genders.index(profile.get('gender', 'Male')) if profile.get('gender') in genders else 0
            gender = st.selectbox("", genders, index=gender_idx, key="profile_gender")
            st.markdown("<p style='color: #a8c5ff;'>Location</p>", unsafe_allow_html=True)
            locs = ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune", "Chennai", "Kolkata", "Remote"]
            location = st.selectbox("", locs, index=locs.index(profile['location']), key="profile_loc")
            st.markdown("<p style='color: #a8c5ff;'>Experience</p>", unsafe_allow_html=True)
            exps = ["Fresher (0 years)", "0-2 years", "2-5 years", "5-10 years", "10+ years"]
            experience = st.selectbox("", exps, index=exps.index(profile['experience']), key="profile_exp")
        roles = ["Frontend Developer", "Backend Developer", "Full Stack Developer", "Data Scientist", "DevOps Engineer", "Mobile Developer", "QA Engineer", "Product Manager", "AI Engineer", "Data Analyst", "Cloud Architect", "Machine Learning Engineer", "Platform Engineer", "SRE", "DevSecOps Engineer", "Solutions Architect", "Infrastructure Engineer", "Kubernetes Engineer", "Security Engineer", "Generative AI Engineer", "Engineering Manager", "Technical Lead", "Scrum Master", "HR Manager", "Recruitment Specialist", "Business Analyst", "Systems Analyst", "Database Administrator", "Network Engineer", "IT Manager"]
        st.markdown("<p style='color: #a8c5ff;'>Target Roles</p>", unsafe_allow_html=True)
        default_roles = [r for r in profile['roles'] if r in roles]
        selected_roles = st.multiselect("", roles, default=default_roles, key="profile_roles")
        st.markdown("<p style='color: #a8c5ff;'>Employment Type</p>", unsafe_allow_html=True)
        emp_type = st.multiselect("", ["Full-time", "Part-time", "Contractor"], default=profile.get('emp_type', ['Full-time']), key="profile_emp")
        applied = get_user_applied_jobs(st.session_state.user_id)
        st.markdown(f"<h3>Applied Jobs: {len(applied)}</h3>", unsafe_allow_html=True)
        if applied:
            for app in applied:
                st.markdown(f"<div class='info-box'><b>{app['job_title']}</b> | {app['match_score']}% match</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Profile", use_container_width=True, key="profile_update"):
                profile_data = {"name": name, "age": age, "gender": gender, "location": location, "experience": experience, "roles": selected_roles, "emp_type": emp_type}
                if update_user_profile(st.session_state.user_id, profile_data):
                    st.session_state.profile = profile_data
                    st.markdown("<p style='color: white;'>Profile updated!</p>", unsafe_allow_html=True)
                    time.sleep(1)
                    st.rerun()
        with col2:
            if st.button("Next → Resume", use_container_width=True, key="profile_next"):
                st.session_state.progress_level = max(st.session_state.progress_level, 2)
                st.session_state.page = "Upload"
                st.query_params["page"] = "Upload"
                st.rerun()

    elif st.session_state.page == "Upload":
        st.title("Resume")
        profile = st.session_state.profile
        st.markdown(f"<div class='info-box'><b>{profile['name']}</b> | {profile['location']}</div>", unsafe_allow_html=True)
        
        # Auto-fetch resume from DB if missing (e.g., after page refresh)
        if st.session_state.parsed_resume is None and st.session_state.user_id:
            latest = get_user_latest_resume(st.session_state.user_id)
            if latest:
                parsed_skills = latest.get('parsed_skills', '')
                original_text = latest.get('original_text', '')
                parsed_exp = latest.get('parsed_experience', 0)
                
                if parsed_skills and parsed_skills.strip():
                    skills_list = [s.strip() for s in parsed_skills.split(',') if s.strip()]
                    exp_val = int(parsed_exp) if parsed_exp else 0
                    st.session_state.parsed_resume = {
                        "skills": skills_list,
                        "experience": exp_val,
                    }
                    st.session_state.resume_text = original_text
        
        has_resume = st.session_state.parsed_resume is not None
        
        # DEBUG
        if st.session_state.user_id:
            with st.expander("Debug Info"):
                st.write(f"User ID: {st.session_state.user_id}")
                st.write(f"Parsed Resume: {st.session_state.parsed_resume}")
                st.write(f"Resume Text exists: {st.session_state.resume_text is not None}")
        
        if has_resume:
            skills_count = len(st.session_state.parsed_resume.get('skills', []))
            exp_years = st.session_state.parsed_resume.get('experience', 0)
            st.markdown(f"""<div style='background: #1a2332; border: 2px solid #667eea; border-radius: 12px; padding: 20px; margin: 20px 0;'>
            <h3 style='color: #a8c5ff; margin-top: 0;'>✓ Resume Loaded</h3>
            <p style='color: #e0e0e0; margin: 10px 0;'><b>Skills:</b> {skills_count} | <b>Experience:</b> {exp_years} years</p>
            </div>""", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Use This Resume", use_container_width=True, key="use_resume"):
                    st.session_state.progress_level = max(st.session_state.progress_level, 4)
                    st.session_state.page = "Search"
                    st.session_state.current_page = 1
                    st.query_params["page"] = "Search"
                    st.rerun()
            with col2:
                if st.button("Go to Jobs", use_container_width=True, key="go_to_jobs"):
                    st.session_state.progress_level = max(st.session_state.progress_level, 4)
                    st.session_state.page = "Search"
                    st.session_state.current_page = 1
                    st.query_params["page"] = "Search"
                    st.rerun()
            with col3:
                if st.button("Upload New", use_container_width=True, key="upload_new"):
                    st.session_state.parsed_resume = None
                    st.session_state.resume_text = None
                    st.rerun()
            
            st.markdown("")
            if st.button("← Back to Profile", use_container_width=False, key="resume_back_profile"):
                st.session_state.page = "Profile"
                st.query_params["page"] = "Profile"
                st.rerun()
        else:
            st.markdown("<p style='color: #e0e0e0;'><b>No resume found.</b> Upload one to continue.</p>", unsafe_allow_html=True)
            st.markdown("<p style='color: #a8c5ff;'>Upload PDF or TXT</p>", unsafe_allow_html=True)
            file = st.file_uploader("", type=["pdf", "txt"], key="resume_uploader")
            if file:
                try:
                    if file.type == "application/pdf":
                        import PyPDF2
                        text = "".join([p.extract_text() for p in PyPDF2.PdfReader(file).pages])
                    else:
                        text = file.read().decode("utf-8")
                    if st.button("Parse Resume", use_container_width=True, key="resume_parse"):
                        st.markdown("<p style='color: white;'>Analysing...</p>", unsafe_allow_html=True)
                        response = client.chat.completions.create(model="gpt-3.5-turbo", max_tokens=2000, 
                            messages=[{"role": "user", "content": f"""Extract EVERY skill, tool, technology, language, framework, platform, certification mentioned. Return ONLY JSON:
{{"skills": ["Python", "SQL", "Azure", "Power BI"], "experience": 2, "companies": ["TCS"], "roles": ["Engineer"]}}
Include: programming languages, databases, cloud platforms, tools, frameworks, soft skills, certifications, methodologies, anything technical or professional.
Resume: {text}"""}])
                        try:
                            content = response.choices[0].message.content.strip()
                            if "```" in content:
                                content = content.split("```")[1].replace("json", "").strip()
                            parsed = json.loads(content)
                        except:
                            parsed = {"skills": [], "experience": 0, "companies": [], "roles": []}
                        
                        if isinstance(parsed.get('experience'), str):
                            try:
                                parsed['experience'] = int(''.join(filter(str.isdigit, str(parsed['experience']).split()[0])) or 0)
                            except:
                                parsed['experience'] = 0
                        
                        st.session_state.parsed_resume = parsed
                        st.session_state.resume_text = text
                        save_resume_to_db(st.session_state.user_id, text, parsed)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"""<div class='metric-box'><h3>Experience</h3><div class='value'>{parsed.get('experience')}</div></div>""", unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"""<div class='metric-box'><h3>Skills</h3><div class='value'>{len(parsed.get('skills', []))}</div></div>""", unsafe_allow_html=True)
                        with col3:
                            st.markdown(f"""<div class='metric-box'><h3>Companies</h3><div class='value'>{len(parsed.get('companies', []))}</div></div>""", unsafe_allow_html=True)
                        
                        st.markdown("<h3 style='color: #a8c5ff;'>Your Skills:</h3>", unsafe_allow_html=True)
                        st.markdown(f"<div class='info-box'>{', '.join(parsed.get('skills', []))}</div>", unsafe_allow_html=True)
                        st.markdown("<p style='color: white;'>Parsed!</p>", unsafe_allow_html=True)
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    elif st.session_state.page == "Search":
        st.title("Find Jobs")
        profile = st.session_state.profile
        parsed = st.session_state.parsed_resume
        
        # Auto-restore search results from URL params on refresh
        if st.session_state.all_scored_jobs is None:
            search_roles = st.query_params.get("search_roles", None)
            if search_roles:
                st.info("🔄 Restoring previous search results...")
                
                # Use cached jobs if available, otherwise fetch new
                if st.session_state.get("cached_raw_jobs"):
                    jobs = st.session_state.cached_raw_jobs
                else:
                    roles_list = search_roles.split(",")
                    country_param = st.query_params.get("search_location", "India")
                    jobs = []
                    for role in roles_list:
                        jobs.extend(fetch_jobs_multi(role.strip(), country_param))
                    jobs = jobs[:50]
                    st.session_state.cached_raw_jobs = jobs
                
                if jobs:
                    jobs_text = "\n".join([f"{j['title']} at {j['company']}" for j in jobs[:20]])
                    response = client.chat.completions.create(model="gpt-3.5-turbo", max_tokens=1200, 
                        messages=[{"role": "user", "content": f"""Score jobs 0-100. Return ONLY JSON:
[{{"idx":0,"score":75}}]
Candidate: {parsed.get('experience', 0)}yrs, {','.join(parsed.get('skills', [])[:10])}
Jobs: {jobs_text}"""}])
                    try:
                        content = response.choices[0].message.content.strip()
                        scores = json.loads(content)
                        st.session_state.all_scored_jobs = [{"job": jobs[s['idx']], "score": s['score']} for s in scores if s['idx'] < len(jobs)]
                        st.session_state.current_page = 1
                    except:
                        st.session_state.all_scored_jobs = []
        
        if st.button("← Back to Resume", use_container_width=False, key="search_back_resume"):
            st.session_state.page = "Upload"
            st.query_params["page"] = "Upload"
            st.rerun()
        
        if st.button("📝 Update Profile", use_container_width=False, key="search_to_profile"):
            st.session_state.page = "Profile"
            st.query_params["page"] = "Profile"
            st.rerun()
        
        if not parsed or not st.session_state.resume_text:
            st.error("⚠️ Please upload resume first")
            st.stop()
        
        st.markdown(f"<div class='info-box'>Searching: <b>{', '.join(profile['roles'][:2])}</b> | {parsed.get('experience', 0)} yrs</div>", unsafe_allow_html=True)
        
        if st.button("Search Jobs", use_container_width=True, key="search_submit"):
            st.markdown("<p style='color: white;'>Searching... (30-60s)</p>", unsafe_allow_html=True)
            with st.spinner(""):
                country_param = "India"
                jobs = []
                for role in profile['roles'][:2]:
                    jobs.extend(fetch_jobs_multi(role, country_param))
                jobs = jobs[:50]
                
                # Cache raw jobs in session
                st.session_state.cached_raw_jobs = jobs
                
                # Store search params in URL for persistence on refresh
                st.query_params["search_roles"] = ",".join(profile['roles'][:2])
                st.query_params["search_location"] = country_param
                
                if jobs:
                    jobs_text = "\n".join([f"{j['title']} at {j['company']}" for j in jobs[:20]])
                    response = client.chat.completions.create(model="gpt-3.5-turbo", max_tokens=1200, 
                        messages=[{"role": "user", "content": f"""Score jobs 0-100. Return ONLY JSON:
[{{"idx":0,"score":75}}]
Candidate: {parsed.get('experience', 0)}yrs, {','.join(parsed.get('skills', [])[:10])}
Jobs: {jobs_text}"""}])
                    
                    try:
                        scores_raw = response.choices[0].message.content.strip()
                        if '```' in scores_raw:
                            scores_raw = scores_raw.split('```')[1].replace('json', '').strip()
                        scores = json.loads(scores_raw)
                        if not isinstance(scores, list):
                            scores = [scores]
                        
                        qualified = []
                        for s in scores:
                            if isinstance(s, dict) and 'idx' in s:
                                idx = int(s.get('idx', -1))
                                score = int(s.get('score', 0))
                                if 0 <= idx < len(jobs):
                                    qualified.append({"job": jobs[idx], "score": score})
                        
                        # If scoring returned too few results, show all jobs with 0 score
                        if len(qualified) < len(jobs) // 2:
                            qualified = [{"job": job, "score": 0} for job in jobs]
                        
                        qualified.sort(key=lambda x: x['score'], reverse=True)
                        st.session_state.all_scored_jobs = qualified
                        st.session_state.current_page = 1
                    except:
                        # If scoring fails completely, show all jobs
                        st.session_state.all_scored_jobs = [{"job": job, "score": 0} for job in jobs]
        
        if st.session_state.all_scored_jobs:
            qualified = st.session_state.all_scored_jobs
            st.markdown(f"<h3 style='color: white;'>{len(qualified)} jobs matched</h3>", unsafe_allow_html=True)
            page_size = 10
            total_pages = ceil(len(qualified) / page_size)
            
            start = (st.session_state.current_page - 1) * page_size
            end = start + page_size
            jobs_to_show = qualified[start:end]
            
            for idx, item in enumerate(jobs_to_show):
                job = item['job']
                score = item['score']
                posted_date = format_date(job.get('posted', 'N/A'))
                st.markdown(f"""<div class='job-card'><h4>{start+idx+1}. {job['title']} @ {job['company']} - ({score}% match)</h4><p><i style='font-size: 12px; color: #a8c5ff;'>Posted on {posted_date}</i></p><p>{job['location']}</p></div>""", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if job['url']:
                        st.link_button("Apply", job['url'], use_container_width=True)
                with col2:
                    if st.button("Applied", key=f"applied_{start}_{idx}"):
                        if save_applied_job(st.session_state.user_id, job, score):
                            st.markdown("<p style='color: white;'>Saved!</p>", unsafe_allow_html=True)
                with col3:
                    if st.button("Personalize Resume", key=f"personalize_{start}_{idx}", use_container_width=True):
                        st.session_state.selected_job = job
                        st.session_state.progress_level = max(st.session_state.progress_level, 5)
                        st.session_state.page = "Personalize"
                        st.query_params["page"] = "Personalize"
                        st.query_params["job_id"] = job.get('id', '')
                        st.query_params["job_title"] = job.get('title', '')
                        st.query_params["job_company"] = job.get('company', '')
                        st.query_params["job_desc"] = job.get('description', '')[:500]
                        st.rerun()
            
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Previous", use_container_width=True, disabled=st.session_state.current_page <= 1, key="prev_page"):
                    st.session_state.current_page -= 1
                    st.rerun()
            with col2:
                st.write(f"Page {st.session_state.current_page} of {total_pages}")
            with col3:
                if st.button("Next", use_container_width=True, disabled=st.session_state.current_page >= total_pages, key="next_page"):
                    st.session_state.current_page += 1
                    st.rerun()

    elif st.session_state.page == "Personalize":
        st.title("Personalize Resume")
        
        # Restore job from URL params if not in session (after refresh)
        if st.session_state.selected_job is None:
            job_title = st.query_params.get("job_title", None)
            if job_title:
                st.session_state.selected_job = {
                    "id": st.query_params.get("job_id", ""),
                    "title": job_title,
                    "company": st.query_params.get("job_company", ""),
                    "description": st.query_params.get("job_desc", "")
                }
        
        job = st.session_state.selected_job
        if job:
            st.markdown(f"<div class='info-box'><b>{job['title']}</b> @ <b>{job['company']}</b></div>", unsafe_allow_html=True)
            st.text_area("JD", value=job.get('description', ''), height=150, disabled=True, key="jd_display")
            
            if st.button("Customize Resume", use_container_width=True, key="customize_submit"):
                st.markdown("<p style='color: white;'>Customizing...</p>", unsafe_allow_html=True)
                with st.spinner(""):
                    response = client.chat.completions.create(model="gpt-4o", max_tokens=2000, 
                        messages=[{"role": "user", "content": f"""Rewrite for {job['title']}: include summary, ALL work experience with metrics, education, projects, skills.
Job: {job.get('description', '')[:800]}
Resume: {st.session_state.resume_text[:3000]}
Professional resume ONLY."""}])
                    st.session_state.customized = response.choices[0].message.content
                    st.markdown("<p style='color: white;'>Done!</p>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Back to Jobs", use_container_width=True, key="personalize_back"):
                    st.session_state.page = "Search"
                    st.query_params["page"] = "Search"
                    st.rerun()
            
            if st.session_state.customized:
                st.text_area("Resume", value=st.session_state.customized, height=300, disabled=True, key="customized_display")
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib import colors
                from io import BytesIO
                
                pdf_buffer = BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
                story = []
                styles = getSampleStyleSheet()
                
                # Professional styles
                name_style = ParagraphStyle(name='Name', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1a1a1a'), spaceAfter=2, fontName='Helvetica-Bold')
                section_style = ParagraphStyle(name='Section', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2c3e50'), spaceAfter=8, spaceBefore=12, fontName='Helvetica-Bold', borderPadding=5)
                normal_style = ParagraphStyle(name='Normal', parent=styles['Normal'], fontSize=10.5, leading=13, textColor=colors.HexColor('#1a1a1a'))
                bullet_style = ParagraphStyle(name='Bullet', parent=styles['Normal'], fontSize=10.5, leading=13, textColor=colors.HexColor('#1a1a1a'), leftIndent=20, bulletIndent=8, firstLineIndent=-12)
                company_style = ParagraphStyle(name='Company', parent=styles['Normal'], fontSize=10.5, textColor=colors.HexColor('#2c3e50'), fontName='Helvetica-Bold', spaceAfter=2)
                
                lines = st.session_state.customized.split('\n')
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        story.append(Spacer(1, 0.1*inch))
                    elif stripped.isupper() and len(stripped) > 3:
                        story.append(Paragraph(stripped.replace('**', ''), section_style))
                    elif stripped.startswith(('•', '-', '*')):
                        clean = stripped.lstrip('•-* ').strip()
                        story.append(Paragraph(clean, bullet_style))
                    elif ',' in stripped and any(word in stripped.lower() for word in ['pune', 'bangalore', 'delhi', 'delhi', 'india', 'us', '|', 'pvt', 'ltd']):
                        story.append(Paragraph(stripped, company_style))
                    else:
                        story.append(Paragraph(stripped, normal_style))
                
                doc.build(story)
                pdf_buffer.seek(0)
                st.download_button("Download PDF", pdf_buffer, f"resume_{job['title'].replace(' ', '_')}.pdf", "application/pdf", use_container_width=True, key="download_pdf")
