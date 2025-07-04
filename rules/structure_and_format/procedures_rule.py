"""
Procedures Rule
Based on IBM Style Guide topic: "Procedures"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class ProceduresRule(BaseStructureRule):
    """
    Checks for style issues in procedural steps. This rule uses dependency
    parsing to identify procedural contexts and ensures that steps begin
    with an imperative verb, while correctly handling optional and
    conditional steps to reduce false positives.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'procedures'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes procedural content using pure context-aware analysis.
        No more heuristics - we KNOW what type of content we're analyzing.
        """
        errors = []
        if not nlp:
            return errors

        # Context-aware analysis: Only analyze content we KNOW is procedural
        # No more guessing or heuristic fallbacks
        
        # Check if this is a procedural list item (ordered lists are typically procedures)
        is_procedural_step = context and context.get('block_type') in [
            'list_item_ordered',  # Numbered lists are typically procedural
            'list_item'           # Generic list items in procedural contexts
        ]
        
        # Check if this is content in a procedures/instructions section
        is_procedural_context = context and (
            context.get('parent_type') == 'section' and 
            any(keyword in text.lower() for keyword in ['procedure', 'steps', 'instructions', 'installation', 'configuration'])
        )
        
        if is_procedural_step or is_procedural_context:
            # We KNOW this is procedural content, so apply procedural rules with confidence
            for i, sentence in enumerate(sentences):
                doc = nlp(sentence)
                
                # Analyze each sentence as a potential procedural step
                step_analysis = self._analyze_procedural_step(doc, context)
                
                if not step_analysis['is_valid']:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=step_analysis['message'],
                        suggestions=step_analysis['suggestions'],
                        severity=step_analysis['severity']
                    ))
        
        # For other content types, we don't apply procedural analysis
        # This eliminates false positives from trying to detect procedures in regular text
        
        return errors

    def _analyze_procedural_step(self, doc, context) -> Dict[str, Any]:
        """
        Analyze a sentence as a procedural step using context-aware linguistic analysis.
        No more heuristics - comprehensive procedural step validation.
        """
        if not doc:
            return {
                'is_valid': False,
                'message': 'Empty procedural step.',
                'suggestions': ['Provide a clear procedural instruction.'],
                'severity': 'medium'
            }
        
        first_token = doc[0]
        
        # Valid procedural step patterns (context-aware)
        
        # Pattern 1: Optional steps (explicitly marked)
        if first_token.text.lower() == 'optional':
            return {'is_valid': True, 'message': '', 'suggestions': [], 'severity': 'low'}
        
        # Pattern 2: Conditional steps
        if first_token.lemma_.lower() in ['if', 'when', 'unless']:
            return {'is_valid': True, 'message': '', 'suggestions': [], 'severity': 'low'}
        
        # Pattern 3: Imperative verbs (main procedural pattern)
        if first_token.pos_ == 'VERB' and first_token.dep_ == 'ROOT':
            return {'is_valid': True, 'message': '', 'suggestions': [], 'severity': 'low'}
        
        # Pattern 4: Context-specific valid patterns
        block_type = context.get('block_type', '') if context else ''
        
        # For ordered list items, be more lenient with numbered steps
        if block_type == 'list_item_ordered':
            # Check if starts with a number (e.g., "1. Click the button")
            if first_token.like_num or first_token.text in ['.', ')', ':']:
                # Look for the actual instruction after the number
                for token in doc[1:]:
                    if token.pos_ == 'VERB' and not token.is_stop:
                        return {'is_valid': True, 'message': '', 'suggestions': [], 'severity': 'low'}
        
        # If we reach here, it's not a valid procedural step
        return self._generate_procedural_error_feedback(doc, context)
    
    def _generate_procedural_error_feedback(self, doc, context) -> Dict[str, Any]:
        """Generate specific feedback for invalid procedural steps."""
        first_token = doc[0]
        sentence_text = doc.text
        
        # Analyze why it's not a valid step and provide specific suggestions
        if first_token.pos_ == 'NOUN':
            return {
                'is_valid': False,
                'message': f"Procedural step starts with a noun ('{first_token.text}') instead of an action verb.",
                'suggestions': [
                    f"Start with an imperative verb. For example: 'Configure {sentence_text.lower()}'",
                    "Use active voice with clear action words."
                ],
                'severity': 'medium'
            }
        
        elif first_token.pos_ == 'DET':
            return {
                'is_valid': False,
                'message': f"Procedural step starts with a determiner ('{first_token.text}') instead of an action verb.",
                'suggestions': [
                    f"Start with an imperative verb. For example: 'Select {sentence_text.lower()}'",
                    "Begin with a clear action word."
                ],
                'severity': 'medium'
            }
        
        elif first_token.pos_ == 'VERB' and first_token.dep_ != 'ROOT':
            return {
                'is_valid': False,
                'message': "Procedural step contains a verb but may be in passive voice or complex structure.",
                'suggestions': [
                    "Use simple imperative form: 'Click', 'Enter', 'Select'",
                    "Ensure the action verb is the main verb of the sentence."
                ],
                'severity': 'medium'
            }
        
        else:
            return {
                'is_valid': False,
                'message': f"Procedural step starts with '{first_token.text}' ({first_token.pos_}) instead of an action verb.",
                'suggestions': [
                    "Start with a clear imperative verb (e.g., 'Click', 'Enter', 'Select', 'Configure')",
                    "Use active voice with direct instructions."
                ],
                'severity': 'medium'
            }
