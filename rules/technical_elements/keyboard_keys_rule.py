"""
Keyboard Keys Rule (Production-Grade)
Based on IBM Style Guide topic: "Keyboard keys"
Evidence-based analysis with surgical zero false positive guards for keyboard key formatting.
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class KeyboardKeysRule(BaseTechnicalRule):
    """
    PRODUCTION-GRADE: Checks for correct formatting of keyboard keys and key combinations.
    
    Implements rule-specific evidence calculation for:
    - Key combinations without proper + separator (e.g., "Ctrl Alt Del")
    - Lowercase key names that should be capitalized
    - Missing formatting around key references
    
    Features:
    - Surgical zero false positive guards for keyboard contexts
    - Dynamic base evidence scoring based on key type specificity
    - Evidence-aware messaging for UI interaction documentation
    """
    def _get_rule_type(self) -> str:
        return 'technical_keyboard_keys'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        PRODUCTION-GRADE: Evidence-based analysis for keyboard key violations.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        context = context or {}

        # === STEP 1: Find potential keyboard key issues ===
        potential_issues = self._find_potential_keyboard_issues(doc, text, context)
        
        # === STEP 2: Process each potential issue with evidence calculation ===
        for issue in potential_issues:
            # Calculate rule-specific evidence score
            evidence_score = self._calculate_keyboard_evidence(
                issue, doc, text, context
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                error = self._create_error(
                    sentence=issue['sentence'],
                    sentence_index=issue['sentence_index'],
                    message=self._generate_evidence_aware_message(issue, evidence_score, "keyboard"),
                    suggestions=self._generate_evidence_aware_suggestions(issue, evidence_score, context, "keyboard"),
                    severity='low' if evidence_score < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=issue.get('span', [0, 0]),
                    flagged_text=issue.get('flagged_text', issue.get('text', ''))
                )
                errors.append(error)
        
        return errors
    
    def _find_potential_keyboard_issues(self, doc, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential keyboard key issues for evidence assessment."""
        issues = []
        
        # Key combination patterns (missing + separator)
        key_combo_patterns = {
            r'\b(Ctrl|Alt|Shift|Cmd|Command)\s+[A-Za-z0-9]+\b': 0.85,  # High evidence for key combos
            r'\b(Ctrl|Alt|Shift|Cmd|Command)\s+(Ctrl|Alt|Shift|Cmd|Command)\s+[A-Za-z0-9]+\b': 0.9,  # Very high for triple combos
        }
        
        # Key names that should be capitalized
        key_names = {
            "enter": 0.8, "shift": 0.8, "alt": 0.8, "ctrl": 0.8, 
            "esc": 0.75, "tab": 0.7, "return": 0.8, "backspace": 0.8,
            "space": 0.6, "delete": 0.7, "home": 0.6, "end": 0.6,
            "pageup": 0.75, "pagedown": 0.75, "insert": 0.75
        }
        
        for i, sent in enumerate(doc.sents):
            sent_text = sent.text
            
            # Check for key combination issues
            for pattern, base_evidence in key_combo_patterns.items():
                for match in re.finditer(pattern, sent_text, re.IGNORECASE):
                    issues.append({
                        'type': 'keyboard',
                        'subtype': 'key_combination_spacing',
                        'text': match.group(0),
                        'sentence': sent_text,
                        'sentence_index': i,
                        'span': [sent.start_char + match.start(), sent.start_char + match.end()],
                        'base_evidence': base_evidence,
                        'flagged_text': match.group(0),
                        'match_obj': match,
                        'sentence_obj': sent
                    })
            
            # Check for lowercase key names
            for token in sent:
                if hasattr(token, 'lemma_') and hasattr(token, 'is_lower'):
                    token_lower = token.lemma_.lower()
                    if token_lower in key_names and token.is_lower:
                        issues.append({
                            'type': 'keyboard',
                            'subtype': 'lowercase_key_name',
                            'key_name': token_lower,
                            'text': token.text,
                            'sentence': sent_text,
                            'sentence_index': i,
                            'span': [token.idx, token.idx + len(token.text)],
                            'base_evidence': key_names[token_lower],
                            'flagged_text': token.text,
                            'token': token,
                            'sentence_obj': sent
                        })
        
        return issues
    
    def _calculate_keyboard_evidence(self, issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence score for keyboard key violations."""
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR KEYBOARD KEYS ===
        sentence_obj = issue.get('sentence_obj')
        if not sentence_obj:
            return 0.0
            
        issue_type = issue.get('subtype', '')
        flagged_text = issue.get('flagged_text', '')
        
        # === GUARD 1: ALREADY PROPERLY FORMATTED ===
        if self._is_properly_formatted_key_reference(flagged_text, sentence_obj, context):
            return 0.0  # Already properly formatted
            
        # === GUARD 2: NON-KEYBOARD CONTEXT ===
        if self._is_non_keyboard_context(flagged_text, sentence_obj, context):
            return 0.0  # Not referring to keyboard keys
            
        # Apply common technical guards
        token = issue.get('token')
        if token and self._apply_surgical_zero_false_positive_guards_technical(token, context):
            return 0.0
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = issue.get('base_evidence', 0.7)
        
        # === LINGUISTIC CLUES ===
        evidence_score = self._apply_keyboard_linguistic_clues(evidence_score, issue, sentence_obj)
        
        # === STRUCTURAL CLUES ===
        evidence_score = self._apply_technical_structural_clues(evidence_score, context)
        
        # === SEMANTIC CLUES ===
        evidence_score = self._apply_keyboard_semantic_clues(evidence_score, issue, text, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _is_properly_formatted_key_reference(self, flagged_text: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if key reference is already properly formatted."""
        sent_text = sentence_obj.text
        
        # Check for proper formatting indicators
        formatting_indicators = ['`', '**', '__', '<kbd>', '</kbd>']
        if any(indicator in sent_text for indicator in formatting_indicators):
            return True
            
        # Check for instructional context that allows flexibility
        instructional_patterns = [
            'press the', 'hold the', 'use the', 'hit the',
            'key combination', 'keyboard shortcut', 'hotkey'
        ]
        
        sent_lower = sent_text.lower()
        return any(pattern in sent_lower for pattern in instructional_patterns)
    
    def _is_non_keyboard_context(self, flagged_text: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if this is not referring to keyboard keys."""
        sent_text = sentence_obj.text.lower()
        flagged_lower = flagged_text.lower()
        
        # Common non-keyboard usages
        non_keyboard_contexts = {
            'shift': ['work shift', 'night shift', 'shift work', 'paradigm shift'],
            'tab': ['browser tab', 'new tab', 'tab page', 'tab character'],
            'home': ['home page', 'home directory', 'go home', 'at home'],
            'end': ['end of', 'at the end', 'end result', 'end user'],
            'space': ['disk space', 'storage space', 'white space', 'namespace'],
            'delete': ['delete file', 'delete record', 'delete user']
        }
        
        if flagged_lower in non_keyboard_contexts:
            for context_phrase in non_keyboard_contexts[flagged_lower]:
                if context_phrase in sent_text:
                    return True
        
        return False
    
    def _apply_keyboard_linguistic_clues(self, evidence_score: float, issue: Dict[str, Any], sentence_obj) -> float:
        """Apply linguistic clues specific to keyboard analysis."""
        sent_text = sentence_obj.text.lower()
        issue_type = issue.get('subtype', '')
        
        # UI instruction context increases evidence
        ui_indicators = ['click', 'press', 'type', 'select', 'choose', 'navigate']
        if any(indicator in sent_text for indicator in ui_indicators):
            evidence_score += 0.1
        
        # Instruction format increases evidence
        if any(pattern in sent_text for pattern in ['to ', 'you can ', 'users can ']):
            evidence_score += 0.05
        
        # Multiple key references suggest instruction context
        key_count = len(re.findall(r'\b(ctrl|alt|shift|cmd|enter|tab|esc)\b', sent_text, re.IGNORECASE))
        if key_count > 1:
            evidence_score += 0.1
        
        return evidence_score
    
    def _apply_keyboard_semantic_clues(self, evidence_score: float, issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Apply semantic clues specific to keyboard key usage."""
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # UI/UX documentation should have proper key formatting
        if content_type in ['ui', 'ux', 'tutorial', 'guide', 'manual']:
            evidence_score += 0.15
        elif content_type in ['technical', 'api']:
            evidence_score += 0.1
        
        # Software domain expects proper key formatting
        if domain in ['software', 'application', 'ui', 'user_interface']:
            evidence_score += 0.1
        
        # General audiences need clear key formatting
        if audience in ['beginner', 'general', 'user']:
            evidence_score += 0.1
        
        return evidence_score
