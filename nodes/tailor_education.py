from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState

def tailor_education(state: ResumeState) -> ResumeState:
    """
    Tailor education section by emphasizing relevant coursework and achievements.
    Formats coursework as "Relevant coursework: Course 1, Course 2, ..." instead of individual bullets.
    CRITICAL: Only modifies highlights - never changes institutions, degrees, or dates.
    """
    print("🎓 Tailoring education section (consolidating coursework into single lines)...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_education = state['working_cv']['cv']['sections'].get('education', [])
        
        if not current_education:
            print("   ℹ️ No education section found, skipping...")
            state['education_tailored'] = True
            return state
        
        job_requirements = state['job_requirements']
        
        # Extract only the highlights for modification
        education_highlights = []
        for i, edu in enumerate(current_education):
            education_highlights.append({
                'entry_index': i,
                'institution': edu.get('institution', 'Unknown'),
                'degree': edu.get('degree', 'Unknown'),
                'area': edu.get('area', 'Unknown'),
                'current_highlights': edu.get('highlights', [])
            })
        
        prompt = f"""
        You are tailoring education section highlights ONLY. DO NOT change institutions, degrees, dates, or any other details.

        Current Education Highlights to Modify:
        {education_highlights}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}

        CRITICAL INSTRUCTIONS:
        1. ONLY modify the highlights content - nothing else
        2. DO NOT change or invent institution names, degrees, areas, or dates
        3. For each education entry, provide improved highlights that:
           - Format relevant coursework as ONE line: "Relevant coursework: Course 1, Course 2, Course 3, Course 4, Course 5"
           - Select ONLY the 5 most relevant courses that align with job requirements
           - Include other achievements (GPA, scholarships, etc.) as separate highlights
           - Focus on skills and knowledge gained that apply to the target role
        4. Keep highlights factual and realistic
        5. IMPORTANT: Coursework should be formatted as a single comma-separated line, not individual bullet points

        FORMATTING EXAMPLE:
        Instead of:
        - "Course 1"
        - "Course 2" 
        - "Course 3"
        
        Use:
        - "Relevant coursework: Course 1, Course 2, Course 3"
        - "Other achievement (e.g., GPA, scholarship)"

        Return a JSON object with:
        - "updated_highlights": list of objects with "entry_index" and "new_highlights" 
        - "changes_summary": brief explanation of what was emphasized/removed
        
        Example format:
        {{
            "updated_highlights": [
                {{"entry_index": 0, "new_highlights": ["Relevant coursework: Data Science, Machine Learning, Statistics, Python Programming, Database Systems", "GPA: 3.5/4.0", "Academic scholarship"]}},
                {{"entry_index": 1, "new_highlights": ["Relevant coursework: Electronics, Programming, Circuit Design", "Thesis: Solar System Project"]}}
            ],
            "changes_summary": "Consolidated coursework into single lines and emphasized relevant courses"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. ONLY modify education highlights - never change institutions, degrees, or dates. CRITICAL: Consolidate coursework into single 'Relevant coursework: Course 1, Course 2, ...' lines instead of individual bullet points."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        updated_highlights = result.get('updated_highlights', [])
        changes_summary = result.get('changes_summary', 'No changes made')
        
        # Apply only the highlights updates to the original education entries
        updated_education = []
        for i, original_edu in enumerate(current_education):
            # Start with the exact original entry
            updated_entry = original_edu.copy()
            
            # Find if there are updated highlights for this entry
            for highlight_update in updated_highlights:
                if highlight_update.get('entry_index') == i:
                    new_highlights = highlight_update.get('new_highlights', [])
                    # Apply the new highlights (coursework now consolidated)
                    updated_entry['highlights'] = new_highlights
                    break
            
            updated_education.append(updated_entry)
        
        # Update the education section
        state['working_cv']['cv']['sections']['education'] = updated_education
        state['education_tailored'] = True
        
        print("✅ Education section tailored successfully")
        print(f"   - Education entries: {len(updated_education)}")
        print(f"   - Real institutions preserved: {', '.join([edu.get('institution', 'Unknown') for edu in updated_education])}")
        print(f"   - Coursework consolidated into single lines per entry")
        print(f"   - Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring education section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        # Don't modify education if there's an error - keep original
        state['education_tailored'] = True
    
    return state
