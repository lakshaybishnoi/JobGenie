import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

class PostgresDatabaseManager:
    """PostgreSQL database manager for JobGenie application."""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.engine = create_engine(self.database_url)
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize database tables."""
        with self.engine.connect() as conn:
            # Create jobs table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    company VARCHAR(255) NOT NULL,
                    location VARCHAR(255),
                    url TEXT,
                    summary TEXT,
                    requirements TEXT,
                    salary VARCHAR(255),
                    date_posted VARCHAR(100),
                    scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    applied BOOLEAN DEFAULT FALSE,
                    applied_date TIMESTAMP,
                    match_score REAL,
                    source VARCHAR(50) DEFAULT 'api',
                    UNIQUE(title, company, location)
                )
            '''))
            
            # Create search_history table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id SERIAL PRIMARY KEY,
                    keywords VARCHAR(255),
                    location VARCHAR(255),
                    results_count INTEGER,
                    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            
            # Create resume_data table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS resume_data (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255),
                    skills JSONB,
                    education JSONB,
                    experience JSONB,
                    contact_info JSONB,
                    full_text TEXT,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            
            # Create applications table for tracking job applications
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS applications (
                    id SERIAL PRIMARY KEY,
                    job_id INTEGER REFERENCES jobs(id),
                    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'applied',
                    notes TEXT
                )
            '''))
            
            # Create indexes for better performance
            conn.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_jobs_scraped_date ON jobs(scraped_date);
            '''))
            conn.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_jobs_applied ON jobs(applied);
            '''))
            conn.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_search_history_date ON search_history(search_date);
            '''))
            
            conn.commit()
    
    def insert_job(self, job_data: Dict[str, Any]) -> int:
        """Insert a new job record, avoiding duplicates."""
        with self.engine.connect() as conn:
            # Use ON CONFLICT to handle duplicates
            result = conn.execute(text('''
                INSERT INTO jobs 
                (title, company, location, url, summary, requirements, salary, date_posted, source)
                VALUES (:title, :company, :location, :url, :summary, :requirements, :salary, :date_posted, :source)
                ON CONFLICT (title, company, location) 
                DO UPDATE SET 
                    url = EXCLUDED.url,
                    summary = EXCLUDED.summary,
                    requirements = EXCLUDED.requirements,
                    salary = EXCLUDED.salary,
                    date_posted = EXCLUDED.date_posted,
                    scraped_date = CURRENT_TIMESTAMP
                RETURNING id
            '''), {
                'title': job_data.get('title', ''),
                'company': job_data.get('company', ''),
                'location': job_data.get('location', ''),
                'url': job_data.get('url', ''),
                'summary': job_data.get('summary', ''),
                'requirements': job_data.get('requirements', ''),
                'salary': job_data.get('salary', ''),
                'date_posted': job_data.get('date_posted', ''),
                'source': job_data.get('source', 'api')
            })
            
            row = result.fetchone()
            job_id = row[0] if row else None
            conn.commit()
            return job_id
    
    def get_recent_jobs(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get jobs scraped within the last N days."""
        with self.engine.connect() as conn:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            result = conn.execute(text('''
                SELECT * FROM jobs 
                WHERE scraped_date >= :cutoff_date 
                ORDER BY scraped_date DESC
            '''), {'cutoff_date': cutoff_date})
            
            return [dict(row._mapping) for row in result]
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID."""
        with self.engine.connect() as conn:
            result = conn.execute(text('''
                SELECT * FROM jobs WHERE id = :job_id
            '''), {'job_id': job_id})
            
            row = result.fetchone()
            return dict(row._mapping) if row else None
    
    def mark_job_applied(self, job_id: int, notes: str = "") -> None:
        """Mark a job as applied and create application record."""
        with self.engine.connect() as conn:
            # Update job record
            conn.execute(text('''
                UPDATE jobs 
                SET applied = TRUE, applied_date = CURRENT_TIMESTAMP 
                WHERE id = :job_id
            '''), {'job_id': job_id})
            
            # Create application record
            conn.execute(text('''
                INSERT INTO applications (job_id, notes)
                VALUES (:job_id, :notes)
                ON CONFLICT DO NOTHING
            '''), {'job_id': job_id, 'notes': notes})
            
            conn.commit()
    
    def get_applied_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs marked as applied."""
        with self.engine.connect() as conn:
            result = conn.execute(text('''
                SELECT j.*, a.application_date, a.notes 
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id
                WHERE j.applied = TRUE 
                ORDER BY j.applied_date DESC
            '''))
            
            return [dict(row._mapping) for row in result]
    
    def get_applied_jobs_count(self) -> int:
        """Get count of applied jobs."""
        with self.engine.connect() as conn:
            result = conn.execute(text('''
                SELECT COUNT(*) FROM jobs WHERE applied = TRUE
            '''))
            return result.fetchone()[0]
    
    def get_total_jobs(self) -> int:
        """Get total count of jobs in database."""
        with self.engine.connect() as conn:
            result = conn.execute(text('''
                SELECT COUNT(*) FROM jobs
            '''))
            return result.fetchone()[0]
    
    def save_search_history(self, keywords: str, location: str, results_count: int) -> None:
        """Save search history record."""
        with self.engine.connect() as conn:
            conn.execute(text('''
                INSERT INTO search_history (keywords, location, results_count)
                VALUES (:keywords, :location, :results_count)
            '''), {
                'keywords': keywords,
                'location': location,
                'results_count': results_count
            })
            conn.commit()
    
    def get_search_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent search history."""
        with self.engine.connect() as conn:
            result = conn.execute(text('''
                SELECT * FROM search_history 
                ORDER BY search_date DESC 
                LIMIT :limit
            '''), {'limit': limit})
            
            return [dict(row._mapping) for row in result]
    
    def save_resume_data(self, resume_data: Dict[str, Any]) -> int:
        """Save resume parsing results."""
        with self.engine.connect() as conn:
            result = conn.execute(text('''
                INSERT INTO resume_data (filename, skills, education, experience, contact_info, full_text)
                VALUES (:filename, :skills, :education, :experience, :contact_info, :full_text)
                RETURNING id
            '''), {
                'filename': resume_data.get('filename', ''),
                'skills': json.dumps(resume_data.get('skills', [])),
                'education': json.dumps(resume_data.get('education', [])),
                'experience': json.dumps(resume_data.get('experience', [])),
                'contact_info': json.dumps(resume_data.get('contact_info', {})),
                'full_text': resume_data.get('text', '')
            })
            
            resume_id = result.fetchone()[0]
            conn.commit()
            return resume_id
    
    def get_latest_resume(self) -> Optional[Dict[str, Any]]:
        """Get the most recently uploaded resume."""
        with self.engine.connect() as conn:
            result = conn.execute(text('''
                SELECT * FROM resume_data 
                ORDER BY upload_date DESC 
                LIMIT 1
            '''))
            
            row = result.fetchone()
            if row:
                resume_data = dict(row._mapping)
                # Parse JSON fields back to Python objects
                resume_data['skills'] = json.loads(resume_data['skills']) if resume_data['skills'] else []
                resume_data['education'] = json.loads(resume_data['education']) if resume_data['education'] else []
                resume_data['experience'] = json.loads(resume_data['experience']) if resume_data['experience'] else []
                resume_data['contact_info'] = json.loads(resume_data['contact_info']) if resume_data['contact_info'] else {}
                return resume_data
            
            return None
    
    def clear_old_jobs(self, days: int = 30) -> int:
        """Clear jobs older than N days that haven't been applied to."""
        with self.engine.connect() as conn:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            result = conn.execute(text('''
                DELETE FROM jobs 
                WHERE scraped_date < :cutoff_date AND applied = FALSE
            '''), {'cutoff_date': cutoff_date})
            
            deleted_count = result.rowcount
            conn.commit()
            return deleted_count
    
    def reset_database(self) -> None:
        """Reset all database tables."""
        with self.engine.connect() as conn:
            conn.execute(text('DELETE FROM applications'))
            conn.execute(text('DELETE FROM jobs'))
            conn.execute(text('DELETE FROM search_history'))
            conn.execute(text('DELETE FROM resume_data'))
            conn.commit()
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get comprehensive job statistics."""
        with self.engine.connect() as conn:
            # Total jobs
            total_result = conn.execute(text('SELECT COUNT(*) FROM jobs'))
            total_jobs = total_result.fetchone()[0]
            
            # Applied jobs
            applied_result = conn.execute(text('SELECT COUNT(*) FROM jobs WHERE applied = TRUE'))
            applied_jobs = applied_result.fetchone()[0]
            
            # Recent jobs (last 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)
            recent_result = conn.execute(text('''
                SELECT COUNT(*) FROM jobs WHERE scraped_date >= :cutoff_date
            '''), {'cutoff_date': cutoff_date})
            recent_jobs = recent_result.fetchone()[0]
            
            # Top companies
            companies_result = conn.execute(text('''
                SELECT company, COUNT(*) as job_count 
                FROM jobs 
                GROUP BY company 
                ORDER BY job_count DESC 
                LIMIT 10
            '''))
            top_companies = [dict(row._mapping) for row in companies_result]
            
            # Job sources
            sources_result = conn.execute(text('''
                SELECT source, COUNT(*) as job_count 
                FROM jobs 
                GROUP BY source 
                ORDER BY job_count DESC
            '''))
            job_sources = [dict(row._mapping) for row in sources_result]
            
            return {
                'total_jobs': total_jobs,
                'applied_jobs': applied_jobs,
                'recent_jobs': recent_jobs,
                'top_companies': top_companies,
                'job_sources': job_sources,
                'application_rate': round((applied_jobs / total_jobs * 100) if total_jobs > 0 else 0, 2)
            }