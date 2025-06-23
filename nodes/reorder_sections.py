from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState

def reorder_sections(state: ResumeState) -> ResumeState:
    """
    Reorder CV sections based on job requirements and relevance.
    """
    print("📋 Reordering CV sections...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Get current section order
        current_sections = list(state['working_cv']['cv']['sections'].keys())
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Based on this job advertisement analysis and current CV sections, determine the optimal order for CV sections.

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Experience Level: {job_requirements.get('experience_level', 'Not specified')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}

        Current CV Sections:
        {current_sections}

        Standard section priority guidelines:
        1. professional_summary - Always first
        2. For experienced roles: experience before education
        3. For technical roles: skills before projects if heavily technical
        4. For research roles: education and projects higher priority
        5. projects - Higher if role emphasizes specific project experience

        Return a JSON object with:
        - "section_order": ordered list of section names
        - "reasoning": brief explanation for the ordering

        Only include sections that exist in the current CV.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Reorder CV sections for maximum impact based on job requirements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        new_order = result['section_order']
        reasoning = result['reasoning']
        
        # Reorder sections in working_cv
        sections = state['working_cv']['cv']['sections']
        reordered_sections = {}
        
        for section_name in new_order:
            if section_name in sections:
                reordered_sections[section_name] = sections[section_name]
        
        # Add any missing sections at the end
        for section_name, section_data in sections.items():
            if section_name not in reordered_sections:
                reordered_sections[section_name] = section_data
        
        state['working_cv']['cv']['sections'] = reordered_sections
        state['sections_reordered'] = True
        
        print("✅ Sections reordered successfully")
        print(f"   - New order: {' → '.join(new_order)}")
        print(f"   - Reasoning: {reasoning}")
        
    except Exception as e:
        error_msg = f"Error reordering sections: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
