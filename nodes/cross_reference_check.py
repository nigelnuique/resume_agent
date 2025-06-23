from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def cross_reference_check(state: ResumeState) -> ResumeState:
    """
    Cross-reference check to ensure consistency between sections.
    """
    print("🔍 Performing cross-reference consistency check...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        working_cv = state['working_cv']['cv']['sections']
        
        prompt = f"""
        Perform a cross-reference consistency check on this CV to identify any unsupported claims or inconsistencies.

        CV Sections:
        Professional Summary: {working_cv.get('professional_summary', [])}
        Experience: {working_cv.get('experience', [])}
        Projects: {working_cv.get('projects', [])}
        Education: {working_cv.get('education', [])}
        Skills: {working_cv.get('skills', [])}

        Check for:
        1. Skills mentioned in summary that aren't supported by experience/projects/education
        2. Technologies claimed in skills that aren't demonstrated in experience/projects
        3. Achievements in summary that aren't backed by specific examples in experience/projects
        4. Inconsistent terminology across sections
        5. Years of experience claims that don't match actual experience timeline

        Return ONLY a properly formatted JSON object (no additional text) with:
        - "inconsistencies": list of specific inconsistencies found
        - "unsupported_claims": list of claims that need supporting evidence
        - "recommendations": list of specific fixes to make
        - "severity": "high", "medium", or "low" based on impact on credibility
        
        Example format:
        {
            "inconsistencies": [],
            "unsupported_claims": [],
            "recommendations": [],
            "severity": "low"
        }
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume reviewer. Identify inconsistencies and unsupported claims that could hurt credibility."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        result = safe_json_parse(response.choices[0].message.content, "cross_reference_check")
        
        if result is None:
            # Provide fallback behavior - assume no critical issues
            fallback_data = {
                'inconsistencies': [],
                'unsupported_claims': [],
                'recommendations': ['Cross-reference check could not be completed - manual review recommended'],
                'severity': 'low'
            }
            result = create_fallback_response("cross_reference_check", fallback_data)
        
        inconsistencies = result.get('inconsistencies', [])
        unsupported_claims = result.get('unsupported_claims', [])
        recommendations = result.get('recommendations', [])
        severity = result.get('severity', 'low')
        
        # Add to warnings or errors based on severity
        if severity == 'high':
            state['errors'].extend(inconsistencies + unsupported_claims)
        else:
            state['warnings'].extend(inconsistencies + unsupported_claims)
        
        state['cross_reference_checked'] = True
        
        print("✅ Cross-reference check completed")
        print(f"   Severity: {severity}")
        print(f"   Found {len(inconsistencies)} inconsistencies")
        print(f"   Found {len(unsupported_claims)} unsupported claims")
        
        if recommendations:
            print("   Recommendations:")
            for rec in recommendations[:3]:  # Show first 3
                print(f"   - {rec}")
        
    except Exception as e:
        error_msg = f"Error in cross-reference check: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state 