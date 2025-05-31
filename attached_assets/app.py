import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from config import Config
from postgres_database import PostgresDatabaseManager
from flexible_job_scraper import FlexibleJobScraper
from resume_parser import ResumeParser
from job_matcher import JobMatcher
from utils import export_to_csv

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = Config()
if 'db' not in st.session_state:
    st.session_state.db = PostgresDatabaseManager()
if 'scraper' not in st.session_state:
    st.session_state.scraper = FlexibleJobScraper()
if 'resume_parser' not in st.session_state:
    st.session_state.resume_parser = ResumeParser()
if 'job_matcher' not in st.session_state:
    st.session_state.job_matcher = JobMatcher()

def main():
    st.set_page_config(
        page_title="JobGenie - AI Job Discovery",
        page_icon="🧞‍♂️",
        layout="wide"
    )
    
    st.title("🧞‍♂️ JobGenie - AI-Powered Job Discovery")
    st.markdown("Find and match jobs from Indeed using AI-powered resume analysis")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "Configuration", 
        "Job Search", 
        "Resume Upload", 
        "Job Matches", 
        "Analytics Dashboard",
        "Search History",
        "Export Data"
    ])
    
    if page == "Configuration":
        show_configuration()
    elif page == "Job Search":
        show_job_search()
    elif page == "Resume Upload":
        show_resume_upload()
    elif page == "Job Matches":
        show_job_matches()
    elif page == "Analytics Dashboard":
        show_analytics_dashboard()
    elif page == "Search History":
        show_search_history()
    elif page == "Export Data":
        show_export_data()

def show_configuration():
    st.header("⚙️ Configuration")
    
    with st.form("config_form"):
        st.subheader("Job Search Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            keywords = st.text_input(
                "Job Keywords", 
                value=st.session_state.config.get_setting('job_keywords', ''),
                help="e.g., 'Python Developer, Data Scientist'"
            )
            
            location = st.text_input(
                "Location", 
                value=st.session_state.config.get_setting('location', ''),
                help="e.g., 'New York, NY' or 'Remote'"
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
                value=st.session_state.config.get_setting('max_results', 25)
            )
            
            min_match_score = st.slider(
                "Minimum Match Score (%)", 
                min_value=0, 
                max_value=100, 
                value=int(st.session_state.config.get_setting('min_match_score', 50))
            )
        
        submitted = st.form_submit_button("Save Configuration")
        
        if submitted:
            st.session_state.config.update_settings({
                'job_keywords': keywords,
                'location': location,
                'experience_level': experience_level,
                'job_type': job_type,
                'max_results': max_results,
                'min_match_score': min_match_score
            })
            st.success("Configuration saved successfully!")
            st.rerun()

def show_job_search():
    st.header("🔍 Job Search")
    
    # Quick search form
    with st.form("quick_search"):
        st.subheader("Quick Search")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_keywords = st.text_input("Keywords", value=st.session_state.config.get_setting('job_keywords', ''))
        with col2:
            search_location = st.text_input("Location", value=st.session_state.config.get_setting('location', ''))
        with col3:
            search_limit = st.number_input("Max Results", min_value=5, max_value=50, value=20)
        
        search_button = st.form_submit_button("🔍 Search Jobs")
    
    if search_button:
        if not search_keywords:
            st.error("Please enter job keywords to search.")
            return
        
        with st.spinner("Searching for jobs on Indeed..."):
            try:
                jobs = st.session_state.scraper.search_jobs(
                    keywords=search_keywords,
                    location=search_location,
                    limit=search_limit
                )
                
                if jobs:
                    # Store jobs in database
                    for job in jobs:
                        st.session_state.db.insert_job(job)
                    
                    st.success(f"Found {len(jobs)} jobs! Check the 'Job Matches' tab to see results.")
                    
                    # Show preview of results
                    st.subheader("Search Results Preview")
                    df = pd.DataFrame(jobs)
                    st.dataframe(df[['title', 'company', 'location', 'summary']], use_container_width=True)
                    
                else:
                    st.warning("No jobs found for the given criteria.")
                    
            except Exception as e:
                st.error(f"Error searching for jobs: {str(e)}")

def show_resume_upload():
    st.header("📄 Resume Upload & Analysis")
    
    uploaded_file = st.file_uploader(
        "Upload your resume", 
        type=['pdf', 'docx', 'txt'],
        help="Supported formats: PDF, DOCX, TXT"
    )
    
    if uploaded_file is not None:
        with st.spinner("Processing resume..."):
            try:
                # Save uploaded file temporarily
                temp_path = f"temp_resume_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Parse resume
                resume_data = st.session_state.resume_parser.parse_resume(temp_path)
                
                # Clean up temp file
                os.remove(temp_path)
                
                # Store resume data in session state
                st.session_state.resume_data = resume_data
                
                st.success("Resume processed successfully!")
                
                # Display parsed information
                st.subheader("Extracted Information")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Skills:**")
                    if resume_data.get('skills'):
                        for skill in resume_data['skills']:
                            st.write(f"• {skill}")
                    else:
                        st.write("No skills detected")
                
                with col2:
                    st.write("**Education:**")
                    if resume_data.get('education'):
                        for edu in resume_data['education']:
                            st.write(f"• {edu}")
                    else:
                        st.write("No education information detected")
                
                st.write("**Full Text:**")
                st.text_area("Resume content", value=resume_data.get('text', ''), height=200, disabled=True)
                
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")

def show_job_matches():
    st.header("🎯 Job Matches")
    
    # Check if resume is uploaded
    if 'resume_data' not in st.session_state:
        st.warning("Please upload your resume first in the 'Resume Upload' tab.")
        return
    
    # Get jobs from database
    jobs = st.session_state.db.get_recent_jobs(days=7)
    
    if not jobs:
        st.info("No recent jobs found. Please search for jobs first.")
        return
    
    # Calculate match scores
    with st.spinner("Calculating job matches..."):
        matched_jobs = []
        for job in jobs:
            match_score = st.session_state.job_matcher.calculate_match_score(
                st.session_state.resume_data,
                job
            )
            
            if match_score >= st.session_state.config.get_setting('min_match_score', 50):
                job['match_score'] = match_score
                matched_jobs.append(job)
        
        # Sort by match score
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    
    if not matched_jobs:
        st.info(f"No jobs found above the minimum match score of {st.session_state.config.get_setting('min_match_score', 50)}%")
        return
    
    st.success(f"Found {len(matched_jobs)} matching jobs!")
    
    # Display filters
    col1, col2, col3 = st.columns(3)
    with col1:
        min_score_filter = st.slider("Minimum Score", 0, 100, 50)
    with col2:
        company_filter = st.multiselect(
            "Companies", 
            options=list(set([job['company'] for job in matched_jobs])),
            default=[]
        )
    with col3:
        location_filter = st.multiselect(
            "Locations",
            options=list(set([job['location'] for job in matched_jobs])),
            default=[]
        )
    
    # Apply filters
    filtered_jobs = [
        job for job in matched_jobs 
        if job['match_score'] >= min_score_filter
        and (not company_filter or job['company'] in company_filter)
        and (not location_filter or job['location'] in location_filter)
    ]
    
    # Display job cards
    for job in filtered_jobs:
        with st.expander(f"🎯 {job['match_score']:.1f}% - {job['title']} at {job['company']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Company:** {job['company']}")
                st.write(f"**Location:** {job['location']}")
                st.write(f"**Posted:** {job.get('date_posted', 'Unknown')}")
                st.write(f"**Summary:** {job.get('summary', 'No summary available')}")
                
                if job.get('requirements'):
                    st.write("**Requirements:**")
                    st.write(job['requirements'])
            
            with col2:
                st.metric("Match Score", f"{job['match_score']:.1f}%")
                
                if job.get('url'):
                    st.link_button("Apply Now", job['url'])
                
                if st.button(f"Mark as Applied", key=f"applied_{job['id']}"):
                    st.session_state.db.mark_job_applied(job['id'])
                    st.success("Marked as applied!")
                    st.rerun()

def show_search_history():
    st.header("📊 Search History")
    
    # Get search statistics
    total_jobs = st.session_state.db.get_total_jobs()
    applied_jobs = st.session_state.db.get_applied_jobs_count()
    recent_jobs = len(st.session_state.db.get_recent_jobs(days=7))
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Jobs Scraped", total_jobs)
    with col2:
        st.metric("Jobs Applied To", applied_jobs)
    with col3:
        st.metric("Recent Jobs (7 days)", recent_jobs)
    
    # Jobs table
    st.subheader("Recent Job History")
    
    days_filter = st.selectbox("Show jobs from last:", [1, 7, 30, 90], index=1)
    jobs = st.session_state.db.get_recent_jobs(days=days_filter)
    
    if jobs:
        df = pd.DataFrame(jobs)
        df['scraped_date'] = pd.to_datetime(df['scraped_date'])
        df = df.sort_values('scraped_date', ascending=False)
        
        # Add applied status
        df['status'] = df['applied'].apply(lambda x: "✅ Applied" if x else "⏳ Not Applied")
        
        st.dataframe(
            df[['title', 'company', 'location', 'status', 'scraped_date']],
            use_container_width=True,
            column_config={
                'scraped_date': st.column_config.DatetimeColumn(
                    'Scraped Date',
                    format='DD/MM/YYYY HH:mm'
                )
            }
        )
    else:
        st.info("No job history available.")

def show_export_data():
    st.header("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Export Job Data")
        days_export = st.selectbox("Export jobs from last:", [7, 30, 90, 365], index=1)
        
        if st.button("Export to CSV"):
            jobs = st.session_state.db.get_recent_jobs(days=days_export)
            if jobs:
                csv_data = export_to_csv(jobs)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"jobgenie_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export.")
    
    with col2:
        st.subheader("Database Management")
        
        if st.button("Clear Old Jobs (>30 days)", type="secondary"):
            cleared = st.session_state.db.clear_old_jobs(days=30)
            st.success(f"Cleared {cleared} old job records.")
        
        if st.button("Reset All Data", type="secondary"):
            if st.checkbox("I understand this will delete all data"):
                st.session_state.db.reset_database()
                st.success("Database reset successfully.")
                st.rerun()

if __name__ == "__main__":
    main()
