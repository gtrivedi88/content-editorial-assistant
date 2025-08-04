"""
Global Audiences Rule
Based on IBM Style Guide topic: "Global audiences"
"""
from typing import List, Dict, Any
from .base_audience_rule import BaseAudienceRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class GlobalAudiencesRule(BaseAudienceRule):
    """
    Checks for constructs that are difficult for a global audience to understand,
    such as negative constructions and overly long sentences.
    """
    def _get_rule_type(self) -> str:
        return 'global_audiences'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            # --- Rule 1: Negative Constructions ---
            for token in sent:
                # Linguistic Anchor: Find a negation token ('not', 'n't').
                if token.dep_ == 'neg':
                    head_verb = token.head
                    # Check if the verb it modifies has an adjectival complement (acomp) like "different".
                    for child in head_verb.children:
                        if child.dep_ == 'acomp' and child.lemma_ in ['different', 'unusual', 'dissimilar']:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message="Avoid negative constructions. State the condition positively.",
                                suggestions=[f"Rewrite '{token.text} {child.text}' to a positive equivalent (e.g., 'similar')."],
                                text=text,  # Enhanced: Pass full text for better confidence analysis
                                context=context,  # Enhanced: Pass context for domain-specific validation
                                severity='medium',
                                span=(token.idx, child.idx + len(child.text)),
                                flagged_text=f"{token.text} {child.text}"
                            ))

            # --- Rule 2: Sentence Length ---
            if len(sent) > 32:
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Sentence is too long for a global audience. Aim for 32 words or fewer.",
                    suggestions=["Break the long sentence into shorter, simpler sentences."],
                    severity='low',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(sent.start_char, sent.end_char),
                    flagged_text=sent.text
                ))
        return errors
