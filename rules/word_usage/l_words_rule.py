"""
Word Usage Rule for words starting with 'L'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection combined with advanced morphological analysis.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class LWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'L'.
    Enhanced with spaCy PhraseMatcher for efficient detection combined with advanced morphological analysis.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_l'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for L-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Enterprise context intelligence
        content_classification = self._get_content_classification(text, context, nlp)
        should_apply = self._should_apply_rule(self._get_rule_category(), content_classification)
        
        if not should_apply:
            return errors  # Skip for technical labels, navigation items, etc.

        l_word_patterns = {
            "land and expand": {"alternatives": ["expansion strategy"], "category": "inclusive_language", "severity": "high"},
            "last name": {"alternatives": ["surname"], "category": "inclusive_language", "severity": "medium"},
            "leverage": {"alternatives": ["use"], "category": "jargon", "severity": "medium"},
            "licence": {"alternatives": ["license"], "category": "spelling", "severity": "low"},
            "log on to": {"alternatives": ["log on to"], "category": "correct_form", "severity": "low"},
            "log off of": {"alternatives": ["log off from"], "category": "preposition_usage", "severity": "medium"},
            "look and feel": {"alternatives": ["appearance", "user interface"], "category": "vague_language", "severity": "medium"},
            "lowercase": {"alternatives": ["lowercase"], "category": "spacing", "severity": "low"},
        }

        # Evidence-based analysis for standard L-word patterns
        for word, details in l_word_patterns.items():
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
                    
                    evidence_score = self._calculate_l_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(char_start, char_end), flagged_text=matched_text
                        ))

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Special morphological analysis for compound words
        for i, sent in enumerate(doc.sents):
            # LINGUISTIC ANCHOR: Use SpaCy to detect "life cycle" (two words) that should be "lifecycle"
            for token in sent:
                if token.lemma_.lower() == "life" and token.i + 1 < len(doc):
                    next_token = doc[token.i + 1]
                    if next_token.lemma_.lower() == "cycle":
                        # Check if they form a compound that should be one word
                        if token.dep_ == "compound" or next_token.dep_ == "compound":
                            # Apply surgical guards for compound detection
                            if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                                continue
                            
                            evidence_score = self._calculate_l_word_evidence("life cycle", token, sent, text, context or {}, "spacing")
                            
                            if evidence_score > 0.1:
                                errors.append(self._create_error(
                                    sentence=sent.text, sentence_index=i,
                                    message=self._generate_evidence_aware_word_usage_message("life cycle", evidence_score, "spacing"),
                                    suggestions=self._generate_evidence_aware_word_usage_suggestions("life cycle", ["lifecycle"], evidence_score, context or {}, "spacing"),
                                    severity='low' if evidence_score < 0.7 else 'medium',
                                    text=text, context=context, evidence_score=evidence_score,
                                    span=(token.idx, next_token.idx + len(next_token.text)),
                                    flagged_text=f"{token.text} {next_token.text}"
                                ))
        
        return errors

    def _calculate_l_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for L-word usage violations."""
        evidence_score = self._get_base_l_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_l_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_l_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_l_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_l_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_l_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on L-word category."""
        if category == 'inclusive_language':
            return 0.85  # "land and expand", "last name" - critical for global content
        elif category in ['jargon', 'vague_language']:
            return 0.75  # "leverage", "look and feel" - clarity and professionalism
        elif category in ['preposition_usage']:
            return 0.65  # "log off of" - grammatical precision
        elif category in ['spelling', 'spacing', 'correct_form']:
            return 0.5  # "licence", "lowercase", "log on to" - consistency
        return 0.6

    def _apply_linguistic_clues_l_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply L-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'land and expand' and any(indicator in sent_text for indicator in ['strategy', 'business', 'growth']):
            ev += 0.2  # Business context needs inclusive terminology
        
        if word_lower == 'leverage' and any(indicator in sent_text for indicator in ['documentation', 'technical', 'international']):
            ev += 0.15  # Technical/international context needs clear language
        
        if word_lower == 'last name' and any(indicator in sent_text for indicator in ['global', 'international', 'form', 'user']):
            ev += 0.15  # User-facing content needs inclusive language
        
        if word_lower == 'look and feel' and any(indicator in sent_text for indicator in ['ui', 'interface', 'design']):
            ev += 0.1  # UI context needs specific terminology
        
        return ev

    def _apply_structural_clues_l_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for L-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_l_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for L-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['land and expand', 'leverage']:
            ev += 0.25  # Customer content needs professional, clear language
        elif content_type == 'international' and word_lower in ['last name', 'leverage']:
            ev += 0.2  # International content needs inclusive, clear language
        elif content_type == 'ui_documentation' and word_lower == 'look and feel':
            ev += 0.15  # UI docs need specific terminology
        
        if audience == 'global' and word_lower in ['last name', 'leverage']:
            ev += 0.15  # Global audiences need inclusive, clear language
        elif audience == 'external' and word_lower == 'land and expand':
            ev += 0.3  # External audiences need inclusive terminology
        
        return ev

    def _apply_feedback_clues_l_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for L-words."""
        patterns = {'often_flagged_terms': {'land and expand', 'leverage', 'last name', 'look and feel'}, 'accepted_terms': {'log on to'}}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.3  # "log on to" is the correct form
        
        return ev