from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def reorder_sections(state: ResumeState) -> ResumeState:
    """
    Reorder CV sections based on job requirements and remove irrelevant sections.
    """
    print("📋 Reordering CV sections and removing irrelevant ones...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Get current section order
        current_sections = list(state['working_cv']['cv']['sections'].keys())
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Based on this job advertisement analysis and current CV sections, determine which sections to KEEP and their optimal order.

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Experience Level: {job_requirements.get('experience_level', 'Not specified')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}

        Current CV Sections:
        {current_sections}

        Guidelines for section inclusion and ordering:
        1. professional_summary - Always keep and place first
        2. skills/experience - Essential for most roles, order based on role type
        3. projects - Keep if role emphasizes project work or technical skills
        4. education - Keep for entry-level or academic roles, may remove for senior roles if not relevant
        5. certifications - Keep only if relevant to role requirements
        6. extracurricular - Often not relevant for professional roles, remove unless specifically valuable
        7. publications - Keep only for research/academic roles
        8. languages - Keep only if mentioned in job requirements or international role

        Return a JSON object with:
        - "sections_to_keep": ordered list of section names to include in final CV
        - "sections_to_remove": list of section names to remove completely
        - "reasoning": brief explanation for inclusions and exclusions

        Be selective - a focused CV is better than a comprehensive one.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Switched to 3.5-turbo for efficiency
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Optimize CV sections for maximum relevance and impact."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content, "reorder_sections")
        
        if result is None:
            # Provide fallback behavior - keep all sections in original order
            fallback_data = {
                'sections_to_keep': current_sections,
                'sections_to_remove': [],
                'reasoning': 'Kept all sections due to parsing error'
            }
            result = create_fallback_response("reorder_sections", fallback_data)
        
        sections_to_keep = result.get('sections_to_keep', current_sections)
        sections_to_remove = result.get('sections_to_remove', [])
        reasoning = result.get('reasoning', 'No reasoning available')
        
        # Create new sections dict with only relevant sections in optimal order
        sections = state['working_cv']['cv']['sections']
        filtered_sections = {}
        
        for section_name in sections_to_keep:
            if section_name in sections:
                filtered_sections[section_name] = sections[section_name]
        
        state['working_cv']['cv']['sections'] = filtered_sections
        state['sections_reordered'] = True
        
        print("✅ Sections optimized successfully")
        print(f"   - Sections kept: {' → '.join(sections_to_keep)}")
        if sections_to_remove:
            print(f"   - Sections removed: {', '.join(sections_to_remove)}")
        print(f"   - Reasoning: {reasoning}")
        
    except Exception as e:
        error_msg = f"Error optimizing sections: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
