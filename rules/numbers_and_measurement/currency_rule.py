"""
Currency Rule
Based on IBM Style Guide topic: "Currency"
Enhanced with pure SpaCy morphological analysis and linguistic anchors.
"""
from typing import List, Dict, Any, Set, Optional
from .base_numbers_rule import BaseNumbersRule

class CurrencyRule(BaseNumbersRule):
    """
    Checks for correct currency formatting using pure spaCy morphological analysis.
    Uses linguistic anchors to detect currency symbols, multipliers, and context-aware patterns.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize linguistic anchors for currency analysis
        self._initialize_currency_anchors()
    
    def _initialize_currency_anchors(self):
        """Initialize morphological and semantic anchors for currency analysis."""
        
        # Currency symbol morphological patterns
        self.currency_morphological_patterns = {
            'symbol_indicators': {
                'currency_symbols': {'$', '€', '£', '¥', '₹', '₽', '₩'},
                'morphological_context': ['SYM+currency', 'NOUN+compound', 'NUM+prefix'],
                'dependency_patterns': ['nummod', 'compound', 'nmod']
            },
            'multiplier_indicators': {
                'letter_multipliers': {'m', 'k', 'million', 'thousand', 'billion', 'trillion'},
                'morphological_features': ['NOUN+abbr', 'X+multiplier', 'NUM+suffix'],
                'invalid_patterns': ['M', 'K', 'B', 'T']  # Letter abbreviations to flag
            },
            'number_patterns': {
                'numeric_indicators': ['NUM', 'CARDINAL'],
                'decimal_patterns': ['like_num', 'is_digit'],
                'currency_context': ['amount', 'price', 'cost', 'value', 'fee']
            }
        }
        
        # Currency formatting validation patterns
        self.currency_formatting_patterns = {
            'iso_codes': {
                'valid_codes': {'USD', 'EUR', 'GBP', 'JPY', 'INR', 'RUB', 'KRW', 'CNY'},
                'morphological_indicators': ['PROPN+currency', 'NOUN+abbr+currency'],
                'contextual_markers': ['currency', 'denomination', 'units']
            },
            'problematic_formats': {
                'symbol_usage': True,  # Any currency symbol usage
                'multiplier_abbreviations': True,  # M, K, B abbreviations
                'informal_references': True  # Colloquial currency terms
            }
        }
        
        # Context detection for currency analysis
        self.currency_context_patterns = {
            'financial_contexts': {
                'verbs': ['cost', 'price', 'charge', 'pay', 'spend', 'earn', 'save'],
                'nouns': ['price', 'cost', 'fee', 'rate', 'amount', 'value', 'budget'],
                'prepositions': ['for', 'at', 'of', 'worth', 'around', 'approximately']
            },
            'quantity_relationships': {
                'dependency_patterns': ['nummod+NOUN', 'compound+NUM', 'nmod+currency'],
                'semantic_roles': ['amount+currency', 'quantity+unit']
            }
        }

    def _get_rule_type(self) -> str:
        return 'numbers_currency'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for currency formatting errors using comprehensive
        morphological and syntactic analysis with linguistic anchors.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # LINGUISTIC ANCHOR 1: Currency symbol detection via morphological analysis
            symbol_errors = self._analyze_currency_symbols(doc, sentence, i)
            errors.extend(symbol_errors)
            
            # LINGUISTIC ANCHOR 2: Multiplier abbreviation detection
            multiplier_errors = self._analyze_multiplier_patterns(doc, sentence, i)
            errors.extend(multiplier_errors)
            
            # LINGUISTIC ANCHOR 3: Compound currency format violations
            compound_errors = self._analyze_compound_currency_patterns(doc, sentence, i)
            errors.extend(compound_errors)

        return errors

    def _analyze_currency_symbols(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Detect currency symbols using morphological analysis."""
        errors = []
        
        for token in doc:
            # Check if token is a currency symbol
            if (token.text in self.currency_morphological_patterns['symbol_indicators']['currency_symbols'] or
                token.pos_ == 'SYM' and self._is_currency_context(token, doc)):
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=f"Currency symbol usage: '{token.text}' should be replaced with ISO code",
                    suggestions=["Replace currency symbols like '$' with three-letter ISO codes like 'USD'"],
                    severity='high',
                    flagged_text=token.text,
                    span=(token.idx, token.idx + len(token.text))
                ))
        
        return errors

    def _analyze_multiplier_patterns(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Detect problematic multiplier abbreviations using morphological analysis."""
        errors = []
        
        for token in doc:
            # Check for letter multiplier abbreviations - handle cases where multiplier is embedded in token
            multiplier_found = None
            token_text = token.text.rstrip('.')  # Remove trailing punctuation
            
            # Check if token ends with invalid multiplier patterns
            for invalid_pattern in self.currency_morphological_patterns['multiplier_indicators']['invalid_patterns']:
                if token_text.upper().endswith(invalid_pattern) and len(token_text) > len(invalid_pattern):
                    # Ensure the part before the multiplier is numeric
                    prefix = token_text[:-len(invalid_pattern)]
                    if prefix.replace(',', '').replace('.', '').isdigit():
                        multiplier_found = invalid_pattern
                        break
            
            # Also check if the entire token is just a multiplier in numeric context
            if not multiplier_found and token.text.upper() in self.currency_morphological_patterns['multiplier_indicators']['invalid_patterns']:
                if self._is_numeric_context(token, doc):
                    multiplier_found = token.text.upper()
            
            if multiplier_found:
                # Use dependency parsing to ensure it's actually a multiplier context
                if self._is_multiplier_context(token, doc) or token.like_num or token.pos_ in ['NUM', 'CARDINAL']:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message=f"Letter abbreviation for multiplier: '{multiplier_found}' should be spelled out",
                        suggestions=["Spell out the full number (e.g., 'USD 4 million' or 'USD 4,000,000')"],
                        severity='high',
                        flagged_text=token.text,
                        span=(token.idx, token.idx + len(token.text))
                    ))
        
        return errors

    def _analyze_compound_currency_patterns(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Detect compound violations (symbol + multiplier) using dependency analysis."""
        errors = []
        
        for token in doc:
            # Look for numeric tokens that might be part of currency expressions
            if token.like_num or token.pos_ in ['NUM', 'CARDINAL']:
                # Check surrounding tokens for compound violations
                compound_violation = self._check_compound_currency_violation(token, doc)
                if compound_violation:
                    symbols, multipliers, span = compound_violation
                    
                    messages = []
                    suggestions = []
                    
                    if symbols:
                        messages.append("use of currency symbol")
                        suggestions.append("Replace currency symbols with ISO codes")
                    
                    if multipliers:
                        messages.append("use of letter abbreviation for multiplier")
                        suggestions.append("Spell out the full amount")
                    
                    if messages:
                        full_message = f"Compound currency error: {' and '.join(messages)}"
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message=full_message,
                            suggestions=list(set(suggestions)),
                            severity='high',
                            flagged_text=sentence[span[0]:span[1]],
                            span=span
                        ))
        
        return errors

    def _is_currency_context(self, token, doc) -> bool:
        """Determine if a token is in a currency context using dependency analysis."""
        # Check if token is near financial terms
        for context_token in doc:
            if (context_token.lemma_.lower() in self.currency_context_patterns['financial_contexts']['verbs'] or
                context_token.lemma_.lower() in self.currency_context_patterns['financial_contexts']['nouns']):
                # Check if tokens are related via dependency
                if (token in context_token.subtree or context_token in token.subtree or
                    abs(token.i - context_token.i) <= 3):
                    return True
        
        return False

    def _is_numeric_context(self, token, doc) -> bool:
        """Check if token is in a numeric context using morphological analysis."""
        # Look for numeric tokens nearby
        for nearby_token in doc[max(0, token.i-2):min(len(doc), token.i+3)]:
            if (nearby_token.like_num or nearby_token.pos_ in ['NUM', 'CARDINAL'] or
                nearby_token.is_digit):
                return True
        return False

    def _is_multiplier_context(self, token, doc) -> bool:
        """Determine if token is actually a multiplier using dependency parsing."""
        # Check if token follows a number and precedes currency context
        if token.i > 0:
            prev_token = doc[token.i - 1]
            if prev_token.like_num or prev_token.pos_ in ['NUM', 'CARDINAL']:
                return True
        
        # Check dependency relationships
        if token.dep_ in ['nummod', 'compound', 'nmod']:
            return True
            
        return False

    def _check_compound_currency_violation(self, num_token, doc) -> Optional[tuple]:
        """Check for compound currency violations around a numeric token."""
        symbols = []
        multipliers = []
        start_idx = num_token.idx
        end_idx = num_token.idx + len(num_token.text)
        
        # Check if the numeric token itself contains a multiplier (e.g., "4M")
        token_text = num_token.text.rstrip('.')
        for invalid_pattern in self.currency_morphological_patterns['multiplier_indicators']['invalid_patterns']:
            if token_text.upper().endswith(invalid_pattern) and len(token_text) > len(invalid_pattern):
                prefix = token_text[:-len(invalid_pattern)]
                if prefix.replace(',', '').replace('.', '').isdigit():
                    multipliers.append(invalid_pattern)
                    break
        
        # Check tokens in a window around the number
        for check_token in doc[max(0, num_token.i-2):min(len(doc), num_token.i+3)]:
            # Check for currency symbols
            if check_token.text in self.currency_morphological_patterns['symbol_indicators']['currency_symbols']:
                symbols.append(check_token.text)
                start_idx = min(start_idx, check_token.idx)
                end_idx = max(end_idx, check_token.idx + len(check_token.text))
            
            # Check for multiplier abbreviations in separate tokens
            if (check_token.text.upper() in self.currency_morphological_patterns['multiplier_indicators']['invalid_patterns'] and
                check_token != num_token):
                multipliers.append(check_token.text)
                start_idx = min(start_idx, check_token.idx)
                end_idx = max(end_idx, check_token.idx + len(check_token.text))
        
        if symbols or multipliers:
            return symbols, multipliers, (start_idx, end_idx)
        
        return None

    def _get_sentence_index(self, doc, sent) -> int:
        """Helper method to get sentence index within document."""
        for i, doc_sent in enumerate(doc.sents):
            if sent == doc_sent:
                return i
        return 0
