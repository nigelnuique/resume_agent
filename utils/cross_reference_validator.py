"""
Cross-reference validation utilities using structured logic.
Provides cost-effective validation of consistency between CV sections.
"""

from typing import Dict, Any, List, Set, Tuple
import re
from collections import defaultdict

def extract_technologies_from_text(text: str) -> Set[str]:
    """
    Extract technology/skill mentions from text using keyword matching.
    """
    if not text:
        return set()
    
    # Common technology patterns
    tech_patterns = [
        # Programming languages
        r'\b(?:python|java|javascript|typescript|c\+\+|c#|ruby|php|go|rust|swift|kotlin|scala|r\b|matlab)\b',
        # Frameworks & libraries
        r'\b(?:react|vue|angular|django|flask|spring|express|laravel|rails|pandas|numpy|scikit-learn|tensorflow|pytorch)\b',
        # Databases
        r'\b(?:mysql|postgresql|mongodb|redis|elasticsearch|sql server|oracle|sqlite|cassandra|dynamodb)\b',
        # Cloud & DevOps
        r'\b(?:aws|azure|gcp|docker|kubernetes|jenkins|gitlab|github|terraform|ansible|chef|puppet)\b',
        # Tools & Platforms
        r'\b(?:git|linux|windows|macos|apache|nginx|hadoop|spark|kafka|airflow|tableau|power bi)\b',
    ]
    
    technologies = set()
    text_lower = text.lower()
    
    for pattern in tech_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        technologies.update(matches)
    
    return technologies

def validate_skills_experience_consistency(skills_section: List[str], experience_section: List[Dict[str, Any]]) -> List[str]:
    """
    Check if skills mentioned in skills section are actually demonstrated in experience.
    """
    issues = []
    
    # Extract skills from skills section
    claimed_skills = set()
    for skill_item in skills_section:
        if isinstance(skill_item, str):
            claimed_skills.update(extract_technologies_from_text(skill_item))
        elif isinstance(skill_item, dict) and 'name' in skill_item:
            claimed_skills.update(extract_technologies_from_text(skill_item['name']))
    
    # Extract technologies mentioned in experience
    demonstrated_skills = set()
    for exp in experience_section:
        highlights = exp.get('highlights', [])
        for highlight in highlights:
            demonstrated_skills.update(extract_technologies_from_text(highlight))
        
        # Also check position and summary
        if 'position' in exp:
            demonstrated_skills.update(extract_technologies_from_text(exp['position']))
        if 'summary' in exp:
            demonstrated_skills.update(extract_technologies_from_text(exp['summary']))
    
    # Find skills not demonstrated in experience
    undemonstrated_skills = claimed_skills - demonstrated_skills
    if undemonstrated_skills:
        issues.append(f"Skills claimed but not demonstrated in experience: {', '.join(sorted(undemonstrated_skills))}")
    
    # Find frequently mentioned skills not in skills section
    skill_counts = defaultdict(int)
    for skill in demonstrated_skills:
        skill_counts[skill] += 1
    
    frequently_used = {skill for skill, count in skill_counts.items() if count >= 2}
    missing_from_skills = frequently_used - claimed_skills
    if missing_from_skills:
        issues.append(f"Technologies frequently used but not in skills section: {', '.join(sorted(missing_from_skills))}")
    
    return issues

def validate_experience_project_consistency(experience_section: List[Dict[str, Any]], projects_section: List[Dict[str, Any]]) -> List[str]:
    """
    Check consistency between experience and projects sections.
    """
    issues = []
    
    # Extract technologies from both sections
    exp_technologies = set()
    for exp in experience_section:
        highlights = exp.get('highlights', [])
        for highlight in highlights:
            exp_technologies.update(extract_technologies_from_text(highlight))
    
    project_technologies = set()
    for project in projects_section:
        highlights = project.get('highlights', [])
        for highlight in highlights:
            project_technologies.update(extract_technologies_from_text(highlight))
    
    # Check for major discrepancies
    if project_technologies and exp_technologies:
        overlap = exp_technologies & project_technologies
        if len(overlap) < len(project_technologies) * 0.3:  # Less than 30% overlap
            issues.append("Low technology overlap between experience and projects - consider aligning them better")
    
    return issues

def validate_education_experience_timeline(education_section: List[Dict[str, Any]], experience_section: List[Dict[str, Any]]) -> List[str]:
    """
    Check if education and experience timelines make sense together.
    """
    issues = []
    
    try:
        from utils.date_validator import parse_resume_date
    except ImportError:
        print("⚠️ Date validator not available for timeline validation")
        return issues
    
    # Get education end dates
    education_ends = []
    for edu in education_section:
        end_date = edu.get('end_date', '')
        if end_date and end_date.lower() not in ['present', 'current']:
            end_dt = parse_resume_date(end_date)
            if end_dt:
                education_ends.append((end_dt, edu.get('degree', 'Degree')))
    
    # Get experience start dates
    experience_starts = []
    for exp in experience_section:
        start_date = exp.get('start_date', '')
        if start_date:
            start_dt = parse_resume_date(start_date)
            if start_dt:
                experience_starts.append((start_dt, exp.get('position', 'Position')))
    
    # Check for reasonable gaps
    if education_ends and experience_starts:
        latest_education = max(education_ends, key=lambda x: x[0])
        earliest_experience = min(experience_starts, key=lambda x: x[0])
        
        # If experience starts significantly before education ends
        if earliest_experience[0] < latest_education[0]:
            gap_years = (latest_education[0] - earliest_experience[0]).days / 365.25
            if gap_years > 1:  # More than 1 year overlap
                issues.append(f"Experience started {gap_years:.1f} years before education ended - verify timeline")
    
    return issues

def validate_contact_information(cv_data: Dict[str, Any]) -> List[str]:
    """
    Validate contact information for completeness and format.
    """
    issues = []
    
    name = cv_data.get('name', '')
    email = cv_data.get('email', '')
    phone = cv_data.get('phone', '')
    location = cv_data.get('location', '')
    
    # Check for required fields
    if not name:
        issues.append("Name is missing")
    
    if not email:
        issues.append("Email is missing")
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        issues.append(f"Email format appears invalid: {email}")
    
    if not phone:
        issues.append("Phone number is missing")
    elif not re.match(r'^[\+]?[1-9][\d\s\-\(\)]{7,}$', phone.replace(' ', '')):
        issues.append(f"Phone number format appears invalid: {phone}")
    
    if not location:
        issues.append("Location is missing")
    
    return issues

def validate_section_completeness(cv_sections: Dict[str, Any]) -> List[str]:
    """
    Check if required sections are present and have content.
    """
    issues = []
    
    required_sections = ['professional_summary', 'experience', 'skills']
    recommended_sections = ['education', 'projects']
    
    for section in required_sections:
        if section not in cv_sections:
            issues.append(f"Required section missing: {section}")
        elif not cv_sections[section]:
            issues.append(f"Required section is empty: {section}")
    
    for section in recommended_sections:
        if section not in cv_sections:
            issues.append(f"Recommended section missing: {section}")
    
    # Check professional summary length
    if 'professional_summary' in cv_sections:
        summary = cv_sections['professional_summary']
        if isinstance(summary, list):
            summary_text = ' '.join(summary)
        else:
            summary_text = str(summary)
        
        word_count = len(summary_text.split())
        if word_count < 20:
            issues.append(f"Professional summary is too short ({word_count} words)")
        elif word_count > 100:
            issues.append(f"Professional summary is too long ({word_count} words)")
    
    return issues

def generate_consistency_report(cv_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive consistency report for the CV.
    """
    sections = cv_data.get('sections', {})
    issues = []
    
    # Run all validation checks
    issues.extend(validate_contact_information(cv_data))
    issues.extend(validate_section_completeness(sections))
    
    if 'skills' in sections and 'experience' in sections:
        issues.extend(validate_skills_experience_consistency(sections['skills'], sections['experience']))
    
    if 'experience' in sections and 'projects' in sections:
        issues.extend(validate_experience_project_consistency(sections['experience'], sections['projects']))
    
    if 'education' in sections and 'experience' in sections:
        issues.extend(validate_education_experience_timeline(sections['education'], sections['experience']))
    
    # Categorize issues by severity
    critical_issues = [issue for issue in issues if any(keyword in issue.lower() for keyword in ['missing', 'invalid', 'required'])]
    warning_issues = [issue for issue in issues if issue not in critical_issues]
    
    return {
        'all_issues': issues,
        'critical_issues': critical_issues,
        'warnings': warning_issues,
        'total_issues': len(issues),
        'critical_count': len(critical_issues),
        'warning_count': len(warning_issues),
        'validation_passed': len(critical_issues) == 0
    }

def suggest_improvements(cv_data: Dict[str, Any]) -> List[str]:
    """
    Suggest specific improvements based on CV analysis.
    """
    suggestions = []
    sections = cv_data.get('sections', {})
    
    # Technology consistency suggestions
    if 'skills' in sections and 'experience' in sections:
        skills_tech = set()
        for skill in sections['skills']:
            if isinstance(skill, str):
                skills_tech.update(extract_technologies_from_text(skill))
        
        exp_tech = set()
        for exp in sections['experience']:
            for highlight in exp.get('highlights', []):
                exp_tech.update(extract_technologies_from_text(highlight))
        
        if skills_tech and exp_tech:
            unique_to_skills = skills_tech - exp_tech
            unique_to_exp = exp_tech - skills_tech
            
            if unique_to_skills:
                suggestions.append(f"Consider adding examples of these skills to experience: {', '.join(sorted(list(unique_to_skills)[:3]))}")
            
            if unique_to_exp:
                suggestions.append(f"Consider adding these demonstrated technologies to skills: {', '.join(sorted(list(unique_to_exp)[:3]))}")
    
    # Section balance suggestions
    if 'experience' in sections:
        exp_count = len(sections['experience'])
        if exp_count < 2:
            suggestions.append("Consider adding more experience entries if available")
        elif exp_count > 6:
            suggestions.append("Consider consolidating or removing older/less relevant experience entries")
    
    return suggestions 