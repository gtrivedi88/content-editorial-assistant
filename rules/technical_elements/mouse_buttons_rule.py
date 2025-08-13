"""
Mouse Buttons Rule (Production-Grade)
Based on IBM Style Guide topic: "Mouse buttons"
Evidence-based analysis with surgical zero false positive guards for mouse action terminology.
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
from .services.technical_config_service import TechnicalConfigServices, TechnicalContext
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class MouseButtonsRule(BaseTechnicalRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect use of the preposition "on" with mouse actions.
    
    Implements rule-specific evidence calculation for:
    - "Click on" and similar phrases with unnecessary prepositions
    - Mouse action terminology consistency
    - UI element interaction phrasing
    
    Features:
    - YAML-based configuration for maintainable pattern management
    - Surgical zero false positive guards for mouse action contexts
    - Dynamic base evidence scoring based on action specificity
    - Evidence-aware messaging for UI interaction documentation
    """
    
    def __init__(self):
        """Initialize with YAML configuration service."""
        super().__init__()
        self.config_service = TechnicalConfigServices.mouse()
    
    def _get_rule_type(self) -> str:
        return 'technical_mouse_buttons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        PRODUCTION-GRADE: Evidence-based analysis for mouse action violations.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        context = context or {}

        # === STEP 1: Find potential mouse action issues ===
        potential_issues = self._find_potential_mouse_issues(doc, text, context)
        
        # === STEP 2: Process each potential issue with evidence calculation ===
        for issue in potential_issues:
            # Calculate rule-specific evidence score
            evidence_score = self._calculate_mouse_evidence(
                issue, doc, text, context
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                error = self._create_error(
                    sentence=issue['sentence'],
                    sentence_index=issue['sentence_index'],
                    message=self._generate_evidence_aware_message(issue, evidence_score, "mouse"),
                    suggestions=self._generate_evidence_aware_suggestions(issue, evidence_score, context, "mouse"),
                    severity='low' if evidence_score < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=issue.get('span', [0, 0]),
                    flagged_text=issue.get('flagged_text', issue.get('text', ''))
                )
                errors.append(error)
        
        return errors
    
    def _find_potential_mouse_issues(self, doc, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential mouse action issues for evidence assessment using YAML configuration."""
        issues = []
        
        # Load mouse action patterns from YAML configuration
        all_patterns = self.config_service.get_patterns()
        mouse_action_patterns = {}
        
        for pattern_id, pattern_config in all_patterns.items():
            if hasattr(pattern_config, 'pattern'):
                # This is a mouse action pattern - create regex pattern
                action = pattern_config.pattern
                regex_pattern = rf'\b{re.escape(action)}\b'
                mouse_action_patterns[regex_pattern] = pattern_config.evidence
        
        for i, sent in enumerate(doc.sents):
            sent_text = sent.text
            
            # Check for each mouse action pattern
            for pattern, base_evidence in mouse_action_patterns.items():
                for match in re.finditer(pattern, sent_text, re.IGNORECASE):
                    # Find corresponding pattern config for additional details
                    pattern_config = None
                    action_phrase = match.group(0).strip()
                    for pid, config in all_patterns.items():
                        if hasattr(config, 'pattern') and config.pattern.lower() == action_phrase.lower():
                            pattern_config = config
                            break
                    
                    issues.append({
                        'type': 'mouse',
                        'subtype': 'unnecessary_preposition',
                        'action_phrase': match.group(0),
                        'text': match.group(0),
                        'sentence': sent_text,
                        'sentence_index': i,
                        'span': [sent.start_char + match.start(), sent.start_char + match.end()],
                        'base_evidence': base_evidence,
                        'flagged_text': match.group(0),
                        'match_obj': match,
                        'sentence_obj': sent,
                        'pattern_config': pattern_config
                    })
        
        return issues
    
    def _calculate_mouse_evidence(self, issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence score for mouse action violations."""
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR MOUSE ACTIONS ===
        sentence_obj = issue.get('sentence_obj')
        if not sentence_obj:
            return 0.0
            
        action_phrase = issue.get('action_phrase', '')
        
        # === GUARD 1: LEGITIMATE PREPOSITION USAGE ===
        if self._is_legitimate_preposition_usage(action_phrase, sentence_obj, context):
            return 0.0  # Legitimate use of preposition
            
        # === GUARD 2: QUOTED INSTRUCTIONS ===
        if self._is_quoted_instruction(action_phrase, sentence_obj, context):
            return 0.0  # Quoted instructions may preserve original phrasing
            
        # === GUARD 3: NON-UI CONTEXT ===
        if self._is_non_ui_context(action_phrase, sentence_obj, context):
            return 0.0  # Not referring to UI interactions
            
        # Apply common technical guards
        mock_token = type('MockToken', (), {
            'text': action_phrase, 
            'sent': sentence_obj
        })
        # Apply selective technical guards (skip technical context guard for mouse actions)
        # Mouse action violations should be flagged even in technical contexts
        
        # Only check code blocks
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return 0.0  # Code blocks have their own formatting rules
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = issue.get('base_evidence', 0.7)
        
        # === CONTEXT ADJUSTMENTS FROM YAML ===
        evidence_score = self.config_service.calculate_context_evidence(evidence_score, context or {})
        
        # === LINGUISTIC CLUES ===
        evidence_score = self._apply_mouse_linguistic_clues(evidence_score, issue, sentence_obj)
        
        # === STRUCTURAL CLUES ===
        evidence_score = self._apply_technical_structural_clues(evidence_score, context)
        
        # === SEMANTIC CLUES ===
        evidence_score = self._apply_mouse_semantic_clues(evidence_score, issue, text, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _is_legitimate_preposition_usage(self, action_phrase: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if preposition usage is legitimate in this context."""
        sent_text = sentence_obj.text.lower()
        phrase_lower = action_phrase.lower()
        
        # Legitimate preposition contexts
        legitimate_contexts = {
            'click on': [
                'click on this link',  # External links
                'click on the link',   # Link references
                'click on each item',  # Sequential actions
                'click on any option', # Multiple choices
            ],
            'tap on': [
                'tap on the screen',   # Physical actions
                'tap on each tile',    # Game contexts
                'tap on multiple',     # Multiple selection
            ],
            'press on': [
                'press on the brake',  # Physical actions
                'press on the gas',    # Physical actions
            ]
        }
        
        if phrase_lower in legitimate_contexts:
            for context_phrase in legitimate_contexts[phrase_lower]:
                if context_phrase in sent_text:
                    return True
        
        # Check for spatial/physical contexts where "on" is appropriate
        spatial_indicators = [
            'surface', 'screen', 'touch', 'physical', 'hardware',
            'device', 'tablet', 'phone', 'touchscreen'
        ]
        
        return any(indicator in sent_text for indicator in spatial_indicators)
    
    def _is_quoted_instruction(self, action_phrase: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if this is in quoted instructions or examples."""
        sent_text = sentence_obj.text
        
        # Check for quotes around the action phrase
        quote_chars = ['"', "'", '`', '"', '"', ''', ''']
        
        for quote_char in quote_chars:
            if quote_char in sent_text:
                return True
                
        # Check for example context
        example_indicators = [
            'for example', 'such as', 'like', 'e.g.',
            'example:', 'sample:', 'demo:'
        ]
        
        sent_lower = sent_text.lower()
        return any(indicator in sent_lower for indicator in example_indicators)
    
    def _is_non_ui_context(self, action_phrase: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if this is not referring to UI interactions."""
        sent_text = sentence_obj.text.lower()
        phrase_lower = action_phrase.lower()
        
        # Non-UI contexts where prepositions might be appropriate
        non_ui_contexts = {
            'click on': [
                'click on this opportunity',  # Business context
                'click on the idea',          # Metaphorical usage
                'click on with team',         # Personal relationships
            ],
            'press on': [
                'press on regardless',        # Perseverance
                'press on with work',         # Continue working
                'press on through',           # Persistence
            ]
        }
        
        if phrase_lower in non_ui_contexts:
            for context_phrase in non_ui_contexts[phrase_lower]:
                if context_phrase in sent_text:
                    return True
        
        # Check for general non-UI indicators
        non_ui_indicators = [
            'business', 'opportunity', 'relationship', 'team',
            'personal', 'emotional', 'mental', 'psychological'
        ]
        
        return any(indicator in sent_text for indicator in non_ui_indicators)
    
    def _apply_mouse_linguistic_clues(self, evidence_score: float, issue: Dict[str, Any], sentence_obj) -> float:
        """Apply linguistic clues specific to mouse action analysis."""
        sent_text = sentence_obj.text.lower()
        action_phrase = issue.get('action_phrase', '').lower()
        
        # UI element references increase evidence
        ui_elements = [
            'button', 'link', 'menu', 'icon', 'tab', 'option',
            'checkbox', 'radio', 'dropdown', 'field', 'form'
        ]
        
        if any(element in sent_text for element in ui_elements):
            evidence_score += 0.15  # Clear UI context
        
        # Instruction format increases evidence
        instruction_indicators = [
            'to ', 'you can ', 'users can ', 'next, ', 'then ',
            'step ', 'first ', 'finally '
        ]
        
        if any(indicator in sent_text for indicator in instruction_indicators):
            evidence_score += 0.1
        
        # Object immediately following the action
        following_words = sent_text.split(action_phrase, 1)
        if len(following_words) > 1:
            next_words = following_words[1].strip().split()[:3]
            ui_objects = ['the', 'a', 'an', 'save', 'ok', 'cancel', 'submit']
            if any(word in ui_objects for word in next_words):
                evidence_score += 0.1
        
        return evidence_score
    
    def _apply_mouse_semantic_clues(self, evidence_score: float, issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Apply semantic clues specific to mouse action usage."""
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # UI/UX documentation should avoid unnecessary prepositions
        if content_type in ['ui', 'ux', 'tutorial', 'guide', 'manual']:
            evidence_score += 0.15
        elif content_type in ['technical', 'procedural']:
            evidence_score += 0.1
        
        # Software domain expects concise mouse actions
        if domain in ['software', 'application', 'ui', 'user_interface']:
            evidence_score += 0.1
        elif domain in ['web', 'mobile', 'desktop']:
            evidence_score += 0.1
        
        # General audiences benefit from concise instructions
        if audience in ['beginner', 'general', 'user']:
            evidence_score += 0.1
        
        return evidence_score
