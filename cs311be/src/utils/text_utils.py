import re
import json
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise
import numpy as np
from src.engines.llm_engine import LLMEngine
import os
import time

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

def clean_text_for_pdf_parse(text: str) -> str:
    """Clean and format text extracted from PDF, DOCX, or JSON strings."""
    if not text:
        return ""
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove excessive spaces
    text = re.sub(r' {2,}', ' ', text)
    # Remove page numbers
    text = re.sub(r'\n\d+\n', '\n', text)
    # Convert single newlines to spaces
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    # Remove special characters that could cause LaTeX issues
    text = re.sub(r'[\\{}$&#^_~%]', ' ', text) 
    # Replace dashes with their LaTeX equivalent
    text = text.replace('-', '{-}')
    # Remove non-ASCII characters
    text = ''.join(char for char in text if ord(char) < 128)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text.strip()

def flatten_data(data) -> str:
    """Flatten complex data (dict or list) into a single string for embedding.
    
    Args:
        data: Input data (str, dict, or list)
        
    Returns:
        str: Flattened string representation of the data
    """
    if isinstance(data, str):
        return data
    elif isinstance(data, dict):
        return " ".join(f"{k}: {flatten_data(v)}" for k, v in data.items() if v)
    elif isinstance(data, list):
        return " ".join(flatten_data(item) for item in data if item)
    return str(data)

def clean_string(text: str):
    """Clean string for use in filenames."""
    text = text.title().replace(" ", "").strip()
    text = re.sub(r"[^a-zA-Z0-9]+", "", text)
    return text

async def generate_simple_report_pdf(report_content: dict) -> str:
    """Generate a simple PDF report using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        # Create temp file
        timestamp = int(time.time())
        pdf_path = f"temp/cv_report_{timestamp}.pdf"
        os.makedirs("temp", exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("CV Evaluation Report", title_style))
        story.append(Spacer(1, 20))
        
        # Basic Info
        story.append(Paragraph(f"<b>Candidate:</b> {report_content['candidate_name']}", styles['Normal']))
        story.append(Paragraph(f"<b>Position:</b> {report_content['job_title']}", styles['Normal']))
        story.append(Paragraph(f"<b>Company:</b> {report_content['company_name']}", styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {report_content['generated_date']}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Alignment Scores Section
        story.append(Paragraph("<b>Alignment Scores</b>", styles['Heading2']))
        
        for group_name, scores in report_content['alignment_scores'].items():
            story.append(Paragraph(f"<b>{group_name}:</b>", styles['Normal']))
            
            # Satisfied requirements
            if scores.get('satisfied_requirements'):
                satisfied_count = len(scores['satisfied_requirements'])
                story.append(Paragraph(f"✓ <b>Satisfied Requirements ({satisfied_count}):</b>", styles['Normal']))
                for req in scores['satisfied_requirements']:
                    story.append(Paragraph(f"  • {req}", styles['Normal']))
            
            # Unsatisfied requirements
            if scores.get('unsatisfied_requirements'):
                unsatisfied_count = len(scores['unsatisfied_requirements'])
                story.append(Paragraph(f"✗ <b>Missing Requirements ({unsatisfied_count}):</b>", styles['Normal']))
                for req in scores['unsatisfied_requirements']:
                    story.append(Paragraph(f"  • {req}", styles['Normal']))
            
            story.append(Spacer(1, 10))
        
        # CV Comments Section
        cv_comment = report_content['cv_comment']
        story.append(Paragraph("<b>CV Evaluation Comments</b>", styles['Heading2']))
        
        # Summary (if exists)
        if cv_comment.get('summary'):
            story.append(Paragraph(f"<b>Summary:</b> {cv_comment['summary']}", styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Advantages
        if cv_comment.get('advantages'):
            story.append(Paragraph("<b>Advantages:</b>", styles['Normal']))
            for advantage in cv_comment['advantages']:
                story.append(Paragraph(f"  • {advantage}", styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Disadvantages 
        if cv_comment.get('disadvantages'):
            story.append(Paragraph("<b>Disadvantages:</b>", styles['Normal']))
            for disadvantage in cv_comment['disadvantages']:
                story.append(Paragraph(f"  • {disadvantage}", styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Strengths (alternative field name)
        if cv_comment.get('strengths'):
            story.append(Paragraph("<b>Strengths:</b>", styles['Normal']))
            for strength in cv_comment['strengths']:
                story.append(Paragraph(f"  • {strength}", styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Weaknesses (alternative field name)
        if cv_comment.get('weaknesses'):
            story.append(Paragraph("<b>Areas for Improvement:</b>", styles['Normal']))
            for weakness in cv_comment['weaknesses']:
                story.append(Paragraph(f"  • {weakness}", styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Missing Information
        if cv_comment.get('missing_information'):
            story.append(Paragraph("<b>Missing Information:</b>", styles['Normal']))
            for missing in cv_comment['missing_information']:
                field_name = missing.get('field', 'Unknown field')
                suggestion = missing.get('suggestion', 'No suggestion provided')
                story.append(Paragraph(f"  • <b>{field_name}:</b> {suggestion}", styles['Normal']))
                story.append(Spacer(1, 5))
        
        # Build PDF
        doc.build(story)
        return pdf_path
        
    except ImportError:
        # Fallback to simple text-based PDF if reportlab not available
        return await generate_fallback_report_pdf(report_content)
    except Exception as e:
        print(f"Error generating report PDF: {e}")
        raise

async def generate_fallback_report_pdf(report_content: dict) -> str:
    """Fallback method to generate simple text-based PDF."""
    try:
        # Create simple HTML content
        html_content = f"""
        <html>
        <head><title>CV Evaluation Report</title></head>
        <body>
        <h1>CV Evaluation Report</h1>
        <p><strong>Candidate:</strong> {report_content['candidate_name']}</p>
        <p><strong>Position:</strong> {report_content['job_title']}</p>
        <p><strong>Company:</strong> {report_content['company_name']}</p>
        <p><strong>Generated:</strong> {report_content['generated_date']}</p>
        
        <h2>Alignment Scores</h2>
        """
        
        for group_name, scores in report_content['alignment_scores'].items():
            html_content += f"<h3>{group_name}</h3>"
            if scores.get('satisfied_requirements'):
                html_content += "<p><strong>✓ Satisfied Requirements:</strong></p><ul>"
                for req in scores['satisfied_requirements']:
                    html_content += f"<li>{req}</li>"
                html_content += "</ul>"
            
            if scores.get('unsatisfied_requirements'):
                html_content += "<p><strong>✗ Missing Requirements:</strong></p><ul>"
                for req in scores['unsatisfied_requirements']:
                    html_content += f"<li>{req}</li>"
                html_content += "</ul>"
        
        cv_comment = report_content['cv_comment']
        html_content += "<h2>CV Evaluation Comments</h2>"
        
        if cv_comment.get('summary'):
            html_content += f"<p><strong>Summary:</strong> {cv_comment['summary']}</p>"
        
        if cv_comment.get('strengths'):
            html_content += "<p><strong>Strengths:</strong></p><ul>"
            for strength in cv_comment['strengths']:
                html_content += f"<li>{strength}</li>"
            html_content += "</ul>"
        
        if cv_comment.get('weaknesses'):
            html_content += "<p><strong>Areas for Improvement:</strong></p><ul>"
            for weakness in cv_comment['weaknesses']:
                html_content += f"<li>{weakness}</li>"
            html_content += "</ul>"
        
        html_content += "</body></html>"
        
        # Save as text file (simple fallback)
        timestamp = int(time.time())
        txt_path = f"temp/cv_report_{timestamp}.txt"
        
        # Convert HTML to simple text
        import re
        text_content = re.sub(r'<[^>]+>', '', html_content)
        text_content = text_content.replace('&strong;', '').replace('&nbsp;', ' ')
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        return txt_path
        
    except Exception as e:
        raise Exception(f"Failed to generate fallback report: {str(e)}")

def calculate_cosine_similarity(embedding_1: list, embedding_2: list) -> float:
        """
        Calculate cosine similarity between two embedding vectors.
        
        Args:
            embedding_1 (list): First embedding vector
            embedding_2 (list): Second embedding vector
            
        Returns:
            float: Cosine similarity score between -1 and 1
        """
        try:
            import numpy as np
            
            # Convert to numpy arrays
            vec1 = np.array(embedding_1)
            vec2 = np.array(embedding_2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            
            # Avoid division by zero
            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0.0
            
            cosine_sim = dot_product / (norm_vec1 * norm_vec2)
            
            # Ensure the result is between -1 and 1
            cosine_sim = np.clip(cosine_sim, -1.0, 1.0)
            
            return float(cosine_sim)
            
        except Exception as e:
            print(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
def extract_resume_text(resume_data: dict) -> str:
        """
        Extract all text content from resume data into a single string.
        
        Args:
            resume_data (dict): Resume data from extract_cv output
            
        Returns:
            str: Concatenated text content from all fields
        """
        text_parts = []
        
        try:
            # Personal information
            if resume_data.get('name'):
                text_parts.append(f"Name: {resume_data['name']}")
            if resume_data.get('title'):
                text_parts.append(f"Title: {resume_data['title']}")
            if resume_data.get('summary'):
                text_parts.append(f"Summary: {resume_data['summary']}")
            if resume_data.get('email'):
                text_parts.append(f"Email: {resume_data['email']}")
            if resume_data.get('phone'):
                text_parts.append(f"Phone: {resume_data['phone']}")
            if resume_data.get('location'):
                text_parts.append(f"Location: {resume_data['location']}")
            
            # Media links
            if resume_data.get('media'):
                media = resume_data['media']
                if media.get('linkedin'):
                    text_parts.append(f"LinkedIn: {media['linkedin']}")
                if media.get('github'):
                    text_parts.append(f"GitHub: {media['github']}")
                if media.get('medium'):
                    text_parts.append(f"Medium: {media['medium']}")
                if media.get('devpost'):
                    text_parts.append(f"Devpost: {media['devpost']}")
            
            # Work experience
            if resume_data.get('work_experience'):
                text_parts.append("Work Experience:")
                for exp in resume_data['work_experience']:
                    if exp.get('role'):
                        text_parts.append(f"Role: {exp['role']}")
                    if exp.get('company'):
                        text_parts.append(f"Company: {exp['company']}")
                    if exp.get('location'):
                        text_parts.append(f"Location: {exp['location']}")
                    if exp.get('from_date'):
                        text_parts.append(f"From: {exp['from_date']}")
                    if exp.get('to_date'):
                        text_parts.append(f"To: {exp['to_date']}")
                    if exp.get('description'):
                        for desc in exp['description']:
                            if desc:
                                text_parts.append(desc)
            
            # Education
            if resume_data.get('education'):
                text_parts.append("Education:")
                for edu in resume_data['education']:
                    if edu.get('degree'):
                        text_parts.append(f"Degree: {edu['degree']}")
                    if edu.get('university'):
                        text_parts.append(f"University: {edu['university']}")
                    if edu.get('from_date'):
                        text_parts.append(f"From: {edu['from_date']}")
                    if edu.get('to_date'):
                        text_parts.append(f"To: {edu['to_date']}")
                    if edu.get('courses'):
                        for course in edu['courses']:
                            if course:
                                text_parts.append(f"Course: {course}")
            
            # Skills
            if resume_data.get('skill_section'):
                text_parts.append("Skills:")
                for skill_section in resume_data['skill_section']:
                    if skill_section.get('name'):
                        text_parts.append(f"Skill Group: {skill_section['name']}")
                    if skill_section.get('skills'):
                        for skill in skill_section['skills']:
                            if skill:
                                text_parts.append(f"Skill: {skill}")
            
            # Projects
            if resume_data.get('projects'):
                text_parts.append("Projects:")
                for project in resume_data['projects']:
                    if project.get('name'):
                        text_parts.append(f"Project: {project['name']}")
                    if project.get('type'):
                        text_parts.append(f"Type: {project['type']}")
                    if project.get('link'):
                        text_parts.append(f"Link: {project['link']}")
                    if project.get('from_date'):
                        text_parts.append(f"From: {project['from_date']}")
                    if project.get('to_date'):
                        text_parts.append(f"To: {project['to_date']}")
                    if project.get('description'):
                        for desc in project['description']:
                            if desc:
                                text_parts.append(desc)
                    if project.get('resources'):
                        for resource in project['resources']:
                            if resource.get('name'):
                                text_parts.append(f"Resource: {resource['name']}")
                            if resource.get('link'):
                                text_parts.append(f"Resource Link: {resource['link']}")
            
            # Certifications
            if resume_data.get('certifications'):
                text_parts.append("Certifications:")
                for cert in resume_data['certifications']:
                    if cert.get('name'):
                        text_parts.append(f"Certification: {cert['name']}")
                    if cert.get('by'):
                        text_parts.append(f"Issued by: {cert['by']}")
                    if cert.get('link'):
                        text_parts.append(f"Link: {cert['link']}")
            
            # Achievements
            if resume_data.get('achievements'):
                text_parts.append("Achievements:")
                for achievement in resume_data['achievements']:
                    if achievement:
                        text_parts.append(achievement)
            
            # Join all text parts
            full_text = " ".join(text_parts)
            
            # Clean the text using existing utility function
            cleaned_text = clean_text_for_pdf_parse(full_text)
            
            return cleaned_text
            
        except Exception as e:
            print(f"Error extracting resume text: {str(e)}")
            return ""
