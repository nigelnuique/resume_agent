from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def tailor_skills(state: ResumeState) -> ResumeState:
    """
    Tailor skills section by reordering and emphasizing relevant skills.
    """
    print("🛠️ Tailoring skills section...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_skills = state['working_cv']['cv']['sections'].get('skills', {})
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Tailor the skills section for this job application by reordering and emphasizing relevant skills.

        Current Skills:
        {current_skills}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}

        Instructions:
        1. Reorder skill categories and individual skills by relevance to the target role
        2. Move the most relevant skills to the top of each category
        3. Consider creating new categories if it improves relevance
        4. Remove skills that are clearly irrelevant or outdated
        5. Keep all factual information accurate - only reorder, don't add new skills
        6. Ensure essential technologies are prominently featured

        Return a JSON object with:
        - "tailored_skills": reorganized skills section with categories in order of relevance
        - "changes_summary": brief explanation of reordering and emphasis changes
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Switched to 3.5-turbo for efficiency
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Tailor skills sections to match job requirements and highlight relevant competencies."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        result = safe_json_parse(response.choices[0].message.content, "tailor_skills")
        
        if result is None:
            # Provide fallback behavior - keep original skills
            fallback_data = {
                'tailored_skills': state['working_cv']['cv']['sections'].get('skills', {}),
                'changes_summary': 'No changes made due to parsing error - original skills retained'
            }
            result = create_fallback_response("tailor_skills", fallback_data)
        
        tailored_skills = result.get('tailored_skills', state['working_cv']['cv']['sections'].get('skills', {}))
        changes_summary = result.get('changes_summary', 'No changes summary available')
        
        # Update the skills section
        state['working_cv']['cv']['sections']['skills'] = tailored_skills
        state['skills_tailored'] = True
        
        print("✅ Skills section tailored successfully")
        print(f"   Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring skills section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state 