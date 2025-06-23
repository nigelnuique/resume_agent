from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def reorder_sections(state: ResumeState) -> ResumeState:
    """
    Reorder CV sections based on job requirements. Only remove sections that are empty or explicitly irrelevant.
    Individual tailoring functions handle content-specific removal decisions.
    """
    print("📋 Reordering CV sections for optimal presentation...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Get current sections and check which ones have content
        current_sections = state['working_cv']['cv']['sections']
        sections_with_content = {}
        empty_sections = []
        
        for section_name, content in current_sections.items():
            if content and (not isinstance(content, list) or len(content) > 0):
                sections_with_content[section_name] = content
            else:
                empty_sections.append(section_name)
        
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Based on this job advertisement analysis, determine the optimal order for existing CV sections.
        IMPORTANT: Only suggest removing sections that are truly irrelevant - most sections have already been processed by specialized functions.

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Experience Level: {job_requirements.get('experience_level', 'Not specified')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}

        Available CV Sections (with content):
        {list(sections_with_content.keys())}

        Empty sections (will be removed): {empty_sections}

        Guidelines for section ordering:
        1. professional_summary - Always first
        2. skills/experience - Order based on role emphasis (technical vs managerial)
        3. projects - High priority for technical roles
        4. education/certifications - Lower priority for experienced roles
        5. extracurricular - Lowest priority, remove only if truly irrelevant

        Return a JSON object with:
        - "optimal_order": ordered list of section names for final CV
        - "sections_to_remove": list of section names to remove (be conservative - only truly irrelevant ones)
        - "reasoning": brief explanation for the ordering and any removals

        Be conservative with removals - sections have already been tailored by specialized functions.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Focus on optimal section ordering rather than aggressive removal."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content, "reorder_sections")
        
        if result is None:
            # Provide fallback behavior - keep all sections with content in a reasonable order
            default_order = ['professional_summary', 'skills', 'experience', 'projects', 'education', 'certifications', 'extracurricular']
            sections_to_keep = [s for s in default_order if s in sections_with_content]
            # Add any remaining sections not in default order
            sections_to_keep.extend([s for s in sections_with_content.keys() if s not in sections_to_keep])
            
            fallback_data = {
                'optimal_order': sections_to_keep,
                'sections_to_remove': empty_sections,
                'reasoning': 'Used default ordering due to parsing error, removed only empty sections'
            }
            result = create_fallback_response("reorder_sections", fallback_data)
        
        optimal_order = result.get('optimal_order', list(sections_with_content.keys()))
        sections_to_remove = result.get('sections_to_remove', []) + empty_sections  # Always remove empty sections
        reasoning = result.get('reasoning', 'No reasoning available')
        
        # Create new sections dict with optimal order, excluding removed sections
        filtered_sections = {}
        
        for section_name in optimal_order:
            if section_name in sections_with_content and section_name not in sections_to_remove:
                filtered_sections[section_name] = sections_with_content[section_name]
        
        state['working_cv']['cv']['sections'] = filtered_sections
        state['sections_reordered'] = True
        
        kept_sections = list(filtered_sections.keys())
        removed_sections = list(set(current_sections.keys()) - set(kept_sections))
        
        print("✅ Sections optimized successfully")
        print(f"   - Final section order: {' → '.join(kept_sections)}")
        if removed_sections:
            print(f"   - Sections removed: {', '.join(removed_sections)}")
        print(f"   - Reasoning: {reasoning}")
        
    except Exception as e:
        error_msg = f"Error optimizing sections: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
