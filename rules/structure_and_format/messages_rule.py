"""
Messages Rule (Enhanced with Evidence-Based Analysis)
Based on IBM Style Guide topic: "Messages"
Enhanced to follow evidence-based rule development methodology for zero false positives.
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class MessagesRule(BaseStructureRule):
    """
    Checks for style issues in error, warning, and informational messages using evidence-based analysis.
    Implements rule-specific evidence calculation for optimal false positive reduction.
    
    Violations detected:
    - Use of exaggerated or unhelpful language in messages
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'messages'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes messages for style violations using evidence-based scoring.
        Each potential violation gets nuanced evidence assessment for precision.
        """
        errors = []
        
        # Linguistic Anchor: Exaggerated adjectives discouraged in messages.
        exaggerated_adjectives = {'catastrophic', 'fatal', 'illegal'}

        for i, sentence in enumerate(sentences):
            for word in exaggerated_adjectives:
                # Use word boundaries for accurate matching.
                for match in re.finditer(rf'\b{word}\b', sentence, re.IGNORECASE):
                    evidence_score = self._calculate_exaggerated_language_evidence(
                        match.group(0), sentence, text, context
                    )
                    
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=self._get_contextual_message('exaggerated_language', evidence_score, context, word=match.group(0)),
                            suggestions=self._generate_smart_suggestions('exaggerated_language', evidence_score, context, word=match.group(0)),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(match.start(), match.end()),
                            flagged_text=match.group(0)
                        ))
        return errors

    # === EVIDENCE CALCULATION METHODS ===

    def _calculate_exaggerated_language_evidence(self, word: str, sentence: str, 
                                               text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential exaggerated language violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            word: The exaggerated word found
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if not context:
            return 0.0  # No context available
        
        # Don't flag exaggerated words in quoted examples
        if self._is_message_word_in_actual_quotes(word, sentence, text, context):
            return 0.0  # Quoted examples are not message language errors
        
        # Don't flag words in technical documentation contexts with approved patterns
        if self._is_message_word_in_technical_context(word, sentence, text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag words in citation or reference context
        if self._is_message_word_in_citation_context(word, sentence, text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'text': word, 'sentence': sentence}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Technical/legal contexts where terms might be appropriate
        if self._is_legitimate_technical_usage(word, sentence, context):
            return 0.0
        
        # Special guard: Quoted content or examples
        if self._is_in_quoted_content(word, sentence):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_exaggerated_language_base_evidence_score(word, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        word_lower = word.lower()
        
        # Some exaggerated words are worse than others
        severe_exaggerations = ['catastrophic', 'fatal']
        if word_lower in severe_exaggerations:
            evidence_score += 0.1
        
        # Check context around the word
        if self._is_in_error_message_context(sentence):
            evidence_score += 0.1  # Error messages especially should avoid exaggeration
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['user_interface', 'messages', 'error_handling']:
            evidence_score += 0.1  # UI messages should be especially careful
        elif content_type in ['legal', 'security']:
            evidence_score -= 0.2  # Legal/security contexts might need stronger language
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_exaggerated_language(evidence_score, word, sentence, context)
        
        # Exaggerated language-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # Exaggerated language is important for clarity but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===

    def _is_legitimate_technical_usage(self, word: str, sentence: str, context: Dict[str, Any]) -> bool:
        """Check if exaggerated word has legitimate technical usage."""
        word_lower = word.lower()
        sentence_lower = sentence.lower()
        
        # "Fatal" is legitimate in programming contexts
        if word_lower == 'fatal':
            programming_indicators = ['error', 'exception', 'crash', 'abort', 'terminate']
            if any(indicator in sentence_lower for indicator in programming_indicators):
                content_type = context.get('content_type', 'general')
                if content_type in ['technical', 'programming', 'api']:
                    return True
        
        # "Illegal" is legitimate in legal/compliance contexts
        if word_lower == 'illegal':
            legal_indicators = ['law', 'legal', 'compliance', 'regulation', 'policy']
            if any(indicator in sentence_lower for indicator in legal_indicators):
                return True
        
        return False

    def _is_in_quoted_content(self, word: str, sentence: str) -> bool:
        """Check if word appears in quoted content."""
        # Simple check for quotes around the word
        word_index = sentence.lower().find(word.lower())
        if word_index == -1:
            return False
        
        # Check for quotes before and after the word
        before_word = sentence[:word_index]
        after_word = sentence[word_index + len(word):]
        
        quote_chars = ['"', "'", '"', '"', '`']
        
        has_opening_quote = any(quote in before_word[-20:] for quote in quote_chars)
        has_closing_quote = any(quote in after_word[:20] for quote in quote_chars)
        
        return has_opening_quote and has_closing_quote

    def _is_in_error_message_context(self, sentence: str) -> bool:
        """Check if sentence appears to be an error message."""
        error_indicators = ['error', 'warning', 'alert', 'failed', 'failure', 'problem', 'issue']
        sentence_lower = sentence.lower()
        
        return any(indicator in sentence_lower for indicator in error_indicators)

    # === CONTEXTUAL MESSAGING AND SUGGESTIONS ===

    def _get_contextual_message(self, violation_type: str, evidence_score: float, 
                               context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual error messages based on violation type and evidence."""
        if violation_type == 'exaggerated_language':
            word = kwargs.get('word', 'word')
            if evidence_score > 0.8:
                return f"Avoid using exaggerated adjectives like '{word}' in messages."
            elif evidence_score > 0.6:
                return f"Consider replacing '{word}' with more neutral language."
            else:
                return f"The word '{word}' may be too strong for this context."
        
        return "Message formatting issue detected."

    def _generate_smart_suggestions(self, violation_type: str, evidence_score: float,
                                  context: Dict[str, Any], **kwargs) -> List[str]:
        """Generate smart suggestions based on violation type and evidence confidence."""
        suggestions = []
        
        if violation_type == 'exaggerated_language':
            word = kwargs.get('word', 'word').lower()
            
            # Word-specific suggestions
            if word == 'fatal':
                suggestions.append("Use 'critical', 'severe', or describe the specific problem instead.")
            elif word == 'catastrophic':
                suggestions.append("Use 'significant', 'major', or describe the specific impact instead.")
            elif word == 'illegal':
                suggestions.append("Use 'invalid', 'not allowed', or 'not supported' instead.")
            else:
                suggestions.append("Use more neutral, descriptive language instead.")
            
            suggestions.append("Focus on the problem and the solution, not the severity.")
            
            if evidence_score > 0.7:
                suggestions.append("Clear, factual language helps users understand and resolve issues effectively.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # === ENHANCED HELPER METHODS FOR 6-STEP EVIDENCE PATTERN ===
    
    def _is_message_word_in_actual_quotes(self, word: str, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the message word actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not sentence:
            return False
        
        # Look for quote pairs that actually enclose the word
        import re
        
        # Find all potential quote pairs
        quote_patterns = [
            (r'"([^"]*)"', '"'),  # Double quotes
            (r"'([^']*)'", "'"),  # Single quotes
            (r'`([^`]*)`', '`')   # Backticks
        ]
        
        for pattern, quote_char in quote_patterns:
            matches = re.finditer(pattern, sentence)
            for match in matches:
                quoted_content = match.group(1)
                if word.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_message_word_in_technical_context(self, word: str, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if message word appears in technical documentation context with approved patterns.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for technical documentation indicators
        technical_indicators = [
            'api documentation', 'technical specification', 'developer guide',
            'software documentation', 'system documentation', 'installation guide',
            'configuration guide', 'troubleshooting guide', 'reference manual'
        ]
        
        for indicator in technical_indicators:
            if indicator in text_lower:
                # Allow some technical-specific message words in strong technical contexts
                if self._is_technical_message_pattern(word, sentence):
                    return True
        
        # Check content type for technical context
        content_type = context.get('content_type', '') if context else ''
        if content_type == 'technical':
            # Common technical message patterns that might be acceptable
            if self._is_technical_message_pattern(word, sentence):
                return True
        
        return False
    
    def _is_message_word_in_citation_context(self, word: str, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if message word appears in citation or reference context.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for citation indicators
        citation_indicators = [
            'according to', 'as stated in', 'reference:', 'cited in',
            'documentation shows', 'manual states', 'guide recommends',
            'specification defines', 'standard requires'
        ]
        
        for indicator in citation_indicators:
            if indicator in text_lower:
                return True
        
        # Check for reference formatting patterns
        if any(pattern in text_lower for pattern in ['see also', 'refer to', 'as described']):
            return True
        
        return False
    
    def _is_technical_message_pattern(self, word: str, sentence: str) -> bool:
        """
        Check if message word follows a technical pattern that might be acceptable.
        """
        word_lower = word.lower()
        sentence_lower = sentence.lower()
        
        # Technical message patterns that might be acceptable
        if word_lower == 'fatal':
            # Fatal is acceptable in programming error contexts
            programming_patterns = [
                'fatal error', 'fatal exception', 'fatal crash', 'fatal signal',
                'fatal assertion', 'fatal abort', 'fatally terminated'
            ]
            for pattern in programming_patterns:
                if pattern in sentence_lower:
                    return True
        
        elif word_lower == 'illegal':
            # Illegal is acceptable in programming/validation contexts
            programming_patterns = [
                'illegal argument', 'illegal operation', 'illegal state',
                'illegal access', 'illegal instruction', 'illegal character'
            ]
            for pattern in programming_patterns:
                if pattern in sentence_lower:
                    return True
        
        elif word_lower == 'catastrophic':
            # Catastrophic is rarely acceptable but might be in system failure contexts
            system_patterns = [
                'catastrophic failure', 'catastrophic error', 'catastrophic system'
            ]
            for pattern in system_patterns:
                if pattern in sentence_lower:
                    return True
        
        return False
    
    def _get_exaggerated_language_base_evidence_score(self, word: str, sentence: str, context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Clearly inappropriate exaggerated words → 0.9 (very specific)
        - Context-dependent exaggerated words → 0.7 (moderate specificity)
        - Borderline exaggerated words → 0.5 (needs context analysis)
        """
        if not word:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_exaggerated_violation(word, sentence):
            return 0.9  # Very specific, clear violation
        elif self._is_pattern_exaggerated_violation(word, sentence):
            return 0.7  # Pattern-based, moderate specificity
        elif self._is_minor_exaggerated_issue(word, sentence):
            return 0.5  # Minor issue, needs context
        else:
            return 0.4  # Possible issue, needs more evidence
    
    def _is_exact_exaggerated_violation(self, word: str, sentence: str) -> bool:
        """
        Check if word represents an exact exaggerated language violation.
        """
        word_lower = word.lower()
        sentence_lower = sentence.lower()
        
        # Clear exaggerations in user-facing messages
        clear_violations = ['catastrophic', 'devastating', 'terrible', 'horrible']
        if word_lower in clear_violations:
            # Check if in user-facing message context
            user_message_indicators = ['error:', 'warning:', 'alert:', 'message:', 'notification:']
            if any(indicator in sentence_lower for indicator in user_message_indicators):
                return True
        
        # Exaggerated severity in simple error messages
        if word_lower in ['fatal', 'critical'] and 'error' in sentence_lower:
            # Check if it's a simple error message (not technical)
            if not self._is_technical_message_pattern(word, sentence):
                return True
        
        return False
    
    def _is_pattern_exaggerated_violation(self, word: str, sentence: str) -> bool:
        """
        Check if word shows a pattern of exaggerated language violation.
        """
        word_lower = word.lower()
        sentence_lower = sentence.lower()
        
        # Moderate exaggerations in general contexts
        moderate_exaggerations = ['illegal', 'invalid', 'forbidden']
        if word_lower in moderate_exaggerations:
            # Check if not in technical context
            if not self._is_technical_message_pattern(word, sentence):
                return True
        
        # Overly dramatic language in informational contexts
        if word_lower in ['catastrophic', 'fatal'] and any(word in sentence_lower for word in ['information', 'note', 'tip']):
            return True
        
        return False
    
    def _is_minor_exaggerated_issue(self, word: str, sentence: str) -> bool:
        """
        Check if word has minor exaggerated language issues.
        """
        word_lower = word.lower()
        sentence_lower = sentence.lower()
        
        # Words that might be borderline exaggerated
        borderline_words = ['serious', 'severe', 'critical']
        if word_lower in borderline_words:
            # Check if in casual context where neutral language would be better
            casual_indicators = ['note', 'tip', 'reminder', 'suggestion']
            if any(indicator in sentence_lower for indicator in casual_indicators):
                return True
        
        return False
    
    def _apply_feedback_clues_exaggerated_language(self, evidence_score: float, word: str, sentence: str, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to exaggerated language in messages.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_messages()
        
        word_lower = word.lower()
        
        # Consistently Accepted Exaggerated Words
        if word_lower in feedback_patterns.get('accepted_exaggerated_words', set()):
            evidence_score -= 0.5  # Users consistently accept this exaggerated word
        
        # Consistently Rejected Suggestions
        if word_lower in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Word-specific acceptance rates
        word_patterns = feedback_patterns.get('exaggerated_word_acceptance', {})
        acceptance_rate = word_patterns.get(word_lower, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance for this word
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Context-specific word acceptance
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_word_acceptance', {})
        
        acceptance_rate = content_patterns.get(word_lower, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Message type-based acceptance
        message_type = self._classify_message_type(sentence)
        message_patterns = feedback_patterns.get('message_type_acceptance', {})
        
        acceptance_rate = message_patterns.get(message_type, {}).get(word_lower, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.2  # Accepted in this message type
        elif acceptance_rate < 0.3:
            evidence_score += 0.1  # Consistently flagged in this message type
        
        # Pattern: Frequency-based adjustment for words
        word_frequency = feedback_patterns.get('word_frequencies', {}).get(word_lower, 0)
        if word_frequency > 10:  # Commonly seen word
            acceptance_rate = feedback_patterns.get('exaggerated_word_acceptance', {}).get(word_lower, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        return evidence_score
    
    def _classify_message_type(self, sentence: str) -> str:
        """
        Classify the type of message for feedback analysis.
        """
        sentence_lower = sentence.lower()
        
        # Error messages
        if any(indicator in sentence_lower for indicator in ['error', 'failed', 'failure', 'exception']):
            return 'error'
        
        # Warning messages
        if any(indicator in sentence_lower for indicator in ['warning', 'caution', 'alert']):
            return 'warning'
        
        # Information messages
        if any(indicator in sentence_lower for indicator in ['info', 'information', 'note', 'tip']):
            return 'info'
        
        # Success messages
        if any(indicator in sentence_lower for indicator in ['success', 'completed', 'done', 'finished']):
            return 'success'
        
        # Confirmation messages
        if any(indicator in sentence_lower for indicator in ['confirm', 'verification', 'validate']):
            return 'confirmation'
        
        # Generic messages
        return 'general'
    
    def _get_cached_feedback_patterns_messages(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for message language.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_exaggerated_words': {
                'critical', 'severe'  # Sometimes acceptable in technical contexts
            },
            'rejected_suggestions': set(),  # Words users don't want flagged
            'exaggerated_word_acceptance': {
                'fatal': 0.3,               # Often acceptable in technical contexts
                'critical': 0.6,            # Sometimes acceptable
                'catastrophic': 0.1,        # Rarely acceptable
                'illegal': 0.4,             # Sometimes acceptable in programming
                'severe': 0.7,              # Often acceptable
                'serious': 0.8,             # Usually acceptable
                'major': 0.9,               # Almost always acceptable
                'significant': 0.95,        # Very acceptable
                'terrible': 0.05,           # Almost never acceptable
                'horrible': 0.05,           # Almost never acceptable
                'devastating': 0.05         # Almost never acceptable
            },
            'technical_word_acceptance': {
                'fatal': 0.8,               # Very acceptable in technical contexts
                'critical': 0.9,            # Very acceptable in technical contexts
                'illegal': 0.7,             # Often acceptable in technical contexts
                'catastrophic': 0.3,        # Sometimes acceptable in system contexts
                'severe': 0.9,              # Very acceptable in technical contexts
                'serious': 0.95,            # Almost always acceptable
                'major': 0.98,              # Almost always acceptable
                'significant': 0.99         # Almost always acceptable
            },
            'user_interface_word_acceptance': {
                'fatal': 0.1,               # Rarely acceptable in UI
                'critical': 0.3,            # Sometimes acceptable in UI
                'illegal': 0.2,             # Rarely acceptable in UI
                'catastrophic': 0.05,       # Almost never acceptable in UI
                'severe': 0.4,              # Sometimes acceptable in UI
                'serious': 0.6,             # Sometimes acceptable in UI
                'major': 0.8,               # Often acceptable in UI
                'significant': 0.9          # Very acceptable in UI
            },
            'error_handling_word_acceptance': {
                'fatal': 0.6,               # Often acceptable in error handling
                'critical': 0.8,            # Very acceptable in error handling
                'illegal': 0.5,             # Sometimes acceptable in error handling
                'catastrophic': 0.2,        # Rarely acceptable in error handling
                'severe': 0.8,              # Very acceptable in error handling
                'serious': 0.9,             # Very acceptable in error handling
                'major': 0.95,              # Almost always acceptable
                'significant': 0.98         # Almost always acceptable
            },
            'legal_word_acceptance': {
                'fatal': 0.4,               # Sometimes acceptable in legal contexts
                'critical': 0.7,            # Often acceptable in legal contexts
                'illegal': 0.9,             # Very acceptable in legal contexts
                'catastrophic': 0.3,        # Sometimes acceptable in legal contexts
                'severe': 0.8,              # Very acceptable in legal contexts
                'serious': 0.9,             # Very acceptable in legal contexts
                'major': 0.95,              # Almost always acceptable
                'significant': 0.98         # Almost always acceptable
            },
            'message_type_acceptance': {
                'error': {
                    'fatal': 0.5,           # Sometimes acceptable in error messages
                    'critical': 0.7,        # Often acceptable in error messages
                    'catastrophic': 0.1,    # Rarely acceptable in error messages
                    'illegal': 0.4,         # Sometimes acceptable in error messages
                    'severe': 0.6           # Sometimes acceptable in error messages
                },
                'warning': {
                    'fatal': 0.3,           # Sometimes acceptable in warnings
                    'critical': 0.6,        # Sometimes acceptable in warnings
                    'catastrophic': 0.1,    # Rarely acceptable in warnings
                    'serious': 0.8,         # Often acceptable in warnings
                    'severe': 0.7           # Often acceptable in warnings
                },
                'info': {
                    'fatal': 0.1,           # Rarely acceptable in info messages
                    'critical': 0.2,        # Rarely acceptable in info messages
                    'catastrophic': 0.05,   # Almost never acceptable in info
                    'serious': 0.4,         # Sometimes acceptable in info
                    'significant': 0.8      # Often acceptable in info
                },
                'general': {
                    'fatal': 0.2,           # Rarely acceptable in general messages
                    'critical': 0.4,        # Sometimes acceptable in general
                    'catastrophic': 0.05,   # Almost never acceptable in general
                    'serious': 0.6,         # Sometimes acceptable in general
                    'severe': 0.5           # Sometimes acceptable in general
                }
            },
            'word_frequencies': {
                'fatal': 150,               # Common word
                'critical': 200,            # Very common word
                'catastrophic': 25,         # Less common word
                'illegal': 100,             # Common word
                'severe': 180,              # Common word
                'serious': 220,             # Very common word
                'major': 300,               # Very common word
                'significant': 250,         # Very common word
                'terrible': 50,             # Less common word
                'horrible': 30,             # Less common word
                'devastating': 20           # Less common word
            }
        }