"""
Word Usage Rule for words starting with 'O'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class OWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'O'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_o'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for O-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        o_word_patterns = {
            "off of": {"alternatives": ["off", "from"], "category": "redundant_preposition", "severity": "medium"},
            "off-line": {"alternatives": ["offline"], "category": "hyphenation", "severity": "low"},
            "OK": {"alternatives": ["OK (UI only)", "acceptable"], "category": "context_specific", "severity": "medium"},
            "on-boarding": {"alternatives": ["onboarding"], "category": "hyphenation", "severity": "low"},
            "on premise": {"alternatives": ["on-premises", "on premises"], "category": "hyphenation", "severity": "medium"},
            "on the fly": {"alternatives": ["dynamically", "during processing"], "category": "jargon", "severity": "medium"},
            "orientate": {"alternatives": ["orient"], "category": "word_choice", "severity": "low"},
            "our": {"alternatives": ["the", "this"], "category": "perspective", "severity": "medium"},
            "out-of-the-box": {"alternatives": ["out of the box"], "category": "hyphenation", "severity": "low"},
        }

        for word, details in o_word_patterns.items():
            for match in re.finditer(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE):
                char_start, char_end, matched_text = match.start(), match.end(), match.group(0)
                
                token, sent, sentence_index = None, None, 0
                for i, s in enumerate(doc.sents):
                    if s.start_char <= char_start < s.end_char:
                        sent, sentence_index = s, i
                        for t in s:
                            if t.idx <= char_start < t.idx + len(t.text):
                                token = t
                                break
                        break
                
                if sent and token:
                    if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                        continue
                    
                    evidence_score = self._calculate_o_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(char_start, char_end), flagged_text=matched_text
                        ))
        return errors

    def _calculate_o_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for O-word usage violations."""
        evidence_score = self._get_base_o_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_o_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_o_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_o_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_o_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_o_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on O-word category."""
        if category in ['redundant_preposition', 'jargon', 'perspective']:
            return 0.75  # "off of", "on the fly", "our" - clarity and professionalism
        elif category in ['context_specific', 'hyphenation']:
            return 0.6  # "OK", "on premise", "on-boarding" - consistency and context
        elif category == 'word_choice':
            return 0.5  # "orientate" - correctness
        return 0.6

    def _apply_linguistic_clues_o_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply O-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'our' and any(indicator in sent_text for indicator in ['documentation', 'technical', 'guide']):
            ev += 0.15  # Technical content should avoid first-person pronouns
        
        if word_lower == 'on the fly' and any(indicator in sent_text for indicator in ['process', 'generate', 'create']):
            ev += 0.1  # Technical context needs precise language
        
        if word_lower == 'ok' and any(indicator in sent_text for indicator in ['button', 'dialog', 'interface']):
            ev -= 0.1  # UI context makes "OK" appropriate
        
        if word_lower == 'off of' and any(indicator in sent_text for indicator in ['remove', 'take', 'get']):
            ev += 0.1  # Action context benefits from precise prepositions
        
        return ev

    def _apply_structural_clues_o_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for O-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_o_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for O-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'technical' and word_lower in ['our', 'on the fly']:
            ev += 0.15  # Technical docs need objective, precise language
        elif content_type == 'tutorial' and word_lower in ['our', 'off of']:
            ev += 0.1  # Tutorials benefit from clear, professional language
        elif content_type == 'ui_documentation' and word_lower == 'ok':
            ev -= 0.2  # UI docs appropriately use "OK" for interface elements
        
        if audience == 'external' and word_lower == 'our':
            ev += 0.2  # External audiences need objective language
        elif audience == 'global' and word_lower == 'on the fly':
            ev += 0.15  # Global audiences need clear, non-idiomatic language
        
        return ev

    def _apply_feedback_clues_o_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for O-words."""
        patterns = {'often_flagged_terms': {'our', 'on the fly', 'off of'}, 'accepted_terms': {'ok'}}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2  # "OK" is acceptable in UI contexts
        
        return ev