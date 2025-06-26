"""AI-based section ordering using OpenAI."""

import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse


def reorder_sections(state: ResumeState) -> ResumeState:
    """Reorder CV sections with help from GPT-4."""
    print("📋 Reordering CV sections using AI...")

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        current_sections = state['working_cv']['cv'].get('sections', {})
        job_requirements = state.get('job_requirements', {})

        prompt = f"""
Reorder and refine the resume sections below so they best match the job requirements.
Return strict JSON with keys:\n- optimized_sections: the reordered sections\n- reasoning: short explanation for each section decision.

IMPORTANT: Return ONLY valid JSON. Do not include any text before or after the JSON object.
Use double quotes for all strings and escape any quotes within strings with backslash.

Resume sections: {list(current_sections.keys())}
Job requirements: {job_requirements}
"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume editor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        result = safe_json_parse(response.choices[0].message.content or "", "reorder_sections")
        if result:
            optimized_order = result.get('optimized_sections', list(current_sections.keys()))
            
            # Create new sections dictionary with reordered content
            reordered_sections = {}
            for section_name in optimized_order:
                if section_name in current_sections:
                    reordered_sections[section_name] = current_sections[section_name]
            
            # Add any sections that weren't in the optimized order
            for section_name, section_content in current_sections.items():
                if section_name not in reordered_sections:
                    reordered_sections[section_name] = section_content
            
            state['working_cv']['cv']['sections'] = reordered_sections
            reasoning = result.get('reasoning', {})
            if reasoning:
                print("   📝 Reasoning:")
                for sec, reason in reasoning.items():
                    print(f"     - {sec}: {reason}")
        state['sections_reordered'] = True
        print("✅ Section reordering completed")
        return state

    except Exception as e:
        print(f"❌ Section reordering failed: {e}")
        state['errors'].append(str(e))
        state['sections_reordered'] = True
        return state
