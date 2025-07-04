"""
AsciiDoc Admonitions Rule
Analyzes content within AsciiDoc admonition blocks for style and clarity.
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class AdmonitionsRule(BaseStructureRule):
    """
    Checks for style issues specific to AsciiDoc admonition blocks.
    This rule is designed to work with structural AsciiDoc parsing.
    """
    def _get_rule_type(self) -> str:
        return 'admonitions'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Note: This rule would ideally receive structured AsciiDoc blocks
        # For now, it provides basic analysis for admonition-like content
        
        admonition_indicators = ['NOTE:', 'TIP:', 'IMPORTANT:', 'WARNING:', 'CAUTION:']
        
        for i, sentence in enumerate(sentences):
            # Check if sentence appears to be admonition content
            starts_with_admonition = any(sentence.strip().startswith(indicator) 
                                       for indicator in admonition_indicators)
            
            if starts_with_admonition:
                # Extract the admonition type and content
                for indicator in admonition_indicators:
                    if sentence.strip().startswith(indicator):
                        admonition_type = indicator.replace(':', '')
                        content = sentence[len(indicator):].strip()
                        
                        # Rule 1: Admonition content should not be empty
                        if not content:
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message=f"{admonition_type} admonition is empty.",
                                suggestions=[f"Provide meaningful content for the {admonition_type} admonition."],
                                severity='medium'
                            ))
                        
                        # Rule 2: WARNING and CAUTION should be specific and actionable
                        elif admonition_type in ['WARNING', 'CAUTION']:
                            if len(content.split()) < 5:
                                errors.append(self._create_error(
                                    sentence=sentence,
                                    sentence_index=i,
                                    message=f"{admonition_type} admonition should provide specific guidance.",
                                    suggestions=[f"Expand the {admonition_type} to explain what might happen and how to avoid it."],
                                    severity='medium'
                                ))
                        
                        # Rule 3: Avoid redundant phrases in admonitions
                        redundant_phrases = ['please note that', 'it is important to note', 'be aware that']
                        for phrase in redundant_phrases:
                            if phrase in content.lower():
                                errors.append(self._create_error(
                                    sentence=sentence,
                                    sentence_index=i,
                                    message=f"Avoid redundant phrase '{phrase}' in {admonition_type} admonition.",
                                    suggestions=[f"Remove '{phrase}' as the {admonition_type} already indicates importance."],
                                    severity='low'
                                ))
                        break
        
        return errors 