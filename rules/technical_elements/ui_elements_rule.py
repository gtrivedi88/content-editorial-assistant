"""
UI Elements Rule (Production-Grade)
Based on IBM Style Guide topic: "UI elements"
Evidence-based analysis with surgical zero false positive guards for UI element verb usage.
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
from .services.technical_config_service import TechnicalConfigServices, TechnicalContext
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
    - YAML-based configuration for maintainable pattern management
    - Surgical zero false positive guards for UI contexts
    - Dynamic base evidence scoring based on UI element specificity
    - Evidence-aware messaging for user interface documentation
    """
    
    def __init__(self):
        """Initialize with YAML configuration service."""
        super().__init__()
        self.config_service = TechnicalConfigServices.ui_elements()
    
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
        """Find potential UI element verb issues for evidence assessment using YAML configuration."""
        issues = []
        
        # Load UI element patterns from YAML configuration
        all_patterns = self.config_service.get_patterns()
        ui_verb_map = {}
        
        for pattern_id, pattern_config in all_patterns.items():
            if hasattr(pattern_config, 'pattern'):
                # This is a UI element pattern
                element = pattern_config.pattern
                ui_verb_map[element] = {
                    "approved": set(pattern_config.approved_verbs) if hasattr(pattern_config, 'approved_verbs') else set(),
                    "incorrect": set(pattern_config.incorrect_verbs) if hasattr(pattern_config, 'incorrect_verbs') else set(),
                    "base_evidence": pattern_config.evidence if hasattr(pattern_config, 'evidence') else 0.7,
                    "pattern_config": pattern_config
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
            
        # Apply selective technical guards (skip technical context guard for UI elements)
        # UI element violations should be flagged even in technical contexts
        
        # Only check code blocks and entities
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return 0.0  # Code blocks have their own formatting rules
            
        # Check entities
        if hasattr(token, 'ent_type_') and token.ent_type_:
            if token.ent_type_ in ['ORG', 'PRODUCT', 'GPE', 'PERSON']:
                return 0.0  # Company names, product names, etc.
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = issue.get('base_evidence', 0.7)
        
        # === CONTEXT ADJUSTMENTS FROM YAML ===
        evidence_score = self.config_service.calculate_context_evidence(evidence_score, context or {})
        
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
