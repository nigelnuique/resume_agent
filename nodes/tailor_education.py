from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState

def tailor_education(state: ResumeState) -> ResumeState:
    """
    Tailor education section by emphasizing relevant coursework (max 5 per entry) and achievements.
    """
    print("🎓 Tailoring education section (limiting to 5 coursework items per entry)...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_education = state['working_cv']['cv']['sections'].get('education', [])
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Tailor the education section by selecting the most relevant coursework and achievements.

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
        2. For each education entry, modify ONLY the highlights to:
           - Select ONLY the 5 most relevant coursework items (or fewer if less exist)
           - Emphasize relevant coursework, projects, or thesis topics that align with job requirements
           - Focus on skills and knowledge gained that apply to the target role
           - Remove or exclude less relevant coursework
        3. Keep ALL other fields EXACTLY as they are (institution, area, degree, start_date, end_date, etc.)
        4. DO NOT change the structure - only modify highlights content
        5. Prioritize coursework that matches key technologies and essential requirements

        CRITICAL: 
        - Maintain the EXACT same structure as the input
        - Only modify the "highlights" field content
        - Limit coursework mentions to maximum 5 items per education entry
        - Keep all dates, institutions, degrees, areas exactly as provided

        Return a JSON object with:
        - "tailored_education": list of education entries with SAME structure but optimized highlights (max 5 coursework items each)
        - "changes_summary": brief explanation of coursework selection and emphasis changes
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Switched to 3.5-turbo for efficiency
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Tailor education section highlights only - keep all other fields unchanged. Maintain exact structure."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        tailored_education = result['tailored_education']
        changes_summary = result['changes_summary']
        
        # Validate and fix structure - ensure each entry has required RenderCV fields
        fixed_education = []
        for i, edu_entry in enumerate(tailored_education):
            # Start with the original entry to preserve structure
            original_entry = current_education[i] if i < len(current_education) else {}
            
            # Create a properly structured entry
            fixed_entry = {
                'institution': edu_entry.get('institution', original_entry.get('institution', 'Unknown Institution')),
                'area': edu_entry.get('area', original_entry.get('area', 'Unknown Area')),
                'degree': edu_entry.get('degree', original_entry.get('degree', 'Unknown Degree')),
                'start_date': edu_entry.get('start_date', original_entry.get('start_date', '')),
                'end_date': edu_entry.get('end_date', original_entry.get('end_date', '')),
                'highlights': edu_entry.get('highlights', original_entry.get('highlights', []))
            }
            
            # If the entry has a 'dates' field instead of start_date/end_date, try to parse it
            if 'dates' in edu_entry and not fixed_entry['start_date']:
                dates_str = edu_entry['dates']
                if ' - ' in dates_str:
                    start, end = dates_str.split(' - ', 1)
                    fixed_entry['start_date'] = start.strip()
                    fixed_entry['end_date'] = end.strip()
                else:
                    fixed_entry['start_date'] = dates_str
                    fixed_entry['end_date'] = dates_str
            
            # Add optional fields if they exist
            if 'gpa' in edu_entry:
                fixed_entry['gpa'] = edu_entry['gpa']
            elif 'gpa' in original_entry:
                fixed_entry['gpa'] = original_entry['gpa']
                
            # Ensure highlights is a list and limit to 5 items
            if isinstance(fixed_entry['highlights'], str):
                fixed_entry['highlights'] = [fixed_entry['highlights']]
            elif not isinstance(fixed_entry['highlights'], list):
                fixed_entry['highlights'] = []
            
            # Limit highlights to 5 items
            if len(fixed_entry['highlights']) > 5:
                fixed_entry['highlights'] = fixed_entry['highlights'][:5]
            
            fixed_education.append(fixed_entry)
        
        # Update the education section
        state['working_cv']['cv']['sections']['education'] = fixed_education
        state['education_tailored'] = True
        
        print("✅ Education section tailored successfully")
        print(f"   - Education entries: {len(fixed_education)}")
        print(f"   - Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring education section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
