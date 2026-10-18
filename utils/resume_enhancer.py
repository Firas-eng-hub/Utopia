"""
Resume Rewriter/Enhancer Module for UtopiaHire
AI-powered resume improvement and optimization

WHY THIS MODULE:
- Rewrites weak bullet points with strong action verbs
- Optimizes content for ATS systems
- Enhances professional tone and impact
- Adds quantifiable achievements where possible
- Region-specific optimizations for MENA/Sub-Saharan Africa
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Groq AI Integration
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    logger.warning("⚠️ Groq not available - will use rule-based enhancement only")


class ResumeEnhancer:
    """
    Enhance and rewrite resume content for better impact
    """
    
    # Action verb replacements (weak → strong)
    ACTION_VERB_UPGRADES = {
        'helped': ['assisted', 'supported', 'facilitated', 'contributed to'],
        'worked on': ['developed', 'implemented', 'executed', 'delivered'],
        'did': ['performed', 'executed', 'accomplished', 'completed'],
        'made': ['created', 'developed', 'designed', 'built'],
        'was responsible for': ['managed', 'oversaw', 'directed', 'coordinated'],
        'used': ['utilized', 'leveraged', 'employed', 'applied'],
        'got': ['achieved', 'obtained', 'secured', 'earned'],
        'tried': ['initiated', 'pioneered', 'launched', 'spearheaded']
    }
    
    # Quantification templates
    QUANTIFICATION_TEMPLATES = [
        "by X%",
        "for X+ clients",
        "across X projects",
        "within X months",
        "X+ team members",
        "resulting in X% improvement",
        "$X in cost savings",
        "X users/customers"
    ]
    
    # Professional tone improvements
    TONE_IMPROVEMENTS = {
        'good': 'excellent',
        'nice': 'professional',
        'pretty': 'highly',
        'really': 'significantly',
        'very': 'exceptionally',
        'lots of': 'extensive',
        'a lot': 'substantial',
        'many': 'numerous'
    }
    
    # Regional keywords for MENA/Sub-Saharan Africa
    REGIONAL_ENHANCEMENTS = {
        'languages': ['bilingual', 'trilingual', 'multilingual', 'cross-cultural communication'],
        'remote': ['remote collaboration', 'distributed teams', 'virtual teamwork'],
        'local_context': ['emerging markets', 'regional expertise', 'local market knowledge']
    }
    
    def __init__(self, use_ai_models: bool = False):
        """
        Initialize enhancer
        
        Args:
            use_ai_models: If True, use Groq API for intelligent enhancement
                          If False, use rule-based enhancement (faster, works offline)
        """
        self.use_ai_models = use_ai_models and HAS_GROQ
        self.groq_client = None
        
        if self.use_ai_models:
            try:
                api_key = os.getenv('GROQ_API_KEY')
                if not api_key:
                    logger.warning("⚠️ GROQ_API_KEY not found - falling back to rule-based enhancement")
                    self.use_ai_models = False
                else:
                    self.groq_client = Groq(api_key=api_key)
                    logger.info("✓ Resume enhancer initialized with Groq AI")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.use_ai_models = False
                
        if not self.use_ai_models:
            logger.info("Resume enhancer initialized (rule-based improvements)")
    
    def enhance_resume(self, parsed_resume: Dict, analysis: Dict) -> Dict:
        """
        Main enhancement function
        
        Args:
            parsed_resume: Output from ResumeParser
            analysis: Output from ResumeAnalyzer
            
        Returns:
            Enhanced resume with improvements
        """
        logger.info(f"Starting resume enhancement... (AI: {self.use_ai_models})")
        
        sections = parsed_resume.get('sections', {})
        structured_data = dict(parsed_resume.get('structured_data', {}))
        # The current parser groups skills by category; enhancement expects a list.
        skills = structured_data.get('skills', [])
        if isinstance(skills, dict):
            structured_data['skills'] = list(dict.fromkeys(
                skill for category in skills.values() if isinstance(category, list)
                for skill in category if isinstance(skill, str)
            ))
        
        # Use Groq AI if available, otherwise fall back to rule-based
        if self.use_ai_models and self.groq_client:
            summary_enhanced = self._enhance_summary_with_groq(
                structured_data.get('summary', ''),
                structured_data
            )
        else:
            summary_enhanced = self._enhance_summary(
                structured_data.get('summary', ''),
                structured_data
            )
        
        enhancements = {
            'summary': summary_enhanced,
            'experience': self._enhance_experience(
                structured_data.get('experience', [])
            ),
            'skills': self._enhance_skills(
                structured_data.get('skills', [])
            ),
            'education': structured_data.get('education', []),  # Usually doesn't need enhancement
            'contact_info': structured_data.get('contact_info', {}),
            'changes_made': [],
            'improvement_summary': {}
        }
        
        # Track changes
        changes = []
        
        if enhancements['summary'] != structured_data.get('summary', ''):
            changes.append({
                'section': 'Professional Summary',
                'type': 'enhanced',
                'description': 'Improved professional summary with stronger language'
            })
        
        if len(enhancements['experience']) > 0:
            original_exp = structured_data.get('experience', [])
            enhanced_bullets = sum(len(exp.get('enhanced_bullets', [])) for exp in enhancements['experience'])
            original_bullets = sum(len(exp.get('bullet_points', [])) for exp in original_exp)
            
            if enhanced_bullets > original_bullets:
                changes.append({
                    'section': 'Experience',
                    'type': 'enhanced',
                    'description': f'Enhanced {enhanced_bullets} bullet points with action verbs and quantification'
                })
        
        if len(enhancements['skills']) > len(structured_data.get('skills', [])):
            changes.append({
                'section': 'Skills',
                'type': 'expanded',
                'description': f'Added {len(enhancements["skills"]) - len(structured_data.get("skills", []))} relevant skills'
            })
        
        enhancements['changes_made'] = changes
        
        # Calculate improvement metrics
        enhancements['improvement_summary'] = self._calculate_improvement_metrics(
            structured_data,
            enhancements,
            analysis
        )
        
        logger.info(f"✓ Enhancement complete - {len(changes)} improvements made")
        
        return enhancements
    
    def generate_enhanced_pdf(self, enhanced_data: Dict, output_path: str) -> bool:
        """
        Generate a PDF with enhanced resume content
        
        Args:
            enhanced_data: Enhanced resume data from enhance_resume()
            output_path: Path to save the PDF
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            
            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=letter,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)
            
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=12,
                alignment=1  # Center
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#374151'),
                spaceAfter=10,
                spaceBefore=12
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#4b5563'),
                spaceAfter=6
            )
            
            # Contact Info
            contact = enhanced_data.get('contact_info', {})
            if contact:
                name = contact.get('name', 'RESUME')
                story.append(Paragraph(name.upper(), title_style))
                story.append(Spacer(1, 6))
                
                contact_line = []
                if contact.get('email'):
                    contact_line.append(contact['email'])
                if contact.get('phone'):
                    contact_line.append(contact['phone'])
                if contact.get('location'):
                    contact_line.append(contact['location'])
                    
                if contact_line:
                    story.append(Paragraph(' | '.join(contact_line), body_style))
                    story.append(Spacer(1, 12))
            
            # Professional Summary
            summary = enhanced_data.get('summary', '')
            if summary:
                story.append(Paragraph('<b>PROFESSIONAL SUMMARY</b>', heading_style))
                story.append(Paragraph(summary, body_style))
                story.append(Spacer(1, 12))
            
            # Skills
            skills = enhanced_data.get('skills', [])
            if skills:
                story.append(Paragraph('<b>SKILLS</b>', heading_style))
                skills_text = ' • '.join(skills)
                story.append(Paragraph(skills_text, body_style))
                story.append(Spacer(1, 12))
            
            # Experience
            experience = enhanced_data.get('experience', [])
            if experience:
                story.append(Paragraph('<b>PROFESSIONAL EXPERIENCE</b>', heading_style))
                
                for exp in experience:
                    # Job title and company
                    job_title = exp.get('job_title', 'Position')
                    company = exp.get('company', 'Company')
                    dates = exp.get('dates', '')
                    
                    job_line = f"<b>{job_title}</b> at {company}"
                    if dates:
                        job_line += f" ({dates})"
                    
                    story.append(Paragraph(job_line, body_style))
                    story.append(Spacer(1, 4))
                    
                    # Bullet points (use enhanced if available)
                    bullets = exp.get('enhanced_bullets', exp.get('bullet_points', []))
                    for bullet in bullets:
                        bullet_text = bullet if bullet.startswith('•') else f'• {bullet}'
                        story.append(Paragraph(bullet_text, body_style))
                    
                    story.append(Spacer(1, 10))
            
            # Education
            education = enhanced_data.get('education', [])
            if education:
                story.append(Paragraph('<b>EDUCATION</b>', heading_style))
                
                for edu in education:
                    degree = edu.get('degree', 'Degree')
                    institution = edu.get('institution', 'Institution')
                    dates = edu.get('dates', '')
                    
                    edu_line = f"<b>{degree}</b> from {institution}"
                    if dates:
                        edu_line += f" ({dates})"
                    
                    story.append(Paragraph(edu_line, body_style))
                    story.append(Spacer(1, 4))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"✓ Enhanced PDF generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced PDF: {e}")
            return False
    
    def _enhance_summary(self, original_summary: str, structured_data: Dict) -> str:
        """
        Enhance professional summary
        
        WHY: Summary is the first thing recruiters read
        Strong summaries capture attention immediately
        """
        if not original_summary or len(original_summary.split()) < 10:
            # Generate a summary if missing
            experience = structured_data.get('experience', [])
            skills = structured_data.get('skills', [])
            education = structured_data.get('education', [])
            
            # Extract key info
            years_exp = "experienced" if experience else "motivated"
            role = "professional"
            
            # Try to infer role from skills
            if any(s.lower() in ['python', 'java', 'javascript'] for s in skills[:5]):
                role = "Software Developer"
            elif any(s.lower() in ['data', 'analysis', 'sql'] for s in skills[:5]):
                role = "Data Analyst"
            
            top_skills = ", ".join(skills[:3]) if len(skills) >= 3 else "various technologies"
            
            generated_summary = (
                f"{years_exp.title()} {role} with strong expertise in {top_skills}. "
                f"Proven track record of delivering high-quality solutions and driving results. "
                f"Seeking opportunities to leverage technical skills and contribute to innovative projects."
            )
            
            return generated_summary
        
        # Enhance existing summary
        enhanced = original_summary
        
        # Replace weak words with stronger alternatives
        for weak, strong in self.TONE_IMPROVEMENTS.items():
            enhanced = re.sub(r'\b' + weak + r'\b', strong, enhanced, flags=re.IGNORECASE)
        
        # Ensure it starts with a strong opener
        if not any(enhanced.lower().startswith(word) for word in ['experienced', 'proven', 'accomplished', 'dedicated', 'results-driven']):
            enhanced = "Results-driven " + enhanced[0].lower() + enhanced[1:]
        
        return enhanced
    
    def _enhance_summary_with_groq(self, original_summary: str, structured_data: Dict) -> str:
        """
        Use Groq AI to enhance professional summary
        """
        if not self.groq_client:
            return self._enhance_summary(original_summary, structured_data)
        
        try:
            # Extract context
            experience = structured_data.get('experience', [])
            skills = structured_data.get('skills', [])
            education = structured_data.get('education', [])
            
            years_exp = len(experience)
            top_skills = ", ".join(skills[:5]) if skills else "various skills"
            
            prompt = f"""You are an expert resume writer. Rewrite this professional summary to be more impactful and ATS-friendly.

Original Summary: "{original_summary if original_summary else 'Not provided'}"

Context:
- Years of experience: {years_exp}
- Top skills: {top_skills}
- Education: {len(education)} degrees

Requirements:
1. Start with a strong action word (e.g., "Results-driven", "Accomplished", "Dedicated")
2. Include specific skills and achievements
3. Keep it concise (3-4 lines maximum)
4. Make it ATS-friendly with relevant keywords
5. Professional tone, no generic phrases

Return ONLY the enhanced summary text, nothing else."""

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            enhanced = response.choices[0].message.content.strip()
            # Remove quotes if Groq added them
            enhanced = enhanced.strip('"\'')
            
            logger.info("✓ Summary enhanced with Groq AI")
            return enhanced
            
        except Exception as e:
            logger.error(f"Groq enhancement failed: {e}")
            return self._enhance_summary(original_summary, structured_data)
    
    def _enhance_bullet_point_with_groq(self, bullet: str, job_title: str = "") -> str:
        """
        Use Groq AI to enhance a bullet point
        """
        if not self.groq_client:
            return self._enhance_bullet_point(bullet)
        
        try:
            prompt = f"""You are an expert resume writer. Rewrite this work experience bullet point to make it more impactful and ATS-friendly.

Original: "{bullet}"
Job Title: {job_title if job_title else "Not specified"}

Requirements:
1. Start with a strong action verb (e.g., Developed, Implemented, Managed, Led, Optimized)
2. Add quantifiable metrics if possible (use realistic estimates like "20%", "5+ projects", "$50K")
3. Highlight impact and results
4. Keep it concise (1-2 lines)
5. Professional tone, no fluff
6. If numbers are missing, add realistic quantification

Return ONLY the enhanced bullet point text (without bullet symbol), nothing else."""

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150
            )
            
            enhanced = response.choices[0].message.content.strip()
            # Remove quotes and bullet symbols if Groq added them
            enhanced = enhanced.strip('"\'•-* ')
            
            # Ensure proper ending
            if not enhanced.endswith('.'):
                enhanced += '.'
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Groq bullet enhancement failed: {e}")
            return self._enhance_bullet_point(bullet)
    
    def _enhance_experience(self, experience_list: List[Dict]) -> List[Dict]:
        """
        Enhance work experience bullet points
        
        WHY: Strong bullet points with action verbs and quantification stand out
        """
        enhanced_experience = []
        
        for exp in experience_list:
            enhanced_exp = exp.copy()
            original_bullets = exp.get('bullet_points', [])
            
            if not original_bullets:
                # Extract bullets from text if not already parsed
                text = exp.get('text', '')
                lines = text.split('\n')
                original_bullets = [line.strip() for line in lines if line.strip().startswith(('•', '-', '*'))]
            
            enhanced_bullets = []
            job_title = exp.get('job_title', '')
            
            for bullet in original_bullets:
                if self.use_ai_models and self.groq_client:
                    enhanced_bullet = self._enhance_bullet_point_with_groq(bullet, job_title)
                else:
                    enhanced_bullet = self._enhance_bullet_point(bullet)
                enhanced_bullets.append(enhanced_bullet)
            
            enhanced_exp['enhanced_bullets'] = enhanced_bullets
            enhanced_exp['original_bullets'] = original_bullets
            enhanced_experience.append(enhanced_exp)
        
        return enhanced_experience
    
    def _enhance_bullet_point(self, bullet: str) -> str:
        """
        Enhance a single bullet point
        """
        # Remove bullet character if present
        bullet = re.sub(r'^[•\-\*○]\s*', '', bullet).strip()
        
        if not bullet:
            return bullet
        
        enhanced = bullet
        
        # 1. Replace weak action verbs with strong ones
        for weak, strong_options in self.ACTION_VERB_UPGRADES.items():
            if bullet.lower().startswith(weak):
                strong = random.choice(strong_options)
                enhanced = strong.capitalize() + bullet[len(weak):]
                break
        
        # 2. Improve tone
        for weak, strong in self.TONE_IMPROVEMENTS.items():
            enhanced = re.sub(r'\b' + weak + r'\b', strong, enhanced, flags=re.IGNORECASE)
        
        # 3. Add quantification hints if missing numbers
        has_numbers = re.search(r'\d+', enhanced)
        if not has_numbers and len(enhanced.split()) < 15:
            # Suggest where quantification could be added (marked with [X])
            if 'improved' in enhanced.lower() or 'increased' in enhanced.lower() or 'reduced' in enhanced.lower():
                enhanced = re.sub(
                    r'(improved|increased|reduced|enhanced|optimized)',
                    r'\1 [+X%]',
                    enhanced,
                    count=1,
                    flags=re.IGNORECASE
                )
        
        # 4. Ensure proper capitalization
        if enhanced and not enhanced[0].isupper():
            enhanced = enhanced[0].upper() + enhanced[1:]
        
        # 5. Ensure it ends with period (professional)
        if enhanced and not enhanced.endswith('.'):
            enhanced += '.'
        
        return enhanced
    
    def _enhance_skills(self, skills_list: List[str]) -> List[str]:
        """
        Enhance and expand skills section
        """
        enhanced_skills = skills_list.copy()
        
        # Remove duplicates (case-insensitive)
        seen = set()
        unique_skills = []
        for skill in enhanced_skills:
            skill_lower = skill.lower().strip()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill.strip())
        
        enhanced_skills = unique_skills
        
        # Add complementary skills based on existing ones
        complementary_skills = self._suggest_complementary_skills(enhanced_skills)
        
        # Add without duplicates
        for skill in complementary_skills:
            if skill.lower() not in seen:
                enhanced_skills.append(skill)
                seen.add(skill.lower())
        
        # Categorize skills for better presentation
        categorized = self._categorize_skills(enhanced_skills)
        
        return enhanced_skills
    
    def _suggest_complementary_skills(self, existing_skills: List[str]) -> List[str]:
        """
        Suggest complementary skills based on existing ones
        """
        suggestions = []
        existing_lower = [s.lower() for s in existing_skills]
        
        # Programming language complements
        if 'python' in existing_lower and 'django' not in existing_lower:
            suggestions.append('Django')
        if 'python' in existing_lower and 'flask' not in existing_lower:
            suggestions.append('Flask')
        if 'javascript' in existing_lower and 'react' not in existing_lower:
            suggestions.append('React')
        if 'javascript' in existing_lower and 'node.js' not in existing_lower:
            suggestions.append('Node.js')
        
        # Database complements
        if any(db in existing_lower for db in ['sql', 'postgresql', 'mysql']):
            if 'database design' not in existing_lower:
                suggestions.append('Database Design')
        
        # Always useful soft skills
        soft_skills = ['Problem Solving', 'Team Collaboration', 'Communication', 'Time Management']
        for skill in soft_skills:
            if skill.lower() not in existing_lower:
                suggestions.append(skill)
        
        # Regional advantages
        if any(lang in existing_lower for lang in ['french', 'arabic']):
            if 'bilingual communication' not in existing_lower:
                suggestions.append('Bilingual Communication')
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Categorize skills for better organization
        """
        categories = {
            'Technical Skills': [],
            'Soft Skills': [],
            'Languages': [],
            'Tools & Frameworks': []
        }
        
        soft_skills_keywords = ['communication', 'leadership', 'teamwork', 'problem solving', 'collaboration', 'management']
        language_keywords = ['english', 'french', 'arabic', 'spanish', 'portuguese']
        
        for skill in skills:
            skill_lower = skill.lower()
            
            if any(lang in skill_lower for lang in language_keywords):
                categories['Languages'].append(skill)
            elif any(soft in skill_lower for soft in soft_skills_keywords):
                categories['Soft Skills'].append(skill)
            elif any(tool in skill_lower for tool in ['git', 'docker', 'aws', 'jenkins', 'kubernetes']):
                categories['Tools & Frameworks'].append(skill)
            else:
                categories['Technical Skills'].append(skill)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _calculate_improvement_metrics(self, original: Dict, enhanced: Dict, analysis: Dict) -> Dict:
        """
        Calculate improvement metrics
        """
        original_scores = analysis.get('scores', {})
        
        # Estimate improvement (this is a projection)
        estimated_improvements = {
            'ats_score': min(100, original_scores.get('ats_score', 0) + 5),
            'content_score': min(100, original_scores.get('content_score', 0) + 15),
            'keyword_score': min(100, original_scores.get('keyword_score', 0) + 10),
            'formatting_score': original_scores.get('formatting_score', 0)
        }
        
        estimated_overall = int(
            estimated_improvements['ats_score'] * 0.30 +
            estimated_improvements['formatting_score'] * 0.25 +
            estimated_improvements['keyword_score'] * 0.25 +
            estimated_improvements['content_score'] * 0.20
        )
        
        original_overall = original_scores.get('overall_score', 0)
        improvement_percentage = ((estimated_overall - original_overall) / max(original_overall, 1)) * 100
        
        return {
            'original_score': original_overall,
            'estimated_new_score': estimated_overall,
            'improvement_points': estimated_overall - original_overall,
            'improvement_percentage': round(improvement_percentage, 1),
            'key_improvements': [
                f"Content quality +{estimated_improvements['content_score'] - original_scores.get('content_score', 0)} points",
                f"Keyword optimization +{estimated_improvements['keyword_score'] - original_scores.get('keyword_score', 0)} points",
                f"ATS compatibility +{estimated_improvements['ats_score'] - original_scores.get('ats_score', 0)} points"
            ]
        }
    
    def generate_improved_resume_text(self, enhanced_data: Dict) -> str:
        """
        Generate formatted resume text from enhanced data
        """
        output = []
        
        # Contact info (would come from original)
        output.append("=" * 70)
        output.append("ENHANCED RESUME")
        output.append("=" * 70)
        output.append("")
        
        # Professional Summary
        if enhanced_data.get('summary'):
            output.append("PROFESSIONAL SUMMARY")
            output.append("-" * 70)
            output.append(enhanced_data['summary'])
            output.append("")
        
        # Experience
        if enhanced_data.get('experience'):
            output.append("PROFESSIONAL EXPERIENCE")
            output.append("-" * 70)
            for exp in enhanced_data['experience']:
                enhanced_bullets = exp.get('enhanced_bullets', [])
                if enhanced_bullets:
                    for bullet in enhanced_bullets:
                        output.append(f"  • {bullet}")
                output.append("")
        
        # Skills
        if enhanced_data.get('skills'):
            output.append("SKILLS")
            output.append("-" * 70)
            output.append(", ".join(enhanced_data['skills']))
            output.append("")
        
        # Changes Made
        if enhanced_data.get('changes_made'):
            output.append("")
            output.append("=" * 70)
            output.append("IMPROVEMENTS MADE")
            output.append("=" * 70)
            for change in enhanced_data['changes_made']:
                output.append(f"✓ {change['section']}: {change['description']}")
        
        # Improvement Summary
        if enhanced_data.get('improvement_summary'):
            summary = enhanced_data['improvement_summary']
            output.append("")
            output.append(f"📊 Projected Score: {summary.get('original_score')}/100 → {summary.get('estimated_new_score')}/100")
            output.append(f"   Improvement: +{summary.get('improvement_points')} points ({summary.get('improvement_percentage')}%)")
        
        return "\n".join(output)


# Test function
if __name__ == '__main__':
    print("Resume Enhancer Module - Ready to use!")
    print("\nUsage:")
    print("  from utils.resume_enhancer import ResumeEnhancer")
    print("  enhancer = ResumeEnhancer(use_ai_models=False)")
    print("  improved = enhancer.enhance_resume(parsed_resume, analysis)")
    print("  print(improved['improvement_summary'])")
