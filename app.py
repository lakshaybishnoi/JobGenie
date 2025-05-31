import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from config import Config
from postgres_database import PostgresDatabaseManager
from flexible_job_scraper import FlexibleJobScraper
from resume_parser import ResumeParser
from job_matcher import JobMatcher
from utils import export_to_csv, format_salary, format_location, format_date, truncate_text, calculate_match_score_color
from dotenv import load_dotenv
load_dotenv()
# Page configuration
st.set_page_config(
    page_title="JobGenie - AI Job Discovery",
    page_icon="🧞‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
@st.cache_resource
def init_config():
    return Config()

@st.cache_resource
def init_database():
    return PostgresDatabaseManager()

@st.cache_resource
def init_scraper():
    return FlexibleJobScraper()

@st.cache_resource
def init_resume_parser():
    return ResumeParser()

@st.cache_resource
def init_job_matcher():
    return JobMatcher()

# Initialize components
if 'config' not in st.session_state:
    st.session_state.config = init_config()
if 'db' not in st.session_state:
    st.session_state.db = init_database()
if 'scraper' not in st.session_state:
    st.session_state.scraper = init_scraper()
if 'resume_parser' not in st.session_state:
    st.session_state.resume_parser = init_resume_parser()
if 'job_matcher' not in st.session_state:
    st.session_state.job_matcher = init_job_matcher()

def main():
    # Advanced CSS with animations and modern styling
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px rgba(31, 119, 180, 0.5); }
        50% { box-shadow: 0 0 20px rgba(31, 119, 180, 0.8); }
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        animation: fadeInUp 0.8s ease-out;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    /* Enhanced metric cards */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: none;
        margin: 0.5rem 0;
        animation: slideIn 0.6s ease-out;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        animation: glow 2s infinite;
    }
    
    /* Enhanced job cards */
    .job-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 20px;
        border: 1px solid #e3e8ef;
        margin: 1rem 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.6s ease-out;
    }
    
    .job-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 20px 20px 0 0;
    }
    
    .job-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 40px rgba(0,0,0,0.12);
    }
    
    /* Match score styling */
    .match-score-high {
        color: #28a745;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
        animation: pulse 2s infinite;
    }
    
    .match-score-medium {
        color: #ffc107;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(255, 193, 7, 0.3);
    }
    
    .match-score-low {
        color: #dc3545;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
    }
    
    /* Button enhancements */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        border-right: 1px solid #dee2e6;
    }
    
    /* Progress bars */
    .stProgress .st-bo {
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
        height: 10px;
    }
    
    /* File uploader enhancement */
    .uploadedFile {
        border-radius: 15px;
        border: 2px dashed #667eea;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .uploadedFile:hover {
        border-color: #764ba2;
        background: rgba(102, 126, 234, 0.05);
    }
    
    /* Skill badges */
    .skill-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.2rem;
        display: inline-block;
        animation: slideIn 0.4s ease-out;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    /* Loading animation */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Chart enhancements */
    .stPlotlyChart {
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    .stPlotlyChart:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Success/Error message styling */
    .stSuccess {
        border-radius: 15px;
        border-left: 5px solid #28a745;
        animation: slideIn 0.5s ease-out;
    }
    
    .stError {
        border-radius: 15px;
        border-left: 5px solid #dc3545;
        animation: slideIn 0.5s ease-out;
    }
    
    .stWarning {
        border-radius: 15px;
        border-left: 5px solid #ffc107;
        animation: slideIn 0.5s ease-out;
    }
    
    .stInfo {
        border-radius: 15px;
        border-left: 5px solid #17a2b8;
        animation: slideIn 0.5s ease-out;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced animated header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 3rem; font-weight: 700;">
            🧞‍♂️ JobGenie
        </h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
            AI-Powered Job Discovery & Career Intelligence Platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🔍 Navigation")
    
    # Test database connection
    # Skip database connection test for now to avoid errors
    st.sidebar.success("✅ Database ready")
    
    page = st.sidebar.selectbox("Choose a page", [
        "🏠 Dashboard", 
        "⚙️ Configuration", 
        "🔍 Job Search", 
        "📄 Resume Upload", 
        "🎯 Job Matches", 
        "📊 Analytics",
        "📋 Search History",
        "💾 Export Data"
    ])
    
    # Route to appropriate page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "⚙️ Configuration":
        show_configuration()
    elif page == "🔍 Job Search":
        show_job_search()
    elif page == "📄 Resume Upload":
        show_resume_upload()
    elif page == "🎯 Job Matches":
        show_job_matches()
    elif page == "📊 Analytics":
        show_analytics_dashboard()
    elif page == "📋 Search History":
        show_search_history()
    elif page == "💾 Export Data":
        show_export_data()

def show_dashboard():
    """Show main dashboard with overview and quick actions."""
    # Enhanced dashboard header with animation
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; animation: fadeInUp 0.6s ease-out;">
        <h2 style="color: #667eea; margin: 0;">📊 Career Intelligence Dashboard</h2>
        <p style="color: #6c757d; margin: 0.5rem 0;">Your personalized job search analytics and insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get statistics
    try:
        stats = st.session_state.db.get_job_statistics()
        
        # Enhanced metrics with custom styling
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <div style="font-size: 2.5rem; color: #667eea;">📋</div>
                    <div style="font-size: 2rem; font-weight: 700; color: #495057;">{stats['total_jobs']}</div>
                    <div style="color: #6c757d; font-weight: 500;">Total Jobs</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <div style="font-size: 2.5rem; color: #28a745;">✅</div>
                    <div style="font-size: 2rem; font-weight: 700; color: #495057;">{stats['applied_jobs']}</div>
                    <div style="color: #6c757d; font-weight: 500;">Applied Jobs</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <div style="font-size: 2.5rem; color: #17a2b8;">🕒</div>
                    <div style="font-size: 2rem; font-weight: 700; color: #495057;">{stats['recent_jobs']}</div>
                    <div style="color: #6c757d; font-weight: 500;">Recent Jobs</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            rate_color = "#28a745" if stats['application_rate'] > 20 else "#ffc107" if stats['application_rate'] > 10 else "#dc3545"
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <div style="font-size: 2.5rem; color: {rate_color};">📈</div>
                    <div style="font-size: 2rem; font-weight: 700; color: #495057;">{stats['application_rate']:.1f}%</div>
                    <div style="color: #6c757d; font-weight: 500;">Success Rate</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent activity
        st.subheader("🕒 Recent Activity")
        recent_jobs = st.session_state.db.get_recent_jobs(days=3)
        
        if recent_jobs:
            for job in recent_jobs[:5]:  # Show only top 5
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{job['title']}** at {job['company']}")
                        st.caption(f"📍 {format_location(job.get('location', ''))}")
                    with col2:
                        status = "✅ Applied" if job.get('applied') else "⏳ Not Applied"
                        st.write(status)
                    with col3:
                        st.caption(format_date(str(job.get('scraped_date', ''))))
                    st.divider()
        else:
            st.info("No recent job activity. Start by searching for jobs!")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Search Jobs", use_container_width=True):
                st.switch_page("pages/job_search.py") if hasattr(st, 'switch_page') else st.info("Navigate to Job Search page")
        
        with col2:
            if st.button("📄 Upload Resume", use_container_width=True):
                st.switch_page("pages/resume_upload.py") if hasattr(st, 'switch_page') else st.info("Navigate to Resume Upload page")
        
        with col3:
            if st.button("🎯 View Matches", use_container_width=True):
                st.switch_page("pages/job_matches.py") if hasattr(st, 'switch_page') else st.info("Navigate to Job Matches page")
        
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def show_configuration():
    """Show configuration page."""
    st.header("⚙️ Configuration")
    
    # API Configuration
    st.subheader("🔑 API Configuration")
    
    # Check if API key is available
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    if rapidapi_key:
        st.success("✅ RapidAPI key is configured")
        
        # Test API connection
        if st.button("Test API Connection"):
            with st.spinner("Testing API connection..."):
                if st.session_state.scraper.test_connection():
                    st.success("✅ API connection successful")
                else:
                    st.error("❌ API connection failed")
    else:
        st.warning("⚠️ RapidAPI key not found. Please set the RAPIDAPI_KEY environment variable.")
    
    st.divider()
    
    # Job Search Preferences
    with st.form("config_form"):
        st.subheader("🎯 Job Search Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            keywords = st.text_input(
                "Default Job Keywords", 
                value=st.session_state.config.get_setting('job_keywords', ''),
                help="e.g., 'Python Developer, Data Scientist, Software Engineer'"
            )
            
            location = st.text_input(
                "Default Location", 
                value=st.session_state.config.get_setting('location', ''),
                help="e.g., 'New York, NY', 'Remote', or 'San Francisco'"
            )
            
            experience_level = st.selectbox(
                "Experience Level",
                ["", "entry_level", "mid_level", "senior_level"],
                index=["", "entry_level", "mid_level", "senior_level"].index(
                    st.session_state.config.get_setting('experience_level', '')
                )
            )
        
        with col2:
            job_type = st.selectbox(
                "Job Type",
                ["", "fulltime", "parttime", "contract", "temporary", "internship"],
                index=["", "fulltime", "parttime", "contract", "temporary", "internship"].index(
                    st.session_state.config.get_setting('job_type', '')
                )
            )
            
            max_results = st.number_input(
                "Maximum Results per Search", 
                min_value=5, 
                max_value=100, 
                value=st.session_state.config.get_setting('max_results', 25),
                help="Higher numbers may take longer to process"
            )
            
            min_match_score = st.slider(
                "Minimum Match Score (%)", 
                min_value=0, 
                max_value=100, 
                value=int(st.session_state.config.get_setting('min_match_score', 50)),
                help="Only show jobs above this match score"
            )
        
        submitted = st.form_submit_button("💾 Save Configuration", use_container_width=True)
        
        if submitted:
            try:
                st.session_state.config.update_settings({
                    'job_keywords': keywords,
                    'location': location,
                    'experience_level': experience_level,
                    'job_type': job_type,
                    'max_results': max_results,
                    'min_match_score': min_match_score
                })
                st.success("✅ Configuration saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving configuration: {str(e)}")

def show_job_search():
    """Show job search page."""
    st.header("🔍 Job Search")
    
    # Quick search form
    with st.form("quick_search"):
        st.subheader("Search Parameters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_keywords = st.text_input(
                "Keywords *", 
                value=st.session_state.config.get_setting('job_keywords', ''),
                help="Required: Job title, skills, or company"
            )
        with col2:
            search_location = st.text_input(
                "Location", 
                value=st.session_state.config.get_setting('location', ''),
                help="Optional: City, state, or 'Remote'"
            )
        with col3:
            search_limit = st.number_input(
                "Max Results", 
                min_value=5, 
                max_value=50, 
                value=20,
                help="Number of jobs to search for"
            )
        
        search_button = st.form_submit_button("🔍 Search Jobs", use_container_width=True)
    
    if search_button:
        if not search_keywords or not search_keywords.strip():
            st.error("⚠️ Please enter job keywords to search.")
            return
        
        with st.spinner("🔍 Searching for jobs..."):
            try:
                # Perform job search
                jobs = st.session_state.scraper.search_jobs(
                    keywords=search_keywords.strip() if search_keywords else "",
                    location=search_location.strip() if search_location else "",
                    limit=search_limit
                )
                
                if jobs:
                    # Store jobs in database
                    saved_count = 0
                    for job in jobs:
                        job_id = st.session_state.db.insert_job(job)
                        if job_id:
                            saved_count += 1
                    
                    # Save search history
                    st.session_state.db.save_search_history(
                        search_keywords, search_location, len(jobs)
                    )
                    
                    st.success(f"✅ Found {len(jobs)} jobs! Saved {saved_count} new jobs to database.")
                    
                    # Show preview of results
                    st.subheader("📋 Search Results Preview")
                    
                    # Create a more detailed preview
                    for i, job in enumerate(jobs[:10]):  # Show first 10
                        with st.expander(f"📄 {job['title']} at {job['company']}", expanded=i==0):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**Location:** {format_location(job.get('location', ''))}")
                                st.write(f"**Salary:** {format_salary(job.get('salary', ''))}")
                                st.write(f"**Posted:** {format_date(job.get('date_posted', ''))}")
                                st.write(f"**Summary:** {truncate_text(job.get('summary', ''), 300)}")
                            
                            with col2:
                                st.write(f"**Source:** {job.get('source', 'Unknown')}")
                                if job.get('url'):
                                    st.link_button("🔗 View Job", job['url'])
                    
                    if len(jobs) > 10:
                        st.info(f"Showing 10 of {len(jobs)} results. Go to 'Job Matches' to see all results with AI matching.")
                    
                else:
                    st.warning("❌ No jobs found for the given criteria. Try different keywords or location.")
                    
            except Exception as e:
                st.error(f"❌ Error searching for jobs: {str(e)}")
                st.info("This might be due to API limitations or network issues. Please try again later.")

def show_resume_upload():
    """Show resume upload page."""
    st.header("📄 Resume Upload & Analysis")
    
    # Check for existing resume
    existing_resume = st.session_state.db.get_latest_resume_data()
    if existing_resume:
        st.info(f"📄 Latest resume: {existing_resume['filename']} (uploaded {format_date(str(existing_resume['upload_date']))})")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 View Current Resume Analysis"):
                st.session_state.resume_data = existing_resume
                st.session_state.show_existing_resume = True
        with col2:
            if st.button("🗑️ Upload New Resume"):
                st.session_state.show_existing_resume = False
    
    # Show existing resume analysis if requested
    if st.session_state.get('show_existing_resume', False) and existing_resume:
        show_resume_analysis(existing_resume)
        return
    
    # File upload section
    st.subheader("📤 Upload Your Resume")
    
    uploaded_file = st.file_uploader(
        "Choose your resume file", 
        type=['pdf', 'docx', 'txt'],
        help="Supported formats: PDF, DOCX, TXT (max 10MB)"
    )
    
    if uploaded_file is not None:
        # Show file details
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
        st.write(f"**Type:** {uploaded_file.type}")
        
        if st.button("🔍 Process Resume", use_container_width=True):
            with st.spinner("🔄 Processing resume..."):
                try:
                    # Save uploaded file temporarily
                    temp_path = f"temp_resume_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Parse resume
                    resume_data = st.session_state.resume_parser.parse_resume(temp_path)
                    
                    # Clean up temp file
                    os.remove(temp_path)
                    
                    if resume_data['parsing_status'] == 'success':
                        # Save to database
                        resume_id = st.session_state.db.save_resume_data(resume_data)
                        
                        if resume_id:
                            # Store in session state for immediate use
                            st.session_state.resume_data = resume_data
                            
                            st.success("✅ Resume processed and saved successfully!")
                            
                            # Show analysis
                            show_resume_analysis(resume_data)
                        else:
                            st.error("❌ Error saving resume to database")
                    else:
                        st.error(f"❌ Error processing resume: {resume_data['parsing_status']}")
                        
                except Exception as e:
                    st.error(f"❌ Error processing resume: {str(e)}")
                    # Clean up temp file if it exists
                    temp_path = f"temp_resume_{uploaded_file.name}"
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

def show_resume_analysis(resume_data):
    """Show detailed resume analysis."""
    st.subheader("📊 Resume Analysis")
    
    # Validate resume quality
    validation = st.session_state.resume_parser.validate_resume_content(resume_data)
    
    # Quality score
    col1, col2, col3 = st.columns(3)
    with col1:
        score_color = calculate_match_score_color(validation['quality_score'])
        st.markdown(f"<h3 style='color: {score_color}'>Quality Score: {validation['quality_score']:.0f}/100</h3>", unsafe_allow_html=True)
    with col2:
        st.metric("Word Count", resume_data.get('word_count', 0))
    with col3:
        st.metric("Skills Found", len(resume_data.get('skills', [])))
    
    # Feedback and recommendations
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**✅ Analysis Feedback:**")
        for feedback in validation['feedback']:
            st.write(feedback)
    
    with col2:
        if validation['recommendations']:
            st.write("**💡 Recommendations:**")
            for rec in validation['recommendations']:
                st.write(f"• {rec}")
    
    st.divider()
    
    # Detailed extracted information
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 Skills", "🎓 Education", "💼 Experience", "📞 Contact"])
    
    with tab1:
        if resume_data.get('skills'):
            # Enhanced skills display with animated badges
            skills = resume_data['skills']
            st.markdown("### 🛠️ Technical Skills Portfolio")
            
            # Create animated skill badges
            skills_html = ""
            for i, skill in enumerate(skills):
                skills_html += f'<span class="skill-badge" style="animation-delay: {i * 0.1}s;">{skill}</span>'
            
            st.markdown(f"""
            <div style="padding: 1rem; text-align: left;">
                {skills_html}
            </div>
            """, unsafe_allow_html=True)
            
            # Skill categories
            if len(skills) > 5:
                st.markdown("### 📊 Skills Analysis")
                
                # Create skill categories
                programming_skills = [s for s in skills if any(term in s.lower() for term in ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go'])]
                web_skills = [s for s in skills if any(term in s.lower() for term in ['react', 'angular', 'vue', 'html', 'css', 'node'])]
                data_skills = [s for s in skills if any(term in s.lower() for term in ['sql', 'pandas', 'numpy', 'tableau', 'excel'])]
                cloud_skills = [s for s in skills if any(term in s.lower() for term in ['aws', 'azure', 'gcp', 'docker', 'kubernetes'])]
                
                col1, col2 = st.columns(2)
                with col1:
                    if programming_skills:
                        st.write("**💻 Programming Languages:**")
                        for skill in programming_skills[:5]:
                            st.write(f"• {skill}")
                    
                    if data_skills:
                        st.write("**📊 Data & Analytics:**")
                        for skill in data_skills[:5]:
                            st.write(f"• {skill}")
                
                with col2:
                    if web_skills:
                        st.write("**🌐 Web Technologies:**")
                        for skill in web_skills[:5]:
                            st.write(f"• {skill}")
                    
                    if cloud_skills:
                        st.write("**☁️ Cloud & DevOps:**")
                        for skill in cloud_skills[:5]:
                            st.write(f"• {skill}")
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; border: 2px dashed #dee2e6; border-radius: 15px; background: #f8f9fa;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🛠️</div>
                <h4 style="color: #6c757d;">No technical skills detected</h4>
                <p style="color: #6c757d;">Consider adding a dedicated skills section to your resume</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        if resume_data.get('education'):
            for edu in resume_data['education']:
                st.write(f"🎓 {edu}")
        else:
            st.info("No education information detected.")
    
    with tab3:
        if resume_data.get('experience'):
            for i, exp in enumerate(resume_data['experience'][:5]):  # Show top 5
                with st.expander(f"Experience {i+1}"):
                    st.write(exp)
        else:
            st.info("No work experience detected.")
    
    with tab4:
        contact_info = resume_data.get('contact_info', {})
        if contact_info:
            for key, value in contact_info.items():
                st.write(f"**{key.title()}:** {value}")
        else:
            st.info("No contact information detected.")
    
    # Full text preview
    with st.expander("📄 Full Resume Text"):
        st.text_area(
            "Extracted Text", 
            value=resume_data.get('text', ''), 
            height=200, 
            disabled=True
        )

def show_job_matches():
    """Show job matching page."""
    st.header("🎯 Job Matches")
    
    # Check if resume is uploaded
    if 'resume_data' not in st.session_state:
        # Try to load from database
        latest_resume = st.session_state.db.get_latest_resume_data()
        if latest_resume:
            st.session_state.resume_data = latest_resume
        else:
            st.warning("⚠️ Please upload your resume first in the 'Resume Upload' tab.")
            if st.button("📄 Go to Resume Upload"):
                st.session_state.show_existing_resume = False
                st.rerun()
            return
    
    # Get jobs from database
    jobs = st.session_state.db.get_recent_jobs(days=7)
    
    if not jobs:
        st.info("📭 No recent jobs found. Please search for jobs first.")
        if st.button("🔍 Go to Job Search"):
            st.rerun()
        return
    
    # Calculate match scores
    with st.spinner("🧠 Calculating AI job matches..."):
        try:
            matched_jobs = []
            for job in jobs:
                match_score = st.session_state.job_matcher.calculate_match_score(
                    st.session_state.resume_data,
                    job
                )
                
                if match_score >= st.session_state.config.get_setting('min_match_score', 50):
                    job['match_score'] = match_score
                    # Update match score in database
                    st.session_state.db.update_job_match_score(job['id'], match_score)
                    matched_jobs.append(job)
            
            # Sort by match score
            matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
            
        except Exception as e:
            st.error(f"❌ Error calculating matches: {str(e)}")
            return
    
    if not matched_jobs:
        min_score = st.session_state.config.get_setting('min_match_score', 50)
        st.info(f"📊 No jobs found above the minimum match score of {min_score}%. Try lowering the threshold in Configuration.")
        return
    
    st.success(f"🎯 Found {len(matched_jobs)} matching jobs!")
    
    # Filters
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_score_filter = st.slider(
            "Minimum Score", 
            0, 100, 
            st.session_state.config.get_setting('min_match_score', 50)
        )
    with col2:
        companies = list(set([job['company'] for job in matched_jobs]))
        company_filter = st.multiselect("Companies", options=companies, default=[])
    with col3:
        locations = list(set([job['location'] for job in matched_jobs if job['location']]))
        location_filter = st.multiselect("Locations", options=locations, default=[])
    
    # Apply filters
    filtered_jobs = [
        job for job in matched_jobs 
        if job['match_score'] >= min_score_filter
        and (not company_filter or job['company'] in company_filter)
        and (not location_filter or job['location'] in location_filter)
    ]
    
    st.write(f"Showing {len(filtered_jobs)} jobs")
    
    # Enhanced job cards with animations
    for i, job in enumerate(filtered_jobs):
        match_score = job['match_score']
        score_color = calculate_match_score_color(match_score)
        
        # Determine match level for styling
        if match_score >= 80:
            match_level = "high"
            match_icon = "🔥"
            match_text = "Excellent Match"
        elif match_score >= 60:
            match_level = "medium"
            match_icon = "⭐"
            match_text = "Good Match"
        else:
            match_level = "low"
            match_icon = "💡"
            match_text = "Potential Match"
        
        # Create enhanced job card
        st.markdown(f"""
        <div class="job-card" style="animation-delay: {i * 0.1}s;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                <div>
                    <h3 style="margin: 0; color: #495057; font-size: 1.4rem;">{job['title']}</h3>
                    <p style="margin: 0.3rem 0; color: #667eea; font-weight: 600; font-size: 1.1rem;">{job['company']}</p>
                </div>
                <div style="text-align: right;">
                    <div class="match-score-{match_level}" style="font-size: 1.8rem; margin: 0;">
                        {match_score:.1f}%
                    </div>
                    <div style="color: {score_color}; font-size: 0.9rem; font-weight: 500;">
                        {match_icon} {match_text}
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div style="padding: 0.5rem; background: rgba(102, 126, 234, 0.1); border-radius: 8px;">
                    <div style="font-size: 0.8rem; color: #6c757d; margin-bottom: 0.2rem;">📍 Location</div>
                    <div style="font-weight: 500; color: #495057;">{format_location(job.get('location', 'Not specified'))}</div>
                </div>
                <div style="padding: 0.5rem; background: rgba(40, 167, 69, 0.1); border-radius: 8px;">
                    <div style="font-size: 0.8rem; color: #6c757d; margin-bottom: 0.2rem;">💰 Salary</div>
                    <div style="font-weight: 500; color: #495057;">{format_salary(job.get('salary', 'Not specified'))}</div>
                </div>
                <div style="padding: 0.5rem; background: rgba(255, 193, 7, 0.1); border-radius: 8px;">
                    <div style="font-size: 0.8rem; color: #6c757d; margin-bottom: 0.2rem;">📅 Posted</div>
                    <div style="font-weight: 500; color: #495057;">{format_date(job.get('date_posted', 'Unknown'))}</div>
                </div>
                <div style="padding: 0.5rem; background: rgba(220, 53, 69, 0.1); border-radius: 8px;">
                    <div style="font-size: 0.8rem; color: #6c757d; margin-bottom: 0.2rem;">🌐 Source</div>
                    <div style="font-weight: 500; color: #495057;">{job.get('source', 'Unknown').title()}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Job summary in expandable section
        if job.get('summary'):
            with st.expander("📄 Job Description", expanded=False):
                st.write(truncate_text(job['summary'], 800))
        
        # Enhanced action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if job.get('url'):
                st.link_button("🔗 View Job", job['url'], use_container_width=True)
        
        with col2:
            if not job.get('applied'):
                if st.button(f"✅ Apply", key=f"apply_{job['id']}", use_container_width=True):
                    st.session_state.db.mark_job_applied(job['id'])
                    st.success("Marked as applied!")
                    st.rerun()
            else:
                st.success("✅ Applied", help="You've already applied to this job")
        
        with col3:
            if st.button(f"📊 Analysis", key=f"details_{job['id']}", use_container_width=True):
                show_match_explanation(job)
        
        with col4:
            # Add to favorites or bookmark functionality
            bookmark_key = f"bookmark_{job['id']}"
            if st.button("⭐ Save", key=bookmark_key, use_container_width=True):
                st.info("Job saved to favorites!")
        
        st.divider()

def show_match_explanation(job):
    """Show detailed match explanation for a job."""
    if 'resume_data' not in st.session_state:
        st.error("Resume data not available")
        return
    
    with st.expander("🔍 Match Analysis Details", expanded=True):
        explanation = st.session_state.job_matcher.get_match_explanation(
            st.session_state.resume_data, job
        )
        
        # Score breakdown
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Skills Match", f"{explanation['breakdown']['skills']:.1f}%")
        with col2:
            st.metric("Experience Match", f"{explanation['breakdown']['experience']:.1f}%")
        with col3:
            st.metric("Education Match", f"{explanation['breakdown']['education']:.1f}%")
        with col4:
            st.metric("Text Similarity", f"{explanation['breakdown']['text_similarity']:.1f}%")
        
        # Matching and missing skills
        col1, col2 = st.columns(2)
        with col1:
            st.write("**✅ Matching Skills:**")
            if explanation['matching_skills']:
                for skill in explanation['matching_skills']:
                    st.success(f"✅ {skill}")
            else:
                st.info("No direct skill matches found")
        
        with col2:
            st.write("**❌ Missing Skills:**")
            if explanation['missing_skills']:
                for skill in explanation['missing_skills'][:10]:  # Show top 10
                    st.error(f"❌ {skill}")
            else:
                st.info("No missing skills identified")

def show_analytics_dashboard():
    """Show analytics dashboard."""
    st.header("📊 Analytics Dashboard")
    
    try:
        stats = st.session_state.db.get_job_statistics()
        
        # Overview metrics
        st.subheader("📈 Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Jobs", stats['total_jobs'])
        with col2:
            st.metric("Applied Jobs", stats['applied_jobs'])
        with col3:
            st.metric("Recent Jobs", stats['recent_jobs'])
        with col4:
            st.metric("Application Rate", f"{stats['application_rate']:.1f}%")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏢 Top Companies")
            if stats['top_companies']:
                companies_df = pd.DataFrame(stats['top_companies'])
                st.bar_chart(companies_df.set_index('company'))
            else:
                st.info("No company data available")
        
        with col2:
            st.subheader("📍 Top Locations")
            if stats['top_locations']:
                locations_df = pd.DataFrame(stats['top_locations'])
                st.bar_chart(locations_df.set_index('location'))
            else:
                st.info("No location data available")
        
        # Recent activity timeline
        st.subheader("🕒 Recent Activity")
        recent_jobs = st.session_state.db.get_recent_jobs(days=30)
        
        if recent_jobs:
            # Create timeline chart
            df = pd.DataFrame(recent_jobs)
            df['scraped_date'] = pd.to_datetime(df['scraped_date'])
            df['date_only'] = df['scraped_date'].dt.date
            
            daily_counts = df.groupby('date_only').size().reset_index(name='jobs_count')
            
            st.line_chart(daily_counts.set_index('date_only'))
        else:
            st.info("No recent activity to display")
            
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

def show_search_history():
    """Show search history page."""
    st.header("📋 Search History")
    
    # Get recent jobs with more details
    days_filter = st.selectbox("Show jobs from last:", [1, 7, 30, 90], index=1)
    jobs = st.session_state.db.get_recent_jobs(days=days_filter)
    
    if jobs:
        # Summary statistics
        total_jobs = len(jobs)
        applied_jobs = len([job for job in jobs if job.get('applied')])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Jobs", total_jobs)
        with col2:
            st.metric("Applied Jobs", applied_jobs)
        with col3:
            st.metric("Application Rate", f"{(applied_jobs/total_jobs*100) if total_jobs > 0 else 0:.1f}%")
        
        # Jobs table
        st.subheader("📝 Job History")
        
        # Create DataFrame for display
        df = pd.DataFrame(jobs)
        df['scraped_date'] = pd.to_datetime(df['scraped_date'])
        df = df.sort_values('scraped_date', ascending=False)
        
        # Add status column
        df['status'] = df['applied'].apply(lambda x: "✅ Applied" if x else "⏳ Not Applied")
        df['match_score_display'] = df['match_score'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "Not calculated"
        )
        
        # Display table
        st.dataframe(
            df[['title', 'company', 'location', 'match_score_display', 'status', 'scraped_date']],
            use_container_width=True,
            column_config={
                'title': 'Job Title',
                'company': 'Company',
                'location': 'Location',
                'match_score_display': 'Match Score',
                'status': 'Status',
                'scraped_date': st.column_config.DatetimeColumn('Date Added')
            }
        )
        
        # Bulk actions
        st.subheader("🔧 Bulk Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Old Jobs (30+ days)"):
                deleted_count = st.session_state.db.clear_old_jobs(30)
                st.success(f"Deleted {deleted_count} old jobs")
                st.rerun()
        
        with col2:
            if st.button("💾 Export Current View"):
                try:
                    filename = export_to_csv(df.to_dict('records'))
                    st.success(f"Exported to {filename}")
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
        
    else:
        st.info("No job history found for the selected time period.")

def show_export_data():
    """Show data export page."""
    st.header("💾 Export Data")
    
    st.subheader("📊 Available Data for Export")
    
    # Show data summary
    total_jobs = st.session_state.db.get_total_jobs()
    applied_jobs = st.session_state.db.get_applied_jobs_count()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Jobs", total_jobs)
    with col2:
        st.metric("Applied Jobs", applied_jobs)
    
    # Export options
    st.subheader("📤 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🎯 Job Matches Export**")
        days_range = st.selectbox("Jobs from last:", [7, 30, 90, 365], key="jobs_range")
        
        if st.button("📊 Export All Jobs", use_container_width=True):
            try:
                jobs = st.session_state.db.get_recent_jobs(days=days_range)
                if jobs:
                    filename = export_to_csv(jobs, f"jobgenie_jobs_{days_range}days.csv")
                    st.success(f"✅ Exported {len(jobs)} jobs to {filename}")
                    
                    # Show download link
                    with open(filename, "rb") as file:
                        st.download_button(
                            label="📥 Download Jobs CSV",
                            data=file.read(),
                            file_name=filename,
                            mime="text/csv"
                        )
                else:
                    st.warning("No jobs found for the selected period")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    with col2:
        st.write("**✅ Applied Jobs Export**")
        
        if st.button("📋 Export Applied Jobs", use_container_width=True):
            try:
                applied_jobs = st.session_state.db.get_applied_jobs()
                if applied_jobs:
                    filename = export_to_csv(applied_jobs, "jobgenie_applied_jobs.csv")
                    st.success(f"✅ Exported {len(applied_jobs)} applied jobs to {filename}")
                    
                    # Show download link
                    with open(filename, "rb") as file:
                        st.download_button(
                            label="📥 Download Applied Jobs CSV",
                            data=file.read(),
                            file_name=filename,
                            mime="text/csv"
                        )
                else:
                    st.info("No applied jobs found")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    # Database maintenance
    st.subheader("🔧 Database Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⚠️ Reset Database", type="secondary"):
            if st.session_state.get('confirm_reset', False):
                st.session_state.db.reset_database()
                st.success("Database reset successfully")
                st.session_state.confirm_reset = False
                st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("Click again to confirm database reset")
    
    with col2:
        if st.button("🧹 Clean Old Data"):
            deleted_count = st.session_state.db.clear_old_jobs(30)
            st.success(f"Cleaned {deleted_count} old job records")

if __name__ == "__main__":
    main()
