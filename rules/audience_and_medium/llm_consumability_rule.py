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
        """
        Evidence-based analysis for LLM consumability.
        Computes nuanced evidence for:
          - Very short topics/sentences likely to be ignored by LLMs
          - References to complex UI structures like accordions/collapsed sections
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        # ENTERPRISE CONTEXT INTELLIGENCE: Check if completeness rules should apply
        content_classification = self._get_content_classification(text, context, nlp)
        should_apply = self._should_apply_rule(self._get_rule_category(), content_classification)
        if not should_apply:
            return errors

        doc = nlp(text)

        # Short-topic consumability
        for i, sent in enumerate(doc.sents):
            ev_short = self._calculate_short_topic_evidence(sent, text, context or {})
            if ev_short > 0.1:
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message=self._get_contextual_short_topic_message(len([t for t in sent if not t.is_space]), ev_short, context or {}),
                    suggestions=self._generate_smart_short_topic_suggestions(sent, ev_short, context or {}),
                    severity='low' if ev_short < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=ev_short,
                    span=(sent.start_char, sent.end_char),
                    flagged_text=sent.text
                ))

        # Accordion/complex-structure references
        accordion_phrases = [
            "in the accordion", "expand the accordion", "within the collapsed section",
            "collapsed section", "expand section", "collapsed content"
        ]
        for i, sent in enumerate(doc.sents):
            for phrase in accordion_phrases:
                for match in re.finditer(r'\b' + re.escape(phrase) + r'\b', sent.text, re.IGNORECASE):
                    ev_acc = self._calculate_accordion_evidence(phrase, sent, text, context or {})
                    if ev_acc > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_accordion_message(phrase, ev_acc, context or {}),
                            suggestions=self._generate_smart_accordion_suggestions(phrase, ev_acc, context or {}),
                            text=text,
                            context=context,
                            evidence_score=ev_acc,
                            severity='medium' if ev_acc > 0.6 else 'low',
                            span=(sent.start_char + match.start(), sent.start_char + match.end()),
                            flagged_text=match.group(0)
                        ))

        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_short_topic_evidence(self, sentence, text: str, context: Dict[str, Any]) -> float:
        tokens = [t for t in sentence if not t.is_space]
        length = len(tokens)

        # Base evidence rises steeply for very short sentences
        if length >= 12:
            base = 0.0
        elif length >= 8:
            base = 0.2
        elif length >= 5:
            base = 0.45
        else:
            base = 0.75

        evidence: float = base

        # Linguistic clues: missing verb, just a fragment/title
        has_verb = any(getattr(t, 'pos_', '') == 'VERB' for t in tokens)
        if not has_verb and length <= 7:
            evidence += 0.1

        # Punctuation-only cues (e.g., ends with ':' or no punctuation)
        if sentence.text.strip().endswith(':'):
            evidence += 0.05
        if not any(t.text in '.!?' for t in sentence):
            evidence += 0.05

        # Structural clues
        evidence = self._apply_structural_clues_llm(evidence, context)

        # Semantic clues
        evidence = self._apply_semantic_clues_llm(evidence, context)

        # Feedback clues
        evidence = self._apply_feedback_clues_llm(evidence, sentence, context)

        return max(0.0, min(1.0, evidence))

    def _calculate_accordion_evidence(self, phrase: str, sentence, text: str, context: Dict[str, Any]) -> float:
        # Base evidence that accordion/collapsed content harms consumability
        evidence: float = 0.6

        # If phrase suggests critical information hidden, increase
        lower = sentence.text.lower()
        if any(k in lower for k in ['important', 'note', 'warning', 'steps', 'requirements']):
            evidence += 0.1

        # Structural: some blocks reduce severity (already a callout)
        evidence = self._apply_structural_clues_llm(evidence, context)

        # Semantic: more critical in technical/how-to/api docs
        evidence = self._apply_semantic_clues_llm(evidence, context)

        # Feedback patterns
        patterns = self._get_cached_feedback_patterns_llm()
        if phrase.lower() in patterns.get('accepted_phrases', set()):
            evidence -= 0.2
        if phrase.lower() in patterns.get('flagged_phrases', set()):
            evidence += 0.1

        return max(0.0, min(1.0, evidence))

    # === CLUE HELPERS ===

    def _apply_structural_clues_llm(self, ev: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return ev - 0.6
        if block_type == 'inline_code':
            return ev - 0.4
        if block_type in {'table_cell', 'table_header'}:
            ev -= 0.1
        if block_type in {'heading', 'title'}:
            ev -= 0.05
        if block_type == 'admonition':
            ev -= 0.05
        return ev

    def _apply_semantic_clues_llm(self, ev: float, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        audience = (context or {}).get('audience', 'general')

        if content_type in {'procedural', 'tutorial', 'how_to', 'api', 'technical'}:
            ev += 0.1
        if content_type in {'marketing', 'narrative'}:
            ev -= 0.05

        if audience in {'beginner', 'general', 'user'}:
            ev += 0.05

        return ev

    def _apply_feedback_clues_llm(self, ev: float, sentence, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_llm()
        sent_lower = sentence.text.lower()
        if any(p in sent_lower for p in patterns.get('accepted_short_patterns', set())):
            ev -= 0.2
        if any(p in sent_lower for p in patterns.get('flagged_short_patterns', set())):
            ev += 0.1
        return ev

    def _get_cached_feedback_patterns_llm(self) -> Dict[str, Any]:
        return {
            'accepted_short_patterns': {'note:', 'tip:', 'warning:'},
            'flagged_short_patterns': set(),
            'accepted_phrases': set(),
            'flagged_phrases': {'collapsed section', 'expand the accordion'}
        }

    # === SMART MESSAGING ===

    def _get_contextual_short_topic_message(self, length: int, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.85:
            return f"Very short sentence/topic ({length} words) may be ignored by LLMs. Expand for completeness."
        if ev > 0.6:
            return f"Short sentence/topic ({length} words). Consider expanding to ensure LLMs capture the context."
        return f"Consider adding context to this short sentence/topic ({length} words) for better LLM consumability."

    def _generate_smart_short_topic_suggestions(self, sentence, ev: float, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append("Combine short standalone lines into a complete paragraph.")
        suggestions.append("Add subject, action, and outcome to provide context.")
        suggestions.append("Group related short items under a clear heading or list.")
        return suggestions[:3]

    def _get_contextual_accordion_message(self, phrase: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.8:
            return "Content hidden in accordions/collapsed sections may be missed by LLMs. Prefer visible sections."
        if ev > 0.6:
            return "Accordion/collapsed content can reduce LLM visibility. Consider standard sections for important info."
        return "Consider surfacing content referenced in accordions for better LLM processing."

    def _generate_smart_accordion_suggestions(self, phrase: str, ev: float, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append("Move critical instructions out of accordions into visible paragraphs or headings.")
        suggestions.append("Use bullet lists or steps instead of collapsed UI components for key content.")
        suggestions.append("If accordions are necessary, summarize key points outside the collapsed section.")
        return suggestions[:3]
