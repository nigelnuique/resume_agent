"""
AI-based cross-reference validation for resume sections.
Uses OpenAI to check consistency across the CV.
"""

from typing import Dict, Any
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse


def cross_reference_check(state: ResumeState) -> ResumeState:
    """Run an AI powered cross-reference check on the working CV."""
    print("🔍 Performing AI-based cross-reference check...")

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        sections: Dict[str, Any] = state['working_cv']['cv']['sections']

        prompt = f"""
Check this resume for internal consistency and alignment with the job requirements.
Return JSON with the keys 'corrected_sections' and 'issues_found'.
Resume sections: {sections}
Job requirements: {state.get('job_requirements', {})}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume editor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        result = safe_json_parse(response.choices[0].message.content, "cross_reference_check")
        if result:
            if isinstance(result.get('corrected_sections'), dict):
                sections.update(result['corrected_sections'])
            if isinstance(result.get('issues_found'), list):
                state['warnings'].extend(result['issues_found'])

        state['cross_reference_checked'] = True
        print("✅ AI cross-reference check completed")
    except Exception as e:
        error_msg = f"Error in cross-reference check: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)

    return state

