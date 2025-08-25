"""
Product and Service Names Rule
Based on IBM Style Guide topic: "Product and service names"
"""
from typing import List, Dict, Any
from .base_references_rule import BaseReferencesRule
from .services.references_config_service import get_product_config, ReferenceContext

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ProductNamesRule(BaseReferencesRule):
    """
    Checks for correct usage of product names, focusing on the requirement
    to include 'IBM' on the first mention.
    """
    def __init__(self):
        super().__init__()
        self.config_service = get_product_config()
    
    def _get_rule_type(self) -> str:
        return 'references_product_names'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for product naming violations using evidence-based approach.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        known_products = {}  # Track first mention of products

        for i, sent in enumerate(doc.sents):
            # Check both named entities and manual product detection
            product_candidates = self._find_product_candidates(sent, doc)
            
            for ent in product_candidates:
                product_name = ent.text
                
                # CONTEXT FILTER: Skip UI elements and common false positives using config
                if self._is_ui_element_or_false_positive_config(ent, doc):
                    continue
                
                # Skip competitor products - check both full name and individual words
                if self._is_competitor_product(product_name):
                    continue
                
                # Rule: First reference must be preceded by "IBM".
                if product_name not in known_products:
                    known_products[product_name] = True
                    
                    # Check if the entity is preceded by "IBM".
                    if not self._has_ibm_prefix(ent, doc):
                        evidence_score = self._calculate_product_name_evidence(
                            ent, sent, text, context
                        )
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_message_product(product_name, evidence_score),
                                suggestions=self._generate_smart_suggestions_product(product_name, context, evidence_score),
                                severity='high',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(ent.start_char, ent.end_char),
                                flagged_text=ent.text
                            ))
        return errors
    
    def _calculate_product_name_evidence(self, entity, sentence, text: str, context: Dict[str, Any] = None) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential product naming violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            entity: The product entity/phrase
            sentence: Sentence containing the entity
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        first_token = list(entity)[0] if entity else None
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return 0.0  # Code has its own rules
        
        # Don't flag technical identifiers, URLs, file paths
        if hasattr(first_token, 'like_url') and first_token.like_url:
            return 0.0
        if hasattr(first_token, 'text') and ('/' in first_token.text or '\\' in first_token.text):
            return 0.0
        
        # Product-specific guards: Don't flag quoted examples
        if self._is_product_in_actual_quotes(entity, sentence, context):
            return 0.0  # Quoted examples are not product naming errors
        
        # Don't flag products that are part of third-party names or brands
        if self._is_product_part_of_third_party_brand(entity, sentence):
            return 0.0  # Non-IBM products, competitor names
        
        # Don't flag UI elements and common false positives
        if self._is_ui_element_or_false_positive(entity, sentence.doc):
            return 0.0  # UI elements are not product naming errors
        
        # Don't flag products in citation or reference context
        if self._is_product_in_citation_context(entity, sentence, context):
            return 0.0  # Academic papers, industry reports, etc.
        
        # Apply inherited zero false positive guards
        if self._apply_zero_false_positive_guards_references(first_token, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_product_name_base_evidence_score(entity, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this entity
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_references(evidence_score, first_token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_references(evidence_score, first_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_references(evidence_score, first_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_products(evidence_score, entity, context)
        
        # Product name-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.1  # Product naming is important but context-dependent
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_product_name_base_evidence_score(self, entity, sentence, context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Well-known IBM products like "Watson" → 0.7 (very specific)
        - Proper product format like "Cloud Platform" → 0.6 (moderate specificity)
        - Generic terms like "Server" → 0.5 (needs context analysis)
        """
        if not entity:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_product_violation(entity):
            return 0.7  # Very specific, clear violation (reduced from 0.9)
        elif self._is_pattern_product_violation(entity):
            return 0.6  # Pattern-based, moderate specificity (reduced from 0.8)
        elif self._is_minor_product_issue(entity):
            return 0.5  # Minor issue, needs context (reduced from 0.7)
        else:
            return 0.4  # Possible issue, needs more evidence (reduced from 0.6)
    
    def _get_contextual_message_product(self, product_name: str, evidence_score: float) -> str:
        """
        Generate contextual error message based on evidence strength.
        """
        if evidence_score > 0.85:
            return f"The first mention of a product, '{product_name}', should be preceded by 'IBM'."
        elif evidence_score > 0.6:
            return f"Consider preceding the first mention of '{product_name}' with 'IBM'."
        else:
            return f"Product name '{product_name}' may need 'IBM' prefix on first mention."
    
    def _generate_smart_suggestions_product(self, product_name: str, context: Dict[str, Any] = None, evidence_score: float = 0.5) -> List[str]:
        """
        Generate evidence-aware suggestions for product naming issues.
        """
        suggestions = []
        
        if evidence_score > 0.8:
            suggestions.append(f"Use the full name 'IBM {product_name}' for the first reference.")
            suggestions.append("Always include 'IBM' with product names on first mention.")
        elif evidence_score > 0.6:
            suggestions.append(f"Consider using 'IBM {product_name}' for the first reference.")
            suggestions.append("Product names typically need 'IBM' prefix initially.")
        else:
            suggestions.append(f"Review product naming: 'IBM {product_name}'.")
        
        return suggestions[:3]
    
    def _is_ui_element_or_false_positive_config(self, entity, doc):
        """
        Configuration-based UI element detection using config service.
        """
        # Check if any part of the entity is a UI element
        for token in entity:
            if self.config_service.is_ui_element(token.text):
                return True
            
            # Check syntactic children (compounds, modifiers)
            for child in token.children:
                if self.config_service.is_ui_element(child.lemma_):
                    return True
            
            # Check syntactic head (what this token modifies)
            if hasattr(token, 'head') and self.config_service.is_ui_element(token.head.lemma_):
                return True
        
        # Check for UI action verbs from configuration
        ui_actions = self.config_service._config.get('ui_elements', {}).get('action_verbs', [])
        sent = entity.sent
        for token in sent:
            if (token.pos_ == 'VERB' and 
                token.lemma_.lower() in ui_actions and
                any(child == entity[0] for child in token.children if child.dep_ in ['dobj', 'pobj'])):
                return True
        
        return False
    
    def _is_ui_element_or_false_positive(self, entity, doc):
        """
        Legacy method - delegates to configuration-based method.
        """
        return self._is_ui_element_or_false_positive_config(entity, doc)
    
    def _is_competitor_product(self, product_name: str) -> bool:
        """Check if product is from a competitor company using configuration."""
        if not product_name:
            return False
        
        product_lower = product_name.lower()
        
        # Check if full name is a competitor
        if self.config_service.is_competitor_company(product_lower):
            return True
        
        # Check if any word in the product name is a competitor
        words = product_lower.split()
        for word in words:
            if self.config_service.is_competitor_company(word):
                return True
        
        # Check for known competitor product patterns
        competitor_patterns = [
            'microsoft', 'google', 'amazon', 'oracle', 'azure', 'aws', 'gcp'
        ]
        
        for pattern in competitor_patterns:
            if pattern in product_lower:
                return True
        
        return False
    
    def _is_product_in_actual_quotes(self, entity, sentence, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the product actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not hasattr(entity, 'text') or not hasattr(sentence, 'text'):
            return False
        
        product = entity.text
        sent_text = sentence.text
        
        # Look for quote pairs that actually enclose the product
        import re
        
        # Find all potential quote pairs
        quote_patterns = [
            (r'"([^"]*)"', '"'),  # Double quotes
            (r"'([^']*)'", "'"),  # Single quotes
            (r'`([^`]*)`', '`')   # Backticks
        ]
        
        for pattern, quote_char in quote_patterns:
            matches = re.finditer(pattern, sent_text)
            for match in matches:
                quoted_content = match.group(1)
                if product.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_product_part_of_third_party_brand(self, entity, sentence) -> bool:
        """
        Check if product is part of a third-party brand name or competitor product.
        """
        if not hasattr(sentence, 'ents'):
            return False
        
        product_text = entity.text.lower()
        
        # Check if this product is part of a larger organization entity that's not IBM
        for ent in sentence.ents:
            if ent.label_ in ['ORG', 'PRODUCT'] and ent != entity:
                if product_text in ent.text.lower():
                    # Check if the organization is likely non-IBM
                    org_text = ent.text.lower()
                    non_ibm_indicators = ['microsoft', 'google', 'amazon', 'oracle', 'sap', 'salesforce', 'apple']
                    if any(indicator in org_text for indicator in non_ibm_indicators):
                        return True  # Part of competitor product
        
        # Check for explicit competitor mentions in sentence
        sentence_text = sentence.text.lower()
        competitor_indicators = [
            'microsoft', 'google', 'amazon', 'oracle', 'sap', 'salesforce', 'apple',
            'adobe', 'vmware', 'cisco', 'dell', 'hp', 'intel', 'nvidia'
        ]
        
        for indicator in competitor_indicators:
            if indicator in sentence_text and product_text in sentence_text:
                # Check if they're close together (within 5 words)
                words = sentence_text.split()
                try:
                    product_idx = next(i for i, word in enumerate(words) if product_text in word)
                    indicator_idx = next(i for i, word in enumerate(words) if indicator in word)
                    if abs(product_idx - indicator_idx) <= 5:
                        return True
                except StopIteration:
                    continue
        
        return False
    
    def _is_product_in_citation_context(self, entity, sentence, context: Dict[str, Any] = None) -> bool:
        """
        Check if product appears in citation or reference context.
        """
        if not hasattr(sentence, 'text'):
            return False
        
        sentence_text = sentence.text.lower()
        product_text = entity.text.lower()
        
        # Check for citation indicators
        citation_indicators = [
            'published by', 'source:', 'reference:', 'cited in', 'according to',
            'doi:', 'isbn:', 'url:', 'retrieved from', 'available at',
            'whitepaper:', 'report:', 'study by', 'research from'
        ]
        
        for indicator in citation_indicators:
            if indicator in sentence_text:
                return True
        
        # Check for reference formatting patterns
        if any(pattern in sentence_text for pattern in ['(19', '(20', '[19', '[20']):  # Years in citations
            return True
        
        # Check for industry report patterns
        if any(pattern in sentence_text for pattern in ['gartner', 'forrester', 'idc', 'analyst']):
            return True
        
        return False
    
    def _is_exact_product_violation(self, entity) -> bool:
        """
        Check if entity represents an exact product naming violation.
        """
        product_name = entity.text
        
        # Well-known IBM product patterns that should have IBM prefix
        ibm_products = [
            'watson', 'cloud', 'db2', 'mainframe', 'z/os', 'aix', 'powervm',
            'spectrum', 'tivoli', 'websphere', 'rational', 'lotus', 'cognos',
            'spss', 'qradar', 'guardium', 'appscan', 'sterling'
        ]
        
        if any(product.lower() in product_name.lower() for product in ibm_products):
            return True
        
        return False
    
    def _is_pattern_product_violation(self, entity) -> bool:
        """
        Check if entity shows a pattern of product naming violation.
        """
        product_name = entity.text
        words = product_name.split()
        
        # Multi-word products with proper casing (likely real products)
        if len(words) > 1 and all(word[0].isupper() if word.isalpha() else True for word in words):
            # Additional checks for product-like patterns
            if any(word.lower() in ['platform', 'suite', 'system', 'service', 'solution'] 
                   for word in words):
                return True
        
        # Single word capitalized products that look like brand names
        if (len(words) == 1 and 
            product_name[0].isupper() and 
            len(product_name) > 3 and
            not product_name.isupper()):  # Not an acronym
            return True
        
        return False
    
    def _is_minor_product_issue(self, entity) -> bool:
        """
        Check if entity has minor product naming issues.
        """
        product_name = entity.text
        words = product_name.split()
        
        # Single word products that might be generic terms
        if len(words) == 1:
            generic_terms = ['server', 'cloud', 'platform', 'system', 'service', 'software']
            if product_name.lower() in generic_terms:
                return True
        
        # All caps products (might be acronyms)
        if product_name.isupper() and len(product_name) <= 6:
            return True
        
        return False
    
    def _apply_feedback_clues_products(self, evidence_score: float, entity, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to product names.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_products()
        
        if not hasattr(entity, 'text'):
            return evidence_score
        
        product_text = entity.text.lower()
        
        # Consistently Accepted Products
        if product_text in feedback_patterns.get('accepted_products', set()):
            evidence_score -= 0.5  # Users consistently accept this without IBM prefix
        
        # Consistently Rejected Suggestions
        if product_text in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Product type acceptance rates
        product_acceptance = feedback_patterns.get('product_type_acceptance', {})
        acceptance_rate = product_acceptance.get(product_text, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance, likely valid without prefix
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Product names in different content types
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_product_acceptance', {})
        
        acceptance_rate = content_patterns.get(product_text, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Context-specific acceptance
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        context_patterns = feedback_patterns.get(f'{block_type}_product_patterns', {})
        
        if product_text in context_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif product_text in context_patterns.get('flagged', set()):
            evidence_score += 0.2
        
        # Pattern: Frequency-based adjustment for products
        term_frequency = feedback_patterns.get('product_term_frequencies', {}).get(product_text, 0)
        if term_frequency > 10:  # Commonly seen product
            acceptance_rate = feedback_patterns.get('product_term_acceptance', {}).get(product_text, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        # Pattern: IBM vs non-IBM product handling
        if self._is_likely_ibm_product(entity):
            ibm_patterns = feedback_patterns.get('ibm_product_acceptance', {})
            acceptance_rate = ibm_patterns.get(product_text, 0.2)  # Lower default for IBM products
            if acceptance_rate > 0.6:
                evidence_score -= 0.2  # Some IBM products acceptable without prefix
        else:
            # Non-IBM products should generally not be flagged
            evidence_score -= 0.4
        
        return evidence_score
    
    def _is_likely_ibm_product(self, entity) -> bool:
        """
        Check if the product is likely an IBM product that should have IBM prefix.
        """
        product_name = entity.text.lower()
        
        # Known IBM product indicators
        ibm_indicators = [
            'watson', 'cloud', 'db2', 'mainframe', 'z/os', 'aix', 'powervm',
            'spectrum', 'tivoli', 'websphere', 'rational', 'lotus', 'cognos',
            'spss', 'qradar', 'guardium', 'appscan', 'sterling', 'maximo',
            'planning analytics', 'security', 'hybrid cloud'
        ]
        
        return any(indicator in product_name for indicator in ibm_indicators)
    
    def _get_cached_feedback_patterns_products(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for product names.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_products': {'api', 'ui', 'sdk'},  # Common technical terms sometimes acceptable
            'rejected_suggestions': set(),  # Products users don't want flagged
            'product_type_acceptance': {
                'watson': 0.1,          # Should almost always have IBM prefix
                'cloud': 0.3,           # Sometimes acceptable without prefix
                'platform': 0.4,        # Often acceptable without prefix
                'server': 0.6,          # Often acceptable without prefix
                'system': 0.7,          # Often acceptable without prefix
                'service': 0.7,         # Often acceptable without prefix
                'api': 0.8,             # Very acceptable without prefix
                'sdk': 0.8,             # Very acceptable without prefix
                'ui': 0.9,              # Almost always acceptable without prefix
                'software': 0.5,        # Moderately acceptable without prefix
                'application': 0.6      # Often acceptable without prefix
            },
            'technical_product_acceptance': {
                'api': 0.9,             # Very acceptable in technical writing
                'sdk': 0.9,             # Very acceptable in technical writing
                'platform': 0.7,        # Acceptable in technical writing
                'service': 0.8,         # Very acceptable in technical writing
                'system': 0.7,          # Acceptable in technical writing
                'cloud': 0.6,           # Moderately acceptable in technical writing
                'watson': 0.2           # Should usually have IBM prefix even in technical
            },
            'marketing_product_acceptance': {
                'watson': 0.05,         # Should almost always have IBM prefix in marketing
                'cloud': 0.2,           # Should usually have IBM prefix in marketing
                'platform': 0.3,        # Sometimes acceptable in marketing
                'solution': 0.4,        # Often acceptable in marketing
                'service': 0.5,         # Often acceptable in marketing
                'system': 0.4           # Sometimes acceptable in marketing
            },
            'documentation_product_acceptance': {
                'api': 0.8,             # Often acceptable in documentation
                'sdk': 0.8,             # Often acceptable in documentation
                'platform': 0.6,        # Moderately acceptable in documentation
                'service': 0.7,         # Acceptable in documentation
                'watson': 0.3,          # Should usually have IBM prefix in docs
                'cloud': 0.4            # Sometimes acceptable in documentation
            },
            'product_term_frequencies': {
                'cloud': 300,           # Very common product term
                'platform': 250,        # Common product term
                'service': 280,         # Very common product term
                'watson': 150,          # Common IBM product
                'api': 400,             # Very common technical term
                'sdk': 200,             # Common technical term
                'system': 180,          # Common product term
                'server': 160           # Common product term
            },
            'product_term_acceptance': {
                'cloud': 0.3,           # Usually needs context or prefix
                'platform': 0.4,        # Moderately acceptable
                'service': 0.7,         # Often acceptable
                'watson': 0.1,          # Almost always needs IBM prefix
                'api': 0.8,             # Often acceptable
                'sdk': 0.8,             # Often acceptable
                'system': 0.6,          # Often acceptable
                'server': 0.6           # Often acceptable
            },
            'ibm_product_acceptance': {
                'watson': 0.1,          # Low acceptance without IBM prefix
                'cloud': 0.2,           # Low acceptance without IBM prefix
                'spectrum': 0.1,        # Low acceptance without IBM prefix
                'db2': 0.1,             # Low acceptance without IBM prefix
                'mainframe': 0.3,       # Sometimes acceptable without prefix
                'tivoli': 0.1,          # Low acceptance without IBM prefix
                'websphere': 0.1,       # Low acceptance without IBM prefix
                'rational': 0.2,        # Low acceptance without IBM prefix
                'cognos': 0.1           # Low acceptance without IBM prefix
            },
            'paragraph_product_patterns': {
                'accepted': {'api', 'sdk', 'ui'},
                'flagged': {'watson', 'cloud', 'db2'}
            },
            'heading_product_patterns': {
                'accepted': {'platform', 'service', 'api'},  # More acceptable in headings
                'flagged': {'watson', 'cognos'}
            },
            'list_product_patterns': {
                'accepted': {'api', 'sdk', 'ui', 'service'},  # Technical terms common in lists
                'flagged': {'watson', 'db2'}
            }
        }
    
    def _find_product_candidates(self, sentence, doc):
        """
        Find product candidates in the sentence using both NER and manual detection.
        """
        candidates = []
        
        # 1. Check named entities that could be products
        for ent in sentence.ents:
            if ent.label_ in ['PRODUCT', 'ORG', 'PERSON']:  # Expanded to catch Watson (PERSON)
                # Additional filtering for likely products
                if self._is_likely_product_entity(ent):
                    candidates.append(ent)
        
        # 2. Manual detection for common product patterns
        manual_products = self._detect_manual_product_patterns(sentence, doc)
        candidates.extend(manual_products)
        
        # Remove duplicates
        unique_candidates = []
        seen_spans = set()
        for candidate in candidates:
            span_key = (candidate.start_char, candidate.end_char)
            if span_key not in seen_spans:
                unique_candidates.append(candidate)
                seen_spans.add(span_key)
        
        return unique_candidates
    
    def _is_likely_product_entity(self, ent):
        """
        Check if a named entity is likely a product that needs IBM prefix using configuration.
        """
        entity_text = ent.text.lower()
        
        # Check if entity is a known IBM product
        ibm_product = self.config_service.get_ibm_product(entity_text)
        if ibm_product:
            return True
        
        # Check if it looks like a product using configured indicators
        if ent.label_ == 'ORG':  # Organizations could be products
            product_indicators = self.config_service.get_product_indicators()
            if any(indicator.lower() in entity_text for indicator in product_indicators):
                return True
        
        return False
    
    def _detect_manual_product_patterns(self, sentence, doc):
        """
        Manually detect product patterns that SpaCy might miss.
        """
        products = []
        
        # Product pattern indicators
        product_keywords = [
            'platform', 'service', 'suite', 'system', 'solution', 'cloud',
            'analytics', 'intelligence', 'security', 'database', 'server'
        ]
        
        # Look for capitalized phrases with product keywords
        for i, token in enumerate(sentence):
            if token.text[0].isupper() and token.pos_ in ['NOUN', 'PROPN']:
                # Check if this starts a product-like phrase
                phrase_tokens = [token]
                j = i + 1
                
                # Collect adjacent capitalized/product words
                while j < len(sentence) and (
                    sentence[j].text[0].isupper() or 
                    sentence[j].text.lower() in product_keywords or
                    sentence[j].pos_ == 'NOUN'
                ):
                    phrase_tokens.append(sentence[j])
                    j += 1
                
                # Check if this looks like a product
                phrase_text = ' '.join(t.text for t in phrase_tokens)
                if (len(phrase_tokens) >= 2 and 
                    any(kw in phrase_text.lower() for kw in product_keywords)):
                    
                    # Create a mock entity-like object
                    class MockEntity:
                        def __init__(self, tokens):
                            self.tokens = tokens
                            self.text = ' '.join(t.text for t in tokens)
                            self.start = tokens[0].i
                            self.end = tokens[-1].i + 1
                            self.start_char = tokens[0].idx
                            self.end_char = tokens[-1].idx + len(tokens[-1].text)
                            self.label_ = 'PRODUCT'
                            self.sent = sentence
                            self.doc = doc
                        
                        def __iter__(self):
                            return iter(self.tokens)
                        
                        def __len__(self):
                            return len(self.tokens)
                        
                        def __getitem__(self, index):
                            return self.tokens[index]
                    
                    products.append(MockEntity(phrase_tokens))
        
        return products
    
    def _has_ibm_prefix(self, entity, doc):
        """
        Check if the entity is preceded by "IBM".
        """
        # Check if the token before the entity is "IBM"
        if entity.start == 0:
            return False
        
        prev_token = doc[entity.start - 1]
        return prev_token.text.upper() == 'IBM'
