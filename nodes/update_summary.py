from typing import Dict, Any
import os
from openai import OpenAI
from state import ResumeState

def update_summary(state: ResumeState) -> ResumeState:
    """
    Update professional summary to align with job requirements.
    """
    print("📝 Updating professional summary...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_summary = state['working_cv']['cv']['sections'].get('professional_summary', [])
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Rewrite the professional summary to align with this job advertisement while staying truthful to the candidate's background.

        Current Professional Summary:
        {current_summary}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}
        - Company Culture: {job_requirements.get('company_culture', '')}
        - Tone: {job_requirements.get('tone_indicators', [])}

        CV Context (for truthfulness):
        - Experience: {[exp.get('position', '') + ' at ' + exp.get('company', '') for exp in state['working_cv']['cv']['sections'].get('experience', [])]}
        - Education: {[edu.get('degree', '') + ' in ' + edu.get('area', '') for edu in state['working_cv']['cv']['sections'].get('education', [])]}
        - Skills: {[skill.get('details', '') for skill in state['working_cv']['cv']['sections'].get('skills', [])]}

        Guidelines:
        1. Keep it to 2-3 bullet points or sentences
        2. Lead with the most relevant experience/skills for this role
        3. Use keywords from the job advertisement naturally
        4. Maintain professional tone matching the job posting
        5. Only mention skills/experience that exist elsewhere in the CV
        6. Quantify achievements where possible

        Return a JSON object with:
        - "summary": list of strings (each bullet point)
        - "changes_made": list of specific changes and reasons
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Tailor professional summaries to job requirements while maintaining truthfulness."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        new_summary = result['summary']
        changes_made = result['changes_made']
        
        # Update the professional summary
        state['working_cv']['cv']['sections']['professional_summary'] = new_summary
        state['summary_updated'] = True
        
        print("✅ Professional summary updated successfully")
        print("   Changes made:")
        for change in changes_made:
            print(f"   - {change}")
        
    except Exception as e:
        error_msg = f"Error updating professional summary: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
