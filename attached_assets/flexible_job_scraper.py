import requests
import os
from typing import List, Dict, Any
import time

class FlexibleJobScraper:
    """Job scraper that tries multiple RapidAPI job search services."""
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY environment variable is required")
        
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
        
        # If no API service works, inform user
        print("No job search APIs are accessible with the current API key.")
        print("Please ensure your RapidAPI key has access to job search services.")
        return []
    
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
                
        elif service_type == 'linkedin':
            raw_jobs = data.get('jobs', [])
            for job in raw_jobs[:limit]:
                formatted_job = {
                    'title': job.get('title', 'Unknown Title'),
                    'company': job.get('company', {}).get('name', 'Unknown Company'),
                    'location': job.get('location', 'Location not specified'),
                    'url': job.get('url', ''),
                    'summary': self._truncate_text(job.get('description', ''), 500),
                    'requirements': job.get('description', ''),
                    'salary': 'Salary not specified',
                    'date_posted': job.get('posted_date', 'Date not specified'),
                    'source': 'linkedin_api'
                }
                jobs.append(formatted_job)
                
        elif service_type == 'indeed':
            raw_jobs = data.get('jobs', [])
            for job in raw_jobs[:limit]:
                formatted_job = {
                    'title': job.get('title', 'Unknown Title'),
                    'company': job.get('company', 'Unknown Company'),
                    'location': job.get('location', 'Location not specified'),
                    'url': job.get('url', ''),
                    'summary': self._truncate_text(job.get('summary', ''), 500),
                    'requirements': job.get('description', job.get('summary', '')),
                    'salary': job.get('salary', 'Salary not specified'),
                    'date_posted': job.get('date', 'Date not specified'),
                    'source': 'indeed_api'
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
        
        if min_salary and max_salary:
            return f"${min_salary:,} - ${max_salary:,}"
        elif min_salary:
            return f"${min_salary:,}+"
        
        return "Salary not specified"
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to specified length."""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."
    
    def test_connection(self) -> bool:
        """Test if any API service is accessible."""
        for service in self.api_services:
            try:
                headers = {
                    'X-RapidAPI-Key': self.api_key,
                    'X-RapidAPI-Host': service['host']
                }
                
                params = self._format_params(service['params_format'], 'test', '', 1)
                
                response = requests.get(
                    service['endpoint'],
                    headers=headers,
                    params=params,
                    timeout=10
                )
                
                if response.status_code in [200, 400]:  # 400 might be expected for test query
                    return True
                    
            except:
                continue
        
        return False