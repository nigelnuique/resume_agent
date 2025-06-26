"""
Utility functions for the Resume Agent system.

Available utilities:
- text_utils: Word counting and summary validation
- interactive_rendering: Interactive workflow utilities
- get_australian_english_instruction: Australian English toggle utility
"""

import os

def get_australian_english_instruction() -> str:
    """
    Get the Australian English instruction based on environment variable.
    
    Returns:
        String with instruction to use Australian English spelling if enabled
    """
    if os.getenv("AUSTRALIAN_ENGLISH", "false").lower() == "true":
        return " Use Australian English spelling (e.g., 'colour' not 'color', 'centre' not 'center', 'organisation' not 'organization')."
    return ""

# Export the function
__all__ = [
    'get_australian_english_instruction',
] 