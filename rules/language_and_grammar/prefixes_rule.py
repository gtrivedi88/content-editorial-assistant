"""
Prefixes Rule
Based on IBM Style Guide topic: "Prefixes"
Enhanced with spaCy morphological analysis for scalable prefix detection.
"""
import re
from typing import List, Dict, Any, Set
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class PrefixesRule(BaseLanguageRule):
    """
    Detects prefixes that should be closed (without hyphens) using spaCy morphological 
    analysis and linguistic anchors. This approach avoids hardcoding and uses 
    morphological features to identify prefix patterns.
    """
    
    def __init__(self):
        super().__init__()
        self._initialize_prefix_patterns()
    
    def _initialize_prefix_patterns(self):
        """Initialize morphological patterns for prefix detection."""
        
        # LINGUISTIC ANCHORS: Common closed prefixes that should not use hyphens
        self.closed_prefix_patterns = {
            'iterative_prefixes': {
                'prefix_morphemes': ['re'],
                'semantic_indicators': ['again', 'back', 'anew'],
                'morphological_features': {'Prefix': 'True'},
                'description': 'iterative or repetitive action'
            },
            'temporal_prefixes': {
                'prefix_morphemes': ['pre', 'post'],
                'semantic_indicators': ['before', 'after', 'prior'],
                'morphological_features': {'Prefix': 'True'},
                'description': 'temporal relationship'
            },
            'negation_prefixes': {
                'prefix_morphemes': ['non', 'un', 'in', 'dis'],
                'semantic_indicators': ['not', 'without', 'opposite'],
                'morphological_features': {'Prefix': 'True', 'Polarity': 'Neg'},
                'description': 'negation or opposition'
            },
            'quantity_prefixes': {
                'prefix_morphemes': ['multi', 'inter', 'over', 'under', 'sub', 'super'],
                'semantic_indicators': ['many', 'between', 'above', 'below'],
                'morphological_features': {'Prefix': 'True'},
                'description': 'quantity or position'
            },
            'relationship_prefixes': {
                'prefix_morphemes': ['co', 'counter', 'anti', 'pro'],
                'semantic_indicators': ['with', 'against', 'for'],
                'morphological_features': {'Prefix': 'True'},
                'description': 'relationship or stance'
            }
        }
        
        # MORPHOLOGICAL ANCHORS: Patterns for detecting hyphenated prefixes
        self.hyphen_detection_patterns = {
            'explicit_hyphen': r'\b(\w+)-(\w+)\b',
            'prefix_boundary': r'\b(re|pre|non|un|in|dis|multi|inter|over|under|sub|super|co|counter|anti|pro)-\w+\b'
        }
    
    def _get_rule_type(self) -> str:
        return 'prefixes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for hyphenated prefixes using evidence-based scoring.
        Uses sophisticated morphological and contextual analysis to distinguish between
        prefixes that should be closed and those where hyphenation may be appropriate.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        
        # LINGUISTIC ANCHOR 1: Detect hyphenated prefix patterns
        for sent in doc.sents:
            # Use regex to find potential hyphenated prefixes
            hyphen_matches = re.finditer(self.hyphen_detection_patterns['prefix_boundary'], 
                                       sent.text, re.IGNORECASE)
            
            for match in hyphen_matches:
                prefix_part = match.group(1).lower()
                full_match = match.group(0)
                
                # MORPHOLOGICAL ANALYSIS: Check if this could be a closed prefix
                potential_closed_prefix = self._should_be_closed_prefix(prefix_part, full_match, doc, sent)
                
                if potential_closed_prefix:
                    # Get the token span for precise analysis
                    char_start = sent.start_char + match.start()
                    char_end = sent.start_char + match.end()
                    
                    # Find corresponding tokens
                    tokens_in_span = [token for token in sent if 
                                    token.idx >= char_start and token.idx < char_end]
                    
                    if tokens_in_span:
                        # Calculate evidence score for this prefix hyphenation
                        evidence_score = self._calculate_prefix_evidence(
                            prefix_part, full_match, tokens_in_span, sent, text, context
                        )
                        
                        # Only create error if evidence suggests it's worth flagging
                        if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                            # Analyze morphological context for smart suggestions
                            context_analysis = self._analyze_prefix_context(tokens_in_span, doc)
                            
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=list(doc.sents).index(sent),
                                message=self._get_contextual_prefix_message(prefix_part, full_match, evidence_score),
                                suggestions=self._generate_smart_prefix_suggestions(prefix_part, full_match, evidence_score, context_analysis, context),
                                severity='medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,  # Your nuanced assessment
                                span=(char_start, char_end),
                                flagged_text=full_match
                            ))
        
        return errors
    
    def _should_be_closed_prefix(self, prefix: str, full_word: str, doc: 'Doc', sent) -> bool:
        """
        Uses morphological analysis to determine if a prefix should be closed.
        LINGUISTIC ANCHOR: Morphological and semantic analysis.
        """
        # Check against known closed prefix patterns
        for pattern_name, pattern_info in self.closed_prefix_patterns.items():
            if prefix in pattern_info['prefix_morphemes']:
                # MORPHOLOGICAL VALIDATION: Check semantic context
                if self._has_prefix_semantic_context(full_word, pattern_info, doc, sent):
                    return True
        
        # LINGUISTIC ANCHOR: Check morphological features of the word
        # Find tokens that contain this hyphenated word
        for token in sent:
            if full_word.lower() in token.text.lower():
                # Analyze morphological structure
                if self._has_prefix_morphology(token, prefix):
                    return True
        
        return False
    
    def _has_prefix_semantic_context(self, word: str, pattern_info: Dict, doc: 'Doc', sent) -> bool:
        """
        Check if the word appears in semantic context appropriate for the prefix.
        LINGUISTIC ANCHOR: Semantic role analysis using spaCy features.
        """
        semantic_indicators = pattern_info.get('semantic_indicators', [])
        
        # Look for semantic indicators in surrounding context
        word_lower = word.lower()
        sent_text = sent.text.lower()
        
        # Check if any semantic indicators appear near the word
        for indicator in semantic_indicators:
            if indicator in sent_text:
                return True
        
        # MORPHOLOGICAL ANALYSIS: Check if word structure suggests prefix usage
        base_word = word.split('-')[1] if '-' in word else word
        
        # Look for the base word elsewhere in the document to understand usage
        for token in doc:
            if token.lemma_.lower() == base_word.lower():
                # If base word exists independently, prefix is likely modifying it
                return True
        
        return True  # Default to flagging for manual review
    
    def _has_prefix_morphology(self, token: 'Token', prefix: str) -> bool:
        """
        Analyze morphological features to detect prefix usage.
        LINGUISTIC ANCHOR: spaCy morphological feature analysis.
        """
        if not token:
            return False
        
        # Check morphological features
        if hasattr(token, 'morph') and token.morph:
            morph_dict = token.morph.to_dict()
            
            # Look for prefix-related morphological features
            if morph_dict.get('Prefix') == 'True':
                return True
            
            # Check for derivational morphology patterns
            if morph_dict.get('Derivation'):
                return True
        
        # LINGUISTIC PATTERN: Analyze word structure
        if hasattr(token, 'lemma_') and token.lemma_:
            # Check if the lemma suggests a prefixed form
            if prefix in token.lemma_.lower() and len(token.lemma_) > len(prefix) + 2:
                return True
        
        # POS analysis: Common prefixed word patterns
        if hasattr(token, 'pos_'):
            # Prefixed verbs, adjectives, and nouns are often closed
            if token.pos_ in ['VERB', 'ADJ', 'NOUN'] and prefix in token.text.lower():
                return True
        
        return False
    
    def _analyze_prefix_context(self, tokens: List['Token'], doc: 'Doc') -> Dict[str, str]:
        """
        Analyze the morphological and syntactic context of the prefix.
        LINGUISTIC ANCHOR: Dependency and morphological analysis.
        """
        if not tokens:
            return {'explanation': 'This prefix typically forms closed compounds.'}
        
        primary_token = tokens[0]
        
        # Analyze POS and morphological context
        pos = getattr(primary_token, 'pos_', '')
        dep = getattr(primary_token, 'dep_', '')
        
        explanations = {
            'VERB': 'Prefixed verbs are typically written as one word.',
            'NOUN': 'Prefixed nouns are typically written as one word.',
            'ADJ': 'Prefixed adjectives are typically written as one word.',
            'ADV': 'Prefixed adverbs are typically written as one word.'
        }
        
        base_explanation = explanations.get(pos, 'This prefix typically forms closed compounds.')
        
        # Add dependency-based context
        if dep in ['compound', 'amod']:
            base_explanation += ' The syntactic role confirms this should be a single word.'
        
        return {
            'explanation': base_explanation,
            'pos': pos,
            'dependency': dep
        }
    
    def _generate_closed_form(self, hyphenated_word: str) -> str:
        """
        Generate the closed form of a hyphenated prefix word.
        MORPHOLOGICAL PATTERN: Simple hyphen removal with validation.
        """
        return hyphenated_word.replace('-', '')

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _calculate_prefix_evidence(self, prefix: str, full_word: str, tokens: List['Token'], 
                                 sentence, text: str, context: dict) -> float:
        """
        Calculate evidence score (0.0-1.0) for prefix hyphenation concerns.
        
        Higher scores indicate stronger evidence that the hyphen should be removed.
        Lower scores indicate acceptable hyphenation in specific contexts.
        
        Args:
            prefix: The prefix part (e.g., 'co', 'pre', 'multi')
            full_word: The complete hyphenated word (e.g., 'co-location')
            tokens: SpaCy tokens in the word span
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable hyphen) to 1.0 (should close)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_prefix_evidence(prefix, full_word, tokens)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this prefix
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_prefix(evidence_score, prefix, full_word, tokens, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_prefix(evidence_score, prefix, full_word, context or {})
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_prefix(evidence_score, prefix, full_word, text, context or {})
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_prefix(evidence_score, prefix, full_word, context or {})
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    # === PREFIX EVIDENCE METHODS ===

    def _get_base_prefix_evidence(self, prefix: str, full_word: str, tokens: List['Token']) -> float:
        """Get base evidence score for prefix closure."""
        
        # === PREFIX TYPE ANALYSIS ===
        # Different prefixes have different closure tendencies
        
        # Highly established closed prefixes
        highly_closed_prefixes = {
            're': 0.8,    # rearrange, rewrite, reconstruct
            'pre': 0.7,   # preprocess, preload, preconfigure
            'un': 0.9,    # undo, uninstall, unsubscribe
            'non': 0.8,   # nonexistent, nonfunctional, nonstandard
            'over': 0.7,  # override, overflow, overwrite
            'under': 0.7, # underscore, underline, underperform
            'sub': 0.6,   # subdomain, subprocess, subnetwork
            'super': 0.7, # superuser, superclass, supersede
            'inter': 0.6, # interface, interact, interconnect
            'multi': 0.5, # multitenant, multicore, multimedia
            'co': 0.4,    # coexist, cooperate, coauthor (but co-location often hyphenated)
            'counter': 0.6, # counteract, counterpart, counterproductive
            'anti': 0.7,  # antivirus, antipattern, antisocial
            'pro': 0.6,   # proactive, process, professional
            'dis': 0.8,   # disconnect, disable, disintegrate
            'in': 0.7     # inactive, inconsistent, incomplete
        }
        
        base_evidence = highly_closed_prefixes.get(prefix, 0.5)
        
        # === WORD LENGTH ANALYSIS ===
        # Longer compounds may benefit from hyphens for readability
        word_length = len(full_word.replace('-', ''))
        if word_length > 12:
            base_evidence -= 0.2  # Long compounds may need hyphens for clarity
        elif word_length > 15:
            base_evidence -= 0.3  # Very long compounds often benefit from hyphens
        
        # === COMPOUND COMPLEXITY ANALYSIS ===
        # Check if the base word (after prefix) is complex
        base_word = full_word.split('-')[1] if '-' in full_word else full_word[len(prefix):]
        
        # Complex base words may benefit from hyphenation
        if len(base_word) > 8:
            base_evidence -= 0.1  # Complex base words may need visual separation
        
        # Technical terms with multiple syllables
        if self._has_multiple_syllables(base_word):
            base_evidence -= 0.1  # Multi-syllabic base words may benefit from hyphens
        
        return base_evidence

    def _apply_linguistic_clues_prefix(self, evidence_score: float, prefix: str, full_word: str, 
                                     tokens: List['Token'], sentence) -> float:
        """Apply linguistic analysis clues for prefix detection."""
        
        if not tokens:
            return evidence_score
        
        primary_token = tokens[0]
        
        # === MORPHOLOGICAL ANALYSIS ===
        # Use existing morphological analysis from the current implementation
        if hasattr(primary_token, 'morph') and primary_token.morph:
            morph_dict = primary_token.morph.to_dict()
            
            # Strong morphological evidence for closure
            if morph_dict.get('Prefix') == 'True':
                evidence_score += 0.2  # Morphological evidence supports closure
            
            # Derivational morphology suggests established word formation
            if morph_dict.get('Derivation'):
                evidence_score += 0.1  # Derivational patterns often close
        
        # === POS ANALYSIS ===
        # Different parts of speech have different hyphenation tendencies
        if hasattr(primary_token, 'pos_'):
            pos = primary_token.pos_
            
            if pos == 'VERB':
                evidence_score += 0.2  # Prefixed verbs typically close (redo, preload)
            elif pos == 'NOUN':
                evidence_score += 0.1  # Prefixed nouns often close (subset, preview)
            elif pos == 'ADJ':
                evidence_score += 0.15  # Prefixed adjectives typically close (inactive, multilingual)
            elif pos == 'ADV':
                evidence_score += 0.1  # Prefixed adverbs often close (prematurely, simultaneously)
        
        # === DEPENDENCY ANALYSIS ===
        # Syntactic role affects hyphenation likelihood
        if hasattr(primary_token, 'dep_'):
            dep = primary_token.dep_
            
            if dep in ['compound', 'amod']:
                evidence_score += 0.1  # Compound/modifier roles often close
            elif dep == 'ROOT':
                evidence_score += 0.1  # Root words tend to be established forms
        
        # === FREQUENCY AND FAMILIARITY ===
        # Check if this appears to be an established compound
        if self._is_established_compound(full_word.replace('-', '')):
            evidence_score += 0.3  # Established compounds strongly favor closure
        
        # === PHONOLOGICAL CONSIDERATIONS ===
        # Some prefix-base combinations are harder to read without hyphens
        base_word = full_word.split('-')[1] if '-' in full_word else full_word[len(prefix):]
        
        # Check for difficult letter combinations
        if self._has_difficult_letter_combination(prefix, base_word):
            evidence_score -= 0.2  # Difficult combinations may need hyphens
        
        return evidence_score

    def _apply_structural_clues_prefix(self, evidence_score: float, prefix: str, full_word: str, context: dict) -> float:
        """Apply document structure clues for prefix detection."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL DOCUMENTATION CONTEXTS ===
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.2  # Code contexts may use established hyphenated forms
        elif block_type == 'inline_code':
            evidence_score -= 0.1  # Inline code may reference hyphenated technical terms
        
        # === FORMAL DOCUMENTATION CONTEXTS ===
        if block_type in ['table_cell', 'table_header']:
            evidence_score += 0.1  # Tables often prefer compact, closed forms
        elif block_type in ['heading', 'title']:
            evidence_score += 0.1  # Headings often use established, closed forms
        
        # === SPECIFICATION CONTEXTS ===
        if block_type in ['admonition']:
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP']:
                evidence_score -= 0.1  # Notes may use explanatory hyphenated forms
            elif admonition_type in ['WARNING', 'IMPORTANT']:
                evidence_score += 0.1  # Warnings prefer established terminology
        
        # === LIST CONTEXTS ===
        if block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.05  # Lists may prefer compact forms
        
        return evidence_score

    def _apply_semantic_clues_prefix(self, evidence_score: float, prefix: str, full_word: str, 
                                   text: str, context: dict) -> float:
        """Apply semantic and content-type clues for prefix detection."""
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        if content_type == 'technical':
            # Technical content may have established hyphenated terms
            if self._is_technical_compound(full_word):
                evidence_score -= 0.2  # Technical compounds may prefer hyphens
            else:
                evidence_score += 0.1  # General technical writing prefers standard forms
        elif content_type == 'api':
            evidence_score += 0.2  # API docs prefer precise, standard terminology
        elif content_type == 'academic':
            evidence_score += 0.1  # Academic writing prefers established forms
        elif content_type == 'legal':
            evidence_score += 0.2  # Legal writing requires precise terminology
        elif content_type == 'marketing':
            evidence_score += 0.1  # Marketing prefers readable, established forms
        elif content_type == 'procedural':
            evidence_score += 0.1  # Procedures prefer clear, standard terminology
        elif content_type == 'narrative':
            evidence_score += 0.05  # Narrative writing favors standard forms
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            # Check for domain-specific established hyphenated terms
            if self._is_established_technical_hyphenation(full_word):
                evidence_score -= 0.3  # Established technical hyphenations
            else:
                evidence_score += 0.1  # General software terms prefer closure
        elif domain in ['specification', 'documentation']:
            evidence_score += 0.1  # Specification writing prefers standard forms
        elif domain in ['networking', 'infrastructure']:
            # Network terms often have established hyphenated forms
            if prefix in ['co', 'inter', 'multi', 'sub']:
                evidence_score -= 0.1  # Network terms may prefer hyphens
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score += 0.05  # Technical audiences prefer precise terminology
        elif audience in ['beginner', 'general', 'user']:
            evidence_score -= 0.05  # General audiences may benefit from hyphen clarity
        
        # === DOCUMENT PURPOSE ANALYSIS ===
        if self._is_specification_documentation(text):
            evidence_score += 0.1  # Specifications prefer standard terminology
        
        if self._is_tutorial_content(text):
            evidence_score -= 0.05  # Tutorials may use clearer hyphenated forms
        
        return evidence_score

    def _apply_feedback_clues_prefix(self, evidence_score: float, prefix: str, full_word: str, context: dict) -> float:
        """Apply feedback patterns for prefix detection."""
        
        feedback_patterns = self._get_cached_feedback_patterns_prefix()
        
        # === PREFIX-SPECIFIC FEEDBACK ===
        # Check if this prefix commonly has accepted closed usage
        accepted_closed_prefixes = feedback_patterns.get('accepted_closed_prefixes', set())
        if prefix in accepted_closed_prefixes:
            evidence_score += 0.2  # Users consistently accept closed form for this prefix
        
        accepted_hyphenated_prefixes = feedback_patterns.get('accepted_hyphenated_prefixes', set())
        if prefix in accepted_hyphenated_prefixes:
            evidence_score -= 0.2  # Users consistently accept hyphenated form for this prefix
        
        # === WORD-SPECIFIC FEEDBACK ===
        closed_form = full_word.replace('-', '')
        
        # Check if this specific word has feedback patterns
        accepted_closed_words = feedback_patterns.get('accepted_closed_words', set())
        if closed_form.lower() in accepted_closed_words:
            evidence_score += 0.3  # Users consistently accept closed form for this word
        
        accepted_hyphenated_words = feedback_patterns.get('accepted_hyphenated_words', set())
        if full_word.lower() in accepted_hyphenated_words:
            evidence_score -= 0.3  # Users consistently accept hyphenated form for this word
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get(f'{content_type}_prefix_patterns', {})
        
        if full_word.lower() in context_patterns.get('closed_acceptable', set()):
            evidence_score += 0.2
        elif full_word.lower() in context_patterns.get('hyphenated_acceptable', set()):
            evidence_score -= 0.2
        
        return evidence_score

    # === HELPER METHODS FOR LINGUISTIC ANALYSIS ===

    def _has_multiple_syllables(self, word: str) -> bool:
        """Estimate if a word has multiple syllables (simplified heuristic)."""
        # Simple vowel-based syllable estimation
        vowels = 'aeiouAEIOU'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Adjust for silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return syllable_count > 1

    def _is_established_compound(self, word: str) -> bool:
        """Check if this appears to be an established compound word."""
        # Common established compounds (this would be expanded in practice)
        established_compounds = {
            'rearrange', 'preprocess', 'undo', 'nonexistent', 'override',
            'subdomain', 'superuser', 'interface', 'multicore', 'coexist',
            'counteract', 'antivirus', 'proactive', 'disconnect', 'inactive',
            'preload', 'uninstall', 'overflow', 'subprocess', 'multimedia',
            'cooperate', 'antipattern', 'disable', 'inconsistent', 'reconstruct'
        }
        
        return word.lower() in established_compounds

    def _has_difficult_letter_combination(self, prefix: str, base_word: str) -> bool:
        """Check if prefix + base creates difficult letter combinations."""
        # Check for doubled consonants or difficult combinations
        combined = prefix + base_word
        
        # Difficult combinations that might benefit from hyphens
        difficult_patterns = [
            'oo', 'ee', 'aa', 'ii', 'uu',  # Doubled vowels
            'll', 'mm', 'nn', 'pp', 'ss', 'tt',  # Doubled consonants
        ]
        
        junction = prefix[-1:] + base_word[:1] if base_word else ''
        
        return any(pattern in junction for pattern in difficult_patterns)

    def _is_technical_compound(self, word: str) -> bool:
        """Check if this is a technical compound that may prefer hyphenation."""
        technical_patterns = [
            'co-location', 'co-tenant', 'co-processor',
            'multi-tenant', 'multi-cloud', 'multi-region',
            'sub-domain', 'sub-network', 'sub-process',
            'inter-service', 'inter-process', 'inter-node'
        ]
        
        return word.lower() in technical_patterns

    def _is_established_technical_hyphenation(self, word: str) -> bool:
        """Check if this word has established hyphenated form in technical contexts."""
        established_hyphenated = {
            'co-location', 'co-tenant', 'co-processor', 'co-design',
            'multi-tenant', 'multi-cloud', 'multi-region', 'multi-tier',
            'sub-domain', 'sub-network', 'sub-module', 'sub-component',
            'inter-service', 'inter-process', 'inter-node', 'inter-cluster',
            'pre-processing', 'post-processing', 'non-blocking', 'anti-pattern'
        }
        
        return word.lower() in established_hyphenated

    def _is_specification_documentation(self, text: str) -> bool:
        """Check if text appears to be specification documentation."""
        spec_indicators = [
            'specification', 'spec', 'standard', 'protocol', 'definition',
            'schema', 'format', 'syntax', 'implementation', 'reference'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in spec_indicators if indicator in text_lower) >= 2

    def _is_tutorial_content(self, text: str) -> bool:
        """Check if text appears to be tutorial content."""
        tutorial_indicators = [
            'tutorial', 'how to', 'guide', 'step', 'procedure', 'walkthrough',
            'getting started', 'introduction', 'learn', 'example'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in tutorial_indicators if indicator in text_lower) >= 2

    def _get_cached_feedback_patterns_prefix(self):
        """Load feedback patterns from cache or feedback analysis for prefixes."""
        # This would load from feedback analysis system
        # For now, return patterns based on common prefix usage
        return {
            'accepted_closed_prefixes': {
                # Prefixes commonly accepted in closed form
                're', 'un', 'non', 'pre', 'over', 'under', 'super', 'anti', 'dis', 'in'
            },
            'accepted_hyphenated_prefixes': {
                # Prefixes commonly accepted in hyphenated form
                'co', 'multi', 'inter', 'sub'
            },
            'accepted_closed_words': {
                # Specific words commonly accepted in closed form
                'rearrange', 'preprocess', 'undo', 'nonexistent', 'override',
                'subdomain', 'superuser', 'interface', 'multicore', 'antivirus'
            },
            'accepted_hyphenated_words': {
                # Specific words commonly accepted in hyphenated form
                'co-location', 'multi-tenant', 'sub-domain', 'inter-service',
                'co-processor', 'multi-cloud', 'sub-network', 'inter-process'
            },
            'technical_prefix_patterns': {
                'closed_acceptable': {
                    # Closed forms acceptable in technical contexts
                    'preprocess', 'subprocess', 'multicore', 'interface',
                    'override', 'superuser', 'antivirus', 'nonblocking'
                },
                'hyphenated_acceptable': {
                    # Hyphenated forms acceptable in technical contexts
                    'co-location', 'multi-tenant', 'sub-domain', 'inter-service',
                    'co-processor', 'multi-cloud', 'non-blocking', 'anti-pattern'
                }
            },
            'academic_prefix_patterns': {
                'closed_acceptable': {
                    # Closed forms preferred in academic contexts
                    'rearrange', 'preprocess', 'nonexistent', 'inconsistent',
                    'counteract', 'proactive', 'disconnect', 'inactive'
                },
                'hyphenated_acceptable': {
                    # Hyphenated forms acceptable in academic contexts
                    'co-author', 'multi-modal', 'inter-disciplinary'
                }
            }
        }

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_prefix_message(self, prefix: str, full_word: str, evidence_score: float) -> str:
        """Generate context-aware error messages for prefix patterns."""
        
        closed_form = self._generate_closed_form(full_word)
        
        if evidence_score > 0.8:
            return f"Prefix '{prefix}' should be closed: '{full_word}' should be written as '{closed_form}'."
        elif evidence_score > 0.5:
            return f"Consider closing the prefix: '{full_word}' typically written as '{closed_form}'."
        else:
            return f"The prefix '{prefix}' in '{full_word}' may benefit from closure as '{closed_form}'."

    def _generate_smart_prefix_suggestions(self, prefix: str, full_word: str, evidence_score: float, 
                                         context_analysis: dict, context: dict) -> List[str]:
        """Generate context-aware suggestions for prefix patterns."""
        
        suggestions = []
        closed_form = self._generate_closed_form(full_word)
        
        # Base suggestions based on evidence strength
        if evidence_score > 0.7:
            suggestions.append(f"Write as '{closed_form}' without the hyphen.")
            suggestions.append(f"{context_analysis.get('explanation', 'This prefix typically forms closed compounds.')}")
        else:
            suggestions.append(f"Consider writing as '{closed_form}' for standard usage.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type in ['technical', 'api']:
                if self._is_established_technical_hyphenation(full_word):
                    suggestions.append("This hyphenated form may be standard in technical contexts.")
                else:
                    suggestions.append("Technical writing typically uses closed prefix forms.")
            elif content_type in ['academic', 'formal']:
                suggestions.append("Academic writing prefers established closed forms.")
            elif content_type == 'specification':
                suggestions.append("Specifications should use standard terminology forms.")
        
        # Prefix-specific advice
        if prefix in ['co', 'multi', 'inter', 'sub']:
            suggestions.append("This prefix sometimes remains hyphenated in technical compounds.")
        elif prefix in ['re', 'un', 'pre', 'non']:
            suggestions.append("This prefix almost always forms closed compounds.")
        
        return suggestions[:3] 