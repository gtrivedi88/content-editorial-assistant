"""
Articles Rule (YAML-based Linguistic Analysis)
Based on IBM Style Guide topic: "Articles"
Uses YAML-based phonetics vocabulary for maintainable article rules.
"""
from typing import List, Dict, Any, Optional
import pyinflect
from .base_language_rule import BaseLanguageRule
from .services.language_vocabulary_service import get_articles_vocabulary

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class ArticlesRule(BaseLanguageRule):
    """
    Checks for common article errors using YAML-based phonetics vocabulary.
    Uses true linguistic analysis to distinguish between countable and uncountable (mass) nouns.
    """
    
    def __init__(self):
        super().__init__()
        self.vocabulary_service = get_articles_vocabulary()
    
    def _get_rule_type(self) -> str:
        return 'articles'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for article errors using evidence-based scoring.
        Uses sophisticated linguistic analysis to distinguish genuine errors from 
        acceptable technical usage and contextual variations.
        """
        errors = []
        if not nlp:
            return errors

        content_classification = self._get_content_classification(text, context, nlp)
        if not self._should_apply_rule(self._get_rule_category(), content_classification):
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                # Check for incorrect a/an usage
                if token.lower_ in ['a', 'an'] and token.i + 1 < len(doc):
                    next_token = doc[token.i + 1]
                    if self._is_incorrect_article_usage(token, next_token):
                        # Calculate evidence score for this incorrect usage
                        evidence_score = self._calculate_incorrect_article_evidence(
                            token, next_token, sent, text, context
                        )
                        
                        # Only create error if evidence suggests it's worth flagging
                        if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                            errors.append(self._create_error(
                                sentence=sent.text, sentence_index=i,
                                message=self._get_contextual_message_incorrect(token, next_token, evidence_score),
                                suggestions=self._generate_smart_suggestions_incorrect(token, next_token, evidence_score, context),
                                severity='medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,  # Your nuanced assessment
                                span=(token.idx, next_token.idx + len(next_token.text)),
                                flagged_text=f"{token.text} {next_token.text}"
                            ))
                
                # Check for missing articles (only in appropriate content types)
                if content_classification == 'descriptive_content' and self._is_missing_article_candidate(token, doc) and not self._is_admonition_context(token, context):
                    # Calculate evidence score for this missing article
                    evidence_score = self._calculate_missing_article_evidence(
                        token, sent, text, context, content_classification
                    )
                    
                    # Only create error if evidence suggests it's worth flagging
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=i,
                            message=self._get_contextual_message_missing(token, evidence_score),
                            suggestions=self._generate_smart_suggestions_missing(token, evidence_score, context),
                            severity='low',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,  # Your nuanced assessment
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors

    def _starts_with_vowel_sound(self, word: str) -> bool:
        """
        YAML-based phonetic analysis for article selection.
        Determines vowel vs. consonant sound based on YAML vocabulary, not spelling.
        """
        word_lower = word.lower()
        
        # Load phonetics vocabulary from YAML
        phonetics = self.vocabulary_service.get_articles_phonetics()
        
        # Check consonant sound words (vowel letters but consonant sounds)
        consonant_sound_words = set()
        consonant_data = phonetics.get('consonant_sound_words', {})
        for category in consonant_data.values():
            if isinstance(category, list):
                consonant_sound_words.update(category)
        
        # Check vowel sound words (consonant letters but vowel sounds)
        vowel_sound_words = set()
        vowel_data = phonetics.get('vowel_sound_words', {})
        for category in vowel_data.values():
            if isinstance(category, list):
                vowel_sound_words.update(category)
        
        # Check exact word matches first (most accurate)
        if word_lower in consonant_sound_words:
            return False
        if word_lower in vowel_sound_words:
            return True
            
        # LINGUISTIC ANCHOR 3: Pattern-based phonetic rules
        # Handle common prefixes that affect pronunciation
        if word_lower.startswith('uni') and len(word_lower) > 3:
            # Most "uni-" words are pronounced /j/ (university, uniform, etc.)
            return False
        
        if word_lower.startswith('eu') and len(word_lower) > 2:
            # Most "eu-" words are pronounced /j/ (European, euphemism, etc.)  
            return False
        
        # LINGUISTIC ANCHOR 4: Default vowel letter check
        # Fall back to simple vowel letter detection for other cases
        return word_lower[0] in 'aeiou'

    def _is_incorrect_article_usage(self, article_token: Token, next_token: Token) -> bool:
        if 'attributeplaceholder' in next_token.text or 'asciidoclinkplaceholder' in next_token.text:
            return False
        starts_with_vowel = self._starts_with_vowel_sound(next_token.text)
        if article_token.lower_ == 'a' and starts_with_vowel: return True
        if article_token.lower_ == 'an' and not starts_with_vowel: return True
        return False

    def _is_uncountable(self, token: Token) -> bool:
        """
        LINGUISTIC ANCHOR: Enhanced mass noun detection for technical contexts.
        Combines pyinflect analysis with comprehensive technical mass noun lists.
        """
        lemma = token.lemma_.lower()
        
        # LINGUISTIC ANCHOR 1: Comprehensive technical mass nouns
        # These are commonly used as uncountable in technical writing
        technical_mass_nouns = {
            # Network/System terms
            'traffic', 'bandwidth', 'throughput', 'latency', 'connectivity',
            'performance', 'availability', 'reliability', 'scalability', 
            'compatibility', 'interoperability', 'security', 'encryption',
            
            # Data/Information terms  
            'data', 'information', 'metadata', 'content', 'storage',
            'consistency', 'integrity', 'accuracy', 'redundancy', 'backup',
            'synchronization', 'replication', 'validation', 'verification',
            
            # Process/Quality terms
            'maintenance', 'monitoring', 'logging', 'debugging', 'testing',
            'optimization', 'configuration', 'deployment', 'installation',
            'documentation', 'compliance', 'governance', 'oversight',
            
            # Resource terms
            'memory', 'storage', 'bandwidth', 'capacity', 'utilization', 'usage',
            'consumption', 'allocation', 'provisioning', 'scaling',
            
            # Abstract technical concepts
            'functionality', 'usability', 'efficiency', 'productivity',
            'transparency', 'flexibility', 'extensibility', 'modularity',
            'abstraction', 'encapsulation', 'inheritance', 'polymorphism',
            
            # Common mass nouns
            'software', 'hardware', 'middleware', 'firmware', 'malware',
            'feedback', 'research', 'analysis', 'synthesis', 'knowledge',
            'expertise', 'experience', 'training', 'education', 'learning'
        }
        
        # LINGUISTIC ANCHOR 2: Check technical mass noun list first
        if lemma in technical_mass_nouns:
            return True
        
        # LINGUISTIC ANCHOR 3: Context-aware mass noun detection
        # Check if the noun is used in typical mass noun contexts
        if self._is_mass_noun_context(token):
            return True
        
        # LINGUISTIC ANCHOR 4: Fallback to pyinflect for other cases
        plural_form = pyinflect.getInflection(token.lemma_, 'NNS')
        return plural_form is None

    def _is_mass_noun_context(self, token: Token) -> bool:
        """
        LINGUISTIC ANCHOR: Context-aware mass noun detection.
        Identifies when a noun is used in typical mass noun contexts.
        """
        # PATTERN 1: Verbs that typically take mass noun objects
        mass_noun_verbs = {
            'ensure', 'ensures', 'provide', 'provides', 'require', 'requires',
            'maintain', 'maintains', 'achieve', 'achieves', 'improve', 'improves',
            'manage', 'manages', 'handle', 'handles', 'process', 'processes',
            'direct', 'directs', 'control', 'controls', 'monitor', 'monitors',
            'optimize', 'optimizes', 'enhance', 'enhances', 'maximize', 'maximizes'
        }
        
        # Check if this noun is the direct object of a mass-noun-taking verb
        if (token.dep_ == 'dobj' and 
            token.head.pos_ == 'VERB' and 
            token.head.lemma_.lower() in mass_noun_verbs):
            return True
        
        # PATTERN 2: Prepositions that commonly precede mass nouns
        mass_noun_prepositions = {
            'for', 'with', 'of', 'in', 'on', 'through', 'via', 'by'
        }
        
        # Check if this noun follows a preposition that commonly takes mass nouns
        if (token.dep_ == 'pobj' and 
            token.head.pos_ == 'ADP' and 
            token.head.lemma_.lower() in mass_noun_prepositions):
            return True
        
        # PATTERN 3: Common mass noun phrase patterns
        # Check for patterns like "data X", "network X", "system X"
        if token.i > 0:
            prev_token = token.doc[token.i - 1]
            mass_noun_modifiers = {
                'data', 'network', 'system', 'application', 'service',
                'database', 'server', 'client', 'user', 'admin',
                'security', 'performance', 'quality', 'real-time'
            }
            
            if (prev_token.pos_ in ('NOUN', 'ADJ') and 
                prev_token.lemma_.lower() in mass_noun_modifiers and
                token.dep_ in ('compound', 'dobj', 'pobj')):
                return True
        
        return False

    def _is_missing_article_candidate(self, token: Token, doc: Doc) -> bool:
        # LINGUISTIC ANCHOR 1: Basic POS and morphology checks.
        if not (token.pos_ == 'NOUN' and token.tag_ == 'NN' and not self._is_uncountable(token)):
            return False
            
        # LINGUISTIC ANCHOR 2: Check for existing determiners or possessives.
        if any(child.dep_ in ('det', 'poss') for child in token.children) or token.dep_ == 'poss':
            return False

        # LINGUISTIC ANCHOR 3: Check for grammatical contexts where articles are not used.
        if token.dep_ == 'compound':
            return False
        if token.lemma_.lower() == 'step' and token.i + 1 < len(doc) and doc[token.i + 1].like_num:
            return False
            
        # LINGUISTIC ANCHOR 3a: Technical terms in prepositional phrases (existing logic)
        if token.dep_ == 'pobj':
            prep = token.head
            if prep.lemma_ in ['in', 'on', 'at', 'by', 'before', 'after'] and prep.head.pos_ == 'VERB':
                if token.lemma_ in ['bold', 'italic', 'deployment', 'substitution', 'text']:
                    return False
        
        # LINGUISTIC ANCHOR 3b: Compound technical phrases (NEW)
        if self._is_technical_compound_phrase(token, doc):
            return False
            
        # LINGUISTIC ANCHOR 3c: Technical terms in coordinated constructions (NEW)
        if self._is_technical_coordination(token, doc):
            return False
        
        # LINGUISTIC ANCHOR 4: The noun must be in a role that typically requires an article.
        if token.dep_ in ('nsubj', 'dobj', 'pobj', 'attr'):
            if token.i > 0 and ('attributeplaceholder' in doc[token.i - 1].text or 'asciidoclinkplaceholder' in doc[token.i - 1].text):
                return False
            return True
            
        return False

    def _is_technical_compound_phrase(self, token: Token, doc: Doc) -> bool:
        """
        Detects technical compound phrases where articles are typically omitted.
        Examples: "attribute substitution", "error handling", "data processing"
        """
        # Define technical terms commonly used without articles
        technical_terms = {
            'substitution', 'text', 'bold', 'italic', 'deployment', 'configuration',
            'analysis', 'processing', 'handling', 'formatting', 'styling', 'parsing',
            'validation', 'authentication', 'authorization', 'encryption', 'compression',
            'optimization', 'integration', 'implementation', 'documentation', 'testing',
            'debugging', 'monitoring', 'logging', 'caching', 'indexing', 'rendering',
            'compilation', 'execution', 'initialization', 'installation', 'backup',
            'recovery', 'migration', 'synchronization', 'serialization', 'deserialization'
        }
        
        if token.lemma_.lower() not in technical_terms:
            return False
        
        # Check if this noun is modified by technical adjectives or other nouns
        technical_modifiers = {
            'attribute', 'parameter', 'configuration', 'system', 'data', 'file',
            'database', 'network', 'security', 'user', 'admin', 'server', 'client',
            'application', 'service', 'component', 'module', 'library', 'framework',
            'algorithm', 'protocol', 'interface', 'api', 'endpoint', 'resource',
            'metadata', 'schema', 'template', 'pattern', 'model', 'structure',
            'format', 'syntax', 'semantic', 'logical', 'physical', 'virtual',
            'dynamic', 'static', 'automatic', 'manual', 'custom', 'default',
            'basic', 'advanced', 'complex', 'simple', 'standard', 'extended',
            'paragraph'  # Added for "paragraph analysis"
        }
        
        # Look for technical modifiers in children (adjectives or noun modifiers)
        for child in token.children:
            if (child.pos_ in ('ADJ', 'NOUN') and 
                child.dep_ in ('amod', 'nmod', 'compound') and
                child.lemma_.lower() in technical_modifiers):
                return True
        
        # Look for technical modifiers as siblings in coordinated structures
        if token.dep_ == 'dobj':
            # Check siblings that are coordinated or modify the same head
            for sibling in token.head.children:
                if (sibling != token and sibling.pos_ in ('ADJ', 'NOUN') and
                    sibling.dep_ in ('amod', 'nmod') and
                    sibling.lemma_.lower() in technical_modifiers):
                    return True
        
        return False

    def _is_technical_coordination(self, token: Token, doc: Doc) -> bool:
        """
        Detects when a technical term is part of a coordination with other technical terms.
        Examples: "analysis and substitution", "formatting and styling"
        """
        technical_terms = {
            'substitution', 'text', 'bold', 'italic', 'deployment', 'configuration',
            'analysis', 'processing', 'handling', 'formatting', 'styling', 'parsing',
            'validation', 'authentication', 'authorization', 'encryption', 'compression',
            'optimization', 'integration', 'implementation', 'documentation', 'testing',
            'debugging', 'monitoring', 'logging', 'caching', 'indexing', 'rendering'
        }
        
        if token.lemma_.lower() not in technical_terms:
            return False
        
        # Check if this token is part of a coordination (conj dependency)
        if token.dep_ == 'conj':
            # Check if it's coordinated with another technical term
            head = token.head
            if head.lemma_.lower() in technical_terms:
                return True
        
        # Check if this token has technical terms as conjuncts
        for child in token.children:
            if (child.dep_ == 'conj' and 
                child.pos_ == 'NOUN' and
                child.lemma_.lower() in technical_terms):
                return True
        
        return False

    def _is_admonition_context(self, token: Token, context: Optional[Dict[str, Any]]) -> bool:
        """
        LINGUISTIC ANCHOR: Context-aware admonition detection using structural information.
        Checks if we're in a context where admonition keywords are legitimate.
        """
        if not context:
            return False
        
        # Check if we're in an admonition block
        if context.get('block_type') == 'admonition':
            return True
        
        # Check if the next block is an admonition (introducing context)
        if context.get('next_block_type') == 'admonition':
            return True
        
        # Check if this is an admonition-related keyword
        admonition_keywords = {'note', 'tip', 'important', 'warning', 'caution'}
        if token.lemma_.lower() in admonition_keywords:
            return True
        
        return False

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _calculate_incorrect_article_evidence(self, article_token, next_token, sentence, text: str, context: dict) -> float:
        """
        Calculate evidence score (0.0-1.0) for incorrect a/an usage.
        
        Higher scores indicate stronger evidence of a genuine error.
        Lower scores indicate borderline cases or acceptable variations.
        
        Args:
            article_token: The article token (a/an)
            next_token: The following word token
            sentence: Sentence containing the tokens
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (clear error)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # This is definitely an incorrect article usage (phonetically wrong)
        evidence_score = 0.8  # Start with high evidence for phonetic errors
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_incorrect(evidence_score, article_token, next_token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_incorrect(evidence_score, article_token, next_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_incorrect(evidence_score, article_token, next_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_incorrect(evidence_score, article_token, next_token, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _calculate_missing_article_evidence(self, noun_token, sentence, text: str, context: dict, content_classification: str) -> float:
        """
        Calculate evidence score (0.0-1.0) for missing article before noun.
        
        Higher scores indicate stronger evidence of missing article.
        Lower scores indicate acceptable omission or technical usage.
        
        Args:
            noun_token: The noun token potentially missing an article
            sentence: Sentence containing the token
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            content_classification: Content type classification
            
        Returns:
            float: Evidence score from 0.0 (acceptable omission) to 1.0 (missing article)
        """
        
        # === ZERO FALSE POSITIVE GUARD FOR UNCOUNTABLE TECHNICAL COMPOUNDS ===
        # CRITICAL: Before any other analysis, check if the noun is part of a
        # well-known uncountable technical compound noun (e.g., "disk space").
        # If so, it is not an error, so we return 0.0 immediately.

        if noun_token.i > 0:
            doc = noun_token.doc
            prev_token = doc[noun_token.i - 1]
            # Check if the preceding token is a noun or adjective modifying our target noun
            if prev_token.dep_ in ('compound', 'amod'):
                compound_phrase = f"{prev_token.text.lower()} {noun_token.text.lower()}"
                
                # This set can be expanded over time with more examples.
                uncountable_compounds = {
                    "disk space",
                    "error handling",
                    "data processing",
                    "user authentication",
                    "attribute substitution",
                    "system performance",
                    "network traffic",
                    "load balancing"
                }
                
                if compound_phrase in uncountable_compounds:
                    return 0.0  # This is a known technical phrase, not an error.

        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Start with moderate evidence for missing article candidate
        evidence_score = 0.6  # Start with moderate evidence
        
        # === INLINE LIST CLUE (EARLY EXIT FOR LIST ITEMS) ===
        # Detect inline lists where articles are commonly and correctly omitted
        if self._is_inline_list_item(noun_token, sentence, text, context):
            evidence_score -= 0.5  # Major reduction for inline list items
            # In list items, articles are often correctly omitted for brevity:
            # "- Configuration options" (not "- The configuration options")
            # "1. User authentication" (not "1. The user authentication")
            # "* Database connections" (not "* The database connections")
        
        # === STYLE POLISH: FORMAL VERB + ABSTRACT NOUN CLUE ===
        # Detect formal constructions where abstract nouns as direct objects appropriately omit articles
        if self._is_formal_verb_abstract_noun_construction(noun_token, sentence):
            evidence_score -= 0.4  # Significant reduction for formal linguistic constructions
            # Examples of appropriate article omission in formal contexts:
            # "This constitutes failure" (not "This constitutes a failure")
            # "The system requires access" (not "The system requires an access")
            # "The process involves risk" (not "The process involves a risk")
            # "This introduces compliance" (not "This introduces a compliance")
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_missing(evidence_score, noun_token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_missing(evidence_score, noun_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_missing(evidence_score, noun_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_missing(evidence_score, noun_token, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _is_inline_list_item(self, noun_token, sentence, text: str, context: dict) -> bool:
        """
        Detect if a noun is the first word after an inline list marker.
        
        Uses regex to detect lines starting with:
        - Hyphen/bullet: "- Configuration options"
        - Asterisk: "* Database connections" 
        - Numbers: "1. User authentication", "2) Setup process"
        
        Args:
            noun_token: The noun token to check
            sentence: Sentence containing the noun
            text: Full document text
            context: Document context
            
        Returns:
            bool: True if noun follows an inline list marker
        """
        import re
        
        # Only check in paragraph blocks where inline lists commonly appear
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        if block_type not in ['paragraph', 'section', 'admonition']:
            return False
        
        # Get the sentence text and find the noun's position within it
        sentence_text = sentence.text
        noun_start_in_sentence = noun_token.idx - sentence.start_char
        
        if noun_start_in_sentence < 0:
            return False
        
        # Look at the text before the noun in the sentence
        text_before_noun = sentence_text[:noun_start_in_sentence].strip()
        
        # Regex patterns for inline list markers
        inline_list_patterns = [
            r'^-\s+',           # "- Configuration"
            r'^\*\s+',          # "* Database"
            r'^\d+\.\s+',       # "1. User", "2. Admin"
            r'^\d+\)\s+',       # "1) Setup", "2) Config"
            r'^[a-zA-Z]\.\s+',  # "a. First", "A. Primary"
            r'^[a-zA-Z]\)\s+',  # "a) Setup", "b) Config"
            r'^[ivxlcdm]+\.\s+', # "i. First", "ii. Second" (roman numerals)
            r'^[IVXLCDM]+\.\s+', # "I. Primary", "II. Secondary"
        ]
        
        # Check if any pattern matches the beginning of the text before the noun
        for pattern in inline_list_patterns:
            if re.match(pattern, text_before_noun, re.IGNORECASE):
                # Additional check: ensure the noun is reasonably close to the list marker
                # (within first few words after the marker)
                remaining_text = re.sub(pattern, '', text_before_noun, count=1, flags=re.IGNORECASE).strip()
                
                # If there are no words or only 1-2 words between marker and noun, it's likely a list item
                word_count_between = len(remaining_text.split()) if remaining_text else 0
                
                if word_count_between <= 2:  # Allow some words like "the new configuration"
                    return True
        
        # ENHANCED: Check the original text line containing this sentence
        # spaCy may not include list markers in sentence.text, so we need to check the original line
        sentence_start = sentence.start_char
        sentence_end = sentence.start_char + len(sentence_text)
        
        # Find the line containing this sentence in the original text
        lines_before_sentence = text[:sentence_start].split('\n')
        current_line_start = sentence_start - len(lines_before_sentence[-1]) if len(lines_before_sentence) > 1 else 0
        
        # Find the end of the current line
        remaining_text = text[sentence_start:]
        next_newline = remaining_text.find('\n')
        current_line_end = sentence_start + (next_newline if next_newline != -1 else len(remaining_text))
        
        # Extract the full line containing the sentence
        full_line = text[current_line_start:current_line_end].strip()
        
        # Check if this full line starts with a list marker
        for pattern in inline_list_patterns:
            if re.match(pattern, full_line, re.IGNORECASE):
                # Check if noun appears early in the line after the marker
                marker_match = re.match(pattern, full_line, re.IGNORECASE)
                if marker_match:
                    text_after_marker = full_line[marker_match.end():].strip()
                    words_after_marker = text_after_marker.split()
                    
                    # If noun is one of the first few words after the marker
                    noun_text = noun_token.text.lower()
                    if len(words_after_marker) > 0 and words_after_marker[0].lower() == noun_text:
                        return True
                    elif len(words_after_marker) > 1 and words_after_marker[1].lower() == noun_text:
                        return True  # Allow for one word like "new" before the noun
                    elif len(words_after_marker) > 2 and words_after_marker[2].lower() == noun_text:
                        return True  # Allow for two words like "new technical" before the noun
        
        return False

    def _is_formal_verb_abstract_noun_construction(self, noun_token, sentence) -> bool:
        """
        Detect formal verb + abstract noun constructions where articles are appropriately omitted.
        
        Analyzes the syntactic relationship between formal verbs and abstract nouns to identify
        constructions where article omission is stylistically appropriate in formal writing.
        
        Examples of legitimate omission:
        - "This constitutes failure" (formal legal/business language)
        - "The system requires access" (technical specification)
        - "The process involves risk" (formal assessment)
        - "This introduces compliance" (regulatory language)
        
        Args:
            noun_token: The noun token potentially missing an article
            sentence: Sentence containing the noun
            
        Returns:
            bool: True if noun is direct object of formal verb in abstract construction
        """
        if not noun_token or not hasattr(noun_token, 'head') or not hasattr(noun_token, 'dep_'):
            return False
        
        # === FORMAL VERB PATTERNS ===
        # List of formal verbs that often take abstract nouns without articles
        formal_verbs = {
            # Core formal verbs specified by user
            'constitute', 'constitutes', 'constituting', 'constituted',
            'introduce', 'introduces', 'introducing', 'introduced', 
            'require', 'requires', 'requiring', 'required',
            'involve', 'involves', 'involving', 'involved',
            
            # Extended formal verbs for broader coverage
            'represent', 'represents', 'representing', 'represented',
            'establish', 'establishes', 'establishing', 'established',
            'demonstrate', 'demonstrates', 'demonstrating', 'demonstrated',
            'ensure', 'ensures', 'ensuring', 'ensured',
            'provide', 'provides', 'providing', 'provided',
            'maintain', 'maintains', 'maintaining', 'maintained',
            'achieve', 'achieves', 'achieving', 'achieved',
            'facilitate', 'facilitates', 'facilitating', 'facilitated'
        }
        
        # === ABSTRACT NOUN PATTERNS ===
        # List of abstract nouns that often appear without articles in formal contexts
        abstract_nouns = {
            # Core abstract nouns specified by user
            'failure', 'agreement', 'risk', 'access', 'compliance',
            
            # Extended abstract nouns for broader coverage
            'success', 'progress', 'development', 'improvement', 'enhancement',
            'security', 'stability', 'reliability', 'availability', 'performance',
            'control', 'management', 'oversight', 'governance', 'supervision',
            'consistency', 'compatibility', 'integration', 'implementation', 'deployment',
            'validation', 'verification', 'authentication', 'authorization', 'approval',
            'transparency', 'accountability', 'responsibility', 'liability', 'coverage',
            'efficiency', 'effectiveness', 'productivity', 'scalability', 'flexibility',
            'maintainability', 'sustainability', 'viability', 'functionality', 'capability'
        }
        
        # === DEPENDENCY ANALYSIS ===
        # Check if the noun is a direct object (dobj) of a formal verb
        
        noun_text = noun_token.text.lower()
        
        # First check if the noun is in our abstract noun list
        if noun_text not in abstract_nouns:
            return False
        
        # Check if noun is direct object
        if noun_token.dep_ != 'dobj':
            return False
        
        # Get the head verb (the verb this noun is a direct object of)
        head_token = noun_token.head
        
        if not hasattr(head_token, 'lemma_') or not hasattr(head_token, 'pos_'):
            return False
        
        # Check if head is a verb
        if head_token.pos_ not in ['VERB', 'AUX']:
            return False
        
        # Check if the head verb is in our formal verb list
        head_lemma = head_token.lemma_.lower()
        head_text = head_token.text.lower()
        
        if head_lemma in formal_verbs or head_text in formal_verbs:
            return True
        
        # === ADDITIONAL PATTERN CHECKS ===
        # Check for passive constructions: "is required by", "was established through"
        if (head_token.dep_ == 'auxpass' or head_token.dep_ == 'nsubjpass'):
            # Look for formal verb patterns in passive voice
            for token in sentence:
                if (hasattr(token, 'lemma_') and 
                    token.lemma_.lower() in formal_verbs and
                    token.pos_ in ['VERB', 'AUX']):
                    return True
        
        return False

    # === LINGUISTIC CLUES FOR INCORRECT A/AN USAGE ===

    def _apply_linguistic_clues_incorrect(self, evidence_score: float, article_token, next_token, sentence) -> float:
        """Apply linguistic analysis clues for incorrect a/an usage."""
        
        word = next_token.text.lower()
        
        # === COMMON WORDS WITH KNOWN PRONUNCIATION ===
        # Words where the pronunciation is very well established
        common_words_vowel_sound = {
            'hour', 'honest', 'honor', 'heir', 'herb', 'api', 'fbi', 'html', 'sql', 'xml'
        }
        common_words_consonant_sound = {
            'user', 'unique', 'university', 'unix', 'ubuntu', 'url', 'utility', 'one', 'once', 'european'
        }
        
        if word in common_words_vowel_sound or word in common_words_consonant_sound:
            evidence_score += 0.1  # Very clear pronunciation, high confidence in error
        
        # === TECHNICAL ABBREVIATIONS ===
        # Technical abbreviations have more standardized pronunciations
        if word.isupper() and len(word) <= 5:
            evidence_score += 0.1  # Technical abbreviations have clear pronunciations
        
        # === PROPER NOUNS ===
        # Proper nouns may have less standardized pronunciations
        if next_token.pos_ == 'PROPN':
            evidence_score -= 0.1  # Proper nouns might have variant pronunciations
        
        # === FOREIGN WORDS ===
        # Check for potential foreign words that might have uncertain pronunciation
        if next_token.ent_type_ in ['LANGUAGE', 'NORP']:
            evidence_score -= 0.2  # Foreign/cultural terms might have variant pronunciations
        
        # === CONTEXT WITHIN SENTENCE ===
        # Article errors in certain grammatical positions are more problematic
        if article_token.dep_ == 'det' and next_token.dep_ == 'nsubj':
            evidence_score += 0.1  # Subject position more noticeable
        elif article_token.dep_ == 'det' and next_token.dep_ == 'dobj':
            evidence_score += 0.05  # Object position somewhat noticeable
        
        return evidence_score

    def _apply_structural_clues_incorrect(self, evidence_score: float, article_token, next_token, context: dict) -> float:
        """Apply document structure-based clues for incorrect a/an usage."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # === FORMAL WRITING CONTEXTS ===
        # In formal contexts, article errors are more problematic
        if block_type in ['heading', 'title']:
            evidence_score += 0.2  # Headings are highly visible
        elif block_type == 'paragraph':
            evidence_score += 0.1  # Body text somewhat visible
        
        # === TECHNICAL CONTEXTS ===
        # In technical contexts, precision is important but tolerance may be higher
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.3  # Code comments more forgiving
        elif block_type == 'inline_code':
            evidence_score -= 0.2  # Inline technical content
        
        # === LISTS AND TABLES ===
        # Abbreviated contexts may be more tolerant
        if block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.1  # List items often abbreviated
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.2  # Tables often use abbreviated language
        
        # === ADMONITIONS ===
        # Notes and warnings should be clear
        if block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['IMPORTANT', 'WARNING', 'CAUTION']:
                evidence_score += 0.1  # Important messages should be clear
        
        return evidence_score

    def _apply_semantic_clues_incorrect(self, evidence_score: float, article_token, next_token, text: str, context: dict) -> float:
        """Apply semantic and content-type clues for incorrect a/an usage."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Different content types have different tolerance for errors
        if content_type == 'technical':
            evidence_score -= 0.1  # Technical writing somewhat more forgiving of minor errors
        elif content_type == 'academic':
            evidence_score += 0.2  # Academic writing expects precision
        elif content_type == 'legal':
            evidence_score += 0.3  # Legal writing demands precision
        elif content_type == 'marketing':
            evidence_score -= 0.2  # Marketing more focused on message than perfection
        elif content_type == 'api':
            evidence_score -= 0.1  # API docs focus on functionality
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['academic', 'legal', 'professional']:
            evidence_score += 0.1  # Professional audiences expect accuracy
        elif audience in ['developer', 'technical']:
            evidence_score -= 0.05  # Technical audiences may be more forgiving of minor errors
        elif audience in ['beginner', 'student']:
            evidence_score += 0.1  # Educational content should model correct usage
        
        # === DOCUMENT FORMALITY ===
        # Check for formality indicators in the surrounding text
        formal_indicators = self._count_formal_indicators(text)
        if formal_indicators > 5:  # High formality
            evidence_score += 0.1
        elif formal_indicators < 2:  # Low formality
            evidence_score -= 0.1
        
        return evidence_score

    def _apply_feedback_clues_incorrect(self, evidence_score: float, article_token, next_token, context: dict) -> float:
        """Apply feedback patterns for incorrect a/an usage."""
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns('articles')
        
        word = next_token.text.lower()
        article = article_token.text.lower()
        
        # Check if this specific word has consistent feedback
        word_feedback = feedback_patterns.get('word_article_corrections', {})
        if word in word_feedback:
            expected_article = word_feedback[word]
            if article != expected_article:
                evidence_score += 0.2  # Consistent user feedback indicates this is wrong
            else:
                evidence_score -= 0.1  # This combination is typically accepted
        
        # Check for common correction patterns
        common_corrections = feedback_patterns.get('common_article_corrections', set())
        error_pattern = f"{article} {word}"
        if error_pattern in common_corrections:
            evidence_score += 0.3  # This is a commonly corrected error
        
        return evidence_score

    # === LINGUISTIC CLUES FOR MISSING ARTICLES ===

    def _apply_linguistic_clues_missing(self, evidence_score: float, noun_token, sentence) -> float:
        """Apply linguistic analysis clues for missing articles."""
        
        # === GRAMMATICAL ROLE ANALYSIS ===
        # Subjects and objects usually need articles more than other roles
        if noun_token.dep_ == 'nsubj':
            evidence_score += 0.2  # Subjects usually need articles
        elif noun_token.dep_ == 'dobj':
            evidence_score += 0.1  # Direct objects often need articles
        elif noun_token.dep_ == 'pobj':
            evidence_score += 0.05  # Prepositional objects sometimes need articles
        elif noun_token.dep_ in ['compound', 'npadvmod']:
            evidence_score -= 0.3  # Compound terms often don't need articles
        
        # === COUNTABILITY ANALYSIS ===
        # Use existing sophisticated countability detection
        if self._is_uncountable(noun_token):
            evidence_score -= 0.4  # Uncountable nouns often don't need articles
        
        # === TECHNICAL TERM ANALYSIS ===
        # Technical terms often used without articles
        if self._is_technical_compound_phrase(noun_token, noun_token.doc):
            evidence_score -= 0.3  # Technical compounds often don't need articles
        
        if self._is_technical_coordination(noun_token, noun_token.doc):
            evidence_score -= 0.2  # Coordinated technical terms often don't need articles
        
        # === DEFINITENESS ANALYSIS ===
        # Check if the noun refers to something specific vs. general
        if self._has_specific_reference(noun_token):
            evidence_score += 0.2  # Specific references usually need 'the'
        elif self._has_generic_reference(noun_token):
            evidence_score += 0.1  # Generic references may need 'a/an'
        
        # === MASS NOUN CONTEXT ===
        # Use existing mass noun context detection
        if self._is_mass_noun_context(noun_token):
            evidence_score -= 0.2  # Mass noun contexts often don't need articles
        
        return evidence_score

    def _apply_structural_clues_missing(self, evidence_score: float, noun_token, context: dict) -> float:
        """Apply document structure-based clues for missing articles."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # === FORMAL WRITING CONTEXTS ===
        # Formal contexts expect complete article usage
        if block_type in ['heading', 'title']:
            evidence_score -= 0.2  # Headings often omit articles for brevity
        elif block_type == 'paragraph':
            evidence_score += 0.1  # Body paragraphs usually need complete grammar
        
        # === TECHNICAL CONTEXTS ===
        # Technical writing often omits articles for conciseness
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.4  # Code comments very abbreviated
        elif block_type == 'inline_code':
            evidence_score -= 0.3  # Inline technical content abbreviated
        
        # === LISTS AND PROCEDURES ===
        # Lists often omit articles for brevity
        if block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.3  # List items commonly abbreviated
            
            # Nested lists even more abbreviated
            if context.get('list_depth', 1) > 1:
                evidence_score -= 0.1
        
        # === TABLES ===
        # Tables use very abbreviated language
        if block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.4  # Tables heavily abbreviated
        
        # === ADMONITIONS ===
        # Admonitions may use abbreviated language
        if block_type == 'admonition':
            evidence_score -= 0.2  # Admonitions often abbreviated
        
        return evidence_score

    def _apply_semantic_clues_missing(self, evidence_score: float, noun_token, text: str, context: dict) -> float:
        """Apply semantic and content-type clues for missing articles."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Technical content often omits articles
        if content_type == 'technical':
            evidence_score -= 0.2  # Technical writing often omits articles
        elif content_type == 'api':
            evidence_score -= 0.3  # API documentation very concise
        elif content_type == 'procedural':
            evidence_score -= 0.2  # Instructions often abbreviated
        elif content_type == 'academic':
            evidence_score += 0.2  # Academic writing expects complete grammar
        elif content_type == 'legal':
            evidence_score += 0.1  # Legal writing fairly complete
        elif content_type == 'marketing':
            evidence_score -= 0.1  # Marketing may be more flexible
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score -= 0.2  # Technical domains omit articles
        elif domain in ['documentation', 'tutorial']:
            evidence_score -= 0.1  # Educational content somewhat abbreviated
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score -= 0.2  # Technical audiences expect abbreviated style
        elif audience in ['academic', 'professional']:
            evidence_score += 0.1  # Professional audiences expect complete grammar
        elif audience in ['beginner', 'general']:
            evidence_score += 0.2  # General audiences need complete grammar
        
        # === CONTENT TYPE SPECIFIC ANALYSIS ===
        # Use helper methods to analyze content type
        if self._is_procedural_documentation(text):
            evidence_score -= 0.3  # Instructions often omit articles for brevity
        elif self._is_reference_documentation(text):
            evidence_score -= 0.2  # Reference docs use abbreviated style
        
        # === TECHNICAL TERM DENSITY ===
        # High technical term density suggests abbreviated style is acceptable
        if self._has_high_technical_density(text):
            evidence_score -= 0.2
        
        return evidence_score

    def _apply_feedback_clues_missing(self, evidence_score: float, noun_token, context: dict) -> float:
        """Apply feedback patterns for missing articles."""
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns('articles')
        
        noun = noun_token.text.lower()
        
        # Check if this noun is commonly used without articles
        no_article_nouns = feedback_patterns.get('commonly_no_article_nouns', set())
        if noun in no_article_nouns:
            evidence_score -= 0.3  # Users consistently accept this without article
        
        # Check if this noun is commonly flagged as missing article
        missing_article_nouns = feedback_patterns.get('commonly_missing_article_nouns', set())
        if noun in missing_article_nouns:
            evidence_score += 0.3  # Users consistently add articles to this
        
        # Check context-specific patterns
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        context_patterns = feedback_patterns.get(f'{block_type}_article_patterns', {})
        
        if noun in context_patterns.get('acceptable_without_article', set()):
            evidence_score -= 0.2
        elif noun in context_patterns.get('needs_article', set()):
            evidence_score += 0.2
        
        return evidence_score

    # === HELPER METHODS ===

    def _has_specific_reference(self, noun_token) -> bool:
        """Check if noun refers to something specific (might need 'the')."""
        # Check for definite reference indicators
        modifiers = [child.text.lower() for child in noun_token.children]
        
        # Demonstratives indicate specific reference
        if any(mod in ['this', 'that', 'these', 'those'] for mod in modifiers):
            return True
        
        # Superlatives indicate specific reference
        if any(child.tag_ in ['JJS', 'RBS'] for child in noun_token.children):
            return True
        
        # Ordinals indicate specific reference
        if any(child.like_num and any(ord_word in child.text.lower() for ord_word in ['first', 'second', 'third', 'last']) for child in noun_token.children):
            return True
        
        return False

    def _has_generic_reference(self, noun_token) -> bool:
        """Check if noun refers to something generic (might need 'a/an')."""
        # Check for generic reference patterns
        if noun_token.dep_ == 'nsubj' and noun_token.head.lemma_ in ['be', 'become', 'seem']:
            return True  # "X is a Y" pattern
        
        # Check for comparison contexts
        if any(child.lemma_ in ['like', 'such', 'similar'] for child in noun_token.ancestors):
            return True
        
        return False

    # Removed _has_high_technical_density - using base class utility

    # Removed _is_procedural_documentation - using base class utility

    # Removed _is_reference_documentation - using base class utility

    def _count_formal_indicators(self, text: str) -> int:
        """Count indicators of formal writing style."""
        formal_indicators = [
            'furthermore', 'moreover', 'consequently', 'therefore', 'nonetheless',
            'nevertheless', 'additionally', 'specifically', 'particularly',
            'respectively', 'accordingly', 'subsequently', 'aforementioned'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in formal_indicators if indicator in text_lower)

    # Removed _get_cached_feedback_patterns - using base class utility

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_message_incorrect(self, article_token, next_token, evidence_score: float) -> str:
        """Generate context-aware error messages for incorrect a/an usage."""
        
        correct_article = 'an' if self._starts_with_vowel_sound(next_token.text) else 'a'
        
        if evidence_score > 0.8:
            return f"Incorrect article: Use '{correct_article}' before '{next_token.text}' (phonetic rule)."
        elif evidence_score > 0.5:
            return f"Consider using '{correct_article}' before '{next_token.text}' for standard pronunciation."
        else:
            return f"Article usage: '{correct_article}' is typically used before '{next_token.text}'."

    def _get_contextual_message_missing(self, noun_token, evidence_score: float) -> str:
        """Generate context-aware error messages for missing articles."""
        
        if evidence_score > 0.8:
            return f"Missing article: Singular noun '{noun_token.text}' typically requires an article (a/an/the)."
        elif evidence_score > 0.5:
            return f"Consider adding an article before '{noun_token.text}' for clarity."
        else:
            return f"Article usage: '{noun_token.text}' might benefit from an article depending on context."

    def _generate_smart_suggestions_incorrect(self, article_token, next_token, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions for incorrect a/an usage."""
        
        suggestions = []
        correct_article = 'an' if self._starts_with_vowel_sound(next_token.text) else 'a'
        
        # Base correction
        suggestions.append(f"Change '{article_token.text} {next_token.text}' to '{correct_article} {next_token.text}'.")
        
        # Explanation based on evidence
        if evidence_score > 0.7:
            suggestions.append(f"'{next_token.text}' starts with a {'vowel' if self._starts_with_vowel_sound(next_token.text) else 'consonant'} sound, requiring '{correct_article}'.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            if content_type in ['academic', 'legal', 'professional']:
                suggestions.append("Correct article usage is important in formal writing.")
            elif content_type == 'technical':
                suggestions.append("While technical writing is concise, article accuracy aids readability.")
        
        return suggestions

    def _generate_smart_suggestions_missing(self, noun_token, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions for missing articles."""
        
        suggestions = []
        
        # Base suggestion
        if self._has_specific_reference(noun_token):
            suggestions.append(f"Consider adding 'the' before '{noun_token.text}' for specific reference.")
        else:
            suggestions.append(f"Consider adding 'a/an/the' before '{noun_token.text}' as appropriate.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            block_type = context.get('block_type', 'paragraph')
            
            if content_type == 'technical' and block_type in ['ordered_list_item', 'unordered_list_item']:
                suggestions.append("Technical lists often omit articles, but consider your style guide.")
            elif content_type in ['academic', 'formal']:
                suggestions.append("Formal writing typically includes articles for completeness.")
            elif content_type == 'procedural':
                suggestions.append("Instructions may omit articles for brevity, but clarity is important.")
        
        # Evidence-based advice
        if evidence_score < 0.3:
            suggestions.append("This usage may be acceptable in your context, depending on style preferences.")
        elif evidence_score > 0.7:
            suggestions.append("Adding an article would improve grammatical completeness.")
        
        return suggestions
