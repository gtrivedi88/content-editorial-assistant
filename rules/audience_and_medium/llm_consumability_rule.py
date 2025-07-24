"""
LLM Consumability Rule
Based on IBM Style Guide topic: "LLM consumability"
"""
from typing import List, Dict, Any
from .base_audience_rule import BaseAudienceRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class LLMConsumabilityRule(BaseAudienceRule):
    """
    Checks for content patterns that are difficult for Large Language Models (LLMs)
    to process effectively, such as overly short topics or complex structures
    like accordions.
    """
    def _get_rule_type(self) -> str:
        return 'llm_consumability'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)

        for i, sent in enumerate(doc.sents):
            # Guideline: Avoid tiny topics (approximated by checking for very short sentences).
            if len(sent) < 5:
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Very short sentences or topics can be missed by LLMs. Ensure topics are comprehensive.",
                    suggestions=["Consider adding more content or combining this information with another related topic."],
                    severity='low',
                    span=(sent.start_char, sent.end_char),
                    flagged_text=sent.text
                ))

        # Guideline: Check for text indicating complex structures that LLMs struggle with.
        accordion_phrases = ["in the accordion", "expand the accordion", "within the collapsed section"]
        
        for i, sent in enumerate(doc.sents):
            for phrase in accordion_phrases:
                for match in re.finditer(r'\b' + re.escape(phrase) + r'\b', sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message="Content inside accordions may not be processed correctly by LLMs.",
                        suggestions=["Consider presenting this information in a standard paragraph or a separate section if it is critical."],
                        severity='medium',
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
