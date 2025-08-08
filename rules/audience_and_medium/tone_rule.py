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
        """
        Evidence-based analysis for professional tone. Flags idioms, slang,
        and overly casual expressions with nuanced evidence considering
        linguistic, structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)

        # Linguistic Anchor: phrases that are too informal or idiomatic.
        informal_phrases = {
            "bit the dust", "elephant in the room", "hit the ground running",
            "in the ballpark", "it's not rocket science", "low-hanging fruit",
            "full-court press", "a slam dunk", "in your wheelhouse",
            "take a dump", "let there be data", "like the good samaritan",
            "nail it", "no-brainer", "game changer", "move the needle"
        }

        for i, sent in enumerate(doc.sents):
            for phrase in informal_phrases:
                for match in re.finditer(r'\b' + re.escape(phrase) + r'\b', sent.text, re.IGNORECASE):
                    ev = self._calculate_tone_evidence(phrase, sent, text, context or {})
                    if ev > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_tone_message(match.group(0), ev, context or {}),
                            suggestions=self._generate_smart_tone_suggestions(match.group(0), ev, sent, context or {}),
                            severity='low' if ev < 0.7 else 'medium',
                            text=text,
                            context=context,
                            evidence_score=ev,
                            span=(sent.start_char + match.start(), sent.start_char + match.end()),
                            flagged_text=match.group(0)
                        ))
        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_tone_evidence(self, phrase: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that a phrase violates professional tone."""
        evidence: float = 0.6  # base for idiomatic/informal phrase

        # Linguistic clues
        evidence = self._apply_linguistic_clues_tone(evidence, phrase, sentence)

        # Structural clues
        evidence = self._apply_structural_clues_tone(evidence, context)

        # Semantic clues
        evidence = self._apply_semantic_clues_tone(evidence, phrase, text, context)

        # Feedback clues
        evidence = self._apply_feedback_clues_tone(evidence, phrase, context)

        return max(0.0, min(1.0, evidence))

    # === CLUE APPLICATION METHODS ===

    def _apply_linguistic_clues_tone(self, ev: float, phrase: str, sentence) -> float:
        sent_text = sentence.text
        sent_lower = sent_text.lower()

        # Quotes or reported speech → reduce impact
        if '"' in sent_text or "'" in sent_text:
            ev -= 0.1

        # Exclamation points increase casualness
        if sent_text.strip().endswith('!'):
            ev += 0.1

        # First/second person pronouns can be conversational; slight reduction
        if any(t.lemma_.lower() in {'i', 'we', 'you'} for t in sentence):
            ev -= 0.05

        # Long sentence amplifies confusion potential
        token_count = len([t for t in sentence if not t.is_space])
        if token_count > 25:
            ev += 0.05

        return ev

    def _apply_structural_clues_tone(self, ev: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return ev - 0.7
        if block_type == 'inline_code':
            return ev - 0.5
        if block_type in {'table_cell', 'table_header'}:
            ev -= 0.05
        if block_type in {'heading', 'title'}:
            ev -= 0.05
        return ev

    def _apply_semantic_clues_tone(self, ev: float, phrase: str, text: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # Stricter in formal/technical contexts
        if content_type in {'technical', 'api', 'procedural'}:
            ev += 0.1
        if content_type in {'legal', 'academic'}:
            ev += 0.15
        if content_type in {'marketing', 'narrative'}:
            ev -= 0.05

        if domain in {'legal', 'finance', 'medical'}:
            ev += 0.1

        if audience in {'beginner', 'general'}:
            ev += 0.05

        return ev

    def _apply_feedback_clues_tone(self, ev: float, phrase: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_tone()
        p = phrase.lower()
        if p in patterns.get('accepted_phrases', set()):
            ev -= 0.2
        if p in patterns.get('flagged_phrases', set()):
            ev += 0.1

        ctype = (context or {}).get('content_type', 'general')
        pc = patterns.get(f'{ctype}_patterns', {})
        if p in pc.get('accepted', set()):
            ev -= 0.1
        if p in pc.get('flagged', set()):
            ev += 0.1
        return ev

    def _get_cached_feedback_patterns_tone(self) -> Dict[str, Any]:
        return {
            'accepted_phrases': set(),
            'flagged_phrases': {'take a dump', "it's not rocket science"},
            'technical_patterns': {
                'accepted': set(),
                'flagged': {"low-hanging fruit", "move the needle"}
            },
            'marketing_patterns': {
                'accepted': {"game changer"},
                'flagged': {"take a dump"}
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_tone_message(self, phrase: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.85:
            return f"The phrase '{phrase}' is too informal/idiomatic for a professional tone."
        if ev > 0.6:
            return f"Consider avoiding the idiom '{phrase}' to maintain a professional tone."
        return f"A more direct, universal alternative to '{phrase}' can improve tone."

    def _generate_smart_tone_suggestions(self, phrase: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append("Replace the idiom with a clear, literal statement of the action or result.")
        suggestions.append("Remove colloquialisms and use direct, professional language.")
        if sentence.text.strip().endswith('!'):
            suggestions.append("Avoid exclamation points in professional documentation.")
        return suggestions[:3]
