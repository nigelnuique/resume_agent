"""
Cross-reference validation using library-based utilities.
Provides cost-effective consistency checking between CV sections.
"""

import os
from typing import Dict, Any, List
from state import ResumeState

# Import library-based utilities
try:
    from utils.cross_reference_validator import generate_consistency_report, suggest_improvements
    from utils.date_validator import validate_experience_dates, validate_education_dates
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    print("⚠️ Cross-reference validation utilities not available")

def cross_reference_check(state: ResumeState) -> ResumeState:
    """
    Validate consistency between different sections using library-based tools.
    """
    print("🔍 Cross-referencing sections for consistency...")
    
    if not UTILS_AVAILABLE:
        print("   ⚠️ Library-based validation not available, skipping...")
        state['cross_reference_checked'] = True
        return state
    
    try:
        working_cv = state['working_cv']['cv']
        sections = working_cv.get('sections', {})
        
        # Generate comprehensive consistency report
        consistency_report = generate_consistency_report(working_cv)
        
        # Validate dates in experience and education
        date_errors = []
        if 'experience' in sections:
            exp_errors = validate_experience_dates(sections['experience'])
            date_errors.extend(exp_errors)
        
        if 'education' in sections:
            edu_errors = validate_education_dates(sections['education'])
            date_errors.extend(edu_errors)
        
        # Get improvement suggestions
        suggestions = suggest_improvements(working_cv)
        
        # Combine all validation results
        all_issues = consistency_report['all_issues'] + date_errors
        critical_issues = consistency_report['critical_issues']
        warnings = consistency_report['warnings'] + date_errors
        
        # Update state with validation results
        state['cross_reference_checked'] = True
        
        # Store validation results for potential use by other functions
        if not hasattr(state, 'validation_results'):
            state['validation_results'] = {}
        
        state['validation_results']['consistency'] = {
            'total_issues': len(all_issues),
            'critical_issues': critical_issues,
            'warnings': warnings,
            'suggestions': suggestions,
            'validation_passed': len(critical_issues) == 0
        }
        
        # Report results
        if all_issues:
            print("✅ Cross-reference checking completed with findings")
            print(f"   📊 Total issues found: {len(all_issues)}")
            print(f"   🚨 Critical issues: {len(critical_issues)}")
            print(f"   ⚠️ Warnings: {len(warnings)}")
            
            if critical_issues:
                print("   🚨 Critical Issues:")
                for issue in critical_issues[:3]:  # Show first 3
                    print(f"     - {issue}")
                if len(critical_issues) > 3:
                    print(f"     ... and {len(critical_issues) - 3} more")
            
            if warnings:
                print("   ⚠️ Warnings:")
                for warning in warnings[:3]:  # Show first 3
                    print(f"     - {warning}")
                if len(warnings) > 3:
                    print(f"     ... and {len(warnings) - 3} more")
        else:
            print("✅ Cross-reference checking completed - no issues found")
        
        # Show improvement suggestions
        if suggestions:
            print("   💡 Suggestions for improvement:")
            for suggestion in suggestions[:3]:  # Show first 3
                print(f"     - {suggestion}")
            if len(suggestions) > 3:
                print(f"     ... and {len(suggestions) - 3} more")
        
        # Technology consistency check
        if 'skills' in sections and 'experience' in sections:
            skills_count = len(sections['skills']) if sections['skills'] else 0
            exp_count = len(sections['experience']) if sections['experience'] else 0
            print(f"   📋 Section summary: {skills_count} skills, {exp_count} experience entries")
        
        return state
        
    except Exception as e:
        print(f"❌ Cross-reference checking failed: {str(e)}")
        print("   Continuing without detailed cross-reference validation...")
        state['cross_reference_checked'] = True
        return state 