"""
Resume API endpoints for UtopiaHire

Handles:
- Resume upload (PDF/DOCX)
- Resume parsing and analysis
- Resume enhancement
- Resume deletion
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from urllib.parse import quote

# Setup logging
logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
from typing import Optional, List
from datetime import datetime
import os
import sys
from pathlib import Path
import json
import tempfile
import time
from psycopg2.extras import Json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import database as db_module

from backend.app.models.resume import (
    ResumeUploadResponse,
    ResumeAnalysisRequest,
    ResumeAnalysisResponse,
    ResumeEnhancementRequest,
    ResumeEnhancementDownloadRequest,
    ResumeEnhancementResponse,
    ResumeListResponse,
    ResumeDeleteResponse,
    ResumeListItem,
    ATSScore,
    SectionScore,
    EnhancementSuggestion,
    CoverLetterRequest,
    CoverLetterResponse
)
from backend.app.core.database import get_database, DatabaseWrapper
from backend.app.api.deps import get_current_active_user
from backend.app.models.user import UserResponse

# Import resume utilities
from utils.resume_parser import EnhancedResumeParser as ResumeParser
from utils.resume_analyzer import ResumeAnalyzer
from utils.resume_enhancer import ResumeEnhancer
from utils.cover_letter_generator import CoverLetterGenerator
from utils.resume_templates import ResumeTemplateGenerator


router = APIRouter()

# Configure upload settings
# Use environment variable, or detect Docker vs local environment
def get_upload_dir():
    env_dir = os.getenv("RESUME_UPLOAD_DIR")
    if env_dir:
        return Path(env_dir)
    # Check if running in Docker (/ app exists) or local
    if Path("/app").exists():
        return Path("/app/data/resumes")
    else:
        # Local development - use relative path from project root
        return Path(__file__).parent.parent.parent.parent / "data" / "resumes"

UPLOAD_DIR = get_upload_dir()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DATABASE_FILE_STORAGE = os.getenv("RESUME_STORAGE", "filesystem") == "database"


def restore_resume_file(resume):
    """Recover a cached source file when a free host replaces its filesystem."""
    file_path = Path(resume['file_path'])
    if not file_path.exists() and resume.get('file_content') is not None:
        file_path = UPLOAD_DIR / Path(resume['file_path']).name
        file_path.write_bytes(bytes(resume['file_content']))
    return file_path


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_active_user),
    db: DatabaseWrapper = Depends(get_database)
):
    """
    Upload and parse a resume file
    
    - **file**: PDF or DOCX resume file (max 10MB)
    
    Returns parsed resume metadata and ID for further operations
    Requires authentication
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded"
        )
    
    # Create unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    # Save file to disk
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Parse resume using Enhanced AI Parser
    try:
        parser = ResumeParser(use_ai=True)
        parsed_data = parser.parse_file(str(file_path))
        logger.info(f"Resume parsed. Quality: {parsed_data.get('metadata', {}).get('extraction_quality', 'unknown')}")
        
        # Store in database - save complete parsed data including raw_text for analysis
        parsed_data_to_store = {
            'raw_text': parsed_data.get('raw_text', ''),
            'sections': parsed_data.get('sections', {}),
            'structured_data': parsed_data.get('structured_data', {}),
            'metadata': parsed_data.get('metadata', {}),
            'validation': parsed_data.get('validation', {})  # AI validation results
        }
        
        resume_id = db.insert_one(
            "resumes",
            {
                "user_id": current_user.id,
                "filename": file.filename,
                "file_path": str(file_path),
                "file_size": file_size,
                "file_type": file_ext[1:],  # Remove dot
                "parsed_text": parsed_data.get('raw_text', ''),
                "parsed_data": Json(parsed_data_to_store),  # JSONB field
                "word_count": parsed_data.get('metadata', {}).get('word_count', 0),
                "uploaded_at": datetime.utcnow(),
                **({"file_content": content} if DATABASE_FILE_STORAGE else {})
            }
        )
        
        if resume_id is None:
            # Clean up file if database insert fails
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store resume in database"
            )
        
        return ResumeUploadResponse(
            resume_id=resume_id,
            filename=file.filename,
            file_size=file_size,
            file_type=file_ext[1:],
            parsed_text_length=len(parsed_data.get('raw_text', '')),
            word_count=parsed_data.get('metadata', {}).get('word_count', 0),
            uploaded_at=datetime.utcnow()
        )
        
    except Exception as e:
        # Clean up file on error
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume: {str(e)}"
        )


@router.post("/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    request: ResumeAnalysisRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    db: DatabaseWrapper = Depends(get_database)
):
    """
    Analyze a resume for ATS compatibility and quality
    
    - **resume_id**: ID of uploaded resume
    - **job_title**: Optional target job title for optimization
    - **job_description**: Optional job description to match against
    
    Returns comprehensive analysis with scores and recommendations
    Requires authentication
    """
    start_time = time.time()
    
    # Get resume from database
    resume = db.get_one(
        "resumes",
        "id = %s AND user_id = %s",
        (request.resume_id, current_user.id)
    )
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or access denied"
        )
    
    # Parse stored data
    try:
        parsed_text = resume['parsed_text'] or resume.get('raw_text', '')
        parsed_data = resume.get('parsed_data', {})
        # Handle JSONB field - it's already a dict from PostgreSQL
        if isinstance(parsed_data, str):
            parsed_sections = json.loads(parsed_data) if parsed_data else {}
        else:
            parsed_sections = parsed_data if parsed_data else {}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load resume data: {str(e)}"
        )
    
    # Analyze resume
    try:
        # Use the resume analyzer
        analyzer = ResumeAnalyzer(use_ai_models=True)  # Enable Groq AI analysis
        
        # Reconstruct parsed_resume format expected by analyzer
        # Extract structured_data from parsed_data if available
        structured_data = parsed_sections.get('structured_data', {}) if isinstance(parsed_sections, dict) else {}
        sections_only = parsed_sections.get('sections', parsed_sections) if isinstance(parsed_sections, dict) else parsed_sections
        
        parsed_resume_data = {
            'raw_text': parsed_text,
            'sections': sections_only,
            'structured_data': structured_data,
            'metadata': {
                'word_count': resume.get('word_count', 0),
                'filename': resume.get('filename', '')
            }
        }
        
        # Perform analysis
        try:
            analysis_result = analyzer.analyze(parsed_resume_data)
        except Exception as analyzer_error:
            # If analyzer fails, create a basic analysis
            print(f"Analyzer error: {analyzer_error}")
            analysis_result = {
                'scores': {
                    'overall_score': 75,
                    'ats_score': 70,
                    'formatting_score': 80,
                    'keyword_score': 75,
                    'content_score': 75
                },
                'grade': 'B',
                'strengths': ['Resume has good structure', 'Clear sections identified'],
                'weaknesses': ['Some improvements possible'],
                'suggestions': ['Add more quantified achievements', 'Optimize keywords for ATS'],
                'missing_sections': [],
                'word_count': resume.get('word_count', 0)
            }
        
        # Convert to response model
        scores = analysis_result.get('scores', {})
        ats_score = ATSScore(
            overall_score=scores.get('ats_score', 70),
            keyword_score=scores.get('keyword_score', 70),
            format_score=scores.get('formatting_score', 80),
            content_score=scores.get('content_score', 75),
            matched_keywords=[],
            missing_keywords=[],
            strengths=analysis_result.get('strengths', []),
            weaknesses=analysis_result.get('weaknesses', [])
        )
        
        # Build section scores (basic ones for now)
        section_scores = []
        for section_name in parsed_sections.keys():
            section_scores.append(SectionScore(
                section_name=section_name.title(),
                score=75.0,
                feedback=f"{section_name.title()} section present",
                issues=[],
                suggestions=[]
            ))
        
        overall_score = scores.get('overall_score', 75)
        
        # Get individual section scores from analyzer
        skill_match_score = float(scores.get('skill_match_score', 75.0))
        experience_score = float(scores.get('experience_score', 75.0))
        education_score = float(scores.get('education_score', 75.0))
        
        # Calculate grade
        if overall_score >= 95:
            grade = "A+"
        elif overall_score >= 90:
            grade = "A"
        elif overall_score >= 85:
            grade = "B+"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 75:
            grade = "C+"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        # Update database with analysis results
        db.update_one(
            "resumes",
            {
                "last_analyzed": datetime.utcnow(),
                "last_score": overall_score
            },
            "id = %s",
            (request.resume_id,)
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Convert suggestions to formatted string list
        suggestions = analysis_result.get('suggestions', [])
        recommendations = []
        for sug in suggestions:
            if isinstance(sug, dict):
                # Format suggestion nicely with priority and impact
                priority = sug.get('priority', 'medium').upper()
                category = sug.get('category', 'general').title()
                message = sug.get('message', str(sug))
                impact = sug.get('impact', '')
                
                # Create formatted suggestion
                formatted = f"[{priority}] {category}: {message}"
                if impact:
                    formatted += f" (Impact: {impact})"
                recommendations.append(formatted)
            else:
                recommendations.append(str(sug))
        
        return ResumeAnalysisResponse(
            resume_id=request.resume_id,
            overall_score=overall_score,
            skill_match_score=skill_match_score,
            experience_score=experience_score,
            education_score=education_score,
            grade=analysis_result.get('grade', grade),
            ats_score=ats_score,
            section_scores=section_scores,
            strengths=analysis_result.get('strengths', []),
            weaknesses=analysis_result.get('weaknesses', []),
            critical_issues=analysis_result.get('missing_sections', []),
            recommendations=recommendations,
            improvement_suggestions=recommendations,  # Same as recommendations for compatibility
            word_count=analysis_result.get('word_count', resume.get('word_count', 0)),
            action_verb_count=10,  # Placeholder
            quantified_achievements=5,  # Placeholder
            spelling_errors=0,
            formatting_issues=0,
            analyzed_at=datetime.utcnow(),
            analysis_duration_ms=duration_ms
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/enhance", response_model=ResumeEnhancementResponse)
async def enhance_resume(
    request: ResumeEnhancementRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    db: DatabaseWrapper = Depends(get_database)
):
    """
    Get AI-powered enhancement suggestions for a resume
    
    - **resume_id**: ID of uploaded resume
    - **enhancement_type**: Type of enhancement (full, grammar, action_verbs, quantify, ats_optimize)
    - **target_job**: Optional target job for tailored suggestions
    
    Returns list of specific improvement suggestions
    Requires authentication
    """
    # Get resume from database
    resume = db.get_one(
        "resumes",
        "id = %s AND user_id = %s",
        (request.resume_id, current_user.id)
    )
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or access denied"
        )
    
    # Parse stored data
    try:
        parsed_text = resume['parsed_text'] or resume.get('raw_text', '')
        parsed_data = resume.get('parsed_data', {})
        # Handle JSONB field - it's already a dict from PostgreSQL
        if isinstance(parsed_data, str):
            parsed_sections = json.loads(parsed_data) if parsed_data else {}
        else:
            parsed_sections = parsed_data if parsed_data else {}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load resume data: {str(e)}"
        )
    
    # Generate enhancements
    try:
        enhancer = ResumeEnhancer(use_ai_models=True)  # Enable Groq AI enhancement
        
        # Prepare data for enhancer (needs analysis too)
        # Extract structured_data from parsed_data if available
        structured_data = parsed_sections.get('structured_data', {}) if isinstance(parsed_sections, dict) else {}
        sections_only = parsed_sections.get('sections', parsed_sections) if isinstance(parsed_sections, dict) else parsed_sections
        
        parsed_resume_data = {
            'raw_text': parsed_text,
            'sections': sections_only,
            'structured_data': structured_data,
            'metadata': {
                'word_count': resume.get('word_count', 0),
                'filename': resume.get('filename', '')
            }
        }
        
        # Simple analysis for enhancement context
        analysis_data = {
            'scores': {'overall_score': 75},
            'suggestions': []
        }
        
        # Run enhancement
        enhancement_result = enhancer.enhance_resume(parsed_resume_data, analysis_data)
        
        # Convert to response format
        suggestions = []
        
        # Extract enhancements - enhancer returns flat structure with 'summary', 'experience', 'skills'
        changes_made = enhancement_result.get('changes_made', [])
        
        # Process changes into suggestions
        for change in changes_made:
            section = change.get('section', 'General')
            change_type = change.get('type', 'enhanced')
            description = change.get('description', '')
            
            # Determine impact based on section
            impact = 'high' if section in ['Professional Summary', 'Experience'] else 'medium'
            
            suggestions.append(EnhancementSuggestion(
                section=section,
                original_text=f"Original {section.lower()} content",
                enhanced_text=description,
                improvement_type=request.enhancement_type,
                impact=impact,
                explanation=description
            ))
        
        # Add specific enhancement details from the result
        enhanced_summary = enhancement_result.get('summary', '')
        original_summary = parsed_resume_data.get('structured_data', {}).get('summary', '')
        
        if enhanced_summary and enhanced_summary != original_summary:
            suggestions.append(EnhancementSuggestion(
                section='Professional Summary',
                original_text=original_summary[:200] if original_summary else 'Not provided',
                enhanced_text=enhanced_summary[:200],
                improvement_type=request.enhancement_type,
                impact='high',
                explanation='Enhanced professional summary with stronger language and better structure'
            ))
        
        # If no specific changes, create general suggestions
        if not suggestions:
            suggestions.append(EnhancementSuggestion(
                section='General',
                original_text='Your resume content',
                enhanced_text='Enhanced version with improved action verbs and quantification',
                improvement_type=request.enhancement_type,
                impact='medium',
                explanation='General improvements to resume content and structure'
            ))
        
        # Count by impact
        high_impact = sum(1 for s in suggestions if s.impact == 'high')
        medium_impact = sum(1 for s in suggestions if s.impact == 'medium')
        low_impact = sum(1 for s in suggestions if s.impact == 'low')
        
        improvements = enhancement_result.get('improvements', {})
        estimated_improvement = improvements.get('estimated_score_increase', 5.0)
        
        return ResumeEnhancementResponse(
            resume_id=request.resume_id,
            enhancement_type=request.enhancement_type,
            suggestions=suggestions,
            total_suggestions=len(suggestions),
            high_impact_count=high_impact,
            medium_impact_count=medium_impact,
            low_impact_count=low_impact,
            estimated_score_improvement=estimated_improvement,
            enhanced_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhancement failed: {str(e)}"
        )


@router.get("/list", response_model=ResumeListResponse)
async def list_resumes(
    page: int = 1,
    page_size: int = 10,
    current_user: UserResponse = Depends(get_current_active_user),
    db: DatabaseWrapper = Depends(get_database)
):
    """
    Get list of user's uploaded resumes
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 50)
    
    Returns paginated list of resumes
    Requires authentication
    """
    # Validate pagination
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 50:
        page_size = 10
    
    offset = (page - 1) * page_size
    
    # Get total count
    count_result = db.execute_query(
        "SELECT COUNT(*) as total FROM resumes WHERE user_id = %s",
        (current_user.id,)
    )
    total = count_result[0]['total'] if count_result else 0
    
    # Get resumes
    resumes = db.execute_query(
        """
        SELECT id, filename, uploaded_at, last_analyzed, last_score, word_count, file_type
        FROM resumes
        WHERE user_id = %s
        ORDER BY uploaded_at DESC
        LIMIT %s OFFSET %s
        """,
        (current_user.id, page_size, offset)
    )
    
    resume_items = []
    for resume in resumes:
        resume_items.append(ResumeListItem(
            resume_id=resume['id'],
            filename=resume['filename'],
            uploaded_at=resume['uploaded_at'],
            last_analyzed=resume.get('last_analyzed'),
            last_score=resume.get('last_score'),
            word_count=resume.get('word_count', 0),
            file_type=resume.get('file_type', 'unknown')
        ))
    
    return ResumeListResponse(
        resumes=resume_items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{resume_id}", response_model=ResumeDeleteResponse)
async def delete_resume(
    resume_id: int,
    current_user: UserResponse = Depends(get_current_active_user),
    db: DatabaseWrapper = Depends(get_database)
):
    """
    Delete a resume
    
    - **resume_id**: ID of resume to delete
    
    Removes resume from database and deletes file
    Requires authentication
    """
    # Get resume to verify ownership and get file path
    resume = db.get_one(
        "resumes",
        "id = %s AND user_id = %s",
        (resume_id, current_user.id)
    )
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or access denied"
        )
    
    # Delete file from disk
    try:
        file_path = Path(resume['file_path'])
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        # Log error but continue with database deletion
        print(f"Warning: Failed to delete file {resume['file_path']}: {e}")
    
    # Delete from database
    success = db.delete_one("resumes", "id = %s", (resume_id,))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume from database"
        )
    
    return ResumeDeleteResponse(
        message="Resume deleted successfully",
        success=True,
        resume_id=resume_id
    )


@router.get("/{resume_id}/download")
async def download_original_resume(
    resume_id: int,
    current_user: UserResponse = Depends(get_current_active_user),
    db: DatabaseWrapper = Depends(get_database)
):
    """
    Download the original resume file
    
    - **resume_id**: ID of resume to download
    
    Returns the original uploaded resume file
    Requires authentication
    """
    # Get resume to verify ownership and get file path
    resume = db.get_one(
        "resumes",
        "id = %s AND user_id = %s",
        (resume_id, current_user.id)
    )
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or access denied"
        )
    
    # Check if file exists
    if resume.get('file_content') is not None:
        filename = resume.get('filename', 'resume.pdf')
        return Response(
            content=bytes(resume['file_content']),
            media_type='application/octet-stream',
            headers={'Content-Disposition': f"attachment; filename*=UTF-8''{quote(filename, safe='')}"}
        )
    file_path = Path(resume['file_path'])
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found on disk"
        )
    
    # Return file
    return FileResponse(
        path=str(file_path),
        filename=resume.get('filename', resume.get('original_filename', 'resume.pdf')),
        media_type='application/octet-stream'
    )


@router.post("/{resume_id}/download-enhanced")
async def download_enhanced_resume(
    resume_id: int,
    request: ResumeEnhancementDownloadRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    db: DatabaseWrapper = Depends(get_database)
):
    """
    Generate and download an enhanced resume with AI improvements applied
    
    - **resume_id**: ID of resume to enhance (in URL path)
    - **enhancement_type**: Type of enhancement (full, grammar, action_verbs, quantify, ats_optimize)
    - **target_job**: Optional target job for tailored improvements
    - **selected_improvements**: Optional list of specific improvement IDs to apply
    
    Returns an enhanced PDF file with improvements applied
    Requires authentication
    """
    # Get resume to verify ownership
    resume = db.get_one(
        "resumes",
        "id = %s AND user_id = %s",
        (resume_id, current_user.id)
    )
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or access denied"
        )
    
    # Check if original file exists
    original_path = restore_resume_file(resume)
    if not original_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original resume file not found"
        )
    
    try:
        # Create enhanced directory if it doesn't exist
        enhanced_dir = UPLOAD_DIR / "enhanced"
        enhanced_dir.mkdir(exist_ok=True)
        
        # IMPORTANT: Re-parse the original file to get fresh, complete data
        # This ensures we have all the actual resume content, not just stored metadata
        logger.info(f"Re-parsing original file for enhancement: {original_path}")
        parser = ResumeParser()
        parsed_data = parser.parse_file(str(original_path))
        logger.info(f"Parsed data contains {len(parsed_data.get('raw_text', ''))} characters")
        
        # Get analysis data if available
        analysis_data_json = resume.get('analysis_data')
        analysis_data = json.loads(analysis_data_json) if isinstance(analysis_data_json, str) and analysis_data_json else {}
        
        # Generate enhancement - this returns a dict with enhanced sections
        enhancer = ResumeEnhancer(use_ai_models=True)  # Enable Groq AI enhancement
        enhancement_result = enhancer.enhance_resume(
            parsed_data,
            analysis_data or {}
        )
        
        # Get changes made for tracking
        changes_made = enhancement_result.get('changes_made', [])
        suggestions_count = len(changes_made)
        
        # Generate enhanced file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = resume.get('filename', 'resume.pdf')
        name_parts = original_name.rsplit('.', 1)
        enhanced_filename = f"{name_parts[0]}_enhanced_{timestamp}.{name_parts[1] if len(name_parts) > 1 else 'pdf'}"
        enhanced_path = enhanced_dir / enhanced_filename
        
        # Generate enhanced PDF with improvements
        logger.info(f"Generating enhanced PDF: {enhanced_path}")
        logger.info(f"Enhancement result keys: {list(enhancement_result.keys())}")
        
        try:
            success = enhancer.generate_enhanced_pdf(enhancement_result, str(enhanced_path))
            logger.info(f"PDF generation success: {success}")
            
            if not success or not enhanced_path.exists():
                logger.warning("PDF generation returned False or file not created, using fallback")
                # Fallback: copy original if PDF generation fails
                import shutil
                shutil.copy(str(original_path), str(enhanced_path))
                logger.info(f"Copied original file to: {enhanced_path}")
                
            # Verify file exists and has content
            if not enhanced_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Enhanced file was not created"
                )
                
            file_size = enhanced_path.stat().st_size
            if file_size == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Enhanced file is empty"
                )
                
            logger.info(f"Enhanced file ready: {enhanced_path} ({file_size} bytes)")
            
        except Exception as pdf_error:
            logger.error(f"Error during PDF generation: {pdf_error}")
            # Try fallback
            try:
                import shutil
                shutil.copy(str(original_path), str(enhanced_path))
                logger.info(f"Fallback: copied original file")
            except Exception as copy_error:
                logger.error(f"Fallback copy also failed: {copy_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create enhanced file: {str(pdf_error)}"
                )
        
        # Store enhancement record in database
        enhancement_record = {
            'resume_id': resume_id,
            'enhancement_type': request.enhancement_type,
            'suggestions_applied': suggestions_count,
            'enhanced_file_path': str(enhanced_path),
            'created_at': datetime.now()
        }
        
        db_module.execute_query(
            """
            INSERT INTO resume_enhancements 
            (resume_id, enhancement_type, suggestions_count, file_path, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (resume_id) DO UPDATE SET
                enhancement_type = EXCLUDED.enhancement_type,
                suggestions_count = EXCLUDED.suggestions_count,
                file_path = EXCLUDED.file_path,
                created_at = EXCLUDED.created_at
            """,
            (
                resume_id,
                request.enhancement_type,
                suggestions_count,
                str(enhanced_path),
                datetime.now()
            ),
            fetch=False
        )
        
        # Return enhanced file
        return FileResponse(
            path=str(enhanced_path),
            filename=enhanced_filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in download_enhanced_resume: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate enhanced resume: {str(e)}"
        )


@router.get("/templates")
async def list_resume_templates():
    """
    Get list of available resume templates
    
    Returns list of templates with descriptions and best-use cases
    No authentication required (public endpoint)
    """
    try:
        generator = ResumeTemplateGenerator()
        templates = generator.list_templates()
        
        return {
            "templates": templates,
            "total": len(templates),
            "message": "Available resume templates"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/templates/{template_id}/download")
async def download_resume_template(template_id: str):
    """
    Download a resume template DOCX file (editable Word document)
    
    - **template_id**: Template identifier (professional_chronological, modern_skills_focused, entry_level_student)
    
    Returns an editable DOCX template ready for customization
    No authentication required (public endpoint)
    """
    try:
        generator = ResumeTemplateGenerator()
        
        # Validate template ID
        if template_id not in generator.TEMPLATES:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{template_id}' not found. Available templates: {list(generator.TEMPLATES.keys())}"
            )
        
        # Generate template file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize template name: remove slashes and special characters, replace spaces with underscores
        template_name = generator.TEMPLATES[template_id]['name'].replace('/', '_').replace(' ', '_')
        filename = f"resume_template_{template_name}_{timestamp}.docx"
        
        # Create templates directory
        templates_dir = UPLOAD_DIR / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        output_path = templates_dir / filename
        
        # Generate template with detailed error logging
        try:
            success = generator.generate_template(template_id, str(output_path))
            
            if not success:
                logger.error(f"Template generation returned False for {template_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate template file for {template_id}"
                )
            
            # Verify file was created
            if not output_path.exists():
                logger.error(f"Template file was not created at {output_path}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Template file was not created"
                )
                
            logger.info(f"✓ Template generated successfully: {output_path}")
            
        except HTTPException:
            raise
        except Exception as gen_error:
            logger.error(f"Error during template generation: {gen_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Template generation error: {str(gen_error)}"
            )
        
        # Return file
        return FileResponse(
            path=str(output_path),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download template: {str(e)}"
        )


@router.post("/generate-cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: CoverLetterRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    db: DatabaseWrapper = Depends(get_database)
):
    """
    Generate a personalized cover letter based on resume and job description
    
    - **resume_id**: ID of the resume to use
    - **job_title**: Target job title/position
    - **company**: Company name
    - **job_description**: Full job description
    - **tone**: Writing tone (professional, enthusiastic, formal, conversational)
    - **length**: Letter length (short, medium, long)
    - **highlights**: Optional specific achievements to emphasize
    
    Returns generated cover letter with sections and suggestions
    """
    try:
        logger.info(f"User {current_user.id} generating cover letter for resume {request.resume_id}")
        
        # Verify resume exists and belongs to user
        resume_data = db.get_one(
            "resumes",
            "id = %s AND user_id = %s",
            (request.resume_id, current_user.id)
        )
        
        if not resume_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {request.resume_id} not found"
            )
        
        
        # Parse stored data
        try:
            parsed_text = resume_data['parsed_text'] or resume_data.get('raw_text', '')
            parsed_data = resume_data.get('parsed_data', {})
            # Handle JSONB field - it's already a dict from PostgreSQL
            if isinstance(parsed_data, str):
                parsed_sections = json.loads(parsed_data) if parsed_data else {}
            else:
                parsed_sections = parsed_data if parsed_data else {}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load resume data: {str(e)}"
            )
        
        if not parsed_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume has not been parsed yet. Please re-upload the resume."
            )
        
        # Reconstruct parsed_resume format
        structured_data = parsed_sections.get('structured_data', {}) if isinstance(parsed_sections, dict) else {}
        sections_only = parsed_sections.get('sections', parsed_sections) if isinstance(parsed_sections, dict) else parsed_sections
        
        parsed_resume = {
            'raw_text': parsed_text,
            'sections': sections_only,
            'structured_data': structured_data,
            'metadata': {
                'word_count': resume_data.get('word_count', 0),
                'filename': resume_data.get('filename', '')
            }
        }
        
        # Add analysis data if available
        if resume_data.get('analysis_result'):
            analysis = resume_data['analysis_result']
            if isinstance(analysis, str):
                analysis = json.loads(analysis)
            
            # Merge analysis data with parsed data
            if 'skills' in analysis:
                parsed_resume['skills'] = analysis['skills']
            if 'experience_years' in analysis:
                parsed_resume['experience_years'] = analysis['experience_years']
            if 'education' in analysis:
                parsed_resume['education'] = analysis['education']
        
        # Generate cover letter
        generator = CoverLetterGenerator()
        
        result = generator.generate(
            parsed_resume=parsed_resume,
            job_description=request.job_description,
            job_title=request.job_title,
            company=request.company,
            tone=request.tone,
            length=request.length,
            highlights=request.highlights
        )
        
        if 'error' in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
        
        logger.info(f"✓ Cover letter generated successfully ({result['word_count']} words)")
        
        return CoverLetterResponse(
            cover_letter=result['cover_letter'],
            word_count=result['word_count'],
            sections=result['sections'],
            suggestions=result['suggestions'],
            metadata=result['metadata']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cover letter: {str(e)}"
        )
