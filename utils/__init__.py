"""
Resume Agent Utilities Package

This package contains library-based alternatives to LLM-powered functions,
providing cost-effective and reliable utilities for resume processing.

Modules:
- text_utils: Lightweight text analysis and validation
- date_validator: Date parsing, validation, and consistency checking
- section_optimizer: Rule-based section ordering and optimization
"""

__version__ = "1.0.0"

# Import main utility functions for easy access
try:
    from .text_utils import count_words_sentences, validate_summary_constraints, get_text_statistics
    from .date_validator import validate_experience_dates, validate_education_dates, calculate_total_experience
    from .section_optimizer import optimize_section_structure, validate_section_optimization
    
    __all__ = [
        'count_words_sentences',
        'validate_summary_constraints', 
        'get_text_statistics',
        'validate_experience_dates',
        'validate_education_dates',
        'calculate_total_experience',
        'optimize_section_structure',
        'validate_section_optimization'
    ]
    
except ImportError as e:
    print(f"⚠️ Some utilities may not be available due to missing dependencies: {e}")
    __all__ = [] 