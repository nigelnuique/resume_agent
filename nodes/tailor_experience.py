from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def tailor_experience(state: ResumeState) -> ResumeState:
    """
    Tailor experience section by reordering and emphasizing relevant experience.
    """
    print("💼 Tailoring experience section...")
    
    try:
        current_experience = state['working_cv']['cv']['sections'].get('experience', [])
        
        if not current_experience:
            print("   ℹ️ No experience section found, skipping...")
            state['experience_tailored'] = True
            return state
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Tailor the experience section for this job application by reordering experiences and optimizing content.

        Current Experience:
        {current_experience}

        Job Requirements:
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}

        Instructions:
        1. Reorder experiences to put most relevant ones first
        2. For each experience, optimize highlights to emphasize relevant skills and achievements
        3. Use keywords from job requirements naturally
        4. Quantify achievements where possible
        5. Focus on impact and results
        6. Keep all factual information accurate (companies, positions, dates, locations)

        Return a JSON object with:
        - "experiences": list of reordered and optimized experience entries
        - "changes_summary": brief explanation of changes made
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Optimize experience sections while maintaining factual accuracy."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content, "tailor_experience")
        
        if result is None:
            print("   ⚠️ Could not parse experience optimization - keeping original")
            state['experience_tailored'] = True
            return state
        
        experiences = result.get('experiences', current_experience)
        changes_summary = result.get('changes_summary', 'No changes summary available')
        
        # Update the experience section
        state['working_cv']['cv']['sections']['experience'] = experiences
        state['experience_tailored'] = True
        
        print("✅ Experience section tailored successfully")
        print(f"   Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring experience section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        # Don't fail the entire process if experience tailoring fails
        state['experience_tailored'] = True
    
    return state
