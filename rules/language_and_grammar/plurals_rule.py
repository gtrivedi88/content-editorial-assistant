"""
Plurals Rule (YAML-based)
Based on IBM Style Guide topic: "Plurals"
Uses YAML-based corrections vocabulary for maintainable pluralization rules.
"""
import re
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule
from .services.language_vocabulary_service import get_plurals_vocabulary

try:
    from spacy.tokens import Doc
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    Doc = Matcher = None
    SPACY_AVAILABLE = False

class PluralsRule(BaseLanguageRule):
    """
    Checks for several common pluralization errors, including the use of "(s)",
    and using plural nouns as adjectives.
    OPTIMIZED: (s) pattern detection now uses spaCy Matcher for better performance
    """
    
    def __init__(self):
        super().__init__()
        self.matcher = None
        self._patterns_initialized = False
        self.vocabulary_service = get_plurals_vocabulary()
    
    def _get_rule_type(self) -> str:
        return 'plurals'
    
    def _initialize_matcher(self, nlp) -> None:
        """Initialize Matcher with (s) patterns."""
        if not SPACY_AVAILABLE or self._patterns_initialized:
            return
        
        self.matcher = Matcher(nlp.vocab)
        
        # Pattern to match word(s) - more accurate than regex
        parenthetical_s_pattern = [
            {"IS_ALPHA": True},
            {"ORTH": "("},
            {"LOWER": "s"},
            {"ORTH": ")"}
        ]
        self.matcher.add("PARENTHETICAL_S", [parenthetical_s_pattern])
        self._patterns_initialized = True
    
    def _get_sentence_index(self, doc: Doc, span_start: int) -> int:
        """Get sentence index for a character position."""
        for i, sent in enumerate(doc.sents):
            if span_start >= sent.start_char and span_start < sent.end_char:
                return i
        return 0

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for pluralization errors.
        Calculates nuanced evidence scores for each detected issue using
        linguistic, structural, semantic, and feedback clues.
        """
        errors = []
        if not nlp:
            return errors
        
        # Initialize Matcher for (s) patterns if available
        if SPACY_AVAILABLE:
            self._initialize_matcher(nlp)
        
        doc = nlp(text)

        # Find all potential issues first
        potential_issues = self._find_potential_issues(doc, text)
        
        for potential_issue in potential_issues:
            # Calculate nuanced evidence score
            evidence_score = self._calculate_plurals_evidence(
                potential_issue, doc, text, context or {}
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                errors.append(self._create_error(
                    sentence=potential_issue['sentence'].text,
                    sentence_index=potential_issue['sentence_index'],
                    message=self._get_contextual_plurals_message(potential_issue, evidence_score),
                    suggestions=self._generate_smart_plurals_suggestions(potential_issue, evidence_score, context or {}),
                    severity=potential_issue.get('severity', 'medium'),
                    text=text,
                    context=context,
                    evidence_score=evidence_score,  # Your nuanced assessment
                    span=potential_issue['span'],
                    flagged_text=potential_issue['flagged_text']
                ))
        
        return errors

    def _find_potential_issues(self, doc, text: str) -> List[Dict[str, Any]]:
        """Find all potential pluralization issues in the document."""
        potential_issues = []
        
        if not SPACY_AVAILABLE:
            return potential_issues
        
        # === RULE 1: "(s)" PATTERN DETECTION ===
        # Use regex approach as SpaCy tokenization can split (s) patterns
        s_pattern_regex = re.compile(r'\b(\w+)\(s\)', re.IGNORECASE)
        
        for match in s_pattern_regex.finditer(text):
            full_match = match.group(0)  # e.g., "user(s)"
            base_word = match.group(1)   # e.g., "user"
            
            # Skip if this pattern is in exceptions
            if self._is_excepted(full_match):
                continue
            
            # Find which sentence this belongs to
            sentence_index = 0
            match_sentence = None
            for i, sent in enumerate(doc.sents):
                if sent.start_char <= match.start() < sent.end_char:
                    sentence_index = i
                    match_sentence = sent
                    break
            
            if match_sentence:
                potential_issues.append({
                    'type': 'parenthetical_s',
                    'span_obj': None,  # We don't have a spaCy span for regex matches
                    'sentence': match_sentence,
                    'sentence_index': sentence_index,
                    'span': (match.start(), match.end()),
                    'flagged_text': full_match,
                    'base_word': base_word,
                    'severity': 'medium'
                })
        
        # === RULE 2: PLURAL ADJECTIVES DETECTION ===
        for i, sent in enumerate(doc.sents):
            for token in sent:
                # Find potential plural noun modifiers
                if self._detect_potential_plural_modifier(token):
                    potential_issues.append({
                        'type': 'plural_adjective',
                        'token': token,
                        'sentence': sent,
                        'sentence_index': i,
                        'span': (token.idx, token.idx + len(token.text)),
                        'flagged_text': token.text,
                        'lemma': token.lemma_,
                        'severity': 'low'
                    })
        
        # === RULE 3: INCORRECT PLURAL FORMS DETECTION ===
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if self._is_incorrect_plural_form(token):
                    potential_issues.append({
                        'type': 'incorrect_plural',
                        'token': token,
                        'sentence': sent,
                        'sentence_index': i,
                        'span': (token.idx, token.idx + len(token.text)),
                        'flagged_text': token.text,
                        'lemma': token.lemma_,
                        'severity': 'high'
                    })
        
        return potential_issues

    def _is_excepted(self, text: str) -> bool:
        """
        Check if the parenthetical (s) pattern is in exceptions using YAML configuration.
        
        This prevents hardcoding and makes the rule production-ready by using 
        the configurable exceptions from plurals_corrections.yaml.
        """
        corrections = self.vocabulary_service.get_plurals_corrections()
        exceptions_config = corrections.get('exceptions', {})
        
        # Get patterns that are allowed in technical documentation contexts
        technical_patterns = exceptions_config.get('technical_documentation', [])
        
        # Check if the text matches any of the allowed patterns  
        text_lower = text.lower()
        for pattern in technical_patterns:
            # Convert pattern to lowercase for comparison
            if text_lower in pattern.lower():
                return True
        
        # TODO: Could extend this to check other exception contexts
        # like space_constrained_ui, established_terminology etc.
        
        return False

    def _is_incorrect_plural_form(self, token) -> bool:
        """Check if token is an incorrect plural form using YAML vocabulary."""
        if token.pos_ != 'NOUN':
            return False
        
        # Load corrections from YAML vocabulary
        corrections = self.vocabulary_service.get_plurals_corrections()
        
        token_lower = token.text.lower()
        
        # PRIORITY 1: Check uncountable technical nouns (special handling)
        uncountable_technical = corrections.get('uncountable_technical_nouns', {})
        for technical_noun, config in uncountable_technical.items():
            incorrect_forms = config.get('incorrect_forms', [])
            if token_lower in [form.lower() for form in incorrect_forms]:
                return True
        
        # PRIORITY 2: Check traditional incorrect plurals
        incorrect_plurals = corrections.get('incorrect_plurals', {})
        all_incorrect = set()
        for category in incorrect_plurals.values():
            if isinstance(category, dict):
                all_incorrect.update(category.keys())
        
        return token_lower in all_incorrect

    def _is_functioning_as_verb(self, token, doc) -> bool:
        """
        LINGUISTIC ANCHOR: Detect when a token tagged as plural noun is actually functioning as a verb.
        This handles SpaCy parsing errors where verbs are incorrectly tagged as plural nouns.
        Enhanced to catch cases like "{product} releases on a different cadence"
        """
        # PATTERN 1: Check if it's the main predicate of the sentence
        if token.dep_ == 'ROOT':
            return True
        
        # PATTERN 2: Check if it has typical verb children (objects, adverbials, etc.)
        verb_children_deps = {'dobj', 'iobj', 'nsubjpass', 'advmod', 'aux', 'auxpass', 'prep'}
        has_verb_children = any(child.dep_ in verb_children_deps for child in token.children)
        
        if has_verb_children:
            return True
        
        # PATTERN 3: Check if it's preceded by a subject and appears to be the main verb
        # Look for pattern: [subject] [this_token] [object/prep]
        if (token.i > 0 and token.i < len(doc) - 1):
            prev_token = doc[token.i - 1]
            next_token = doc[token.i + 1]
            
            # Subject + verb + object/prepositional pattern
            if (prev_token.dep_ in ('nsubj', 'compound') and 
                next_token.dep_ in ('dobj', 'attr', 'prep')):
                return True
        
        # PATTERN 4: Enhanced subject-verb-prepositional phrase detection
        # Pattern: [subject] [verb] [preposition] (e.g., "logging releases on")
        if (token.i > 0 and token.i < len(doc) - 1):
            prev_token = doc[token.i - 1]
            next_token = doc[token.i + 1]
            
            # Look for: noun/product + verb + preposition
            if (prev_token.pos_ in ('NOUN', 'PROPN') and 
                next_token.pos_ == 'ADP'):  # ADP = preposition
                return True
        
        # PATTERN 5: Check actual POS tag - if spaCy tagged it as VERB, trust that
        if token.pos_ == 'VERB':
            return True
        
        # PATTERN 6: Common verb forms that might be mis-tagged (expanded list)
        common_verbs_as_nouns = {
            'stores', 'processes', 'handles', 'manages', 'creates', 'generates',
            'provides', 'requires', 'ensures', 'validates', 'monitors',
            'executes', 'performs', 'delivers', 'supports', 'contains',
            'releases', 'updates', 'publishes', 'deploys', 'builds',
            'configures', 'installs', 'maintains', 'operates', 'runs'
        }
        
        if token.lower_ in common_verbs_as_nouns:
            # Enhanced context check: subject-verb positioning
            if token.i > 0:
                prev_tokens = doc[max(0, token.i-3):token.i]  # Look at previous 3 tokens
                has_subject_context = any(t.pos_ in ('NOUN', 'PROPN', 'PRON') for t in prev_tokens)
                
                if has_subject_context:
                    return True
        
        # PATTERN 7: Dependency-based detection for mis-parsed verbs
        # If tagged as dobj but has verb-like children, likely a parsing error
        if token.dep_ == 'dobj' and any(child.dep_ in ('prep', 'advmod') for child in token.children):
            return True
        
        return False

    def _is_compound_head_noun(self, token, doc) -> bool:
        """
        LINGUISTIC ANCHOR: Detect when a plural noun is actually the head noun
        of a compound phrase, not a modifier.
        
        Examples:
        - "BYO Knowledge images" - "images" is the head noun
        - "container registry images" - "images" is the head noun
        - "systems administrator" - "systems" is the modifier (should be flagged)
        """
        # Check if this token is the rightmost noun in a compound noun phrase
        # and has other nouns/adjectives depending on it as compounds
        has_compound_children = any(
            child.dep_ == 'compound' and child.i < token.i 
            for child in token.children
        )
        
        # Check if this token is the head (not dependent on another noun to its right)
        head_token = token.head
        is_sentence_head = (
            head_token.pos_ != 'NOUN' or  # Head is not a noun
            head_token.i < token.i or     # Head comes before this token
            head_token.dep_ == 'ROOT'     # This token's head is the root
        )
        
        # If it has compound modifiers and is the rightmost noun, it's likely the head
        if has_compound_children and is_sentence_head:
            return True
        
        # Additional check: Look for patterns like "adjective + adjective + plural_noun"
        # where the plural noun is clearly the head
        preceding_modifiers = []
        for i in range(max(0, token.i - 3), token.i):
            prev_token = doc[i]
            if (prev_token.pos_ in ('ADJ', 'NOUN', 'PROPN') and 
                (prev_token.dep_ == 'compound' or prev_token.head == token)):
                preceding_modifiers.append(prev_token)
        
        # If we have 2+ preceding modifiers, this is likely the head noun
        if len(preceding_modifiers) >= 2:
            return True
        
        # Check for specific patterns with brand names or acronyms
        # (e.g., "BYO Knowledge images", "AWS S3 buckets")
        if preceding_modifiers:
            first_modifier = preceding_modifiers[0]
            # Look for patterns with uppercase acronyms or brand names
            if (first_modifier.text.isupper() or 
                any(char.isupper() for char in first_modifier.text)):
                return True
        
        return False

    def _is_legitimate_technical_compound(self, token, doc) -> bool:
        """
        LINGUISTIC ANCHOR: Identifies legitimate technical compound plurals.
        These are plural nouns that are correctly used as modifiers in technical contexts.
        """
        lemma_lower = token.lemma_.lower()
        token_lower = token.lower_
        
        # LINGUISTIC ANCHOR 1: Technical mass nouns that are inherently plural
        # These are commonly used in their plural form as modifiers
        technical_mass_plurals = {
            'data',      # "data consistency", "data processing"
            'media',     # "media storage", "media streaming"  
            'criteria',  # "criteria validation", "criteria checking"
            'metadata',  # "metadata analysis", "metadata storage"
            'analytics', # "analytics dashboard", "analytics processing"
            'metrics',   # "metrics collection", "metrics analysis"
            'statistics', # "statistics gathering", "statistics reporting"
            'graphics',  # "graphics processing", "graphics rendering"
            'diagnostics', # "diagnostics tools", "diagnostics reporting"
            'logistics', # "logistics management", "logistics coordination"
        }
        
        if token_lower in technical_mass_plurals:
            return True
        
        # LINGUISTIC ANCHOR 2: Domain-specific technical plurals commonly used as modifiers
        technical_domain_plurals = {
            'systems',      # "systems architecture", "systems integration"
            'operations',   # "operations team", "operations management"
            'services',     # "services layer", "services architecture"
            'applications', # "applications layer", "applications server"
            'users',        # "users guide", "users manual" (debatable, but common)
            'communications', # "communications protocol", "communications layer"
            'networks',     # "networks administrator", "networks topology"
            'credentials',  # "credentials management", "credentials validation"
            'permissions',  # "permissions model", "permissions management"
            'requirements', # "requirements analysis", "requirements gathering"
            'specifications', # "specifications document", "specifications review"
            'procedures',   # "procedures manual", "procedures guide"
            'resources',    # "resources allocation", "resources management"
            'utilities',    # "utilities management", "utilities monitoring"
            'components',   # "components architecture", "components design"
            'tools',        # "diagnostics tools", "monitoring tools"
            'servers',      # "servers monitoring", "servers management"
        }
        
        if token_lower in technical_domain_plurals:
            return True
        
        # LINGUISTIC ANCHOR 3: Context-aware detection for technical compound phrases
        # Check if the compound is modifying a technical noun
        head_noun = token.head
        if head_noun.pos_ == 'NOUN':
            technical_head_nouns = {
                'architecture', 'design', 'framework', 'infrastructure', 'platform',
                'management', 'administration', 'coordination', 'integration',
                'analysis', 'processing', 'monitoring', 'validation', 'verification',
                'consistency', 'integrity', 'reliability', 'availability', 'security',
                'performance', 'optimization', 'configuration', 'deployment',
                'documentation', 'specification', 'requirement', 'procedure',
                'protocol', 'interface', 'layer', 'tier', 'model', 'pattern',
                'solution', 'approach', 'strategy', 'methodology', 'implementation'
            }
            
            if head_noun.lemma_.lower() in technical_head_nouns:
                return True
        
        # LINGUISTIC ANCHOR 4: Special case for "users" in documentation contexts
        # "users manual", "users guide" are widely accepted in technical writing
        if (token_lower == 'users' and head_noun.pos_ == 'NOUN' and
            head_noun.lemma_.lower() in {'manual', 'guide', 'documentation', 'handbook', 'reference'}):
            return True
        
        return False

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _calculate_plurals_evidence(self, potential_issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for pluralization concerns.
        
        Higher scores indicate stronger evidence that the issue should be flagged.
        Lower scores indicate acceptable usage in specific contexts.
        
        Args:
            potential_issue: Dictionary containing issue details
            doc: SpaCy document
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be flagged)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_plurals_evidence(potential_issue)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this issue
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_plurals(evidence_score, potential_issue, doc)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_plurals(evidence_score, potential_issue, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_plurals(evidence_score, potential_issue, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_plurals(evidence_score, potential_issue, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _get_base_plurals_evidence(self, potential_issue: Dict[str, Any]) -> float:
        """Get base evidence score based on issue type."""
        issue_type = potential_issue['type']
        
        if issue_type == 'parenthetical_s':
            # All (s) patterns start with moderate evidence
            return 0.7  # Default moderate evidence for (s) patterns
        elif issue_type == 'plural_adjective':
            # Use existing sophisticated analysis to determine base evidence
            token = potential_issue['token']
            doc = potential_issue['sentence'].doc
            
            # If it's functioning as a verb, no evidence for plural adjective error
            if self._is_functioning_as_verb(token, doc):
                return 0.0
            
            # If it's a compound head noun, no evidence for plural adjective error
            if self._is_compound_head_noun(token, doc):
                return 0.0
            
            # If it's a legitimate technical compound, low evidence
            if self._is_legitimate_technical_compound(token, doc):
                return 0.3  # Low evidence - technical context may justify it
            
            # Otherwise, moderate evidence that it's a plural adjective problem
            return 0.7  # Moderate evidence for potential plural adjective issue
        elif issue_type == 'incorrect_plural':
            # Incorrect plural forms are always high evidence
            return 0.9  # High evidence - these are clear grammar errors
        
        return 0.5  # Default evidence for unknown issue types

    def _detect_potential_plural_modifier(self, token) -> bool:
        """Detect tokens that could potentially be plural noun modifiers."""
        
        # Early exit if basic conditions aren't met
        if not (token.tag_ == 'NNS' and 
                token.dep_ in ('compound', 'nsubj', 'amod') and
                token.lemma_ != token.lower_):
            return False
        
        # ZERO FALSE POSITIVE GUARD: Check exemption lists before flagging plural adjectives
        
        # GUARD 1: Legitimate plural subjects
        # Don't flag plural nouns that are subjects of verbs
        if self._is_legitimate_plural_subject(token):
            return False  # Don't flag legitimate plural subjects
        
        # GUARD 2: Check uncountable technical nouns exemption list
        if self._is_uncountable_technical_noun(token.text.lower()):
            return False  # Don't flag uncountable technical nouns like 'data'
        
        # GUARD 3: Check proper nouns ending in 's' exemption list
        if self._is_proper_noun_ending_in_s(token.text.lower()):
            return False  # Don't flag proper nouns like 'kubernetes'
        
        # GUARD 4: Check acceptable plural compounds list
        if self._is_acceptable_plural_compound(token):
            return False  # Don't flag legitimate technical compounds like 'settings panel'
        
        return True
    
    def _is_uncountable_technical_noun(self, word: str) -> bool:
        """Check if word is in the uncountable technical nouns exemption list."""
        corrections = self.vocabulary_service.get_plurals_corrections()
        uncountable_technical = corrections.get('uncountable_technical_nouns', {})
        
        # Check both exact word match and lemmatized forms
        return word in uncountable_technical

    def _is_proper_noun_ending_in_s(self, word: str) -> bool:
        """
        Check if word is a proper noun ending in 's' that should not be flagged as plural.
        
        This prevents false positives for legitimate proper nouns like:
        - Technology platforms: kubernetes, jenkins, prometheus
        - Company names: ibm 
        - Geographic names: wales
        - Frameworks: express
        """
        corrections = self.vocabulary_service.get_plurals_corrections()
        proper_nouns = corrections.get('proper_nouns_ending_in_s', {})
        
        # Check both exact word match and case-insensitive match
        return word in proper_nouns or word.capitalize() in proper_nouns

    def _is_acceptable_plural_compound(self, token) -> bool:
        """
        Check if token is part of an acceptable plural compound from YAML configuration.
        
        This handles cases like "settings panel" where "settings" is a legitimate 
        plural modifier in technical writing.
        """
        corrections = self.vocabulary_service.get_plurals_corrections()
        plural_adjectives = corrections.get('plural_adjectives', {})
        acceptable_compounds = plural_adjectives.get('acceptable_compounds', [])
        
        if not acceptable_compounds:
            return False
        
        # Get the possible compound phrases this token is part of
        compound_phrases = self._extract_compound_phrase(token)
        
        if not compound_phrases:
            return False
        
        # Split multiple phrases (separated by " | ") and check each
        phrases_to_check = compound_phrases.split(" | ")
        
        for phrase in phrases_to_check:
            phrase_lower = phrase.strip().lower()
            for acceptable in acceptable_compounds:
                if acceptable.lower() == phrase_lower:
                    return True
        
        return False

    def _extract_compound_phrase(self, token) -> str:
        """
        Extract the compound phrase that this token is part of.
        
        For "settings" in "settings panel", returns "settings panel".
        For "systems" in "systems administrator", returns "systems administrator".
        For "tools" in "tools development team", returns both "tools development" and "tools team".
        """
        if not token.doc:
            return ""
        
        # Collect all possible compound phrases this token could be part of
        possible_phrases = []
        
        # Method 1: Direct compound relationship (token -> head)
        if token.dep_ == 'compound' and token.head:
            phrase = f"{token.text} {token.head.text}"
            possible_phrases.append(phrase)
        
        # Method 2: Look for compound chains in the sentence
        # Find all compound tokens that could form a phrase with this token
        sentence = list(token.sent)
        
        for other_token in sentence:
            if other_token != token and other_token.pos_ == 'NOUN':
                # Check if they form a compound phrase
                distance = abs(other_token.i - token.i)
                if distance <= 3:  # Within reasonable distance
                    if token.i < other_token.i:
                        phrase = f"{token.text} {other_token.text}"
                    else:
                        phrase = f"{other_token.text} {token.text}"
                    possible_phrases.append(phrase)
        
        # Return all possible phrases joined (we'll check all of them)
        return " | ".join(possible_phrases)

    def _apply_linguistic_clues_plurals(self, evidence_score: float, potential_issue: Dict[str, Any], doc) -> float:
        """
        Apply linguistic analysis clues for pluralization detection.
        
        Analyzes SpaCy linguistic features including POS tags, dependency parsing,
        morphological features, and surrounding context to determine evidence strength.
        """
        issue_type = potential_issue['type']
        
        if issue_type == 'parenthetical_s':
            return self._apply_linguistic_clues_s_pattern(evidence_score, potential_issue['span_obj'], doc)
        elif issue_type == 'plural_adjective':
            return self._apply_linguistic_clues_plural_adjective(evidence_score, potential_issue['token'], potential_issue['sentence'])
        
        return evidence_score

    def _apply_structural_clues_plurals(self, evidence_score: float, potential_issue: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Apply document structure clues for pluralization detection.
        
        Analyzes document structure context including block types, heading levels,
        and other structural elements.
        """
        issue_type = potential_issue['type']
        
        if issue_type == 'parenthetical_s':
            return self._apply_structural_clues_s_pattern(evidence_score, potential_issue['span_obj'], context)
        elif issue_type == 'plural_adjective':
            return self._apply_structural_clues_plural_adjective(evidence_score, potential_issue['token'], context)
        
        return evidence_score

    def _apply_semantic_clues_plurals(self, evidence_score: float, potential_issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """
        Apply semantic and content-type clues for pluralization detection.
        
        Analyzes high-level semantic context including content type, domain, audience,
        and document purpose.
        """
        issue_type = potential_issue['type']
        
        if issue_type == 'parenthetical_s':
            return self._apply_semantic_clues_s_pattern(evidence_score, potential_issue['span_obj'], text, context)
        elif issue_type == 'plural_adjective':
            return self._apply_semantic_clues_plural_adjective(evidence_score, potential_issue['token'], text, context)
        
        return evidence_score

    def _apply_feedback_clues_plurals(self, evidence_score: float, potential_issue: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Apply feedback patterns for pluralization detection.
        
        Incorporates learned patterns from user feedback including acceptance rates,
        context-specific patterns, and correction success rates.
        """
        issue_type = potential_issue['type']
        
        if issue_type == 'parenthetical_s':
            # For (s) patterns, pass the base word for feedback analysis
            return self._apply_feedback_clues_s_pattern_enhanced(evidence_score, potential_issue['span_obj'], context, potential_issue.get('base_word'))
        elif issue_type == 'plural_adjective':
            return self._apply_feedback_clues_plural_adjective(evidence_score, potential_issue['token'], context)
        
        return evidence_score

    # === PARENTHETICAL (S) EVIDENCE METHODS ===

    def _get_base_s_pattern_evidence(self, span) -> float:
        """Get base evidence score for (s) pattern."""
        # All (s) patterns start with moderate evidence
        # The context will determine if it's acceptable or problematic
        return 0.7  # Default moderate evidence for (s) patterns

    def _apply_linguistic_clues_s_pattern(self, evidence_score: float, span, doc) -> float:
        """Apply linguistic analysis clues for (s) pattern detection."""
        
        # Handle both spaCy span and regex-based detection
        if span is None:
            # For regex-based detection, we don't have a spaCy span
            # The evidence calculation will work with sentence-level analysis
            return evidence_score
        
        # Get the word before (s)
        base_word = span[0]  # The word before (s)
        
        # === NAMED ENTITY RECOGNITION ===
        # Named entities may affect (s) pattern appropriateness
        if hasattr(base_word, 'ent_type_') and base_word.ent_type_:
            ent_type = base_word.ent_type_
            # Organizations and products often have established naming conventions
            if ent_type in ['ORG', 'PRODUCT', 'FAC']:
                evidence_score -= 0.3  # Organizations may legitimately use (s) for variations
            # Technical entities may have domain-specific conventions
            elif ent_type in ['GPE', 'NORP']:
                evidence_score -= 0.1  # Geographic/nationality entities may have variations
        
        # Check for named entities in sentence context
        for sent_token in span.sent:
            if hasattr(sent_token, 'ent_type_') and sent_token.ent_type_:
                ent_type = sent_token.ent_type_
                # Technical product entities suggest technical documentation
                if ent_type in ['PRODUCT', 'ORG', 'FAC']:
                    evidence_score -= 0.02  # Technical context allows more (s) usage
                # Money/quantity entities suggest formal specification
                elif ent_type in ['MONEY', 'QUANTITY', 'PERCENT']:
                    evidence_score -= 0.01  # Formal contexts may need (s) for ranges
        
        # === WORD TYPE ANALYSIS ===
        # Technical terms often have legitimate (s) usage for variability
        if base_word.pos_ in ['NOUN', 'PROPN']:
            if base_word.text.lower() in ['parameter', 'option', 'setting', 'value', 'file', 'directory']:
                evidence_score -= 0.3  # Technical terms often need (s) for flexibility
        
        # === SENTENCE POSITION ANALYSIS ===
        # (s) patterns at end of sentences often more problematic
        remaining_tokens = [t for t in span.sent[span.end:] if not t.is_punct and not t.is_space]
        if len(remaining_tokens) == 0:
            evidence_score += 0.1  # End of sentence (s) patterns more problematic
        
        # === SURROUNDING CONTEXT ===
        # Look for specification language around the (s) pattern
        specification_indicators = ['specify', 'configure', 'set', 'define', 'provide', 'enter']
        sentence_text = span.sent.text.lower()
        
        if any(indicator in sentence_text for indicator in specification_indicators):
            evidence_score -= 0.2  # Specification contexts often need (s) for flexibility
        
        # Look for placeholder/example language
        placeholder_indicators = ['example', 'sample', 'placeholder', 'template', 'format']
        if any(indicator in sentence_text for indicator in placeholder_indicators):
            evidence_score -= 0.3  # Placeholder contexts often use (s) appropriately
        
        return evidence_score

    def _apply_structural_clues_s_pattern(self, evidence_score: float, span, context: dict) -> float:
        """Apply document structure clues for (s) pattern detection."""
        
        # Handle case where span might be None (regex-based detection)
        if span is None:
            # Use context-based analysis only
            pass
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL DOCUMENTATION CONTEXTS ===
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.4  # Code examples often need (s) for variability
        elif block_type == 'inline_code':
            evidence_score -= 0.3  # Inline code often shows optional parameters
        
        # === SPECIFICATION CONTEXTS ===
        if block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.2  # Tables often show parameter variations
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.1  # Lists may show optional items
        
        # === FORMAL CONTEXTS ===
        if block_type in ['heading', 'title']:
            evidence_score += 0.2  # Headings should be clear and definitive
        
        # === EXAMPLE CONTEXTS ===
        if block_type in ['example', 'sample']:
            evidence_score -= 0.3  # Examples often show variations with (s)
        elif block_type in ['admonition']:
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP']:
                evidence_score -= 0.1  # Notes may explain optional variations
            elif admonition_type in ['WARNING', 'IMPORTANT']:
                evidence_score += 0.1  # Warnings should be definitive
        
        return evidence_score

    def _apply_semantic_clues_s_pattern(self, evidence_score: float, span, text: str, context: dict) -> float:
        """Apply semantic and content-type clues for (s) pattern detection."""
        
        # Handle case where span might be None (regex-based detection)
        if span is None:
            # Use context-based analysis only
            pass
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        if content_type == 'technical':
            evidence_score -= 0.2  # Technical docs often need (s) for parameter flexibility
        elif content_type == 'api':
            evidence_score -= 0.3  # API docs often show optional parameters with (s)
        elif content_type == 'academic':
            evidence_score += 0.1  # Academic writing should be precise
        elif content_type == 'legal':
            evidence_score += 0.2  # Legal writing must be unambiguous
        elif content_type == 'marketing':
            evidence_score += 0.2  # Marketing should be clear and direct
        elif content_type == 'procedural':
            evidence_score += 0.1  # Procedures should be specific
        elif content_type == 'narrative':
            evidence_score += 0.2  # Narrative writing should be clear
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score -= 0.2  # Technical domains often use (s) appropriately
        elif domain in ['configuration', 'installation']:
            evidence_score -= 0.3  # Setup domains often show optional steps
        elif domain in ['user-guide', 'tutorial']:
            evidence_score += 0.1  # User guides should be clear
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score -= 0.1  # Technical audiences understand (s) notation
        elif audience in ['beginner', 'general', 'user']:
            evidence_score += 0.2  # General audiences need clearer language
        
        # === DOCUMENT PURPOSE ANALYSIS ===
        if self._is_specification_documentation(text):
            evidence_score -= 0.2  # Specifications often need (s) for options
        
        if self._is_reference_documentation(text):
            evidence_score -= 0.1  # Reference docs may show variations
        
        if self._is_tutorial_content(text):
            evidence_score += 0.2  # Tutorials should be step-by-step clear
        
        return evidence_score

    def _apply_feedback_clues_s_pattern(self, evidence_score: float, span, context: dict) -> float:
        """Apply feedback patterns for (s) pattern detection."""
        
        feedback_patterns = self._get_cached_feedback_patterns('plurals')
        
        # This method is replaced by _apply_feedback_clues_s_pattern_enhanced
        return evidence_score
    
    def _apply_feedback_clues_s_pattern_enhanced(self, evidence_score: float, span, context: dict, base_word: str = None) -> float:
        """Enhanced feedback patterns for (s) pattern detection."""
        
        feedback_patterns = self._get_cached_feedback_patterns('plurals')
        
        # === WORD-SPECIFIC FEEDBACK ===
        # Handle both spaCy span and regex-based detection
        if span is not None:
            word_to_check = span[0].text.lower()
        elif base_word is not None:
            word_to_check = base_word.lower()
        else:
            return evidence_score  # Can't do word-specific analysis
        
        # Check if this word commonly has accepted (s) usage
        accepted_s_words = feedback_patterns.get('accepted_s_patterns', set())
        if word_to_check in accepted_s_words:
            evidence_score -= 0.3  # Users consistently accept (s) for this word
        
        flagged_s_words = feedback_patterns.get('flagged_s_patterns', set())
        if word_to_check in flagged_s_words:
            evidence_score += 0.3  # Users consistently flag (s) for this word
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get(f'{content_type}_s_patterns', {})
        
        if word_to_check in context_patterns.get('acceptable', set()):
            evidence_score -= 0.2
        elif word_to_check in context_patterns.get('problematic', set()):
            evidence_score += 0.2
        
        return evidence_score

    # === PLURAL ADJECTIVE EVIDENCE METHODS ===

    def _apply_linguistic_clues_plural_adjective(self, evidence_score: float, token, sentence) -> float:
        """Apply linguistic analysis clues for plural adjective detection."""
        
        # === DEPENDENCY ANALYSIS ===
        # Compound modifiers are more suspicious than other dependencies
        if token.dep_ == 'compound':
            evidence_score += 0.1  # Compound modifiers more likely to be errors
        elif token.dep_ == 'amod':
            evidence_score += 0.2  # Adjectival modifiers very likely to be errors
        elif token.dep_ == 'nsubj':
            evidence_score -= 0.1  # Subjects less likely to be adjective errors
        
        # === WORD FREQUENCY ANALYSIS ===
        # Common plurals used as modifiers have lower evidence
        common_modifier_plurals = {
            'systems', 'operations', 'services', 'applications', 'users',
            'communications', 'networks', 'resources', 'components', 'tools'
        }
        
        if token.text.lower() in common_modifier_plurals:
            evidence_score -= 0.2  # Common technical modifier plurals
        
        # === NAMED ENTITY RECOGNITION ===
        # Named entities may affect pluralization appropriateness
        if hasattr(token, 'ent_type_') and token.ent_type_:
            ent_type = token.ent_type_
            # Organizations and products often have specific naming conventions
            if ent_type in ['ORG', 'PRODUCT', 'FAC']:
                evidence_score -= 0.2  # Organizations may have established plural usage
            # Personal entities should follow standard grammar rules
            elif ent_type == 'PERSON':
                evidence_score += 0.1  # Personal entities should be grammatically correct
            # Technical entities may have domain-specific conventions
            elif ent_type in ['GPE', 'EVENT']:
                evidence_score -= 0.1  # Geographic/event entities may have special conventions
        
        # Check for named entities in surrounding context
        sentence = token.sent
        for sent_token in sentence:
            if hasattr(sent_token, 'ent_type_') and sent_token.ent_type_:
                ent_type = sent_token.ent_type_
                # Technical product entities suggest technical documentation
                if ent_type in ['PRODUCT', 'ORG', 'FAC']:
                    evidence_score -= 0.02  # Technical context allows more flexible pluralization
                # Money/quantity entities suggest formal documentation
                elif ent_type in ['MONEY', 'QUANTITY', 'PERCENT']:
                    evidence_score -= 0.01  # Financial/quantitative contexts may be more formal
        
        # === HEAD NOUN ANALYSIS ===
        head_noun = token.head
        if head_noun.pos_ == 'NOUN':
            # Check if head noun is a named entity
            if hasattr(head_noun, 'ent_type_') and head_noun.ent_type_:
                if head_noun.ent_type_ in ['PRODUCT', 'ORG']:
                    evidence_score -= 0.1  # Product/org head nouns may have special conventions
            
            # Technical head nouns often accept plural modifiers
            technical_heads = {
                'architecture', 'management', 'administration', 'analysis',
                'monitoring', 'configuration', 'documentation', 'interface'
            }
            
            if head_noun.lemma_.lower() in technical_heads:
                evidence_score -= 0.2  # Technical head nouns accept plural modifiers
        
        # === MORPHOLOGICAL ANALYSIS ===
        # Some plurals are inherently acceptable as modifiers
        inherent_modifier_plurals = {
            'data', 'media', 'criteria', 'metadata', 'analytics', 'metrics',
            'statistics', 'graphics', 'diagnostics', 'logistics'
        }
        
        if token.lemma_.lower() in inherent_modifier_plurals:
            evidence_score -= 0.4  # Inherently acceptable plural modifiers
        
        return evidence_score

    def _apply_structural_clues_plural_adjective(self, evidence_score: float, token, context: dict) -> float:
        """Apply document structure clues for plural adjective detection."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL CONTEXTS ===
        # Technical documentation more tolerant of plural adjectives
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.3  # Code contexts often use technical compound plurals
        elif block_type == 'inline_code':
            evidence_score -= 0.2  # Inline code may reference plural concepts
        
        # === SPECIFICATION CONTEXTS ===
        if block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.2  # Tables often use abbreviated compound terms
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.1  # Lists may use compact compound terms
        
        # === FORMAL CONTEXTS ===
        if block_type in ['heading', 'title']:
            evidence_score += 0.1  # Headings should use proper grammar
        
        # === DOCUMENTATION CONTEXTS ===
        if block_type in ['admonition']:
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP']:
                evidence_score -= 0.1  # Notes may use technical shorthand
        
        return evidence_score

    def _apply_semantic_clues_plural_adjective(self, evidence_score: float, token, text: str, context: dict) -> float:
        """Apply semantic and content-type clues for plural adjective detection."""
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        if content_type == 'technical':
            evidence_score -= 0.2  # Technical content more tolerant of plural adjectives
        elif content_type == 'api':
            evidence_score -= 0.2  # API docs often use technical compound terms
        elif content_type == 'academic':
            evidence_score += 0.2  # Academic writing prefers proper grammar
        elif content_type == 'legal':
            evidence_score += 0.1  # Legal writing should be grammatically correct
        elif content_type == 'marketing':
            evidence_score += 0.2  # Marketing should be grammatically polished
        elif content_type == 'procedural':
            evidence_score += 0.1  # Procedures should be clear and grammatical
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score -= 0.2  # Technical domains accept plural adjectives
        elif domain in ['systems-administration', 'network-management']:
            evidence_score -= 0.3  # System admin domains heavily use plural adjectives
        elif domain in ['user-documentation', 'tutorial']:
            evidence_score += 0.1  # User docs should be grammatically clear
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score -= 0.1  # Technical audiences accept technical compounds
        elif audience in ['beginner', 'general', 'user']:
            evidence_score += 0.1  # General audiences prefer standard grammar
        
        # === TECHNICAL DENSITY ANALYSIS ===
        if self._has_high_technical_density(text):
            evidence_score -= 0.1  # High technical density tolerates plural adjectives
        
        return evidence_score

    def _apply_feedback_clues_plural_adjective(self, evidence_score: float, token, context: dict) -> float:
        """Apply feedback patterns for plural adjective detection."""
        
        feedback_patterns = self._get_cached_feedback_patterns('plurals')
        
        # === TOKEN-SPECIFIC FEEDBACK ===
        token_text = token.text.lower()
        
        # Check if this specific plural is commonly accepted as modifier
        accepted_plural_modifiers = feedback_patterns.get('accepted_plural_modifiers', set())
        if token_text in accepted_plural_modifiers:
            evidence_score -= 0.3  # Users consistently accept this plural modifier
        
        flagged_plural_modifiers = feedback_patterns.get('flagged_plural_modifiers', set())
        if token_text in flagged_plural_modifiers:
            evidence_score += 0.3  # Users consistently flag this plural modifier
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get(f'{content_type}_plural_patterns', {})
        
        if token_text in context_patterns.get('acceptable', set()):
            evidence_score -= 0.2
        elif token_text in context_patterns.get('problematic', set()):
            evidence_score += 0.2
        
        # === COMPOUND PHRASE FEEDBACK ===
        # Check if this token is part of commonly accepted compound phrases
        head_noun = token.head
        if head_noun.pos_ == 'NOUN':
            compound_phrase = f"{token_text}_{head_noun.lemma_.lower()}"
            accepted_compounds = feedback_patterns.get('accepted_compound_phrases', set())
            
            if compound_phrase in accepted_compounds:
                evidence_score -= 0.2  # This compound phrase is commonly accepted
        
        return evidence_score

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_plurals_message(self, potential_issue: Dict[str, Any], evidence_score: float) -> str:
        """Generate context-aware error messages for pluralization patterns."""
        issue_type = potential_issue['type']
        
        if issue_type == 'parenthetical_s':
            return self._get_contextual_s_pattern_message(potential_issue['span_obj'], evidence_score, potential_issue.get('base_word'))
        elif issue_type == 'plural_adjective':
            return self._get_contextual_plural_adjective_message(potential_issue['token'], evidence_score)
        elif issue_type == 'incorrect_plural':
            return self._get_contextual_incorrect_plural_message(potential_issue['token'], evidence_score)
        
        return f"Pluralization issue detected in '{potential_issue['flagged_text']}'."

    def _generate_smart_plurals_suggestions(self, potential_issue: Dict[str, Any], evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for pluralization patterns."""
        issue_type = potential_issue['type']
        
        if issue_type == 'parenthetical_s':
            return self._generate_smart_s_pattern_suggestions(potential_issue['span_obj'], evidence_score, context, potential_issue.get('base_word'))
        elif issue_type == 'plural_adjective':
            return self._generate_smart_plural_adjective_suggestions(potential_issue['token'], evidence_score, context)
        elif issue_type == 'incorrect_plural':
            return self._generate_smart_incorrect_plural_suggestions(potential_issue['token'], evidence_score, context)
        
        return ["Consider reviewing the pluralization pattern."]

    def _get_contextual_s_pattern_message(self, span, evidence_score: float, base_word: str = None) -> str:
        """Generate context-aware error messages for (s) patterns."""
        
        # Handle both spaCy span and regex-based detection
        if span is not None:
            base_word = span[0].text
        elif base_word is None:
            base_word = "term"  # Fallback
        
        if evidence_score > 0.8:
            return f"Avoid using '({base_word})' to indicate a plural."
        elif evidence_score > 0.5:
            return f"Consider avoiding '({base_word})' pattern. Use either singular or plural form."
        else:
            return f"The '({base_word})' pattern may be acceptable in technical contexts but consider clarity."

    def _get_contextual_plural_adjective_message(self, token, evidence_score: float) -> str:
        """Generate context-aware error messages for plural adjectives."""
        
        if evidence_score > 0.8:
            return f"Potential misuse of plural noun '{token.text}' as an adjective."
        elif evidence_score > 0.5:
            return f"Consider using singular form: '{token.text}' may work better as '{token.lemma_}'."
        else:
            return f"Plural adjective '{token.text}' noted. May be acceptable in technical contexts."

    def _generate_smart_s_pattern_suggestions(self, span, evidence_score: float, context: dict, base_word: str = None) -> List[str]:
        """Generate context-aware suggestions for (s) patterns."""
        
        suggestions = []
        # Handle both spaCy span and regex-based detection
        if span is not None:
            base_word = span[0].text
        elif base_word is None:
            base_word = "term"  # Fallback
        
        # Base suggestions based on evidence strength
        if evidence_score > 0.7:
            suggestions.append(f"Use either '{base_word}' or '{base_word}s' consistently.")
            suggestions.append("Rewrite to use 'one or more' or 'multiple' instead.")
        else:
            suggestions.append(f"Consider using either '{base_word}' or '{base_word}s' for clarity.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type in ['technical', 'api']:
                suggestions.append("In technical docs, consider showing both forms in separate examples.")
            elif content_type in ['procedural', 'tutorial']:
                suggestions.append("For step-by-step instructions, use the specific form needed.")
            elif content_type == 'specification':
                suggestions.append("In specifications, use precise language without ambiguity.")
        
        return suggestions[:3]

    def _generate_smart_plural_adjective_suggestions(self, token, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions for plural adjectives."""
        
        suggestions = []
        singular_form = token.lemma_
        
        # Base suggestions based on evidence strength
        if evidence_score > 0.7:
            suggestions.append(f"Use the singular form '{singular_form}' when modifying another noun.")
        else:
            suggestions.append(f"Consider using '{singular_form}' instead of '{token.text}'.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type in ['technical', 'api']:
                suggestions.append("Technical writing may accept this usage if it's industry standard.")
            elif content_type in ['academic', 'formal']:
                suggestions.append("Use singular forms for grammatical correctness.")
        
        # Token-specific advice
        if token.text.lower() in ['systems', 'operations', 'services']:
            suggestions.append("This may be acceptable in technical compound terms.")
        
        return suggestions[:3]

    def _get_contextual_incorrect_plural_message(self, token, evidence_score: float) -> str:
        """Generate context-aware error messages for incorrect plural forms using YAML vocabulary."""
        
        # Load corrections from YAML vocabulary
        corrections = self.vocabulary_service.get_plurals_corrections()
        token_lower = token.text.lower()
        
        # PRIORITY 1: Check uncountable technical nouns first
        uncountable_technical = corrections.get('uncountable_technical_nouns', {})
        for technical_noun, config in uncountable_technical.items():
            incorrect_forms = config.get('incorrect_forms', [])
            if token_lower in [form.lower() for form in incorrect_forms]:
                correct_form = config.get('correct_plural_form', technical_noun)
                explanation = config.get('explanation', '')
                return f"'{token.text}' is incorrect. Use '{correct_form}' instead. {explanation}"
        
        # PRIORITY 2: Check traditional incorrect plurals
        incorrect_plurals = corrections.get('incorrect_plurals', {})
        correct_form = 'correct form'
        
        # Find the correct form from all categories
        for category in incorrect_plurals.values():
            if isinstance(category, dict) and token_lower in category:
                correct_form = category[token_lower]['correct_form']
                break
        
        return f"'{token.text}' is not a correct plural form. Use '{correct_form}' instead."

    def _generate_smart_incorrect_plural_suggestions(self, token, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate smart suggestions for incorrect plural forms using YAML vocabulary."""
        
        # Load corrections from YAML vocabulary
        corrections = self.vocabulary_service.get_plurals_corrections()
        token_lower = token.text.lower()
        suggestions = []
        
        # PRIORITY 1: Check uncountable technical nouns first
        uncountable_technical = corrections.get('uncountable_technical_nouns', {})
        for technical_noun, config in uncountable_technical.items():
            incorrect_forms = config.get('incorrect_forms', [])
            if token_lower in [form.lower() for form in incorrect_forms]:
                correct_form = config.get('correct_plural_form', technical_noun)
                never_suggest = config.get('never_suggest', [])
                
                # Preserve original capitalization
                if token.text[0].isupper():
                    correct_form_cap = correct_form.capitalize()
                    suggestions.append(correct_form_cap)
                else:
                    suggestions.append(correct_form)
                
                # Add technical noun specific explanation
                suggestions.append(f"'{correct_form}' is uncountable in technical contexts")
                
                # Add warning about archaic forms if applicable
                if never_suggest:
                    archaic_forms = ', '.join([f"'{form}'" for form in never_suggest])
                    suggestions.append(f"Never use archaic forms: {archaic_forms}")
                
                return suggestions[:3]
        
        # PRIORITY 2: Check traditional incorrect plurals
        incorrect_plurals = corrections.get('incorrect_plurals', {})
        correct_form = None
        correction_info = None
        
        # Find the correct form and additional info from all categories
        for category in incorrect_plurals.values():
            if isinstance(category, dict) and token_lower in category:
                correction_info = category[token_lower]
                correct_form = correction_info['correct_form']
                break
        
        if correct_form and correction_info:
            # Preserve original capitalization
            if token.text[0].isupper():
                correct_form_cap = correct_form.capitalize()
                suggestions.append(correct_form_cap)
            else:
                suggestions.append(correct_form)
                
            # Add explanation based on type
            correction_type = correction_info.get('type', 'correction')
            if correction_type == 'uncountable':
                suggestions.append(f"'{correct_form}' is uncountable and doesn't take a plural form")
            else:
                suggestions.append(f"The correct plural form is '{correct_form}'")
                
            # Add usage explanation if available
            explanation = correction_info.get('explanation')
            if explanation:
                suggestions.append(explanation)
        else:
            suggestions.append("Use the correct plural form")
        
        return suggestions[:3]

    def _is_legitimate_plural_subject(self, token) -> bool:
        """
        Check if token is a legitimate plural subject of a verb.
        
        This prevents false positives for cases like:
        - "enterprises move to the cloud" (enterprises = plural subject ✓)
        - "users access the system" (users = plural subject ✓)
        - "teams collaborate effectively" (teams = plural subject ✓)
        
        Production-ready approach using grammatical role analysis.
        """
        
        # Check if this token is a nominal subject
        if token.dep_ != 'nsubj':
            return False
        
        # Check if it's the subject of a verb (should have a verb head)
        if not (hasattr(token, 'head') and hasattr(token.head, 'pos_') and token.head.pos_ == 'VERB'):
            return False
        
        # Additional checks using YAML configuration
        corrections = self.vocabulary_service.get_plurals_corrections()
        subject_patterns = corrections.get('legitimate_plural_subjects', {})
        
        # Check if this word is commonly used as a plural subject
        word_lower = token.text.lower()
        common_plural_subjects = subject_patterns.get('common_business_entities', [])
        
        if word_lower in common_plural_subjects:
            return True
        
        # Check if the verb typically takes plural subjects
        verb_lemma = token.head.lemma_.lower()
        verbs_with_plural_subjects = subject_patterns.get('verbs_expecting_plural_subjects', [])
        
        if verb_lemma in verbs_with_plural_subjects:
            return True
        
        # Fallback: if it's clearly a legitimate plural subject pattern
        # Most plural subjects are legitimate unless they're clearly modifiers
        return True  # Default to allowing plural subjects