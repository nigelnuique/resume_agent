from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState

def tailor_skills(state: ResumeState) -> ResumeState:
    """
    Tailor skills section by emphasizing relevant skills and matching job keywords.
    """
    print("🛠️ Tailoring skills section...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_skills = state['working_cv']['cv']['sections'].get('skills', [])
        job_requirements = state['job_requirements']
        
        # Get skills from other sections for context
        experience_skills = []
        for exp in state['working_cv']['cv']['sections'].get('experience', []):
            experience_skills.extend(exp.get('highlights', []))
        
        project_skills = []
        for proj in state['working_cv']['cv']['sections'].get('projects', []):
            project_skills.extend(proj.get('highlights', []))
        
        prompt = f"""
        Tailor the skills section for this job application by emphasizing relevant skills and matching terminology.

        Current Skills:
        {current_skills}

        Job Requirements:
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}
        - Desirable Requirements: {job_requirements.get('desirable_requirements', [])}
        - Role Focus: {job_requirements.get('role_focus', [])}

        Skills mentioned in Experience/Projects (for validation):
        {experience_skills + project_skills}

        Instructions:
        1. Reorder skill categories by relevance to the job
        2. For each skill category:
           - Remove skills not relevant to the target role
           - Use exact terminology from job advertisement where possible
           - Add relevant skills that are mentioned in experience/projects but missing from skills
           - Group related technologies logically
        3. Only add skills that can be supported by experience/projects in the CV
        4. Match naming conventions used in the job posting
        5. Prioritize essential requirements over desirable ones

        Return a JSON object with:
        - "tailored_skills": list of skill category objects with modified details
        - "changes_summary": brief explanation of skills added/removed/reordered
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Tailor skills sections to match job requirements while maintaining truthfulness."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        tailored_skills = result['tailored_skills']
        changes_summary = result['changes_summary']
        
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