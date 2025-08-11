"""
Inclusive Language Rule
Based on IBM Style Guide topic: "Inclusive language"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class InclusiveLanguageRule(BaseLanguageRule):
    """
    Checks for non-inclusive terms and suggests modern, neutral alternatives
    as specified by the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        return 'inclusive_language'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for non-inclusive language.
        Calculates nuanced evidence scores for each detected issue using
        linguistic, structural, semantic, and feedback clues.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)

        # Find all potential issues first
        potential_issues = self._find_potential_issues(doc, text)
        
        for potential_issue in potential_issues:
            # Calculate nuanced evidence score
            evidence_score = self._calculate_inclusive_language_evidence(
                potential_issue, doc, text, context or {}
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                errors.append(self._create_error(
                    sentence=potential_issue['sentence'].text,
                    sentence_index=potential_issue['sentence_index'],
                    message=self._get_contextual_inclusive_message(potential_issue, evidence_score),
                    suggestions=self._generate_smart_inclusive_suggestions(potential_issue, evidence_score, context or {}),
                    severity=potential_issue.get('severity', 'medium'),
                    text=text,
                    context=context,
                    evidence_score=evidence_score,  # Your nuanced assessment
                    span=potential_issue['span'],
                    flagged_text=potential_issue['flagged_text']
                ))
        
        return errors

    def _find_potential_issues(self, doc, text: str) -> List[Dict[str, Any]]:
        """Find all potential non-inclusive language issues in the document."""
        potential_issues = []
        
        # Enhanced non-inclusive terms with categorization for better evidence scoring
        non_inclusive_terms = self._get_non_inclusive_terms_categorized()

        for i, sent in enumerate(doc.sents):
            for term_info in non_inclusive_terms:
                term = term_info['term']
                for match in re.finditer(r'\b' + re.escape(term) + r'\b', sent.text, re.IGNORECASE):
                    potential_issues.append({
                        'type': 'non_inclusive_term',
                        'match': match,
                        'term_info': term_info,
                        'sentence': sent,
                        'sentence_index': i,
                        'span': (sent.start_char + match.start(), sent.start_char + match.end()),
                        'flagged_text': match.group(0),
                        'matched_term': match.group(),
                        'severity': term_info.get('severity_level', 'medium')
                    })
        
        return potential_issues

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _get_non_inclusive_terms_categorized(self) -> List[Dict[str, Any]]:
        """Get categorized non-inclusive terms for better evidence scoring."""
        return [
            # Technical terms (often have legacy system justifications)
            {
                'term': 'whitelist',
                'replacement': 'allowlist',
                'category': 'technical',
                'severity_level': 'medium',
                'description': 'access control terminology'
            },
            {
                'term': 'blacklist',
                'replacement': 'blocklist',
                'category': 'technical',
                'severity_level': 'medium',
                'description': 'access control terminology'
            },
            {
                'term': 'master',
                'replacement': 'primary, main, or controller',
                'category': 'technical',
                'severity_level': 'high',
                'description': 'hierarchical system terminology'
            },
            {
                'term': 'slave',
                'replacement': 'secondary, replica, or agent',
                'category': 'technical',
                'severity_level': 'high',
                'description': 'hierarchical system terminology'
            },
            # Gendered language (often easier to change)
            {
                'term': 'man-hours',
                'replacement': 'person-hours or work-hours',
                'category': 'gendered',
                'severity_level': 'medium',
                'description': 'gendered work measurement'
            },
            {
                'term': 'man hours',
                'replacement': 'person-hours or work-hours',
                'category': 'gendered',
                'severity_level': 'medium',
                'description': 'gendered work measurement'
            },
            {
                'term': 'manned',
                'replacement': 'staffed, operated, or crewed',
                'category': 'gendered',
                'severity_level': 'medium',
                'description': 'gendered operation terminology'
            },
            # Ableist language (often unconscious usage)
            {
                'term': 'sanity check',
                'replacement': 'coherence check, confirmation, or validation',
                'category': 'ableist',
                'severity_level': 'medium',
                'description': 'mental health terminology'
            }
        ]

    def _calculate_inclusive_language_evidence(self, potential_issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for non-inclusive language concerns.
        
        Higher scores indicate stronger evidence that the term should be flagged.
        Lower scores indicate acceptable usage in specific contexts (legacy references, quotes, etc.).
        
        Args:
            potential_issue: Dictionary containing issue details
            doc: SpaCy document
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable usage) to 1.0 (should be flagged)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_inclusive_language_evidence(potential_issue)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this term
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_inclusive(evidence_score, potential_issue, doc)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_inclusive(evidence_score, potential_issue, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_inclusive(evidence_score, potential_issue, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_inclusive(evidence_score, potential_issue, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _get_base_inclusive_language_evidence(self, potential_issue: Dict[str, Any]) -> float:
        """Get base evidence score based on term category and severity."""
        
        term_info = potential_issue['term_info']
        category = term_info.get('category', 'unknown')
        severity_level = term_info.get('severity_level', 'medium')
        
        # === BASE EVIDENCE BY CATEGORY ===
        # Technical terms often have legacy justifications
        if category == 'technical':
            if severity_level == 'high':
                return 0.7  # High severity technical terms (master/slave)
            else:
                return 0.6  # Medium severity technical terms (whitelist/blacklist)
        
        # Gendered language often clear to change
        elif category == 'gendered':
            return 0.8  # Generally high evidence for gendered language
        
        # Ableist language varies by context
        elif category == 'ableist':
            return 0.7  # High evidence but context-dependent
        
        # Unknown categories default to moderate evidence
        else:
            return 0.6  # Default moderate evidence

    # === LINGUISTIC CLUES FOR INCLUSIVE LANGUAGE ===

    def _apply_linguistic_clues_inclusive(self, evidence_score: float, potential_issue: Dict[str, Any], doc) -> float:
        """Apply linguistic analysis clues for inclusive language detection."""
        
        match = potential_issue['match']
        sentence = potential_issue['sentence']
        matched_text = match.group().lower()
        sentence_text = sentence.text.lower()
        
        # === SPACY TOKEN ANALYSIS ===
        # Find the SpaCy token(s) corresponding to the matched text
        matched_tokens = self._find_matching_tokens(match, sentence, doc)
        
        if matched_tokens:
            for token in matched_tokens:
                # === PART-OF-SPEECH ANALYSIS ===
                if hasattr(token, 'pos_') and token.pos_:
                    # Nouns are more likely to be problematic non-inclusive terms
                    if token.pos_ in ['NOUN', 'PROPN']:
                        evidence_score += 0.1  # Nouns often represent concepts to change
                    # Adjectives may be descriptive and context-dependent
                    elif token.pos_ == 'ADJ':
                        evidence_score += 0.05  # Adjectives may have neutral alternatives
                    # Verbs in past tense might indicate established practices
                    elif token.pos_ == 'VERB':
                        evidence_score += 0.02  # Verbal usage patterns
                
                # === DEPENDENCY PARSING ===
                if hasattr(token, 'dep_') and token.dep_:
                    # Subjects and objects are more central to meaning
                    if token.dep_ in ['nsubj', 'nsubjpass', 'dobj', 'pobj']:
                        evidence_score += 0.1  # Central grammatical roles
                    # Compound words often technical terms
                    elif token.dep_ == 'compound':
                        evidence_score -= 0.1  # Technical compounds may be legacy
                    # Attributes and modifiers may be easier to change
                    elif token.dep_ in ['amod', 'nmod', 'advmod']:
                        evidence_score += 0.05  # Modifiers often changeable
                
                # === PENN TREEBANK TAG ANALYSIS ===
                if hasattr(token, 'tag_') and token.tag_:
                    # Plural nouns might indicate established systems
                    if token.tag_ in ['NNS', 'NNPS']:
                        evidence_score -= 0.05  # Plural forms often systematic
                    # Singular proper nouns might be product/system names
                    elif token.tag_ == 'NNP':
                        evidence_score -= 0.1  # Proper nouns often legacy systems
                    # Past participles might indicate established processes
                    elif token.tag_ in ['VBN', 'VBD']:
                        evidence_score -= 0.03  # Past forms suggest established usage
                
                # === NAMED ENTITY RECOGNITION ===
                if hasattr(token, 'ent_type_') and token.ent_type_:
                    ent_type = token.ent_type_
                    # Organizations and products often have established names
                    if ent_type in ['ORG', 'PRODUCT', 'FAC']:
                        evidence_score -= 0.2  # Organizational terms harder to change
                    # Person names rarely non-inclusive (different context)
                    elif ent_type == 'PERSON':
                        evidence_score -= 0.1  # Person names different category
                    # Technical entities might be system names
                    elif ent_type in ['GPE', 'EVENT']:
                        evidence_score -= 0.05  # Geographic/event entities
                
                # === LEMMA ANALYSIS ===
                if hasattr(token, 'lemma_') and token.lemma_:
                    lemma_lower = token.lemma_.lower()
                    # Check if lemma is in our non-inclusive terms
                    term_info = potential_issue['term_info']
                    base_term = term_info.get('term', '').lower()
                    
                    if lemma_lower == base_term:
                        evidence_score += 0.1  # Lemma matches our target term
                    
                    # Technical verb lemmas
                    if lemma_lower in ['configure', 'implement', 'deploy', 'manage', 'control']:
                        evidence_score -= 0.05  # Technical action verbs
                    
                    # Administrative lemmas
                    elif lemma_lower in ['administer', 'supervise', 'oversee', 'govern']:
                        evidence_score += 0.05  # Administrative terms often changeable
                
                # === MORPHOLOGICAL FEATURES ===
                if hasattr(token, 'morph') and token.morph:
                    morph_str = str(token.morph)
                    
                    # Plural forms might indicate systematic usage
                    if 'Number=Plur' in morph_str:
                        evidence_score -= 0.03  # Plural suggests system-wide usage
                    
                    # Past tense might indicate established processes
                    if 'Tense=Past' in morph_str:
                        evidence_score -= 0.02  # Past tense suggests established usage
                    
                    # Definite articles suggest specific references
                    if 'Definite=Def' in morph_str:
                        evidence_score -= 0.02  # Definite references to specific systems
        
        # === QUOTATION CONTEXT ANALYSIS ===
        # Terms in quotes often reference external sources
        if self._is_in_quotation_context(match, sentence):
            evidence_score -= 0.4  # Quotes often preserve original language
        
        # === LEGACY REFERENCE INDICATORS ===
        # Look for words that indicate legacy system references
        legacy_indicators = [
            'legacy', 'existing', 'current', 'old', 'previous', 'deprecated',
            'historical', 'traditional', 'original', 'inherited', 'migrating from'
        ]
        
        if any(indicator in sentence_text for indicator in legacy_indicators):
            evidence_score -= 0.3  # Legacy references more acceptable
        
        # === TECHNICAL SPECIFICATION CONTEXT ===
        # Look for technical specification language
        spec_indicators = [
            'api', 'endpoint', 'database', 'field', 'column', 'table',
            'configuration', 'config', 'parameter', 'variable', 'function',
            'method', 'class', 'interface', 'protocol'
        ]
        
        if any(indicator in sentence_text for indicator in spec_indicators):
            evidence_score -= 0.2  # Technical specs may use legacy terms
        
        # === EXPLANATION/EDUCATIONAL CONTEXT ===
        # Look for explanatory language about terminology
        explanation_indicators = [
            'formerly', 'previously called', 'also known as', 'traditionally',
            'used to be called', 'historically referred to', 'sometimes called',
            'older term', 'legacy term', 'deprecated term'
        ]
        
        if any(indicator in sentence_text for indicator in explanation_indicators):
            evidence_score -= 0.5  # Educational content about terminology
        
        # === REPLACEMENT CONTEXT ===
        # Look for language indicating the term is being replaced
        replacement_indicators = [
            'replace', 'instead of', 'rather than', 'substitute',
            'alternative to', 'preferred over', 'better than', 'use.*instead'
        ]
        
        if any(re.search(indicator, sentence_text) for indicator in replacement_indicators):
            evidence_score -= 0.3  # Discussion of replacement
        
        # === NEGATION CONTEXT ===
        # Look for negation around the term
        negation_indicators = [
            'not', 'no longer', 'avoid', "don't use", "shouldn't use",
            'stop using', 'eliminate', 'remove', 'phase out'
        ]
        
        if any(indicator in sentence_text for indicator in negation_indicators):
            evidence_score -= 0.4  # Discussing not using the term
        
        # === IMPERATIVE/DIRECTIVE CONTEXT ===
        # New content creating directives using non-inclusive terms
        directive_indicators = [
            'create', 'add', 'implement', 'build', 'develop', 'design',
            'establish', 'set up', 'configure', 'install', 'deploy'
        ]
        
        if any(indicator in sentence_text for indicator in directive_indicators):
            evidence_score += 0.2  # New creation using non-inclusive terms
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_structural_clues_inclusive(self, evidence_score: float, potential_issue: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for inclusive language detection."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # === DOCUMENTATION CONTEXTS ===
        # Migration guides and legacy documentation
        if block_type in ['heading', 'title']:
            heading_text = context.get('heading_text', '').lower()
            if any(term in heading_text for term in ['migration', 'legacy', 'deprecated', 'historical']):
                evidence_score -= 0.3  # Migration/legacy documentation
            else:
                evidence_score += 0.1  # New headings should use inclusive language
        
        # === TECHNICAL CONTEXTS ===
        # Code blocks and technical content
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.3  # Code may reference legacy APIs/systems
        elif block_type == 'inline_code':
            evidence_score -= 0.2  # Inline code references
        
        # === LISTS AND PROCEDURES ===
        # Lists often contain legacy system references
        if block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.1  # Lists may document existing systems
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.1  # Tables may list legacy systems
        
        # === QUOTES AND CITATIONS ===
        # Quoted material preserves original language
        if block_type in ['block_quote', 'citation']:
            evidence_score -= 0.5  # Quotes preserve historical language
        elif block_type in ['example', 'sample']:
            evidence_score -= 0.2  # Examples may show legacy usage
        
        # === ADMONITIONS ===
        # Notes and warnings about legacy systems
        if block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'WARNING', 'CAUTION']:
                evidence_score -= 0.2  # Often discuss legacy systems
            elif admonition_type in ['IMPORTANT', 'TIP']:
                evidence_score += 0.0  # Neutral adjustment
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_semantic_clues_inclusive(self, evidence_score: float, potential_issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for inclusive language detection."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Different content types have different inclusion expectations
        if content_type == 'technical':
            evidence_score -= 0.2  # Technical content may reference legacy systems
        elif content_type == 'api':
            evidence_score -= 0.3  # API docs often reference existing endpoints
        elif content_type == 'academic':
            evidence_score += 0.2  # Academic writing should use inclusive language
        elif content_type == 'legal':
            evidence_score -= 0.1  # Legal docs may reference existing contracts/systems
        elif content_type == 'marketing':
            evidence_score += 0.3  # Marketing should definitely use inclusive language
        elif content_type == 'narrative':
            evidence_score += 0.1  # Narrative writing should be inclusive
        elif content_type == 'procedural':
            evidence_score -= 0.1  # Procedures may reference legacy systems
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score -= 0.2  # Technical domains have more legacy systems
        elif domain in ['documentation', 'tutorial']:
            evidence_score += 0.1  # Educational content should be inclusive
        elif domain in ['academic', 'research']:
            evidence_score += 0.2  # Academic domains expect inclusive language
        elif domain in ['legacy', 'migration', 'maintenance']:
            evidence_score -= 0.3  # Legacy domains often reference old systems
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score -= 0.1  # Technical audiences understand legacy references
        elif audience in ['academic', 'research']:
            evidence_score += 0.2  # Academic audiences expect inclusive language
        elif audience in ['beginner', 'general', 'consumer']:
            evidence_score += 0.2  # General audiences should see inclusive language
        elif audience in ['professional', 'business']:
            evidence_score += 0.1  # Professional contexts expect inclusivity
        
        # === DOCUMENT PURPOSE ANALYSIS ===
        # Analyze document for migration, legacy, or historical content
        if self._is_migration_documentation(text):
            evidence_score -= 0.3  # Migration docs reference legacy systems
        
        if self._is_historical_documentation(text):
            evidence_score -= 0.2  # Historical docs may preserve original language
        
        if self._is_new_development_content(text):
            evidence_score += 0.2  # New development should use inclusive language
        
        # === TERM CATEGORY IN CONTEXT ===
        term_info = potential_issue['term_info']
        category = term_info.get('category', 'unknown')
        
        # Technical terms in non-technical content more problematic
        if category == 'technical' and content_type not in ['technical', 'api']:
            evidence_score += 0.2  # Technical terms in general content
        
        # Gendered language particularly problematic in professional contexts
        if category == 'gendered' and content_type in ['marketing', 'academic']:
            evidence_score += 0.2  # Gendered language in professional contexts
        
        # === SYSTEM ARCHITECTURE CONTEXT ===
        # Architecture docs often reference established patterns with legacy terminology
        if self._is_system_architecture_context(text, context):
            evidence_score -= 0.3  # Architecture docs may need legacy term references
            
            # But still flag new architecture designs
            if self._is_new_development_content(text):
                evidence_score += 0.2  # New designs should use inclusive language
        
        # === COMPLIANCE DOCUMENTATION CONTEXT ===
        # Compliance docs may be constrained by legal/regulatory requirements
        if self._is_compliance_documentation_context(text, context):
            evidence_score -= 0.2  # Compliance docs may have regulatory constraints
            
            # But internal policies should still be inclusive
            if content_type in ['policy', 'procedure'] and 'internal' in text.lower():
                evidence_score += 0.1  # Internal policies can be more inclusive
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_feedback_clues_inclusive(self, evidence_score: float, potential_issue: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Apply feedback patterns for inclusive language detection."""
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns('inclusive_language')
        
        # === TERM-SPECIFIC FEEDBACK ===
        match = potential_issue['match']
        term_info = potential_issue['term_info']
        term = match.group().lower()
        category = term_info.get('category', 'unknown')
        
        # Check if this specific term is commonly accepted in certain contexts
        accepted_terms = feedback_patterns.get('accepted_legacy_terms', set())
        if term in accepted_terms:
            evidence_score -= 0.3  # Users consistently accept this term in legacy contexts
        
        flagged_terms = feedback_patterns.get('flagged_terms', set())
        if term in flagged_terms:
            evidence_score += 0.3  # Users consistently flag this term
        
        # === CATEGORY-SPECIFIC FEEDBACK ===
        category_patterns = feedback_patterns.get('category_patterns', {})
        
        if category == 'technical':
            technical_acceptance = category_patterns.get('technical_acceptance_rate', 0.4)
            if technical_acceptance > 0.7:
                evidence_score -= 0.2  # High acceptance for technical terms
            elif technical_acceptance < 0.3:
                evidence_score += 0.2  # Low acceptance for technical terms
        
        elif category == 'gendered':
            gendered_acceptance = category_patterns.get('gendered_acceptance_rate', 0.2)
            if gendered_acceptance > 0.5:
                evidence_score -= 0.1  # Some acceptance for gendered terms
            elif gendered_acceptance < 0.2:
                evidence_score += 0.2  # Very low acceptance for gendered terms
        
        elif category == 'ableist':
            ableist_acceptance = category_patterns.get('ableist_acceptance_rate', 0.3)
            if ableist_acceptance > 0.6:
                evidence_score -= 0.1  # Some acceptance for ableist terms
            elif ableist_acceptance < 0.2:
                evidence_score += 0.2  # Very low acceptance for ableist terms
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        if context:
            content_type = context.get('content_type', 'general')
            context_patterns = feedback_patterns.get(f'{content_type}_inclusive_patterns', {})
            
            if term in context_patterns.get('acceptable', set()):
                evidence_score -= 0.2
            elif term in context_patterns.get('problematic', set()):
                evidence_score += 0.2
        
        # === REPLACEMENT SUCCESS PATTERNS ===
        # Terms that users successfully replace vs. consistently ignore
        replacement_patterns = feedback_patterns.get('replacement_success', {})
        replacement_rate = replacement_patterns.get(term, 0.5)
        
        if replacement_rate > 0.8:
            evidence_score += 0.1  # Users successfully replace this term
        elif replacement_rate < 0.2:
            evidence_score -= 0.2  # Users consistently ignore suggestions for this term
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===

    def _is_in_quotation_context(self, match, sentence) -> bool:
        """Check if the matched term is within quotation marks."""
        sentence_text = sentence.text
        match_start = match.start()
        match_end = match.end()
        
        # Look for quotes before and after the match
        before_match = sentence_text[:match_start]
        after_match = sentence_text[match_end:]
        
        # Check for various quote types
        quote_chars = ['"', "'", '"', '"', ''', ''', '`']
        
        # Count quotes before and after
        for quote_char in quote_chars:
            quotes_before = before_match.count(quote_char)
            quotes_after = after_match.count(quote_char)
            
            # If odd number of quotes before and after, likely inside quotes
            if quotes_before % 2 == 1 and quotes_after % 2 == 1:
                return True
        
        return False



    def _is_historical_documentation(self, text: str) -> bool:
        """Check if text appears to be historical documentation."""
        historical_indicators = [
            'historically', 'traditionally', 'in the past', 'previously',
            'originally', 'initially', 'used to be', 'was formerly',
            'history of', 'evolution of', 'development of', 'background'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in historical_indicators)

    def _is_new_development_content(self, text: str) -> bool:
        """Check if text appears to be about new development."""
        new_development_indicators = [
            'new', 'creating', 'building', 'developing', 'implementing',
            'designing', 'future', 'upcoming', 'planned', 'proposal',
            'specification', 'requirements', 'best practices', 'guidelines'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in new_development_indicators)

    def _find_matching_tokens(self, match, sentence, doc):
        """Find SpaCy tokens that correspond to the regex match."""
        matched_tokens = []
        match_start = match.start()
        match_end = match.end()
        
        # Find tokens that overlap with the match span
        for token in sentence:
            token_start = token.idx - sentence.start_char
            token_end = token_start + len(token.text)
            
            # Check if token overlaps with match
            if (token_start < match_end and token_end > match_start):
                matched_tokens.append(token)
        
        return matched_tokens

    def _is_system_architecture_context(self, text: str, context: dict) -> bool:
        """
        Detect if content is system architecture documentation.
        
        System architecture docs often reference established patterns and
        legacy system designs that may use non-inclusive terminology.
        
        Args:
            text: Document text
            context: Document context
            
        Returns:
            bool: True if system architecture context detected
        """
        architecture_indicators = {
            'architecture', 'design', 'blueprint', 'schema', 'framework',
            'infrastructure', 'topology', 'hierarchy', 'component', 'module',
            'service', 'microservice', 'distributed', 'scalable', 'pattern',
            'client-server', 'master-slave', 'producer-consumer', 'pipeline'
        }
        
        text_lower = text.lower()
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        
        # Direct text indicators
        arch_score = sum(1 for indicator in architecture_indicators if indicator in text_lower)
        
        # Context-based indicators
        if domain in {'architecture', 'infrastructure', 'systems', 'platform'}:
            arch_score += 2
        
        if content_type in {'technical', 'specification', 'design', 'architecture'}:
            arch_score += 2
        
        # Check for architecture patterns in text
        architecture_patterns = [
            'system design', 'distributed system', 'service architecture',
            'data flow', 'component diagram', 'system topology',
            'master node', 'slave node', 'control plane'
        ]
        
        pattern_matches = sum(1 for pattern in architecture_patterns if pattern in text_lower)
        arch_score += pattern_matches
        
        # Threshold for architecture context detection
        return arch_score >= 3

    def _is_compliance_documentation_context(self, text: str, context: dict) -> bool:
        """
        Detect if content is compliance or regulatory documentation.
        
        Compliance docs often reference specific legal or regulatory
        terminology that may be difficult to change due to legal requirements.
        
        Args:
            text: Document text
            context: Document context
            
        Returns:
            bool: True if compliance documentation context detected
        """
        compliance_indicators = {
            'compliance', 'regulation', 'regulatory', 'legal', 'audit',
            'policy', 'procedure', 'standard', 'certification', 'requirement',
            'mandate', 'directive', 'guideline', 'framework', 'governance',
            'sox', 'gdpr', 'hipaa', 'pci', 'iso', 'cmmi'
        }
        
        text_lower = text.lower()
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        audience = context.get('audience', '')
        
        # Direct text indicators
        compliance_score = sum(1 for indicator in compliance_indicators if indicator in text_lower)
        
        # Context-based indicators
        if domain in {'legal', 'compliance', 'regulatory', 'governance', 'audit'}:
            compliance_score += 2
        
        if content_type in {'legal', 'compliance', 'policy', 'procedure', 'regulatory'}:
            compliance_score += 2
            
        if audience in {'auditor', 'compliance', 'legal', 'regulatory', 'governance'}:
            compliance_score += 2
        
        # Check for compliance-specific patterns
        compliance_patterns = [
            'regulatory requirement', 'compliance standard', 'audit requirement',
            'legal mandate', 'regulatory framework', 'compliance policy',
            'industry standard', 'certification requirement'
        ]
        
        pattern_matches = sum(1 for pattern in compliance_patterns if pattern in text_lower)
        compliance_score += pattern_matches
        
        # Legal language patterns
        legal_patterns = [
            'shall be', 'must be', 'is required to', 'in accordance with',
            'pursuant to', 'subject to', 'notwithstanding', 'whereas'
        ]
        
        legal_matches = sum(1 for pattern in legal_patterns if pattern in text_lower)
        compliance_score += legal_matches
        
        # Threshold for compliance context detection
        return compliance_score >= 4



    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_inclusive_message(self, potential_issue: Dict[str, Any], evidence_score: float) -> str:
        """Generate context-aware error messages for inclusive language patterns."""
        matched_term = potential_issue['matched_term']
        term_info = potential_issue['term_info']
        return self._get_contextual_message(matched_term, term_info, evidence_score)

    def _generate_smart_inclusive_suggestions(self, potential_issue: Dict[str, Any], evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for inclusive language patterns."""
        matched_term = potential_issue['matched_term']
        term_info = potential_issue['term_info']
        return self._generate_smart_suggestions(matched_term, term_info, evidence_score, context)

    def _get_contextual_message(self, matched_term: str, term_info: dict, evidence_score: float) -> str:
        """Generate context-aware error messages for inclusive language."""
        
        category = term_info.get('category', 'unknown')
        description = term_info.get('description', 'term')
        
        if evidence_score > 0.8:
            return f"Non-inclusive {description} found: '{matched_term}'. Consider using more inclusive language."
        elif evidence_score > 0.5:
            return f"Potentially non-inclusive {description}: '{matched_term}'. Verify appropriateness for your context."
        else:
            return f"Non-inclusive {description} noted: '{matched_term}'. May be acceptable in legacy/technical contexts."

    def _generate_smart_suggestions(self, matched_term: str, term_info: dict, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions for inclusive language."""
        
        suggestions = []
        replacement = term_info.get('replacement', 'a more inclusive alternative')
        category = term_info.get('category', 'unknown')
        
        # Base suggestions based on evidence strength
        if evidence_score > 0.7:
            suggestions.append(f"Use a more inclusive alternative: {replacement}.")
        else:
            suggestions.append(f"Consider using: {replacement}.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type in ['technical', 'api'] and category == 'technical':
                suggestions.append("If referencing legacy systems, consider adding context (e.g., 'legacy master branch').")
            elif content_type in ['marketing', 'academic']:
                suggestions.append("Use inclusive language to ensure accessibility for all audiences.")
            elif content_type == 'migration':
                suggestions.append("For migration docs, clarify when discussing old vs. new terminology.")
        
        # Category-specific advice
        if category == 'technical':
            suggestions.append("Many technical systems are adopting more inclusive terminology.")
        elif category == 'gendered':
            suggestions.append("Gender-neutral language is more inclusive and professional.")
        elif category == 'ableist':
            suggestions.append("Consider language that doesn't reference mental health or disability.")
        
        # Evidence-based advice
        if evidence_score < 0.3:
            suggestions.append("This may be acceptable if referencing existing systems or in quotes.")
        elif evidence_score > 0.8:
            suggestions.append("Strong recommendation to use inclusive language in this context.")
        
        return suggestions
