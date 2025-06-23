"""
Grammar checking utilities using language-tool-python for Australian English.
Provides cost-effective alternative to LLM-based grammar checking.
"""

from typing import Dict, Any, List, Tuple
import re
import textstat

try:
    import language_tool_python
    LANGUAGE_TOOL_AVAILABLE = True
except ImportError:
    LANGUAGE_TOOL_AVAILABLE = False
    print("⚠️ language-tool-python not available. Install with: pip install language-tool-python")

class GrammarChecker:
    """Australian English grammar checker using LanguageTool."""
    
    def __init__(self):
        self.tool = None
        if LANGUAGE_TOOL_AVAILABLE:
            try:
                # Use Australian English variant
                self.tool = language_tool_python.LanguageTool('en-AU')
            except Exception as e:
                print(f"⚠️ Could not initialize LanguageTool: {e}")
                self.tool = None
    
    def check_text(self, text: str) -> Dict[str, Any]:
        """
        Check grammar and readability of text.
        Returns corrections and statistics.
        """
        if not self.tool or not text:
            return {
                'corrections': [],
                'corrected_text': text,
                'error_count': 0,
                'readability_score': 0,
                'available': False
            }
        
        try:
            # Check grammar
            matches = self.tool.check(text)
            
            corrections = []
            for match in matches:
                corrections.append({
                    'error_type': match.ruleId,
                    'message': match.message,
                    'suggestions': match.replacements[:3],  # Top 3 suggestions
                    'position': (match.offset, match.offset + match.errorLength),
                    'severity': 'error' if match.ruleId.startswith('GRAMMAR') else 'style'
                })
            
            # Apply corrections
            corrected_text = language_tool_python.utils.correct(text, matches)
            
            # Calculate readability
            readability_score = textstat.flesch_reading_ease(text)
            
            return {
                'corrections': corrections,
                'corrected_text': corrected_text,
                'error_count': len(matches),
                'readability_score': readability_score,
                'available': True
            }
            
        except Exception as e:
            print(f"⚠️ Grammar check failed: {e}")
            return {
                'corrections': [],
                'corrected_text': text,
                'error_count': 0,
                'readability_score': 0,
                'available': False
            }

def check_grammar(text: str) -> Dict[str, Any]:
    """
    Convenience function for grammar checking.
    """
    checker = GrammarChecker()
    return checker.check_text(text)

def count_words_sentences(text: str) -> Dict[str, int]:
    """
    Count words and sentences in text using simple, reliable methods.
    """
    if not text or not isinstance(text, str):
        return {'words': 0, 'sentences': 0}
    
    # Count words (split by whitespace, filter empty strings)
    words = len([word for word in text.split() if word.strip()])
    
    # Count sentences (split by sentence-ending punctuation)
    sentences = len([s for s in re.split(r'[.!?]+', text) if s.strip()])
    
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

def improve_readability(text: str) -> Dict[str, Any]:
    """
    Suggest readability improvements using textstat.
    """
    if not text:
        return {'suggestions': [], 'score': 0}
    
    # Calculate various readability metrics
    flesch_score = textstat.flesch_reading_ease(text)
    flesch_grade = textstat.flesch_kincaid_grade(text)
    avg_sentence_length = textstat.avg_sentence_length(text)
    
    suggestions = []
    
    # Readability suggestions
    if flesch_score < 60:  # Difficult to read
        suggestions.append("Consider using shorter sentences and simpler words")
    
    if avg_sentence_length > 20:
        suggestions.append(f"Average sentence length is {avg_sentence_length:.1f} words - consider breaking up long sentences")
    
    if flesch_grade > 12:
        suggestions.append("Text may be too complex for general readability")
    
    return {
        'flesch_score': flesch_score,
        'grade_level': flesch_grade,
        'avg_sentence_length': avg_sentence_length,
        'suggestions': suggestions
    } 