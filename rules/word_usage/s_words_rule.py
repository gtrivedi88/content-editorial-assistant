"""
Word Usage Rule for words starting with 'S' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for S-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Preserves sophisticated POS analysis for verb form detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class SWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'S'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for S-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    - PRESERVED: Advanced POS analysis for verb form detection
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each S-word violation
    - Evidence-aware suggestions tailored to writing context
    - Sophisticated grammatical analysis for setup/shutdown verb forms
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_s'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for S-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        s_word_patterns = {
            "sanity check": {"alternatives": ["validation", "check", "review"], "category": "inclusive_language", "severity": "high"},
            "screen shot": {"alternatives": ["screenshot"], "category": "spacing", "severity": "low"},
            "second name": {"alternatives": ["surname"], "category": "inclusive_language", "severity": "medium"},
            "secure": {"alternatives": ["security-enhanced"], "category": "absolute_claim", "severity": "high"},
            "segregate": {"alternatives": ["separate"], "category": "inclusive_language", "severity": "high"},
            "server-side": {"alternatives": ["serverside"], "category": "hyphenation", "severity": "low"},
            "shall": {"alternatives": ["must", "will"], "category": "modal_verb", "severity": "medium"},
            "ship": {"alternatives": ["release", "make available"], "category": "jargon", "severity": "medium"},
            "should": {"alternatives": ["must"], "category": "modal_verb", "severity": "medium"},
            "slave": {"alternatives": ["secondary", "replica", "agent"], "category": "inclusive_language", "severity": "high"},
            "stand-alone": {"alternatives": ["standalone"], "category": "hyphenation", "severity": "low"},
            "suite": {"alternatives": ["family", "set"], "category": "word_choice", "severity": "medium"},
            "sunset": {"alternatives": ["discontinue", "withdraw"], "category": "jargon", "severity": "medium"},
        }

        # Evidence-based analysis for standard S-word patterns
        for word, details in s_word_patterns.items():
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
                    
                    evidence_score = self._calculate_s_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(char_start, char_end), flagged_text=matched_text
                        ))

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: POS analysis for verb forms
        # This sophisticated linguistic analysis distinguishes verbs from nouns/adjectives
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.lemma_.lower() == "setup" and token.pos_ == "VERB":
                    # Apply surgical guards for POS detection
                    if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                        continue
                    
                    evidence_score = self._calculate_s_word_evidence("setup", token, sent, text, context or {}, "verb_form")
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=i,
                            message=self._generate_evidence_aware_word_usage_message("setup", evidence_score, "verb_form"),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions("setup", ["set up"], evidence_score, context or {}, "verb_form"),
                            severity='high' if evidence_score >= 0.7 else 'medium',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(token.idx, token.idx + len(token.text)), flagged_text=token.text
                        ))
                        
                if token.lemma_.lower() == "shutdown" and token.pos_ == "VERB":
                    # Apply surgical guards for POS detection
                    if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                        continue
                    
                    evidence_score = self._calculate_s_word_evidence("shutdown", token, sent, text, context or {}, "verb_form")
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=i,
                            message=self._generate_evidence_aware_word_usage_message("shutdown", evidence_score, "verb_form"),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions("shutdown", ["shut down"], evidence_score, context or {}, "verb_form"),
                            severity='medium' if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(token.idx, token.idx + len(token.text)), flagged_text=token.text
                        ))
        
        return errors

    def _calculate_s_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for S-word usage violations."""
        evidence_score = self._get_base_s_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_s_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_s_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_s_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_s_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_s_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on S-word category."""
        if category == 'inclusive_language':
            return 0.9  # "sanity check", "slave", "segregate" - critical for inclusive content
        elif category in ['absolute_claim', 'verb_form']:
            return 0.8  # "secure", "setup/shutdown" - accuracy and grammatical correctness
        elif category in ['jargon', 'modal_verb']:
            return 0.75  # "ship", "sunset", "shall", "should" - professional clarity
        elif category == 'word_choice':
            return 0.6  # "suite" - precision
        elif category in ['spacing', 'hyphenation']:
            return 0.5  # "screen shot", "server-side", "stand-alone" - consistency
        return 0.6

    def _apply_linguistic_clues_s_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply S-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower in ['sanity check', 'slave', 'segregate'] and any(indicator in sent_text for indicator in ['customer', 'user', 'global']):
            ev += 0.3  # Customer/global content needs inclusive language
        
        if word_lower == 'secure' and any(indicator in sent_text for indicator in ['system', 'application', 'data']):
            ev += 0.2  # Security context needs qualified claims
        
        if word_lower in ['setup', 'shutdown'] and any(indicator in sent_text for indicator in ['system', 'server', 'process']):
            ev += 0.15  # Technical action context needs correct verb forms
        
        if word_lower in ['shall', 'should'] and any(indicator in sent_text for indicator in ['must', 'required', 'mandatory']):
            ev += 0.1  # Requirement context needs authoritative language
        
        return ev

    def _apply_structural_clues_s_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for S-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_s_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for S-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['sanity check', 'slave', 'ship']:
            ev += 0.3  # Customer content must use professional, inclusive language
        elif content_type == 'international' and word_lower in ['sanity check', 'segregate']:
            ev += 0.25  # International content requires inclusive language
        elif content_type == 'technical' and word_lower in ['setup', 'shutdown', 'secure']:
            ev += 0.15  # Technical docs need precise, qualified language
        
        if audience == 'external' and word_lower in ['sanity check', 'slave', 'ship']:
            ev += 0.3  # External audiences need professional terminology
        elif audience == 'global' and word_lower in ['sanity check', 'segregate']:
            ev += 0.2  # Global audiences need inclusive language
        
        return ev

    def _apply_feedback_clues_s_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for S-words."""
        patterns = {'often_flagged_terms': {'sanity check', 'slave', 'secure', 'setup', 'shutdown'}, 'accepted_terms': set()}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        return ev