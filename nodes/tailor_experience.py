from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState

def tailor_experience(state: ResumeState) -> ResumeState:
    """
    Tailor experience section by reordering entries and modifying highlights.
    """
    print("💼 Tailoring experience section...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_experience = state['working_cv']['cv']['sections'].get('experience', [])
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Tailor the experience section for this job application by reordering entries and modifying highlights.

        Current Experience:
        {current_experience}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}
        - Experience Level: {job_requirements.get('experience_level', 'Not specified')}

        Instructions:
        1. Reorder experiences by relevance to the target role (most relevant first)
        2. For each experience, modify highlights to:
           - Emphasize skills/achievements relevant to the target role
           - Use keywords from the job advertisement naturally
           - Add quantification where truthful and impactful
           - Remove or de-emphasize irrelevant highlights
        3. Keep all factual information accurate
        4. Maintain chronological accuracy of dates and companies

        Return a JSON object with:
        - "reordered_experience": list of experience entries in new order with modified highlights
        - "changes_summary": brief explanation of reordering and highlight changes
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Tailor experience sections to highlight relevant achievements and skills matching job requirements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        tailored_experience = result['reordered_experience']
        changes_summary = result['changes_summary']
        
        # Update the experience section
        state['working_cv']['cv']['sections']['experience'] = tailored_experience
        state['experience_tailored'] = True
        
        print("✅ Experience section tailored successfully")
        print(f"   Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring experience section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
