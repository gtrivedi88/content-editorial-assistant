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

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Context-aware analysis: Only analyze if we know this is an admonition block
        if not context or context.get('block_type') != 'admonition':
            return errors  # Skip analysis if not an admonition block
            
        # Get admonition type from context (set by asciidoctor parsing)
        admonition_type = context.get('admonition_type', 'NOTE').upper()
        
        # Combine all sentences to get full admonition content
        full_content = ' '.join(sentences).strip()
        
        # Rule 1: Admonition content should not be empty
        if not full_content:
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message=f"{admonition_type} admonition is empty.",
                suggestions=[f"Provide meaningful content for the {admonition_type} admonition."],
                severity='medium'
            ))
            return errors
        
        # Rule 2: WARNING and CAUTION should be specific and actionable
        if admonition_type in ['WARNING', 'CAUTION']:
            if len(full_content.split()) < 5:
                errors.append(self._create_error(
                    sentence=full_content,
                    sentence_index=0,
                    message=f"{admonition_type} admonition should provide specific guidance.",
                    suggestions=[f"Expand the {admonition_type} to explain what might happen and how to avoid it."],
                    severity='medium'
                ))
        
        # Rule 3: Avoid redundant phrases in admonitions
        redundant_phrases = ['please note that', 'it is important to note', 'be aware that']
        for i, sentence in enumerate(sentences):
            for phrase in redundant_phrases:
                if phrase in sentence.lower():
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Avoid redundant phrase '{phrase}' in {admonition_type} admonition.",
                        suggestions=[f"Remove '{phrase}' as the {admonition_type} already indicates importance."],
                        severity='low'
                    ))
        
        return errors 