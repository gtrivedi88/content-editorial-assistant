"""
This file implements the QuotationsRule for the writing style linter.
It focuses on codifying the guidelines for formatting direct quotations, as
described in the IBM Style Guide.

This enhanced version uses comprehensive spaCy morphological analysis and 
linguistic anchors to identify various quotation patterns, punctuation issues,
and formatting problems with multiple permutations and combinations.
"""

from typing import List, Dict, Any, Tuple
import re

# Handle imports for different contexts
try:
    from ..base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule


class QuotationsRule(BaseRule):
    """
    Checks for correct formatting and usage of direct quotations using comprehensive linguistic analysis.
    Handles various quote types, nesting, and complex punctuation patterns.
    """
    def _get_rule_type(self) -> str:
        return "citations_quotations"

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for issues related to quotation formatting.

        Args:
            text: The full text to analyze.
            sentences: A list of sentences from the text.
            nlp: A loaded spaCy NLP model, passed from the main application.

        Returns:
            A list of dictionaries, where each dictionary represents a found error.
        """
        if not nlp:
            return []
            
        errors = []
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            
            doc = nlp(sentence)
            # Enhanced comprehensive quotation analysis
            errors.extend(self._check_punctuation_placement_comprehensive(doc, sentence, i))
            errors.extend(self._check_unbracketed_edits_comprehensive(doc, sentence, i))
            errors.extend(self._check_emphasis_quotes_comprehensive(doc, sentence, i))
            errors.extend(self._check_quotation_consistency(doc, sentence, i))
            
        return errors

    def _detect_quotation_boundaries_comprehensive(self, doc):
        """
        Comprehensive detection of quotation boundaries using morphological analysis.
        Handles various quote types, nesting, and complex patterns.
        """
        quote_patterns = []
        quote_chars = {'"', "'", '"', '"', ''', ''', '«', '»', '‹', '›'}
        
        # Track quotes with better context awareness
        quote_stack = []
        
        for i, token in enumerate(doc):
            if token.is_quote or token.text in quote_chars:
                quote_type = self._classify_quote_type_comprehensive(token)
                is_opening = self._determine_quote_direction(doc, i, quote_stack)
                
                if is_opening:
                    quote_entry = {
                        'type': quote_type,
                        'token': token,
                        'index': i,
                        'opening': True,
                        'context': self._analyze_quote_context(doc, i)
                    }
                    quote_stack.append(quote_entry)
                else:
                    if quote_stack:
                        opening_quote = quote_stack.pop()
                        quote_patterns.append({
                            'opening': opening_quote,
                            'closing': {
                                'type': quote_type, 
                                'token': token, 
                                'index': i, 
                                'opening': False,
                                'context': self._analyze_quote_context(doc, i)
                            },
                            'content_span': (opening_quote['index'] + 1, i),
                            'nesting_level': len(quote_stack),
                            'quote_content': doc[opening_quote['index'] + 1:i]
                        })
        
        return quote_patterns

    def _classify_quote_type_comprehensive(self, token):
        """Enhanced quote type classification with comprehensive morphological features."""
        quote_mappings = {
            '"': 'double_straight',
            "'": 'single_straight', 
            '"': 'double_left',
            '"': 'double_right',
            ''': 'single_left',
            ''': 'single_right',
            '«': 'guillemet_left',
            '»': 'guillemet_right',
            '‹': 'single_guillemet_left',
            '›': 'single_guillemet_right'
        }
        return quote_mappings.get(token.text, 'unknown')

    def _determine_quote_direction(self, doc, token_index, quote_stack):
        """
        Determine if a quote is opening or closing using contextual morphological analysis.
        """
        token = doc[token_index]
        
        # Context-based heuristics
        if token_index == 0:
            return True  # Start of sentence is always opening
        
        prev_token = doc[token_index - 1] if token_index > 0 else None
        next_token = doc[token_index + 1] if token_index + 1 < len(doc) else None
        
        # Check preceding context
        preceded_by_space_or_punct = prev_token and (prev_token.is_space or prev_token.is_punct)
        followed_by_alpha = next_token and (next_token.is_alpha or next_token.is_digit)
        
        # Stack-based logic with context validation
        expected_opening = len(quote_stack) % 2 == 0
        
        if expected_opening and preceded_by_space_or_punct and followed_by_alpha:
            return True
        elif not expected_opening and not followed_by_alpha:
            return False
        
        return expected_opening  # Default to stack logic

    def _analyze_quote_context(self, doc, token_index):
        """Analyze morphological context around quotation marks."""
        context = {
            'sentence_position': 'start' if token_index == 0 else 'end' if token_index == len(doc) - 1 else 'middle',
            'preceded_by_verb': False,
            'followed_by_punct': False,
            'in_citation': False
        }
        
        # Check for speech verbs in the vicinity
        window_start = max(0, token_index - 5)
        for i in range(window_start, token_index):
            if doc[i].pos_ == 'VERB' and doc[i].lemma_.lower() in {
                'say', 'said', 'state', 'stated', 'declare', 'declared', 
                'mention', 'mentioned', 'report', 'reported', 'claim', 'claimed'
            }:
                context['preceded_by_verb'] = True
                break
        
        # Check following punctuation
        if token_index + 1 < len(doc) and doc[token_index + 1].is_punct:
            context['followed_by_punct'] = True
        
        return context

    def _check_punctuation_placement_comprehensive(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Enhanced punctuation placement check with comprehensive pattern detection.
        Handles various quote types and punctuation combinations.
        """
        issues = []
        quote_patterns = self._detect_quotation_boundaries_comprehensive(doc)
        
        for pattern in quote_patterns:
            closing_quote = pattern['closing']
            closing_index = closing_quote['index']
            
            # Check for punctuation immediately following closing quote
            if closing_index + 1 < len(doc):
                next_token = doc[closing_index + 1]
                
                if next_token.is_punct:
                    punct_type = next_token.lemma_
                    should_be_inside = self._should_punctuation_be_inside(punct_type, pattern, doc)
                    
                    if should_be_inside:
                        message = f"Punctuation '{next_token.text}' should be placed inside closing quotation marks."
                        suggestion = f"In American English style, move '{next_token.text}' before the closing quote."
                        
                        # Safe token combination for error reporting
                        violating_text = closing_quote['token'].text + next_token.text
                        
                        issues.append(self._create_error(
                            sentence=sentence, sentence_index=sentence_index, message=message,
                            suggestions=[suggestion], severity="high", violating_token=violating_text
                        ))
        
        return issues

    def _should_punctuation_be_inside(self, punct_type: str, quote_pattern: dict, doc) -> bool:
        """
        Determine if punctuation should be inside quotes based on morphological context.
        """
        # American English rules
        if punct_type in ['.', ',']:
            return True
        
        # Semicolons and colons typically go outside
        if punct_type in [';', ':']:
            return False
        
        # Question marks and exclamation points: inside if they're part of the quote
        if punct_type in ['!', '?']:
            quote_content = quote_pattern['quote_content']
            # Check if the quoted content itself is interrogative or exclamatory
            return any(token.text in ['?', '!'] for token in quote_content)
        
        return False

    def _check_unbracketed_edits_comprehensive(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Enhanced detection of unbracketed edits with comprehensive pattern matching.
        """
        issues = []
        quote_patterns = self._detect_quotation_boundaries_comprehensive(doc)
        
        for pattern in quote_patterns:
            quote_content = pattern['quote_content']
            edit_patterns = self._detect_edit_patterns_in_quote(quote_content)
            
            for edit_pattern in edit_patterns:
                message = self._get_edit_error_message(edit_pattern['type'])
                suggestion = self._get_edit_suggestion(edit_pattern['type'])
                
                # Safe content text creation
                content_text = ' '.join(token.text for token in quote_content)
                violating_text = f'"{content_text}"'
                
                issues.append(self._create_error(
                    sentence=sentence, sentence_index=sentence_index, message=message,
                    suggestions=[suggestion], severity="medium", violating_token=violating_text
                ))
                break  # One error per quote to avoid redundancy
        
        return issues

    def _detect_edit_patterns_in_quote(self, quote_tokens):
        """
        Detect various edit patterns within quoted content using morphological analysis.
        """
        patterns = []
        
        for i, token in enumerate(quote_tokens):
            # Parenthetical edits (should be square brackets)
            if token.text == '(':
                patterns.append({'type': 'parenthetical_edit', 'token': token, 'index': i})
            
            # Unbracketed ellipsis
            elif token.text in ['...', '…']:
                # Check if properly bracketed
                is_bracketed = (i > 0 and quote_tokens[i-1].text == '[' and 
                               i + 1 < len(quote_tokens) and quote_tokens[i+1].text == ']')
                if not is_bracketed:
                    patterns.append({'type': 'unbracketed_ellipsis', 'token': token, 'index': i})
            
            # Potential insertions (words in parentheses that should be brackets)
            elif (token.text == '(' and i + 2 < len(quote_tokens) and 
                  quote_tokens[i+2].text == ')' and 
                  quote_tokens[i+1].pos_ in ['NOUN', 'ADJ', 'VERB']):
                patterns.append({'type': 'unbracketed_insertion', 'token': token, 'index': i})
        
        return patterns

    def _get_edit_error_message(self, edit_type: str) -> str:
        """Get appropriate error message for edit type."""
        messages = {
            'parenthetical_edit': "Incorrect formatting for edits within a quotation.",
            'unbracketed_ellipsis': "Omission in a quotation is not marked correctly.",
            'unbracketed_insertion': "Insertion in a quotation should be bracketed."
        }
        return messages.get(edit_type, "Improper editing format in quotation.")

    def _get_edit_suggestion(self, edit_type: str) -> str:
        """Get appropriate suggestion for edit type."""
        suggestions = {
            'parenthetical_edit': "Use square brackets '[...]' to indicate edits or omissions in a quotation, not parentheses.",
            'unbracketed_ellipsis': "When omitting text from a quotation, enclose the ellipsis in square brackets: '[...]'.",
            'unbracketed_insertion': "Use square brackets to indicate insertions or clarifications: '[clarification]'."
        }
        return suggestions.get(edit_type, "Use square brackets for quotation edits.")

    def _check_emphasis_quotes_comprehensive(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Comprehensive detection of quotation marks used for emphasis with morphological analysis.
        """
        issues = []
        quote_patterns = self._detect_quotation_boundaries_comprehensive(doc)
        
        for pattern in quote_patterns:
            quote_content = pattern['quote_content']
            emphasis_analysis = self._analyze_emphasis_likelihood(pattern, doc)
            
            if emphasis_analysis['is_likely_emphasis']:
                content_text = ' '.join(token.text for token in quote_content)
                message = "Quotation marks may be used incorrectly for emphasis."
                suggestion = "Avoid using quotation marks for emphasis. Use italic font for highlighting words or phrases."
                
                # Safe quote construction
                violating_text = f'"{content_text}"'
                
                issues.append(self._create_error(
                    sentence=sentence, sentence_index=sentence_index, message=message,
                    suggestions=[suggestion], severity="low", violating_token=violating_text
                ))
        
        return issues

    def _analyze_emphasis_likelihood(self, quote_pattern: dict, doc) -> dict:
        """
        Analyze patterns to determine if quotes are used for emphasis rather than citation.
        """
        quote_content = quote_pattern['quote_content']
        opening_index = quote_pattern['opening']['index']
        
        indicators = {'is_likely_emphasis': False, 'confidence': 0.0}
        
        # Factor 1: Length (short phrases are more likely emphasis)
        if len(quote_content) <= 3:
            indicators['confidence'] += 0.3
        
        # Factor 2: Context before quote (no speech verb)
        if opening_index > 0:
            preceding_context = quote_pattern['opening']['context']
            if not preceding_context['preceded_by_verb']:
                indicators['confidence'] += 0.4
        
        # Factor 3: Content analysis (no sentence structure)
        has_verb = any(token.pos_ == 'VERB' for token in quote_content)
        if not has_verb and len(quote_content) > 0:
            indicators['confidence'] += 0.2
        
        # Factor 4: Special words often emphasized
        emphasis_words = {'so-called', 'alleged', 'supposed', 'special', 'unique', 'important'}
        if any(token.lemma_.lower() in emphasis_words for token in quote_content):
            indicators['confidence'] += 0.3
        
        indicators['is_likely_emphasis'] = indicators['confidence'] >= 0.5
        return indicators

    def _check_quotation_consistency(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Check for consistency in quotation mark usage throughout the sentence.
        """
        issues = []
        quote_patterns = self._detect_quotation_boundaries_comprehensive(doc)
        
        for pattern in quote_patterns:
            opening_type = pattern['opening']['type']
            closing_type = pattern['closing']['type']
            
            # Check for mismatched quote types
            if not self._are_quote_types_compatible(opening_type, closing_type):
                message = f"Mismatched quotation marks: opening {opening_type} with closing {closing_type}."
                suggestion = "Use matching quotation mark types for opening and closing quotes."
                
                violating_text = f"{pattern['opening']['token'].text}...{pattern['closing']['token'].text}"
                
                issues.append(self._create_error(
                    sentence=sentence, sentence_index=sentence_index, message=message,
                    suggestions=[suggestion], severity="high", violating_token=violating_text
                ))
        
        return issues

    def _are_quote_types_compatible(self, opening_type: str, closing_type: str) -> bool:
        """Check if opening and closing quote types are compatible."""
        compatible_pairs = {
            ('double_straight', 'double_straight'),
            ('single_straight', 'single_straight'),
            ('double_left', 'double_right'),
            ('single_left', 'single_right'),
            ('guillemet_left', 'guillemet_right'),
            ('single_guillemet_left', 'single_guillemet_right')
        }
        return (opening_type, closing_type) in compatible_pairs
