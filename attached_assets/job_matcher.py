import re
import spacy
from typing import Dict, List, Any
from collections import Counter
import math

class JobMatcher:
    """Job matching engine using NLP to score job-resume compatibility."""
    
    def __init__(self):
        # Try to load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp = None
            print("Warning: spaCy English model not found. Using basic text matching.")
        
        # Weight factors for different matching criteria
        self.weights = {
            'skills': 0.4,          # 40% weight for skills match
            'experience': 0.3,       # 30% weight for experience keywords
            'education': 0.2,        # 20% weight for education match
            'text_similarity': 0.1   # 10% weight for overall text similarity
        }
    
    def calculate_match_score(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calculate overall match score between resume and job."""
        scores = {}
        
        # Calculate individual scores
        scores['skills'] = self._calculate_skills_match(resume_data, job_data)
        scores['experience'] = self._calculate_experience_match(resume_data, job_data)
        scores['education'] = self._calculate_education_match(resume_data, job_data)
        scores['text_similarity'] = self._calculate_text_similarity(resume_data, job_data)
        
        # Calculate weighted average
        total_score = sum(scores[key] * self.weights[key] for key in scores)
        
        return min(100, max(0, total_score))  # Ensure score is between 0-100
    
    def _calculate_skills_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calculate skills matching score."""
        resume_skills = [skill.lower() for skill in resume_data.get('skills', [])]
        
        if not resume_skills:
            return 0
        
        # Extract skills from job description
        job_text = self._get_job_full_text(job_data).lower()
        job_skills = self._extract_skills_from_text(job_text)
        
        if not job_skills:
            return 50  # Neutral score if no skills found in job
        
        # Calculate overlap
        matching_skills = set(resume_skills) & set(job_skills)
        total_job_skills = len(set(job_skills))
        
        if total_job_skills == 0:
            return 50
        
        # Score based on how many job skills are covered
        coverage_score = (len(matching_skills) / total_job_skills) * 100
        
        # Bonus for having more skills than required
        bonus = min(20, (len(resume_skills) - len(matching_skills)) * 2)
        
        return min(100, coverage_score + bonus)
    
    def _calculate_experience_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calculate experience matching score."""
        resume_text = resume_data.get('text', '').lower()
        job_text = self._get_job_full_text(job_data).lower()
        
        # Extract experience keywords
        experience_keywords = self._extract_experience_keywords(job_text)
        
        if not experience_keywords:
            return 70  # Neutral score if no experience keywords found
        
        # Count matches in resume
        matches = 0
        for keyword in experience_keywords:
            if keyword in resume_text:
                matches += 1
        
        # Calculate match percentage
        match_percentage = (matches / len(experience_keywords)) * 100
        
        # Extract years of experience if mentioned
        job_years = self._extract_years_experience(job_text)
        resume_years = self._extract_years_experience(resume_text)
        
        years_score = 70  # Default neutral score
        if job_years and resume_years:
            if resume_years >= job_years:
                years_score = 100
            elif resume_years >= job_years * 0.75:  # Within 25% of required
                years_score = 80
            else:
                years_score = 50
        
        return (match_percentage * 0.7) + (years_score * 0.3)
    
    def _calculate_education_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calculate education matching score."""
        resume_education = [edu.lower() for edu in resume_data.get('education', [])]
        job_text = self._get_job_full_text(job_data).lower()
        
        # Common education requirements
        education_patterns = [
            r'\b(?:bachelor|degree|b\.s\.|b\.a\.|bs|ba)\b',
            r'\b(?:master|m\.s\.|m\.a\.|mba|ms|ma)\b',
            r'\b(?:phd|doctorate|ph\.d\.)\b',
            r'\b(?:computer science|engineering|mathematics|physics)\b'
        ]
        
        job_education_requirements = []
        for pattern in education_patterns:
            if re.search(pattern, job_text):
                job_education_requirements.append(pattern)
        
        if not job_education_requirements:
            return 80  # Neutral score if no education requirements found
        
        if not resume_education:
            return 30  # Low score if no education info in resume
        
        # Check for matches
        matches = 0
        resume_edu_text = ' '.join(resume_education)
        
        for pattern in job_education_requirements:
            if re.search(pattern, resume_edu_text):
                matches += 1
        
        return (matches / len(job_education_requirements)) * 100
    
    def _calculate_text_similarity(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calculate overall text similarity using keyword overlap."""
        resume_text = resume_data.get('text', '').lower()
        job_text = self._get_job_full_text(job_data).lower()
        
        if not resume_text or not job_text:
            return 50
        
        # Extract keywords using spaCy if available
        if self.nlp:
            resume_keywords = self._extract_keywords_spacy(resume_text)
            job_keywords = self._extract_keywords_spacy(job_text)
        else:
            resume_keywords = self._extract_keywords_basic(resume_text)
            job_keywords = self._extract_keywords_basic(job_text)
        
        if not resume_keywords or not job_keywords:
            return 50
        
        # Calculate cosine similarity
        return self._cosine_similarity(resume_keywords, job_keywords) * 100
    
    def _get_job_full_text(self, job_data: Dict[str, Any]) -> str:
        """Get full text from job data."""
        text_parts = [
            job_data.get('title', ''),
            job_data.get('summary', ''),
            job_data.get('requirements', ''),
            job_data.get('company', '')
        ]
        return ' '.join([part for part in text_parts if part])
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract technical skills from job text."""
        # Common technical skills patterns
        skill_patterns = [
            r'\b(?:python|java|javascript|c\+\+|c#|php|ruby|go|rust|swift|kotlin|typescript)\b',
            r'\b(?:react|angular|vue|django|flask|spring|laravel|express|node\.js|jquery)\b',
            r'\b(?:sql|mysql|postgresql|mongodb|redis|oracle|sqlserver|sqlite)\b',
            r'\b(?:aws|azure|gcp|docker|kubernetes|jenkins|git|ci/cd|devops)\b',
            r'\b(?:pandas|numpy|scikit-learn|tensorflow|pytorch|jupyter|tableau|power bi)\b',
            r'\b(?:html|css|rest|api|graphql|microservices|agile|scrum|linux|windows)\b'
        ]
        
        skills = []
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skills.append(match.group().lower())
        
        return list(set(skills))
    
    def _extract_experience_keywords(self, text: str) -> List[str]:
        """Extract experience-related keywords from job text."""
        keywords = []
        
        # Common experience keywords
        exp_patterns = [
            r'\b(?:experience|worked|developed|managed|led|built|created|designed|implemented)\b',
            r'\b(?:team|project|product|system|application|software|solution)\b',
            r'\b(?:leadership|management|collaboration|communication)\b'
        ]
        
        for pattern in exp_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                keywords.append(match.group().lower())
        
        return list(set(keywords))
    
    def _extract_years_experience(self, text: str) -> int:
        """Extract years of experience from text."""
        # Look for patterns like "3+ years", "5-7 years", "minimum 2 years"
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'(?:minimum|min|at least)\s*(\d+)\s*(?:years?|yrs?)',
            r'(\d+)\s*(?:to|-)\s*\d+\s*(?:years?|yrs?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _extract_keywords_spacy(self, text: str) -> List[str]:
        """Extract keywords using spaCy."""
        doc = self.nlp(text)
        keywords = []
        
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                len(token.text) > 2 and 
                token.is_alpha and 
                not token.is_stop):
                keywords.append(token.lemma_.lower())
        
        return keywords
    
    def _extract_keywords_basic(self, text: str) -> List[str]:
        """Extract keywords using basic text processing."""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        # Simple tokenization
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [word for word in words if word not in stop_words]
        
        return keywords
    
    def _cosine_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """Calculate cosine similarity between two keyword lists."""
        # Create frequency vectors
        counter1 = Counter(keywords1)
        counter2 = Counter(keywords2)
        
        # Get all unique terms
        all_terms = set(counter1.keys()) | set(counter2.keys())
        
        # Create vectors
        vec1 = [counter1.get(term, 0) for term in all_terms]
        vec2 = [counter2.get(term, 0) for term in all_terms]
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def get_match_explanation(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed explanation of match score."""
        explanation = {
            'skills_score': self._calculate_skills_match(resume_data, job_data),
            'experience_score': self._calculate_experience_match(resume_data, job_data),
            'education_score': self._calculate_education_match(resume_data, job_data),
            'text_similarity_score': self._calculate_text_similarity(resume_data, job_data),
            'overall_score': self.calculate_match_score(resume_data, job_data)
        }
        
        # Add detailed breakdowns
        resume_skills = resume_data.get('skills', [])
        job_text = self._get_job_full_text(job_data).lower()
        job_skills = self._extract_skills_from_text(job_text)
        
        explanation['matching_skills'] = list(set([skill.lower() for skill in resume_skills]) & set(job_skills))
        explanation['missing_skills'] = list(set(job_skills) - set([skill.lower() for skill in resume_skills]))
        
        return explanation
