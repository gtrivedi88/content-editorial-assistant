"""
UI Elements Rule (Production-Grade)
Based on IBM Style Guide topic: "UI elements"
Evidence-based analysis with surgical zero false positive guards for UI element verb usage.
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class UIElementsRule(BaseTechnicalRule):
    """
    PRODUCTION-GRADE: Checks for correct verb usage with specific UI elements.
    
    Implements rule-specific evidence calculation for:
    - Incorrect verbs used with specific UI elements (e.g., "press" a checkbox)
    - Context-aware detection of UI interaction vs. general usage
    - Consistency in UI documentation terminology
    
    Features:
    - Surgical zero false positive guards for UI contexts
    - Dynamic base evidence scoring based on UI element specificity
    - Evidence-aware messaging for user interface documentation
    """
    def _get_rule_type(self) -> str:
        return 'technical_ui_elements'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        PRODUCTION-GRADE: Evidence-based analysis for UI element verb violations.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        context = context or {}

        # === STEP 1: Find potential UI element issues ===
        potential_issues = self._find_potential_ui_issues(doc, text, context)
        
        # === STEP 2: Process each potential issue with evidence calculation ===
        for issue in potential_issues:
            # Calculate rule-specific evidence score
            evidence_score = self._calculate_ui_evidence(
                issue, doc, text, context
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                error = self._create_error(
                    sentence=issue['sentence'],
                    sentence_index=issue['sentence_index'],
                    message=self._generate_evidence_aware_message(issue, evidence_score, "ui_element"),
                    suggestions=self._generate_evidence_aware_suggestions(issue, evidence_score, context, "ui_element"),
                    severity='low' if evidence_score < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=issue.get('span', [0, 0]),
                    flagged_text=issue.get('flagged_text', issue.get('text', ''))
                )
                errors.append(error)
        
        return errors
    
    def _find_potential_ui_issues(self, doc, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential UI element verb issues for evidence assessment."""
        issues = []
        
        # UI element verb mapping with base evidence scores
        ui_verb_map = {
            # High specificity UI elements
            "checkbox": {
                "approved": {"select", "check", "clear", "uncheck", "toggle"},
                "incorrect": {"click", "press", "push", "hit", "tap"},
                "base_evidence": 0.85
            },
            "radio button": {
                "approved": {"select", "choose"},
                "incorrect": {"click", "press", "push", "hit", "tap", "check"},
                "base_evidence": 0.85
            },
            "toggle": {
                "approved": {"toggle", "switch", "turn on", "turn off"},
                "incorrect": {"click", "press", "select", "check"},
                "base_evidence": 0.8
            },
            "switch": {
                "approved": {"toggle", "switch", "turn on", "turn off"},
                "incorrect": {"click", "press", "select", "check"},
                "base_evidence": 0.8
            },
            
            # Medium specificity UI elements
            "field": {
                "approved": {"type", "enter", "specify", "input", "fill"},
                "incorrect": {"click", "select", "press", "choose"},
                "base_evidence": 0.75
            },
            "text field": {
                "approved": {"type", "enter", "specify", "input", "fill"},
                "incorrect": {"click", "select", "press", "choose"},
                "base_evidence": 0.75
            },
            "dropdown": {
                "approved": {"select", "choose", "open"},
                "incorrect": {"type", "enter", "press", "push"},
                "base_evidence": 0.8
            },
            "list": {
                "approved": {"select", "choose"},
                "incorrect": {"type", "enter", "press", "push"},
                "base_evidence": 0.7
            },
            
            # Lower specificity UI elements (more context dependent)
            "button": {
                "approved": {"click", "press", "select"},
                "incorrect": {"type", "enter", "fill"},
                "base_evidence": 0.6
            },
            "link": {
                "approved": {"click", "select", "follow"},
                "incorrect": {"type", "enter", "fill", "press"},
                "base_evidence": 0.6
            },
            "menu": {
                "approved": {"open", "access", "navigate"},
                "incorrect": {"type", "enter", "fill"},
                "base_evidence": 0.65
            },
            "icon": {
                "approved": {"click", "select"},
                "incorrect": {"type", "enter", "fill"},
                "base_evidence": 0.6
            }
        }
        
        for i, sent in enumerate(doc.sents):
            sent_text = sent.text
            
            # Look for UI elements and their associated verbs
            for ui_element, verb_info in ui_verb_map.items():
                # Find UI element mentions
                ui_pattern = r'\b' + re.escape(ui_element) + r'\b'
                for ui_match in re.finditer(ui_pattern, sent_text, re.IGNORECASE):
                    # Look for verbs in the sentence that act on this UI element
                    for token in sent:
                        if (hasattr(token, 'pos_') and token.pos_ == 'VERB' and
                            hasattr(token, 'lemma_') and token.lemma_.lower() in verb_info["incorrect"]):
                            
                            # Check if this verb is related to the UI element
                            if self._is_verb_related_to_ui_element(token, ui_match, sent_text, ui_element):
                                issues.append({
                                    'type': 'ui_element',
                                    'subtype': 'incorrect_verb',
                                    'ui_element': ui_element,
                                    'incorrect_verb': token.lemma_.lower(),
                                    'approved_verbs': list(verb_info["approved"]),
                                    'text': token.text,
                                    'sentence': sent_text,
                                    'sentence_index': i,
                                    'span': [token.idx, token.idx + len(token.text)],
                                    'base_evidence': verb_info["base_evidence"],
                                    'flagged_text': token.text,
                                    'token': token,
                                    'sentence_obj': sent,
                                    'ui_match': ui_match
                                })
        
        return issues
    
    def _is_verb_related_to_ui_element(self, verb_token, ui_match, sent_text: str, ui_element: str) -> bool:
        """Check if the verb is related to the UI element in the sentence."""
        # Simple proximity check - verb should be near the UI element
        verb_pos = verb_token.idx
        ui_start = ui_match.start()
        ui_end = ui_match.end()
        
        # Check if verb is within reasonable distance of UI element (50 characters)
        distance = min(abs(verb_pos - ui_start), abs(verb_pos - ui_end))
        if distance > 50:
            return False
        
        # Look for direct object relationships
        for child in verb_token.children:
            if (child.dep_ in ['dobj', 'pobj'] and 
                ui_element.lower() in child.text.lower()):
                return True
        
        # Check if UI element appears after the verb (common pattern)
        if verb_pos < ui_start and distance < 30:
            return True
        
        return False
    
    def _calculate_ui_evidence(self, issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence score for UI element violations."""
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR UI ELEMENTS ===
        token = issue.get('token')
        if not token:
            return 0.0
            
        ui_element = issue.get('ui_element', '')
        incorrect_verb = issue.get('incorrect_verb', '')
        sentence_obj = issue.get('sentence_obj')
        
        # === GUARD 1: NON-UI CONTEXT ===
        if self._is_non_ui_context_usage(incorrect_verb, ui_element, sentence_obj, context):
            return 0.0  # Not referring to UI interactions
            
        # === GUARD 2: GENERAL INSTRUCTION CONTEXT ===
        if self._is_general_instruction_context(incorrect_verb, sentence_obj, context):
            return 0.0  # General instructions may use flexible language
            
        # === GUARD 3: METAPHORICAL OR ABSTRACT USAGE ===
        if self._is_metaphorical_ui_usage(ui_element, sentence_obj, context):
            return 0.0  # Metaphorical usage is not UI violation
            
        # === GUARD 4: QUOTED EXAMPLES ===
        if self._is_quoted_ui_example(sentence_obj, context):
            return 0.0  # Quoted examples may preserve original language
            
        # Apply common technical guards
        if self._apply_surgical_zero_false_positive_guards_technical(token, context):
            return 0.0
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = issue.get('base_evidence', 0.7)
        
        # === LINGUISTIC CLUES ===
        evidence_score = self._apply_ui_linguistic_clues(evidence_score, issue, sentence_obj)
        
        # === STRUCTURAL CLUES ===
        evidence_score = self._apply_technical_structural_clues(evidence_score, context)
        
        # === SEMANTIC CLUES ===
        evidence_score = self._apply_ui_semantic_clues(evidence_score, issue, text, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _is_non_ui_context_usage(self, verb: str, ui_element: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if this is not referring to UI interactions."""
        sent_text = sentence_obj.text.lower()
        
        # Non-UI contexts for common terms
        non_ui_contexts = {
            'button': [
                'shirt button', 'coat button', 'button up', 'button down',
                'belly button', 'button mushroom', 'panic button'
            ],
            'field': [
                'field of study', 'playing field', 'field trip', 'field work',
                'magnetic field', 'field research', 'field test', 'field day'
            ],
            'menu': [
                'restaurant menu', 'food menu', 'lunch menu', 'dinner menu',
                'menu item', 'menu selection', 'à la carte menu'
            ],
            'list': [
                'shopping list', 'todo list', 'grocery list', 'reading list',
                'list price', 'mailing list', 'waiting list'
            ],
            'link': [
                'chain link', 'missing link', 'weak link', 'golf link',
                'link in chain', 'link together', 'connecting link'
            ]
        }
        
        if ui_element in non_ui_contexts:
            for context_phrase in non_ui_contexts[ui_element]:
                if context_phrase in sent_text:
                    return True
        
        # Check for physical/non-digital context indicators
        physical_indicators = [
            'physical', 'hardware', 'mechanical', 'manual', 'paper',
            'printed', 'handwritten', 'offline', 'real world'
        ]
        
        return any(indicator in sent_text for indicator in physical_indicators)
    
    def _is_general_instruction_context(self, verb: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if this is in general instruction context where flexibility is allowed."""
        sent_text = sentence_obj.text.lower()
        
        # General instruction indicators
        general_indicators = [
            'you can also', 'alternatively', 'another way', 'different method',
            'users may', 'some people', 'often', 'sometimes', 'typically'
        ]
        
        return any(indicator in sent_text for indicator in general_indicators)
    
    def _is_metaphorical_ui_usage(self, ui_element: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if UI element is used metaphorically or abstractly."""
        sent_text = sentence_obj.text.lower()
        
        # Metaphorical usage patterns
        metaphorical_patterns = [
            'like a', 'similar to', 'acts as', 'serves as', 'functions as',
            'think of', 'imagine', 'conceptually', 'metaphorically'
        ]
        
        return any(pattern in sent_text for pattern in metaphorical_patterns)
    
    def _is_quoted_ui_example(self, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if this is in quoted examples or user feedback."""
        sent_text = sentence_obj.text
        
        # Check for quotes
        quote_chars = ['"', "'", '`', '"', '"', ''', ''']
        if any(quote_char in sent_text for quote_char in quote_chars):
            return True
        
        # Check for user feedback context
        feedback_indicators = [
            'user said', 'user reported', 'feedback', 'user quote',
            'testimonial', 'user experience', 'user story'
        ]
        
        sent_lower = sent_text.lower()
        return any(indicator in sent_lower for indicator in feedback_indicators)
    
    def _apply_ui_linguistic_clues(self, evidence_score: float, issue: Dict[str, Any], sentence_obj) -> float:
        """Apply linguistic clues specific to UI element analysis."""
        sent_text = sentence_obj.text.lower()
        ui_element = issue.get('ui_element', '')
        incorrect_verb = issue.get('incorrect_verb', '')
        
        # Clear UI instruction context increases evidence
        ui_instruction_indicators = [
            'step', 'then', 'next', 'first', 'finally', 'to',
            'user should', 'users can', 'you must', 'click to'
        ]
        
        if any(indicator in sent_text for indicator in ui_instruction_indicators):
            evidence_score += 0.15
        
        # Direct UI element reference increases evidence
        if f'the {ui_element}' in sent_text:
            evidence_score += 0.1
        
        # Multiple UI elements in sentence suggest UI context
        ui_terms = ['button', 'field', 'checkbox', 'menu', 'dropdown', 'list', 'icon']
        ui_count = sum(1 for term in ui_terms if term in sent_text)
        if ui_count > 1:
            evidence_score += 0.1
        
        return evidence_score
    
    def _apply_ui_semantic_clues(self, evidence_score: float, issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Apply semantic clues specific to UI element usage."""
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # UI/UX documentation should use precise UI terminology
        if content_type in ['ui', 'ux', 'tutorial', 'guide', 'manual']:
            evidence_score += 0.2
        elif content_type in ['technical', 'procedural']:
            evidence_score += 0.15
        
        # Software/app domains expect precise UI language
        if domain in ['software', 'application', 'web', 'mobile']:
            evidence_score += 0.15
        elif domain in ['ui', 'user_interface', 'frontend']:
            evidence_score += 0.2
        
        # General audiences need clear, consistent UI instructions
        if audience in ['beginner', 'general', 'user']:
            evidence_score += 0.15
        elif audience in ['designer', 'developer']:
            evidence_score += 0.1
        
        return evidence_score
