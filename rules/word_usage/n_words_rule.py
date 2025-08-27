"""
Word Usage Rule for words starting with 'N'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'N'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_n'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for N-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        n_word_patterns = {
            "name space": {"alternatives": ["namespace"], "category": "spacing", "severity": "low"},
            "native": {"alternatives": ["local", "basic", "default"], "category": "vague_language", "severity": "medium"},
            "need to": {"alternatives": ["must"], "category": "action_clarity", "severity": "medium"},
            "new": {"alternatives": ["latest", "current"], "category": "temporal_language", "severity": "low"},
            "news feed": {"alternatives": ["newsfeed"], "category": "spacing", "severity": "low"},
            "no.": {"alternatives": ["number"], "category": "abbreviation", "severity": "medium"},
            "non-English": {"alternatives": ["in languages other than English"], "category": "inclusive_language", "severity": "medium"},
            "notebook": {"alternatives": ["notebook (UI)", "laptop (computer)"], "category": "context_specific", "severity": "low"},
        }

        for word, details in n_word_patterns.items():
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
                    
                    evidence_score = self._calculate_n_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
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

    def _calculate_n_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for N-word usage violations."""
        evidence_score = self._get_base_n_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_n_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_n_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_n_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_n_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_n_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on N-word category."""
        if category in ['vague_language', 'action_clarity']:
            return 0.75  # "native", "need to" - clarity and specificity
        elif category in ['abbreviation', 'inclusive_language']:
            return 0.7  # "no.", "non-English" - global communication
        elif category in ['spacing', 'temporal_language', 'context_specific']:
            return 0.5  # "name space", "new", "notebook" - consistency
        return 0.6

    def _apply_linguistic_clues_n_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply N-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'need to' and any(indicator in sent_text for indicator in ['must', 'required', 'mandatory']):
            ev += 0.15  # Instruction context needs authoritative language
        
        if word_lower == 'native' and any(indicator in sent_text for indicator in ['application', 'feature', 'support']):
            ev += 0.1  # Technical context needs specific terminology
        
        if word_lower == 'non-english' and any(indicator in sent_text for indicator in ['international', 'global', 'translation']):
            ev += 0.15  # Global context needs inclusive language
        
        if word_lower == 'no.' and any(indicator in sent_text for indicator in ['translation', 'international', 'localization']):
            ev += 0.1  # Translation context avoids problematic abbreviations
        
        return ev

    def _apply_structural_clues_n_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for N-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_n_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for N-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial' and word_lower == 'need to':
            ev += 0.15  # Tutorials need clear, authoritative instructions
        elif content_type == 'international' and word_lower in ['non-english', 'no.']:
            ev += 0.2  # International content needs inclusive language
        elif content_type == 'technical' and word_lower in ['native', 'name space']:
            ev += 0.1  # Technical docs need precise terminology
        
        if audience == 'global' and word_lower in ['non-english', 'no.', 'native']:
            ev += 0.15  # Global audiences need inclusive, clear language
        elif audience == 'external' and word_lower == 'non-english':
            ev += 0.2  # External audiences need inclusive terminology
        
        return ev

    def _apply_feedback_clues_n_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for N-words."""
        patterns = {'often_flagged_terms': {'need to', 'native', 'non-english', 'no.'}, 'accepted_terms': set()}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        return ev