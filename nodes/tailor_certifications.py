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
        Tailor the certifications section by selecting relevant certifications and ordering them by relevance.

        Current Certifications (USE ONLY THESE - DO NOT CREATE NEW ONES):
        {current_certifications}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}
        - Desirable Requirements: {job_requirements.get('desirable_requirements', [])}
        - Certifications Required: {job_requirements.get('certifications_required', [])}
        - Technical Expertise: {job_requirements.get('technical_expertise', [])}
        - Professional Qualifications: {job_requirements.get('professional_qualifications', [])}

        Instructions:
        1. Include any certification that relates to any skill, technology, or area of expertise mentioned in the job requirements.
        2. Be inclusive: if there is any reasonable connection between a certification and the job requirements, keep it.
        3. Prioritize certifications that demonstrate proficiency in the job's key technical or professional areas.
        4. Order certifications by relevance to the job requirements (most relevant first).
        5. Remove only certifications that are completely unrelated to the role's requirements.

        CRITICAL RULES:
        - Use ONLY the actual certifications listed above.
        - DO NOT create, invent, or generate new certification names.
        - If a certification relates to any skill, technology, or area of expertise in the job requirements, keep it.
        - Only remove certifications that are completely irrelevant to the job requirements.
        - When in doubt, keep the certification.

        PRIORITY ORDER:
        1. Certifications for skills, technologies, or areas of expertise mentioned in the job requirements.
        2. Industry-specific certifications relevant to the role.
        3. Professional certifications that demonstrate relevant expertise.
        4. General certifications that show professional development.

        Return a JSON object with:
        - "relevant_certifications": list of relevant certifications in order of relevance (use EXACT names from the list above)
        - "removed_certifications": list of certification names that were removed
        - "changes_summary": brief explanation of selection criteria and changes made
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer specializing in certification selection. CRITICAL: Be INCLUSIVE - if a certification relates to ANY skill, technology, or expertise mentioned in the job requirements, you MUST include it. Only remove certifications that are completely irrelevant to the role. Prioritize technical certifications that demonstrate proficiency in the job's key areas. Use ONLY the actual certifications provided - never create or invent new ones. When in doubt, KEEP the certification."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content or "", "tailor_certifications")
        
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