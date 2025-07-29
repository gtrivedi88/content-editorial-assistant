"""
Pronouns Rule (Consolidated)
Based on IBM Style Guide topic: "Pronouns"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PronounsRule(BaseLanguageRule):
    """
    Checks for specific pronoun style issues:
    1. Use of gender-specific pronouns in technical writing.
    
    Note: Ambiguous pronoun detection is handled by the more sophisticated
    PronounAmbiguityDetector in the ambiguity module to avoid duplication.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'pronouns'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for gender-specific pronouns using robust morphological analysis.
        
        Note: Ambiguous pronoun detection is delegated to PronounAmbiguityDetector
        for more sophisticated linguistic analysis without duplication.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        sents = list(doc.sents)
        
        # LINGUISTIC ANCHOR: Gender-specific pronouns to avoid in technical writing
        gendered_pronouns = {'he', 'him', 'his', 'she', 'her', 'hers'}

        for i, sent in enumerate(sents):
            for token in sent:
                # Use robust morphological analysis for gendered pronoun detection
                lemma_lower = token.lemma_.lower()
                
                # Primary check: lemma in gendered pronouns list
                if lemma_lower in gendered_pronouns:
                    # Secondary linguistic anchors for validation
                    is_pronoun = token.pos_ in ['PRON', 'DET']
                    
                    # Enhanced morphological validation using SpaCy features
                    is_gendered = (
                        # Check morphological gender markers
                        'Gender=Masc' in str(token.morph) or 
                        'Gender=Fem' in str(token.morph) or
                        # Fallback check for common gendered forms
                        lemma_lower in {'he', 'him', 'his', 'she', 'her', 'hers'}
                    )
                    
                    # Final validation: must be a pronoun or determiner AND gendered
                    if is_pronoun and is_gendered:
                        
                        # Context-aware suggestions for better guidance
                        suggestions = [
                            "Use gender-neutral language. Consider rewriting with 'they/them' or addressing the user directly with 'you'.",
                            "Alternatively, restructure the sentence to avoid pronouns entirely."
                        ]
                        
                        # Enhanced context detection for generic usage
                        sentence_lower = sent.text.lower()
                        if any(generic_term in sentence_lower for generic_term in [
                            'user', 'developer', 'administrator', 'person', 'individual', 
                            'someone', 'anyone', 'everyone', 'customer', 'client'
                        ]):
                            # Generic context - high priority for inclusivity
                            severity = 'high'
                            message = f"Gender-specific pronoun '{token.text}' used in generic context. This excludes non-binary individuals and reduces inclusivity."
                        else:
                            # Specific context - medium priority
                            severity = 'medium' 
                            message = f"Gender-specific pronoun '{token.text}' detected. Consider using inclusive language."
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=message,
                            suggestions=suggestions,
                            severity=severity,
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors
