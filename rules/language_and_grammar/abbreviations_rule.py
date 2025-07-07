"""
Abbreviations Rule (Enhanced)
Based on IBM Style Guide topic: "Abbreviations"
"""
import re
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class AbbreviationsRule(BaseLanguageRule):
    """
    Checks for the use of informal or Latin abbreviations in general text,
    using context to avoid flagging them in technical contexts like filenames.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'abbreviations'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for discouraged abbreviations.
        """
        errors = []
        
        # Linguistic Anchor: A dictionary of discouraged abbreviations and their replacements.
        abbreviations_map = {
            # Latin
            r'\be\.g\.': 'for example',
            r'\bi\.e\.': 'that is',
            r'\betc\.': 'and so on',
            # Informal English
            r'\binfo\b': 'information',
            r'\badmin\b': 'administrator',
            r'\bapp\b': 'application',
            r'\bconfig\b': 'configuration',
        }

        for i, sentence in enumerate(sentences):
            for pattern, replacement in abbreviations_map.items():
                # Find all occurrences of the pattern in the sentence.
                for match in re.finditer(pattern, sentence, re.IGNORECASE):
                    abbrev = match.group(0)
                    # Use a helper to check if the context is technical.
                    if not self._is_technical_context(sentence, match.start()):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Avoid using the abbreviation '{abbrev}'.",
                            suggestions=[f"Use '{replacement}' instead for clarity."],
                            severity='medium'
                        ))
        return errors
    
    def _is_technical_context(self, sentence: str, position: int) -> bool:
        """
        A helper function to check if an abbreviation appears in a technical
        context where it might be legitimate (e.g., part of a filename).
        """
        # Look for common technical characters or patterns near the abbreviation.
        context_window = sentence[max(0, position - 15):position + 25].lower()
        
        technical_indicators = [
            '.', '/', '\\', '_', '-', ':', '=', 
            'http', 'www', '.com', 'git', 'api'
        ]
        
        return any(indicator in context_window for indicator in technical_indicators)
