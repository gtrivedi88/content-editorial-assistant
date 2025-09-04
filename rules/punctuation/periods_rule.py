"""
Periods Rule - Evidence-Based Analysis
Based on IBM Style Guide topic: "Periods"

**UPDATED** with evidence-based scoring for nuanced period usage analysis.
"""
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule
from .services.punctuation_config_service import get_punctuation_config

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class PeriodsRule(BasePunctuationRule):
    """
    Checks for incorrect use of periods using evidence-based analysis:
    - Periods within uppercase abbreviations
    - Other period usage violations
    Enhanced with dependency parsing and contextual awareness.
    """
    def __init__(self):
        """Initialize the rule with configuration service."""
        super().__init__()
        self.config = get_punctuation_config()
    
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'periods'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Enhanced evidence-based analysis for period usage violations:
        - Periods within uppercase abbreviations
        - Duplicate periods (e.g., ".." or "...")
        - Extra periods in lists, headings
        - Missing periods at sentence endings
        - Context-aware period rules for different content types
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Fallback analysis when nlp is not available
        if not nlp:
            return self._fallback_enhanced_periods_analysis(text, sentences, context)

        try:
            doc = nlp(text)
            
            # Analyze periods in abbreviations (existing functionality)
            for i, sent in enumerate(doc.sents):
                for token in sent:
                    # Look for tokens that contain periods in abbreviations (e.g., "U.S.A.")
                    if self._is_abbreviation_with_periods(token):
                        evidence_score = self._calculate_period_evidence(token, sent, text, context)
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_period_message('abbreviation_periods', evidence_score, context),
                                suggestions=self._generate_smart_period_suggestions(token, evidence_score, context),
                                severity='low' if evidence_score < 0.7 else 'medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text,
                                violation_type='abbreviation_periods'
                            ))
            
            # NEW: Analyze duplicate periods
            errors.extend(self._analyze_duplicate_periods(doc, text, context))
            
            # NEW: Analyze unnecessary periods in headings and lists
            errors.extend(self._analyze_unnecessary_periods(doc, text, context))
            
            # NEW: Analyze missing periods at sentence endings
            errors.extend(self._analyze_missing_periods(doc, text, context))
            
        except Exception as e:
            # Graceful degradation for SpaCy errors
            return self._fallback_enhanced_periods_analysis(text, sentences, context)
        
        return errors

    # === EVIDENCE CALCULATION ===

    def _is_abbreviation_with_periods(self, token: 'Token') -> bool:
        """
        Check if this token is an abbreviation containing periods.
        SpaCy tokenizes "U.S.A." as a single token, so we check the token text.
        """
        import re
        # Pattern for abbreviations with periods (e.g., U.S.A., A.P.I., E.U.)
        return bool(re.match(r'^[A-Z]\.(?:[A-Z]\.)*[A-Z]?\.?$', token.text))

    def _calculate_period_evidence(self, abbrev_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that a period usage is incorrect.
        
        Higher scores indicate stronger evidence of an error.
        Lower scores indicate acceptable usage or ambiguous cases.
        """
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply surgical guards FIRST to eliminate false positives
        if self._apply_zero_false_positive_guards_punctuation(abbrev_token, context):
            return 0.0
        
        # Creative content commonly uses various punctuation styles
        content_type = context.get('content_type', 'general')
        if content_type in ['creative', 'literary', 'narrative']:
            return 0.0
        
        # Legal documents often require periods in abbreviations
        if content_type == 'legal':
            return 0.0
        
        # Quotes preserve original punctuation
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['quote', 'blockquote']:
            return 0.0
        
        # Citations and academic references have specific formatting
        if block_type in ['citation', 'reference', 'footnote', 'bibliography']:
            return 0.0
        
        # Check for legitimate abbreviations that should keep periods
        if self._is_legitimate_abbreviation_period(abbrev_token, sent, context):
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Start with strong evidence for abbreviation periods
        evidence_score = 0.8
        
        # === STEP 2: LINGUISTIC CLUES ===
        evidence_score = self._apply_common_linguistic_clues_punctuation(evidence_score, abbrev_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES ===
        evidence_score = self._apply_common_structural_clues_punctuation(evidence_score, abbrev_token, context)
        
        # === STEP 4: SEMANTIC CLUES ===
        evidence_score = self._apply_common_semantic_clues_punctuation(evidence_score, abbrev_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _is_legitimate_abbreviation_period(self, abbrev_token: 'Token', sent: 'Span', context: Dict[str, Any]) -> bool:
        """
        Check if this abbreviation period usage is legitimate in this context.
        """
        # Check for legitimate abbreviations that should keep periods (from YAML configuration)
        if self.config.is_legitimate_abbreviation(abbrev_token.text)[0]:
            return True
        
        return False

    # === ENHANCED PERIODS ANALYSIS METHODS ===

    def _fallback_enhanced_periods_analysis(self, text: str, sentences: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced fallback analysis when spaCy is not available."""
        errors = []
        
        # Apply basic guards for fallback analysis
        content_type = context.get('content_type', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        # Skip if in contexts where periods might be used differently
        if content_type in ['creative', 'literary', 'narrative', 'legal']:
            return errors  # No errors for creative or legal content
        if block_type in ['quote', 'blockquote', 'code_block', 'literal_block', 'citation']:
            return errors  # No errors for quotes, code, and citations
        
        import re
        
        # 1. Existing: Abbreviations with periods (e.g., U.S.A., A.P.I., E.U.)
        for i, sentence in enumerate(sentences):
            for match in re.finditer(r'\b[A-Z]\.(?:[A-Z]\.)*[A-Z]?\.?\b', sentence):
                match_text = match.group(0)
                
                # Check for legitimate abbreviations that should keep periods
                legitimate_patterns = ['P.M.', 'A.M.', 'P.O.', 'U.K.', 'U.S.', 'P.M', 'A.M', 'P.O', 'U.K', 'U.S']
                if match_text.upper() in legitimate_patterns:
                    continue  # Skip legitimate time/location abbreviations
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Consider removing periods from this abbreviation for modern style.",
                    suggestions=["Remove periods from abbreviations (e.g., 'USA' instead of 'U.S.A.')", "Modern style guides prefer clean abbreviations without periods."],
                    severity='low',
                    text=text,
                    context=context,
                    evidence_score=0.7,  # Default evidence for fallback analysis
                    span=(match.start(), match.end()),
                    flagged_text=match_text,
                    violation_type='abbreviation_periods'
                ))
        
        # 2. NEW: Duplicate periods (exclude legitimate ellipses)
        for match in re.finditer(r'\.{2,}(?!\.)', text):
            if len(match.group()) == 2:  # Double periods are usually errors
                evidence_score = 0.8
            else:
                continue  # Skip potential ellipses (3+ periods)
            
            errors.append(self._create_error(
                sentence=self._get_sentence_for_position(match.start(), text),
                sentence_index=0,
                message="Double periods detected - likely a typo.",
                suggestions=["Remove extra period.", "Use single period for sentence ending.", "Use ellipsis (...) if trailing off is intended."],
                severity='medium',
                text=text,
                context=context,
                evidence_score=evidence_score,
                span=(match.start(), match.end()),
                flagged_text=match.group(),
                violation_type='duplicate_periods'
            ))
        
        return errors

    def _analyze_duplicate_periods(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze text for duplicate periods using spaCy."""
        errors = []
        
        import re
        # Pattern for duplicate periods (excluding legitimate ellipses)
        for match in re.finditer(r'\.{2}(?!\.)', text):  # Exactly two periods (not ellipses)
            evidence_score = self._calculate_duplicate_periods_evidence(match, text, context)
            
            if evidence_score > 0.1:
                errors.append(self._create_error(
                    sentence=self._get_sentence_for_position(match.start(), text),
                    sentence_index=self._get_sentence_index_for_position(match.start(), doc),
                    message=self._get_contextual_period_message('duplicate_periods', evidence_score, context),
                    suggestions=self._generate_duplicate_periods_suggestions(evidence_score, context),
                    severity='medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(match.start(), match.end()),
                    flagged_text=match.group(),
                    violation_type='duplicate_periods'
                ))
        
        return errors

    def _analyze_unnecessary_periods(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze text for unnecessary periods in headings and lists."""
        errors = []
        
        block_type = context.get('block_type', 'paragraph')
        
        # Check headings for unnecessary periods
        if block_type == 'heading':
            if text.strip().endswith('.'):
                evidence_score = self._calculate_unnecessary_period_evidence('heading', text, context)
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=text.strip(),
                        sentence_index=0,
                        message=self._get_contextual_period_message('unnecessary_period_in_heading', evidence_score, context),
                        suggestions=self._generate_unnecessary_period_suggestions('heading', evidence_score, context),
                        severity='low',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(len(text.rstrip()) - 1, len(text.rstrip())),
                        flagged_text='.',
                        violation_type='unnecessary_period_in_heading'
                    ))
        
        # Check list items for unnecessary periods
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            stripped_text = text.strip()
            if stripped_text.endswith('.'):
                evidence_score = self._calculate_unnecessary_period_evidence('list_item', text, context)
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=stripped_text,
                        sentence_index=0,
                        message=self._get_contextual_period_message('unnecessary_period_in_list', evidence_score, context),
                        suggestions=self._generate_unnecessary_period_suggestions('list_item', evidence_score, context),
                        severity='low',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(len(text.rstrip()) - 1, len(text.rstrip())),
                        flagged_text='.',
                        violation_type='unnecessary_period_in_list'
                    ))
        
        return errors

    def _analyze_missing_periods(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze text for missing periods at sentence endings."""
        errors = []
        
        # Skip contexts where missing periods are acceptable
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['heading', 'ordered_list_item', 'unordered_list_item', 'table_cell']:
            return errors
        
        # Check each sentence for missing end punctuation
        for i, sent in enumerate(doc.sents):
            sentence_text = sent.text.strip()
            
            # Skip very short sentences and questions/exclamations
            if len(sentence_text) < 10 or sentence_text.endswith(('?', '!')):
                continue
            
            # Check if sentence ends without proper punctuation
            if not sentence_text.endswith(('.', ':', ';')):
                evidence_score = self._calculate_missing_period_evidence(sent, text, context)
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sentence_text,
                        sentence_index=i,
                        message=self._get_contextual_period_message('missing_period', evidence_score, context),
                        suggestions=self._generate_missing_period_suggestions(evidence_score, context),
                        severity='medium' if evidence_score > 0.7 else 'low',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(sent[-1].idx + len(sent[-1].text), sent[-1].idx + len(sent[-1].text)),
                        flagged_text=sent[-1].text,
                        violation_type='missing_period'
                    ))
        
        return errors

    # === ENHANCED EVIDENCE CALCULATION ===
    
    def _calculate_duplicate_periods_evidence(self, match, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for duplicate period violations."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return 0.0
        
        if context.get('content_type') in ['creative', 'literary']:
            return 0.0  # Creative writing may use unusual punctuation
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.9  # Very strong evidence for duplicate periods
        
        # === STEP 2: CONTEXT CLUES ===
        # Double periods are almost always errors in standard text
        return max(0.0, min(1.0, evidence_score))

    def _calculate_unnecessary_period_evidence(self, location_type: str, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for unnecessary period violations."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return 0.0
        
        if context.get('content_type') in ['creative', 'literary']:
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        if location_type == 'heading':
            evidence_score = 0.7  # Good evidence - headings usually don't end with periods
        elif location_type == 'list_item':
            # Check if it's a complete sentence
            word_count = len(text.strip().split())
            if word_count <= 3:
                evidence_score = 0.8  # Strong evidence for short items
            elif word_count <= 6:
                evidence_score = 0.6  # Medium evidence for medium items
            else:
                evidence_score = 0.3  # Weak evidence for long items (might be sentences)
        else:
            evidence_score = 0.5
        
        # === STEP 2: CONTEXT CLUES ===
        content_type = context.get('content_type', 'general')
        if content_type == 'formal':
            evidence_score -= 0.1  # Formal documents might be more flexible
        elif content_type == 'technical':
            evidence_score += 0.1  # Technical docs prefer clean formatting
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_missing_period_evidence(self, sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for missing period violations."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return 0.0
        
        # Check if sentence ends with other acceptable punctuation
        sentence_text = sent.text.strip()
        if sentence_text.endswith((':', ';', '-', ')', ']')):
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.6  # Medium evidence for missing periods
        
        # === STEP 2: SENTENCE ANALYSIS ===
        # Complete sentences with verbs are more likely to need periods
        has_verb = any(token.pos_ == 'VERB' for token in sent)
        if has_verb:
            evidence_score += 0.2
        
        # Longer sentences are more likely to need periods
        word_count = len([token for token in sent if token.is_alpha])
        if word_count > 8:
            evidence_score += 0.1
        
        # === STEP 3: CONTEXT CLUES ===
        content_type = context.get('content_type', 'general')
        if content_type == 'formal':
            evidence_score += 0.1  # Formal writing needs proper punctuation
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===
    
    def _get_sentence_for_position(self, position: int, text: str) -> str:
        """Get the sentence containing a specific text position."""
        # Find sentence boundaries around the position
        start = max(0, text.rfind('.', 0, position) + 1)
        end = text.find('.', position)
        if end == -1:
            end = len(text)
        
        return text[start:end].strip()
    
    def _get_sentence_index_for_position(self, position: int, doc: 'Doc') -> int:
        """Get the sentence index for a specific text position."""
        for i, sent in enumerate(doc.sents):
            if sent.start_char <= position < sent.end_char:
                return i
        return 0

    # === SMART MESSAGING ===

    def _get_contextual_period_message(self, violation_type: str, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for period usage."""
        confidence_phrase = "clearly has" if evidence_score > 0.8 else ("likely has" if evidence_score > 0.6 else "may have")
        
        messages = {
            'abbreviation_periods': f"This text {confidence_phrase} unnecessary periods within abbreviations.",
            'duplicate_periods': f"This text {confidence_phrase} duplicate periods that should be corrected.",
            'unnecessary_period_in_heading': f"This heading {confidence_phrase} an unnecessary period at the end.",
            'unnecessary_period_in_list': f"This list item {confidence_phrase} an unnecessary period.",
            'missing_period': f"This sentence {confidence_phrase} a missing period at the end."
        }
        
        # Fallback for legacy calls without violation_type
        if violation_type == 'abbreviation_periods' or not violation_type:
            if evidence_score > 0.8:
                return "Avoid using periods within uppercase abbreviations."
            elif evidence_score > 0.6:
                return "Consider removing periods from this uppercase abbreviation."
            else:
                return "Review period usage in this abbreviation for style consistency."
        
        return messages.get(violation_type, f"This text {confidence_phrase} a period usage issue.")

    def _generate_smart_period_suggestions(self, period_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for period usage."""
        suggestions = []
        
        if evidence_score > 0.7:
            suggestions.append("Remove the periods from the abbreviation (e.g., 'USA' instead of 'U.S.A.').")
            suggestions.append("Modern style guides prefer abbreviations without internal periods.")
        else:
            suggestions.append("Consider removing periods for a cleaner, modern style.")
            suggestions.append("Check your style guide's preference for abbreviation periods.")
        
        # Context-specific suggestions
        content_type = context.get('content_type', 'general')
        if content_type == 'technical':
            suggestions.append("Technical documentation typically uses abbreviations without periods.")
        elif content_type == 'legal':
            suggestions.append("Legal documents may require periods in abbreviations - check your style guide.")
        elif content_type == 'academic':
            suggestions.append("Academic style may vary - consult your institution's guidelines.")
        
        return suggestions[:3]
    
    def _generate_duplicate_periods_suggestions(self, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate suggestions for duplicate periods."""
        return [
            "Remove the extra period.",
            "Use a single period to end sentences.",
            "Use ellipsis (...) if trailing off is intended."
        ]
    
    def _generate_unnecessary_period_suggestions(self, location_type: str, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate suggestions for unnecessary periods."""
        if location_type == 'heading':
            return [
                "Remove the period from this heading.",
                "Headings are titles, not complete sentences.",
                "Use periods only for complete sentences."
            ]
        elif location_type == 'list_item':
            return [
                "Remove the period from this list item.",
                "Use periods only for complete sentences in lists.",
                "Keep list items concise without periods."
            ]
        else:
            return ["Remove the unnecessary period."]
    
    def _generate_missing_period_suggestions(self, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate suggestions for missing periods."""
        return [
            "Add a period to end this sentence.",
            "Complete sentences should end with periods.",
            "Use proper punctuation for sentence endings."
        ]
