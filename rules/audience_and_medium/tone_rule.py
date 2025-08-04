"""
Tone Rule
Based on IBM Style Guide topic: "Tone"
"""
from typing import List, Dict, Any
from .base_audience_rule import BaseAudienceRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ToneRule(BaseAudienceRule):
    """
    Checks for violations of professional tone, such as the use of jargon,
    idioms, sports metaphors, or overly casual expressions.
    """
    def _get_rule_type(self) -> str:
        return 'tone'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)

        # Linguistic Anchor: A list of phrases that are too informal or idiomatic.
        informal_phrases = {
            "bit the dust", "elephant in the room", "hit the ground running",
            "in the ballpark", "it's not rocket science", "low-hanging fruit",
            "full-court press", "a slam dunk", "in your wheelhouse",
            "take a dump", "let there be data", "like the good samaritan"
        }

        for i, sent in enumerate(doc.sents):
            for phrase in informal_phrases:
                for match in re.finditer(r'\b' + re.escape(phrase) + r'\b', sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"The phrase '{match.group()}' is too informal or idiomatic for a professional tone.",
                        suggestions=["Rewrite the sentence using more direct and universal language."],
                        severity='medium',
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
