"""
Highlighting Rule (Enhanced with Evidence-Based Analysis)
Based on IBM Style Guide topic: "Highlighting"
Enhanced to follow evidence-based rule development methodology for zero false positives.
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class HighlightingRule(BaseStructureRule):
    """
    Checks for missing highlighting on UI elements using evidence-based analysis with surgical precision.
    Implements rule-specific evidence calculation for optimal false positive reduction.
    
    Violations detected:
    - UI elements that should be highlighted but are not formatted
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'highlighting'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes highlighting violations using evidence-based scoring.
        Each potential violation gets nuanced evidence assessment for precision.
        """
        errors = []
        if not nlp or not context:
            return errors

        paragraph_node = context.get('node')
        
        # Enhanced: Support both rich document parsing and plain text analysis
        if not paragraph_node:
            # Fallback to plain text analysis when no rich document structure available
            paragraph_node = None

        # --- Pass 1: Linguistic Analysis ---
        # Identify phrases that should be highlighted based on linguistic patterns.
        doc = nlp(text)
        candidates = self._find_highlighting_candidates(doc)

        # --- Pass 2: Structural Verification ---
        # Check the rich document model to see if candidates are already highlighted.
        for candidate in candidates:
            start_char, end_char = candidate['span']
            
            # Enhanced: Check both rich document and markdown formatting
            # Handle both structured documents and plain text
            if paragraph_node:
                is_bold_highlighted = (self._is_span_highlighted(paragraph_node, start_char, end_char, style='bold') or
                                     self._is_markdown_formatted(text, candidate, style='bold'))
            else:
                # Plain text analysis - only check markdown formatting
                is_bold_highlighted = self._is_markdown_formatted(text, candidate, style='bold')
            
            if not is_bold_highlighted:
                # Check if it's highlighted with wrong format (e.g., italics instead of bold)
                if paragraph_node:
                    is_italic_highlighted = (self._is_span_highlighted(paragraph_node, start_char, end_char, style='italic') or
                                           self._is_markdown_formatted(text, candidate, style='italic'))
                else:
                    # Plain text analysis - only check markdown formatting
                    is_italic_highlighted = self._is_markdown_formatted(text, candidate, style='italic')
                
                if is_italic_highlighted:
                    # Wrong highlighting format detected
                    evidence_score = self._calculate_wrong_format_evidence(candidate, text, context)
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=candidate['sentence'],
                            sentence_index=candidate['sentence_index'],
                            message=self._get_contextual_message('wrong_highlighting_format', evidence_score, context, candidate=candidate),
                            suggestions=self._generate_smart_suggestions('wrong_highlighting_format', evidence_score, context, candidate=candidate),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=candidate['span'],
                            flagged_text=candidate['text']
                        ))
                else:
                    # Missing highlighting entirely
                    evidence_score = self._calculate_highlighting_evidence(
                        candidate, text, context
                    )
                    
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        errors.append(self._create_error(
                            sentence=candidate['sentence'],
                            sentence_index=candidate['sentence_index'],
                            message=self._get_contextual_message('missing_highlighting', evidence_score, context, candidate=candidate),
                            suggestions=self._generate_smart_suggestions('missing_highlighting', evidence_score, context, candidate=candidate),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=candidate['span'],
                            flagged_text=candidate['text']
                        ))

        return errors

    # === EVIDENCE CALCULATION METHODS ===

    def _calculate_highlighting_evidence(self, candidate: Dict[str, Any], text: str, 
                                       context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential missing highlighting violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            candidate: UI element candidate found by linguistic analysis
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
        
        # Don't flag UI elements in quoted examples
        if self._is_ui_element_in_actual_quotes(candidate['text'], candidate['sentence'], context):
            return 0.0  # Quoted examples are not highlighting errors
        
        # Don't flag UI elements in technical documentation contexts with approved patterns
        if self._is_ui_element_in_technical_context(candidate, text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag UI elements in citation or reference context
        if self._is_ui_element_in_citation_context(candidate, text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'text': candidate['text'], 'sentence': candidate['sentence']}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Generic or ambiguous UI references
        if self._is_generic_ui_reference(candidate['text']):
            return 0.0
        
        # Special guard: UI elements in code blocks or examples
        if self._is_in_code_or_example_context(candidate, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_highlighting_base_evidence_score(candidate, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this UI element
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        ui_text = candidate['text'].lower()
        
        # Specific UI element types have higher confidence
        high_confidence_elements = ['button', 'menu', 'dialog', 'window', 'tab']
        if any(element in ui_text for element in high_confidence_elements):
            evidence_score += 0.2
        
        # UI elements with specific names/labels are more likely to need highlighting
        if self._has_specific_ui_name(candidate['text']):
            evidence_score += 0.1
        
        # UI elements in imperative context (click, select, etc.)
        if self._is_in_imperative_context(candidate):
            evidence_score += 0.1
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['user_guide', 'tutorial']:
            evidence_score += 0.1  # User guides should highlight UI elements
        elif content_type in ['reference', 'api']:
            evidence_score -= 0.1  # Reference docs might be less strict
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_highlighting(evidence_score, candidate, context)
        
        # Highlighting-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # UI highlighting is important for user experience but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===

    def _find_highlighting_candidates(self, doc: Doc) -> List[Dict[str, Any]]:
        """
        Enhanced UI element detection using both generic patterns and specific YAML-configured labels.
        """
        candidates = []
        
        # METHOD 1: Generic UI element detection (existing logic)
        ui_element_lemmas = {"button", "menu", "window", "dialog", "tab", "field", "checkbox", "link", "icon", "list", "panel", "pane"}

        for token in doc:
            # Linguistic Anchor: A UI element is often a noun phrase ending with a UI keyword,
            # especially when it's the object of an imperative verb like "Click" or "Select".
            if token.lemma_ in ui_element_lemmas and token.pos_ == 'NOUN':
                # Check if the head is an imperative verb
                if token.head.pos_ == 'VERB' and token.head.tag_ == 'VB':
                    # Reconstruct the full noun phrase (e.g., "the Save button")
                    phrase_tokens = list(token.lefts) + [token]
                    start_token = min(phrase_tokens, key=lambda t: t.i)
                    end_token = max(phrase_tokens, key=lambda t: t.i)
                    
                    phrase_text = doc.text[start_token.idx : end_token.idx + len(end_token.text)]
                    
                    # Find which sentence this belongs to
                    sent_span = doc.char_span(start_token.idx, end_token.idx + len(end_token.text), alignment_mode="expand")
                    if sent_span:
                        sentence_text = sent_span.sent.text
                        # Correctly find the sentence index within the doc
                        sentence_index = -1
                        for idx, sent in enumerate(doc.sents):
                            if sent.start_char == sent_span.sent.start_char:
                                sentence_index = idx
                                break

                        if sentence_index != -1:
                            candidates.append({
                                'text': phrase_text,
                                'span': (start_token.idx, end_token.idx + len(end_token.text)),
                                'sentence': sentence_text,
                                'sentence_index': sentence_index,
                                'ui_type': token.lemma_,
                                'imperative_verb': token.head.lemma_
                            })
        
        # METHOD 2: Specific UI label detection from YAML configuration
        candidates.extend(self._find_specific_ui_labels(doc))
        
        return candidates

    def _find_specific_ui_labels(self, doc: Doc) -> List[Dict[str, Any]]:
        """
        Find specific UI labels from YAML configuration like "Forgot Password".
        
        This catches UI elements that don't follow the generic "click the button" pattern
        but are specific UI labels that need bold formatting.
        """
        candidates = []
        
        # Get UI labels from YAML configuration
        vocab_data = self._get_structure_vocabulary()
        ui_elements = vocab_data.get('ui_elements', {})
        ui_labels = ui_elements.get('ui_labels_requiring_bold', [])
        
        # Search for each configured UI label in the text
        text_lower = doc.text.lower()
        
        for label_config in ui_labels:
            if isinstance(label_config, dict):
                label_text = label_config.get('element', '')
                
                # Find occurrences of this label
                import re
                pattern = re.escape(label_text)
                for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                    # Find the actual case-preserved text
                    actual_text = doc.text[match.start():match.end()]
                    
                    # Find which sentence this belongs to
                    for sent_idx, sent in enumerate(doc.sents):
                        if sent.start_char <= match.start() < sent.end_char:
                            candidates.append({
                                'text': actual_text,
                                'span': (match.start(), match.end()),
                                'sentence': sent.text,
                                'sentence_index': sent_idx,
                                'ui_type': 'specific_label',
                                'label_category': label_config.get('category', 'ui_label'),
                                'evidence_base': label_config.get('evidence', 0.8)
                            })
                            break
        
        return candidates

    def _get_structure_vocabulary(self) -> Dict[str, Any]:
        """Get structure vocabulary from YAML configuration."""
        # Load from structure vocabularies YAML
        import yaml
        import os
        
        config_path = os.path.join(
            os.path.dirname(__file__), 'config', 'structure_vocabularies.yaml'
        )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _is_generic_ui_reference(self, ui_text: str) -> bool:
        """Check if UI reference is too generic to require highlighting."""
        generic_terms = ['the button', 'a button', 'the menu', 'a menu', 'the window', 'a window']
        return ui_text.lower().strip() in generic_terms

    def _is_in_code_or_example_context(self, candidate: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if UI element is mentioned in code or example context."""
        # Check for code-related keywords in the sentence
        sentence = candidate['sentence'].lower()
        code_indicators = ['code', 'example', 'sample', 'snippet', '```', '`']
        
        for indicator in code_indicators:
            if indicator in sentence:
                return True
        
        # Check context block type
        block_type = context.get('block_type', '')
        if block_type in ['code_block', 'inline_code', 'example']:
            return True
        
        return False

    def _has_specific_ui_name(self, ui_text: str) -> bool:
        """Check if UI element has a specific name or label."""
        # UI elements with proper names (capitalized) are more likely to need highlighting
        words = ui_text.split()
        for word in words:
            if word[0].isupper() and len(word) > 2 and word not in ['The', 'A', 'An']:
                return True
        return False

    def _is_in_imperative_context(self, candidate: Dict[str, Any]) -> bool:
        """Check if UI element is mentioned in imperative context."""
        imperative_verbs = ['click', 'select', 'choose', 'press', 'tap', 'open', 'close']
        verb = candidate.get('imperative_verb', '').lower()
        return verb in imperative_verbs

    def _is_span_highlighted(self, node, start_char: int, end_char: int, style: str) -> bool:
        """
        Traverses the rich document model to check if a character span has a specific style.
        """
        current_pos = 0
        for child in getattr(node, 'children', []):
            child_text = getattr(child, 'text_content', '')
            child_len = len(child_text)
            child_start = current_pos
            child_end = current_pos + child_len

            # Check if the target span is fully contained within this child node
            if start_char >= child_start and end_char <= child_end:
                # Check if the node's style matches the required style
                if style == 'bold' and getattr(child, 'node_type', 'text') in ['strong', 'b']:
                    return True
                if style == 'italic' and getattr(child, 'node_type', 'text') in ['emphasis', 'i']:
                    return True
                # If the span is within a single node that is NOT styled correctly, it's an error.
                return False

            current_pos += child_len
        
        # If the span crosses multiple nodes, this simple check returns False.
        # A more complex implementation could check if all nodes covering the span are highlighted.
        return False

    def _is_markdown_formatted(self, text: str, candidate: Dict[str, Any], style: str) -> bool:
        """
        Check if UI element is formatted with markdown-style highlighting.
        
        Detects patterns like:
        - _text_ (italics)
        - **text** (bold)
        - `text` (code)
        
        Production-ready approach for markdown and plain text detection.
        """
        start_char, end_char = candidate['span']
        ui_text = candidate['text']
        
        # Check the surrounding characters for markdown formatting
        if style == 'italic':
            # Check for _text_ pattern
            if (start_char > 0 and end_char < len(text) and
                text[start_char - 1] == '_' and text[end_char] == '_'):
                return True
            
            # Check for *text* pattern (single asterisk)
            if (start_char > 0 and end_char < len(text) and
                text[start_char - 1] == '*' and text[end_char] == '*' and
                not (start_char > 1 and text[start_char - 2] == '*')):
                return True
        
        elif style == 'bold':
            # Check for **text** pattern
            if (start_char > 1 and end_char < len(text) - 1 and
                text[start_char - 2:start_char] == '**' and text[end_char:end_char + 2] == '**'):
                return True
            
            # Check for __text__ pattern (double underscore)
            if (start_char > 1 and end_char < len(text) - 1 and
                text[start_char - 2:start_char] == '__' and text[end_char:end_char + 2] == '__'):
                return True
        
        elif style == 'code':
            # Check for `text` pattern
            if (start_char > 0 and end_char < len(text) and
                text[start_char - 1] == '`' and text[end_char] == '`'):
                return True
        
        return False

    # === CONTEXTUAL MESSAGING AND SUGGESTIONS ===

    def _get_contextual_message(self, violation_type: str, evidence_score: float, 
                               context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual error messages based on violation type and evidence."""
        if violation_type == 'missing_highlighting':
            candidate = kwargs.get('candidate', {})
            ui_text = candidate.get('text', 'UI element')
            
            if evidence_score > 0.8:
                return f"UI element '{ui_text}' must be highlighted in bold for clarity."
            elif evidence_score > 0.6:
                return f"Consider highlighting '{ui_text}' to help users identify the UI element."
            else:
                return f"UI element '{ui_text}' may benefit from bold formatting."
        
        elif violation_type == 'wrong_highlighting_format':
            candidate = kwargs.get('candidate', {})
            ui_text = candidate.get('text', 'UI element')
            
            if evidence_score > 0.8:
                return f"UI element '{ui_text}' should use bold formatting, not italics."
            elif evidence_score > 0.6:
                return f"Consider changing '{ui_text}' from italics to bold formatting for UI elements."
            else:
                return f"UI element '{ui_text}' may need bold instead of italic formatting."
        
        return "UI highlighting issue detected."

    def _generate_smart_suggestions(self, violation_type: str, evidence_score: float,
                                  context: Dict[str, Any], **kwargs) -> List[str]:
        """Generate smart suggestions based on violation type and evidence confidence."""
        suggestions = []
        
        if violation_type == 'missing_highlighting':
            candidate = kwargs.get('candidate', {})
            ui_text = candidate.get('text', 'UI element')
            ui_type = candidate.get('ui_type', 'element')
            
            suggestions.append(f"Apply bold formatting to '{ui_text}'.")
            suggestions.append(f"Highlight {ui_type} names to help users locate them in the interface.")
            
            if evidence_score > 0.7:
                suggestions.append("Consistent UI element highlighting improves user experience and reduces confusion.")
        
        elif violation_type == 'wrong_highlighting_format':
            candidate = kwargs.get('candidate', {})
            ui_text = candidate.get('text', 'UI element')
            
            suggestions.append(f"Change from _{ui_text}_ to **{ui_text}** for proper UI element formatting.")
            suggestions.append("Use bold formatting for UI elements instead of italics.")
            
            if evidence_score > 0.7:
                suggestions.append("Bold formatting makes UI elements more visible and easier to identify.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # === ENHANCED HELPER METHODS FOR 6-STEP EVIDENCE PATTERN ===
    
    def _is_ui_element_in_actual_quotes(self, ui_element: str, sentence: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the UI element actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not sentence:
            return False
        
        # Look for quote pairs that actually enclose the UI element
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
                if ui_element.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_ui_element_in_technical_context(self, candidate: Dict[str, Any], text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if UI element appears in technical documentation context with approved patterns.
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
                # Allow some technical-specific UI elements in strong technical contexts
                if self._is_technical_ui_pattern(candidate):
                    return True
        
        # Check content type for technical context
        content_type = context.get('content_type', '') if context else ''
        if content_type == 'technical':
            # Common technical UI patterns that might be acceptable
            if self._is_technical_ui_pattern(candidate):
                return True
        
        return False
    
    def _is_ui_element_in_citation_context(self, candidate: Dict[str, Any], text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if UI element appears in citation or reference context.
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
    
    def _is_technical_ui_pattern(self, candidate: Dict[str, Any]) -> bool:
        """
        Check if UI element follows a technical pattern that might be acceptable.
        """
        ui_text = candidate['text'].lower()
        
        # Technical UI patterns that might be acceptable without highlighting
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
            if re.search(pattern, ui_text):
                return True
        
        return False
    
    def _get_highlighting_base_evidence_score(self, candidate: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Specific named UI elements → 0.8 (very specific)
        - Generic UI element types → 0.6 (moderate specificity)
        - Ambiguous UI references → 0.4 (needs context analysis)
        """
        if not candidate:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_ui_violation(candidate):
            return 0.8  # Very specific, clear violation
        elif self._is_pattern_ui_violation(candidate):
            return 0.6  # Pattern-based, moderate specificity
        elif self._is_minor_ui_issue(candidate):
            return 0.4  # Minor issue, needs context
        else:
            return 0.3  # Possible issue, needs more evidence
    
    def _is_exact_ui_violation(self, candidate: Dict[str, Any]) -> bool:
        """
        Check if UI element represents an exact highlighting violation.
        """
        ui_text = candidate['text']
        
        # Specific named UI elements with imperative verbs are clear violations
        if self._has_specific_ui_name(ui_text) and self._is_in_imperative_context(candidate):
            return True
        
        # High-confidence UI elements in user-facing instructions
        ui_text_lower = ui_text.lower()
        high_confidence_elements = ['save button', 'ok button', 'cancel button', 'submit button']
        if any(element in ui_text_lower for element in high_confidence_elements):
            return True
        
        return False
    
    def _is_pattern_ui_violation(self, candidate: Dict[str, Any]) -> bool:
        """
        Check if UI element shows a pattern of highlighting violation.
        """
        ui_text = candidate['text']
        ui_type = candidate.get('ui_type', '')
        
        # UI elements with specific types are pattern violations
        specific_types = ['button', 'menu', 'dialog', 'window', 'tab', 'field']
        if ui_type in specific_types:
            return True
        
        # UI elements in imperative context are pattern violations
        if self._is_in_imperative_context(candidate):
            return True
        
        return False
    
    def _is_minor_ui_issue(self, candidate: Dict[str, Any]) -> bool:
        """
        Check if UI element has minor highlighting issues.
        """
        ui_text = candidate['text']
        
        # Generic UI references are minor issues
        if self._is_generic_ui_reference(ui_text):
            return False  # Actually, these should be protected
        
        # Short UI references might be minor issues
        if len(ui_text.split()) <= 2:
            return True
        
        return False
    
    def _apply_feedback_clues_highlighting(self, evidence_score: float, candidate: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to UI highlighting.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_highlighting()
        
        ui_text = candidate['text'].lower()
        ui_type = candidate.get('ui_type', 'element')
        
        # Consistently Accepted UI Elements
        if ui_text in feedback_patterns.get('accepted_ui_elements', set()):
            evidence_score -= 0.5  # Users consistently accept this UI element without highlighting
        
        # Consistently Rejected Suggestions
        if ui_text in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: UI element highlighting acceptance rates
        ui_patterns = feedback_patterns.get('ui_highlighting_acceptance', {})
        
        # Classify UI element type
        ui_category = self._classify_ui_element_type(candidate)
        acceptance_rate = ui_patterns.get(ui_category, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance for this UI element type
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Context-specific UI highlighting acceptance
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_ui_acceptance', {})
        
        acceptance_rate = content_patterns.get(ui_category, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: UI element frequency-based adjustment
        ui_frequency = feedback_patterns.get('ui_element_frequencies', {}).get(ui_text, 0)
        if ui_frequency > 10:  # Commonly seen UI element
            acceptance_rate = feedback_patterns.get('ui_highlighting_acceptance', {}).get(ui_category, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        return evidence_score

    def _calculate_wrong_format_evidence(self, candidate: Dict[str, Any], text: str, 
                                        context: Dict[str, Any]) -> float:
        """
        Calculate evidence score for wrong highlighting format (e.g., italics instead of bold).
        
        UI elements should typically use bold formatting, not italics.
        Higher evidence = more confident this is an error.
        """
        
        # Apply inherited zero false positive guards
        violation = {'text': candidate['text'], 'sentence': candidate['sentence']}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Start with high evidence - wrong format is usually clear error
        evidence_score = 0.8
        
        # Check if this is a known UI element type that requires bold
        ui_text = candidate['text'].lower()
        
        # UI elements that definitely need bold formatting (from YAML)
        high_confidence_ui = ['button', 'menu', 'dialog', 'window', 'tab', 'link', 'password', 'login', 'forgot']
        if any(element in ui_text for element in high_confidence_ui):
            evidence_score = 0.9  # Very high confidence
        
        # Context adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['user_guide', 'tutorial', 'documentation']:
            evidence_score += 0.05  # UI documentation should be precise
        
        return min(evidence_score, 1.0)
    
    def _classify_ui_element_type(self, candidate: Dict[str, Any]) -> str:
        """
        Classify the type of UI element for feedback analysis.
        """
        ui_text = candidate['text'].lower()
        ui_type = candidate.get('ui_type', 'element')
        
        # Button elements
        if ui_type == 'button' or 'button' in ui_text:
            return 'button'
        
        # Menu elements
        if ui_type == 'menu' or 'menu' in ui_text:
            return 'menu'
        
        # Dialog elements
        if ui_type == 'dialog' or 'dialog' in ui_text or 'window' in ui_text:
            return 'dialog'
        
        # Field elements
        if ui_type == 'field' or 'field' in ui_text or 'input' in ui_text:
            return 'field'
        
        # Tab elements
        if ui_type == 'tab' or 'tab' in ui_text:
            return 'tab'
        
        # Link elements
        if ui_type == 'link' or 'link' in ui_text:
            return 'link'
        
        # Generic UI elements
        return 'generic_ui'
    
    def _get_cached_feedback_patterns_highlighting(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for UI highlighting.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_ui_elements': {
                'the menu', 'a button', 'the window', 'a dialog', 'the field'
            },
            'rejected_suggestions': set(),  # UI elements users don't want flagged
            'ui_highlighting_acceptance': {
                'button': 0.2,              # Buttons usually need highlighting
                'menu': 0.3,                # Menus often need highlighting
                'dialog': 0.4,              # Dialogs sometimes need highlighting
                'field': 0.5,               # Fields moderately need highlighting
                'tab': 0.3,                 # Tabs often need highlighting
                'link': 0.6,                # Links sometimes need highlighting
                'generic_ui': 0.7           # Generic UI often acceptable without highlighting
            },
            'user_guide_ui_acceptance': {
                'button': 0.1,              # Very important to highlight in user guides
                'menu': 0.2,                # Important to highlight in user guides
                'dialog': 0.2,              # Important to highlight in user guides
                'field': 0.3,               # Important to highlight in user guides
                'tab': 0.2,                 # Important to highlight in user guides
                'link': 0.4,                # Sometimes acceptable in user guides
                'generic_ui': 0.5           # Generic UI sometimes acceptable
            },
            'tutorial_ui_acceptance': {
                'button': 0.1,              # Very important to highlight in tutorials
                'menu': 0.1,                # Very important to highlight in tutorials
                'dialog': 0.2,              # Important to highlight in tutorials
                'field': 0.2,               # Important to highlight in tutorials
                'tab': 0.2,                 # Important to highlight in tutorials
                'link': 0.3,                # Sometimes acceptable in tutorials
                'generic_ui': 0.4           # Generic UI sometimes acceptable
            },
            'reference_ui_acceptance': {
                'button': 0.4,              # Less critical in reference docs
                'menu': 0.5,                # Less critical in reference docs
                'dialog': 0.6,              # Less critical in reference docs
                'field': 0.7,               # Less critical in reference docs
                'tab': 0.5,                 # Less critical in reference docs
                'link': 0.8,                # Often acceptable in reference docs
                'generic_ui': 0.9           # Generic UI often acceptable
            },
            'technical_ui_acceptance': {
                'button': 0.5,              # Sometimes acceptable in technical docs
                'menu': 0.6,                # Sometimes acceptable in technical docs
                'dialog': 0.7,              # Often acceptable in technical docs
                'field': 0.8,               # Often acceptable in technical docs
                'tab': 0.6,                 # Sometimes acceptable in technical docs
                'link': 0.9,                # Very acceptable in technical docs
                'generic_ui': 0.9           # Generic UI very acceptable
            },
            'ui_element_frequencies': {
                'save button': 100,         # Very common UI element
                'ok button': 80,            # Very common UI element
                'cancel button': 70,        # Common UI element
                'submit button': 60,        # Common UI element
                'file menu': 50,            # Common UI element
                'edit menu': 40,            # Common UI element
                'help menu': 35,            # Common UI element
                'settings dialog': 30,      # Common UI element
                'preferences dialog': 25,   # Common UI element
                'login dialog': 20,         # Less common UI element
                'name field': 45,           # Common UI element
                'email field': 35,          # Common UI element
                'password field': 30,       # Common UI element
                'search field': 25,         # Common UI element
                'home tab': 20,             # Less common UI element
                'settings tab': 15,         # Less common UI element
                'profile tab': 10           # Less common UI element
            }
        }