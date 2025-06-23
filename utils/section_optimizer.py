"""
Rule-based section ordering and optimization utilities.
Provides cost-effective alternative to LLM-based section reordering.
"""

from typing import Dict, Any, List, Tuple, Set
import re
from collections import Counter

def extract_job_keywords(job_requirements: Dict[str, Any]) -> Set[str]:
    """
    Extract key technologies and requirements from job requirements.
    """
    keywords = set()
    
    # Extract from various job requirement fields
    for field in ['key_technologies', 'essential_requirements', 'role_focus']:
        if field in job_requirements:
            values = job_requirements[field]
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, str):
                        # Extract technology names using regex
                        tech_words = re.findall(r'\b[a-zA-Z0-9+#.-]+\b', value.lower())
                        keywords.update(tech_words)
    
    # Add industry-specific keywords
    industry = job_requirements.get('industry_domain', '').lower()
    if 'data' in industry:
        keywords.update(['data', 'analytics', 'science', 'pipeline', 'warehouse'])
    elif 'software' in industry or 'tech' in industry:
        keywords.update(['software', 'development', 'programming', 'engineering'])
    elif 'web' in industry:
        keywords.update(['web', 'frontend', 'backend', 'fullstack'])
    
    return keywords

def calculate_section_relevance(section_name: str, section_data: List[Dict[str, Any]], 
                              job_keywords: Set[str]) -> float:
    """
    Calculate relevance score for a section based on job requirements.
    """
    if not section_data or not job_keywords:
        return 0.0
    
    # Base relevance scores for different section types
    base_scores = {
        'professional_summary': 0.9,
        'skills': 0.8,
        'experience': 0.9,
        'projects': 0.7,
        'education': 0.5,
        'certifications': 0.6,
        'extracurricular': 0.3,
        'publications': 0.4,
        'awards': 0.4
    }
    
    base_score = base_scores.get(section_name, 0.5)
    
    # Count keyword matches in section content
    keyword_matches = 0
    total_content = 0
    
    for entry in section_data:
        if isinstance(entry, dict):
            # Check all text fields in the entry
            for key, value in entry.items():
                if isinstance(value, str):
                    content_words = set(re.findall(r'\b[a-zA-Z0-9+#.-]+\b', value.lower()))
                    matches = len(content_words & job_keywords)
                    keyword_matches += matches
                    total_content += len(content_words)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            content_words = set(re.findall(r'\b[a-zA-Z0-9+#.-]+\b', item.lower()))
                            matches = len(content_words & job_keywords)
                            keyword_matches += matches
                            total_content += len(content_words)
        elif isinstance(entry, str):
            content_words = set(re.findall(r'\b[a-zA-Z0-9+#.-]+\b', entry.lower()))
            matches = len(content_words & job_keywords)
            keyword_matches += matches
            total_content += len(content_words)
    
    # Calculate relevance ratio
    if total_content > 0:
        relevance_ratio = keyword_matches / total_content
        return base_score * (1 + relevance_ratio * 2)  # Boost based on keyword density
    
    return base_score

def determine_optimal_section_order(cv_sections: Dict[str, Any], 
                                  job_requirements: Dict[str, Any]) -> List[str]:
    """
    Determine optimal section order based on job requirements and best practices.
    """
    job_keywords = extract_job_keywords(job_requirements)
    
    # Calculate relevance scores for each section
    section_scores = {}
    for section_name, section_data in cv_sections.items():
        if section_data:  # Only consider non-empty sections
            relevance_score = calculate_section_relevance(section_name, section_data, job_keywords)
            section_scores[section_name] = relevance_score
    
    # Apply ordering rules
    ordered_sections = []
    
    # 1. Professional summary always first (if present)
    if 'professional_summary' in section_scores:
        ordered_sections.append('professional_summary')
        del section_scores['professional_summary']
    
    # 2. Skills section early if highly relevant
    if 'skills' in section_scores and section_scores['skills'] > 0.7:
        ordered_sections.append('skills')
        del section_scores['skills']
    
    # 3. Experience section (always high priority)
    if 'experience' in section_scores:
        ordered_sections.append('experience')
        del section_scores['experience']
    
    # 4. Projects section if relevant
    if 'projects' in section_scores and section_scores['projects'] > 0.6:
        ordered_sections.append('projects')
        del section_scores['projects']
    
    # 5. Add skills if not already added
    if 'skills' in section_scores:
        ordered_sections.append('skills')
        del section_scores['skills']
    
    # 6. Sort remaining sections by relevance score
    remaining_sections = sorted(section_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Add remaining sections with decent relevance scores
    for section_name, score in remaining_sections:
        if score > 0.4:  # Only include sections with reasonable relevance
            ordered_sections.append(section_name)
    
    return ordered_sections

def identify_sections_to_remove(cv_sections: Dict[str, Any], 
                              job_requirements: Dict[str, Any]) -> Dict[str, str]:
    """
    Identify sections that should be removed and provide reasoning.
    """
    job_keywords = extract_job_keywords(job_requirements)
    sections_to_remove = {}
    
    # Industry-specific removal rules
    industry = job_requirements.get('industry_domain', '').lower()
    role_focus = job_requirements.get('role_focus', [])
    
    for section_name, section_data in cv_sections.items():
        if not section_data:  # Empty sections
            sections_to_remove[section_name] = "Section is empty"
            continue
        
        relevance_score = calculate_section_relevance(section_name, section_data, job_keywords)
        
        # Removal criteria based on section type and relevance
        if section_name == 'education':
            # Remove education for senior roles or when experience is strong
            experience_count = len(cv_sections.get('experience', []))
            if experience_count >= 4 and relevance_score < 0.6:
                sections_to_remove[section_name] = "Extensive work experience makes education less critical"
        
        elif section_name == 'certifications':
            # Remove if certifications are not relevant to the role
            if relevance_score < 0.4:
                sections_to_remove[section_name] = "Certifications not directly relevant to the role requirements"
        
        elif section_name == 'extracurricular':
            # Remove for senior/technical roles unless highly relevant
            if any(keyword in industry for keyword in ['senior', 'lead', 'principal']) or relevance_score < 0.5:
                sections_to_remove[section_name] = "Extracurricular activities less relevant for technical/senior roles"
        
        elif section_name == 'publications':
            # Keep only for research/academic roles
            if not any(keyword in industry for keyword in ['research', 'academic', 'science']):
                sections_to_remove[section_name] = "Publications not relevant for non-research roles"
        
        elif section_name == 'awards':
            # Remove unless highly relevant or recent
            if relevance_score < 0.5:
                sections_to_remove[section_name] = "Awards not directly relevant to the role"
        
        # General low relevance removal
        elif relevance_score < 0.3:
            sections_to_remove[section_name] = f"Low relevance score ({relevance_score:.1f}) for this role"
    
    return sections_to_remove

def optimize_section_structure(cv_sections: Dict[str, Any], 
                             job_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize CV section structure based on job requirements.
    """
    # Determine optimal order
    optimal_order = determine_optimal_section_order(cv_sections, job_requirements)
    
    # Identify sections to remove
    sections_to_remove = identify_sections_to_remove(cv_sections, job_requirements)
    
    # Create optimized structure
    optimized_sections = {}
    kept_sections = []
    removed_sections = []
    
    for section_name in optimal_order:
        if section_name not in sections_to_remove:
            optimized_sections[section_name] = cv_sections[section_name]
            kept_sections.append(section_name)
        else:
            removed_sections.append(section_name)
    
    # Add any remaining sections not in optimal order (if not removed)
    for section_name, section_data in cv_sections.items():
        if section_name not in optimized_sections and section_name not in sections_to_remove:
            optimized_sections[section_name] = section_data
            kept_sections.append(section_name)
    
    # Generate reasoning for decisions
    reasoning = {}
    
    # Reasoning for kept sections
    for section_name in kept_sections:
        if section_name == 'professional_summary':
            reasoning[section_name] = "Always keep and place first to provide a snapshot of expertise and goals"
        elif section_name == 'skills':
            reasoning[section_name] = "Essential for showcasing proficiency in key technologies"
        elif section_name == 'experience':
            reasoning[section_name] = "Critical to demonstrate relevant work history and achievements"
        elif section_name == 'projects':
            reasoning[section_name] = "Important to highlight practical application of skills"
        elif section_name == 'education':
            reasoning[section_name] = "Relevant educational background for the role"
        elif section_name == 'certifications':
            reasoning[section_name] = "Certifications align with job requirements"
        else:
            reasoning[section_name] = f"Maintained due to relevance to the role"
    
    # Reasoning for removed sections
    for section_name, reason in sections_to_remove.items():
        reasoning[section_name] = reason
    
    return {
        'optimized_sections': optimized_sections,
        'kept_sections': kept_sections,
        'removed_sections': removed_sections,
        'reasoning': reasoning,
        'section_order': list(optimized_sections.keys())
    }

def validate_section_optimization(original_sections: Dict[str, Any], 
                                optimized_sections: Dict[str, Any]) -> List[str]:
    """
    Validate that section optimization didn't remove critical information.
    """
    warnings = []
    
    # Check if critical sections were removed
    critical_sections = ['professional_summary', 'experience', 'skills']
    
    for section in critical_sections:
        if section in original_sections and section not in optimized_sections:
            warnings.append(f"Critical section '{section}' was removed - this may impact CV effectiveness")
    
    # Check if too many sections were removed
    original_count = len([s for s in original_sections.values() if s])
    optimized_count = len([s for s in optimized_sections.values() if s])
    
    if optimized_count < original_count * 0.5:  # Removed more than 50% of sections
        warnings.append(f"Removed {original_count - optimized_count} sections - CV may be too sparse")
    
    return warnings 