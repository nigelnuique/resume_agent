from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response


def tailor_certifications_and_extracurricular(state: ResumeState) -> ResumeState:
    """
    Tailor certifications and extracurricular sections together in a single LLM call.
    Both are simple filtering/reordering tasks that share the same job requirements context.
    """
    print("🏆🌟 Tailoring certifications and extracurricular sections...")

    current_certifications = state['working_cv']['cv']['sections'].get('certifications', [])
    current_extracurricular = state['working_cv']['cv']['sections'].get('extracurricular', [])

    # If both sections are empty, skip entirely
    if not current_certifications and not current_extracurricular:
        print("   ℹ️ No certifications or extracurricular sections found, skipping...")
        state['certifications_tailored'] = True
        state['extracurricular_tailored'] = True
        return state

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        job_requirements = state['job_requirements']

        # Build section-specific parts of the prompt
        cert_block = ""
        if current_certifications:
            cert_block = f"""
## CERTIFICATIONS

Current Certifications (USE ONLY THESE - DO NOT CREATE NEW ONES):
{current_certifications}

Instructions for certifications:
1. Include any certification that relates to any skill, technology, or area of expertise in the job requirements.
2. Be inclusive: if there is any reasonable connection, keep it.
3. Order by relevance to the job (most relevant first).
4. Remove only certifications completely unrelated to the role.
5. When in doubt, keep the certification.

PRIORITY ORDER:
1. Certifications for skills/technologies mentioned in the job requirements.
2. Industry-specific certifications relevant to the role.
3. Professional certifications that demonstrate relevant expertise.
4. General certifications showing professional development.
"""

        extra_block = ""
        if current_extracurricular:
            extra_block = f"""
## EXTRACURRICULAR ACTIVITIES

Current Extracurricular Activities:
{current_extracurricular}

Instructions for extracurricular:
1. Select ONLY activities that demonstrate relevant professional skills or qualities.
2. Order by relevance to the target role.
3. Remove activities that are completely unrelated to professional skills, too personal, or outdated.
4. Keep activities showing: leadership, teamwork, skills in job requirements, company culture alignment.
5. Be selective - only include activities that add professional value.
"""

        prompt = f"""
Tailor the following resume sections by filtering and reordering for relevance to the target job.

Job Requirements:
- Role Focus: {job_requirements.get('role_focus', [])}
- Industry: {job_requirements.get('industry_domain', 'General')}
- Key Technologies: {job_requirements.get('key_technologies', [])}
- Essential Requirements: {job_requirements.get('essential_requirements', [])}
- Soft Skills: {job_requirements.get('soft_skills', [])}
- Company Culture: {job_requirements.get('company_culture', '')}
- Certifications Required: {job_requirements.get('certifications_required', [])}
- Technical Expertise: {job_requirements.get('technical_expertise', [])}
- Professional Qualifications: {job_requirements.get('professional_qualifications', [])}
{cert_block}{extra_block}
CRITICAL RULES:
- Use ONLY the actual items listed above. DO NOT create or invent new ones.
- Return empty lists if no items are relevant.

Return a JSON object with:
{{
  "relevant_certifications": ["list of relevant certifications in order of relevance (exact names from above, or empty list)"],
  "removed_certifications": ["list of removed certification names"],
  "relevant_activities": ["list of relevant extracurricular activities in order of relevance (or empty list)"],
  "removed_activities": ["list of removed activity names"],
  "changes_summary": "brief explanation of what was kept/removed and why"
}}
"""

        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. For certifications: be INCLUSIVE - keep anything with a reasonable connection to the job. For extracurricular: be SELECTIVE - only keep activities that add clear professional value. Use ONLY items provided - never invent new ones."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        result = safe_json_parse(response.choices[0].message.content or "", "tailor_certifications_and_extracurricular")

        if result is None:
            # Fallback: keep certifications, remove extracurricular
            print("   ⚠️ JSON parsing failed, using fallback")
            if current_certifications:
                state['working_cv']['cv']['sections']['certifications'] = current_certifications
            if 'extracurricular' in state['working_cv']['cv']['sections']:
                del state['working_cv']['cv']['sections']['extracurricular']
            state['certifications_tailored'] = True
            state['extracurricular_tailored'] = True
            return state

        # Process certifications
        if current_certifications:
            relevant_certs = result.get('relevant_certifications', [])
            removed_certs = result.get('removed_certifications', [])
            if relevant_certs:
                state['working_cv']['cv']['sections']['certifications'] = relevant_certs
            else:
                if 'certifications' in state['working_cv']['cv']['sections']:
                    del state['working_cv']['cv']['sections']['certifications']
            print(f"   Certifications kept: {len(relevant_certs)}")
            if removed_certs:
                print(f"   Certifications removed: {len(removed_certs)}")

        # Process extracurricular
        if current_extracurricular:
            relevant_activities = result.get('relevant_activities', [])
            removed_activities = result.get('removed_activities', [])
            if relevant_activities:
                state['working_cv']['cv']['sections']['extracurricular'] = relevant_activities
            else:
                if 'extracurricular' in state['working_cv']['cv']['sections']:
                    del state['working_cv']['cv']['sections']['extracurricular']
            print(f"   Activities kept: {len(relevant_activities)}")
            if removed_activities:
                print(f"   Activities removed: {len(removed_activities)}")

        changes_summary = result.get('changes_summary', 'No changes summary available')
        print(f"   Summary: {changes_summary}")

        state['certifications_tailored'] = True
        state['extracurricular_tailored'] = True
        print("✅ Certifications and extracurricular sections tailored successfully")

    except Exception as e:
        error_msg = f"Error tailoring certifications/extracurricular: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        state['certifications_tailored'] = True
        state['extracurricular_tailored'] = True

    return state
