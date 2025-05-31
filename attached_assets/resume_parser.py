import os
import re
import spacy
from typing import Dict, List, Any
import PyPDF2
from docx import Document

class ResumeParser:
    """Resume parser using spaCy for NLP processing."""
    
    def __init__(self):
        # Try to load spaCy model, use simple English if available
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback to basic processing if spaCy model not available
            self.nlp = None
            print("Warning: spaCy English model not found. Using basic text processing.")
        
        # Common skills patterns
        self.skill_patterns = [
            # Programming languages
            r'\b(?:Python|Java|JavaScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|TypeScript)\b',
            # Frameworks and libraries
            r'\b(?:React|Angular|Vue|Django|Flask|Spring|Laravel|Express|Node\.js|jQuery)\b',
            # Databases
            r'\b(?:SQL|MySQL|PostgreSQL|MongoDB|Redis|Oracle|SQLServer|SQLite)\b',
            # Cloud and DevOps
            r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|CI/CD|DevOps)\b',
            # Data Science
            r'\b(?:pandas|numpy|scikit-learn|TensorFlow|PyTorch|Jupyter|R|Tableau|Power BI)\b',
            # Other technologies
            r'\b(?:HTML|CSS|REST|API|GraphQL|Microservices|Agile|Scrum|Linux|Windows)\b'
        ]
        
        # Education patterns
        self.education_patterns = [
            r'\b(?:Bachelor|Master|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.|MBA|BS|MS|BA|MA)\b.*?(?:in|of).*?(?:\n|$)',
            r'\b(?:University|College|Institute)\b.*?(?:\n|$)',
            r'\b(?:Computer Science|Engineering|Mathematics|Physics|Business|Economics)\b'
        ]
    
    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse resume from file and extract relevant information."""
        # Extract text based on file type
        text = self._extract_text_from_file(file_path)
        
        if not text:
            return {'error': 'Could not extract text from file'}
        
        # Parse the text
        resume_data = {
            'filename': os.path.basename(file_path),
            'text': text,
            'skills': self._extract_skills(text),
            'education': self._extract_education(text),
            'experience': self._extract_experience(text),
            'contact_info': self._extract_contact_info(text)
        }
        
        return resume_data
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats."""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension == '.docx':
                return self._extract_from_docx(file_path)
            elif file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX: {e}")
        return text
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text."""
        skills = set()
        
        # Use regex patterns to find skills
        for pattern in self.skill_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skills.add(match.group().strip())
        
        # If spaCy is available, use NLP processing
        if self.nlp:
            doc = self.nlp(text)
            
            # Look for entities that might be skills
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT']:  # Organizations and products might be technologies
                    # Filter for tech-related terms
                    if any(tech in ent.text.lower() for tech in 
                          ['tech', 'software', 'system', 'platform', 'framework', 'library']):
                        skills.add(ent.text)
        
        return list(skills)
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education information from resume text."""
        education = []
        
        for pattern in self.education_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                edu_text = match.group().strip()
                if edu_text and len(edu_text) > 5:  # Filter out very short matches
                    education.append(edu_text)
        
        return education
    
    def _extract_experience(self, text: str) -> List[str]:
        """Extract work experience from resume text."""
        experience = []
        
        # Look for experience patterns
        experience_patterns = [
            r'(?:Experience|Work Experience|Employment History|Professional Experience)\s*:?\s*\n(.*?)(?=\n\s*(?:Education|Skills|Projects|$))',
            r'(\d{4}\s*-\s*(?:\d{4}|Present|Current)).*?(?=\n\d{4}|\n\s*[A-Z]|\n\s*$)',
        ]
        
        for pattern in experience_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                exp_text = match.group(1) if match.lastindex else match.group()
                if exp_text and len(exp_text.strip()) > 10:
                    # Clean up the text
                    exp_text = re.sub(r'\s+', ' ', exp_text.strip())
                    experience.append(exp_text)
        
        return experience
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume text."""
        contact_info = {}
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Phone pattern
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact_info['phone'] = phone_match.group()
        
        # LinkedIn pattern
        linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/pub/)([A-Za-z0-9\-]+)'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            contact_info['linkedin'] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
        
        return contact_info
    
    def get_resume_keywords(self, resume_data: Dict[str, Any]) -> List[str]:
        """Get important keywords from resume for job matching."""
        keywords = []
        
        # Add skills
        if resume_data.get('skills'):
            keywords.extend(resume_data['skills'])
        
        # Extract keywords from experience and education
        text = resume_data.get('text', '')
        if text and self.nlp:
            doc = self.nlp(text)
            
            # Extract important nouns and proper nouns
            for token in doc:
                if (token.pos_ in ['NOUN', 'PROPN'] and 
                    len(token.text) > 2 and 
                    token.is_alpha and 
                    not token.is_stop):
                    keywords.append(token.text.lower())
        
        # Remove duplicates and return
        return list(set(keywords))
