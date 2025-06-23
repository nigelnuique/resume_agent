"""
Grammar and tone checking using library-based utilities.
Provides cost-effective Australian English grammar checking.
"""

import os
from typing import Dict, List, Any
from state import ResumeState

# Import library-based utilities
try:
    from utils.grammar_checker import check_grammar, improve_readability, GrammarChecker
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    print("⚠️ Grammar checking utilities not available")

def grammar_tone_check(state: ResumeState) -> ResumeState:
    """
    Check grammar and tone using library-based tools (Australian English).
    """
    print("📝 Checking grammar and tone using library-based tools...")
    
    if not UTILS_AVAILABLE:
        print("   ⚠️ Library-based grammar checking not available, skipping...")
        state['grammar_checked'] = True
        return state
    
    try:
        # Initialize grammar checker
        grammar_checker = GrammarChecker()
        if not grammar_checker.tool:
            print("   ⚠️ LanguageTool not available, performing basic checks only...")
        
        working_cv = state['working_cv']
        sections = working_cv['cv']['sections']
        
        corrections_made = []
        total_errors = 0
        sections_checked = 0
        
        # Check each section
        for section_name, section_data in sections.items():
            if not section_data:
                continue
                
            print(f"   📋 Checking {section_name}...")
            section_corrections = 0
            
            # Process different section types
            if section_name == 'professional_summary':
                if isinstance(section_data, list):
                    corrected_summary = []
                    for item in section_data:
                        if isinstance(item, str):
                            result = check_grammar(item)
                            if result['available'] and result['error_count'] > 0:
                                corrected_summary.append(result['corrected_text'])
                                section_corrections += result['error_count']
                            else:
                                corrected_summary.append(item)
                    
                    if section_corrections > 0:
                        sections[section_name] = corrected_summary
                        corrections_made.append(f"{section_name}: {section_corrections} corrections")
            
            elif isinstance(section_data, list):
                # Handle experience, projects, education, etc.
                corrected_entries = []
                for entry in section_data:
                    if isinstance(entry, dict):
                        corrected_entry = entry.copy()
                        
                        # Check highlights
                        if 'highlights' in entry and isinstance(entry['highlights'], list):
                            corrected_highlights = []
                            for highlight in entry['highlights']:
                                if isinstance(highlight, str):
                                    result = check_grammar(highlight)
                                    if result['available'] and result['error_count'] > 0:
                                        corrected_highlights.append(result['corrected_text'])
                                        section_corrections += result['error_count']
                                    else:
                                        corrected_highlights.append(highlight)
                            corrected_entry['highlights'] = corrected_highlights
                        
                        # Check other text fields
                        for field in ['summary', 'description']:
                            if field in entry and isinstance(entry[field], str):
                                result = check_grammar(entry[field])
                                if result['available'] and result['error_count'] > 0:
                                    corrected_entry[field] = result['corrected_text']
                                    section_corrections += result['error_count']
                        
                        corrected_entries.append(corrected_entry)
                    else:
                        corrected_entries.append(entry)
                
                if section_corrections > 0:
                    sections[section_name] = corrected_entries
                    corrections_made.append(f"{section_name}: {section_corrections} corrections")
            
            total_errors += section_corrections
            sections_checked += 1
        
        # Generate readability report for professional summary
        readability_feedback = []
        if 'professional_summary' in sections:
            summary_text = ' '.join(sections['professional_summary']) if isinstance(sections['professional_summary'], list) else str(sections['professional_summary'])
            readability = improve_readability(summary_text)
            
            if readability['suggestions']:
                readability_feedback = readability['suggestions']
                print(f"   📊 Readability score: {readability['flesch_score']:.1f}")
                print(f"   📚 Grade level: {readability['grade_level']:.1f}")
        
        # Update state
        state['working_cv'] = working_cv
        state['grammar_checked'] = True
        
        # Report results
        if corrections_made:
            print("✅ Grammar checking completed successfully")
            print(f"   📊 Total corrections: {total_errors}")
            print(f"   📋 Sections checked: {sections_checked}")
            print("   📝 Corrections by section:")
            for correction in corrections_made:
                print(f"     - {correction}")
        else:
            print("✅ Grammar checking completed - no corrections needed")
            print(f"   📋 Sections checked: {sections_checked}")
        
        if readability_feedback:
            print("   💡 Readability suggestions:")
            for suggestion in readability_feedback:
                print(f"     - {suggestion}")
        
        return state
        
    except Exception as e:
        print(f"❌ Grammar checking failed: {str(e)}")
        print("   Continuing without grammar corrections...")
        state['grammar_checked'] = True
        return state
    
    return state 