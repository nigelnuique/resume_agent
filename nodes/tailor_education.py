from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState

def tailor_education(state: ResumeState) -> ResumeState:
    """
    Tailor education section by emphasizing relevant coursework (max 5 per entry) and achievements.
    CRITICAL: Only modifies highlights - never changes institutions, degrees, or dates.
    """
    print("🎓 Tailoring education section (limiting to 5 coursework items per entry)...")
    
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
           - Select ONLY the 5 most relevant coursework/achievement items
           - Emphasize coursework that aligns with job requirements
           - Focus on skills and knowledge gained that apply to the target role
           - Remove less relevant coursework
        4. Keep highlights factual and realistic
        5. Maximum 5 highlight items per education entry

        Return a JSON object with:
        - "updated_highlights": list of objects with "entry_index" and "new_highlights" (max 5 items each)
        - "changes_summary": brief explanation of what was emphasized/removed
        
        Example format:
        {{
            "updated_highlights": [
                {{"entry_index": 0, "new_highlights": ["item1", "item2", "item3"]}},
                {{"entry_index": 1, "new_highlights": ["item1", "item2"]}}
            ],
            "changes_summary": "Emphasized relevant coursework"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. ONLY modify education highlights - never change institutions, degrees, or dates. Keep all information factually accurate."},
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
                    # Limit to 5 highlights maximum
                    updated_entry['highlights'] = new_highlights[:5]
                    break
            
            updated_education.append(updated_entry)
        
        # Update the education section
        state['working_cv']['cv']['sections']['education'] = updated_education
        state['education_tailored'] = True
        
        print("✅ Education section tailored successfully")
        print(f"   - Education entries: {len(updated_education)}")
        print(f"   - Real institutions preserved: {', '.join([edu.get('institution', 'Unknown') for edu in updated_education])}")
        print(f"   - Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring education section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        # Don't modify education if there's an error - keep original
        state['education_tailored'] = True
    
    return state
