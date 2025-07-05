"""
Procedures Rule
Based on IBM Style Guide topic: "Procedures"
"""
from typing import List, Dict, Any, Optional
from .base_structure_rule import BaseStructureRule

class ProceduresRule(BaseStructureRule):
    """
    Checks for style issues in procedural steps. This rule identifies procedural
    contexts and ensures that steps begin with an imperative verb, while correctly
    handling optional and conditional steps to reduce false positives.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'procedures'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes procedural content using enhanced detection methods.
        """
        errors = []
        if not nlp:
            return errors

        # Enhanced procedural detection - check both context and content patterns
        is_procedural_content = self._is_procedural_content(text, context)
        
        if is_procedural_content:
            # Get step number from context if available (for ordered list items)
            step_number = context.get('step_number', 1) if context else 1
            
            for i, sentence in enumerate(sentences):
                doc = nlp(sentence)
                
                # Analyze each sentence as a potential procedural step
                step_analysis = self._analyze_procedural_step(doc, context, step_number)
                
                if not step_analysis['is_valid']:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=step_analysis['message'],
                        suggestions=step_analysis['suggestions'],
                        severity=step_analysis['severity']
                    ))
                
                # Only increment step number if not using context-provided step number
                if not (context and context.get('step_number')):
                    step_number += 1
        
        return errors

    def _is_procedural_content(self, text: str, context: Optional[dict] = None) -> bool:
        """
        Enhanced method to detect procedural content using both context and content analysis.
        """
        # Method 1: Context-based detection (existing approach)
        context_indicates_procedural = False
        if context:
            # Check if this is a procedural list item
            block_type = context.get('block_type', '')
            if block_type in ['list_item_ordered', 'list_item']:
                context_indicates_procedural = True
            
            # Check if this is content in a procedures/instructions section
            if (context.get('parent_type') == 'section' and 
                any(keyword in text.lower() for keyword in ['procedure', 'steps', 'instructions', 'installation', 'configuration'])):
                context_indicates_procedural = True
        
        # Method 2: Content-based detection (new approach)
        content_indicates_procedural = self._detect_procedural_patterns(text)
        
        return context_indicates_procedural or content_indicates_procedural

    def _detect_procedural_patterns(self, text: str) -> bool:
        """
        Detect procedural content based on text patterns.
        """
        text_lower = text.lower()
        
        # Pattern 1: Sequential numbered/bulleted lists that look like steps
        if any(pattern in text_lower for pattern in [
            'first', 'second', 'third', 'next', 'then', 'finally',
            'step 1', 'step 2', 'step 3', '1.', '2.', '3.',
            'install', 'configure', 'setup', 'download', 'uninstall'
        ]):
            return True
        
        # Pattern 2: Imperative/instructional language patterns
        instructional_patterns = [
            'should be', 'must be', 'need to', 'have to',
            'downloading', 'configuration', 'installation',
            'updating', 'setting', 'creating', 'removing'
        ]
        
        if any(pattern in text_lower for pattern in instructional_patterns):
            return True
        
        return False

    def _analyze_procedural_step(self, doc, context, step_number: int) -> Dict[str, Any]:
        """
        Analyze a sentence as a procedural step using enhanced linguistic analysis.
        """
        if not doc:
            return {
                'is_valid': False,
                'message': f'PROCEDURES: Step {step_number} is empty.',
                'suggestions': ['Provide a clear procedural instruction.'],
                'severity': 'medium'
            }
        
        first_token = doc[0]
        
        # Valid procedural step patterns
        
        # Pattern 1: Optional steps (explicitly marked)
        if first_token.text.lower() == 'optional':
            return {'is_valid': True, 'message': '', 'suggestions': [], 'severity': 'low'}
        
        # Pattern 2: Conditional steps
        if first_token.lemma_.lower() in ['if', 'when', 'unless']:
            return {'is_valid': True, 'message': '', 'suggestions': [], 'severity': 'low'}
        
        # Pattern 3: Imperative verbs (main procedural pattern)
        if self._is_imperative_verb(first_token):
            return {'is_valid': True, 'message': '', 'suggestions': [], 'severity': 'low'}
        
        # Pattern 4: Context-specific valid patterns
        block_type = context.get('block_type', '') if context else ''
        
        # For ordered list items, check if starts with a number
        if block_type == 'list_item_ordered':
            if first_token.like_num or first_token.text in ['.', ')', ':']:
                # Look for the actual instruction after the number
                for token in doc[1:]:
                    if self._is_imperative_verb(token):
                        return {'is_valid': True, 'message': '', 'suggestions': [], 'severity': 'low'}
        
        # If we reach here, it's not a valid procedural step
        return self._generate_procedural_error_feedback(step_number, doc, context)
    
    def _is_imperative_verb(self, token) -> bool:
        """
        Check if a token is an imperative verb.
        """
        if not token or token.pos_ != 'VERB':
            return False
        
        # Exclude gerunds (VBG) and participles (VBN) - these are not imperative
        if token.tag_ in ['VBG', 'VBN']:
            return False
        
        # Check if it's a root verb (main action of the sentence)
        if token.dep_ == 'ROOT':
            return True
        
        # Check if it's explicitly marked as imperative
        if hasattr(token, 'morph') and 'Mood=Imp' in str(token.morph):
            return True
        
        return False
    
    def _generate_procedural_error_feedback(self, step_number: int, doc, context) -> Dict[str, Any]:
        """Generate specific feedback for invalid procedural steps."""
        first_token = doc[0]
        sentence_text = doc.text
        
        # Generate the exact error message format expected by the user
        error_message = f"PROCEDURES: Step {step_number} does not begin with an imperative verb."
        
        # Analyze why it's not a valid step and provide specific suggestions
        suggestions = []
        
        if first_token.pos_ == 'NOUN':
            suggestions = [
                f"Start with an imperative verb. For example: 'Configure {sentence_text.lower()}'",
                "Use active voice with clear action words like 'Install', 'Download', 'Configure'."
            ]
        
        elif first_token.pos_ == 'DET':
            suggestions = [
                f"Start with an imperative verb. For example: 'Uninstall {sentence_text.lower()}'",
                "Begin with a clear action word like 'Remove', 'Select', 'Enter'."
            ]
        
        elif first_token.pos_ == 'VERB' and first_token.tag_ == 'VBG':  # Gerund form
            verb_root = first_token.lemma_
            suggestions = [
                f"Use imperative form: '{verb_root.capitalize()}' instead of '{first_token.text}'",
                "Use simple imperative verbs like 'Download', 'Install', 'Configure'."
            ]
        
        else:
            suggestions = [
                "Start with a clear imperative verb (e.g., 'Click', 'Enter', 'Select', 'Configure')",
                "Use active voice with direct instructions."
            ]
        
        return {
            'is_valid': False,
            'message': error_message,
            'suggestions': suggestions,
            'severity': 'medium'
        }
