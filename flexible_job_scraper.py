import requests
import os
from typing import List, Dict, Any
import time

class FlexibleJobScraper:
    """Job scraper that tries multiple RapidAPI job search services."""
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        if not self.api_key:
            print("Warning: RAPIDAPI_KEY not found in environment variables")
            self.api_key = None
        
        # Multiple API endpoints to try
        self.api_services = [
            {
                'name': 'JSearch',
                'host': 'jsearch.p.rapidapi.com',
                'endpoint': 'https://jsearch.p.rapidapi.com/search',
                'params_format': 'jsearch'
            },
            {
                'name': 'LinkedIn Job Search',
                'host': 'linkedin-job-search.p.rapidapi.com',
                'endpoint': 'https://linkedin-job-search.p.rapidapi.com/jobs',
                'params_format': 'linkedin'
            },
            {
                'name': 'Indeed Job Search',
                'host': 'indeed-job-search-api.p.rapidapi.com',
                'endpoint': 'https://indeed-job-search-api.p.rapidapi.com/search',
                'params_format': 'indeed'
            }
        ]
        
        self.working_service = None
    
    def search_jobs(self, keywords: str, location: str = "", limit: int = 25) -> List[Dict[str, Any]]:
        """Search for jobs using available API services."""
        
        if not self.api_key:
            print("No API key available. Please provide a RAPIDAPI_KEY to search for real jobs.")
            return self._get_demo_jobs(keywords, location, limit)
        
        # If we already found a working service, use it
        if self.working_service:
            return self._search_with_service(self.working_service, keywords, location, limit)
        
        # Try each service until we find one that works
        for service in self.api_services:
            try:
                print(f"Trying {service['name']} API...")
                jobs = self._search_with_service(service, keywords, location, limit)
                
                if jobs:
                    self.working_service = service
                    print(f"Successfully connected to {service['name']}")
                    return jobs
                    
            except Exception as e:
                print(f"{service['name']} failed: {str(e)}")
                continue
        
        # If no API service works, return demo data
        print("No job search APIs are accessible with the current API key.")
        print("Returning demo data for testing purposes.")
        return self._get_demo_jobs(keywords, location, limit)
    
    def _search_with_service(self, service: Dict[str, Any], keywords: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Search using a specific API service."""
        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': service['host']
        }
        
        # Format parameters based on service type
        params = self._format_params(service['params_format'], keywords, location, limit)
        
        response = requests.get(
            service['endpoint'],
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return self._format_response(service['params_format'], data, limit)
        
        elif response.status_code == 403:
            raise Exception(f"Access forbidden - API key doesn't have access to {service['name']}")
        
        elif response.status_code == 429:
            raise Exception("Rate limit exceeded")
        
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text[:100]}")
    
    def _format_params(self, service_type: str, keywords: str, location: str, limit: int) -> Dict[str, Any]:
        """Format parameters for different API services."""
        
        if service_type == 'jsearch':
            params = {
                'query': f"{keywords} {location}".strip(),
                'page': '1',
                'num_pages': '1'
            }
            if location:
                params['location'] = location
                
        elif service_type == 'linkedin':
            params = {
                'keywords': keywords,
                'locationId': location if location else '',
                'start': '0'
            }
            
        elif service_type == 'indeed':
            params = {
                'query': keywords,
                'location': location,
                'page': '1'
            }
            
        else:
            # Generic format
            params = {
                'q': keywords,
                'location': location,
                'limit': str(limit)
            }
        
        return params
    
    def _format_response(self, service_type: str, data: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Format response data from different API services."""
        
        jobs = []
        
        if service_type == 'jsearch':
            raw_jobs = data.get('data', [])
            for job in raw_jobs[:limit]:
                formatted_job = {
                    'title': job.get('job_title', 'Unknown Title'),
                    'company': job.get('employer_name', 'Unknown Company'),
                    'location': self._format_jsearch_location(job),
                    'url': job.get('job_apply_link', job.get('job_url', '')),
                    'summary': self._truncate_text(job.get('job_description', ''), 500),
                    'requirements': job.get('job_description', ''),
                    'salary': self._format_jsearch_salary(job),
                    'date_posted': job.get('job_posted_at_datetime_utc', 'Date not specified'),
                    'source': 'jsearch_api'
                }
                jobs.append(formatted_job)
        
        return jobs
    
    def _format_jsearch_location(self, job: Dict[str, Any]) -> str:
        """Format location for JSearch API response."""
        city = job.get('job_city', '')
        state = job.get('job_state', '')
        country = job.get('job_country', '')
        
        location_parts = []
        if city:
            location_parts.append(city)
        if state:
            location_parts.append(state)
        if country and country.upper() != 'US':
            location_parts.append(country)
            
        location = ', '.join(location_parts) if location_parts else 'Location not specified'
        
        if job.get('job_is_remote', False):
            location = f"Remote ({location})" if location != 'Location not specified' else 'Remote'
            
        return location
    
    def _format_jsearch_salary(self, job: Dict[str, Any]) -> str:
        """Format salary for JSearch API response."""
        min_salary = job.get('job_min_salary')
        max_salary = job.get('job_max_salary')
        currency = job.get('job_salary_currency', 'USD')
        period = job.get('job_salary_period', 'YEAR')
        
        if min_salary and max_salary:
            symbol = '$' if currency == 'USD' else currency
            period_text = 'per year' if period == 'YEAR' else f'per {period.lower()}'
            return f"{symbol}{min_salary:,} - {symbol}{max_salary:,} {period_text}"
        elif min_salary:
            symbol = '$' if currency == 'USD' else currency
            period_text = 'per year' if period == 'YEAR' else f'per {period.lower()}'
            return f"{symbol}{min_salary:,}+ {period_text}"
        
        return "Salary not specified"
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to specified length."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _get_demo_jobs(self, keywords: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Generate sample job data when API is not available."""
        demo_jobs = [
            {
                'title': 'Senior Python Developer',
                'company': 'TechCorp Inc',
                'location': 'Remote',
                'url': 'https://example.com/job1',
                'summary': 'We are looking for a Senior Python Developer to join our growing team. You will be responsible for developing scalable web applications using Django and Flask frameworks.',
                'requirements': 'Requirements: 5+ years Python experience, Django/Flask knowledge, AWS experience, SQL databases, Git, Agile methodologies. Bachelor\'s degree in Computer Science preferred.',
                'salary': '$120,000 - $150,000 per year',
                'date_posted': '2 days ago',
                'source': 'demo_data'
            },
            {
                'title': 'Full Stack JavaScript Developer',
                'company': 'StartupXYZ',
                'location': 'San Francisco, CA',
                'url': 'https://example.com/job2',
                'summary': 'Join our dynamic team building cutting-edge web applications. Work with React, Node.js, and modern cloud technologies.',
                'requirements': 'Skills needed: JavaScript, React, Node.js, MongoDB, RESTful APIs, Git, 3+ years experience. Experience with AWS and Docker a plus.',
                'salary': '$100,000 - $130,000 per year',
                'date_posted': '1 day ago',
                'source': 'demo_data'
            },
            {
                'title': 'Data Scientist',
                'company': 'Analytics Pro',
                'location': 'New York, NY',
                'url': 'https://example.com/job3',
                'summary': 'Seeking a Data Scientist to analyze large datasets and build machine learning models to drive business insights.',
                'requirements': 'Required: Python, pandas, scikit-learn, SQL, statistics, 2+ years experience. PhD in Data Science, Statistics, or related field preferred.',
                'salary': '$110,000 - $140,000 per year',
                'date_posted': '3 days ago',
                'source': 'demo_data'
            }
        ]
        
        # Filter by keywords if provided
        if keywords:
            keyword_list = keywords.lower().split()
            filtered_jobs = []
            for job in demo_jobs:
                job_text = (job['title'] + ' ' + job['summary'] + ' ' + job['requirements']).lower()
                if any(keyword in job_text for keyword in keyword_list):
                    filtered_jobs.append(job)
            if filtered_jobs:
                demo_jobs = filtered_jobs
        
        return demo_jobs[:limit]
    
    def test_connection(self) -> bool:
        """Test if any API service is accessible."""
        if not self.api_key:
            return False
        
        for service in self.api_services:
            try:
                headers = {
                    'X-RapidAPI-Key': self.api_key,
                    'X-RapidAPI-Host': service['host']
                }
                
                # Simple test request
                response = requests.get(
                    service['endpoint'],
                    headers=headers,
                    params={'query': 'test', 'page': '1'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    return True
                    
            except Exception:
                continue
        
        return False