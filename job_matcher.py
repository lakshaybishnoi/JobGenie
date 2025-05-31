import re
from typing import Dict, List, Any
from collections import Counter
import math

class JobMatcher:
    """Job matching engine using NLP to score job-resume compatibility."""
    
    def __init__(self):
        # Try to load spaCy model if available
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except (ImportError, OSError):
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
        
        # Calculate cosine similarity
        return self._cosine_similarity(resume_keywords, job_keywords) * 100
    
    def _get_job_full_text(self, job_data: Dict[str, Any]) -> str:
        """Get full text from job data."""
        text_parts = []
        
        for field in ['title', 'summary', 'requirements']:
            value = job_data.get(field, '')
            if value:
                text_parts.append(str(value))
        
        return ' '.join(text_parts)
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract technical skills from job text."""
        # Common technical skills and tools
        skill_patterns = [
            r'\b(?:python|java|javascript|typescript|c\+\+|c#|php|ruby|go|rust|swift|kotlin)\b',
            r'\b(?:react|angular|vue|django|flask|spring|laravel|express|node\.js)\b',
            r'\b(?:sql|mysql|postgresql|mongodb|redis|oracle)\b',
            r'\b(?:aws|azure|gcp|docker|kubernetes|git|jenkins)\b',
            r'\b(?:html|css|rest|api|agile|scrum|linux|windows)\b'
        ]
        
        skills = set()
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skills.add(match.group().lower())
        
        return list(skills)
    
    def _extract_experience_keywords(self, text: str) -> List[str]:
        """Extract experience-related keywords from job text."""
        keywords = [
            'experience', 'years', 'worked', 'developed', 'managed', 'led', 
            'built', 'created', 'designed', 'implemented', 'maintained'
        ]
        
        found_keywords = []
        for keyword in keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _extract_years_experience(self, text: str) -> int:
        """Extract years of experience from text."""
        # Look for patterns like "3+ years", "5 years experience", etc.
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+?\s*years?\s*(?:in|with)',
            r'minimum\s*(?:of\s*)?(\d+)\s*years?',
            r'at\s*least\s*(\d+)\s*years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _extract_keywords_spacy(self, text: str) -> List[str]:
        """Extract keywords using spaCy."""
        if not self.nlp:
            return self._extract_keywords_basic(text)
        
        doc = self.nlp(text)
        keywords = []
        
        for token in doc:
            if (token.pos_ in ['NOUN', 'ADJ', 'VERB'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                keywords.append(token.lemma_.lower())
        
        return keywords
    
    def _extract_keywords_basic(self, text: str) -> List[str]:
        """Extract keywords using basic text processing."""
        # Simple word extraction with filtering
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Common stop words to exclude
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
            'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy',
            'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'
        }
        
        return [word for word in words if word not in stop_words]
    
    def _cosine_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """Calculate cosine similarity between two keyword lists."""
        if not keywords1 or not keywords2:
            return 0.0
        
        # Count word frequencies
        counter1 = Counter(keywords1)
        counter2 = Counter(keywords2)
        
        # Get all unique words
        all_words = set(counter1.keys()) | set(counter2.keys())
        
        # Create vectors
        vector1 = [counter1.get(word, 0) for word in all_words]
        vector2 = [counter2.get(word, 0) for word in all_words]
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a ** 2 for a in vector1))
        magnitude2 = math.sqrt(sum(b ** 2 for b in vector2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def get_match_explanation(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed explanation of match score."""
        explanation = {
            'overall_score': self.calculate_match_score(resume_data, job_data),
            'breakdown': {},
            'matching_skills': [],
            'missing_skills': [],
            'recommendations': []
        }
        
        # Calculate breakdown
        explanation['breakdown']['skills'] = self._calculate_skills_match(resume_data, job_data)
        explanation['breakdown']['experience'] = self._calculate_experience_match(resume_data, job_data)
        explanation['breakdown']['education'] = self._calculate_education_match(resume_data, job_data)
        explanation['breakdown']['text_similarity'] = self._calculate_text_similarity(resume_data, job_data)
        
        # Find matching and missing skills
        resume_skills = set(skill.lower() for skill in resume_data.get('skills', []))
        job_text = self._get_job_full_text(job_data).lower()
        job_skills = set(self._extract_skills_from_text(job_text))
        
        explanation['matching_skills'] = list(resume_skills & job_skills)
        explanation['missing_skills'] = list(job_skills - resume_skills)
        
        # Generate recommendations
        if explanation['breakdown']['skills'] < 70:
            explanation['recommendations'].append("Consider developing skills mentioned in the job requirements")
        
        if explanation['breakdown']['experience'] < 60:
            explanation['recommendations'].append("Highlight relevant experience that matches job requirements")
        
        if explanation['breakdown']['education'] < 50:
            explanation['recommendations'].append("Consider relevant certifications or education")
        
        return explanation