"""
Currency Rule
Based on IBM Style Guide topic: "Currency"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CurrencyRule(BaseNumbersRule):
    """
    Checks for correct currency formatting, including the use of ISO codes
    and the avoidance of letter abbreviations for multipliers like 'M' for million.
    """
    def _get_rule_type(self) -> str:
        return 'numbers_currency'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for currency formatting:
          - Prefer ISO currency codes (e.g., 'USD 100') over symbols for global audiences
          - Avoid letter multipliers like 'M'/'K' (e.g., '4M') in currency amounts
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)

        # Pattern to find currency symbols or multipliers.
        currency_pattern = re.compile(r'([\$€£]\s?\d[\d,.]*)|(\d[\d,.]*\s?[MK])\b', re.IGNORECASE)

        for i, sent in enumerate(doc.sents):
            for match in currency_pattern.finditer(sent.text):
                flagged_text = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())

                # --- Evidence for symbol usage ---
                if any(c in flagged_text for c in "$€£"):
                    ev_symbol = self._calculate_currency_symbol_evidence(flagged_text, sent, text, context or {})
                    if ev_symbol > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_currency_symbol_message(flagged_text, ev_symbol, context or {}),
                            suggestions=self._generate_smart_currency_symbol_suggestions(flagged_text, ev_symbol, sent, context or {}),
                            severity='low' if ev_symbol < 0.6 else 'medium',
                            text=text,
                            context=context,
                            evidence_score=ev_symbol,
                            span=span,
                            flagged_text=flagged_text
                        ))

                # --- Evidence for multiplier usage (M/K) ---
                if any(c in flagged_text.upper() for c in "MK"):
                    ev_mult = self._calculate_currency_multiplier_evidence(flagged_text, sent, text, context or {})
                    if ev_mult > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_multiplier_message(flagged_text, ev_mult, context or {}),
                            suggestions=self._generate_smart_multiplier_suggestions(flagged_text, ev_mult, sent, context or {}),
                            severity='medium' if ev_mult > 0.6 else 'low',
                            text=text,
                            context=context,
                            evidence_score=ev_mult,
                            span=span,
                            flagged_text=flagged_text
                        ))
        return errors

    # === EVIDENCE CALCULATION: SYMBOLS ===

    def _calculate_currency_symbol_evidence(self, flagged_text: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) for currency symbol usage issues.
        
        Following the 5-step evidence calculation pattern:
        1. Base Evidence Assessment
        2. Linguistic Clues (Micro-Level)
        3. Structural Clues (Meso-Level)
        4. Semantic Clues (Macro-Level)
        5. Feedback Patterns (Learning Clues)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.55  # Base evidence for symbol usage
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_currency_symbol(evidence_score, flagged_text, sentence, text)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_currency(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_currency(evidence_score, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_currency(evidence_score, flagged_text, context)
        
        return max(0.0, min(1.0, evidence_score))

    # === EVIDENCE CALCULATION: MULTIPLIERS ===

    def _calculate_currency_multiplier_evidence(self, flagged_text: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) for currency multiplier usage issues.
        
        Following the 5-step evidence calculation pattern:
        1. Base Evidence Assessment
        2. Linguistic Clues (Micro-Level)
        3. Structural Clues (Meso-Level)
        4. Semantic Clues (Macro-Level)
        5. Feedback Patterns (Learning Clues)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.65  # Base evidence for M/K multiplier usage
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_currency_multiplier(evidence_score, flagged_text, sentence, text)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_currency(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_currency(evidence_score, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_currency(evidence_score, flagged_text, context)
        
        return max(0.0, min(1.0, evidence_score))

    # === LINGUISTIC CLUES (MICRO-LEVEL) ===
    
    def _apply_linguistic_clues_currency_symbol(self, evidence_score: float, flagged_text: str, sentence, text: str) -> float:
        """Apply SpaCy-based linguistic analysis clues for currency symbol usage."""
        
        sentence_text = sentence.text
        sentence_lower = sentence_text.lower()
        
        # Strong reduction: ISO code present in same sentence
        iso_codes = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR", "KRW", "SEK", "NOK", "DKK", "ZAR", "MXN", "BRL"]
        if any(code in sentence_text for code in iso_codes):
            evidence_score -= 0.3  # ISO code present - symbol redundant
        
        # Reduction: Currency word clarification present
        currency_words = ['dollar', 'euro', 'pound', 'yen', 'franc', 'yuan', 'peso', 'rupee', 'won', 'krona', 'rand']
        if any(word in sentence_lower for word in currency_words):
            evidence_score -= 0.25  # Currency name clarifies symbol
        
        # Check for ISO code + amount pattern in sentence
        if re.search(r'\b(usd|eur|gbp|jpy|aud|cad|chf|cny|inr)\s+\d', sentence_text, flags=re.I):
            evidence_score -= 0.25  # Proper ISO format already used
        
        # Increase: Ambiguous symbol without clarification
        if re.search(r'[\$€£]\s?\d', flagged_text):
            if not any(word in sentence_lower for word in currency_words + [code.lower() for code in iso_codes]):
                evidence_score += 0.15  # Symbol only, no clarification
        
        # Check for quote context (might be showing UI or examples)
        if '"' in sentence_text or "'" in sentence_text:
            evidence_score -= 0.1  # Quoted text might preserve original format
        
        # Check for list of multiple currencies (comparison context)
        symbol_count = sum(sentence_text.count(symbol) for symbol in ['$', '€', '£', '¥', '₹'])
        if symbol_count > 1:
            evidence_score += 0.1  # Multiple currencies need ISO for clarity
        
        # Check for international context indicators
        international_indicators = ['global', 'international', 'worldwide', 'multi-currency', 'exchange rate', 'foreign']
        if any(indicator in sentence_lower for indicator in international_indicators):
            evidence_score += 0.2  # International context needs ISO codes
        
        # Check for amount ranges or comparisons
        if re.search(r'[\$€£]\s?\d[\d,.]*(.*?-.*?|.*?to.*?)[\$€£]\s?\d', sentence_text, flags=re.I):
            evidence_score += 0.1  # Ranges clearer with ISO codes
        
        # Check for mathematical operations with currencies
        math_operators = ['+', '-', '×', '*', '÷', '/', '=']
        if any(op in sentence_text for op in math_operators) and any(symbol in flagged_text for symbol in ['$', '€', '£']):
            evidence_score += 0.1  # Math operations clearer with ISO
        
        # Check for parenthetical amounts (often need clarification)
        if re.search(r'\([\$€£]\s?\d[\d,.]*\)', sentence_text):
            evidence_score += 0.05  # Parenthetical amounts often need ISO
        
        # Check for currency conversion context
        conversion_indicators = ['convert', 'equivalent', 'equals', 'rate', 'exchange']
        if any(indicator in sentence_lower for indicator in conversion_indicators):
            evidence_score += 0.15  # Conversion contexts need ISO clarity
        
        return evidence_score
    
    def _apply_linguistic_clues_currency_multiplier(self, evidence_score: float, flagged_text: str, sentence, text: str) -> float:
        """Apply SpaCy-based linguistic analysis clues for currency multiplier usage."""
        
        sentence_text = sentence.text
        sentence_lower = sentence_text.lower()
        
        # Strong reduction: Non-currency contexts
        tech_contexts = ['resolution', 'video', 'display', 'pixels', 'screen', 'monitor', 'kb', 'mb', 'gb', 'tb']
        if any(term in sentence_lower for term in tech_contexts):
            evidence_score -= 0.4  # Technical contexts use K/M for bytes/pixels
        
        # Check for file size contexts
        file_contexts = ['file', 'download', 'upload', 'storage', 'disk', 'memory', 'ram']
        if any(context in sentence_lower for context in file_contexts):
            evidence_score -= 0.35  # File size contexts use K/M/G
        
        # Check for performance/metrics contexts
        performance_contexts = ['speed', 'bandwidth', 'throughput', 'fps', 'hz', 'mhz', 'ghz']
        if any(context in sentence_lower for context in performance_contexts):
            evidence_score -= 0.3  # Performance metrics use K/M
        
        # Presence of ISO code (still prefer spelled-out amounts)
        iso_codes = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR"]
        if any(code in sentence_text for code in iso_codes):
            evidence_score -= 0.1  # ISO present but still prefer full amounts
        
        # Check for currency symbols alongside multipliers
        if re.search(r'[\$€£]\s?\d[\d,.]*[mk]\b', flagged_text, flags=re.I):
            evidence_score += 0.1  # Symbol + multiplier needs clarification
        
        # Check for financial/business context
        business_contexts = ['revenue', 'profit', 'budget', 'investment', 'funding', 'valuation', 'market cap']
        if any(context in sentence_lower for context in business_contexts):
            evidence_score += 0.15  # Business contexts need precise amounts
        
        # Check for legal/contract context
        legal_contexts = ['contract', 'agreement', 'legal', 'court', 'settlement', 'damages', 'fine']
        if any(context in sentence_lower for context in legal_contexts):
            evidence_score += 0.2  # Legal contexts require precise amounts
        
        return evidence_score

    # === STRUCTURAL CLUES (MESO-LEVEL) ===

    def _apply_structural_clues_currency(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for currency formatting."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Code contexts have different formatting rules
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.8  # Code often shows exact API responses or examples
        elif block_type == 'inline_code':
            evidence_score -= 0.6  # Inline code may show format examples
        
        # Table contexts often need consistent, compact formatting
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.1  # Tables may use symbols for space efficiency
            
            # Financial tables might need more precision
            if context.get('table_type') in ['financial', 'pricing', 'budget']:
                evidence_score += 0.1  # Financial tables benefit from ISO codes
        
        # Form contexts often use symbols for user familiarity
        elif block_type in ['form_field', 'form_label']:
            evidence_score -= 0.15  # Forms often use familiar symbols
        
        # List contexts
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.05  # Lists may use symbols for brevity
            
            # Pricing lists might need ISO codes
            if context.get('list_type') in ['pricing', 'comparison']:
                evidence_score += 0.1  # Pricing lists benefit from clarity
        
        # Heading contexts
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.05  # Headings may use either format
            
            # Main headings might need formal ISO codes
            heading_level = context.get('block_level', 1)
            if heading_level == 1:  # H1 - main headings
                evidence_score += 0.05  # Main headings more formal
        
        # Admonition contexts
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['WARNING', 'CAUTION', 'IMPORTANT']:
                evidence_score += 0.1  # Critical info needs clarity
            elif admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score -= 0.05  # Informal contexts more flexible
        
        # Quote/citation contexts may preserve original style
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.2  # Quotes preserve original formatting
        
        return evidence_score

    # === SEMANTIC CLUES (MACRO-LEVEL) ===

    def _apply_semantic_clues_currency(self, evidence_score: float, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for currency formatting."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Content type adjustments
        if content_type == 'technical':
            evidence_score += 0.1  # Technical docs benefit from precision
        elif content_type == 'api':
            evidence_score += 0.15  # API docs need consistent, clear formats
        elif content_type == 'legal':
            evidence_score += 0.25  # Legal documents require precision
        elif content_type == 'academic':
            evidence_score += 0.1  # Academic writing prefers formal notation
        elif content_type == 'financial':
            evidence_score += 0.2  # Financial content needs ISO clarity
        elif content_type == 'marketing':
            evidence_score -= 0.1  # Marketing may use familiar symbols
        elif content_type == 'narrative':
            evidence_score -= 0.15  # Narrative writing more flexible
        elif content_type == 'procedural':
            evidence_score += 0.05  # Procedures benefit from clarity
        
        # Domain-specific adjustments
        if domain == 'finance':
            evidence_score += 0.2  # Financial domain requires precision
        elif domain == 'legal':
            evidence_score += 0.25  # Legal domain requires unambiguous notation
        elif domain == 'banking':
            evidence_score += 0.2  # Banking needs clear currency notation
        elif domain == 'insurance':
            evidence_score += 0.15  # Insurance documents need precision
        elif domain == 'accounting':
            evidence_score += 0.2  # Accounting requires precise notation
        elif domain == 'investment':
            evidence_score += 0.15  # Investment contexts need clarity
        elif domain == 'ecommerce':
            evidence_score -= 0.05  # E-commerce may use familiar symbols
        elif domain == 'retail':
            evidence_score -= 0.1  # Retail often uses symbols for familiarity
        elif domain == 'gaming':
            evidence_score -= 0.1  # Gaming contexts more casual
        
        # Audience adjustments
        if audience == 'international':
            evidence_score += 0.2  # International audience needs ISO codes
        elif audience in ['global', 'worldwide']:
            evidence_score += 0.15  # Global audience benefits from ISO
        elif audience in ['beginner', 'general']:
            evidence_score += 0.1  # General audience needs clarity
        elif audience in ['expert', 'professional']:
            evidence_score += 0.05  # Professionals expect proper notation
        elif audience == 'developer':
            evidence_score += 0.1  # Developers need consistent formats
        elif audience == 'consumer':
            evidence_score -= 0.05  # Consumers familiar with symbols
        
        # Document-level analysis
        text_lower = text.lower()
        
        # Check for international context in document
        international_indicators = [
            'international', 'global', 'worldwide', 'multi-currency', 'exchange rate',
            'foreign exchange', 'cross-border', 'overseas', 'multinational'
        ]
        if any(indicator in text_lower for indicator in international_indicators):
            evidence_score += 0.15  # Document has international scope
        
        # Check for multiple currency mentions
        currencies = ['usd', 'eur', 'gbp', 'jpy', 'aud', 'cad', 'chf', 'cny', 'inr', 'dollar', 'euro', 'pound', 'yen']
        currency_count = sum(text_lower.count(currency) for currency in currencies)
        if currency_count > 3:
            evidence_score += 0.1  # Multiple currencies need consistent ISO notation
        
        return evidence_score

    # === FEEDBACK PATTERNS (LEARNING CLUES) ===

    def _apply_feedback_clues_currency(self, evidence_score: float, flagged_text: str, context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for currency formatting."""
        
        feedback_patterns = self._get_cached_feedback_patterns_currency()
        
        flagged_lower = flagged_text.lower()
        
        # Consistently accepted formats
        if flagged_lower in feedback_patterns.get('often_accepted_symbols', set()):
            evidence_score -= 0.3  # Strong acceptance pattern for symbols
        elif flagged_lower in feedback_patterns.get('often_accepted_multipliers', set()):
            evidence_score -= 0.25  # Acceptance pattern for multipliers
        
        # Consistently flagged formats
        elif flagged_lower in feedback_patterns.get('often_flagged_symbols', set()):
            evidence_score += 0.2  # Strong rejection pattern for symbols
        elif flagged_lower in feedback_patterns.get('often_flagged_multipliers', set()):
            evidence_score += 0.25  # Strong rejection pattern for multipliers
        
        # Context-specific patterns
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Symbol vs ISO preference by context
        iso_preferences = feedback_patterns.get('iso_preference_by_context', {})
        context_key = f"{content_type}_{domain}_{audience}"
        
        if context_key in iso_preferences:
            iso_preference = iso_preferences[context_key]
            if '$' in flagged_text or '€' in flagged_text or '£' in flagged_text:  # Symbol usage
                if iso_preference > 0.8:  # Strong ISO preference
                    evidence_score += 0.2
                elif iso_preference < 0.3:  # Strong symbol preference
                    evidence_score -= 0.15
        
        return evidence_score

    def _get_cached_feedback_patterns_currency(self) -> Dict[str, Any]:
        """Load feedback patterns for currency formatting from cache or feedback analysis."""
        return {
            'often_accepted_symbols': {'$10', '$5', '€20', '£15'},  # Small, common amounts
            'often_accepted_multipliers': set(),  # Context-dependent
            'often_flagged_symbols': {'$1000000', '€500000', '£1000000'},  # Large amounts need ISO
            'often_flagged_multipliers': {'4m', '10k', '100m'},  # Ambiguous multipliers
            
            # ISO preference by context (0.0 = symbols, 1.0 = ISO codes)
            'iso_preference_by_context': {
                'legal_finance_professional': 0.9,     # Strong ISO preference
                'api_finance_developer': 0.95,         # Very strong ISO preference
                'academic_finance_expert': 0.85,       # Strong ISO preference
                'technical_banking_professional': 0.9, # Strong ISO preference
                'marketing_retail_consumer': 0.2,      # Strong symbol preference
                'narrative_general_general': 0.3,      # Symbol preference
                'ecommerce_retail_consumer': 0.25,     # Strong symbol preference
                'documentation_finance_general': 0.8,  # ISO preference
            },
        }

    # === SMART MESSAGING & SUGGESTIONS ===

    def _get_contextual_currency_symbol_message(self, flagged_text: str, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for currency symbol usage."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        if evidence_score > 0.85:
            if audience == 'international':
                return f"International audience requires ISO currency codes: replace '{flagged_text}' with 'USD {flagged_text[1:]}' (or appropriate ISO code)."
            elif domain in ['finance', 'legal', 'banking']:
                return f"Financial/legal documents require precise currency notation: use ISO codes instead of '{flagged_text}'."
            elif content_type == 'api':
                return f"API documentation should use ISO currency codes for consistency and clarity."
            else:
                return "Use the three-letter ISO currency code before the amount for global audiences."
        
        elif evidence_score > 0.6:
            if content_type in ['technical', 'procedural']:
                return f"Technical documentation benefits from ISO currency codes (e.g., 'USD 100') instead of symbols."
            elif audience in ['professional', 'expert']:
                return f"Professional context: consider using ISO currency code instead of '{flagged_text}'."
            else:
                return "Consider using the ISO currency code (e.g., 'USD 100') instead of a symbol."
        
        else:
            return "ISO currency codes improve clarity for international readers."

    def _generate_smart_currency_symbol_suggestions(self, flagged_text: str, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for currency symbol usage."""
        
        suggestions = []
        
        # Extract amount from flagged text
        amount = re.sub(r'^[\$€£¥₹]\s?', '', flagged_text)
        
        # Determine appropriate ISO code based on symbol
        symbol_to_iso = {'$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₹': 'INR'}
        detected_symbol = next((symbol for symbol in symbol_to_iso.keys() if symbol in flagged_text), '$')
        iso_code = symbol_to_iso.get(detected_symbol, 'USD')
        
        # Generate suggestions
        suggestions.append(f"Replace with '{iso_code} {amount}' (or appropriate ISO code).")
        suggestions.append("Use ISO codes (USD, EUR, GBP) consistently across the document.")
        
        audience = context.get('audience', 'general')
        if audience == 'international':
            suggestions.append("International audiences require ISO currency codes to avoid confusion.")
        
        return suggestions[:3]

    def _get_contextual_multiplier_message(self, flagged_text: str, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for currency multiplier usage."""
        
        domain = context.get('domain', 'general')
        
        if evidence_score > 0.8:
            if domain in ['legal', 'finance', 'banking']:
                return f"Legal/financial documents require precise amounts: spell out '{flagged_text}' completely (e.g., 'USD 4,000,000')."
            else:
                return f"Avoid letter abbreviations like '{flagged_text}' for currency. Spell out the full amount."
        
        elif evidence_score > 0.6:
            return f"Consider spelling out currency multipliers instead of '{flagged_text}'."
        
        else:
            return "Spell out currency multipliers for clarity (e.g., '4 million')."

    def _generate_smart_multiplier_suggestions(self, flagged_text: str, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for currency multiplier usage."""
        
        suggestions = []
        
        # Extract numeric portion and multiplier
        num_match = re.findall(r'\d[\d,.]*', flagged_text)
        num_str = num_match[0] if num_match else ''
        
        multiplier = 'k' if 'k' in flagged_text.lower() else 'm' if 'm' in flagged_text.lower() else ''
        
        # Determine appropriate ISO code (default to USD)
        iso_code = 'USD'
        
        # Generate suggestions
        if multiplier == 'm':
            suggestions.append(f"Use '{iso_code} {num_str} million' or '{iso_code} {num_str},000,000'.")
        elif multiplier == 'k':
            suggestions.append(f"Use '{iso_code} {num_str} thousand' or '{iso_code} {num_str},000'.")
        else:
            suggestions.append("Spell out the full number with an ISO currency code.")
        
        suggestions.append("Ensure numeric formatting uses separators appropriate for the style guide.")
        
        return suggestions[:3]
