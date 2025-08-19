"""
Notes Rule (Enhanced with Evidence-Based Analysis)
Based on IBM Style Guide topic: "Notes"
Enhanced to follow evidence-based rule development methodology for zero false positives.
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NotesRule(BaseStructureRule):
    """
    Checks for correct formatting of notes using evidence-based analysis with surgical precision.
    Implements rule-specific evidence calculation for optimal false positive reduction.
    
    Violations detected:
    - Missing colons after note labels
    - Incomplete sentences within notes
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'notes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes notes for formatting violations using evidence-based scoring.
        Each potential violation gets nuanced evidence assessment for precision.
        """
        errors = []
        if not nlp:
            return errors

        note_labels = {
            'note', 'exception', 'fast path', 'important', 'remember',
            'requirement', 'restriction', 'tip', 'attention', 'caution', 'danger', 'warning'
        }
        
        # This rule assumes each sentence passed in could be a note.
        for i, sentence in enumerate(sentences):
            # Linguistic Anchor: Check if the first word(s) is a known label.
            # Try to match single word with optional colon
            match = re.match(r'(\w+):?', sentence.strip())
            if not match:
                continue
            
            first_word_or_phrase = match.group(1)
            
            # Also check for two-word phrases like "fast path" with optional colon
            two_word_match = re.match(r'(\w+\s+\w+):?', sentence.strip())
            if two_word_match:
                two_word_phrase = two_word_match.group(1)
                if two_word_phrase.lower() in note_labels:
                    first_word_or_phrase = two_word_phrase
            
            if first_word_or_phrase.lower().strip(':') in note_labels:
                # === EVIDENCE-BASED ANALYSIS 1: Missing Colon ===
                # Check if the sentence has a colon after the label
                label_pattern = re.escape(first_word_or_phrase)
                has_colon = re.match(fr'{label_pattern}:', sentence.strip(), re.IGNORECASE)
                if not has_colon:
                    evidence_score = self._calculate_missing_colon_evidence(
                        first_word_or_phrase, sentence, text, context
                    )
                    
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message=self._get_contextual_message('missing_colon', evidence_score, context, label=first_word_or_phrase),
                            suggestions=self._generate_smart_suggestions('missing_colon', evidence_score, context, label=first_word_or_phrase),
                            severity='high',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(sentence.find(first_word_or_phrase), sentence.find(first_word_or_phrase) + len(first_word_or_phrase)),
                            flagged_text=first_word_or_phrase
                        ))
                
                # === EVIDENCE-BASED ANALYSIS 2: Incomplete Sentence ===
                note_content = sentence[len(first_word_or_phrase):].strip()
                if note_content:
                    doc = nlp(note_content)
                    if not self._is_complete_sentence(doc):
                        evidence_score = self._calculate_incomplete_sentence_evidence(
                            note_content, doc, sentence, text, context
                        )
                        
                        if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                            errors.append(self._create_error(
                                sentence=sentence, sentence_index=i,
                                message=self._get_contextual_message('incomplete_sentence', evidence_score, context),
                                suggestions=self._generate_smart_suggestions('incomplete_sentence', evidence_score, context),
                                severity='low',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(sentence.find(note_content), sentence.find(note_content) + len(note_content)),
                                flagged_text=note_content
                            ))
        return errors

    # === EVIDENCE CALCULATION METHODS ===

    def _calculate_missing_colon_evidence(self, label: str, sentence: str, 
                                        text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential missing colon violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            label: The note label (e.g., "NOTE", "IMPORTANT")
            sentence: Full sentence containing the label
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
        
        # Don't flag note labels in quoted examples
        if self._is_note_label_in_actual_quotes(label, sentence, text, context):
            return 0.0  # Quoted examples are not note formatting errors
        
        # Don't flag labels in technical documentation contexts with approved patterns
        if self._is_note_label_in_technical_context(label, sentence, text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag labels in citation or reference context
        if self._is_note_label_in_citation_context(label, sentence, text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'text': label, 'sentence': sentence}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Labels that might be part of regular text
        if self._is_label_in_regular_text(label, sentence):
            return 0.0
        
        # Special guard: Formatted differently (e.g., in brackets)
        if self._is_differently_formatted_note(label, sentence):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_missing_colon_base_evidence_score(label, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this label
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Check if label appears at start of sentence
        if not sentence.strip().lower().startswith(label.lower()):
            evidence_score -= 0.3  # Might not be a note label
        
        # Check if followed by content that looks like note content
        remaining_text = sentence[len(label):].strip()
        if len(remaining_text) < 5:
            evidence_score -= 0.2  # Might not be a complete note
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['formal', 'documentation']:
            evidence_score += 0.1  # Formal docs should follow strict formatting
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_missing_colon(evidence_score, label, sentence, context)
        
        # Missing colon-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # Missing colon is important for formatting but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_incomplete_sentence_evidence(self, note_content: str, doc: 'Doc', 
                                              sentence: str, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential incomplete sentence violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            note_content: The content part of the note
            doc: SpaCy document of the note content
            sentence: Full sentence containing the note
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
        
        # Don't flag note content in quoted examples
        if self._is_note_content_in_actual_quotes(note_content, sentence, text, context):
            return 0.0  # Quoted examples are not note completion errors
        
        # Don't flag content in technical documentation contexts with approved patterns
        if self._is_note_content_in_technical_context(note_content, sentence, text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag content in citation or reference context
        if self._is_note_content_in_citation_context(note_content, sentence, text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'text': note_content, 'sentence': sentence}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Short technical references might be acceptable
        if self._is_legitimate_fragment(note_content, context):
            return 0.0
        
        # Special guard: Lists or bullet points
        if self._is_list_or_bullet_content(note_content):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_incomplete_sentence_base_evidence_score(note_content, doc, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this content
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Very short content might be acceptable
        word_count = len(note_content.split())
        if word_count <= 3:
            evidence_score -= 0.3
        elif word_count >= 8:
            evidence_score += 0.2  # Longer content should be complete sentences
        
        # Check for sentence-like structure
        if note_content.endswith('.'):
            evidence_score -= 0.1  # Has period, might be intended as complete
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['user_guide', 'tutorial']:
            evidence_score += 0.1  # User-facing content should be complete sentences
        elif content_type in ['reference', 'technical']:
            evidence_score -= 0.1  # Technical docs might have fragments
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_incomplete_sentence(evidence_score, note_content, doc, context)
        
        # Incomplete sentence-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # Complete sentences are important for clarity but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===

    def _is_complete_sentence(self, doc: Doc) -> bool:
        """
        Uses dependency parsing to check if the text forms a complete sentence.
        """
        if not doc or len(doc) < 2:
            return False
            
        has_root = any(token.dep_ == 'ROOT' for token in doc)
        has_subject = any(token.dep_ in ('nsubj', 'nsubjpass', 'csubj') for token in doc)
        is_imperative = doc[0].pos_ == 'VERB' and doc[0].dep_ == 'ROOT'

        return has_root and (has_subject or is_imperative)

    def _is_label_in_regular_text(self, label: str, sentence: str) -> bool:
        """Check if label appears to be part of regular text rather than a note label."""
        # Check if label is not at the beginning of the sentence
        stripped_sentence = sentence.strip()
        if not stripped_sentence.lower().startswith(label.lower()):
            return True
        
        # Check if followed by content that doesn't look like note content
        remaining = sentence[len(label):].strip()
        if remaining.startswith(('is', 'was', 'are', 'were', 'that', 'which')):
            return True  # Looks like regular sentence continuation
        
        return False

    def _is_differently_formatted_note(self, label: str, sentence: str) -> bool:
        """Check if note is formatted differently (e.g., in brackets, bold, etc.)."""
        # Check for bracket formatting like [NOTE] or (TIP)
        if f'[{label.upper()}]' in sentence.upper() or f'({label.upper()})' in sentence.upper():
            return True
        
        # Check for other formatting indicators
        if sentence.startswith('**') or sentence.startswith('*'):
            return True  # Markdown formatting
        
        return False

    def _is_legitimate_fragment(self, note_content: str, context: Dict[str, Any]) -> bool:
        """Check if note content fragment is legitimate."""
        # Technical references might be acceptable
        if re.search(r'\b(API|SDK|URL|HTTP|version|v\d+)\b', note_content, re.IGNORECASE):
            return True
        
        # References to other sections
        if re.search(r'\b(see|section|chapter|page)\b', note_content, re.IGNORECASE):
            return True
        
        # Single technical terms in reference context
        content_type = context.get('content_type', 'general')
        if content_type == 'reference' and len(note_content.split()) <= 3:
            return True
        
        return False

    def _is_list_or_bullet_content(self, note_content: str) -> bool:
        """Check if note content is a list or bullet point."""
        # Check for list indicators
        list_indicators = ['-', '*', '•', '1.', '2.', '3.', 'a)', 'b)', 'c)']
        for indicator in list_indicators:
            if note_content.strip().startswith(indicator):
                return True
        
        return False

    # === CONTEXTUAL MESSAGING AND SUGGESTIONS ===

    def _get_contextual_message(self, violation_type: str, evidence_score: float, 
                               context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual error messages based on violation type and evidence."""
        if violation_type == 'missing_colon':
            label = kwargs.get('label', 'label')
            if evidence_score > 0.8:
                return f"The note label '{label}' must be followed by a colon."
            elif evidence_score > 0.6:
                return f"Consider adding a colon after the note label '{label}'."
            else:
                return f"Note label '{label}' may need a colon for proper formatting."
        
        elif violation_type == 'incomplete_sentence':
            if evidence_score > 0.8:
                return "The content of the note must be a complete sentence for clarity."
            elif evidence_score > 0.6:
                return "Consider expanding this note into a complete sentence."
            else:
                return "This note content could be more complete."
        
        return "Note formatting issue detected."

    def _generate_smart_suggestions(self, violation_type: str, evidence_score: float,
                                  context: Dict[str, Any], **kwargs) -> List[str]:
        """Generate smart suggestions based on violation type and evidence confidence."""
        suggestions = []
        
        if violation_type == 'missing_colon':
            label = kwargs.get('label', 'label')
            suggestions.append(f"Add a colon after '{label}' (e.g., '{label}:').")
            suggestions.append("Note labels should always be followed by a colon for proper formatting.")
            
            if evidence_score > 0.7:
                suggestions.append("Consistent note formatting improves document professionalism and clarity.")
        
        elif violation_type == 'incomplete_sentence':
            suggestions.append("Ensure the text within the note forms a complete, standalone sentence.")
            suggestions.append("Add a subject and verb to create a complete thought.")
            
            if evidence_score > 0.7:
                suggestions.append("Complete sentences in notes improve clarity and comprehension for all readers.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # === ENHANCED HELPER METHODS FOR 6-STEP EVIDENCE PATTERN ===
    
    def _is_note_label_in_actual_quotes(self, label: str, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the note label actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not sentence:
            return False
        
        # Look for quote pairs that actually enclose the label
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
                if label.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_note_label_in_technical_context(self, label: str, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if note label appears in technical documentation context with approved patterns.
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
                # Allow some technical-specific note patterns in strong technical contexts
                if self._is_technical_note_pattern(label, sentence):
                    return True
        
        # Check content type for technical context
        content_type = context.get('content_type', '') if context else ''
        if content_type == 'technical':
            # Common technical note patterns that might be acceptable
            if self._is_technical_note_pattern(label, sentence):
                return True
        
        return False
    
    def _is_note_label_in_citation_context(self, label: str, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if note label appears in citation or reference context.
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
    
    def _is_note_content_in_actual_quotes(self, note_content: str, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the note content actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not sentence:
            return False
        
        # Look for quote pairs that actually enclose the content
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
                # If the note content is mostly within quotes, consider it quoted
                if len(quoted_content.strip()) > len(note_content.strip()) * 0.7:
                    return True
        
        return False
    
    def _is_note_content_in_technical_context(self, note_content: str, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if note content appears in technical reference context.
        """
        if not note_content:
            return False
        
        content_lower = note_content.lower()
        
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
        
        import re
        for pattern in technical_patterns:
            if re.search(pattern, content_lower):
                return True
        
        # Check content type for technical context
        content_type = context.get('content_type', '') if context else ''
        if content_type in ['technical', 'api', 'reference']:
            # Technical note content starting with technical terms
            if self._starts_with_technical_term(note_content):
                return True
        
        return False
    
    def _is_note_content_in_citation_context(self, note_content: str, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if note content appears in citation or reference context.
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
    
    def _is_technical_note_pattern(self, label: str, sentence: str) -> bool:
        """
        Check if note follows a technical pattern that might be acceptable.
        """
        sentence_lower = sentence.lower()
        
        # Technical note patterns that might be acceptable without strict formatting
        technical_patterns = [
            'note about', 'note on', 'note regarding',
            'important for', 'remember to', 'tip for',
            'warning about', 'caution when', 'attention to'
        ]
        
        for pattern in technical_patterns:
            if pattern in sentence_lower:
                return True
        
        # Notes in code comments or technical discussions
        if any(indicator in sentence_lower for indicator in ['code', 'function', 'method', 'variable', 'parameter']):
            return True
        
        return False
    
    def _starts_with_technical_term(self, note_content: str) -> bool:
        """
        Check if note content starts with a legitimate technical term.
        """
        first_word = note_content.split()[0] if note_content.split() else ''
        
        # Common technical terms that legitimately start note content
        technical_terms = {
            'api', 'url', 'json', 'xml', 'http', 'https', 'css', 'html',
            'boolean', 'string', 'integer', 'float', 'array', 'object',
            'function', 'method', 'class', 'interface', 'protocol',
            'version', 'config', 'parameter', 'argument', 'variable'
        }
        
        return first_word.lower() in technical_terms
    
    def _get_missing_colon_base_evidence_score(self, label: str, sentence: str, context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Clear note labels missing colons → 0.9 (very specific)
        - Borderline note labels → 0.7 (moderate specificity)
        - Ambiguous labels → 0.5 (needs context analysis)
        """
        if not label:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_missing_colon_violation(label, sentence):
            return 0.9  # Very specific, clear violation
        elif self._is_pattern_missing_colon_violation(label, sentence):
            return 0.7  # Pattern-based, moderate specificity
        elif self._is_minor_missing_colon_issue(label, sentence):
            return 0.5  # Minor issue, needs context
        else:
            return 0.4  # Possible issue, needs more evidence
    
    def _get_incomplete_sentence_base_evidence_score(self, note_content: str, doc: 'Doc', context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Clear incomplete sentences → 0.8 (very specific)
        - Borderline fragments → 0.6 (moderate specificity)
        - Technical fragments → 0.4 (needs context analysis)
        """
        if not note_content:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_incomplete_sentence_violation(note_content, doc):
            return 0.8  # Very specific, clear violation
        elif self._is_pattern_incomplete_sentence_violation(note_content, doc):
            return 0.6  # Pattern-based, moderate specificity
        elif self._is_minor_incomplete_sentence_issue(note_content, doc):
            return 0.4  # Minor issue, needs context
        else:
            return 0.3  # Possible issue, needs more evidence
    
    def _is_exact_missing_colon_violation(self, label: str, sentence: str) -> bool:
        """
        Check if label represents an exact missing colon violation.
        """
        # Clear note labels that should definitely have colons
        clear_note_labels = ['note', 'important', 'warning', 'caution', 'attention', 'tip']
        
        if label.lower() in clear_note_labels:
            # Check if it's at the start of sentence and followed by content
            sentence_stripped = sentence.strip()
            if sentence_stripped.lower().startswith(label.lower()):
                remaining = sentence_stripped[len(label):].strip()
                # Has content but no colon
                if remaining and not label.endswith(':') and not remaining.startswith(':'):
                    return True
        
        return False
    
    def _is_pattern_missing_colon_violation(self, label: str, sentence: str) -> bool:
        """
        Check if label shows a pattern of missing colon violation.
        """
        # Other note-like labels that might need colons
        note_like_labels = ['exception', 'requirement', 'restriction', 'remember', 'fast path']
        
        if label.lower() in note_like_labels:
            # Check positioning and content
            sentence_stripped = sentence.strip()
            if sentence_stripped.lower().startswith(label.lower()):
                remaining = sentence_stripped[len(label):].strip()
                if remaining and not label.endswith(':'):
                    return True
        
        return False
    
    def _is_minor_missing_colon_issue(self, label: str, sentence: str) -> bool:
        """
        Check if label has minor missing colon issues.
        """
        # Labels that might be borderline
        borderline_labels = ['danger', 'fast path']
        
        if label.lower() in borderline_labels:
            # Check if used as a note label
            sentence_stripped = sentence.strip()
            if sentence_stripped.lower().startswith(label.lower()):
                return True
        
        return False
    
    def _is_exact_incomplete_sentence_violation(self, note_content: str, doc: 'Doc') -> bool:
        """
        Check if note content represents an exact incomplete sentence violation.
        """
        if not doc or len(doc) < 3:
            return False  # Too short to be a clear violation
        
        # Clear incomplete sentences - have some structure but missing key elements
        has_root = any(token.dep_ == 'ROOT' for token in doc)
        has_subject = any(token.dep_ in ('nsubj', 'nsubjpass', 'csubj') for token in doc)
        is_imperative = doc[0].pos_ == 'VERB' and doc[0].dep_ == 'ROOT'
        
        # Has some structure but incomplete
        if has_root and not has_subject and not is_imperative and len(doc) >= 4:
            return True
        
        return False
    
    def _is_pattern_incomplete_sentence_violation(self, note_content: str, doc: 'Doc') -> bool:
        """
        Check if note content shows a pattern of incomplete sentence violation.
        """
        if not doc or len(doc) < 2:
            return False
        
        # Pattern: looks like it should be a sentence but isn't
        word_count = len(note_content.split())
        if 4 <= word_count <= 8:  # Medium length but incomplete
            if not self._is_complete_sentence(doc):
                return True
        
        return False
    
    def _is_minor_incomplete_sentence_issue(self, note_content: str, doc: 'Doc') -> bool:
        """
        Check if note content has minor incomplete sentence issues.
        """
        if not doc:
            return False
        
        # Minor issues: very long content that should be sentences
        word_count = len(note_content.split())
        if word_count > 8:
            if not self._is_complete_sentence(doc):
                return True
        
        return False
    
    def _apply_feedback_clues_missing_colon(self, evidence_score: float, label: str, sentence: str, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to missing colons in notes.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_notes()
        
        label_lower = label.lower()
        
        # Consistently Accepted Labels Without Colons
        if label_lower in feedback_patterns.get('accepted_no_colon_labels', set()):
            evidence_score -= 0.5  # Users consistently accept this without colon
        
        # Consistently Rejected Suggestions
        if label_lower in feedback_patterns.get('rejected_colon_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Label-specific colon acceptance rates
        label_patterns = feedback_patterns.get('colon_requirement_acceptance', {})
        acceptance_rate = label_patterns.get(label_lower, 0.5)
        if acceptance_rate > 0.8:
            evidence_score += 0.4  # High acceptance for colon requirement means missing colon is a strong violation
        elif acceptance_rate < 0.2:
            evidence_score -= 0.2  # Low acceptance, users prefer without colon
        
        # Pattern: Context-specific label acceptance
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_colon_acceptance', {})
        
        acceptance_rate = content_patterns.get(label_lower, 0.5)
        if acceptance_rate > 0.7:
            evidence_score += 0.3  # High acceptance for colon requirement in this content type
        elif acceptance_rate < 0.3:
            evidence_score -= 0.2  # Low acceptance, users prefer without colon in this content type
        
        # Pattern: Label frequency-based adjustment
        label_frequency = feedback_patterns.get('label_frequencies', {}).get(label_lower, 0)
        if label_frequency > 10:  # Commonly seen label
            acceptance_rate = feedback_patterns.get('colon_requirement_acceptance', {}).get(label_lower, 0.5)
            if acceptance_rate > 0.7:
                evidence_score += 0.3  # Frequently accepted with colon requirement, so missing colon is a violation
            elif acceptance_rate < 0.3:
                evidence_score -= 0.2  # Frequently accepted without colon
        
        return evidence_score
    
    def _apply_feedback_clues_incomplete_sentence(self, evidence_score: float, note_content: str, doc: 'Doc', context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to incomplete sentences in notes.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_notes()
        
        # Classify note content type
        content_type_class = self._classify_note_content_type(note_content)
        
        # Consistently Accepted Incomplete Content
        content_signature = self._get_note_content_signature(note_content)
        if content_signature in feedback_patterns.get('accepted_incomplete_content', set()):
            evidence_score -= 0.5  # Users consistently accept this incomplete content
        
        # Consistently Rejected Suggestions
        if content_signature in feedback_patterns.get('rejected_completion_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Content type-specific completion acceptance rates
        content_patterns = feedback_patterns.get('completion_requirement_acceptance', {})
        acceptance_rate = content_patterns.get(content_type_class, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance for completion requirement
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, users prefer fragments
        
        # Pattern: Context-specific completion acceptance
        doc_content_type = context.get('content_type', 'general') if context else 'general'
        context_patterns = feedback_patterns.get(f'{doc_content_type}_completion_acceptance', {})
        
        acceptance_rate = context_patterns.get(content_type_class, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Length-based completion acceptance
        word_count = len(note_content.split())
        length_patterns = feedback_patterns.get('completion_length_acceptance', {})
        
        if word_count <= 3:
            acceptance_rate = length_patterns.get('short', 0.7)  # Short content often acceptable
        elif word_count <= 8:
            acceptance_rate = length_patterns.get('medium', 0.4)
        else:
            acceptance_rate = length_patterns.get('long', 0.2)  # Long content should be complete
        
        if acceptance_rate > 0.7:
            evidence_score -= 0.2
        elif acceptance_rate < 0.3:
            evidence_score += 0.1
        
        return evidence_score
    
    def _classify_note_content_type(self, note_content: str) -> str:
        """
        Classify the type of note content for feedback analysis.
        """
        if not note_content:
            return 'empty'
        
        content_lower = note_content.lower()
        
        # Technical reference patterns
        if self._starts_with_technical_term(note_content):
            return 'technical_reference'
        
        # Instruction patterns
        if any(word in content_lower for word in ['must', 'should', 'do not', 'ensure', 'make sure']):
            return 'instruction'
        
        # Reference patterns
        if any(word in content_lower for word in ['see', 'refer', 'check', 'section', 'chapter']):
            return 'reference'
        
        # Warning patterns
        if any(word in content_lower for word in ['avoid', 'prevent', 'careful', 'danger', 'risk']):
            return 'warning'
        
        # Explanatory patterns
        if any(word in content_lower for word in ['this', 'that', 'these', 'means', 'indicates']):
            return 'explanation'
        
        # General content
        return 'general'
    
    def _get_note_content_signature(self, note_content: str) -> str:
        """
        Generate a signature for the note content for feedback analysis.
        """
        if not note_content:
            return 'empty'
        
        # Create a signature based on structure
        word_count = len(note_content.split())
        content_type = self._classify_note_content_type(note_content)
        
        # Check if it ends with punctuation
        ends_with_punct = note_content.strip().endswith(('.', '!', '?', ':', ';'))
        
        # Create signature
        signature_parts = [content_type, f'{word_count}_words']
        
        if ends_with_punct:
            signature_parts.append('punctuated')
        else:
            signature_parts.append('unpunctuated')
        
        return '_'.join(signature_parts)
    
    def _get_cached_feedback_patterns_notes(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for note formatting.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_no_colon_labels': {
                'fast path'  # Sometimes acceptable without colon in technical contexts
            },
            'rejected_colon_suggestions': set(),  # Labels users don't want colon requirements for
            'colon_requirement_acceptance': {
                'note': 0.9,                # Users almost always want colons after NOTE
                'important': 0.9,           # Users almost always want colons after IMPORTANT
                'warning': 0.8,             # Users usually want colons after WARNING
                'caution': 0.8,             # Users usually want colons after CAUTION
                'tip': 0.7,                 # Users often want colons after TIP
                'attention': 0.8,           # Users usually want colons after ATTENTION
                'remember': 0.6,            # Users sometimes want colons after REMEMBER
                'exception': 0.7,           # Users often want colons after EXCEPTION
                'requirement': 0.8,         # Users usually want colons after REQUIREMENT
                'restriction': 0.7,         # Users often want colons after RESTRICTION
                'fast path': 0.4,           # Users sometimes accept without colon
                'danger': 0.8               # Users usually want colons after DANGER
            },
            'formal_colon_acceptance': {
                'note': 0.95,               # Very important in formal docs
                'important': 0.95,          # Very important in formal docs
                'warning': 0.9,             # Very important in formal docs
                'tip': 0.8,                 # Important in formal docs
                'exception': 0.8,           # Important in formal docs
                'fast path': 0.6            # Sometimes acceptable in formal docs
            },
            'documentation_colon_acceptance': {
                'note': 0.9,                # Important in documentation
                'important': 0.9,           # Important in documentation
                'warning': 0.8,             # Important in documentation
                'tip': 0.7,                 # Often important in documentation
                'fast path': 0.5            # Sometimes acceptable in documentation
            },
            'user_guide_colon_acceptance': {
                'note': 0.95,               # Very important in user guides
                'important': 0.95,          # Very important in user guides
                'tip': 0.9,                 # Very important in user guides
                'warning': 0.9,             # Very important in user guides
                'fast path': 0.3            # Less important in user guides
            },
            'technical_colon_acceptance': {
                'note': 0.7,                # Somewhat important in technical docs
                'important': 0.8,           # Important in technical docs
                'warning': 0.7,             # Somewhat important in technical docs
                'fast path': 0.8,           # Often acceptable in technical docs
                'exception': 0.6            # Sometimes acceptable in technical docs
            },
            'accepted_incomplete_content': {
                'technical_reference_2_words_unpunctuated',
                'technical_reference_3_words_unpunctuated',
                'reference_3_words_unpunctuated',
                'reference_4_words_unpunctuated'
            },
            'rejected_completion_suggestions': set(),
            'completion_requirement_acceptance': {
                'technical_reference': 0.3,  # Technical references often acceptable as fragments
                'instruction': 0.8,          # Instructions should usually be complete
                'reference': 0.4,            # References sometimes acceptable as fragments
                'warning': 0.7,              # Warnings should usually be complete
                'explanation': 0.8,          # Explanations should usually be complete
                'general': 0.6               # General content moderately needs completion
            },
            'formal_completion_acceptance': {
                'technical_reference': 0.4,  # Somewhat acceptable in formal docs
                'instruction': 0.9,          # Very important in formal docs
                'reference': 0.5,            # Sometimes acceptable in formal docs
                'warning': 0.8,              # Important in formal docs
                'explanation': 0.9,          # Very important in formal docs
                'general': 0.7               # Important in formal docs
            },
            'user_guide_completion_acceptance': {
                'technical_reference': 0.2,  # Less acceptable in user guides
                'instruction': 0.95,         # Very important in user guides
                'reference': 0.3,            # Less acceptable in user guides
                'warning': 0.9,              # Very important in user guides
                'explanation': 0.9,          # Very important in user guides
                'general': 0.8               # Important in user guides
            },
            'technical_completion_acceptance': {
                'technical_reference': 0.7,  # Often acceptable in technical docs
                'instruction': 0.6,          # Sometimes acceptable in technical docs
                'reference': 0.8,            # Often acceptable in technical docs
                'warning': 0.5,              # Sometimes acceptable in technical docs
                'explanation': 0.6,          # Sometimes acceptable in technical docs
                'general': 0.4               # Sometimes acceptable in technical docs
            },
            'completion_length_acceptance': {
                'short': 0.7,                # 1-3 words, often acceptable as fragments
                'medium': 0.4,               # 4-8 words, moderate completion requirement
                'long': 0.2                  # 9+ words, strong completion requirement
            },
            'label_frequencies': {
                'note': 500,                 # Very common label
                'important': 300,            # Very common label
                'warning': 250,              # Common label
                'tip': 200,                  # Common label
                'caution': 150,              # Common label
                'attention': 100,            # Common label
                'exception': 80,             # Less common label
                'requirement': 70,           # Less common label
                'restriction': 60,           # Less common label
                'remember': 50,              # Less common label
                'fast path': 30,             # Less common label
                'danger': 40                 # Less common label
            }
        }