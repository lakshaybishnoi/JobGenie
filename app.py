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
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .job-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e6e6e6;
        margin-bottom: 1rem;
    }
    .match-score-high {
        color: #28a745;
        font-weight: bold;
    }
    .match-score-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .match-score-low {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Title and description
    st.title("🧞‍♂️ JobGenie - AI-Powered Job Discovery")
    st.markdown("Find and match jobs using AI-powered resume analysis and multiple job sources")
    
    # Sidebar navigation
    st.sidebar.title("🔍 Navigation")
    
    # Test database connection
    if not st.session_state.db.test_connection():
        st.sidebar.error("⚠️ Database connection failed")
        st.error("Unable to connect to the database. Please check your database configuration.")
        return
    else:
        st.sidebar.success("✅ Database connected")
    
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
    st.header("🏠 Dashboard")
    
    # Get statistics
    try:
        stats = st.session_state.db.get_job_statistics()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Jobs", stats['total_jobs'])
        with col2:
            st.metric("Applied Jobs", stats['applied_jobs'])
        with col3:
            st.metric("Recent Jobs (7 days)", stats['recent_jobs'])
        with col4:
            st.metric("Application Rate", f"{stats['application_rate']:.1f}%")
        
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
        if not search_keywords.strip():
            st.error("⚠️ Please enter job keywords to search.")
            return
        
        with st.spinner("🔍 Searching for jobs..."):
            try:
                # Perform job search
                jobs = st.session_state.scraper.search_jobs(
                    keywords=search_keywords.strip(),
                    location=search_location.strip(),
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
            # Display skills in a nice grid
            skills = resume_data['skills']
            cols = st.columns(3)
            for i, skill in enumerate(skills):
                with cols[i % 3]:
                    st.success(f"✅ {skill}")
        else:
            st.info("No technical skills detected. Consider adding a dedicated skills section.")
    
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
    
    # Display job cards
    for job in filtered_jobs:
        match_score = job['match_score']
        score_color = calculate_match_score_color(match_score)
        
        with st.container():
            # Job header
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### {job['title']} at {job['company']}")
            with col2:
                st.markdown(f"<h3 style='color: {score_color}; text-align: right;'>{match_score:.1f}%</h3>", unsafe_allow_html=True)
            
            # Job details
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"📍 **Location:** {format_location(job.get('location', ''))}")
            with col2:
                st.write(f"💰 **Salary:** {format_salary(job.get('salary', ''))}")
            with col3:
                st.write(f"📅 **Posted:** {format_date(job.get('date_posted', ''))}")
            
            # Job summary
            if job.get('summary'):
                st.write(f"**Summary:** {truncate_text(job['summary'], 400)}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if job.get('url'):
                    st.link_button("🔗 View Full Job", job['url'], use_container_width=True)
            with col2:
                if not job.get('applied'):
                    if st.button(f"✅ Mark as Applied", key=f"apply_{job['id']}", use_container_width=True):
                        st.session_state.db.mark_job_applied(job['id'])
                        st.success("Marked as applied!")
                        st.rerun()
                else:
                    st.success("✅ Applied")
            with col3:
                if st.button(f"📊 Match Details", key=f"details_{job['id']}", use_container_width=True):
                    show_match_explanation(job)
            
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
            st.metric("Skills Match", f"{explanation['skills_score']:.1f}%")
        with col2:
            st.metric("Experience Match", f"{explanation['experience_score']:.1f}%")
        with col3:
            st.metric("Education Match", f"{explanation['education_score']:.1f}%")
        with col4:
            st.metric("Text Similarity", f"{explanation['text_similarity_score']:.1f}%")
        
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
