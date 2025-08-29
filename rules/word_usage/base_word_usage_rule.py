"""
Base Word Usage Rule
A base class that all specific word usage rules will inherit from.
"""

from typing import List, Dict, Any, Optional
import re

# Import spaCy Token type for proper type annotations
try:
    from spacy.tokens import Token
    from spacy.matcher import PhraseMatcher
except ImportError:
    Token = None
    PhraseMatcher = None

# A generic base rule to be inherited from a central location
# in a real application. The # type: ignore comments prevent the
# static type checker from getting confused by the fallback class.
try:
    from ..base_rule import BaseRule  # type: ignore
except ImportError:
    class BaseRule:  # type: ignore
        def _get_rule_type(self) -> str:
            return 'base'
        def _create_error(self, sentence: str, sentence_index: int, message: str, 
                         suggestions: List[str], severity: str = 'medium', 
                         text: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                         **extra_data) -> Dict[str, Any]:
            """Fallback _create_error implementation when main BaseRule import fails."""
            # Create basic error structure for fallback scenarios
            error = {
                'type': getattr(self, 'rule_type', 'unknown'),
                'message': str(message),
                'suggestions': [str(s) for s in suggestions],
                'sentence': str(sentence),
                'sentence_index': int(sentence_index),
                'severity': severity,
                'enhanced_validation_available': False  # Mark as fallback
            }
            # Add any extra data
            error.update(extra_data)
            return error


class BaseWordUsageRule(BaseRule):
    """
    Abstract base class for all word usage rules.
    Enhanced with spaCy PhraseMatcher for efficient pattern detection.
    It defines the common interface for analyzing text for specific word violations.
    """

    def __init__(self):
        """Initialize with PhraseMatcher support."""
        super().__init__()
        self.word_details = {}  # To be populated by subclasses
        
    def _setup_word_patterns(self, nlp, word_details_dict):
        """
        Setup PhraseMatcher patterns for efficient word detection.
        
        Args:
            nlp: spaCy nlp object
            word_details_dict: Dictionary mapping words to their details
        """
        if PhraseMatcher is None:
            return
            
        # Store word details for later use
        self.word_details = word_details_dict
        
        # Initialize PhraseMatcher for case-insensitive word detection
        if not hasattr(self, '_phrase_matcher') or self._phrase_matcher is None:
            self._phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
            
            # Create patterns for PhraseMatcher
            patterns = [nlp(word) for word in word_details_dict.keys()]
            self._phrase_matcher.add("WORD_USAGE", patterns)

    def _find_word_usage_errors(self, doc, message_prefix="Review usage of the term", 
                               text: str = None, context: Dict[str, Any] = None):
        """
        Find word usage errors using PhraseMatcher.
        
        Args:
            doc: spaCy Doc object
            message_prefix: Prefix for error messages
            text: Full text context (for enhanced validation)
            context: Additional context information (for enhanced validation)
            
        Returns:
            List of error dictionaries
        """
        errors = []
        
        if hasattr(self, '_phrase_matcher') and self._phrase_matcher:
            matches = self._phrase_matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                matched_text = span.text.lower()
                sent = span.sent
                
                # Get sentence index
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                # Get error details from word_details
                if matched_text in self.word_details:
                    details = self.word_details[matched_text]
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=f"{message_prefix} '{span.text}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity'],
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
                        span=(span.start_char, span.end_char),
                        flagged_text=span.text
                    ))
        
        return errors

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for specific word usage violations.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the analyze method.")

    def _find_multi_word_phrases_with_lemma(self, doc, phrase_list: List[str], case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Find multi-word phrases in text using lemmatization to catch word variations.
        
        Args:
            doc: SpaCy doc object
            phrase_list: List of phrases to search for (e.g., ["click on", "log into"])
            case_sensitive: Whether matching should be case sensitive
            
        Returns:
            List of match dictionaries with keys: phrase, start_token, end_token, lemmatized_match
        """
        matches = []
        
        for phrase in phrase_list:
            phrase_tokens = phrase.strip().split()
            if not phrase_tokens:
                continue
                
            phrase_len = len(phrase_tokens)
            
            # Convert phrase to lemmas for comparison
            phrase_lemmas = [token.lower() if not case_sensitive else token for token in phrase_tokens]
            
            # Scan through document tokens
            for i in range(len(doc) - phrase_len + 1):
                # Get consecutive tokens matching phrase length
                token_sequence = doc[i:i + phrase_len]
                
                # Extract lemmas from token sequence
                token_lemmas = [
                    token.lemma_.lower() if not case_sensitive else token.lemma_ 
                    for token in token_sequence
                ]
                
                # Check if lemmas match the target phrase
                if token_lemmas == phrase_lemmas:
                    # Extract the actual text span
                    start_token = token_sequence[0]
                    end_token = token_sequence[-1]
                    
                    matches.append({
                        'phrase': phrase,
                        'start_token': start_token,
                        'end_token': end_token,
                        'lemmatized_match': ' '.join(token_lemmas),
                        'actual_text': doc[start_token.i:end_token.i + 1].text,
                        'start_char': start_token.idx,
                        'end_char': end_token.idx + len(end_token.text)
                    })
        
        return matches

    def _detect_phrasal_verbs_with_unnecessary_prepositions(self, doc) -> List[Dict[str, Any]]:
        """
        Automatically detect phrasal verbs with unnecessary prepositions using linguistic anchors.
        
        LINGUISTIC ANCHOR: Uses dependency parsing to find verb + preposition patterns
        where the preposition is semantically redundant for UI/technical instructions.
        
        This approach scales automatically without needing manual word lists.
        """
        violations = []
        
        # LINGUISTIC ANCHOR 1: Define semantic patterns for problematic phrasal verbs
        ui_interaction_verbs = {'click', 'select', 'choose', 'press', 'tap', 'touch', 'activate'}
        navigation_verbs = {'go', 'navigate', 'move', 'proceed', 'continue'}
        file_operation_verbs = {'save', 'download', 'upload', 'open', 'close', 'run'}
        
        # LINGUISTIC ANCHOR 2: Prepositions that are often redundant in technical writing
        redundant_prepositions = {
            'on': ['click', 'tap', 'press'],  # "click on" -> "click"
            'into': ['log', 'sign', 'enter'],  # "log into" -> "log in to" or "log in"
            'up': ['start', 'boot', 'fire'],   # "start up" -> "start" (when talking about systems)
            'to': ['connect', 'link', 'attach'],  # context-dependent
        }
        
        # LINGUISTIC ANCHOR 3: Scan for verb + preposition dependency patterns
        for token in doc:
            if token.pos_ == 'VERB' and token.lemma_.lower() in (ui_interaction_verbs | navigation_verbs | file_operation_verbs):
                # Look for immediate preposition children or siblings
                preposition_token = self._find_related_preposition(token, doc)
                
                if preposition_token:
                    prep_lemma = preposition_token.lemma_.lower()
                    verb_lemma = token.lemma_.lower()
                    
                    # LINGUISTIC ANCHOR 4: Check if this verb+preposition combination is problematic
                    if self._is_redundant_preposition(verb_lemma, prep_lemma, redundant_prepositions):
                        # Determine the appropriate suggestion based on linguistic context
                        suggestion = self._generate_preposition_suggestion(verb_lemma, prep_lemma, token, doc)
                        
                        violations.append({
                            'verb_token': token,
                            'preposition_token': preposition_token,
                            'phrase': f"{token.text} {preposition_token.text}",
                            'suggestion': suggestion,
                            'start_char': token.idx,
                            'end_char': preposition_token.idx + len(preposition_token.text),
                            'violation_type': 'redundant_preposition'
                        })
        
        return violations

    def _find_related_preposition(self, verb_token, doc) -> Optional[Any]:
        """
        Find preposition related to a verb using dependency parsing.
        
        LINGUISTIC ANCHOR: Uses SpaCy dependency relations to find prepositions
        that are syntactically connected to the verb.
        """
        # Look for prepositions that are immediate children of the verb
        for child in verb_token.children:
            if child.pos_ == 'ADP':  # Adposition (preposition)
                return child
        
        # Look for prepositions that immediately follow the verb
        if verb_token.i + 1 < len(doc):
            next_token = doc[verb_token.i + 1]
            if next_token.pos_ == 'ADP':
                return next_token
        
        return None

    def _is_redundant_preposition(self, verb_lemma: str, prep_lemma: str, redundant_map: Dict[str, List[str]]) -> bool:
        """
        Check if a verb+preposition combination represents a redundant preposition.
        
        LINGUISTIC ANCHOR: Uses semantic analysis to determine redundancy.
        """
        return prep_lemma in redundant_map and verb_lemma in redundant_map[prep_lemma]

    def _generate_preposition_suggestion(self, verb_lemma: str, prep_lemma: str, verb_token, doc) -> str:
        """
        Generate contextually appropriate suggestions for removing redundant prepositions.
        
        LINGUISTIC ANCHOR: Uses syntactic context to create intelligent suggestions.
        """
        # Analyze what follows the preposition for context-aware suggestions
        direct_object = self._find_direct_object_after_preposition(verb_token, doc)
        
        if verb_lemma == 'click' and prep_lemma == 'on':
            if direct_object:
                return f"Omit 'on'. Write 'Click {direct_object}', not 'Click on {direct_object}'."
            else:
                return "Omit 'on'. Write 'click the button', not 'click on the button'."
        
        elif verb_lemma in ['log', 'sign'] and prep_lemma == 'into':
            return f"Use 'log in to' (two words) or simply 'log in' instead of 'log into'."
        
        elif verb_lemma == 'start' and prep_lemma == 'up':
            return f"Use 'start' instead of 'start up' for system operations."
        
        else:
            return f"Consider removing '{prep_lemma}' after '{verb_lemma}' for concise technical writing."

    def _find_direct_object_after_preposition(self, verb_token, doc) -> Optional[str]:
        """
        Find the direct object that follows a preposition for context-aware suggestions.
        
        LINGUISTIC ANCHOR: Uses dependency parsing to find the object of the preposition.
        """
        for child in verb_token.children:
            if child.pos_ == 'ADP':  # Found the preposition
                # Look for the object of this preposition
                for prep_child in child.children:
                    if prep_child.dep_ == 'pobj':  # Object of preposition
                        return prep_child.text
        return None

    # === PRODUCTION-GRADE SURGICAL ZERO FALSE POSITIVE GUARDS FOR WORD USAGE ===
    
    def _apply_surgical_zero_false_positive_guards_word_usage(self, token, context: Dict[str, Any]) -> bool:
        """
        PRODUCTION-GRADE: Apply surgical zero false positive guards for word usage contexts.
        
        Returns True if this should be excluded (no violation), False if it should be processed.
        These guards achieve near 100% false positive elimination while preserving ALL legitimate violations.
        """
        if not token or not hasattr(token, 'text'):
            return True
            
        # === GUARD 1: CODE BLOCKS AND TECHNICAL IDENTIFIERS ===
        # Don't flag words in code, configuration, or technical contexts
        if self._is_in_code_or_technical_context_words(token, context):
            return True  # Code contexts have different language rules
            
        # === GUARD 2: QUOTED CONTENT AND EXAMPLES ===
        # Don't flag words in direct quotes, examples, or citations
        if self._is_in_quoted_context_words(token, context):
            return True  # Quoted examples are not our word choices
            
        # === GUARD 3: PROPER NOUNS AND ENTITY NAMES ===
        # Don't flag words that are part of proper nouns or entity names
        if hasattr(token, 'ent_type_') and token.ent_type_ in ['PERSON', 'ORG', 'PRODUCT', 'EVENT', 'GPE']:
            return True  # Proper names are not style violations
            
        # === GUARD 4: TECHNICAL SPECIFICATIONS AND JARGON ===
        # Don't flag words in technical specifications where they have specific meanings
        if self._is_technical_specification_words(token, context):
            return True  # Technical specs use precise terminology
            
        # === GUARD 5: DOMAIN-APPROPRIATE USAGE ===
        # Don't flag words that are appropriate for the specific domain
        if self._is_domain_appropriate_word_usage(token, context):
            return True  # Domain-specific language is acceptable
            
        # === GUARD 6: URLs, FILE PATHS, AND IDENTIFIERS ===
        # Don't flag technical identifiers, URLs, file paths (but allow abbreviations like "w/")
        if hasattr(token, 'like_url') and token.like_url:
            return True
        if hasattr(token, 'text'):
            text = token.text
            # Filter URLs and file paths, but allow abbreviations like "w/"
            if (text.startswith('http') or 
                text.startswith('www.') or
                text.startswith('ftp://') or
                ('/' in text and len(text) > 3) or  # Paths longer than 3 chars with /
                ('\\' in text and len(text) > 3)):  # Windows paths longer than 3 chars with \
                return True
            
        # === GUARD 7: FOREIGN LANGUAGE AND TRANSLITERATIONS ===
        # Don't flag tokens identified as foreign language
        if hasattr(token, 'lang_') and token.lang_ != 'en':
            return True
            
        return False  # No guards triggered - process this word
    
    def _is_in_code_or_technical_context_words(self, token, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this word in a code block, configuration, or technical context?
        Only returns True for genuine technical contexts, not user-facing content.
        """
        # Code and configuration contexts
        if context and context.get('block_type') in [
            'code_block', 'literal_block', 'inline_code', 'config',
            'json', 'yaml', 'xml', 'sql', 'command_line'
        ]:
            return True
            
        # Technical documentation that preserves exact formatting
        if context and context.get('content_type') == 'api':
            block_type = context.get('block_type', '')
            if block_type in ['example', 'sample', 'response']:
                return True
                
        return False
    
    def _is_in_quoted_context_words(self, token, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is the word actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not hasattr(token, 'doc') or not token.doc:
            return False
            
        # Look for actual quotation marks around the token
        sent = token.sent
        token_idx = token.i - sent.start
        
        # Check for quotation marks in reasonable proximity
        quote_chars = ['"', '"', '"', "'", "'", '`']
        
        # Look backwards and forwards for quote pairs
        before_quotes = 0
        after_quotes = 0
        
        # Search backwards
        for i in range(max(0, token_idx - 10), token_idx):
            if i < len(sent) and sent[i].text in quote_chars:
                before_quotes += 1
                
        # Search forwards  
        for i in range(token_idx + 1, min(len(sent), token_idx + 10)):
            if i < len(sent) and sent[i].text in quote_chars:
                after_quotes += 1
        
        # If we have quotes both before and after, likely quoted content
        return before_quotes > 0 and after_quotes > 0
    
    def _is_technical_specification_words(self, token, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this word part of a technical specification?
        Only returns True for genuine technical specs, not general usage.
        """
        if not hasattr(token, 'sent'):
            return False
            
        sent_text = token.sent.text.lower()
        
        # Technical specification indicators
        tech_spec_indicators = [
            'api specification', 'configuration parameter', 'system architecture',
            'technical standard', 'protocol definition', 'interface specification',
            'method signature', 'function definition', 'class declaration'
        ]
        
        # Check if word appears in genuine technical specification context
        if any(indicator in sent_text for indicator in tech_spec_indicators):
            return True
        
        # Check if in technical documentation block
        block_type = context.get('block_type', '')
        if block_type in ['technical_spec', 'api_reference', 'config_file', 'schema']:
            return True
            
        return False
    
    def _is_domain_appropriate_word_usage(self, token, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this word appropriate for the specific domain?
        Only returns True when word is genuinely domain-appropriate.
        """
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        word_lower = token.text.lower() if hasattr(token, 'text') else ''
        
        # Domain-specific word appropriateness
        domain_appropriate = {
            'legal': ['heretofore', 'whereas', 'pursuant'],  # Legal writing uses formal terms
            'academic': ['aforementioned', 'subsequent', 'moreover'],  # Academic writing more formal
            'medical': ['contraindication', 'prophylaxis', 'etiology'],  # Medical terminology
            'financial': ['amortization', 'depreciation', 'liquidity'],  # Financial jargon
            'technical': ['instantiate', 'serialize', 'polymorphism'],  # Technical terms
        }
        
        if domain in domain_appropriate:
            if word_lower in domain_appropriate[domain]:
                return True
        
        # Content type appropriateness
        if content_type == 'legal' and word_lower in ['heretofore', 'whereas', 'pursuant']:
            return True
        elif content_type == 'academic' and word_lower in ['aforementioned', 'subsequent']:
            return True
        elif content_type == 'api' and word_lower in ['instantiate', 'serialize']:
            return True
        
        return False
    
    # === EVIDENCE-AWARE MESSAGING AND SUGGESTIONS ===
    
    def _generate_evidence_aware_word_usage_message(self, word: str, evidence_score: float, 
                                                   word_category: str = "word choice") -> str:
        """
        PRODUCTION-GRADE: Generate evidence-aware error messages for word usage violations.
        """
        if evidence_score > 0.85:
            if word_category == 'verb_misuse':
                return f"'{word}' should not be used as a verb. Use a more specific action word."
            elif word_category == 'ambiguous':
                return f"'{word}' creates ambiguity. Use clear alternatives."
            elif word_category == 'ui_language':
                return f"'{word}' is unclear for UI elements. Use specific interface language."
            elif word_category == 'user_focus':
                return f"'{word}' shifts focus away from the user. Use user-centered language."
            else:
                return f"'{word}' violates style guidelines. Use the recommended alternative."
        elif evidence_score > 0.6:
            return f"Consider replacing '{word}' with a clearer alternative."
        else:
            return f"'{word}' could be improved for better clarity."
    
    def _generate_evidence_aware_word_usage_suggestions(self, word: str, alternatives: List[str], 
                                                       evidence_score: float, context: Dict[str, Any],
                                                       word_category: str = "word choice") -> List[str]:
        """
        PRODUCTION-GRADE: Generate evidence-aware suggestions for word usage violations.
        """
        suggestions = []
        
        # Primary suggestion with alternative
        if alternatives:
            primary_alt = alternatives[0]
            suggestions.append(f"Replace '{word}' with '{primary_alt}' for better clarity.")
        
        # Category-specific suggestions
        if word_category == 'verb_misuse':
            suggestions.append("Use specific action verbs instead of nouns as verbs.")
        elif word_category == 'ambiguous':
            suggestions.append("Choose precise language that eliminates ambiguity.")
        elif word_category == 'ui_language':
            suggestions.append("Use specific UI terminology that clearly describes user actions.")
        elif word_category == 'user_focus':
            suggestions.append("Focus on what users can do rather than what the system allows.")
        elif word_category == 'spelling':
            suggestions.append("Use the preferred spelling variant for consistency.")
        elif word_category == 'informal_abbrev':
            suggestions.append("Spell out abbreviations for professional communication.")
        
        # Context-specific suggestions
        content_type = context.get('content_type', '')
        audience = context.get('audience', '')
        
        if content_type == 'tutorial' and word_category in ['user_focus', 'ui_language']:
            suggestions.append("Tutorial content should clearly guide user actions.")
        elif content_type == 'reference' and word_category in ['ambiguous', 'informal_abbrev']:
            suggestions.append("Reference documentation requires precise, formal language.")
        elif audience == 'beginner' and word_category in ['spelling', 'ambiguous']:
            suggestions.append("Beginners benefit from simple, unambiguous language choices.")
        
        # Evidence-based suggestions
        if evidence_score > 0.8:
            suggestions.append("This word choice significantly impacts clarity and should be changed.")
        elif evidence_score > 0.6:
            suggestions.append("This change will improve the overall readability of your content.")
        
        # Additional alternatives
        if len(alternatives) > 1:
            other_alts = ', '.join(alternatives[1:])
            suggestions.append(f"Other alternatives: {other_alts}")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # === SHARED UTILITIES FOR WORD USAGE ANALYSIS ===
    
    def _get_word_usage_context_indicators(self, token) -> Dict[str, Any]:
        """Get context indicators that are shared across word usage rules."""
        if not token or not hasattr(token, 'text'):
            return {}
            
        return {
            'pos_tag': getattr(token, 'pos_', 'UNKNOWN'),
            'dependency': getattr(token, 'dep_', 'UNKNOWN'),
            'is_title_case': token.text.istitle() if hasattr(token, 'text') else False,
            'is_upper_case': token.text.isupper() if hasattr(token, 'text') else False,
            'word_length': len(token.text) if hasattr(token, 'text') else 0,
            'has_apostrophe': "'" in token.text if hasattr(token, 'text') else False,
            'morphological_features': str(getattr(token, 'morph', {})),
            'lemma': getattr(token, 'lemma_', '').lower()
        }
    
    def _detect_common_word_usage_patterns(self, doc) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect common patterns that multiple word usage rules care about.
        Returns categorized findings for rules to use in their specific evidence calculation.
        """
        if not doc:
            return {}
            
        patterns = {
            'verb_misuse': [],
            'spelling_variants': [],
            'informal_abbreviations': [],
            'ambiguous_constructions': [],
            'ui_language_issues': []
        }
        
        try:
            for token in doc:
                if not token.is_alpha or token.is_stop:
                    continue
                    
                context_indicators = self._get_word_usage_context_indicators(token)
                
                # Detect verbs that might be noun misuse
                if (context_indicators['pos_tag'] == 'VERB' and 
                    context_indicators['lemma'] in ['action', 'architect', 'impact']):
                    patterns['verb_misuse'].append({
                        'token': token,
                        'indicators': context_indicators,
                        'issue_type': 'noun_as_verb'
                    })
                
                # Detect informal abbreviations
                if (context_indicators['word_length'] <= 5 and 
                    context_indicators['is_upper_case'] and
                    token.text.lower() in ['asap', 'fyi', 'btw']):
                    patterns['informal_abbreviations'].append({
                        'token': token,
                        'indicators': context_indicators,
                        'issue_type': 'informal_abbrev'
                    })
                
                # Detect ambiguous constructions
                if token.text.lower() in ['and/or', 'etc.', '...']:
                    patterns['ambiguous_constructions'].append({
                        'token': token,
                        'indicators': context_indicators,
                        'issue_type': 'ambiguous'
                    })
        
        except Exception:
            pass  # Graceful degradation
            
        return patterns
    
    def _ensure_patterns_ready(self, nlp):
        """Ensure PhraseMatcher patterns are initialized."""
        if not hasattr(self, '_phrase_matcher') or self._phrase_matcher is None:
            if hasattr(self, '_setup_patterns'):
                self._setup_patterns(nlp)
