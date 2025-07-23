"""
Conjunctions Rule
Based on IBM Style Guide topic: "Conjunctions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ConjunctionsRule(BaseLanguageRule):
    """
    Checks for incorrect usage of subordinating conjunctions like 'while' and 'since'.
    """
    def _get_rule_type(self) -> str:
        return 'conjunctions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.dep_ == 'mark' and token.lemma_.lower() in ['while', 'since']:
                    main_verb = token.head
                    is_time_related = any(ent.label_ == 'TIME' for ent in main_verb.subtree.ents)
                    
                    if not is_time_related:
                        suggestion = ""
                        if token.lemma_.lower() == 'while':
                            suggestion = "For contrast, use 'although' or 'whereas'."
                        elif token.lemma_.lower() == 'since':
                            suggestion = "For causation, use 'because'."
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=f"The conjunction '{token.text}' may be used incorrectly.",
                            suggestions=[suggestion],
                            severity='medium',
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors
