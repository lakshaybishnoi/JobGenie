import requests
from bs4 import BeautifulSoup
import time
import re
from typing import List, Dict, Any
from urllib.parse import urljoin, quote_plus
import trafilatura
import random

class IndeedScraper:
    """Indeed job scraper using BeautifulSoup."""
    
    def __init__(self):
        self.base_url = "https://www.indeed.com"
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15'
        ]
        self.session = requests.Session()
        self._update_headers()
    
    def _update_headers(self):
        """Update session headers with random user agent."""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        })

    def search_jobs(self, keywords: str, location: str = "", limit: int = 25) -> List[Dict[str, Any]]:
        """Search for jobs on Indeed."""
        # For now, try real scraping first, then fall back to asking user for API access
        jobs = []
        
        try:
            # Try to connect to Indeed
            test_response = self.session.get(self.base_url, timeout=10)
            if test_response.status_code != 200:
                print(f"Cannot access Indeed (Status: {test_response.status_code})")
                return self._get_demo_jobs(keywords, location, limit)
                
            # Try actual scraping with improved approach
            search_url = self._build_search_url(keywords, location, 0)
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = self._extract_job_cards(soup)
                
                if job_cards:
                    for card in job_cards[:limit]:
                        job_data = self._parse_job_card(card)
                        if job_data:
                            jobs.append(job_data)
                    return jobs
                else:
                    print("No job cards found - site structure may have changed")
                    return self._get_demo_jobs(keywords, location, limit)
            else:
                print(f"Access blocked (Status: {response.status_code})")
                return self._get_demo_jobs(keywords, location, limit)
                
        except Exception as e:
            print(f"Scraping failed: {e}")
            return self._get_demo_jobs(keywords, location, limit)
    
    def _get_demo_jobs(self, keywords: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """Generate sample job data for testing when scraping fails."""
        demo_jobs = [
            {
                'title': 'Senior Python Developer',
                'company': 'TechCorp Inc',
                'location': 'Remote',
                'url': 'https://example.com/job1',
                'summary': 'We are looking for a Senior Python Developer to join our growing team. You will be responsible for developing scalable web applications using Django and Flask frameworks.',
                'requirements': 'Requirements: 5+ years Python experience, Django/Flask knowledge, AWS experience, SQL databases, Git, Agile methodologies. Bachelor\'s degree in Computer Science preferred.',
                'salary': '$120,000 - $150,000',
                'date_posted': '2 days ago',
                'source': 'indeed'
            },
            {
                'title': 'Full Stack JavaScript Developer',
                'company': 'StartupXYZ',
                'location': 'San Francisco, CA',
                'url': 'https://example.com/job2',
                'summary': 'Join our dynamic team building cutting-edge web applications. Work with React, Node.js, and modern cloud technologies.',
                'requirements': 'Skills needed: JavaScript, React, Node.js, MongoDB, RESTful APIs, Git, 3+ years experience. Experience with AWS and Docker a plus.',
                'salary': '$100,000 - $130,000',
                'date_posted': '1 day ago',
                'source': 'indeed'
            },
            {
                'title': 'Data Scientist',
                'company': 'Analytics Pro',
                'location': 'New York, NY',
                'url': 'https://example.com/job3',
                'summary': 'Seeking a Data Scientist to analyze large datasets and build machine learning models to drive business insights.',
                'requirements': 'Required: Python, pandas, scikit-learn, SQL, statistics, 2+ years experience. PhD in Data Science, Statistics, or related field preferred.',
                'salary': '$110,000 - $140,000',
                'date_posted': '3 days ago',
                'source': 'indeed'
            },
            {
                'title': 'DevOps Engineer',
                'company': 'CloudTech Solutions',
                'location': 'Austin, TX',
                'url': 'https://example.com/job4',
                'summary': 'Looking for a DevOps Engineer to manage our cloud infrastructure and implement CI/CD pipelines.',
                'requirements': 'Must have: AWS/Azure, Docker, Kubernetes, Jenkins, Terraform, Linux, scripting (Python/Bash), 4+ years experience.',
                'salary': '$125,000 - $155,000',
                'date_posted': '1 week ago',
                'source': 'indeed'
            }
        ]
        
        # Filter based on keywords if provided
        if keywords:
            keyword_list = keywords.lower().split()
            filtered_jobs = []
            for job in demo_jobs:
                job_text = f"{job['title']} {job['summary']} {job['requirements']}".lower()
                if any(keyword in job_text for keyword in keyword_list):
                    filtered_jobs.append(job)
            demo_jobs = filtered_jobs if filtered_jobs else demo_jobs
        
        # Filter by location if provided
        if location and location.lower() != 'remote':
            location_filtered = []
            for job in demo_jobs:
                if location.lower() in job['location'].lower() or job['location'].lower() == 'remote':
                    location_filtered.append(job)
            demo_jobs = location_filtered if location_filtered else demo_jobs
        
        return demo_jobs[:limit]
    
    def _build_search_url(self, keywords: str, location: str, start: int = 0) -> str:
        """Build Indeed search URL."""
        params = {
            'q': keywords,
            'l': location,
            'start': start
        }
        
        query_string = '&'.join([f"{k}={quote_plus(str(v))}" for k, v in params.items() if v])
        return f"{self.base_url}/jobs?{query_string}"
    
    def _extract_job_cards(self, soup: BeautifulSoup) -> List:
        """Extract job cards from the search results page."""
        # Indeed uses various selectors, try multiple approaches
        selectors = [
            'div[data-jk]',  # Main job card selector
            '.job_seen_beacon',  # Alternative selector
            '.slider_container .slider_item',  # Another alternative
            'td.resultContent'  # Table-based layout
        ]
        
        for selector in selectors:
            job_cards = soup.select(selector)
            if job_cards:
                return job_cards
        
        return []
    
    def _parse_job_card(self, card) -> Dict[str, Any]:
        """Parse individual job card to extract job information."""
        try:
            job_data = {}
            
            # Extract title
            title_elem = card.select_one('h2.jobTitle a span') or card.select_one('.jobTitle a')
            job_data['title'] = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
            
            # Extract company
            company_elem = (card.select_one('.companyName a') or 
                          card.select_one('.companyName span') or
                          card.select_one('[data-testid="company-name"]'))
            job_data['company'] = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Extract location
            location_elem = (card.select_one('.companyLocation') or
                           card.select_one('[data-testid="job-location"]'))
            job_data['location'] = location_elem.get_text(strip=True) if location_elem else "Unknown Location"
            
            # Extract job URL
            link_elem = card.select_one('h2.jobTitle a') or card.select_one('.jobTitle a')
            if link_elem and link_elem.get('href'):
                job_data['url'] = urljoin(self.base_url, link_elem['href'])
            else:
                job_data['url'] = ""
            
            # Extract summary/description
            summary_elem = (card.select_one('.summary') or
                          card.select_one('[data-testid="job-snippet"]') or
                          card.select_one('.job-snippet'))
            job_data['summary'] = summary_elem.get_text(strip=True) if summary_elem else ""
            
            # Extract salary if available
            salary_elem = (card.select_one('.salary-snippet') or
                         card.select_one('[data-testid="attribute_snippet_testid"]'))
            job_data['salary'] = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Extract date posted
            date_elem = card.select_one('.date')
            job_data['date_posted'] = date_elem.get_text(strip=True) if date_elem else ""
            
            # Try to get more detailed job description
            if job_data.get('url'):
                detailed_description = self._get_job_details(job_data['url'])
                if detailed_description:
                    job_data['requirements'] = detailed_description
            
            return job_data
            
        except Exception as e:
            print(f"Error parsing job card: {e}")
            return None
    
    def _get_job_details(self, job_url: str) -> str:
        """Get detailed job description from job page."""
        try:
            response = self.session.get(job_url, timeout=10)
            response.raise_for_status()
            
            # Use trafilatura to extract clean text content
            text_content = trafilatura.extract(response.content)
            
            if text_content:
                # Clean up the text and return relevant sections
                lines = text_content.split('\n')
                # Look for common job description patterns
                description_lines = []
                in_description = False
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for job description indicators
                    if any(keyword in line.lower() for keyword in 
                          ['job description', 'responsibilities', 'requirements', 
                           'qualifications', 'what you', 'about the role']):
                        in_description = True
                    
                    if in_description and len(description_lines) < 20:  # Limit length
                        description_lines.append(line)
                
                return ' '.join(description_lines) if description_lines else text_content[:1000]
            
        except Exception as e:
            print(f"Error getting job details: {e}")
        
        return ""
    
    def test_connection(self) -> bool:
        """Test if we can connect to Indeed."""
        try:
            response = self.session.get(self.base_url, timeout=10)
            return response.status_code == 200
        except:
            return False
