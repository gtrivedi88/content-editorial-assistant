"""
Plurals Rule
Based on IBM Style Guide topic: "Plurals"
"""
import re
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

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
        Analyzes sentences for pluralization errors.
        OPTIMIZED: (s) pattern detection now uses spaCy Matcher for better performance
        """
        errors = []
        if not nlp:
            return errors
        
        # Initialize Matcher for (s) patterns if available
        if SPACY_AVAILABLE:
            self._initialize_matcher(nlp)
        
        doc = nlp(text)

        # Rule 1: Avoid using "(s)" to indicate plural - DIRECT REPLACEMENT with Matcher
        if not SPACY_AVAILABLE:
            raise ImportError("spaCy is required for optimized plurals detection")
        
        # Use spaCy Matcher for high-performance (s) detection
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            if nlp.vocab.strings[match_id] == "PARENTHETICAL_S":
                span = doc[start:end]
                sentence_index = self._get_sentence_index(doc, span.start_char)
                
                # Skip if this pattern is in exceptions
                if self._is_excepted(span.text):
                    continue
                
                errors.append(self._create_error(
                    sentence=span.sent.text,
                    sentence_index=sentence_index,
                    message="Avoid using '(s)' to indicate a plural.",
                    suggestions=["Rewrite the sentence to use either the singular or plural form, or use a phrase like 'one or more'."],
                    severity='medium',
                    span=(span.start_char, span.end_char),
                    flagged_text=span.text
                ))

        # Rule 2: Avoid using plural nouns as adjectives (with technical exceptions)
        # PRESERVED: All existing morphological analysis logic
        for i, sent in enumerate(doc.sents):
            for token in sent:
                # LINGUISTIC ANCHOR: Check for plural nouns in modifier positions
                is_modifier = (token.tag_ == 'NNS' and 
                              token.dep_ in ('compound', 'nsubj', 'amod') and
                              token.lemma_ != token.lower_)
                
                if is_modifier:
                    # LINGUISTIC ANCHOR: Skip words that are actually functioning as verbs
                    if self._is_functioning_as_verb(token, sent.doc):
                        continue
                        
                    # LINGUISTIC ANCHOR: Skip legitimate technical compound plurals
                    if not self._is_legitimate_technical_compound(token, sent.doc):
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=f"Potential misuse of a plural noun '{token.text}' as an adjective.",
                            suggestions=[f"Consider using the singular form '{token.lemma_}' when a noun modifies another noun."],
                            severity='low',
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors

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