"""
Capitalization Rule
Based on IBM Style Guide topic: "Capitalization"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class CapitalizationRule(BaseLanguageRule):
    """
    Checks for capitalization issues, such as using headline-style instead
    of the preferred sentence-style capitalization.
    """
    def _get_rule_type(self) -> str:
        return 'capitalization'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Context-aware analysis: Only check capitalization for headings and titles
        # No more heuristics - we KNOW what type of content we're analyzing
        if context and context.get('block_type') == 'heading':
            # We KNOW this is a heading, so check for proper sentence-style capitalization
            heading_text = text.strip()
            words = heading_text.split()
            
            if len(words) > 1:  # Skip single-word headings
                title_cased_words = [word for word in words[1:] if word.istitle()]
                # Check if more than a third of words (excluding the first) are capitalized
                if len(title_cased_words) > len(words) / 3:
                    errors.append(self._create_error(
                        sentence=heading_text,
                        sentence_index=0,
                        message="Heading uses incorrect headline-style capitalization.",
                        suggestions=["Use sentence-style capitalization for headings (capitalize only the first word and proper nouns)."],
                        severity='medium'
                    ))
        
        # For regular text content, check for other capitalization issues
        elif context and context.get('block_type') in ['paragraph', 'list_item']:
            # Context-aware analysis for paragraph/list content
            for i, sentence in enumerate(sentences):
                # Check for improper capitalization of common words
                if nlp:
                    doc = nlp(sentence)
                    for token in doc:
                        # Check for improperly capitalized common words
                        if (token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV'] and 
                            token.is_title and 
                            not token.is_sent_start and
                            not any(ent.start <= token.i < ent.end for ent in doc.ents)):
                            
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message=f"Unnecessary capitalization of '{token.text}'.",
                                suggestions=[f"Use lowercase '{token.text.lower()}' unless it's a proper noun."],
                                severity='low'
                            ))
        
        return errors
