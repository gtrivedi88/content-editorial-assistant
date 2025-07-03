"""
Ellipses Rule
Based on IBM Style Guide topic: "Ellipses"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class EllipsesRule(BasePunctuationRule):
    """
    Comprehensive ellipses usage checker using morphological spaCy analysis with linguistic anchors.
    Handles ellipses formatting, context appropriateness, and alternatives in technical writing.
    """
    
    def _get_rule_type(self) -> str:
        return 'ellipses'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Fallback to regex-based analysis if nlp is unavailable
        if not nlp:
            return self._analyze_with_regex(text, sentences)
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            errors.extend(self._analyze_sentence_with_nlp(doc, sentence, i))
            
        return errors

    def _analyze_sentence_with_nlp(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Comprehensive NLP-based ellipses analysis using linguistic anchors."""
        errors = []
        
        # Find all ellipses patterns in the sentence
        ellipses_patterns = self._find_ellipses_patterns(sentence)
        
        for pattern_info in ellipses_patterns:
            pattern_start, pattern_end, pattern_text = pattern_info
            
            # Find corresponding token positions in spaCy doc
            ellipses_tokens = self._find_ellipses_tokens(doc, pattern_start, pattern_end)
            
            # Check various ellipses usage patterns
            errors.extend(self._check_ellipses_context(doc, ellipses_tokens, sentence, sentence_index, pattern_text))
            errors.extend(self._check_ellipses_formatting(doc, ellipses_tokens, sentence, sentence_index, pattern_text))
            errors.extend(self._check_ellipses_alternatives(doc, ellipses_tokens, sentence, sentence_index, pattern_text))
            errors.extend(self._check_ellipses_spacing(doc, ellipses_tokens, sentence, sentence_index, pattern_text))
            errors.extend(self._check_ellipses_punctuation_combination(doc, ellipses_tokens, sentence, sentence_index, pattern_text))
        
        return errors

    def _find_ellipses_patterns(self, sentence: str) -> List[Tuple[int, int, str]]:
        """Find all ellipses patterns in the sentence."""
        patterns = []
        
        # Various ellipses patterns
        ellipses_regex = [
            r'\.{3,}',      # Three or more dots
            r'…',           # Unicode ellipsis character
            r'\. \. \.',    # Spaced periods
            r'\.\s*\.\s*\.', # Variably spaced periods
        ]
        
        for pattern in ellipses_regex:
            for match in re.finditer(pattern, sentence):
                patterns.append((match.start(), match.end(), match.group()))
        
        return patterns

    def _find_ellipses_tokens(self, doc, start_pos: int, end_pos: int) -> List[int]:
        """Find token indices corresponding to ellipses positions."""
        token_indices = []
        
        for token in doc:
            if token.idx >= start_pos and token.idx < end_pos:
                token_indices.append(token.i)
        
        return token_indices

    def _check_ellipses_context(self, doc, ellipses_tokens: List[int], sentence: str, sentence_index: int, pattern_text: str) -> List[Dict[str, Any]]:
        """Check ellipses context using linguistic anchors."""
        errors = []
        
        if not ellipses_tokens:
            return errors
        
        # Get the primary ellipses token
        primary_token_idx = ellipses_tokens[0] if ellipses_tokens else 0
        
        # Determine the context of ellipses usage
        context_type = self._determine_ellipses_context(doc, primary_token_idx)
        
        if context_type == 'quotation_omission':
            # Check if properly formatted for quotations
            if not self._is_proper_quotation_ellipses(doc, primary_token_idx):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Ellipses in quotations should be properly formatted and bracketed.",
                    suggestions=["Use [...] to indicate omitted text in quotations.",
                               "Ensure ellipses are properly spaced in quotations."],
                    severity='medium'
                ))
        
        elif context_type == 'incomplete_thought':
            # Check if appropriate for the writing style
            if self._is_technical_writing_context(doc):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Ellipses indicating incomplete thoughts should be avoided in technical writing.",
                    suggestions=["Complete the thought with a full sentence.",
                               "Use 'and so on' or 'etc.' for continuing series.",
                               "Rewrite to be more direct and clear."],
                    severity='medium'
                ))
        
        elif context_type == 'dramatic_pause':
            # Generally inappropriate in technical writing
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Ellipses for dramatic pauses should be avoided in formal writing.",
                suggestions=["Remove the ellipses and use direct statements.",
                           "Use appropriate punctuation like periods or commas.",
                           "Rewrite for a more professional tone."],
                severity='medium'
            ))
        
        elif context_type == 'list_continuation':
            # Check if there's a better alternative
            if self._should_use_explicit_continuation(doc, primary_token_idx):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Consider using explicit continuation instead of ellipses.",
                    suggestions=["Use 'and so on' or 'etc.' for clarity.",
                               "Complete the list or provide clear indication of continuation.",
                               "Use 'among others' or 'including' for examples."],
                    severity='low'
                ))
        
        elif context_type == 'trailing_off':
            # Generally inappropriate in technical writing
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Ellipses indicating trailing off should be avoided in technical writing.",
                suggestions=["Complete the sentence with a clear conclusion.",
                           "Use specific examples instead of trailing off.",
                           "Rewrite to be more definitive."],
                severity='medium'
            ))
        
        return errors

    def _check_ellipses_formatting(self, doc, ellipses_tokens: List[int], sentence: str, sentence_index: int, pattern_text: str) -> List[Dict[str, Any]]:
        """Check ellipses formatting using linguistic anchors."""
        errors = []
        
        # Check for proper ellipses format
        if self._is_improper_ellipses_format(pattern_text):
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Ellipses formatting is incorrect.",
                suggestions=["Use exactly three periods (...) or the ellipsis character (…).",
                           "Ensure consistent spacing in ellipses."],
                severity='medium'
            ))
        
        # Check for excessive ellipses
        if len(pattern_text) > 3 and not pattern_text == '…':
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Excessive dots in ellipses.",
                suggestions=["Use exactly three dots for ellipses.",
                           "Avoid using more than three periods."],
                severity='medium'
            ))
        
        return errors

    def _check_ellipses_alternatives(self, doc, ellipses_tokens: List[int], sentence: str, sentence_index: int, pattern_text: str) -> List[Dict[str, Any]]:
        """Check for better alternatives to ellipses."""
        errors = []
        
        if not ellipses_tokens:
            return errors
        
        primary_token_idx = ellipses_tokens[0]
        alternatives = self._suggest_ellipses_alternatives(doc, primary_token_idx)
        
        for alternative in alternatives:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=alternative['message'],
                suggestions=alternative['suggestions'],
                severity=alternative['severity']
            ))
        
        return errors

    def _check_ellipses_spacing(self, doc, ellipses_tokens: List[int], sentence: str, sentence_index: int, pattern_text: str) -> List[Dict[str, Any]]:
        """Check spacing around ellipses."""
        errors = []
        
        if not ellipses_tokens:
            return errors
        
        spacing_issues = self._analyze_ellipses_spacing(doc, ellipses_tokens, pattern_text)
        
        for issue in spacing_issues:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=issue['message'],
                suggestions=issue['suggestions'],
                severity=issue['severity']
            ))
        
        return errors

    def _check_ellipses_punctuation_combination(self, doc, ellipses_tokens: List[int], sentence: str, sentence_index: int, pattern_text: str) -> List[Dict[str, Any]]:
        """Check combinations of ellipses with other punctuation."""
        errors = []
        
        if not ellipses_tokens:
            return errors
        
        primary_token_idx = ellipses_tokens[0]
        combination_issues = self._analyze_punctuation_combinations(doc, primary_token_idx)
        
        for issue in combination_issues:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=issue['message'],
                suggestions=issue['suggestions'],
                severity=issue['severity']
            ))
        
        return errors

    # Helper methods using linguistic anchors

    def _determine_ellipses_context(self, doc, token_idx: int) -> str:
        """Linguistic anchor: Determine the context of ellipses usage."""
        # Check if in quotation context
        if self._is_in_quotation_context(doc, token_idx):
            return 'quotation_omission'
        
        # Check if indicating incomplete thought
        if self._is_incomplete_thought_context(doc, token_idx):
            return 'incomplete_thought'
        
        # Check if used for dramatic pause
        if self._is_dramatic_pause_context(doc, token_idx):
            return 'dramatic_pause'
        
        # Check if used for list continuation
        if self._is_list_continuation_context(doc, token_idx):
            return 'list_continuation'
        
        # Check if trailing off
        if self._is_trailing_off_context(doc, token_idx):
            return 'trailing_off'
        
        return 'unknown'

    def _is_in_quotation_context(self, doc, token_idx: int) -> bool:
        """Check if ellipses is within quotation marks."""
        # Look for quotation marks before and after
        before_tokens = doc[:token_idx]
        after_tokens = doc[token_idx + 1:]
        
        # Check for opening quote before
        has_opening_quote = any(t.text in ['"', "'", '"', '"'] for t in before_tokens[-10:])
        # Check for closing quote after
        has_closing_quote = any(t.text in ['"', "'", '"', '"'] for t in after_tokens[:10])
        
        return has_opening_quote and has_closing_quote

    def _is_incomplete_thought_context(self, doc, token_idx: int) -> bool:
        """Check if ellipses indicates incomplete thought."""
        # Look at sentence structure before ellipses
        if token_idx == 0:
            return False
        
        before_tokens = doc[:token_idx]
        
        # Check if sentence seems incomplete (no main verb or incomplete clause)
        has_main_verb = any(t.pos_ == 'VERB' and t.dep_ == 'ROOT' for t in before_tokens)
        has_incomplete_structure = any(t.dep_ in ['prep', 'mark'] and t.head.i >= token_idx for t in before_tokens)
        
        return not has_main_verb or has_incomplete_structure

    def _is_dramatic_pause_context(self, doc, token_idx: int) -> bool:
        """Check if ellipses is used for dramatic pause."""
        # Look at position in sentence and surrounding context
        total_length = len(doc)
        
        # If in middle of sentence with complete thoughts on both sides
        if token_idx > 0 and token_idx < total_length - 1:
            before_tokens = doc[:token_idx]
            after_tokens = doc[token_idx + 1:]
            
            # Check if both sides have meaningful content
            has_content_before = any(t.pos_ in ['NOUN', 'VERB', 'ADJ'] for t in before_tokens[-3:])
            has_content_after = any(t.pos_ in ['NOUN', 'VERB', 'ADJ'] for t in after_tokens[:3])
            
            return has_content_before and has_content_after
        
        return False

    def _is_list_continuation_context(self, doc, token_idx: int) -> bool:
        """Check if ellipses indicates list continuation."""
        # Look for list patterns before ellipses
        before_tokens = doc[:token_idx]
        
        # Check for comma-separated items
        has_list_commas = len([t for t in before_tokens if t.text == ',']) >= 2
        
        # Check for list indicators
        list_indicators = {'first', 'second', 'third', 'also', 'additionally', 'furthermore'}
        has_list_indicators = any(t.lemma_ in list_indicators for t in before_tokens)
        
        return has_list_commas or has_list_indicators

    def _is_trailing_off_context(self, doc, token_idx: int) -> bool:
        """Check if ellipses indicates trailing off."""
        # Usually at the end of a sentence
        return token_idx >= len(doc) - 2

    def _is_technical_writing_context(self, doc) -> bool:
        """Determine if this is technical writing context."""
        # Look for technical indicators
        technical_indicators = {
            'system', 'process', 'method', 'algorithm', 'function', 'protocol',
            'interface', 'implementation', 'configuration', 'parameter', 'variable',
            'database', 'server', 'client', 'api', 'framework', 'library',
            'documentation', 'specification', 'requirement', 'procedure'
        }
        
        doc_text = doc.text.lower()
        return any(indicator in doc_text for indicator in technical_indicators)

    def _is_proper_quotation_ellipses(self, doc, token_idx: int) -> bool:
        """Check if ellipses in quotation is properly formatted."""
        # Look for bracket formatting [...]
        if token_idx > 0 and token_idx < len(doc) - 1:
            prev_token = doc[token_idx - 1]
            next_token = doc[token_idx + 1]
            
            return prev_token.text == '[' and next_token.text == ']'
        
        return False

    def _should_use_explicit_continuation(self, doc, token_idx: int) -> bool:
        """Check if explicit continuation would be better."""
        # If in academic or technical writing, explicit is better
        if self._is_technical_writing_context(doc):
            return True
        
        # If list is formal or structured
        before_tokens = doc[:token_idx]
        has_formal_structure = any(t.lemma_ in {'include', 'contain', 'comprise'} for t in before_tokens)
        
        return has_formal_structure

    def _is_improper_ellipses_format(self, pattern_text: str) -> bool:
        """Check if ellipses format is improper."""
        # Proper formats: "..." or "…"
        proper_formats = ['...', '…']
        
        # Check for common improper formats
        improper_patterns = [
            r'\.{4,}',      # Four or more dots
            r'\. \. \. \.',  # Four spaced periods
            r'\.\.\.\.+',   # More than three consecutive dots
        ]
        
        # If it's not in proper formats, check against improper patterns
        if pattern_text not in proper_formats:
            return any(re.match(pattern, pattern_text) for pattern in improper_patterns)
        
        return False

    def _suggest_ellipses_alternatives(self, doc, token_idx: int) -> List[Dict[str, Any]]:
        """Suggest alternatives to ellipses based on context."""
        alternatives = []
        
        context_type = self._determine_ellipses_context(doc, token_idx)
        
        if context_type == 'list_continuation':
            alternatives.append({
                'message': "Consider using explicit continuation instead of ellipses.",
                'suggestions': [
                    "Use 'and so on' or 'etc.' for continuing series.",
                    "Use 'among others' or 'including' for examples.",
                    "Complete the list or provide clear examples."
                ],
                'severity': 'low'
            })
        
        elif context_type == 'incomplete_thought':
            alternatives.append({
                'message': "Complete the thought instead of using ellipses.",
                'suggestions': [
                    "Finish the sentence with a clear conclusion.",
                    "Use specific examples instead of trailing off.",
                    "Rewrite to be more direct and comprehensive."
                ],
                'severity': 'medium'
            })
        
        elif context_type == 'dramatic_pause':
            alternatives.append({
                'message': "Use appropriate punctuation instead of ellipses for pauses.",
                'suggestions': [
                    "Use a comma for a brief pause.",
                    "Use a dash for a longer pause.",
                    "Use a period and start a new sentence."
                ],
                'severity': 'medium'
            })
        
        # General technical writing alternative
        if self._is_technical_writing_context(doc):
            alternatives.append({
                'message': "Ellipses are generally inappropriate in technical writing.",
                'suggestions': [
                    "Use clear, direct statements.",
                    "Provide complete information.",
                    "Use appropriate technical terminology."
                ],
                'severity': 'medium'
            })
        
        return alternatives

    def _analyze_ellipses_spacing(self, doc, ellipses_tokens: List[int], pattern_text: str) -> List[Dict[str, Any]]:
        """Analyze spacing around ellipses."""
        issues = []
        
        if not ellipses_tokens:
            return issues
        
        primary_token_idx = ellipses_tokens[0]
        
        # Check spacing before ellipses
        if primary_token_idx > 0:
            prev_token = doc[primary_token_idx - 1]
            if not prev_token.text_with_ws.endswith(' ') and prev_token.text not in ['[', '(', '"', "'", '"']:
                issues.append({
                    'message': "Consider adding space before ellipses.",
                    'suggestions': ["Add a space before ellipses for better readability."],
                    'severity': 'low'
                })
        
        # Check spacing after ellipses
        if primary_token_idx < len(doc) - 1:
            next_token = doc[primary_token_idx + 1]
            current_token = doc[primary_token_idx]
            
            if not current_token.whitespace_ and next_token.text not in [']', ')', '"', "'", '"', '.', '!', '?']:
                issues.append({
                    'message': "Consider adding space after ellipses.",
                    'suggestions': ["Add a space after ellipses for better readability."],
                    'severity': 'low'
                })
        
        return issues

    def _analyze_punctuation_combinations(self, doc, token_idx: int) -> List[Dict[str, Any]]:
        """Analyze combinations of ellipses with other punctuation."""
        issues = []
        
        if token_idx >= len(doc):
            return issues
        
        # Check for ellipses combined with other punctuation
        if token_idx < len(doc) - 1:
            next_token = doc[token_idx + 1]
            
            # Ellipses followed by period
            if next_token.text == '.':
                issues.append({
                    'message': "Avoid combining ellipses with periods.",
                    'suggestions': ["Use either ellipses or period, not both."],
                    'severity': 'medium'
                })
            
            # Ellipses followed by comma
            elif next_token.text == ',':
                issues.append({
                    'message': "Ellipses followed by comma is unusual.",
                    'suggestions': ["Consider using just ellipses or restructuring the sentence."],
                    'severity': 'low'
                })
            
            # Ellipses followed by exclamation or question mark
            elif next_token.text in ['!', '?']:
                issues.append({
                    'message': "Combining ellipses with exclamation/question marks should be used carefully.",
                    'suggestions': ["Consider if both punctuation marks are necessary."],
                    'severity': 'low'
                })
        
        return issues

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Basic ellipses patterns detectable without NLP
            
            # Pattern 1: Basic ellipses usage
            if re.search(r'\.{3,}|…', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Ellipses should be used sparingly in formal writing.",
                    suggestions=["Consider using explicit language instead of ellipses.",
                               "Complete thoughts rather than trailing off.",
                               "Use 'and so on' or 'etc.' for continuing series."],
                    severity='low'
                ))
            
            # Pattern 2: Excessive dots
            if re.search(r'\.{4,}', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Use exactly three dots for ellipses.",
                    suggestions=["Replace with exactly three dots (...) or ellipsis character (…)."],
                    severity='medium'
                ))
            
            # Pattern 3: Improper ellipses spacing
            if re.search(r'\.{3,}\.', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid combining ellipses with periods.",
                    suggestions=["Use either ellipses or period, not both."],
                    severity='medium'
                ))
            
            # Pattern 4: Multiple ellipses in one sentence
            ellipses_count = len(re.findall(r'\.{3,}|…', sentence))
            if ellipses_count > 1:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple ellipses in one sentence may impact clarity.",
                    suggestions=["Limit ellipses usage to one per sentence.",
                               "Consider rewriting for better clarity."],
                    severity='medium'
                ))
            
            # Pattern 5: Ellipses at beginning of sentence
            if re.match(r'^\s*\.{3,}', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid starting sentences with ellipses.",
                    suggestions=["Begin with clear, direct statements.",
                               "Use proper sentence structure."],
                    severity='medium'
                ))
        
        return errors
