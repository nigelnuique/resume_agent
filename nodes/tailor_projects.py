from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def tailor_projects(state: ResumeState) -> ResumeState:
    """
    Tailor projects section by reordering entries and modifying highlights.
    """
    print("🚀 Tailoring projects section...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_projects = state['working_cv']['cv']['sections'].get('projects', [])
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Tailor the projects section for this job application by reordering entries and modifying highlights.

        Current Projects:
        {current_projects}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}

        Instructions:
        1. Reorder projects by relevance to the target role (most relevant first)
        2. For each project, modify highlights and summary to:
           - Emphasize technical skills and outcomes relevant to the target role
           - Use keywords from the job advertisement naturally
           - Add quantification and impact metrics where possible
           - Highlight methodologies and tools that match job requirements
        3. Consider removing less relevant projects if there are many
        4. Keep all factual information accurate
        5. Maintain project timelines and links

        Return ONLY a properly formatted JSON object (no additional text) with:
        - "tailored_projects": list of project entries in new order with modified content
        - "changes_summary": brief explanation of reordering and content changes
        
        Example format:
        {{
            "tailored_projects": [...],
            "changes_summary": "Brief description of changes made"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Tailor project sections to showcase relevant technical skills and achievements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        result = safe_json_parse(response.choices[0].message.content, "tailor_projects")
        
        if result is None:
            # Provide fallback behavior - keep original projects
            fallback_data = {
                'tailored_projects': state['working_cv']['cv']['sections'].get('projects', []),
                'changes_summary': 'No changes made due to parsing error - original projects retained'
            }
            result = create_fallback_response("tailor_projects", fallback_data)
        
        tailored_projects = result.get('tailored_projects', state['working_cv']['cv']['sections'].get('projects', []))
        changes_summary = result.get('changes_summary', 'No changes summary available')
        
        # Update the projects section
        state['working_cv']['cv']['sections']['projects'] = tailored_projects
        state['projects_tailored'] = True
        
        print("✅ Projects section tailored successfully")
        print(f"   Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring projects section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
