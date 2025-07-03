"""
Hyphens Rule
Based on IBM Style Guide topics: "Hyphens" and "Prefixes"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class HyphensRule(BasePunctuationRule):
    """
    Checks for incorrect hyphenation with common prefixes.
    """
    def _get_rule_type(self) -> str:
        return 'hyphens'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        
        closed_prefixes = {"pre", "post", "multi", "non", "inter", "intra", "re"}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.text == '-':
                    if token.i > 0 and token.i < len(doc) - 1:
                        prefix_token = doc[token.i - 1]
                        word_token = doc[token.i + 1]
                        
                        if prefix_token.lemma_ in closed_prefixes:
                            if prefix_token.lemma_ == "re" and word_token.lemma_.startswith("e"):
                                continue
                            if prefix_token.lemma_ == "multi" and word_token.lemma_ in ["agent", "core", "instance"]:
                                continue

                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message=f"Incorrect hyphenation with prefix '{prefix_token.text}'.",
                                suggestions=[f"Consider removing the hyphen to form '{prefix_token.text}{word_token.text}'."],
                                severity='medium'
                            ))
        return errors