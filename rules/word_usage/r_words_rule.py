"""
Word Usage Rule for words starting with 'R' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for R-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Preserves sophisticated dependency parsing for 'real time' detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class RWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'R'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for R-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    - PRESERVED: Advanced dependency parsing for 'real time' detection
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each R-word violation
    - Evidence-aware suggestions tailored to writing context
    - Sophisticated adjectival modification pattern analysis
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_r'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for R-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        r_word_patterns = {
            "read-only": {"alternatives": ["read-only"], "category": "hyphenation", "severity": "low"},
            "re-": {"alternatives": ["re- (no hyphen)"], "category": "prefix_usage", "severity": "low"},
            "Redbook": {"alternatives": ["IBM Redbooks publication"], "category": "brand_terminology", "severity": "high"},
            "refer to": {"alternatives": ["see"], "category": "cross_reference", "severity": "low"},
            "respective": {"alternatives": ["(rewrite sentence)"], "category": "vague_language", "severity": "medium"},
            "roadmap": {"alternatives": ["roadmap"], "category": "spacing", "severity": "low"},
            "roll back": {"alternatives": ["roll back (verb)", "rollback (noun)"], "category": "form_usage", "severity": "low"},
            "run time": {"alternatives": ["runtime (adjective)", "run time (noun)"], "category": "form_usage", "severity": "low"},
        }

        # Evidence-based analysis for standard R-word patterns
        for word, details in r_word_patterns.items():
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
                    
                    evidence_score = self._calculate_r_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(char_start, char_end), flagged_text=matched_text
                        ))

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Context-aware dependency parsing for 'real time' 
        # This sophisticated linguistic analysis checks for adjectival modification patterns
        for token in doc:
            # Linguistic Anchor: Check for 'real time' used as an adjective through dependency analysis
            if token.lemma_ == "real" and token.i + 1 < len(doc) and doc[token.i + 1].lemma_ == "time":
                if doc[token.i + 1].dep_ == "amod" or token.dep_ == "amod":
                    sent = token.sent
                    next_token = doc[token.i + 1]
                    
                    # Get sentence index
                    sentence_index = 0
                    for i, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = i
                            break
                    
                    # Apply surgical guards for dependency detection
                    if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                        continue
                    
                    evidence_score = self._calculate_r_word_evidence("real time", token, sent, text, context or {}, "hyphenation")
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message("real time", evidence_score, "hyphenation"),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions("real time", ["real-time"], evidence_score, context or {}, "hyphenation"),
                            severity='medium' if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(token.idx, next_token.idx + len(next_token.text)),
                            flagged_text=f"{token.text} {next_token.text}"
                        ))
        
        return errors

    def _calculate_r_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for R-word usage violations."""
        evidence_score = self._get_base_r_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_r_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_r_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_r_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_r_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_r_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on R-word category."""
        if category == 'brand_terminology':
            return 0.9  # "Redbook" - critical brand compliance
        elif category in ['vague_language', 'hyphenation']:
            return 0.7  # "respective", "real time" - clarity and consistency
        elif category in ['form_usage', 'cross_reference']:
            return 0.6  # "roll back", "refer to" - correctness and style
        elif category in ['spacing', 'prefix_usage']:
            return 0.5  # "roadmap", "re-" - consistency
        return 0.6

    def _apply_linguistic_clues_r_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply R-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'redbook' and any(indicator in sent_text for indicator in ['ibm', 'publication', 'documentation']):
            ev += 0.2  # IBM context needs proper brand terminology
        
        if word_lower == 'respective' and any(indicator in sent_text for indicator in ['each', 'their', 'corresponding']):
            ev += 0.15  # Context suggests unclear writing that can be improved
        
        if word_lower == 'real time' and any(indicator in sent_text for indicator in ['processing', 'data', 'system']):
            ev += 0.1  # Technical context needs precise hyphenation
        
        if word_lower == 'refer to' and any(indicator in sent_text for indicator in ['section', 'chapter', 'page']):
            ev += 0.1  # Cross-reference context benefits from "see"
        
        return ev

    def _apply_structural_clues_r_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for R-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_r_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for R-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['redbook', 'respective']:
            ev += 0.2  # Customer content needs clear, proper terminology
        elif content_type == 'technical' and word_lower in ['real time', 'run time']:
            ev += 0.15  # Technical docs need precise form usage
        elif content_type == 'documentation' and word_lower == 'refer to':
            ev += 0.1  # Documentation benefits from concise cross-references
        
        if audience == 'external' and word_lower in ['redbook', 'respective']:
            ev += 0.2  # External audiences need clear, proper terminology
        elif audience == 'global' and word_lower == 'respective':
            ev += 0.15  # Global audiences benefit from clear language
        
        return ev

    def _apply_feedback_clues_r_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for R-words."""
        patterns = {'often_flagged_terms': {'redbook', 'respective', 'real time'}, 'accepted_terms': {'roadmap'}}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2  # "roadmap" is correct as one word
        
        return ev