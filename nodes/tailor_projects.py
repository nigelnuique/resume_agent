from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def tailor_projects(state: ResumeState) -> ResumeState:
    """
    Tailor projects section by selecting top 4 most relevant projects and optimizing their content.
    """
    print("🚀 Tailoring projects section (limiting to 4 most relevant)...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_projects = state['working_cv']['cv']['sections'].get('projects', [])
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Select the 4 MOST RELEVANT projects for this job and tailor their content.

        Current Projects ({len(current_projects)} total):
        {current_projects}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}

        Instructions:
        1. Select ONLY the 4 most relevant projects (or fewer if less than 4 exist)
        2. Order them by relevance to the target role (most relevant first)
        3. For each selected project, optimize:
           - Summary to emphasize relevant outcomes and technologies
           - Highlights to showcase skills matching job requirements
           - Use keywords from the job advertisement naturally
           - Add quantification and impact metrics where possible
           - Remove irrelevant details
        4. Keep all factual information accurate
        5. Maintain project timelines and links

        CRITICAL: Return ONLY the top 4 most relevant projects, not all projects.

        Return ONLY a properly formatted JSON object (no additional text) with:
        - "tailored_projects": list of TOP 4 project entries in relevance order with optimized content
        - "changes_summary": brief explanation of selection criteria and content changes
        - "projects_removed": count of how many projects were excluded
        
        Example format:
        {{
            "tailored_projects": [...],
            "changes_summary": "Selected 4 most relevant projects and optimized content",
            "projects_removed": 2
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Switched to 3.5-turbo for efficiency
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Select and tailor the most relevant projects to showcase skills matching job requirements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        result = safe_json_parse(response.choices[0].message.content, "tailor_projects")
        
        if result is None:
            # Provide fallback behavior - keep original projects but limit to 4
            original_projects = state['working_cv']['cv']['sections'].get('projects', [])
            fallback_data = {
                'tailored_projects': original_projects[:4],  # Just take first 4
                'changes_summary': 'Limited to first 4 projects due to parsing error',
                'projects_removed': max(0, len(original_projects) - 4)
            }
            result = create_fallback_response("tailor_projects", fallback_data)
        
        tailored_projects = result.get('tailored_projects', state['working_cv']['cv']['sections'].get('projects', [])[:4])
        changes_summary = result.get('changes_summary', 'No changes summary available')
        projects_removed = result.get('projects_removed', 0)
        
        # Ensure we don't exceed 4 projects
        if len(tailored_projects) > 4:
            tailored_projects = tailored_projects[:4]
            projects_removed += len(tailored_projects) - 4
        
        # Update the projects section
        state['working_cv']['cv']['sections']['projects'] = tailored_projects
        state['projects_tailored'] = True
        
        print("✅ Projects section tailored successfully")
        print(f"   - Projects selected: {len(tailored_projects)}")
        if projects_removed > 0:
            print(f"   - Projects removed: {projects_removed}")
        print(f"   - Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring projects section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
