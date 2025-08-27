"""
Word Usage Rule for words starting with 'D'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class DWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'D'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_d'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for D-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define D-word patterns with evidence categories
        d_word_patterns = {
            "data base": {"alternatives": ["database"], "category": "spacing", "severity": "high"},
            "data center": {"alternatives": ["datacenter"], "category": "context_specific", "severity": "low"},
            "data set": {"alternatives": ["dataset"], "category": "spacing", "severity": "medium"},
            "deactivate": {"alternatives": ["deactivate"], "category": "correct_form", "severity": "low"},
            "deallocate": {"alternatives": ["deallocate"], "category": "correct_form", "severity": "low"},
            "deinstall": {"alternatives": ["uninstall"], "category": "word_choice", "severity": "high"},
            "desire": {"alternatives": ["want", "need"], "category": "user_focus", "severity": "medium"},
            "dialogue": {"alternatives": ["dialog"], "category": "spelling", "severity": "low"},
            "disable": {"alternatives": ["turn off", "clear"], "category": "user_clarity", "severity": "medium"},
            "double click": {"alternatives": ["double-click"], "category": "hyphenation", "severity": "low"},
        }

        # Evidence-based analysis for D-words
        for word, details in d_word_patterns.items():
            for match in re.finditer(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE):
                char_start = match.start()
                char_end = match.end()
                matched_text = match.group(0)
                
                # Find the token and sentence
                token = None
                sent = None
                sentence_index = 0
                
                for i, s in enumerate(doc.sents):
                    if s.start_char <= char_start < s.end_char:
                        sent = s
                        sentence_index = i
                        for t in s:
                            if t.idx <= char_start < t.idx + len(t.text):
                                token = t
                                break
                        break
                
                if sent and token:
                    # Apply surgical guards
                    if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                        continue
                    
                    evidence_score = self._calculate_d_word_evidence(
                        word, token, sent, text, context or {}, details["category"]
                    )
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(char_start, char_end),
                            flagged_text=matched_text
                        ))
        
        return errors

    def _calculate_d_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for D-word usage violations."""
        evidence_score = self._get_base_d_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_d_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_d_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_d_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_d_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_d_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on D-word category."""
        if category == 'spacing':
            return 0.9  # "data base" vs "database", "data set" vs "dataset"
        elif category == 'word_choice':
            return 0.85  # "deinstall" vs "uninstall"
        elif category in ['user_focus', 'user_clarity']:
            return 0.75  # "desire", "disable" - user-centered language
        elif category == 'hyphenation':
            return 0.6  # "double click" vs "double-click"
        elif category in ['spelling', 'context_specific', 'correct_form']:
            return 0.5  # "dialogue"/"dialog", "data center" context
        return 0.6

    def _apply_linguistic_clues_d_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply D-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # User action context
        action_indicators = ['click', 'select', 'choose', 'enable', 'turn']
        if any(action in sent_text for action in action_indicators):
            if word_lower in ['disable', 'double click']:
                ev += 0.1  # User action clarity important
        
        # Data/database context
        if word_lower in ['data base', 'data set']:
            data_indicators = ['store', 'query', 'table', 'record']
            if any(data in sent_text for data in data_indicators):
                ev += 0.15  # Database terminology needs precision
        
        return ev

    def _apply_structural_clues_d_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for D-words."""
        block_type = context.get('block_type', 'paragraph')
        
        if block_type in ['step', 'procedure']:
            ev += 0.1  # Procedural content needs precision
        elif block_type == 'heading':
            ev -= 0.1  # Headings more flexible
        
        return ev

    def _apply_semantic_clues_d_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for D-words."""
        content_type = context.get('content_type', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial':
            if word_lower in ['disable', 'desire', 'double click']:
                ev += 0.15  # Tutorials need user-focused language
        elif content_type == 'technical':
            if word_lower in ['data base', 'deinstall']:
                ev += 0.1  # Technical docs need standard terminology
        
        return ev

    def _apply_feedback_clues_d_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for D-words."""
        patterns = {'often_flagged_terms': {'data base', 'deinstall', 'desire'}, 'accepted_terms': set()}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        return ev