"""
Hyphens Rule
Based on IBM Style Guide topics: "Hyphens" and "Prefixes"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class HyphensRule(BasePunctuationRule):
    """
    Checks for incorrect hyphenation, focusing on common prefixes that
    the IBM Style Guide specifies should be "closed" (unhyphenated).
    This rule uses linguistic anchors for prefixes and handles documented
    exceptions to reduce false positives.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'hyphens'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for incorrect hyphenation with common prefixes.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        # Linguistic Anchor: Common prefixes that should be closed (not hyphenated).
        closed_prefixes = {"pre", "post", "multi", "non", "inter", "intra", "re"}

        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.text == '-':
                    if token.i > sent.start and token.i < sent.end - 1:
                        prefix_token = sent.doc[token.i - 1]
                        word_token = sent.doc[token.i + 1]
                        
                        if prefix_token.lemma_ in closed_prefixes:
                            # --- Context-Aware Edge Case Handling ---
                            # Exception 1: 're' before 'e' (e.g., re-enter).
                            if prefix_token.lemma_ == "re" and word_token.lemma_.startswith("e"):
                                continue 
                            
                            # Exception 2: 'multi' has specific exceptions (e.g., multi-agent).
                            if prefix_token.lemma_ == "multi" and word_token.lemma_ in ["agent", "core", "instance"]:
                                continue

                            flagged_text = f"{prefix_token.text}-{word_token.text}"
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=f"Incorrect hyphenation with prefix '{prefix_token.text}'. IBM Style prefers closed prefixes.",
                                suggestions=[f"Consider removing the hyphen to form '{prefix_token.text}{word_token.text}'."],
                                severity='medium',
                                text=text,  # Enhanced: Pass full text for better confidence analysis
                                context=context,  # Enhanced: Pass context for domain-specific validation
                                span=(prefix_token.idx, word_token.idx + len(word_token.text)),
                                flagged_text=flagged_text
                            ))
        return errors
