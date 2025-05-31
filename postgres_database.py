import os
import json
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

class PostgresDatabaseManager:
    """PostgreSQL database manager for JobGenie application."""
    
    def __init__(self):
        # Get database connection parameters from environment variables
        self.db_params = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5432'),
            'database': os.getenv('PGDATABASE', 'jobgenie'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', '')
        }
        
        # Alternative: use DATABASE_URL if provided
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            self.database_url = database_url
            self.use_url = True
        else:
            self.use_url = False
        
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            if self.use_url:
                conn = psycopg2.connect(self.database_url)
            else:
                conn = psycopg2.connect(**self.db_params)
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def init_database(self) -> None:
        """Initialize database tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create jobs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS jobs (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        company TEXT NOT NULL,
                        location TEXT,
                        url TEXT,
                        summary TEXT,
                        requirements TEXT,
                        salary TEXT,
                        date_posted TEXT,
                        scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        applied BOOLEAN DEFAULT FALSE,
                        applied_date TIMESTAMP,
                        match_score REAL,
                        source TEXT DEFAULT 'indeed',
                        UNIQUE(title, company, location)
                    )
                ''')
                
                # Create search_history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_history (
                        id SERIAL PRIMARY KEY,
                        keywords TEXT,
                        location TEXT,
                        results_count INTEGER,
                        search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create resume_data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resume_data (
                        id SERIAL PRIMARY KEY,
                        filename TEXT,
                        skills TEXT,  -- JSON string
                        education TEXT,  -- JSON string
                        experience TEXT,  -- JSON string
                        full_text TEXT,
                        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_jobs_scraped_date ON jobs(scraped_date);
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_jobs_applied ON jobs(applied);
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score);
                ''')
                
                conn.commit()
                
        except psycopg2.Error as e:
            print(f"Database initialization error: {e}")
            raise e
    
    def insert_job(self, job_data: Dict[str, Any]) -> int:
        """Insert a new job record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO jobs 
                    (title, company, location, url, summary, requirements, salary, date_posted, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (title, company, location) DO UPDATE SET
                        url = EXCLUDED.url,
                        summary = EXCLUDED.summary,
                        requirements = EXCLUDED.requirements,
                        salary = EXCLUDED.salary,
                        date_posted = EXCLUDED.date_posted,
                        scraped_date = CURRENT_TIMESTAMP
                    RETURNING id
                ''', (
                    job_data.get('title', ''),
                    job_data.get('company', ''),
                    job_data.get('location', ''),
                    job_data.get('url', ''),
                    job_data.get('summary', ''),
                    job_data.get('requirements', ''),
                    job_data.get('salary', ''),
                    job_data.get('date_posted', ''),
                    job_data.get('source', 'indeed')
                ))
                
                result = cursor.fetchone()
                job_id = result[0] if result else None
                conn.commit()
                return job_id
                
        except psycopg2.Error as e:
            print(f"Error inserting job: {e}")
            return None
    
    def get_recent_jobs(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get jobs scraped within the last N days."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor.execute('''
                    SELECT id, title, company, location, url, summary, requirements, 
                           salary, date_posted, scraped_date, applied, applied_date, 
                           match_score, source
                    FROM jobs 
                    WHERE scraped_date >= %s 
                    ORDER BY scraped_date DESC
                ''', (cutoff_date,))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except psycopg2.Error as e:
            print(f"Error getting recent jobs: {e}")
            return []
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, company, location, url, summary, requirements, 
                           salary, date_posted, scraped_date, applied, applied_date, 
                           match_score, source
                    FROM jobs WHERE id = %s
                ''', (job_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except psycopg2.Error as e:
            print(f"Error getting job by ID: {e}")
            return None
    
    def mark_job_applied(self, job_id: int) -> None:
        """Mark a job as applied."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE jobs 
                    SET applied = TRUE, applied_date = CURRENT_TIMESTAMP 
                    WHERE id = %s
                ''', (job_id,))
                
                conn.commit()
                
        except psycopg2.Error as e:
            print(f"Error marking job as applied: {e}")
    
    def get_applied_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs marked as applied."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, company, location, url, summary, requirements, 
                           salary, date_posted, scraped_date, applied, applied_date, 
                           match_score, source
                    FROM jobs 
                    WHERE applied = TRUE 
                    ORDER BY applied_date DESC
                ''')
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except psycopg2.Error as e:
            print(f"Error getting applied jobs: {e}")
            return []
    
    def get_applied_jobs_count(self) -> int:
        """Get count of applied jobs."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM jobs WHERE applied = TRUE')
                return cursor.fetchone()[0]
                
        except psycopg2.Error as e:
            print(f"Error getting applied jobs count: {e}")
            return 0
    
    def get_total_jobs(self) -> int:
        """Get total count of jobs in database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM jobs')
                return cursor.fetchone()[0]
                
        except psycopg2.Error as e:
            print(f"Error getting total jobs count: {e}")
            return 0
    
    def save_search_history(self, keywords: str, location: str, results_count: int) -> None:
        """Save search history record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO search_history (keywords, location, results_count)
                    VALUES (%s, %s, %s)
                ''', (keywords, location, results_count))
                
                conn.commit()
                
        except psycopg2.Error as e:
            print(f"Error saving search history: {e}")
    
    def save_resume_data(self, resume_data: Dict[str, Any]) -> int:
        """Save resume parsing results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO resume_data (filename, skills, education, experience, full_text)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    resume_data.get('filename', ''),
                    json.dumps(resume_data.get('skills', [])),
                    json.dumps(resume_data.get('education', [])),
                    json.dumps(resume_data.get('experience', [])),
                    resume_data.get('text', '')
                ))
                
                result = cursor.fetchone()
                resume_id = result[0] if result else None
                conn.commit()
                return resume_id
                
        except psycopg2.Error as e:
            print(f"Error saving resume data: {e}")
            return None
    
    def get_latest_resume_data(self) -> Optional[Dict[str, Any]]:
        """Get the most recently uploaded resume data."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, filename, skills, education, experience, full_text, upload_date
                    FROM resume_data 
                    ORDER BY upload_date DESC 
                    LIMIT 1
                ''')
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    resume_data = dict(zip(columns, row))
                    
                    # Parse JSON fields
                    resume_data['skills'] = json.loads(resume_data['skills']) if resume_data['skills'] else []
                    resume_data['education'] = json.loads(resume_data['education']) if resume_data['education'] else []
                    resume_data['experience'] = json.loads(resume_data['experience']) if resume_data['experience'] else []
                    
                    return resume_data
                return None
                
        except psycopg2.Error as e:
            print(f"Error getting latest resume data: {e}")
            return None
    
    def clear_old_jobs(self, days: int = 30) -> int:
        """Clear jobs older than N days."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor.execute('''
                    DELETE FROM jobs 
                    WHERE scraped_date < %s AND applied = FALSE
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
                
        except psycopg2.Error as e:
            print(f"Error clearing old jobs: {e}")
            return 0
    
    def update_job_match_score(self, job_id: int, match_score: float) -> None:
        """Update the match score for a specific job."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE jobs 
                    SET match_score = %s 
                    WHERE id = %s
                ''', (match_score, job_id))
                
                conn.commit()
                
        except psycopg2.Error as e:
            print(f"Error updating job match score: {e}")
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get comprehensive job statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get basic counts
                cursor.execute('SELECT COUNT(*) FROM jobs')
                total_jobs = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM jobs WHERE applied = TRUE')
                applied_jobs = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM jobs WHERE scraped_date >= %s', 
                             (datetime.now() - timedelta(days=7),))
                recent_jobs = cursor.fetchone()[0]
                
                # Get top companies
                cursor.execute('''
                    SELECT company, COUNT(*) as job_count 
                    FROM jobs 
                    GROUP BY company 
                    ORDER BY job_count DESC 
                    LIMIT 10
                ''')
                top_companies = [{'company': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                # Get top locations
                cursor.execute('''
                    SELECT location, COUNT(*) as job_count 
                    FROM jobs 
                    WHERE location IS NOT NULL AND location != ''
                    GROUP BY location 
                    ORDER BY job_count DESC 
                    LIMIT 10
                ''')
                top_locations = [{'location': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                return {
                    'total_jobs': total_jobs,
                    'applied_jobs': applied_jobs,
                    'recent_jobs': recent_jobs,
                    'application_rate': (applied_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                    'top_companies': top_companies,
                    'top_locations': top_locations
                }
                
        except psycopg2.Error as e:
            print(f"Error getting job statistics: {e}")
            return {
                'total_jobs': 0,
                'applied_jobs': 0,
                'recent_jobs': 0,
                'application_rate': 0,
                'top_companies': [],
                'top_locations': []
            }
    
    def reset_database(self) -> None:
        """Reset all database tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM jobs')
                cursor.execute('DELETE FROM search_history')
                cursor.execute('DELETE FROM resume_data')
                
                conn.commit()
                
        except psycopg2.Error as e:
            print(f"Error resetting database: {e}")
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                return True
        except psycopg2.Error:
            return False
