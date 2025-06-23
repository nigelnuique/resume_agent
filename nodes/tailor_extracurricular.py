from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState

def tailor_extracurricular(state: ResumeState) -> ResumeState:
    """
    Tailor extracurricular section by reordering and removing irrelevant activities.
    """
    print("🌟 Tailoring extracurricular activities section...")
    
    try:
        # Check if extracurricular section exists
        current_extracurricular = state['working_cv']['cv']['sections'].get('extracurricular', [])
        
        if not current_extracurricular:
            print("   ℹ️ No extracurricular section found, skipping...")
            state['extracurricular_tailored'] = True
            return state
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Tailor the extracurricular activities section by selecting only relevant activities that add value to the job application.

        Current Extracurricular Activities:
        {current_extracurricular}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Company Culture: {job_requirements.get('company_culture', '')}
        - Soft Skills: {job_requirements.get('soft_skills', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}

        Instructions:
        1. Select ONLY extracurricular activities that demonstrate relevant skills or qualities
        2. Order them by relevance to the target role
        3. Remove activities that are:
           - Completely unrelated to professional skills
           - Too personal or not professionally relevant
           - Outdated or from too long ago
        4. Keep activities that demonstrate:
           - Leadership skills
           - Teamwork and collaboration
           - Skills mentioned in job requirements
           - Qualities that align with company culture
           - Community involvement (if valued by company)

        Be very selective - most extracurricular activities should be removed for professional roles.

        Return a JSON object with:
        - "relevant_activities": list of relevant extracurricular activities in order of relevance (empty list if none are relevant)
        - "removed_activities": list of activity names that were removed
        - "changes_summary": brief explanation of selection criteria and changes made
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Be highly selective about extracurricular activities - only include those that directly add professional value."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        relevant_activities = result.get('relevant_activities', [])
        removed_activities = result.get('removed_activities', [])
        changes_summary = result.get('changes_summary', 'No changes summary available')
        
        # Update the extracurricular section
        if relevant_activities:
            state['working_cv']['cv']['sections']['extracurricular'] = relevant_activities
        else:
            # Remove the entire extracurricular section if no relevant activities
            if 'extracurricular' in state['working_cv']['cv']['sections']:
                del state['working_cv']['cv']['sections']['extracurricular']
        
        state['extracurricular_tailored'] = True
        
        print("✅ Extracurricular activities section tailored successfully")
        print(f"   - Activities kept: {len(relevant_activities)}")
        if removed_activities:
            print(f"   - Activities removed: {len(removed_activities)}")
        print(f"   - Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring extracurricular section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        # Don't fail the entire process if extracurricular tailoring fails
        state['extracurricular_tailored'] = True
    
    return state 