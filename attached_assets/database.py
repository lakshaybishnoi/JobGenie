import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """Database manager for JobGenie application using SQLite."""
    
    def __init__(self, db_path: str = "jobgenie.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    source TEXT DEFAULT 'indeed'
                )
            ''')
            
            # Create search_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keywords TEXT,
                    location TEXT,
                    results_count INTEGER,
                    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create resume_data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resume_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    skills TEXT,  -- JSON string
                    education TEXT,  -- JSON string
                    experience TEXT,  -- JSON string
                    full_text TEXT,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def insert_job(self, job_data: Dict[str, Any]) -> int:
        """Insert a new job record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO jobs 
                (title, company, location, url, summary, requirements, salary, date_posted, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            
            conn.commit()
            return cursor.lastrowid
    
    def get_recent_jobs(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get jobs scraped within the last N days."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE scraped_date >= ? 
                ORDER BY scraped_date DESC
            ''', (cutoff_date,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
            row = cursor.fetchone()
            
            return dict(row) if row else None
    
    def mark_job_applied(self, job_id: int) -> None:
        """Mark a job as applied."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE jobs 
                SET applied = TRUE, applied_date = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (job_id,))
            
            conn.commit()
    
    def get_applied_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs marked as applied."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE applied = TRUE 
                ORDER BY applied_date DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_applied_jobs_count(self) -> int:
        """Get count of applied jobs."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM jobs WHERE applied = TRUE')
            return cursor.fetchone()[0]
    
    def get_total_jobs(self) -> int:
        """Get total count of jobs in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM jobs')
            return cursor.fetchone()[0]
    
    def save_search_history(self, keywords: str, location: str, results_count: int) -> None:
        """Save search history record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO search_history (keywords, location, results_count)
                VALUES (?, ?, ?)
            ''', (keywords, location, results_count))
            
            conn.commit()
    
    def save_resume_data(self, resume_data: Dict[str, Any]) -> int:
        """Save resume parsing results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO resume_data (filename, skills, education, experience, full_text)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                resume_data.get('filename', ''),
                json.dumps(resume_data.get('skills', [])),
                json.dumps(resume_data.get('education', [])),
                json.dumps(resume_data.get('experience', [])),
                resume_data.get('text', '')
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def clear_old_jobs(self, days: int = 30) -> int:
        """Clear jobs older than N days."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                DELETE FROM jobs 
                WHERE scraped_date < ? AND applied = FALSE
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
    
    def reset_database(self) -> None:
        """Reset all database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM jobs')
            cursor.execute('DELETE FROM search_history')
            cursor.execute('DELETE FROM resume_data')
            
            conn.commit()
