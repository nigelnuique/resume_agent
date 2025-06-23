from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState

def tailor_education(state: ResumeState) -> ResumeState:
    """
    Tailor education section by emphasizing relevant coursework and achievements.
    """
    print("🎓 Tailoring education section...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_education = state['working_cv']['cv']['sections'].get('education', [])
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Tailor the education section for this job application by emphasizing relevant coursework and achievements.

        Current Education:
        {current_education}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Education Requirements: {job_requirements.get('education_requirements', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}

        Instructions:
        1. Keep education entries in chronological order (most recent first)
        2. For each education entry, modify highlights to:
           - Emphasize relevant coursework, projects, or thesis topics
           - Highlight GPA if strong and relevant
           - Focus on skills and knowledge gained that apply to the target role
           - Remove or de-emphasize less relevant highlights
        3. Keep all factual information accurate (institutions, degrees, dates, GPA)
        4. Add relevant coursework or capstone projects if they align with job requirements

        Return a JSON object with:
        - "tailored_education": list of education entries with modified highlights
        - "changes_summary": brief explanation of emphasis changes made
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Tailor education sections to highlight relevant academic achievements and coursework."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        tailored_education = result['tailored_education']
        changes_summary = result['changes_summary']
        
        # Update the education section
        state['working_cv']['cv']['sections']['education'] = tailored_education
        state['education_tailored'] = True
        
        print("✅ Education section tailored successfully")
        print(f"   Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring education section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
