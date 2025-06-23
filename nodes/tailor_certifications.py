from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def tailor_certifications(state: ResumeState) -> ResumeState:
    """
    Tailor certifications section by reordering and removing irrelevant certifications.
    """
    print("🏆 Tailoring certifications section...")
    
    try:
        # Check if certifications section exists
        current_certifications = state['working_cv']['cv']['sections'].get('certifications', [])
        
        if not current_certifications:
            print("   ℹ️ No certifications section found, skipping...")
            state['certifications_tailored'] = True
            return state
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        job_requirements = state['job_requirements']
        
        prompt = f"""
        Tailor the certifications section by selecting only relevant certifications and ordering them by relevance.

        Current Certifications:
        {current_certifications}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}
        - Desirable Requirements: {job_requirements.get('desirable_requirements', [])}

        Instructions:
        1. Select ONLY certifications that are relevant to the target role
        2. Order them by relevance (most relevant first)
        3. Remove certifications that are:
           - Unrelated to the job requirements
           - Too generic or outdated
           - Not adding value to the application
        4. Keep certifications that demonstrate:
           - Skills mentioned in job requirements
           - Industry knowledge relevant to the role
           - Technical competencies needed for the position

        Return a JSON object with:
        - "relevant_certifications": list of relevant certifications in order of relevance
        - "removed_certifications": list of certification names that were removed
        - "changes_summary": brief explanation of selection criteria and changes made
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Select and prioritize the most relevant certifications for the target role."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content, "tailor_certifications")
        
        if result is None:
            # Provide fallback behavior - keep all certifications
            fallback_data = {
                'relevant_certifications': current_certifications,
                'removed_certifications': [],
                'changes_summary': 'No changes made due to parsing error - all certifications retained'
            }
            result = create_fallback_response("tailor_certifications", fallback_data)
        
        relevant_certifications = result.get('relevant_certifications', [])
        removed_certifications = result.get('removed_certifications', [])
        changes_summary = result.get('changes_summary', 'No changes summary available')
        
        # Update the certifications section
        if relevant_certifications:
            state['working_cv']['cv']['sections']['certifications'] = relevant_certifications
        else:
            # Remove the entire certifications section if no relevant certs
            if 'certifications' in state['working_cv']['cv']['sections']:
                del state['working_cv']['cv']['sections']['certifications']
        
        state['certifications_tailored'] = True
        
        print("✅ Certifications section tailored successfully")
        print(f"   - Certifications kept: {len(relevant_certifications)}")
        if removed_certifications:
            print(f"   - Certifications removed: {len(removed_certifications)}")
        print(f"   - Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring certifications section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        # Don't fail the entire process if certifications tailoring fails
        state['certifications_tailored'] = True
    
    return state 