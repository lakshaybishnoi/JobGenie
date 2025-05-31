import csv
import io
from typing import List, Dict, Any
from datetime import datetime

def export_to_csv(jobs: List[Dict[str, Any]]) -> str:
    """Export job data to CSV format."""
    if not jobs:
        return ""
    
    output = io.StringIO()
    
    # Define CSV columns
    fieldnames = [
        'id', 'title', 'company', 'location', 'url', 'summary', 
        'requirements', 'salary', 'date_posted', 'scraped_date', 
        'applied', 'applied_date', 'match_score', 'source'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for job in jobs:
        # Ensure all fields are present
        row = {field: job.get(field, '') for field in fieldnames}
        writer.writerow(row)
    
    csv_content = output.getvalue()
    output.close()
    
    return csv_content

def clean_text(text: str) -> str:
    """Clean and normalize text data."""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    import re
    text = re.sub(r'[^\w\s\.\,\!\?\-\(\)]', ' ', text)
    
    return text.strip()

def format_salary(salary_text: str) -> str:
    """Format salary text for consistent display."""
    if not salary_text:
        return "Not specified"
    
    # Common salary formatting
    import re
    
    # Look for salary ranges
    salary_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:to|-|–)\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
    match = re.search(salary_pattern, salary_text)
    
    if match:
        return f"${match.group(1)} - ${match.group(2)}"
    
    # Look for single salary value
    single_salary = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
    match = re.search(single_salary, salary_text)
    
    if match:
        return f"${match.group(1)}"
    
    return salary_text

def calculate_days_ago(date_posted: str) -> int:
    """Calculate how many days ago a job was posted."""
    if not date_posted:
        return 0
    
    # Common Indeed date formats
    import re
    
    # "X days ago" format
    days_match = re.search(r'(\d+)\s*days?\s*ago', date_posted.lower())
    if days_match:
        return int(days_match.group(1))
    
    # "Today" or "yesterday"
    if 'today' in date_posted.lower():
        return 0
    if 'yesterday' in date_posted.lower():
        return 1
    
    # "X hours ago"
    hours_match = re.search(r'(\d+)\s*hours?\s*ago', date_posted.lower())
    if hours_match:
        return 0  # Same day
    
    return 0

def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted."""
    if not url:
        return False
    
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to specified length with ellipsis."""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def extract_domain(url: str) -> str:
    """Extract domain name from URL."""
    if not url:
        return ""
    
    import re
    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if domain_match:
        return domain_match.group(1)
    
    return ""

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage."""
    if not filename:
        return "untitled"
    
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove extra spaces and periods
    filename = re.sub(r'\.+', '.', filename)
    filename = re.sub(r'\s+', '_', filename)
    
    # Limit length
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:90] + ('.' + ext if ext else '')
    
    return filename

def format_job_title(title: str) -> str:
    """Format job title for consistent display."""
    if not title:
        return "Unknown Position"
    
    # Capitalize properly
    words = title.split()
    formatted_words = []
    
    for word in words:
        if word.upper() in ['IT', 'AI', 'ML', 'UI', 'UX', 'API', 'SQL', 'AWS', 'GCP']:
            formatted_words.append(word.upper())
        elif word.lower() in ['and', 'or', 'of', 'in', 'at', 'for', 'with']:
            formatted_words.append(word.lower())
        else:
            formatted_words.append(word.capitalize())
    
    return ' '.join(formatted_words)

def get_experience_level_from_title(title: str) -> str:
    """Determine experience level from job title."""
    if not title:
        return "unknown"
    
    title_lower = title.lower()
    
    if any(word in title_lower for word in ['senior', 'sr', 'lead', 'principal', 'architect', 'director']):
        return "senior"
    elif any(word in title_lower for word in ['junior', 'jr', 'entry', 'associate', 'trainee', 'intern']):
        return "entry"
    else:
        return "mid"

def score_to_color(score: float) -> str:
    """Convert match score to color for UI display."""
    if score >= 80:
        return "green"
    elif score >= 60:
        return "orange"
    else:
        return "red"

def generate_search_summary(keywords: str, location: str, num_results: int) -> str:
    """Generate a summary of search parameters."""
    summary_parts = []
    
    if keywords:
        summary_parts.append(f"Keywords: {keywords}")
    
    if location:
        summary_parts.append(f"Location: {location}")
    
    summary_parts.append(f"Results: {num_results}")
    
    return " | ".join(summary_parts)
