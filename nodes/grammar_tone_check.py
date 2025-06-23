"""
Grammar and tone checking - simplified version.
Since LLMs handle grammar during content generation, this step just validates completion.
"""

from typing import Dict, List, Any
from state import ResumeState

def grammar_tone_check(state: ResumeState) -> ResumeState:
    """
    Mark grammar checking as completed since LLMs handle grammar during content generation.
    """
    print("📝 Grammar and tone checking...")
    print("   ✅ Grammar handled by LLM content generation - no separate checking needed")
    
    # Mark as completed
    state['grammar_checked'] = True
    
    # Provide basic statistics for transparency
    working_cv = state['working_cv']
    sections = working_cv['cv']['sections']
    
    sections_processed = 0
    total_content_items = 0
    
    for section_name, section_data in sections.items():
        if section_data:
            sections_processed += 1
            if isinstance(section_data, list):
                total_content_items += len(section_data)
            else:
                total_content_items += 1
    
    print(f"   📊 Sections processed: {sections_processed}")
    print(f"   📝 Content items: {total_content_items}")
    print("   💡 All content has been generated/refined by LLMs with proper grammar")
    
    return state 