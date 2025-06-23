"""
Rule-based section ordering and optimization.
Provides cost-effective alternative to LLM-based section reordering.
"""

import os
from typing import Dict, Any, List
from state import ResumeState

# Import library-based utilities
try:
    from utils.section_optimizer import optimize_section_structure, validate_section_optimization
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    print("⚠️ Section optimization utilities not available")

def reorder_sections(state: ResumeState) -> ResumeState:
    """
    Reorder and optimize CV sections using rule-based logic.
    """
    print("📋 Optimizing CV section structure using rule-based logic...")
    
    if not UTILS_AVAILABLE:
        print("   ⚠️ Rule-based optimization not available, skipping...")
        state['sections_reordered'] = True
        return state
    
    try:
        working_cv = state['working_cv']['cv']
        current_sections = working_cv.get('sections', {})
        job_requirements = state.get('job_requirements', {})
        
        # Optimize section structure
        optimization_result = optimize_section_structure(current_sections, job_requirements)
        
        # Validate optimization
        warnings = validate_section_optimization(current_sections, optimization_result['optimized_sections'])
        
        # Apply optimization
        working_cv['sections'] = optimization_result['optimized_sections']
        
        # Update state
        state['working_cv']['cv'] = working_cv
        state['sections_reordered'] = True
        
        # Report results
        kept_sections = optimization_result['kept_sections']
        removed_sections = optimization_result['removed_sections']
        reasoning = optimization_result['reasoning']
        
        print("✅ Section optimization completed")
        print(f"   📊 Sections kept: {' → '.join(kept_sections)}")
        
        if removed_sections:
            print(f"   🗑️ Sections removed: {', '.join(removed_sections)}")
        
        # Show reasoning for key decisions
        print("   📝 Reasoning:")
        for section, reason in reasoning.items():
            if section in kept_sections:
                print(f"     ✅ {section}: {reason}")
            elif section in removed_sections:
                print(f"     ❌ {section}: {reason}")
        
        # Show any warnings
        if warnings:
            print("   ⚠️ Optimization warnings:")
            for warning in warnings:
                print(f"     - {warning}")
        
        # Summary statistics
        original_count = len([s for s in current_sections.values() if s])
        optimized_count = len([s for s in optimization_result['optimized_sections'].values() if s])
        print(f"   📈 Section count: {original_count} → {optimized_count}")
        
        return state
        
    except Exception as e:
        print(f"❌ Section optimization failed: {str(e)}")
        print("   Continuing with original section order...")
        state['sections_reordered'] = True
        return state
