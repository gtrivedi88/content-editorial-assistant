"""
Punctuation and Symbols Rule
Based on IBM Style Guide topic: "Punctuation and symbols"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class PunctuationAndSymbolsRule(BasePunctuationRule):
    """
    Comprehensive punctuation and symbols checker using morphological spaCy analysis with linguistic anchors.
    Handles mathematical symbols, currency, technical symbols, special characters, and contextual appropriateness.
    """
    
    def _get_rule_type(self) -> str:
        return 'punctuation_and_symbols'

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
        """Comprehensive NLP-based punctuation and symbols analysis using linguistic anchors."""
        errors = []
        
        # Find all symbol tokens in the sentence
        symbol_tokens = self._find_symbol_tokens(doc)
        
        for token_idx in symbol_tokens:
            # Check various symbol usage patterns
            errors.extend(self._check_ampersand_usage(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_mathematical_symbols(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_currency_symbols(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_at_symbol_usage(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_hashtag_usage(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_percent_symbols(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_special_characters(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_trademark_symbols(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_bullet_symbols(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_symbol_spacing(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_symbol_combinations(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_inappropriate_symbols(doc, token_idx, sentence, sentence_index))
        
        return errors

    def _find_symbol_tokens(self, doc) -> List[int]:
        """Find all symbol tokens in the document using linguistic anchors."""
        symbol_indices = []
        
        # Define symbol categories using Unicode categories and specific patterns
        for i, token in enumerate(doc):
            if self._is_symbol_token(token):
                symbol_indices.append(i)
        
        return symbol_indices

    def _is_symbol_token(self, token) -> bool:
        """Check if token is a symbol using linguistic anchors."""
        # Check for punctuation that's not standard sentence punctuation
        if token.pos_ == 'SYM':
            return True
        
        # Check for specific symbol characters
        symbol_chars = {
            '&', '+', '=', '<', '>', '~', '^', '|', '\\', '/', '*', '%', '$', '€', '£', '¥',
            '@', '#', '§', '©', '®', '™', '°', '±', '×', '÷', '∞', '∑', '∆', '∇', '∂',
            '∫', '∏', '√', '∛', '∜', '∝', '∈', '∉', '∋', '∌', '∩', '∪', '⊂', '⊃',
            '⊆', '⊇', '⊕', '⊗', '⊥', '⊤', '⊨', '⊢', '⊣', '⊡', '⊠', '⊟', '⊞',
            '♠', '♣', '♥', '♦', '♪', '♫', '♯', '♭', '♮', '※', '‼', '⁇', '⁈', '⁉',
            '⁺', '⁻', '⁼', '⁽', '⁾', '₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉',
            '₊', '₋', '₌', '₍', '₎', '°', '′', '″', '‴', '‵', '‶', '‷', '‸', '‹', '›',
            '«', '»', '‚', '„', '‛', '‟', '‡', '†', '‰', '‱', '′', '″', '‴', '‵', '‶',
            '‷', '‸', '‹', '›', '«', '»', '‚', '„', '‛', '‟', '‡', '†', '‰', '‱'
        }
        
        return token.text in symbol_chars

    def _check_ampersand_usage(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check ampersand usage using linguistic anchors."""
        errors = []
        
        if doc[token_idx].text != '&':
            return errors
        
        context_analysis = self._analyze_ampersand_context(doc, token_idx)
        
        if context_analysis['in_general_text']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Avoid using '&' in general text.",
                suggestions=["Replace '&' with 'and' in general writing.",
                           "Use '&' only in formal names, titles, or technical contexts."],
                severity='medium'
            ))
        
        elif context_analysis['spacing_issue']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Improper spacing around '&' symbol.",
                suggestions=["Add proper spacing around '&' symbol.",
                           "Use consistent spacing in formal names and titles."],
                severity='low'
            ))
        
        elif context_analysis['in_company_name'] and context_analysis['inconsistent_style']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Inconsistent ampersand usage in company names.",
                suggestions=["Use consistent style for company names throughout document.",
                           "Follow the company's official naming convention."],
                severity='low'
            ))
        
        return errors

    def _check_mathematical_symbols(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check mathematical symbols usage using linguistic anchors."""
        errors = []
        
        math_symbols = {'+', '-', '=', '<', '>', '≤', '≥', '≠', '≈', '≡', '∞', '∑', '∆', '∇', '∂', '∫', '∏', '√', '±', '×', '÷'}
        
        if doc[token_idx].text not in math_symbols:
            return errors
        
        math_analysis = self._analyze_mathematical_context(doc, token_idx)
        
        if math_analysis['in_general_text']:
            symbol = doc[token_idx].text
            suggestions = []
            
            if symbol == '+':
                suggestions = ["Use 'plus' or 'and' instead of '+' in general text.",
                             "Reserve '+' for mathematical expressions."]
            elif symbol == '-':
                suggestions = ["Use 'minus' or appropriate word instead of '-' in general text.",
                             "Use em dash (—) or en dash (–) for text breaks."]
            elif symbol == '=':
                suggestions = ["Use 'equals' or 'is' instead of '=' in general text.",
                             "Reserve '=' for mathematical expressions."]
            elif symbol == '<':
                suggestions = ["Use 'less than' instead of '<' in general text.",
                             "Reserve '<' for mathematical expressions."]
            elif symbol == '>':
                suggestions = ["Use 'greater than' instead of '>' in general text.",
                             "Reserve '>' for mathematical expressions."]
            else:
                suggestions = [f"Spell out '{symbol}' in general text.",
                             f"Reserve '{symbol}' for mathematical expressions."]
            
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Mathematical symbol '{symbol}' should be spelled out in general text.",
                suggestions=suggestions,
                severity='medium'
            ))
        
        elif math_analysis['spacing_issue']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Improper spacing around mathematical symbols.",
                suggestions=["Add proper spacing around mathematical operators.",
                           "Use consistent spacing in mathematical expressions."],
                severity='low'
            ))
        
        elif math_analysis['context_mismatch']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Mathematical symbol usage may not match context.",
                suggestions=["Ensure mathematical symbols are appropriate for the context.",
                           "Consider if technical notation is suitable for the audience."],
                severity='low'
            ))
        
        return errors

    def _check_currency_symbols(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check currency symbols usage using linguistic anchors."""
        errors = []
        
        currency_symbols = {'$', '€', '£', '¥', '₹', '₽', '₩', '₪', '₦', '₨', '₴', '₵', '₶', '₷', '₸', '₹', '₺', '₻', '₼', '₽', '₾', '₿'}
        
        if doc[token_idx].text not in currency_symbols:
            return errors
        
        currency_analysis = self._analyze_currency_context(doc, token_idx)
        
        if currency_analysis['formatting_issue']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Currency formatting may need adjustment.",
                suggestions=["Use consistent currency formatting throughout document.",
                           "Follow standard currency notation conventions.",
                           "Consider local currency formatting preferences."],
                severity='low'
            ))
        
        elif currency_analysis['spacing_issue']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Improper spacing around currency symbols.",
                suggestions=["Check spacing conventions for currency symbols.",
                           "Use consistent spacing in monetary amounts."],
                severity='low'
            ))
        
        elif currency_analysis['mixed_currencies']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Mixed currency symbols may cause confusion.",
                suggestions=["Use consistent currency symbols throughout section.",
                           "Specify currency conversions when using multiple currencies."],
                severity='low'
            ))
        
        return errors

    def _check_at_symbol_usage(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check @ symbol usage using linguistic anchors."""
        errors = []
        
        if doc[token_idx].text != '@':
            return errors
        
        at_analysis = self._analyze_at_symbol_context(doc, token_idx)
        
        if at_analysis['in_general_text']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Avoid using '@' in general text.",
                suggestions=["Use 'at' instead of '@' in general writing.",
                           "Reserve '@' for email addresses and technical contexts."],
                severity='medium'
            ))
        
        elif at_analysis['email_formatting']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Email address formatting may need adjustment.",
                suggestions=["Ensure proper email address formatting.",
                           "Check for spacing issues around email addresses."],
                severity='low'
            ))
        
        return errors

    def _check_hashtag_usage(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check # symbol usage using linguistic anchors."""
        errors = []
        
        if doc[token_idx].text != '#':
            return errors
        
        hashtag_analysis = self._analyze_hashtag_context(doc, token_idx)
        
        if hashtag_analysis['in_formal_text']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Hashtag usage may not be appropriate in formal writing.",
                suggestions=["Consider if hashtags are suitable for this context.",
                           "Use 'number' or 'pound' instead of '#' in formal text."],
                severity='low'
            ))
        
        elif hashtag_analysis['spacing_issue']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Improper spacing around '#' symbol.",
                suggestions=["Check spacing conventions for hashtags or number signs.",
                           "Use consistent formatting for similar symbols."],
                severity='low'
            ))
        
        return errors

    def _check_percent_symbols(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check % symbol usage using linguistic anchors."""
        errors = []
        
        if doc[token_idx].text != '%':
            return errors
        
        percent_analysis = self._analyze_percent_context(doc, token_idx)
        
        if percent_analysis['spacing_issue']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Improper spacing around '%' symbol.",
                suggestions=["Check spacing conventions for percent symbols.",
                           "Use consistent spacing in percentage expressions."],
                severity='low'
            ))
        
        elif percent_analysis['formatting_inconsistency']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Inconsistent percentage formatting.",
                suggestions=["Use consistent format: either '5%' or '5 percent'.",
                           "Choose one style and apply consistently."],
                severity='low'
            ))
        
        return errors

    def _check_special_characters(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check special characters usage using linguistic anchors."""
        errors = []
        
        special_chars = {'~', '^', '|', '\\', '*', '§', '¶', '†', '‡', '•', '◦', '‣', '⁃'}
        
        if doc[token_idx].text not in special_chars:
            return errors
        
        special_analysis = self._analyze_special_character_context(doc, token_idx)
        
        if special_analysis['inappropriate_context']:
            symbol = doc[token_idx].text
            suggestions = []
            
            if symbol == '~':
                suggestions = ["Use 'approximately' instead of '~' in general text.",
                             "Reserve '~' for technical or mathematical contexts."]
            elif symbol == '^':
                suggestions = ["Use proper superscript formatting instead of '^'.",
                             "Spell out exponents in general text."]
            elif symbol == '|':
                suggestions = ["Use appropriate punctuation instead of '|'.",
                             "Consider using em dash (—) or parentheses."]
            elif symbol == '*':
                suggestions = ["Use bullet points or proper list formatting.",
                             "Consider using '×' for multiplication in text."]
            else:
                suggestions = [f"Consider if '{symbol}' is appropriate for general text.",
                             f"Use standard punctuation instead of '{symbol}'."]
            
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Special character '{symbol}' may not be appropriate in general text.",
                suggestions=suggestions,
                severity='medium'
            ))
        
        return errors

    def _check_trademark_symbols(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check trademark symbols usage using linguistic anchors."""
        errors = []
        
        trademark_symbols = {'©', '®', '™', '℠'}
        
        if doc[token_idx].text not in trademark_symbols:
            return errors
        
        trademark_analysis = self._analyze_trademark_context(doc, token_idx)
        
        if trademark_analysis['placement_issue']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Trademark symbol placement may need adjustment.",
                suggestions=["Place trademark symbols immediately after the trademarked term.",
                           "Use consistent placement throughout document."],
                severity='low'
            ))
        
        elif trademark_analysis['overuse']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Excessive trademark symbol usage.",
                suggestions=["Use trademark symbols sparingly in general text.",
                           "Include trademark notice once per document or section."],
                severity='low'
            ))
        
        return errors

    def _check_bullet_symbols(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check bullet symbols usage using linguistic anchors."""
        errors = []
        
        bullet_symbols = {'•', '◦', '‣', '⁃', '▪', '▫', '‒', '–', '—', '―'}
        
        if doc[token_idx].text not in bullet_symbols:
            return errors
        
        bullet_analysis = self._analyze_bullet_context(doc, token_idx)
        
        if bullet_analysis['inconsistent_style']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Inconsistent bullet symbol usage.",
                suggestions=["Use consistent bullet symbols throughout lists.",
                           "Choose one bullet style and apply consistently."],
                severity='low'
            ))
        
        elif bullet_analysis['inappropriate_context']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Bullet symbol may not be appropriate in continuous text.",
                suggestions=["Use proper list formatting for bullet points.",
                           "Consider using standard punctuation in paragraph text."],
                severity='low'
            ))
        
        return errors

    def _check_symbol_spacing(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check spacing around symbols using linguistic anchors."""
        errors = []
        
        spacing_analysis = self._analyze_symbol_spacing(doc, token_idx)
        
        if spacing_analysis['missing_space_before']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Missing space before symbol.",
                suggestions=["Add appropriate space before symbol.",
                           "Check spacing conventions for this symbol type."],
                severity='low'
            ))
        
        elif spacing_analysis['missing_space_after']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Missing space after symbol.",
                suggestions=["Add appropriate space after symbol.",
                           "Ensure proper spacing for readability."],
                severity='low'
            ))
        
        elif spacing_analysis['excessive_spacing']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Excessive spacing around symbol.",
                suggestions=["Use standard spacing around symbols.",
                           "Remove extra spaces for consistent formatting."],
                severity='low'
            ))
        
        return errors

    def _check_symbol_combinations(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check symbol combinations using linguistic anchors."""
        errors = []
        
        combination_analysis = self._analyze_symbol_combinations(doc, token_idx)
        
        if combination_analysis['conflicting_symbols']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Conflicting symbol usage detected.",
                suggestions=["Review symbol combinations for consistency.",
                           "Use appropriate single symbol instead of combination."],
                severity='medium'
            ))
        
        elif combination_analysis['redundant_symbols']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Redundant symbol usage detected.",
                suggestions=["Remove redundant symbols.",
                           "Use single symbol for clarity."],
                severity='low'
            ))
        
        return errors

    def _check_inappropriate_symbols(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for inappropriate symbol usage using linguistic anchors."""
        errors = []
        
        inappropriate_analysis = self._analyze_inappropriate_symbol_usage(doc, token_idx)
        
        if inappropriate_analysis['context_mismatch']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Symbol usage may not match document context.",
                suggestions=["Consider if symbol is appropriate for this writing style.",
                           "Use conventional punctuation in formal writing."],
                severity='low'
            ))
        
        elif inappropriate_analysis['audience_mismatch']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Symbol usage may not be appropriate for target audience.",
                suggestions=["Consider audience familiarity with specialized symbols.",
                           "Use standard punctuation for general audiences."],
                severity='low'
            ))
        
        return errors

    # Helper methods using linguistic anchors

    def _analyze_ampersand_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze ampersand context using linguistic anchors."""
        # Check if ampersand is in a company name or title
        surrounding_tokens = self._get_surrounding_tokens(doc, token_idx, 3)
        
        # Check for proper nouns that might indicate company names
        has_proper_nouns = any(token.pos_ == 'PROPN' for token in surrounding_tokens)
        
        # Check for title case patterns
        has_title_case = any(token.text.istitle() for token in surrounding_tokens)
        
        # Check for spacing issues
        spacing_issue = self._has_spacing_issue(doc, token_idx)
        
        return {
            'in_general_text': not (has_proper_nouns or has_title_case),
            'in_company_name': has_proper_nouns and has_title_case,
            'spacing_issue': spacing_issue,
            'inconsistent_style': False  # Could be enhanced with document-wide analysis
        }

    def _analyze_mathematical_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze mathematical symbol context using linguistic anchors."""
        # Check for mathematical context indicators
        math_indicators = {'equation', 'formula', 'calculate', 'mathematics', 'math', 'algebra', 'geometry'}
        
        surrounding_text = ' '.join([token.text.lower() for token in doc])
        has_math_context = any(indicator in surrounding_text for indicator in math_indicators)
        
        # Check for numeric context
        surrounding_tokens = self._get_surrounding_tokens(doc, token_idx, 2)
        has_numeric_context = any(token.like_num for token in surrounding_tokens)
        
        return {
            'in_general_text': not (has_math_context or has_numeric_context),
            'spacing_issue': self._has_spacing_issue(doc, token_idx),
            'context_mismatch': False  # Could be enhanced with document analysis
        }

    def _analyze_currency_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze currency symbol context using linguistic anchors."""
        # Check for proper currency formatting
        surrounding_tokens = self._get_surrounding_tokens(doc, token_idx, 2)
        
        # Check for numeric values
        has_numeric_value = any(token.like_num for token in surrounding_tokens)
        
        return {
            'formatting_issue': not has_numeric_value,
            'spacing_issue': self._has_spacing_issue(doc, token_idx),
            'mixed_currencies': False  # Could be enhanced with document-wide analysis
        }

    def _analyze_at_symbol_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze @ symbol context using linguistic anchors."""
        # Check for email address pattern
        surrounding_tokens = self._get_surrounding_tokens(doc, token_idx, 2)
        
        # Simple email pattern check
        email_pattern = any(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', token.text) 
                           for token in surrounding_tokens)
        
        return {
            'in_general_text': not email_pattern,
            'email_formatting': email_pattern and self._has_spacing_issue(doc, token_idx)
        }

    def _analyze_hashtag_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze # symbol context using linguistic anchors."""
        # Check for formal writing context
        formal_indicators = {'research', 'study', 'analysis', 'report', 'documentation'}
        
        surrounding_text = ' '.join([token.text.lower() for token in doc])
        is_formal_context = any(indicator in surrounding_text for indicator in formal_indicators)
        
        return {
            'in_formal_text': is_formal_context,
            'spacing_issue': self._has_spacing_issue(doc, token_idx)
        }

    def _analyze_percent_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze % symbol context using linguistic anchors."""
        # Check for proper percentage formatting
        surrounding_tokens = self._get_surrounding_tokens(doc, token_idx, 1)
        
        # Check if preceded by number
        has_preceding_number = False
        if token_idx > 0:
            prev_token = doc[token_idx - 1]
            has_preceding_number = prev_token.like_num
        
        return {
            'spacing_issue': self._has_spacing_issue(doc, token_idx),
            'formatting_inconsistency': not has_preceding_number
        }

    def _analyze_special_character_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze special character context using linguistic anchors."""
        # Check for technical writing context
        technical_indicators = {'code', 'programming', 'software', 'algorithm', 'system'}
        
        surrounding_text = ' '.join([token.text.lower() for token in doc])
        is_technical_context = any(indicator in surrounding_text for indicator in technical_indicators)
        
        return {
            'inappropriate_context': not is_technical_context
        }

    def _analyze_trademark_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze trademark symbol context using linguistic anchors."""
        # Check for proper placement after brand names
        if token_idx > 0:
            prev_token = doc[token_idx - 1]
            proper_placement = prev_token.pos_ == 'PROPN'
        else:
            proper_placement = False
        
        return {
            'placement_issue': not proper_placement,
            'overuse': False  # Could be enhanced with document-wide analysis
        }

    def _analyze_bullet_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze bullet symbol context using linguistic anchors."""
        # Check for list context
        sentence_start = any(token.is_sent_start for token in doc[:token_idx + 3])
        
        return {
            'inconsistent_style': False,  # Could be enhanced with document-wide analysis
            'inappropriate_context': not sentence_start
        }

    def _analyze_symbol_spacing(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze spacing around symbols using linguistic anchors."""
        missing_before = False
        missing_after = False
        excessive = False
        
        # Check spacing before symbol
        if token_idx > 0:
            prev_token = doc[token_idx - 1]
            if not prev_token.whitespace_ and prev_token.text not in ['(', '[', '{']:
                missing_before = True
        
        # Check spacing after symbol
        if token_idx < len(doc) - 1:
            current_token = doc[token_idx]
            if not current_token.whitespace_ and doc[token_idx + 1].text not in [')', ']', '}', '.', ',']:
                missing_after = True
        
        return {
            'missing_space_before': missing_before,
            'missing_space_after': missing_after,
            'excessive_spacing': excessive
        }

    def _analyze_symbol_combinations(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze symbol combinations using linguistic anchors."""
        # Check for adjacent symbols
        adjacent_symbols = []
        
        if token_idx > 0 and self._is_symbol_token(doc[token_idx - 1]):
            adjacent_symbols.append(doc[token_idx - 1].text)
        
        if token_idx < len(doc) - 1 and self._is_symbol_token(doc[token_idx + 1]):
            adjacent_symbols.append(doc[token_idx + 1].text)
        
        return {
            'conflicting_symbols': len(adjacent_symbols) > 0,
            'redundant_symbols': len(adjacent_symbols) > 1
        }

    def _analyze_inappropriate_symbol_usage(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze inappropriate symbol usage using linguistic anchors."""
        # Check document formality
        formal_indicators = {'research', 'study', 'analysis', 'report', 'documentation', 'academic'}
        casual_indicators = {'blog', 'social', 'informal', 'chat', 'message'}
        
        doc_text = doc.text.lower()
        is_formal = any(indicator in doc_text for indicator in formal_indicators)
        is_casual = any(indicator in doc_text for indicator in casual_indicators)
        
        return {
            'context_mismatch': is_formal and doc[token_idx].text in ['#', '@', '&'],
            'audience_mismatch': not is_casual and doc[token_idx].text in ['#', '@']
        }

    def _get_surrounding_tokens(self, doc, token_idx: int, window: int) -> List:
        """Get surrounding tokens within a window."""
        start = max(0, token_idx - window)
        end = min(len(doc), token_idx + window + 1)
        return doc[start:end]

    def _has_spacing_issue(self, doc, token_idx: int) -> bool:
        """Check for spacing issues around a token."""
        # Simple spacing check - could be enhanced
        if token_idx > 0:
            prev_token = doc[token_idx - 1]
            if not prev_token.whitespace_ and prev_token.text not in ['(', '[', '{']:
                return True
        
        return False

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Pattern 1: Ampersand in general text
            if re.search(r'\b\w+\s*&\s*\w+\b', sentence):
                # Check if it's not in a company name (simple heuristic)
                if not re.search(r'\b[A-Z][a-z]*\s*&\s*[A-Z][a-z]*\b', sentence):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Avoid using '&' in general text.",
                        suggestions=["Replace '&' with 'and' in general writing.",
                                   "Use '&' only in formal names, titles, or technical contexts."],
                        severity='medium'
                    ))
            
            # Pattern 2: Mathematical symbols in general text
            math_symbols_pattern = r'[+\-=<>]'
            if re.search(math_symbols_pattern, sentence):
                # Check if it's not in a mathematical context
                if not re.search(r'\d+\s*[+\-=<>]\s*\d+', sentence):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Mathematical symbols should be spelled out in general text.",
                        suggestions=["Use 'plus', 'minus', 'equals' instead of symbols.",
                                   "Reserve symbols for mathematical expressions."],
                        severity='medium'
                    ))
            
            # Pattern 3: @ symbol not in email
            if '@' in sentence:
                if not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', sentence):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Avoid using '@' in general text.",
                        suggestions=["Use 'at' instead of '@' in general writing.",
                                   "Reserve '@' for email addresses."],
                        severity='medium'
                    ))
            
            # Pattern 4: Multiple consecutive symbols
            if re.search(r'[^\w\s]{2,}', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple consecutive symbols detected.",
                    suggestions=["Check if symbol combination is necessary.",
                               "Use appropriate single symbols or punctuation."],
                    severity='low'
                ))
            
            # Pattern 5: Improper spacing around symbols
            if re.search(r'\w[+\-=<>&%@#]\w', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Missing spaces around symbols.",
                    suggestions=["Add appropriate spacing around symbols.",
                               "Ensure proper spacing for readability."],
                    severity='low'
                ))
            
            # Pattern 6: Currency symbols without numbers
            currency_pattern = r'[\$€£¥](?!\s*\d)'
            if re.search(currency_pattern, sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Currency symbol should be followed by amount.",
                    suggestions=["Use currency symbols with numeric amounts.",
                               "Spell out currency in general text."],
                    severity='low'
                ))
            
            # Pattern 7: Hashtag in formal text
            if '#' in sentence:
                # Simple heuristic for formal context
                formal_words = ['research', 'study', 'analysis', 'report', 'documentation']
                if any(word in sentence.lower() for word in formal_words):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Hashtag usage may not be appropriate in formal writing.",
                        suggestions=["Consider if hashtags are suitable for this context.",
                                   "Use 'number' instead of '#' in formal text."],
                        severity='low'
                    ))
            
            # Pattern 8: Special characters in general text
            special_chars_pattern = r'[~^|\\*]'
            if re.search(special_chars_pattern, sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Special characters may not be appropriate in general text.",
                    suggestions=["Use standard punctuation instead of special characters.",
                               "Consider if technical symbols are suitable for the audience."],
                    severity='low'
                ))
        
        return errors
