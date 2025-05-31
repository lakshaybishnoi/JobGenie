import requests
import os
from typing import List, Dict, Any
import time

class APIJobScraper:
    """Job scraper using RapidAPI services for authentic job data."""
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY environment variable is required")
        
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
        }
        
        self.base_url = "https://jsearch.p.rapidapi.com"
    
    def search_jobs(self, keywords: str, location: str = "", limit: int = 25) -> List[Dict[str, Any]]:
        """Search for jobs using JSearch API."""
        try:
            # Build query parameters
            params = {
                'query': f"{keywords} {location}".strip(),
                'page': '1',
                'num_pages': '1',
                'date_posted': 'all'
            }
            
            # If location is specified, add it as a separate parameter
            if location:
                params['location'] = location
                
            # Make API request
            response = requests.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                
                # Convert API response to our format
                formatted_jobs = []
                for job in jobs[:limit]:
                    formatted_job = self._format_job_data(job)
                    if formatted_job:
                        formatted_jobs.append(formatted_job)
                
                return formatted_jobs
            
            elif response.status_code == 429:
                print("API rate limit exceeded. Please wait before making more requests.")
                return []
            
            else:
                print(f"API request failed with status {response.status_code}: {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Network error during API request: {e}")
            return []
        except Exception as e:
            print(f"Error during job search: {e}")
            return []
    
    def _format_job_data(self, api_job: Dict[str, Any]) -> Dict[str, Any]:
        """Convert API job data to our internal format."""
        try:
            # Extract job details from API response
            job_data = {
                'title': api_job.get('job_title', 'Unknown Title'),
                'company': api_job.get('employer_name', 'Unknown Company'),
                'location': self._format_location(api_job),
                'url': api_job.get('job_apply_link', api_job.get('job_url', '')),
                'summary': api_job.get('job_description', '')[:500] + '...' if len(api_job.get('job_description', '')) > 500 else api_job.get('job_description', ''),
                'requirements': api_job.get('job_description', ''),
                'salary': self._format_salary(api_job),
                'date_posted': self._format_date_posted(api_job),
                'source': 'jsearch_api'
            }
            
            return job_data
            
        except Exception as e:
            print(f"Error formatting job data: {e}")
            return {
                'title': 'Error Processing Job',
                'company': 'Unknown',
                'location': 'Unknown',
                'url': '',
                'summary': 'Error occurred while processing this job listing',
                'requirements': '',
                'salary': '',
                'date_posted': '',
                'source': 'jsearch_api'
            }
    
    def _format_location(self, api_job: Dict[str, Any]) -> str:
        """Format location from API data."""
        city = api_job.get('job_city', '')
        state = api_job.get('job_state', '')
        country = api_job.get('job_country', '')
        
        location_parts = []
        if city:
            location_parts.append(city)
        if state:
            location_parts.append(state)
        if country and country.upper() != 'US':
            location_parts.append(country)
            
        location = ', '.join(location_parts) if location_parts else 'Location not specified'
        
        # Check if it's remote
        if api_job.get('job_is_remote', False):
            location = f"Remote ({location})" if location != 'Location not specified' else 'Remote'
            
        return location
    
    def _format_salary(self, api_job: Dict[str, Any]) -> str:
        """Format salary information from API data."""
        min_salary = api_job.get('job_min_salary')
        max_salary = api_job.get('job_max_salary')
        salary_currency = api_job.get('job_salary_currency', 'USD')
        salary_period = api_job.get('job_salary_period', 'YEAR')
        
        if min_salary and max_salary:
            currency_symbol = '$' if salary_currency == 'USD' else salary_currency
            period_text = 'per year' if salary_period == 'YEAR' else f'per {salary_period.lower()}'
            
            # Format numbers with commas
            min_formatted = f"{min_salary:,}"
            max_formatted = f"{max_salary:,}"
            
            return f"{currency_symbol}{min_formatted} - {currency_symbol}{max_formatted} {period_text}"
        
        elif min_salary:
            currency_symbol = '$' if salary_currency == 'USD' else salary_currency
            period_text = 'per year' if salary_period == 'YEAR' else f'per {salary_period.lower()}'
            return f"{currency_symbol}{min_salary:,}+ {period_text}"
        
        return "Salary not specified"
    
    def _format_date_posted(self, api_job: Dict[str, Any]) -> str:
        """Format date posted from API data."""
        date_posted = api_job.get('job_posted_at_datetime_utc', '')
        
        if date_posted:
            try:
                from datetime import datetime
                # Parse the date and calculate days ago
                posted_date = datetime.fromisoformat(date_posted.replace('Z', '+00:00'))
                now = datetime.now(posted_date.tzinfo)
                days_ago = (now - posted_date).days
                
                if days_ago == 0:
                    return "Today"
                elif days_ago == 1:
                    return "1 day ago"
                else:
                    return f"{days_ago} days ago"
            except:
                return date_posted
        
        return "Date not specified"
    
    def test_connection(self) -> bool:
        """Test if the API connection is working."""
        try:
            # Make a simple test request
            response = requests.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params={'query': 'test', 'page': '1'},
                timeout=10
            )
            
            return response.status_code in [200, 400]  # 400 might be expected for test query
        except:
            return False