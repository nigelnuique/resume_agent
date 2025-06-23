from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState

def resolve_inconsistencies(state: ResumeState) -> ResumeState:
    """
    Resolve inconsistencies and unsupported claims found during cross-reference check.
    """
    print("🔧 Resolving inconsistencies...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        working_cv = state['working_cv']['cv']['sections']
        
        # Check if there are inconsistencies that need fixing (from warnings and errors)
        inconsistencies_to_fix = []
        inconsistencies_to_fix.extend([error for error in state['errors'] if 'inconsistent' in error.lower() or 'not supported' in error.lower() or 'no evidence' in error.lower()])
        inconsistencies_to_fix.extend([warning for warning in state['warnings'] if 'inconsistent' in warning.lower() or 'not supported' in warning.lower() or 'proficiency' in warning.lower()])
        
        if not inconsistencies_to_fix:
            print("✅ No inconsistencies to resolve")
            state['inconsistencies_resolved'] = True
            return state
        
        prompt = f"""
        Fix the inconsistencies in this CV by making specific corrections. The cross-reference check found several unsupported claims that need to be addressed.

        Current CV Sections:
        Professional Summary: {working_cv.get('professional_summary', [])}
        Experience: {working_cv.get('experience', [])}
        Projects: {working_cv.get('projects', [])}
        Education: {working_cv.get('education', [])}
        Skills: {working_cv.get('skills', [])}

        Inconsistencies Found:
        {inconsistencies_to_fix}

        Instructions:
        1. Remove or modify claims in the professional summary that aren't supported by experience/projects
        2. Remove skills that have no evidence in experience/projects/education
        3. Ensure all claims can be backed up by specific examples in the CV
        4. Keep all factual information accurate - only remove unsupported claims, don't add false information
        5. Maintain the tailored focus for the target job while ensuring accuracy

        Return a JSON object with the corrected sections:
        {{
            "professional_summary": [...],
            "experience": [...], 
            "projects": [...],
            "education": [...],
            "skills": [...],
            "corrections_made": ["list of specific corrections"]
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume editor focused on accuracy and consistency. Remove or modify unsupported claims while maintaining the CV's strength and relevance."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        # Update all sections with corrected versions
        for section_name in ['professional_summary', 'experience', 'projects', 'education', 'skills']:
            if section_name in result:
                state['working_cv']['cv']['sections'][section_name] = result[section_name]
        
        corrections_made = result.get('corrections_made', [])
        
        # Clear the resolved inconsistencies from errors and warnings
        state['errors'] = [error for error in state['errors'] if error not in inconsistencies_to_fix]
        state['warnings'] = [warning for warning in state['warnings'] if warning not in inconsistencies_to_fix]
        
        state['inconsistencies_resolved'] = True
        
        print("✅ Inconsistencies resolved successfully")
        print("   Corrections made:")
        for correction in corrections_made:
            print(f"   - {correction}")
        
    except Exception as e:
        error_msg = f"Error resolving inconsistencies: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state 