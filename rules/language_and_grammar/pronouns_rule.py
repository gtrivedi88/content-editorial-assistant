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
        Analyzes sentences for gender-specific pronouns only.
        
        Note: Ambiguous pronoun detection is delegated to PronounAmbiguityDetector
        for more sophisticated linguistic analysis without duplication.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        sents = list(doc.sents)
        
        # LINGUISTIC ANCHOR: Gender-specific pronouns to avoid in technical writing
        gendered_pronouns = {'he', 'him', 'his', 'she', 'her'}

        for i, sent in enumerate(sents):
            for token in sent:
                # Use morphological analysis to detect gendered pronouns
                if (token.lemma_.lower() in gendered_pronouns and 
                    token.pos_ in ['PRON', 'DET'] and
                    # Additional linguistic check for gender markers
                    (not hasattr(token, 'morph') or 
                     'Gender=Masc' in str(token.morph) or 
                     'Gender=Fem' in str(token.morph))):
                    
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Gender-specific pronoun '{token.text}' used.",
                        suggestions=["Use gender-neutral language. Consider rewriting with 'they' or addressing the user directly with 'you'."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors
