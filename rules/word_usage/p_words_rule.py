"""
Word Usage Rule for words starting with 'P'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'P'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_p'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for P-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        p_word_patterns = {
            "pain point": {"alternatives": ["challenge", "issue", "problem"], "category": "jargon", "severity": "medium"},
            "pane": {"alternatives": ["pane (framed section)", "panel", "window"], "category": "context_specific", "severity": "low"},
            "partner": {"alternatives": ["IBM Business Partner"], "category": "brand_specific", "severity": "medium"},
            "path name": {"alternatives": ["pathname"], "category": "spacing", "severity": "low"},
            "PDF": {"alternatives": ["PDF file", "PDF document"], "category": "noun_usage", "severity": "medium"},
            "per": {"alternatives": ["according to"], "category": "preposition_choice", "severity": "low"},
            "perform": {"alternatives": ["run", "install", "execute"], "category": "action_clarity", "severity": "low"},
            "please": {"alternatives": ["(remove)", "ensure"], "category": "cultural_sensitivity", "severity": "medium"},
            "plug-in": {"alternatives": ["plugin"], "category": "hyphenation", "severity": "low"},
            "pop up": {"alternatives": ["pop-up"], "category": "hyphenation", "severity": "low"},
            "power up": {"alternatives": ["power on", "turn on"], "category": "action_clarity", "severity": "medium"},
            "practise": {"alternatives": ["practice"], "category": "spelling", "severity": "low"},
            "preinstall": {"alternatives": ["preinstall"], "category": "spacing", "severity": "low"},
            "prior to": {"alternatives": ["before"], "category": "redundant_phrase", "severity": "low"},
            "program product": {"alternatives": ["licensed program"], "category": "technical_precision", "severity": "medium"},
            "punch": {"alternatives": ["press", "type"], "category": "action_clarity", "severity": "high"},
        }

        for word, details in p_word_patterns.items():
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
                    
                    evidence_score = self._calculate_p_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
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

    def _calculate_p_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for P-word usage violations."""
        evidence_score = self._get_base_p_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_p_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_p_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_p_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_p_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_p_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on P-word category."""
        if category == 'action_clarity':
            return 0.8  # "punch", "power up" - clarity critical for instructions
        elif category in ['jargon', 'cultural_sensitivity', 'technical_precision']:
            return 0.75  # "pain point", "please", "program product" - professional clarity
        elif category in ['brand_specific', 'noun_usage']:
            return 0.7  # "partner", "PDF" - consistency and precision
        elif category in ['spacing', 'hyphenation', 'spelling', 'redundant_phrase', 'preposition_choice']:
            return 0.5  # Various consistency issues
        elif category == 'context_specific':
            return 0.4  # "pane" - context dependent
        return 0.6

    def _apply_linguistic_clues_p_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply P-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'punch' and any(indicator in sent_text for indicator in ['key', 'button', 'keyboard']):
            ev += 0.2  # Action context needs precise language
        
        if word_lower == 'please' and any(indicator in sent_text for indicator in ['international', 'global', 'documentation']):
            ev += 0.15  # International content avoids cultural assumptions
        
        if word_lower == 'pain point' and any(indicator in sent_text for indicator in ['business', 'customer', 'solution']):
            ev += 0.1  # Business context benefits from professional language
        
        if word_lower == 'pdf' and any(indicator in sent_text for indicator in ['document', 'file', 'download']):
            ev += 0.1  # File context needs precise noun usage
        
        return ev

    def _apply_structural_clues_p_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for P-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_p_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for P-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial' and word_lower in ['punch', 'please', 'perform']:
            ev += 0.15  # Tutorials need clear, direct instructions
        elif content_type == 'customer_facing' and word_lower in ['pain point', 'please']:
            ev += 0.2  # Customer content needs professional, inclusive language
        elif content_type == 'international' and word_lower == 'please':
            ev += 0.25  # International content avoids cultural assumptions
        elif content_type == 'technical' and word_lower in ['program product', 'perform']:
            ev += 0.1  # Technical docs need precise terminology
        
        if audience == 'global' and word_lower in ['please', 'pain point']:
            ev += 0.15  # Global audiences need inclusive, professional language
        elif audience == 'external' and word_lower in ['partner', 'please']:
            ev += 0.2  # External audiences need specific, inclusive language
        
        return ev

    def _apply_feedback_clues_p_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for P-words."""
        patterns = {'often_flagged_terms': {'punch', 'please', 'pain point', 'pdf'}, 'accepted_terms': {'preinstall'}}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2  # "preinstall" is correct as one word
        
        return ev