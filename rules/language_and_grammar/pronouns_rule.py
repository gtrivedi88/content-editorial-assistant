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
    Checks for a comprehensive set of pronoun-related style issues, including:
    1. Use of gender-specific pronouns.
    2. Ambiguous pronoun references (e.g., unclear 'it' or 'this').
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'pronouns'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for gender-specific and ambiguous pronouns.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        sents = list(doc.sents)
        
        gendered_pronouns = {'he', 'him', 'his', 'she', 'her'}

        for i, sent in enumerate(sents):
            # --- Rule 1: Gender-Specific Pronouns ---
            for token in sent:
                if token.lemma_.lower() in gendered_pronouns:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Gender-specific pronoun '{token.text}' used.",
                        suggestions=["Use gender-neutral language. Consider rewriting with 'they' or addressing the user directly with 'you'."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))

            # --- Rule 2: Ambiguous Pronouns ('it', 'this', 'that') ---
            # Check for ambiguous pronouns at sentence start
            ambiguous_pronouns = ['it', 'this', 'that']
            
            for j, token in enumerate(sent):
                # Check if it's an ambiguous pronoun at the start of a sentence
                if (j == 0 and 
                    token.lemma_.lower() in ambiguous_pronouns and 
                    token.pos_ in ['PRON', 'DET']):
                    
                    # Look for potential ambiguity in previous context
                    if i > 0:
                        prev_sent = sents[i-1]
                        noun_count = sum(1 for prev_token in prev_sent if prev_token.pos_ == 'NOUN')
                        
                        # Flag if there are multiple potential referents
                        if noun_count > 1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=f"Ambiguous pronoun: '{token.text}' may have an unclear antecedent.",
                                suggestions=[f"Replace '{token.text}' with the specific noun to improve clarity."],
                                severity='medium',
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))
                            break  # Only flag one pronoun per sentence
        return errors
