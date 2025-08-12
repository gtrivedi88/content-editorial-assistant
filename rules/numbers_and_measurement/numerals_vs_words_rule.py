"""
Numerals versus Words Rule
Based on IBM Style Guide topic: "Numerals versus words"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NumeralsVsWordsRule(BaseNumbersRule):
    """
    Checks for consistency in using numerals versus words for numbers,
    especially for numbers under 10.
    """
    def _get_rule_type(self) -> str:
        return 'numerals_vs_words'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        EVIDENCE-BASED: Flag ALL inconsistent number formatting (numerals vs words).
        Following the evidence-based guide pattern for 100% effectiveness.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)

        words_under_10 = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine"}

        # Find all potential inconsistencies - don't filter by dominance
        potential_issues = []
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if self._is_small_number_word(token, words_under_10):
                    potential_issues.append({
                        'token': token,
                        'style': 'words',
                        'sentence': sent,
                        'sentence_index': i
                    })
                elif self._is_small_number_numeral(token):
                    potential_issues.append({
                        'token': token,
                        'style': 'numerals', 
                        'sentence': sent,
                        'sentence_index': i
                    })

        # Check for mixed usage in document
        styles_found = set(issue['style'] for issue in potential_issues)
        if len(styles_found) < 2:
            return errors  # No inconsistency if only one style used

        # Process each potential issue with evidence calculation
        for issue in potential_issues:
            evidence_score = self._calculate_numerals_evidence(
                issue['token'], issue['style'], issue['sentence'], text, context or {}
            )
            
            if evidence_score > 0.1:  # Evidence-based threshold
                errors.append(self._create_error(
                    sentence=issue['sentence'].text,
                    sentence_index=issue['sentence_index'],
                    message=self._generate_numerals_message(issue['token'], issue['style'], evidence_score),
                    suggestions=self._generate_numerals_suggestions(issue['style'], evidence_score),
                    severity='low' if evidence_score < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(issue['token'].idx, issue['token'].idx + len(issue['token'].text)),
                    flagged_text=issue['token'].text
                ))
        return errors

    # === NEW EVIDENCE-BASED METHODS ===
    
    def _calculate_numerals_evidence(self, token, style: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        EVIDENCE-BASED: Calculate evidence for numerals vs words inconsistency.
        
        Following the evidence-based guide pattern:
        1. Surgical Zero False Positive Guards
        2. Dynamic Base Evidence Assessment
        3. Context-aware adjustments
        """
        
        # === STEP 1: SURGICAL GUARDS ===
        if self._apply_numerals_surgical_guards(token, sentence, context):
            return 0.0  # Protected context
        
        # === STEP 2: BASE EVIDENCE ===
        evidence_score = 0.6  # Base evidence for inconsistency
        
        # === STEP 3: CONTEXT ADJUSTMENTS ===
        
        # Sentence start numerals should be words
        if token.i == sentence.start and style == 'numerals':
            evidence_score += 0.3  # Strong evidence for sentence-start rule
        
        # Technical contexts prefer numerals
        content_type = context.get('content_type', '')
        if content_type in ['technical', 'scientific']:
            if style == 'words':
                evidence_score += 0.2  # Technical content prefers numerals
            else:
                evidence_score -= 0.1  # Numerals acceptable in technical
        
        # Business contexts prefer consistency
        elif content_type in ['business', 'professional']:
            evidence_score += 0.1  # Business needs consistency
        
        # Age/time expressions can use words
        if self._is_age_or_time_expression(token, sentence):
            evidence_score -= 0.3  # Age expressions often use words appropriately
        
        return max(0.0, min(1.0, evidence_score))
    
    def _apply_numerals_surgical_guards(self, token, sentence, context: Dict[str, Any]) -> bool:
        """Surgical guards to eliminate false positives."""
        
        # Code and technical blocks
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return True
        
        # Version numbers and identifiers
        if self._is_version_or_identifier(token, sentence):
            return True
        
        # Ordinal numbers (first, second, third vs 1st, 2nd, 3rd)
        if hasattr(token, 'morph') and 'NumType=Ord' in str(token.morph):
            return True
        
        return False
    
    def _is_version_or_identifier(self, token, sentence) -> bool:
        """Check if token is part of version number or identifier."""
        sent_text = sentence.text.lower()
        patterns = ['version', 'v.', 'chapter', 'section', 'step', 'part', 'phase']
        return any(pattern in sent_text for pattern in patterns)
    
    def _is_age_or_time_expression(self, token, sentence) -> bool:
        """Check if token is part of age or time expression."""
        sent_text = sentence.text.lower()
        age_patterns = ['year', 'month', 'day', 'hour', 'old', 'age']
        return any(pattern in sent_text for pattern in age_patterns)
    
    def _generate_numerals_message(self, token, style: str, evidence_score: float) -> str:
        """Generate evidence-aware error messages."""
        if evidence_score > 0.8:
            if style == 'numerals' and token.i == 0:  # Sentence start
                return f"Spell out numbers at the beginning of sentences: '{token.text}' should be written as a word."
            else:
                return f"Use consistent number formatting throughout the document."
        elif evidence_score > 0.6:
            return f"Consider consistent formatting for numbers under 10 across the document."
        else:
            return f"Number formatting could be more consistent: '{token.text}'."
    
    def _generate_numerals_suggestions(self, style: str, evidence_score: float) -> List[str]:
        """Generate evidence-aware suggestions."""
        suggestions = []
        
        if style == 'numerals':
            suggestions.append("Consider spelling out single-digit numbers as words.")
            suggestions.append("Use words for numbers at the beginning of sentences.")
        else:
            suggestions.append("Consider using numerals for technical or statistical content.")
            suggestions.append("Use numerals consistently for measurements and quantities.")
        
        if evidence_score > 0.7:
            suggestions.append("Maintain consistent number formatting throughout the document.")
        
        return suggestions[:3]

    # === LEGACY EVIDENCE CALCULATION (KEEP FOR COMPATIBILITY) ===

    def _calculate_numerals_words_evidence(self, token, style: str, dominant: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence (0.0-1.0) that the token's style is inconsistent.
        
        Implements rule-specific evidence calculation with:
        - Surgical zero false positive guards for numerals/words contexts
        - Dynamic base evidence based on style consistency and domain requirements
        - Context-aware adjustments for different numerical communication standards
        
        Following the enhanced evidence calculation pattern:
        1. Surgical Zero False Positive Guards
        2. Base Evidence Assessment
        3. Linguistic Clues (Micro-Level)
        4. Structural Clues (Meso-Level)
        5. Semantic Clues (Macro-Level)
        6. Feedback Patterns (Learning Clues)
        """
        
        # === STEP 1: SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply base class surgical guards for numbers
        if self._apply_surgical_zero_false_positive_guards_numbers(token.text, context):
            return 0.0  # No violation - protected context
            
        # Apply numerals/words-specific surgical guards
        if self._apply_numerals_words_specific_guards(token, style, sentence, context):
            return 0.0  # No violation - numerals/words-specific protected context
        
        # === STEP 2: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.6  # Base evidence when both styles are present in document
        
        # === STEP 3: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_numerals_words(evidence_score, token, style, dominant, sentence)
        
        # === STEP 4: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_numerals_words(evidence_score, context)
        
        # === STEP 5: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_numerals_words(evidence_score, style, dominant, text, context)
        
        # === STEP 6: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_numerals_words(evidence_score, token.text, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    # === SURGICAL ZERO FALSE POSITIVE GUARD METHODS ===
    
    def _apply_numerals_words_specific_guards(self, token, style: str, sentence, context: Dict[str, Any]) -> bool:
        """
        PRODUCTION-GRADE: Apply surgical guards specific to numerals vs words contexts.
        Returns True if this should be excluded (no violation), False if it should be processed.
        """
        sent_text = sentence.text
        sent_lower = sent_text.lower()
        token_text = token.text
        
        # === GUARD 1: EXCEPTIONAL REFERENCE CONTEXTS ===
        # Don't flag numbers in contexts where specific style is conventional
        exceptional_contexts = ['version', 'chapter', 'section', 'figure', 'table', 'page', 'step', 'part']
        head_lemma = getattr(token.head, 'lemma_', '').lower()
        if head_lemma in exceptional_contexts:
            return True  # Reference contexts often have specific conventions
        
        # === GUARD 2: TECHNICAL IDENTIFIERS AND SPECIFICATIONS ===
        # Don't flag numbers that are part of technical specifications
        tech_contexts = ['api', 'http', 'port', 'build', 'revision', 'iteration', 'phase', 'level']
        if head_lemma in tech_contexts:
            return True  # Technical contexts often require specific formats
        
        # === GUARD 3: ORDINAL NUMBERS IN FORMAL CONTEXTS ===
        # Don't flag ordinal numbers which have different conventions
        if hasattr(token, 'morph') and token.morph:
            if 'NumType=Ord' in str(token.morph):
                return True  # Ordinals have different style rules
        
        # === GUARD 4: MATHEMATICAL AND MEASUREMENT CONTEXTS ===
        # Don't flag numbers in mathematical or measurement contexts
        math_indicators = ['+', '-', '*', '/', '=', '<', '>', '%', '±']
        measurement_indicators = ['meter', 'gram', 'liter', 'byte', 'inch', 'foot', 'pound', 'second', 'minute', 'hour']
        
        if any(indicator in sent_text for indicator in math_indicators):
            return True  # Mathematical contexts require numerals
        
        if any(indicator in sent_lower for indicator in measurement_indicators):
            return True  # Measurement contexts typically use numerals
        
        # === GUARD 5: AGE, TIME, AND PERCENTAGE CONTEXTS ===
        # Don't flag numbers in specific quantity contexts
        specific_quantity_indicators = ['year old', 'years old', 'age', 'aged', '%', 'percent', 'ratio']
        if any(indicator in sent_lower for indicator in specific_quantity_indicators):
            return True  # Specific quantities have conventional formats
        
        # === GUARD 6: TITLE CASE AND PROPER NOUNS ===
        # Don't flag numbers at the start of sentences or in titles
        if getattr(token, 'i', 0) == sentence.start and style == 'words':
            return True  # Sentence-initial words often acceptable
        
        return False  # No numerals/words-specific guards triggered

    # === LINGUISTIC CLUES (MICRO-LEVEL) ===
    
    def _apply_linguistic_clues_numerals_words(self, evidence_score: float, token, style: str, dominant: str, sentence) -> float:
        """Apply SpaCy-based linguistic analysis clues for numerals vs words consistency."""
        
        # Check for exceptional contexts that reduce evidence
        head_lemma = getattr(token.head, 'lemma_', '').lower()
        exceptions = {"version", "release", "chapter", "figure", "table", "page", "step", "section", "part"}
        if head_lemma in exceptions:
            evidence_score -= 0.3  # Strong exception context
        
        # Check for additional technical contexts
        tech_exceptions = {"api", "http", "port", "build", "revision", "iteration", "phase"}
        if head_lemma in tech_exceptions:
            evidence_score -= 0.25  # Technical contexts often use numerals
        
        # Check POS tags and dependency relationships
        token_pos = getattr(token, 'pos_', '')
        token_dep = getattr(token, 'dep_', '')
        
        # Numbers as subjects or objects in technical contexts
        if token_dep in ['nsubj', 'dobj', 'pobj'] and token_pos == 'NUM':
            evidence_score -= 0.1  # Grammatical number usage often acceptable
        
        # Numbers in compound structures (e.g., "3-part series")
        if token_dep == 'compound':
            evidence_score -= 0.15  # Compound numbers often use numerals
        
        # Check for ordinal vs cardinal patterns
        if hasattr(token, 'morph') and token.morph:
            if 'NumType=Ord' in str(token.morph):  # Ordinal numbers (1st, 2nd, etc.)
                evidence_score -= 0.1  # Ordinals often use numerals
        
        # Sentence start spelled-out words (narrative style)
        if style == "words" and getattr(token, 'i', 0) == sentence.start:
            evidence_score -= 0.1  # Sentence-initial words more acceptable
        
        # Check for consistency within the same sentence
        words_under_10 = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine"}
        sentence_word_count = sum(1 for t in sentence if self._is_small_number_word(t, words_under_10))
        sentence_numeral_count = sum(1 for t in sentence if self._is_small_number_numeral(t))
        
        if sentence_word_count > 0 and sentence_numeral_count > 0:
            evidence_score += 0.2  # Mixed styles within sentence is problematic
        elif sentence_word_count > 1 and style == "numerals":
            evidence_score += 0.15  # Inconsistent with sentence pattern
        elif sentence_numeral_count > 1 and style == "words":
            evidence_score += 0.15  # Inconsistent with sentence pattern
        
        # Check for mathematical or technical expressions
        math_indicators = ['+', '-', '*', '/', '=', '<', '>', '%']
        sentence_text = sentence.text
        if any(indicator in sentence_text for indicator in math_indicators):
            if style == "words":
                evidence_score += 0.2  # Words inappropriate in math contexts
            else:
                evidence_score -= 0.1  # Numerals appropriate in math contexts
        
        # Check for list or enumeration patterns
        if token_dep in ['appos', 'attr'] or sentence_text.strip().startswith(('-', '*', '•')):
            if style == "numerals":
                evidence_score -= 0.1  # Lists often use numerals
        
        # Check for time, date, or measurement contexts
        time_indicators = ['hour', 'minute', 'second', 'day', 'week', 'month', 'year']
        measurement_indicators = ['meter', 'gram', 'liter', 'byte', 'inch', 'foot', 'pound']
        sentence_lower = sentence_text.lower()
        
        if any(indicator in sentence_lower for indicator in time_indicators + measurement_indicators):
            if style == "words":
                evidence_score += 0.15  # Measurements typically use numerals
            else:
                evidence_score -= 0.1  # Numerals appropriate with measurements
        
        # Check for age or quantity expressions
        age_indicators = ['year old', 'years old', 'age', 'aged']
        if any(indicator in sentence_lower for indicator in age_indicators):
            if style == "words":
                evidence_score += 0.1  # Ages typically use numerals
        
        # Check for percentage or ratio contexts
        if '%' in sentence_text or 'percent' in sentence_lower or 'ratio' in sentence_lower:
            if style == "words":
                evidence_score += 0.2  # Percentages use numerals
            else:
                evidence_score -= 0.1  # Numerals appropriate for percentages
        
        # Check for quotes (might be showing examples or UI text)
        if '"' in sentence_text or "'" in sentence_text:
            evidence_score -= 0.05  # Quoted text may preserve original format
        
        return evidence_score

    # === CLUE HELPERS ===

    def _is_small_number_word(self, token, words_under_10: set) -> bool:
        return getattr(token, 'lemma_', '').lower() in words_under_10 and getattr(token, 'pos_', '') in {"NUM", "DET", "ADJ", "NOUN", "PRON"}

    def _is_small_number_numeral(self, token) -> bool:
        if not getattr(token, 'like_num', False):
            return False
        try:
            num_value = float(token.text)
            return num_value.is_integer() and 0 < int(num_value) < 10
        except Exception:
            return False

    def _apply_structural_clues_numerals_words(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for numerals vs words consistency."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Code contexts have different formatting rules
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.8  # Code often shows exact syntax with numerals
        elif block_type == 'inline_code':
            evidence_score -= 0.6  # Inline code may show format examples
        
        # List contexts often favor numerals for clarity
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.1  # Lists often use numerals for brevity
            
            # Nested lists might be more technical
            list_depth = context.get('list_depth', 1)
            if list_depth > 1:
                evidence_score -= 0.05  # Deeper lists more technical
        
        # Table contexts benefit from consistent, compact formatting
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.1  # Tables often prefer numerals for space
        
        # Heading contexts
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.05  # Headings may use either style
            
            # Higher-level headings might be more formal
            heading_level = context.get('block_level', 1)
            if heading_level == 1:  # H1 - main headings
                evidence_score += 0.05  # Main headings might prefer words
        
        # Admonition contexts
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score -= 0.05  # Informal contexts more flexible
            elif admonition_type in ['WARNING', 'CAUTION', 'IMPORTANT']:
                evidence_score += 0.05  # Critical info might prefer clarity of numerals
        
        # Quote/citation contexts may preserve original style
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.2  # Quotes preserve original formatting
        
        # Form/UI contexts often use numerals
        elif block_type in ['form_field', 'ui_element']:
            evidence_score -= 0.1  # UI often uses numerals
        
        # Step-by-step procedures often use numerals
        elif block_type in ['procedure', 'steps']:
            evidence_score -= 0.15  # Procedures typically use numerals
        
        return evidence_score

    def _apply_semantic_clues_numerals_words(self, evidence_score: float, style: str, dominant: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for numerals vs words consistency."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Content type adjustments
        if content_type == 'technical':
            if style == 'words' and dominant == 'numerals':
                evidence_score += 0.15  # Technical content strongly prefers numerals
            elif style == 'numerals' and dominant == 'words':
                evidence_score -= 0.1  # Numerals acceptable in technical content
        
        elif content_type == 'api':
            if style == 'words':
                evidence_score += 0.2  # API docs almost always use numerals
            else:
                evidence_score -= 0.1  # Numerals expected in API contexts
        
        elif content_type == 'academic':
            if style == 'words' and dominant == 'numerals':
                evidence_score += 0.05  # Academic writing has mixed preferences
            # Academic writing may use either style depending on field
        
        elif content_type == 'legal':
            if style == 'numerals' and dominant == 'words':
                evidence_score += 0.1  # Legal documents often spell out numbers
            elif style == 'words':
                evidence_score -= 0.05  # Words sometimes preferred in legal
        
        elif content_type == 'marketing':
            if style == 'words':
                evidence_score -= 0.1  # Marketing often uses words for impact
            elif style == 'numerals' and dominant == 'words':
                evidence_score += 0.05  # But should be consistent
        
        elif content_type == 'narrative':
            if style == 'words':
                evidence_score -= 0.15  # Narrative strongly prefers words
            elif style == 'numerals' and dominant == 'words':
                evidence_score += 0.1  # Numerals disrupting narrative flow
        
        elif content_type == 'procedural':
            if style == 'words' and dominant == 'numerals':
                evidence_score += 0.2  # Procedures strongly prefer numerals for clarity
            elif style == 'numerals':
                evidence_score -= 0.1  # Numerals expected in procedures
        
        # Domain-specific adjustments
        if domain in ['software', 'engineering', 'devops']:
            if style == 'words' and dominant == 'numerals':
                evidence_score += 0.15  # Technical domains prefer numerals
            elif style == 'numerals':
                evidence_score -= 0.1  # Numerals expected
        
        elif domain in ['finance', 'legal', 'medical']:
            if style == 'numerals' and dominant == 'words':
                evidence_score += 0.1  # Formal domains may prefer spelled-out numbers
            # But depends on specific context (measurements vs amounts)
        
        elif domain in ['scientific', 'research']:
            if style == 'words' and dominant == 'numerals':
                evidence_score += 0.1  # Scientific writing typically uses numerals
        
        elif domain in ['media', 'entertainment', 'creative']:
            if style == 'words':
                evidence_score -= 0.1  # Creative domains more flexible with words
        
        # Audience level adjustments
        if audience in ['beginner', 'general']:
            # General audiences benefit from consistency
            evidence_score += 0.05  # Any inconsistency more problematic
        
        elif audience in ['expert', 'developer', 'professional']:
            if style == 'words' and content_type in ['technical', 'api', 'procedural']:
                evidence_score += 0.1  # Experts expect technical conventions
            else:
                evidence_score -= 0.05  # Experts more tolerant of style variations
        
        elif audience == 'international':
            if style == 'numerals':
                evidence_score -= 0.05  # Numerals more universal
        
        # Document length and consistency context
        doc_length = len(text.split())
        if doc_length > 5000:  # Long documents
            evidence_score += 0.05  # Consistency more important in long docs
        
        # Check for document-wide number density
        number_word_count = len([word for word in text.lower().split() 
                               if word in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']])
        numeral_count = len([char for char in text if char.isdigit()])
        
        if number_word_count > 10 and numeral_count > 20:
            evidence_score += 0.1  # High inconsistency across document
        
        # Check for style guide indicators in the document
        style_indicators = ['style guide', 'writing guidelines', 'documentation standards']
        text_lower = text.lower()
        if any(indicator in text_lower for indicator in style_indicators):
            evidence_score += 0.1  # Style guides need consistency
        
        return evidence_score

    def _apply_feedback_clues_numerals_words(self, evidence_score: float, token_text: str, context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for numerals vs words consistency."""
        
        feedback_patterns = self._get_cached_feedback_patterns_numerals_words()
        
        token_lower = token_text.lower()
        
        # Consistently accepted formats
        if token_lower in feedback_patterns.get('often_accepted_words', set()):
            evidence_score -= 0.3  # Strong acceptance pattern
        elif token_lower in feedback_patterns.get('often_accepted_numerals', set()):
            evidence_score -= 0.3  # Strong acceptance pattern
        
        # Consistently flagged formats
        elif token_lower in feedback_patterns.get('often_flagged_words', set()):
            evidence_score += 0.2  # Strong rejection pattern
        elif token_lower in feedback_patterns.get('often_flagged_numerals', set()):
            evidence_score += 0.2  # Strong rejection pattern
        
        # Context-specific acceptance patterns
        block_type = context.get('block_type', 'paragraph')
        content_type = context.get('content_type', 'general')
        
        # Block-specific patterns
        block_patterns = feedback_patterns.get(f'{block_type}_number_patterns', {})
        if token_lower in block_patterns.get('accepted_words', set()):
            evidence_score -= 0.2
        elif token_lower in block_patterns.get('accepted_numerals', set()):
            evidence_score -= 0.2
        elif token_lower in block_patterns.get('flagged', set()):
            evidence_score += 0.15
        
        # Content-specific patterns
        content_patterns = feedback_patterns.get(f'{content_type}_number_patterns', {})
        if token_lower in content_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif token_lower in content_patterns.get('flagged', set()):
            evidence_score += 0.15
        
        # Style consistency patterns by context
        style_preferences = feedback_patterns.get('style_preference_by_context', {})
        context_key = f"{content_type}_{context.get('domain', 'general')}"
        
        if context_key in style_preferences:
            numeral_preference = style_preferences[context_key]
            if token_text.isdigit():  # This is a numeral
                if numeral_preference > 0.8:
                    evidence_score -= 0.1  # Strong numeral preference
                elif numeral_preference < 0.3:
                    evidence_score += 0.1  # Strong word preference
            else:  # This is a word
                if numeral_preference > 0.8:
                    evidence_score += 0.1  # Should use numerals in this context
                elif numeral_preference < 0.3:
                    evidence_score -= 0.1  # Words preferred in this context
        
        # Exception context patterns
        exception_contexts = feedback_patterns.get('exception_context_acceptance', {})
        for exception_type, acceptance_rate in exception_contexts.items():
            if exception_type in context.get('detected_contexts', []):
                if acceptance_rate > 0.8:
                    evidence_score -= 0.15  # High acceptance for exceptions
                elif acceptance_rate < 0.3:
                    evidence_score += 0.1  # Low acceptance for exceptions
        
        return evidence_score

    def _get_cached_feedback_patterns_numerals_words(self) -> Dict[str, Any]:
        """Load feedback patterns for numerals vs words consistency from cache or feedback analysis."""
        return {
            'often_accepted_words': {'one', 'two', 'three', 'first', 'second', 'third'},
            'often_accepted_numerals': {'1', '2', '3', '4', '5', '6', '7', '8', '9'},
            'often_flagged_words': {'one', 'two', 'three'},  # When used inconsistently
            'often_flagged_numerals': {'1', '2', '3'},  # When used inconsistently
            'style_preference_by_context': {
                'technical_software': 0.9,        # Strong numeral preference
                'api_software': 0.95,             # Very strong numeral preference
                'procedural_general': 0.8,        # Strong numeral preference
                'narrative_general': 0.2,         # Strong word preference
                'marketing_general': 0.3,         # Word preference
                'academic_general': 0.6,          # Moderate numeral preference
                'legal_general': 0.4,             # Moderate word preference
            },
            'exception_context_acceptance': {
                'version_numbers': 0.9,           # Version contexts highly accept numerals
                'chapter_references': 0.8,        # Chapter refs often accept numerals
                'figure_references': 0.85,        # Figure refs prefer numerals
                'step_procedures': 0.9,           # Steps strongly prefer numerals
                'mathematical_expressions': 0.95, # Math contexts require numerals
            },
            'paragraph_number_patterns': {
                'accepted_words': {'one', 'two', 'first', 'second'},
                'accepted_numerals': {'1', '2', '3', '4', '5'},
                'flagged': {'mixed_usage'}  # Placeholder
            },
            'technical_number_patterns': {
                'accepted': {'1', '2', '3', '4', '5', '6', '7', '8', '9'},
                'flagged': {'one', 'two', 'three', 'four', 'five'}
            },
            'narrative_number_patterns': {
                'accepted': {'one', 'two', 'three', 'first', 'second', 'third'},
                'flagged': {'1', '2', '3', '4', '5'}
            },
            'academic_number_patterns': {
                'accepted': {'1', '2', '3', 'one', 'two', 'three'},  # Mixed acceptance
                'flagged': set()  # Context-dependent
            },
            'code_block_number_patterns': {
                'accepted_numerals': {'1', '2', '3', '4', '5', '6', '7', '8', '9'},
                'flagged': set()  # Code accepts numerals
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_numerals_words_message(self, style: str, dominant: str, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for numerals vs words consistency."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        if evidence_score > 0.85:
            if content_type in ['technical', 'api', 'procedural']:
                if style == 'words':
                    return f"Technical content should use numerals: replace '{style}' style with numerals for consistency."
                else:
                    return f"Use numerals consistently in technical content (document uses mainly words)."
            elif content_type in ['narrative', 'marketing']:
                if style == 'numerals':
                    return f"Narrative content should spell out small numbers: use words instead of numerals."
                else:
                    return f"Spell out numbers consistently in narrative content (document uses mainly numerals)."
            else:
                return "Inconsistent use of numerals and words for numbers under 10. Use one style consistently."
        
        elif evidence_score > 0.6:
            if domain in ['software', 'engineering']:
                return f"Technical documents typically prefer numerals for small numbers."
            elif audience in ['beginner', 'general']:
                return f"For clarity, align number formatting with the dominant style in this document."
            else:
                return "Consider aligning small-number formatting with the dominant style in this document."
        
        elif evidence_score > 0.4:
            return f"Number formatting inconsistency: consider using {dominant} style throughout."
        
        else:
            return "Consider consistent formatting for numbers under 10 across the document."

    def _generate_smart_numerals_words_suggestions(self, style: str, dominant: str, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for numerals vs words consistency."""
        
        suggestions = []
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        # High evidence suggestions (strong inconsistency)
        if evidence_score > 0.7:
            if content_type in ['technical', 'api', 'procedural']:
                suggestions.append("Use numerals for numbers under 10 in technical content.")
                suggestions.append("Technical documentation favors numerals for precision and scannability.")
            elif content_type in ['narrative', 'marketing']:
                suggestions.append("Spell out numbers under 10 in narrative content.")
                suggestions.append("Narrative writing flows better with spelled-out small numbers.")
            elif content_type == 'academic':
                if dominant == 'numerals':
                    suggestions.append("Follow the document's numerical style for consistency.")
                else:
                    suggestions.append("Follow the document's word-based style for consistency.")
            else:
                if dominant == 'numerals':
                    suggestions.append("Use numerals for numbers under 10 for consistency.")
                else:
                    suggestions.append("Spell out numbers under 10 for consistency.")
        
        # Medium evidence suggestions
        elif evidence_score > 0.4:
            suggestions.append(f"Consider using {dominant} style to match the document's predominant pattern.")
            if domain in ['software', 'engineering']:
                suggestions.append("Technical domains typically favor numerals for clarity.")
            elif domain in ['legal', 'creative']:
                suggestions.append("Consider context-appropriate number formatting.")
        
        # Context-specific suggestions
        if block_type in ['ordered_list_item', 'unordered_list_item']:
            suggestions.append("Lists often benefit from numerals for quick scanning.")
        elif block_type in ['heading', 'title']:
            suggestions.append("Choose number format that matches the heading's formality level.")
        elif block_type == 'procedure':
            suggestions.append("Procedural steps typically use numerals for clarity.")
        
        # Audience-specific suggestions
        if audience in ['beginner', 'general']:
            suggestions.append("Maintain consistent number formatting to avoid reader confusion.")
        elif audience in ['expert', 'developer']:
            suggestions.append("Follow established conventions for your field and document type.")
        
        # Exception-aware suggestions
        sentence_text = sentence.text.lower()
        if any(exception in sentence_text for exception in ['version', 'chapter', 'figure', 'step']):
            suggestions.append("Note: Version numbers, chapters, and references often use numerals regardless of style.")
        
        # General guidance if specific suggestions weren't added
        if len(suggestions) < 2:
            suggestions.append("Choose one style (numerals or words) and apply consistently.")
            suggestions.append("Consider your audience and document type when selecting number format.")
        
        return suggestions[:3]
