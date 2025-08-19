"""
Glossaries Rule (Enhanced with Evidence-Based Analysis)
Based on IBM Style Guide topic: "Glossaries"
Enhanced to follow evidence-based rule development methodology for zero false positives.
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class GlossariesRule(BaseStructureRule):
    """
    Checks for glossary formatting issues using evidence-based analysis with surgical precision.
    Implements rule-specific evidence calculation for optimal false positive reduction.
    
    Violations detected:
    - Terms that should be lowercase but are capitalized
    - Definitions that should start with capital letters
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'glossaries'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes glossaries for formatting violations using evidence-based scoring.
        Each potential violation gets nuanced evidence assessment for precision.
        """
        errors = []
        if not nlp or not context or not context.get('is_glossary', False):
            return errors

        for i, sentence in enumerate(sentences):
            match = re.match(r'^\s*([\w\s-]+?)\s*[:—-]\s*(.*)', sentence)
            if match:
                term, definition = match.groups()
                term = term.strip()
                definition = definition.strip()

                if not term or not definition:
                    continue

                term_doc = nlp(term)
                is_proper_noun = all(tok.pos_ == 'PROPN' for tok in term_doc)

                # === EVIDENCE-BASED ANALYSIS 1: Term Capitalization ===
                if not is_proper_noun and not term.islower():
                    evidence_score = self._calculate_term_capitalization_evidence(
                        term, term_doc, sentence, text, context
                    )
                    
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=self._get_contextual_message('term_capitalization', evidence_score, context, term=term),
                            suggestions=self._generate_smart_suggestions('term_capitalization', evidence_score, context, term=term),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(sentence.find(term), sentence.find(term) + len(term)),
                            flagged_text=term
                        ))

                # === EVIDENCE-BASED ANALYSIS 2: Definition Capitalization ===
                if definition and not definition[0].isupper():
                    evidence_score = self._calculate_definition_capitalization_evidence(
                        definition, sentence, text, context
                    )
                    
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=self._get_contextual_message('definition_capitalization', evidence_score, context),
                            suggestions=self._generate_smart_suggestions('definition_capitalization', evidence_score, context),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(sentence.find(definition), sentence.find(definition) + len(definition)),
                            flagged_text=definition
                        ))
        return errors

    # === EVIDENCE CALCULATION METHODS ===

    def _calculate_term_capitalization_evidence(self, term: str, term_doc: 'Doc', 
                                              sentence: str, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential glossary term capitalization violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            term: The glossary term
            term_doc: SpaCy document of the term
            sentence: Full sentence containing the term
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if not context or not context.get('is_glossary', False):
            return 0.0  # Only apply to glossary blocks
        
        # Don't flag terms in quoted examples
        if self._is_term_in_actual_quotes(term, sentence, context):
            return 0.0  # Quoted examples are not glossary errors
        
        # Don't flag terms in technical documentation contexts with approved patterns
        if self._is_term_in_technical_context(term, sentence, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag terms in citation or reference context
        if self._is_term_in_citation_context(term, sentence, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'text': term, 'sentence': sentence}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Technical terms and brand names
        if self._is_legitimate_capitalized_term(term, context):
            return 0.0
        
        # Special guard: Acronyms and abbreviations
        if self._is_acronym_or_abbreviation(term):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_term_capitalization_base_evidence_score(term, term_doc, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this term
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Check if all words are capitalized (title case)
        words = term.split()
        title_case_words = sum(1 for word in words if word.istitle())
        if title_case_words == len(words) and len(words) > 1:
            evidence_score += 0.1  # Clear title case violation
        
        # Check for mixed capitalization
        if any(word.isupper() for word in words):
            evidence_score -= 0.2  # Might be technical term
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['technical', 'api']:
            evidence_score -= 0.1  # Technical glossaries might have more technical terms
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_terms(evidence_score, term, context)
        
        # Term capitalization-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # Term consistency is important but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_definition_capitalization_evidence(self, definition: str, sentence: str, 
                                                    text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential definition capitalization violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            definition: The definition text
            sentence: Full sentence containing the definition
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if not context or not context.get('is_glossary', False):
            return 0.0  # Only apply to glossary blocks
        
        # Don't flag definitions in quoted examples
        if self._is_definition_in_actual_quotes(definition, sentence, context):
            return 0.0  # Quoted examples are not glossary errors
        
        # Don't flag definitions in technical documentation contexts with approved patterns
        if self._is_definition_in_technical_context(definition, sentence, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag definitions in citation or reference context
        if self._is_definition_in_citation_context(definition, sentence, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'text': definition, 'sentence': sentence}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Definitions starting with technical terms
        if self._starts_with_technical_term(definition):
            return 0.0
        
        # Special guard: Definitions for technical terms (check the term before the colon)
        if self._is_definition_for_technical_term(sentence, context):
            return 0.0
        
        # Special guard: Very short definitions might be fragments
        if len(definition.split()) <= 2:
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_definition_capitalization_base_evidence_score(definition, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this definition
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        first_char = definition[0]
        
        # Check if first character is a number or symbol
        if first_char.isdigit() or not first_char.isalpha():
            evidence_score -= 0.4  # Might be legitimate
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['technical', 'reference']:
            evidence_score -= 0.1  # Technical definitions might start with lowercase technical terms
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_definitions(evidence_score, definition, context)
        
        # Definition capitalization-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.1  # Definition capitalization is important for readability
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===

    def _is_legitimate_capitalized_term(self, term: str, context: Dict[str, Any]) -> bool:
        """Check if capitalized term is legitimate (brand names, technical terms)."""
        # Common technical terms that should be capitalized
        technical_terms = {
            'API', 'SDK', 'HTTP', 'HTTPS', 'JSON', 'XML', 'HTML', 'CSS', 'SQL',
            'REST', 'SOAP', 'URL', 'URI', 'UI', 'UX', 'AI', 'ML', 'CI', 'CD',
            'AWS', 'GCP', 'IBM', 'Microsoft', 'Google', 'Apple', 'Oracle'
        }
        
        # Check if term or any word in term matches technical terms
        term_words = term.split()
        for word in term_words:
            if word.upper() in technical_terms:
                return True
        
        # Check for brand names or product names
        if any(word[0].isupper() and len(word) > 2 for word in term_words):
            content_type = context.get('content_type', 'general')
            if content_type in ['product', 'marketing', 'technical']:
                return True
        
        return False

    def _is_acronym_or_abbreviation(self, term: str) -> bool:
        """Check if term is an acronym or abbreviation that should be capitalized."""
        # All caps terms (likely acronyms)
        if term.isupper() and len(term) >= 2:
            return True
        
        # Mixed case with multiple caps (like 'OAuth', 'iPhone')
        caps_count = sum(1 for c in term if c.isupper())
        if caps_count >= 2 and len(term) <= 10:
            return True
        
        # Common abbreviation patterns
        abbreviation_patterns = [
            r'^[A-Z]{2,}$',  # All caps
            r'^[A-Z][a-z]*[A-Z][a-z]*',  # CamelCase
            r'^[a-z]*[A-Z]{2,}',  # ending with caps
        ]
        
        for pattern in abbreviation_patterns:
            if re.match(pattern, term):
                return True
        
        return False

    def _starts_with_technical_term(self, definition: str) -> bool:
        """Check if definition starts with a legitimate lowercase technical term."""
        first_word = definition.split()[0] if definition.split() else ''
        
        # Common technical terms that legitimately start lowercase
        lowercase_technical = {
            'api', 'url', 'json', 'xml', 'http', 'https', 'css', 'html',
            'boolean', 'string', 'integer', 'float', 'array', 'object',
            'function', 'method', 'class', 'interface', 'protocol'
        }
        
        return first_word.lower() in lowercase_technical
    
    def _is_definition_for_technical_term(self, sentence: str, context: Dict[str, Any] = None) -> bool:
        """Check if the definition is for a technical term (appears before the colon)."""
        import re
        
        # Extract the term before the colon
        match = re.match(r'^\s*([\w\s-]+?)\s*[:—-]\s*(.*)', sentence)
        if match:
            term, definition = match.groups()
            term = term.strip()
            
            # Check if this term is technical
            if self._is_legitimate_capitalized_term(term, context) or self._is_acronym_or_abbreviation(term):
                return True
        
        return False

    # === CONTEXTUAL MESSAGING AND SUGGESTIONS ===

    def _get_contextual_message(self, violation_type: str, evidence_score: float, 
                               context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual error messages based on violation type and evidence."""
        if violation_type == 'term_capitalization':
            term = kwargs.get('term', 'term')
            if evidence_score > 0.8:
                return f"Glossary term '{term}' should be lowercase unless it's a proper noun."
            elif evidence_score > 0.6:
                return f"Consider using lowercase for the glossary term '{term}'."
            else:
                return f"The glossary term '{term}' capitalization could be reviewed."
        
        elif violation_type == 'definition_capitalization':
            if evidence_score > 0.8:
                return "Glossary definitions must start with a capital letter."
            elif evidence_score > 0.6:
                return "Consider capitalizing the first word of this definition."
            else:
                return "This definition could start with a capital letter."
        
        return "Glossary formatting issue detected."

    def _generate_smart_suggestions(self, violation_type: str, evidence_score: float,
                                  context: Dict[str, Any], **kwargs) -> List[str]:
        """Generate smart suggestions based on violation type and evidence confidence."""
        suggestions = []
        
        if violation_type == 'term_capitalization':
            term = kwargs.get('term', 'term')
            suggestions.append(f"Change '{term}' to '{term.lower()}'.")
            suggestions.append("Use lowercase for glossary terms unless they are proper nouns or technical acronyms.")
            
            if evidence_score > 0.7:
                suggestions.append("Consistent capitalization improves glossary professionalism.")
        
        elif violation_type == 'definition_capitalization':
            suggestions.append("Capitalize the first word of the definition.")
            suggestions.append("Glossary definitions should follow standard sentence capitalization.")
            
            if evidence_score > 0.7:
                suggestions.append("Proper capitalization enhances readability and professionalism.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # === ENHANCED HELPER METHODS FOR 6-STEP EVIDENCE PATTERN ===
    
    def _is_term_in_actual_quotes(self, term: str, sentence: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the glossary term actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not sentence:
            return False
        
        # Look for quote pairs that actually enclose the term
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
                if term.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_term_in_technical_context(self, term: str, sentence: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if glossary term appears in technical documentation context with approved patterns.
        """
        if not sentence:
            return False
        
        sentence_lower = sentence.lower()
        
        # Check for technical documentation indicators
        technical_indicators = [
            'api documentation', 'technical specification', 'developer guide',
            'software documentation', 'system documentation', 'installation guide',
            'configuration guide', 'troubleshooting guide', 'reference manual'
        ]
        
        for indicator in technical_indicators:
            if indicator in sentence_lower:
                # Allow some technical-specific terms in strong technical contexts
                if self._is_legitimate_capitalized_term(term, context):
                    return True
        
        # Check content type for technical context
        content_type = context.get('content_type', '') if context else ''
        if content_type == 'technical':
            # Common technical terms that might be acceptable
            if self._is_acronym_or_abbreviation(term):
                return True
        
        return False
    
    def _is_term_in_citation_context(self, term: str, sentence: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if glossary term appears in citation or reference context.
        """
        if not sentence:
            return False
        
        sentence_lower = sentence.lower()
        
        # Check for citation indicators
        citation_indicators = [
            'according to', 'as stated in', 'reference:', 'cited in',
            'documentation shows', 'manual states', 'guide recommends',
            'specification defines', 'standard requires'
        ]
        
        for indicator in citation_indicators:
            if indicator in sentence_lower:
                return True
        
        # Check for reference formatting patterns
        if any(pattern in sentence_lower for pattern in ['see also', 'refer to', 'as described']):
            return True
        
        return False
    
    def _is_definition_in_actual_quotes(self, definition: str, sentence: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the definition actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not sentence:
            return False
        
        # Look for quote pairs that actually enclose the definition
        import re
        
        # Find all potential quote pairs in surrounding context
        quote_patterns = [
            (r'"([^"]*)"', '"'),  # Double quotes
            (r"'([^']*)'", "'"),  # Single quotes
            (r'`([^`]*)`', '`')   # Backticks
        ]
        
        for pattern, quote_char in quote_patterns:
            matches = re.finditer(pattern, sentence)
            for match in matches:
                quoted_content = match.group(1)
                # If the definition is mostly within quotes, consider it quoted
                if len(quoted_content.strip()) > len(definition.strip()) * 0.7:
                    return True
        
        return False
    
    def _is_definition_in_technical_context(self, definition: str, sentence: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if definition appears in technical reference context.
        """
        if not definition:
            return False
        
        definition_lower = definition.lower()
        
        # Check for technical reference indicators
        technical_patterns = [
            r'\b(api|sdk|cli|gui|ui|url|uri|http|https)\b',
            r'\b(json|xml|yaml|csv|sql|html|css|js)\b',
            r'\b(get|post|put|delete|patch)\b',  # HTTP methods
            r'\b(200|404|500|401|403)\b',  # HTTP status codes
            r'v?\d+\.\d+(\.\d+)?',  # Version numbers
            r'\b[A-Z_]{3,}\b',  # Constants
            r'\w+\(\)',  # Function calls
            r'<\w+>',  # XML/HTML tags or placeholders
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, definition_lower):
                return True
        
        # Check content type for technical context
        content_type = context.get('content_type', '') if context else ''
        if content_type in ['technical', 'api', 'reference']:
            # Technical definitions starting with lowercase technical terms
            if self._starts_with_technical_term(definition):
                return True
        
        return False
    
    def _is_definition_in_citation_context(self, definition: str, sentence: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if definition appears in citation or reference context.
        """
        if not sentence:
            return False
        
        sentence_lower = sentence.lower()
        
        # Check for citation indicators
        citation_indicators = [
            'according to', 'as stated in', 'reference:', 'cited in',
            'documentation shows', 'manual states', 'guide recommends',
            'specification defines', 'standard requires',
            'source:', 'see:', 'note:', 'example:',
            'figure:', 'table:', 'section:', 'chapter:', 'page:'
        ]
        
        for indicator in citation_indicators:
            if indicator in sentence_lower:
                return True
        
        # Check for reference patterns
        if any(pattern in sentence_lower for pattern in ['see section', 'refer to', 'as shown', 'as described']):
            return True
        
        return False
    
    def _get_term_capitalization_base_evidence_score(self, term: str, term_doc: 'Doc', context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Clear title case violations → 0.7 (very specific)
        - Mixed case terms → 0.5 (moderate specificity)
        - Single capitalized words → 0.4 (needs context analysis)
        """
        if not term:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_term_violation(term):
            return 0.7  # Very specific, clear violation (reduced from 0.8)
        elif self._is_pattern_term_violation(term):
            return 0.5  # Pattern-based, moderate specificity
        elif self._is_minor_term_issue(term):
            return 0.4  # Minor issue, needs context
        else:
            return 0.3  # Possible issue, needs more evidence
    
    def _get_definition_capitalization_base_evidence_score(self, definition: str, sentence: str, context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Clear lowercase start → 0.8 (very specific)
        - Ambiguous cases → 0.5 (moderate specificity)
        - Technical patterns → 0.3 (needs context analysis)
        """
        if not definition:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_definition_violation(definition):
            return 0.8  # Very specific, clear violation (reduced from 0.9)
        elif self._is_pattern_definition_violation(definition):
            return 0.5  # Pattern-based, moderate specificity
        elif self._is_minor_definition_issue(definition):
            return 0.3  # Minor issue, needs context
        else:
            return 0.2  # Possible issue, needs more evidence
    
    def _is_exact_term_violation(self, term: str) -> bool:
        """
        Check if term represents an exact capitalization violation.
        """
        # Title case terms that are not proper nouns or technical terms
        words = term.split()
        if len(words) > 1:
            title_case_words = sum(1 for word in words if word.istitle())
            if title_case_words == len(words):
                # Check if it's likely a proper noun or technical term
                if not self._is_likely_proper_noun_term(term):
                    return True
        
        # Single capitalized word that's not likely a proper noun
        if len(words) == 1 and term.istitle():
            if not self._is_likely_proper_noun_term(term):
                return True
        
        return False
    
    def _is_pattern_term_violation(self, term: str) -> bool:
        """
        Check if term shows a pattern of capitalization violation.
        """
        # Mixed case patterns that might be violations
        if any(char.isupper() for char in term) and any(char.islower() for char in term):
            # Exclude common technical patterns
            if not self._is_acronym_or_abbreviation(term):
                return True
        
        return False
    
    def _is_minor_term_issue(self, term: str) -> bool:
        """
        Check if term has minor capitalization issues.
        """
        # Single uppercase letters or very short terms
        if len(term) <= 3 and term.isupper():
            return False  # Likely acronym
        
        # Terms with some capitalization that might be borderline
        if term != term.lower() and term != term.upper():
            return True
        
        return False
    
    def _is_exact_definition_violation(self, definition: str) -> bool:
        """
        Check if definition represents an exact capitalization violation.
        """
        if not definition:
            return False
        
        # Clear lowercase start with alphabetic character
        first_char = definition[0]
        if first_char.islower() and first_char.isalpha():
            # Exclude technical terms
            if not self._starts_with_technical_term(definition):
                return True
        
        return False
    
    def _is_pattern_definition_violation(self, definition: str) -> bool:
        """
        Check if definition shows a pattern of capitalization violation.
        """
        if not definition:
            return False
        
        # Starts with lowercase but longer definition
        first_char = definition[0]
        if first_char.islower() and len(definition.split()) > 3:
            # Check if it's not a technical pattern
            if not self._starts_with_technical_term(definition):
                return True
        
        return False
    
    def _is_minor_definition_issue(self, definition: str) -> bool:
        """
        Check if definition has minor capitalization issues.
        """
        if not definition:
            return False
        
        # Short definitions with lowercase start
        first_char = definition[0]
        if first_char.islower() and 3 <= len(definition.split()) <= 5:
            return True
        
        return False
    
    def _is_likely_proper_noun_term(self, term: str) -> bool:
        """
        Check if term is likely a proper noun that should be capitalized.
        """
        # Check against common proper noun patterns
        proper_noun_indicators = [
            'IBM', 'Microsoft', 'Google', 'Apple', 'Oracle', 'Amazon', 'AWS',
            'Windows', 'Linux', 'Mac', 'Android', 'iOS',
            'JavaScript', 'Python', 'Java', 'C++', 'SQL'
        ]
        
        for indicator in proper_noun_indicators:
            if indicator.lower() in term.lower():
                return True
        
        # Check for company/product name patterns
        words = term.split()
        if len(words) >= 2:
            # Multiple capitalized words might be a company/product name
            if all(word[0].isupper() for word in words if len(word) > 1):
                return True
        
        return False
    
    def _apply_feedback_clues_terms(self, evidence_score: float, term: str, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to glossary terms.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_terms()
        
        term_lower = term.lower()
        
        # Consistently Accepted Capitalized Terms
        if term_lower in feedback_patterns.get('accepted_capitalized_terms', set()):
            evidence_score -= 0.5  # Users consistently accept this capitalization
        
        # Consistently Rejected Suggestions
        if term_lower in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Term capitalization acceptance rates
        term_acceptance = feedback_patterns.get('term_capitalization_acceptance', {})
        acceptance_rate = term_acceptance.get(term_lower, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance, likely valid in some contexts
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Terms in different content types
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_term_acceptance', {})
        
        acceptance_rate = content_patterns.get(term_lower, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Term length-based acceptance
        term_length = len(term)
        length_patterns = feedback_patterns.get('term_length_acceptance', {})
        
        if term_length <= 5:
            acceptance_rate = length_patterns.get('short', 0.4)  # Short terms often acronyms
        elif term_length <= 15:
            acceptance_rate = length_patterns.get('medium', 0.6)
        else:
            acceptance_rate = length_patterns.get('long', 0.3)  # Long terms rarely all caps
        
        if acceptance_rate > 0.7:
            evidence_score -= 0.2
        elif acceptance_rate < 0.3:
            evidence_score += 0.1
        
        # Pattern: Frequency-based adjustment for terms
        term_frequency = feedback_patterns.get('term_frequencies', {}).get(term_lower, 0)
        if term_frequency > 10:  # Commonly seen term
            acceptance_rate = feedback_patterns.get('term_capitalization_acceptance', {}).get(term_lower, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        return evidence_score
    
    def _apply_feedback_clues_definitions(self, evidence_score: float, definition: str, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to glossary definitions.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_definitions()
        
        definition_lower = definition.lower().strip()
        
        # Consistently Accepted Lowercase Definitions
        if definition_lower in feedback_patterns.get('accepted_lowercase_definitions', set()):
            evidence_score -= 0.5  # Users consistently accept this lowercase start
        
        # Consistently Rejected Suggestions
        if definition_lower in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Definition start type acceptance rates
        start_patterns = feedback_patterns.get('definition_start_acceptance', {})
        
        # Classify definition start type
        start_type = self._classify_definition_start_type(definition)
        acceptance_rate = start_patterns.get(start_type, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance for this start type
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Definitions in different content types
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_definition_acceptance', {})
        
        acceptance_rate = content_patterns.get(start_type, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Definition length-based acceptance
        word_count = len(definition.split())
        length_patterns = feedback_patterns.get('definition_length_acceptance', {})
        
        if word_count <= 5:
            acceptance_rate = length_patterns.get('short', 0.3)
        elif word_count <= 15:
            acceptance_rate = length_patterns.get('medium', 0.2)
        else:
            acceptance_rate = length_patterns.get('long', 0.1)
        
        if acceptance_rate > 0.5:
            evidence_score -= 0.2
        elif acceptance_rate < 0.2:
            evidence_score += 0.1
        
        return evidence_score
    
    def _classify_definition_start_type(self, definition: str) -> str:
        """
        Classify the type of definition start for feedback analysis.
        """
        if not definition:
            return 'empty'
        
        first_char = definition[0]
        first_word = definition.split()[0] if definition.split() else ''
        
        # Technical term patterns
        if self._starts_with_technical_term(definition):
            return 'technical_term'
        
        # Lowercase alphabetic
        if first_char.islower() and first_char.isalpha():
            return 'lowercase_word'
        
        # Number or symbol
        if first_char.isdigit():
            return 'number'
        elif not first_char.isalpha():
            return 'symbol'
        
        # Uppercase word
        if first_char.isupper():
            return 'uppercase_word'
        
        return 'other'
    
    def _get_cached_feedback_patterns_terms(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for glossary terms.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_capitalized_terms': {'API', 'JSON', 'XML', 'HTTP', 'IBM', 'SDK'},  # Common technical terms
            'rejected_suggestions': set(),  # Terms users don't want flagged
            'term_capitalization_acceptance': {
                'api': 0.2,           # Usually should be uppercase
                'json': 0.2,          # Usually should be uppercase
                'xml': 0.2,           # Usually should be uppercase
                'http': 0.2,          # Usually should be uppercase
                'sdk': 0.2,           # Usually should be uppercase
                'url': 0.3,           # Sometimes acceptable lowercase
                'database': 0.9,      # Almost always lowercase
                'server': 0.9,        # Almost always lowercase
                'client': 0.9,        # Almost always lowercase
                'network': 0.9,       # Almost always lowercase
                'software': 0.9,      # Almost always lowercase
                'hardware': 0.9,      # Almost always lowercase
                'internet': 0.8,      # Usually lowercase
                'website': 0.8,       # Usually lowercase
                'webpage': 0.8,       # Usually lowercase
                'email': 0.8,         # Usually lowercase
                'password': 0.9,      # Almost always lowercase
                'username': 0.9       # Almost always lowercase
            },
            'technical_term_acceptance': {
                'api': 0.95,          # Very acceptable capitalized in technical
                'json': 0.95,         # Very acceptable capitalized in technical
                'xml': 0.95,          # Very acceptable capitalized in technical
                'http': 0.95,         # Very acceptable capitalized in technical
                'sdk': 0.95,          # Very acceptable capitalized in technical
                'url': 0.8,           # Often acceptable capitalized in technical
                'database': 0.3,      # Less acceptable capitalized even in technical
                'server': 0.3,        # Less acceptable capitalized even in technical
                'client': 0.3         # Less acceptable capitalized even in technical
            },
            'business_term_acceptance': {
                'api': 0.7,           # Sometimes acceptable capitalized in business
                'database': 0.2,      # Less acceptable capitalized in business
                'server': 0.2,        # Less acceptable capitalized in business
                'software': 0.1,      # Rarely acceptable capitalized in business
                'hardware': 0.1,      # Rarely acceptable capitalized in business
                'internet': 0.1,      # Rarely acceptable capitalized in business
                'website': 0.1,       # Rarely acceptable capitalized in business
                'email': 0.1,         # Rarely acceptable capitalized in business
                'password': 0.1,      # Rarely acceptable capitalized in business
                'username': 0.1       # Rarely acceptable capitalized in business
            },
            'reference_term_acceptance': {
                'api': 0.9,           # Very acceptable capitalized in reference
                'json': 0.9,          # Very acceptable capitalized in reference
                'xml': 0.9,           # Very acceptable capitalized in reference
                'database': 0.4,      # Sometimes acceptable in reference
                'server': 0.4,        # Sometimes acceptable in reference
                'software': 0.2,      # Less acceptable in reference
                'hardware': 0.2       # Less acceptable in reference
            },
            'term_frequencies': {
                'api': 500,           # Very common term
                'json': 300,          # Very common term
                'xml': 250,           # Common term
                'http': 400,          # Very common term
                'database': 200,      # Common term
                'server': 180,        # Common term
                'client': 150,        # Common term
                'software': 120,      # Common term
                'hardware': 100,      # Common term
                'internet': 80,       # Less common term
                'website': 60,        # Less common term
                'email': 40,          # Less common term
                'password': 30,       # Less common term
                'username': 25        # Less common term
            },
            'term_length_acceptance': {
                'short': 0.6,         # 1-5 chars often acronyms
                'medium': 0.3,        # 6-15 chars usually lowercase
                'long': 0.1           # 16+ chars rarely all caps
            }
        }
    
    def _get_cached_feedback_patterns_definitions(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for glossary definitions.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_lowercase_definitions': {
                'api that provides', 'json format for', 'xml structure that',
                'http protocol used', 'boolean value indicating'
            },
            'rejected_suggestions': set(),  # Definitions users don't want flagged
            'definition_start_acceptance': {
                'technical_term': 0.8,        # Technical terms often acceptable lowercase
                'lowercase_word': 0.2,        # Regular words usually should be capitalized
                'uppercase_word': 0.95,       # Uppercase is correct
                'number': 0.9,                # Numbers are acceptable
                'symbol': 0.8,                # Symbols often acceptable
                'other': 0.5                  # Unknown patterns
            },
            'technical_definition_acceptance': {
                'technical_term': 0.95,       # Very acceptable in technical writing
                'lowercase_word': 0.3,        # Sometimes acceptable in technical
                'uppercase_word': 0.98,       # Almost always correct
                'number': 0.95,               # Very acceptable
                'symbol': 0.9                 # Very acceptable
            },
            'business_definition_acceptance': {
                'technical_term': 0.6,        # Sometimes acceptable in business
                'lowercase_word': 0.1,        # Rarely acceptable in business
                'uppercase_word': 0.98,       # Almost always correct
                'number': 0.9,                # Very acceptable
                'symbol': 0.7                 # Often acceptable
            },
            'reference_definition_acceptance': {
                'technical_term': 0.9,        # Very acceptable in reference
                'lowercase_word': 0.2,        # Sometimes acceptable in reference
                'uppercase_word': 0.98,       # Almost always correct
                'number': 0.95,               # Very acceptable
                'symbol': 0.85                # Very acceptable
            },
            'definition_length_acceptance': {
                'short': 0.4,                 # 1-5 words, more lenient
                'medium': 0.2,                # 6-15 words, standard rules
                'long': 0.1                   # 16+ words, strict rules
            }
        }