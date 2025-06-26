"""
Lightweight text utilities for word counting and summary validation.
Provides simple, fast text analysis without external dependencies.
"""

from typing import Dict, Any, List

def count_words_sentences(text: str) -> Dict[str, int]:
    """
    Count words and sentences in text using simple, reliable methods.
    """
    if not text or not isinstance(text, str):
        return {'words': 0, 'sentences': 0}
    
    # Count words (split by whitespace, filter empty strings)
    words = len([word for word in text.split() if word.strip()])
    
    # Count sentences using basic punctuation checks without regex
    cleaned = text.replace('?', '.').replace('!', '.')
    sentences = len([s for s in cleaned.split('.') if s.strip()])
    
    return {'words': words, 'sentences': sentences}

def validate_summary_constraints(text_list: List[str], min_words: int = 40, max_words: int = 70, 
                               min_sentences: int = 2, max_sentences: int = 4) -> Dict[str, Any]:
    """
    Validate professional summary against word and sentence constraints.
    """
    if not text_list:
        return {
            'valid': False,
            'words': 0,
            'sentences': 0,
            'issues': ['Summary is empty']
        }
    
    # Join all summary points
    full_text = ' '.join(text_list)
    counts = count_words_sentences(full_text)
    
    issues = []
    if counts['words'] < min_words:
        issues.append(f"Too few words: {counts['words']} (minimum: {min_words})")
    elif counts['words'] > max_words:
        issues.append(f"Too many words: {counts['words']} (maximum: {max_words})")
    
    if counts['sentences'] < min_sentences:
        issues.append(f"Too few sentences: {counts['sentences']} (minimum: {min_sentences})")
    elif counts['sentences'] > max_sentences:
        issues.append(f"Too many sentences: {counts['sentences']} (maximum: {max_sentences})")
    
    return {
        'valid': len(issues) == 0,
        'words': counts['words'],
        'sentences': counts['sentences'],
        'issues': issues
    }

def get_text_statistics(text: str) -> Dict[str, Any]:
    """
    Get basic text statistics for reporting purposes.
    """
    if not text:
        return {
            'words': 0,
            'sentences': 0,
            'characters': 0,
            'avg_words_per_sentence': 0
        }
    
    counts = count_words_sentences(text)
    characters = len(text.strip())
    avg_words_per_sentence = counts['words'] / counts['sentences'] if counts['sentences'] > 0 else 0
    
    return {
        'words': counts['words'],
        'sentences': counts['sentences'],
        'characters': characters,
        'avg_words_per_sentence': round(avg_words_per_sentence, 1)
    } 