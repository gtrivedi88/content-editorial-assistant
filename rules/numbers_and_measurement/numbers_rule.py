"""
Numbers Rule
Based on IBM Style Guide topic: "Numbers"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NumbersRule(BaseNumbersRule):
    """
    Checks for general number formatting issues, such as missing comma
    separators and incorrect decimal formatting.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'numbers_general'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for number formatting:
          - Large integers should use thousands separators
          - Decimals <1 should include a leading zero
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        
        no_comma_pattern = re.compile(r'\b\d{5,}\b')
        leading_decimal_pattern = re.compile(r'(?<!\d)\.\d+')

        for i, sent in enumerate(doc.sents):
            # Thousands separators
            for match in no_comma_pattern.finditer(sent.text):
                flagged = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())
                ev_sep = self._calculate_thousands_separator_evidence(flagged, sent, text, context or {})
                if ev_sep > 0.1:
                    message = self._get_contextual_thousands_message(flagged, ev_sep, context or {})
                    suggestions = self._generate_smart_thousands_suggestions(flagged, ev_sep, sent, context or {})
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=message,
                        suggestions=suggestions,
                        severity='low' if ev_sep < 0.7 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=ev_sep,
                        span=span,
                        flagged_text=flagged
                    ))

            # Leading zero for <1 decimals
            for match in leading_decimal_pattern.finditer(sent.text):
                flagged = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())
                ev_dec = self._calculate_leading_decimal_evidence(flagged, sent, text, context or {})
                if ev_dec > 0.1:
                    message = self._get_contextual_leading_decimal_message(flagged, ev_dec, context or {})
                    suggestions = self._generate_smart_leading_decimal_suggestions(flagged, ev_dec, sent, context or {})
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=message,
                        suggestions=suggestions,
                        severity='low' if ev_dec < 0.7 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=ev_dec,
                        span=span,
                        flagged_text=flagged
                    ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_thousands_separator_evidence(self, number_str: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that a large integer should use separators.
        
        Following the 5-step evidence calculation pattern:
        1. Base Evidence Assessment
        2. Linguistic Clues (Micro-Level)
        3. Structural Clues (Meso-Level)
        4. Semantic Clues (Macro-Level)
        5. Feedback Patterns (Learning Clues)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        try:
            digits = len(number_str)
        except Exception:
            digits = 5
        
        if digits < 5:
            return 0.0  # Numbers under 5 digits don't need separators
        
        # Base scales with length beyond 4
        over = max(0, digits - 4)
        evidence_score = min(1.0, 0.5 + min(0.4, over * 0.05))
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_thousands(evidence_score, number_str, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_numbers(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_numbers(evidence_score, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_numbers(evidence_score, number_str, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_leading_decimal_evidence(self, flagged: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that a <1 decimal needs a leading zero.
        
        Following the 5-step evidence calculation pattern:
        1. Base Evidence Assessment
        2. Linguistic Clues (Micro-Level)
        3. Structural Clues (Meso-Level)
        4. Semantic Clues (Macro-Level)
        5. Feedback Patterns (Learning Clues)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.6  # Base evidence for missing leading zero
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_decimal(evidence_score, flagged, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_numbers(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_numbers(evidence_score, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_numbers(evidence_score, flagged, context)
        
        return max(0.0, min(1.0, evidence_score))

    # === LINGUISTIC CLUES (MICRO-LEVEL) ===
    
    def _apply_linguistic_clues_thousands(self, evidence_score: float, number_str: str, sentence) -> float:
        """Apply SpaCy-based linguistic analysis clues for thousands separators."""
        
        sent_lower = sentence.text.lower()
        
        # Check for technical/identifier contexts that don't need separators
        id_indicators = ['id', 'uuid', 'hash', 'checksum', 'serial', 'key', 'token', 'code']
        if any(indicator in sent_lower for indicator in id_indicators):
            evidence_score -= 0.3  # IDs/hashes don't use separators
        
        # Check for version numbers or technical specifications
        version_indicators = ['version', 'v.', 'build', 'revision', 'port', 'address']
        if any(indicator in sent_lower for indicator in version_indicators):
            evidence_score -= 0.2
        
        # Check for mathematical contexts where separators might not be used
        math_indicators = ['calculation', 'formula', 'equation', 'result', 'sum', 'product']
        if any(indicator in sent_lower for indicator in math_indicators):
            evidence_score -= 0.1
        
        # Check for quotes (might be showing exact format or UI text)
        if '"' in sentence.text or "'" in sentence.text:
            evidence_score -= 0.15
        
        # Check for code/monospace indicators
        if '`' in sentence.text:
            evidence_score -= 0.2
        
        # Check for measurement/unit contexts
        measurement_words = ['bytes', 'kb', 'mb', 'gb', 'tb', 'pixels', 'hz', 'mhz', 'ghz']
        if any(word in sent_lower for word in measurement_words):
            evidence_score += 0.1  # Measurements often benefit from separators
        
        # Check for financial contexts (where separators are very important)
        financial_words = ['dollar', 'cost', 'price', 'revenue', 'profit', 'budget', 'expense']
        if any(word in sent_lower for word in financial_words):
            evidence_score += 0.2
        
        # Check surrounding punctuation
        sentence_text = sentence.text
        number_index = sentence_text.find(number_str)
        if number_index > 0:
            prev_char = sentence_text[number_index - 1]
            if prev_char in ['(', '[', '{']:
                evidence_score -= 0.1  # Parenthesized numbers might be references
        
        return evidence_score
    
    def _apply_linguistic_clues_decimal(self, evidence_score: float, flagged: str, sentence) -> float:
        """Apply SpaCy-based linguistic analysis clues for leading zeros in decimals."""
        
        sent_lower = sentence.text.lower()
        
        # Check for code/monospace contexts where format might be specified
        if '`' in sentence.text:
            evidence_score -= 0.25  # Code examples might show specific format
        
        # Check for quotes (might be exact format specification)
        if '"' in sentence.text or "'" in sentence.text:
            evidence_score -= 0.15
        
        # Check for mathematical/statistical contexts
        math_indicators = ['probability', 'coefficient', 'correlation', 'percentage', 'ratio']
        if any(indicator in sent_lower for indicator in math_indicators):
            evidence_score += 0.1  # Math contexts benefit from leading zeros
        
        # Check for measurement contexts
        measurement_indicators = ['measurement', 'precision', 'accuracy', 'tolerance', 'calibration']
        if any(indicator in sent_lower for indicator in measurement_indicators):
            evidence_score += 0.15  # Precision contexts need leading zeros
        
        # Check for range indicators (where consistency is important)
        range_indicators = ['between', 'from', 'to', 'range', 'varies']
        if any(indicator in sent_lower for indicator in range_indicators):
            evidence_score += 0.1
        
        # Check if part of a list or series of numbers
        if ',' in sentence.text and sentence.text.count('.') > 1:
            evidence_score += 0.1  # Multiple decimals should be consistent
        
        # Check for scientific notation context
        if 'e-' in sent_lower or 'e+' in sent_lower:
            evidence_score -= 0.1  # Scientific notation has different rules
        
        return evidence_score

    # === CLUE HELPERS ===

    def _apply_structural_clues_numbers(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for number formatting."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Code contexts have different formatting rules
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.7  # Code often shows exact formats
        elif block_type == 'inline_code':
            evidence_score -= 0.5  # Inline code may show format examples
        
        # Table contexts often need consistent formatting
        elif block_type in ['table_cell', 'table_header']:
            evidence_score += 0.1  # Tables benefit from consistent number formatting
        
        # Heading contexts
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.05  # Headings may use various formats
        
        # List contexts
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.05  # Lists benefit from readable numbers
            
            # Nested lists might be more technical
            list_depth = context.get('list_depth', 1)
            if list_depth > 1:
                evidence_score -= 0.05
        
        # Admonition contexts
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score += 0.05  # Informational contexts benefit from clarity
            elif admonition_type in ['WARNING', 'CAUTION', 'IMPORTANT']:
                evidence_score += 0.1  # Critical information needs clarity
        
        # Quote/citation contexts may preserve original formatting
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.2
        
        # Form/UI contexts need user-friendly formats
        elif block_type in ['form_field', 'ui_element']:
            evidence_score += 0.15
        
        return evidence_score

    def _apply_semantic_clues_numbers(self, evidence_score: float, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for number formatting."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Content type adjustments
        if content_type == 'technical':
            evidence_score -= 0.1  # Technical content may use specialized formats
        elif content_type == 'api':
            evidence_score -= 0.2  # API docs often show exact formats
        elif content_type == 'academic':
            evidence_score += 0.1  # Academic writing prefers standard formatting
        elif content_type == 'legal':
            evidence_score += 0.2  # Legal documents need absolute clarity
        elif content_type == 'marketing':
            evidence_score += 0.05  # Marketing benefits from readable numbers
        elif content_type == 'narrative':
            evidence_score -= 0.05  # Stories may use varied formats
        elif content_type == 'procedural':
            evidence_score += 0.1  # Procedures need clear, consistent formatting
        
        # Domain-specific adjustments
        if domain in ['finance', 'legal', 'medical']:
            evidence_score += 0.15  # Critical domains need precision
        elif domain in ['scientific', 'engineering']:
            evidence_score += 0.1  # Technical domains benefit from clarity
        elif domain in ['software', 'devops']:
            evidence_score -= 0.1  # Tech domains familiar with various formats
        elif domain in ['media', 'entertainment']:
            evidence_score -= 0.05  # Creative domains more flexible
        
        # Audience level adjustments
        if audience in ['beginner', 'general']:
            evidence_score += 0.1  # General audiences need clearer formatting
        elif audience in ['expert', 'developer']:
            evidence_score -= 0.1  # Expert audiences understand various formats
        elif audience == 'international':
            evidence_score += 0.05  # International audiences benefit from standards
        
        # Document length context
        doc_length = len(text.split())
        if doc_length < 100:  # Short documents
            evidence_score -= 0.05  # Brief content may use shorthand
        elif doc_length > 5000:  # Long documents
            evidence_score += 0.05  # Consistency more important in long docs
        
        # Check for financial indicators in the document
        financial_indicators = ['$', '€', '£', '¥', 'USD', 'EUR', 'revenue', 'budget', 'cost']
        text_lower = text.lower()
        if any(indicator.lower() in text_lower for indicator in financial_indicators):
            evidence_score += 0.1  # Financial context benefits from separators
        
        # Check for technical specification indicators
        tech_spec_indicators = ['specification', 'requirements', 'configuration', 'settings']
        if any(indicator in text_lower for indicator in tech_spec_indicators):
            evidence_score -= 0.05  # Technical specs may use exact formats
        
        # Check for data/statistics indicators
        data_indicators = ['data', 'statistics', 'metrics', 'analytics', 'measurement']
        if any(indicator in text_lower for indicator in data_indicators):
            evidence_score += 0.1  # Data contexts benefit from readable numbers
        
        return evidence_score

    def _apply_feedback_clues_numbers(self, evidence_score: float, flagged_text: str, context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for number formatting."""
        
        feedback_patterns = self._get_cached_feedback_patterns_numbers()
        
        flagged_lower = flagged_text.lower()
        
        # Consistently accepted formats
        if flagged_lower in feedback_patterns.get('often_accepted', set()):
            evidence_score -= 0.3  # Strong acceptance pattern
        
        # Consistently flagged formats
        elif flagged_lower in feedback_patterns.get('often_flagged', set()):
            evidence_score += 0.2  # Strong rejection pattern
        
        # Context-specific acceptance patterns
        block_type = context.get('block_type', 'paragraph')
        content_type = context.get('content_type', 'general')
        
        # Block-specific patterns
        block_patterns = feedback_patterns.get(f'{block_type}_number_patterns', {})
        if flagged_lower in block_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif flagged_lower in block_patterns.get('flagged', set()):
            evidence_score += 0.15
        
        # Content-specific patterns
        content_patterns = feedback_patterns.get(f'{content_type}_number_patterns', {})
        if flagged_lower in content_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif flagged_lower in content_patterns.get('flagged', set()):
            evidence_score += 0.15
        
        # Number length patterns
        num_length = len(flagged_text)
        length_patterns = feedback_patterns.get('number_length_acceptance', {})
        
        if num_length in length_patterns:
            acceptance_rate = length_patterns[num_length]
            if acceptance_rate > 0.8:
                evidence_score -= 0.1  # High acceptance for this length
            elif acceptance_rate < 0.3:
                evidence_score += 0.1  # Low acceptance for this length
        
        # Decimal vs integer patterns
        if '.' in flagged_text:
            decimal_acceptance = feedback_patterns.get('decimal_leading_zero_acceptance', 0.8)
            if decimal_acceptance > 0.8:
                evidence_score += 0.1  # High expectation for leading zeros
            elif decimal_acceptance < 0.3:
                evidence_score -= 0.1  # Low expectation for leading zeros
        else:
            separator_acceptance = feedback_patterns.get('thousands_separator_acceptance', 0.7)
            if separator_acceptance > 0.8:
                evidence_score += 0.1  # High expectation for separators
            elif separator_acceptance < 0.3:
                evidence_score -= 0.1  # Low expectation for separators
        
        return evidence_score

    def _get_cached_feedback_patterns_numbers(self) -> Dict[str, Any]:
        """Load feedback patterns for number formatting from cache or feedback analysis."""
        return {
            'often_accepted': {'12345', '123456', '.5', '.25', '.75'},  # Commonly accepted without changes
            'often_flagged': {'1000000', '10000', '.1', '.2', '.3'},  # Commonly flagged for formatting
            'thousands_separator_acceptance': 0.75,  # Generally expected for large numbers
            'decimal_leading_zero_acceptance': 0.85,  # Highly expected for decimals < 1
            'number_length_acceptance': {
                5: 0.3,   # 5-digit numbers: moderate expectation for separators
                6: 0.6,   # 6-digit numbers: higher expectation
                7: 0.8,   # 7-digit numbers: strong expectation
                8: 0.9,   # 8+ digit numbers: very strong expectation
            },
            'paragraph_number_patterns': {
                'accepted': {'12,345', '0.5', '0.25'},
                'flagged': {'12345', '.5', '.25'}
            },
            'technical_number_patterns': {
                'accepted': {'12345', 'v1.2', 'port8080', '.config'},
                'flagged': {'1000000', '.1'}
            },
            'financial_number_patterns': {
                'accepted': {'10,000', '1,000,000', '0.05'},
                'flagged': {'10000', '1000000', '.05'}
            },
            'code_block_number_patterns': {
                'accepted': {'12345', '.5', '0x1234'},  # Code has different rules
                'flagged': set()  # Less flagging in code contexts
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_numbers_message(self, flagged: str, evidence_score: float, context: Dict[str, Any], message_type: str = 'thousands') -> str:
        """Generate context-aware error message for number formatting."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        if message_type == 'thousands':
            if evidence_score > 0.85:
                if domain == 'finance':
                    return f"Financial numbers like '{flagged}' should use thousands separators."
                elif audience in ['beginner', 'general']:
                    return f"Large numbers like '{flagged}' are easier to read with separators."
                else:
                    return "Large numbers should include thousands separators for readability."
            elif evidence_score > 0.6:
                return f"Consider adding separators to '{flagged}' to improve readability."
            elif evidence_score > 0.4:
                return f"Number '{flagged}' may be clearer with thousands separators."
            else:
                return "Consider using thousands separators for large numbers."
        
        else:  # decimal message
            if evidence_score > 0.8:
                if domain in ['finance', 'medical', 'scientific']:
                    return f"Critical contexts require leading zero: use '0{flagged}'."
                elif content_type == 'procedural':
                    return f"For clarity in procedures, use '0{flagged}'."
                else:
                    return f"Include a leading zero for decimals less than 1: '0{flagged}'."
            elif evidence_score > 0.6:
                return f"Consider adding a leading zero to '{flagged}' for clarity."
            elif evidence_score > 0.4:
                return f"Decimal '{flagged}' may be clearer as '0{flagged}'."
            else:
                return "Consider using leading zeros for decimals less than 1."
    
    def _get_contextual_thousands_message(self, flagged: str, ev: float, context: Dict[str, Any]) -> str:
        """Legacy method - redirects to new contextual messaging."""
        return self._get_contextual_numbers_message(flagged, ev, context, 'thousands')

    def _generate_smart_numbers_suggestions(self, flagged: str, evidence_score: float, sentence, context: Dict[str, Any], suggestion_type: str = 'thousands') -> List[str]:
        """Generate context-aware suggestions for number formatting."""
        
        suggestions = []
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        if suggestion_type == 'thousands':
            # High evidence suggestions
            if evidence_score > 0.7:
                try:
                    formatted_number = f"{int(flagged):,}"
                    suggestions.append(f"Format as '{formatted_number}'.")
                except Exception:
                    suggestions.append("Insert thousands separators (commas) for readability.")
                
                if domain == 'finance':
                    suggestions.append("Financial documents require clear number formatting.")
                elif audience in ['beginner', 'general']:
                    suggestions.append("Separators help readers quickly understand large numbers.")
            
            # Medium evidence suggestions
            elif evidence_score > 0.4:
                suggestions.append("Consider adding thousands separators for clarity.")
                if content_type == 'technical':
                    suggestions.append("Unless this is an identifier, use standard formatting.")
            
            # Context-specific suggestions
            if block_type in ['table_cell', 'table_header']:
                suggestions.append("Consistent formatting improves table readability.")
            elif content_type == 'procedural':
                suggestions.append("Clear formatting helps users follow procedures accurately.")
        
        else:  # decimal suggestions
            if evidence_score > 0.6:
                suggestions.append(f"Use '0{flagged}' instead of '{flagged}'.")
                suggestions.append("Leading zeros prevent misreading of decimal values.")
            elif evidence_score > 0.3:
                suggestions.append(f"Consider '0{flagged}' for clarity.")
            
            if domain in ['finance', 'medical', 'scientific']:
                suggestions.append("Critical contexts require unambiguous decimal notation.")
            elif content_type == 'procedural':
                suggestions.append("Procedures benefit from clear, consistent number formats.")
        
        # General guidance if few specific suggestions
        if len(suggestions) < 2:
            if suggestion_type == 'thousands':
                suggestions.append("Follow consistent number formatting throughout the document.")
                suggestions.append("Use locale-appropriate thousands separators.")
            else:
                suggestions.append("Apply leading zero formatting consistently.")
        
        return suggestions[:3]
    
    def _generate_smart_thousands_suggestions(self, flagged: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Legacy method - redirects to new suggestion generator."""
        return self._generate_smart_numbers_suggestions(flagged, ev, sentence, context, 'thousands')

    def _get_contextual_leading_decimal_message(self, flagged: str, ev: float, context: Dict[str, Any]) -> str:
        """Legacy method - redirects to new contextual messaging."""
        return self._get_contextual_numbers_message(flagged, ev, context, 'decimal')

    def _generate_smart_leading_decimal_suggestions(self, flagged: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Legacy method - redirects to new suggestion generator."""
        return self._generate_smart_numbers_suggestions(flagged, ev, sentence, context, 'decimal')
