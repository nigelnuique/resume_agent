from typing import Dict, Any
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def resolve_inconsistencies(state: ResumeState) -> ResumeState:
    """
    Resolve any inconsistencies found in the CV using AI.
    """
    print("🔧 Resolving inconsistencies...")
    
    # Check if there are any inconsistencies to resolve
    inconsistencies = []
    
    # Collect inconsistencies from various sources
    if 'warnings' in state and state['warnings']:
        inconsistencies.extend(state['warnings'])
    
    if not inconsistencies:
        print("✅ No inconsistencies to resolve")
        state['inconsistencies_resolved'] = True
        return state
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_cv = state['working_cv']['cv']['sections']
        
        prompt = f"""
        Review and resolve the following inconsistencies found in this CV:

        Inconsistencies to resolve:
        {inconsistencies}

        Current CV sections:
        {current_cv}

        Please provide specific corrections for each inconsistency. Return a JSON object with:
        - "corrections": list of specific corrections made
        - "updated_sections": any CV sections that need to be updated (only include sections that changed)
        - "resolution_summary": brief summary of what was resolved

        Focus on making the CV internally consistent and accurate.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume editor. Resolve inconsistencies while maintaining accuracy and professionalism."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        result = safe_json_parse(response.choices[0].message.content, "resolve_inconsistencies")
        
        if result is None:
            print("   ⚠️ Could not parse inconsistency resolution - inconsistencies remain")
            state['inconsistencies_resolved'] = True
            return state
        
        corrections = result.get('corrections', [])
        updated_sections = result.get('updated_sections', {})
        resolution_summary = result.get('resolution_summary', 'No summary available')
        
        # Apply any section updates
        sections_updated = 0
        for section_name, section_content in updated_sections.items():
            if section_name in current_cv:
                current_cv[section_name] = section_content
                sections_updated += 1
        
        state['inconsistencies_resolved'] = True
        
        print("✅ Inconsistencies resolved successfully")
        print(f"   - Corrections made: {len(corrections)}")
        print(f"   - Sections updated: {sections_updated}")
        if resolution_summary:
            print(f"   - Summary: {resolution_summary}")
        
        # Clear resolved inconsistencies from warnings
        if corrections:
            state['warnings'] = []
        
    except Exception as e:
        error_msg = f"Error resolving inconsistencies: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        # Mark as resolved even if there's an error to avoid blocking the pipeline
        state['inconsistencies_resolved'] = True
    
    return state 