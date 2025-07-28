"""
Semicolons Rule (Accurate)
Based on IBM Style Guide topic: "Semicolons"
"""
import re
from typing import List, Dict, Any
from ..base_rule import BaseRule

class SemicolonsRule(BaseRule):
    """
    Checks for the use of semicolons and advises against them in technical writing.
    """
    def _get_rule_type(self) -> str:
        return 'semicolons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        for i, sent_text in enumerate(sentences):
            # PRIORITY 1 FIX: This rule checks if a semicolon character is present,
            # but excludes semicolons that are part of HTML entities (e.g., &#8217;)
            # This prevents false positives from smart quotes and other entities
            
            # First check if there are any semicolons at all
            if ';' in sent_text:
                # Remove HTML entities (both named and numeric) to avoid false positives
                # Pattern matches: &#8217; &amp; &lt; &gt; &quot; etc.
                text_without_entities = re.sub(r'&[a-zA-Z0-9#]+;', '', sent_text)
                
                # Only flag if semicolons remain after removing HTML entities
                if ';' in text_without_entities:
                    errors.append(self._create_error(
                        sentence=sent_text,
                        sentence_index=i,
                        message="Avoid semicolons in technical writing to improve clarity.",
                        suggestions=["Consider rewriting the sentence as two separate, shorter sentences."],
                        severity='low'
                    ))
        return errors
