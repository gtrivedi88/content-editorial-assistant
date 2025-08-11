"""
Capitalization Rule
Based on IBM Style Guide topic: "Capitalization"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CapitalizationRule(BaseLanguageRule):
    """
    Checks for missing capitalization in text.
    Comprehensive rule processing using the SpaCy engine for linguistic accuracy.
    """
    def _get_rule_type(self) -> str:
        return 'capitalization'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for capitalization errors using evidence-based scoring.
        Uses sophisticated linguistic analysis to distinguish genuine capitalization errors from 
        acceptable technical variations and contextual usage patterns.
        """
        errors = []
        if not nlp:
            return errors

        # Skip analysis for content that was originally inline formatted (code, emphasis, etc.)
        if context and context.get('contains_inline_formatting'):
            return errors

        # ENTERPRISE CONTEXT INTELLIGENCE: Get content classification
        content_classification = self._get_content_classification(text, context, nlp)
        
        doc = nlp(text)

        # LINGUISTIC ANCHOR: Use spaCy sentence segmentation for precise analysis
        for i, sent in enumerate(doc.sents):
            for token in sent:
                # Check for potential capitalization issues and calculate evidence
                if self._is_potential_capitalization_candidate(token, doc, content_classification):
                    if token.text.islower():
                        # Calculate evidence score for this capitalization issue
                        evidence_score = self._calculate_capitalization_evidence(
                            token, sent, text, context, content_classification
                        )
                        
                        # Only create error if evidence suggests it's worth flagging
                        if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                            errors.append(self._create_error(
                                sentence=sent.text, sentence_index=i,
                                message=self._get_contextual_capitalization_message(token, evidence_score, context),
                                suggestions=self._generate_smart_capitalization_suggestions(token, evidence_score, context),
                                severity='medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,  # Your nuanced assessment
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))

        return errors

    def _is_potential_capitalization_candidate(self, token, doc, content_classification: str) -> bool:
        """
        Ultra-conservative morphological logic using SpaCy linguistic anchors.
        Only flags high-confidence proper nouns to avoid false positives.
        """
        
        # EXCEPTION CHECK: Never flag words in the exception list
        if self._is_excepted(token.text):
            return False
        
        # LINGUISTIC ANCHOR 1: High-confidence Named Entity Recognition ONLY
        # This is the primary and most reliable signal for proper nouns
        if token.ent_type_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT']:
            # Additional confidence check: ensure it's not a misclassified common word
            # and has proper noun characteristics
            if (len(token.text) > 1 and  # Skip single characters
                not token.text.lower() in ['user', 'data', 'file', 'system', 'admin', 'guest', 'client', 'server'] and
                # Entity should have some proper noun indicators
                (token.text[0].isupper() or  # Already properly capitalized
                 token.ent_iob_ in ['B', 'I'])):  # Strong entity boundary signal
                return True
        
        # LINGUISTIC ANCHOR 2: Very conservative sentence start logic
        # Only for clear proper nouns at sentence start that are definitely names
        if token.is_sent_start and len(token.text) > 1:
            # Must be explicitly tagged as a named entity with strong confidence
            if (token.ent_type_ in ['PERSON', 'ORG', 'GPE'] and 
                token.text[0].islower() and
                not self._is_excepted(token.text)):
                return True
                
        # LINGUISTIC ANCHOR 3: Proper noun sequences (like "New York")
        # Only trigger for clear multi-word proper nouns  
        if (token.i > 0 and 
            doc[token.i - 1].ent_type_ in ['PERSON', 'ORG', 'GPE'] and  # Previous token is a named entity
            token.ent_type_ == doc[token.i - 1].ent_type_ and  # Same entity type
            token.text[0].islower() and
            not self._is_excepted(token.text)):
            return True
        
        return False

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _calculate_capitalization_evidence(self, token, sentence, text: str, context: dict, content_classification: str) -> float:
        """
        Calculate evidence score (0.0-1.0) for capitalization error.
        
        Higher scores indicate stronger evidence of a genuine capitalization error.
        Lower scores indicate borderline cases or acceptable technical variations.
        
        Args:
            token: The token potentially needing capitalization
            sentence: Sentence containing the token
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            content_classification: Content type classification
            
        Returns:
            float: Evidence score from 0.0 (acceptable as-is) to 1.0 (clear error)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_capitalization_evidence(token)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this token
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_capitalization(evidence_score, token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_capitalization(evidence_score, token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_capitalization(evidence_score, token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_capitalization(evidence_score, token, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _get_base_capitalization_evidence(self, token) -> float:
        """Get base evidence score based on the type and confidence of entity recognition."""
        
        # High-confidence entity types get higher base evidence
        if token.ent_type_ == 'PERSON':
            return 0.9  # Person names should almost always be capitalized
        elif token.ent_type_ == 'ORG':
            return 0.8  # Organization names usually capitalized
        elif token.ent_type_ == 'GPE':
            return 0.8  # Geographic/political entities usually capitalized
        elif token.ent_type_ == 'PRODUCT':
            return 0.6  # Product names often have variant capitalization
        
        # Sentence-start proper nouns with entity recognition
        if token.is_sent_start and token.ent_type_ in ['PERSON', 'ORG', 'GPE']:
            return 0.8  # Strong evidence for sentence-start proper nouns
        
        # Multi-word entity sequences
        if (token.i > 0 and 
            token.doc[token.i - 1].ent_type_ in ['PERSON', 'ORG', 'GPE'] and 
            token.ent_type_ == token.doc[token.i - 1].ent_type_):
            return 0.7  # Part of entity sequence
        
        return 0.0  # No evidence for capitalization

    # === LINGUISTIC CLUES FOR CAPITALIZATION ===

    def _apply_linguistic_clues_capitalization(self, evidence_score: float, token, sentence) -> float:
        """Apply comprehensive SpaCy-based linguistic analysis clues for capitalization."""
        
        # === ENTITY BOUNDARY ANALYSIS ===
        # Strong entity boundaries indicate higher confidence
        if token.ent_iob_ == 'B':  # Beginning of entity
            evidence_score += 0.1
        elif token.ent_iob_ == 'I':  # Inside entity
            evidence_score += 0.05
        elif token.ent_iob_ == 'O':  # Outside entity
            if token.ent_type_:  # But still has entity type
                evidence_score += 0.03  # Weak entity signal
        
        # === POS TAG ANALYSIS ===
        # Detailed part-of-speech analysis
        if token.pos_ == 'PROPN':
            evidence_score += 0.2  # Proper noun tag
        elif token.pos_ == 'NOUN' and token.ent_type_:
            evidence_score += 0.1  # Common noun but recognized as entity
        elif token.pos_ == 'ADJ' and token.ent_type_:
            evidence_score -= 0.1  # Adjectives less likely to need capitalization
        elif token.pos_ in ['VERB', 'ADV', 'ADP']:
            evidence_score -= 0.3  # Function words unlikely proper nouns
        
        # === ENHANCED TAG ANALYSIS ===
        # More granular tag-based analysis using Penn Treebank tags
        if hasattr(token, 'tag_'):
            if token.tag_ == 'NNP':  # Proper noun, singular
                evidence_score += 0.25  # Strong proper noun indicator
            elif token.tag_ == 'NNPS':  # Proper noun, plural
                evidence_score += 0.2  # Proper noun plural
            elif token.tag_ in ['NN', 'NNS']:  # Common nouns
                if token.ent_type_:  # But recognized as entity
                    evidence_score += 0.15  # Common noun that's actually proper
                else:
                    evidence_score -= 0.1  # Regular common noun
            elif token.tag_ in ['JJ', 'JJR', 'JJS']:  # Adjectives
                evidence_score -= 0.2  # Adjectives rarely proper nouns
            elif token.tag_ in ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']:  # Verbs
                evidence_score -= 0.4  # Verbs are not proper nouns
            elif token.tag_ in ['DT', 'IN', 'CC', 'TO']:  # Function words
                evidence_score -= 0.5  # Function words never proper nouns
            elif token.tag_ in ['CD', 'LS']:  # Numbers and list markers
                evidence_score -= 0.3  # Numbers rarely need capitalization
        
        # === DEPENDENCY PARSING ANALYSIS ===
        # Syntactic role affects capitalization likelihood
        if token.dep_ == 'nsubj':  # Nominal subject
            if token.ent_type_:
                evidence_score += 0.1  # Subject entities more likely proper
        elif token.dep_ == 'compound':  # Compound modifier
            evidence_score -= 0.1  # Compounds may be technical
        elif token.dep_ == 'amod':  # Adjectival modifier
            evidence_score -= 0.2  # Adjectives less likely proper nouns
        elif token.dep_ == 'appos':  # Appositional modifier
            evidence_score += 0.1  # Appositive often proper noun
        elif token.dep_ in ['dobj', 'pobj']:  # Object roles
            if token.ent_type_:
                evidence_score += 0.05  # Objects can be proper nouns
        
        # === MORPHOLOGICAL FEATURES ANALYSIS ===
        # Comprehensive morphological feature analysis
        if hasattr(token, 'morph') and token.morph:
            morph_str = str(token.morph)
            
            # Noun type features
            if 'NounType=Prop' in morph_str:
                evidence_score += 0.2  # Explicit proper noun marking
            elif 'Number=Sing' in morph_str and token.pos_ == 'NOUN':
                evidence_score += 0.05  # Singular nouns more likely proper
            elif 'Number=Plur' in morph_str:
                evidence_score -= 0.1  # Plural less likely proper noun
            
            # Case features (for languages that have them)
            if 'Case=Nom' in morph_str:
                evidence_score += 0.05  # Nominative case
            elif 'Case=Gen' in morph_str:
                evidence_score += 0.03  # Genitive case
            
            # Person features (relevant for some contexts)
            if 'Person=3' in morph_str and token.pos_ == 'PROPN':
                evidence_score += 0.05
        
        # === NAMED ENTITY TYPE DETAILED ANALYSIS ===
        # More nuanced entity type handling
        if token.ent_type_:
            if token.ent_type_ == 'PERSON':
                evidence_score += 0.2  # Strong evidence for person names
            elif token.ent_type_ == 'ORG':
                evidence_score += 0.15  # Organizations usually capitalized
            elif token.ent_type_ == 'GPE':
                evidence_score += 0.15  # Geographic entities
            elif token.ent_type_ == 'PRODUCT':
                evidence_score += 0.1  # Products often capitalized
            elif token.ent_type_ == 'EVENT':
                evidence_score += 0.12  # Events usually capitalized
            elif token.ent_type_ == 'FAC':
                evidence_score += 0.08  # Facilities
            elif token.ent_type_ == 'LAW':
                evidence_score += 0.15  # Laws and legal documents
            elif token.ent_type_ in ['MONEY', 'PERCENT', 'QUANTITY']:
                evidence_score -= 0.2  # Numeric entities less relevant
            elif token.ent_type_ in ['DATE', 'TIME']:
                evidence_score -= 0.1  # Temporal entities variable
        
        # === LENGTH AND CHARACTER PATTERN ANALYSIS ===
        # Enhanced character pattern analysis
        if len(token.text) <= 1:
            evidence_score -= 0.5  # Single characters rarely proper nouns
        elif len(token.text) == 2:
            if token.text.isupper():
                evidence_score -= 0.1  # Could be acronym
            else:
                evidence_score -= 0.3  # Short words less likely proper
        elif len(token.text) >= 3 and len(token.text) <= 5:
            if token.text.isupper():
                evidence_score -= 0.2  # Likely acronym
            else:
                evidence_score += 0.0  # Neutral length
        elif len(token.text) >= 6:
            evidence_score += 0.1  # Longer words more likely proper nouns
        
        # === CAPITALIZATION PATTERN ANALYSIS ===
        # Analyze existing capitalization patterns
        if token.text.isupper() and len(token.text) <= 5:
            evidence_score -= 0.3  # All-caps likely acronym
        elif token.text.istitle():
            evidence_score -= 0.8  # Already capitalized correctly
        elif any(c.isupper() for c in token.text[1:]):
            evidence_score -= 0.2  # Mixed case, might be brand name
        
        # === COMMON WORD FILTERING ENHANCED ===
        # Expanded common technical terms filtering using both text and lemma
        common_tech_words = {
            'user', 'data', 'file', 'system', 'admin', 'guest', 'client', 'server',
            'api', 'url', 'http', 'json', 'xml', 'html', 'css', 'sql', 'email',
            'config', 'log', 'debug', 'test', 'code', 'app', 'web', 'site',
            'database', 'network', 'protocol', 'interface', 'module', 'component',
            'service', 'application', 'framework', 'library', 'package', 'version'
        }
        
        # Check both text and lemma for technical words
        if token.text.lower() in common_tech_words:
            evidence_score -= 0.4  # Strong reduction for common tech words
        elif hasattr(token, 'lemma_') and token.lemma_.lower() in common_tech_words:
            evidence_score -= 0.35  # Also check lemmatized form
        
        # === LEMMA-BASED ANALYSIS ===
        # Use lemmatized forms for more accurate semantic analysis
        if hasattr(token, 'lemma_') and token.lemma_:
            lemma_lower = token.lemma_.lower()
            
            # Common verbs that are never proper nouns
            if lemma_lower in ['be', 'have', 'do', 'say', 'get', 'make', 'go', 'know', 'take', 'see']:
                evidence_score -= 0.6  # Strong evidence against proper noun
            
            # Technical action verbs
            elif lemma_lower in ['configure', 'install', 'deploy', 'execute', 'process', 'handle']:
                evidence_score -= 0.4  # Technical verbs not proper nouns
            
            # Abstract concepts that might be mistaken for proper nouns
            elif lemma_lower in ['concept', 'idea', 'method', 'approach', 'solution', 'problem']:
                evidence_score -= 0.3  # Abstract nouns less likely proper
            
            # Technology-related lemmas
            elif lemma_lower in ['technology', 'software', 'hardware', 'computer', 'machine']:
                evidence_score -= 0.2  # Generic tech terms
        
        # === SURROUNDING TOKEN ANALYSIS ===
        # Analyze neighboring tokens for context
        doc = token.doc
        
        # Previous token analysis
        if token.i > 0:
            prev_token = doc[token.i - 1]
            if prev_token.text.lower() in ['the', 'a', 'an']:
                evidence_score -= 0.1  # Articles suggest common noun
            elif prev_token.pos_ == 'ADP':  # Preposition
                evidence_score -= 0.05  # After preposition
            elif prev_token.ent_type_ and prev_token.ent_type_ == token.ent_type_:
                evidence_score += 0.1  # Part of multi-word entity
        
        # Next token analysis
        if token.i < len(doc) - 1:
            next_token = doc[token.i + 1]
            if next_token.pos_ == 'PUNCT':
                if next_token.text in ['.', '!', '?']:
                    evidence_score += 0.02  # End of sentence
                elif next_token.text in [',', ';']:
                    evidence_score += 0.01  # Punctuation context
            elif next_token.ent_type_ and next_token.ent_type_ == token.ent_type_:
                evidence_score += 0.1  # Part of multi-word entity
        
        # === BRAND/PRODUCT NAME PATTERNS ===
        # Enhanced pattern recognition
        if self._has_brand_name_pattern(token.text):
            evidence_score += 0.2
        elif self._has_technical_name_pattern(token.text):
            evidence_score -= 0.2  # Technical names may have variant capitalization
        
        # === SENTENCE POSITION ANALYSIS ===
        # Position within sentence affects likelihood
        if token.is_sent_start:
            evidence_score += 0.05  # Sentence start slightly more likely
        elif token.i / len(list(token.sent)) < 0.3:  # Early in sentence
            evidence_score += 0.02
        elif token.i / len(list(token.sent)) > 0.7:  # Late in sentence
            evidence_score += 0.01
        
        return evidence_score

    def _apply_structural_clues_capitalization(self, evidence_score: float, token, context: dict) -> float:
        """Apply document structure-based clues for capitalization."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # === FORMAL WRITING CONTEXTS ===
        # Formal contexts expect proper capitalization
        if block_type in ['heading', 'title']:
            evidence_score += 0.2  # Headings expect proper capitalization
        elif block_type == 'paragraph':
            evidence_score += 0.1  # Body text somewhat important
        
        # === TECHNICAL CONTEXTS ===
        # Technical contexts may have different capitalization rules
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.5  # Code has its own capitalization rules
        elif block_type == 'inline_code':
            evidence_score -= 0.4  # Inline code may not follow prose rules
        
        # === LISTS AND TABLES ===
        # Lists and tables may have abbreviated or technical content
        if block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.2  # Lists may be more technical/abbreviated
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.3  # Tables often have technical content
        
        # === ADMONITIONS ===
        # Notes and warnings may contain technical terms
        if block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP']:
                evidence_score -= 0.1  # Notes may contain technical terms
            elif admonition_type in ['WARNING', 'CAUTION']:
                evidence_score += 0.0  # Warnings should be clear
        
        return evidence_score

    def _apply_semantic_clues_capitalization(self, evidence_score: float, token, text: str, context: dict) -> float:
        """Apply semantic and content-type clues for capitalization."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Different content types have different capitalization expectations
        if content_type == 'technical':
            evidence_score -= 0.2  # Technical writing may have variant capitalization
        elif content_type == 'api':
            evidence_score -= 0.3  # API documentation very technical
        elif content_type == 'academic':
            evidence_score += 0.2  # Academic writing expects proper capitalization
        elif content_type == 'legal':
            evidence_score += 0.3  # Legal writing demands precision
        elif content_type == 'marketing':
            evidence_score -= 0.1  # Marketing may use stylistic variations
        elif content_type == 'narrative':
            evidence_score += 0.1  # Narrative writing expects proper nouns
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score -= 0.2  # Technical domains have variant rules
        elif domain in ['documentation', 'tutorial']:
            evidence_score -= 0.1  # Educational content may be mixed
        elif domain in ['academic', 'research']:
            evidence_score += 0.1  # Academic domains expect precision
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score -= 0.2  # Technical audiences familiar with conventions
        elif audience in ['academic', 'professional']:
            evidence_score += 0.1  # Professional audiences expect correctness
        elif audience in ['beginner', 'general']:
            evidence_score += 0.2  # General audiences need clear examples
        
        # === CONTENT TYPE SPECIFIC ANALYSIS ===
        # Use helper methods to analyze content type
        if self._is_api_documentation(text):
            evidence_score -= 0.3  # API docs very technical
        elif self._is_technical_specification(text, context):
            evidence_score -= 0.2  # Technical specs allow variant capitalization
        elif self._is_academic_documentation(text, context):
            evidence_score += 0.2  # Academic writing expects precision
        elif self._is_brand_marketing_content(text, context):
            evidence_score += 0.1  # Marketing focuses on brand names
        elif self._is_legal_documentation(text, context):
            evidence_score += 0.3  # Legal docs require precise capitalization
        
        # === TECHNICAL TERM DENSITY ===
        # High technical density suggests technical content with variant rules
        if self._has_high_technical_density(text):
            evidence_score -= 0.2
        
        # === BRAND/PRODUCT CONTEXT ===
        # Check if surrounded by other brand/product names
        if self._is_in_brand_context(token, text):
            evidence_score += 0.2  # Brand context increases capitalization likelihood
        
        return evidence_score

    def _apply_feedback_clues_capitalization(self, evidence_score: float, token, context: dict) -> float:
        """Apply feedback patterns for capitalization."""
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns('capitalization')
        
        word_lower = token.text.lower()
        
        # Check if this word is commonly accepted without capitalization
        accepted_lowercase = feedback_patterns.get('accepted_lowercase_terms', set())
        if word_lower in accepted_lowercase:
            evidence_score -= 0.4  # Users consistently accept this lowercase
        
        # Check if this word is commonly corrected to capitalize
        flagged_for_caps = feedback_patterns.get('flagged_for_capitalization', set())
        if word_lower in flagged_for_caps:
            evidence_score += 0.3  # Users consistently capitalize this
        
        # Entity-type specific patterns
        if token.ent_type_:
            entity_patterns = feedback_patterns.get(f'{token.ent_type_.lower()}_patterns', {})
            if word_lower in entity_patterns.get('acceptable_lowercase', set()):
                evidence_score -= 0.2
            elif word_lower in entity_patterns.get('needs_capitalization', set()):
                evidence_score += 0.2
        
        # Context-specific patterns
        if context:
            block_type = context.get('block_type', 'paragraph')
            context_patterns = feedback_patterns.get(f'{block_type}_capitalization_patterns', {})
            
            if word_lower in context_patterns.get('acceptable_lowercase', set()):
                evidence_score -= 0.2
            elif word_lower in context_patterns.get('needs_capitalization', set()):
                evidence_score += 0.2
        
        return evidence_score

    # === HELPER METHODS ===

    # Removed _is_api_documentation - using base class utility

    def _is_technical_specification(self, text: str, context: dict) -> bool:
        """Check if content is technical specification."""
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        
        # Direct indicators
        if content_type in ['specification', 'technical'] or domain in ['engineering', 'technical']:
            return True
        
        # Text-based indicators
        spec_indicators = [
            'specification', 'requirement', 'protocol', 'standard',
            'implementation', 'architecture', 'design', 'interface',
            'component', 'module', 'system', 'framework', 'library',
            'algorithm', 'data structure', 'performance', 'scalability'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in spec_indicators if indicator in text_lower) >= 3

    def _is_academic_documentation(self, text: str, context: dict) -> bool:
        """Check if content is academic documentation."""
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        # Direct indicators
        if content_type in ['academic', 'research'] or domain in ['academic', 'research']:
            return True
        
        # Text-based indicators
        academic_indicators = [
            'research', 'study', 'analysis', 'methodology', 'hypothesis',
            'conclusion', 'abstract', 'literature', 'citation', 'reference',
            'experiment', 'data', 'statistical', 'empirical', 'theoretical'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in academic_indicators if indicator in text_lower) >= 3

    def _is_brand_marketing_content(self, text: str, context: dict) -> bool:
        """Check if content is brand/marketing material."""
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        # Direct indicators
        if content_type in ['marketing', 'promotional'] or domain in ['marketing', 'branding']:
            return True
        
        # Text-based indicators
        marketing_indicators = [
            'brand', 'product', 'solution', 'service', 'customer',
            'experience', 'innovation', 'leading', 'premier', 'enterprise',
            'industry', 'market', 'competitive', 'advantage', 'benefit'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in marketing_indicators if indicator in text_lower) >= 3

    def _is_legal_documentation(self, text: str, context: dict) -> bool:
        """Check if content is legal documentation."""
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        # Direct indicators
        if content_type in ['legal', 'compliance'] or domain in ['legal', 'compliance']:
            return True
        
        # Text-based indicators
        legal_indicators = [
            'legal', 'contract', 'agreement', 'terms', 'conditions',
            'policy', 'compliance', 'regulation', 'statute', 'law',
            'clause', 'provision', 'liability', 'warranty', 'disclaimer',
            'copyright', 'trademark', 'patent', 'intellectual property'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in legal_indicators if indicator in text_lower) >= 3

    def _has_brand_name_pattern(self, text: str) -> bool:
        """Check if text follows typical brand name patterns."""
        # Common brand name patterns
        brand_patterns = [
            # Mixed case patterns
            lambda s: any(c.isupper() for c in s[1:]),  # Internal capitals like iPhone
            # All caps acronyms
            lambda s: s.isupper() and len(s) <= 6,  # IBM, API, etc.
            # Starts with lowercase but has capitals (camelCase)
            lambda s: s[0].islower() and any(c.isupper() for c in s[1:])
        ]
        
        return any(pattern(text) for pattern in brand_patterns)

    def _has_technical_name_pattern(self, text: str) -> bool:
        """Check if text follows technical naming patterns."""
        # Technical patterns that may not need capitalization
        technical_patterns = [
            # Contains numbers
            lambda s: any(c.isdigit() for c in s),
            # Contains underscores or hyphens
            lambda s: '_' in s or '-' in s,
            # All lowercase tech terms
            lambda s: s.islower() and len(s) > 2
        ]
        
        return any(pattern(text) for pattern in technical_patterns)

    # Removed _has_high_technical_density - using base class utility

    def _is_in_brand_context(self, token, text: str) -> bool:
        """Check if token appears in a context with other brand/product names."""
        # Look for other capitalized words nearby (within 10 words)
        words = text.split()
        try:
            token_index = words.index(token.text)
            start = max(0, token_index - 5)
            end = min(len(words), token_index + 6)
            context_words = words[start:end]
            
            # Count capitalized words in context
            capitalized_count = sum(1 for word in context_words if word and word[0].isupper())
            
            # High ratio of capitalized words suggests brand/product context
            return capitalized_count / len(context_words) > 0.3
        except ValueError:
            return False

    # Removed _get_cached_feedback_patterns - using base class utility

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_capitalization_message(self, token, evidence_score: float, context: dict = None) -> str:
        """Generate context-aware error messages for capitalization based on evidence score and context."""
        
        # Get entity type and context information
        entity_type = token.ent_type_ if hasattr(token, 'ent_type_') else ''
        content_type = context.get('content_type', 'general') if context else 'general'
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        audience = context.get('audience', 'general') if context else 'general'
        
        # High evidence messages (0.8+)
        if evidence_score > 0.8:
            if entity_type == 'PERSON':
                return f"'{token.text}' should be capitalized as it is a person's name."
            elif entity_type == 'ORG':
                return f"'{token.text}' should be capitalized as it is an organization name."
            elif entity_type == 'GPE':
                return f"'{token.text}' should be capitalized as it is a geographic or political entity."
            elif content_type in ['academic', 'legal']:
                return f"'{token.text}' should be capitalized as proper nouns are required in formal writing."
            else:
                return f"'{token.text}' should be capitalized as it appears to be a proper noun."
        
        # Medium evidence messages (0.5-0.8)
        elif evidence_score > 0.5:
            if entity_type == 'PRODUCT':
                return f"Consider capitalizing '{token.text}' if it is a specific product name."
            elif content_type == 'technical':
                return f"Consider capitalizing '{token.text}' if it refers to a specific system, product, or entity rather than a generic term."
            elif content_type == 'marketing':
                return f"Consider capitalizing '{token.text}' following your brand style guidelines."
            elif block_type in ['heading', 'title']:
                return f"Consider capitalizing '{token.text}' in headings for proper formatting."
            else:
                return f"Consider capitalizing '{token.text}' if it refers to a specific entity."
        
        # Lower evidence messages (0.3-0.5)
        elif evidence_score > 0.3:
            if content_type == 'technical' and audience in ['developer', 'technical']:
                return f"'{token.text}' might need capitalization unless it's an established technical term."
            elif block_type in ['code_block', 'inline_code']:
                return f"'{token.text}' might need capitalization depending on your coding style conventions."
            else:
                return f"'{token.text}' might need capitalization depending on whether it's a proper noun in context."
        
        # Very low evidence messages (0.1-0.3)
        else:
            if content_type == 'api':
                return f"'{token.text}' may be acceptable lowercase in API documentation unless it's a specific service name."
            elif content_type == 'technical':
                return f"'{token.text}' may be acceptable lowercase as a technical term, but verify if it's a proper noun."
            else:
                return f"'{token.text}' capitalization depends on context - verify if it's a proper noun."

    def _generate_smart_capitalization_suggestions(self, token, evidence_score: float, context: dict = None) -> List[str]:
        """Generate context-aware suggestions for capitalization based on evidence and context."""
        
        suggestions = []
        entity_type = token.ent_type_ if hasattr(token, 'ent_type_') else ''
        content_type = context.get('content_type', 'general') if context else 'general'
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        audience = context.get('audience', 'general') if context else 'general'
        domain = context.get('domain', 'general') if context else 'general'
        
        # Primary suggestion - capitalize the word
        capitalized = token.text.capitalize()
        suggestions.append(f"Change '{token.text}' to '{capitalized}'")
        
        # Entity-specific suggestions
        if entity_type == 'PERSON':
            suggestions.append("Person names must be capitalized in all writing styles")
            suggestions.append("Check if this is part of a full name that should be fully capitalized")
        elif entity_type == 'ORG':
            suggestions.append("Organization names typically require capitalization")
            suggestions.append("Verify the official capitalization of this organization name")
        elif entity_type == 'GPE':
            suggestions.append("Geographic and political entities should be capitalized")
            suggestions.append("Check if this is part of a full place name")
        elif entity_type == 'PRODUCT':
            suggestions.append("Product names often require capitalization")
            suggestions.append("Check the official brand styling for this product name")
        elif entity_type == 'EVENT':
            suggestions.append("Event names should be capitalized")
            suggestions.append("Consider if this is a specific event or general activity")
        
        # Context-specific suggestions
        if content_type == 'technical':
            suggestions.append("In technical writing, distinguish between proper nouns (capitalize) and technical terms (often lowercase)")
            if audience in ['developer', 'technical']:
                suggestions.append("Follow established conventions in your technical domain")
            suggestions.append("Check if this term appears in official documentation with specific capitalization")
        
        elif content_type == 'api':
            suggestions.append("API documentation: capitalize service names, but keep technical terms lowercase")
            suggestions.append("Check if this is an endpoint, parameter, or service name requiring capitalization")
        
        elif content_type in ['academic', 'legal']:
            suggestions.append("Formal writing requires strict adherence to proper noun capitalization")
            suggestions.append("When in doubt, consult style guides like APA, MLA, or Chicago")
        
        elif content_type == 'marketing':
            suggestions.append("Follow brand style guidelines for capitalization")
            suggestions.append("Ensure consistency with other marketing materials")
            suggestions.append("Consider trademark implications of capitalization")
        
        elif content_type == 'narrative':
            suggestions.append("Narrative writing expects proper noun capitalization")
            suggestions.append("Consider the context - is this a character, place, or specific thing?")
        
        # Block-type specific suggestions
        if block_type in ['heading', 'title']:
            suggestions.append("Headings often require title case or sentence case capitalization")
            suggestions.append("Consider your organization's heading style guidelines")
        
        elif block_type in ['code_block', 'inline_code']:
            suggestions.append("Code may have different capitalization rules than prose")
            suggestions.append("Follow the conventions of the programming language or framework")
        
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            suggestions.append("List items should follow consistent capitalization within the list")
            suggestions.append("Consider whether list items are sentence fragments or complete sentences")
        
        elif block_type in ['table_cell', 'table_header']:
            suggestions.append("Table content should maintain consistent capitalization")
            suggestions.append("Headers often use title case or consistent formatting")
        
        # Evidence-based suggestions
        if evidence_score > 0.8:
            suggestions.append("Strong evidence suggests this should be capitalized")
            suggestions.append("This appears to be clearly identified as a proper noun")
        elif evidence_score > 0.5:
            suggestions.append("Moderate evidence suggests capitalization may be needed")
            suggestions.append("Review context to confirm if this is a proper noun")
        elif evidence_score < 0.3:
            suggestions.append("Low evidence for capitalization - this may be acceptable as-is")
            suggestions.append("Consider if lowercase is conventional for this term")
        
        # Domain-specific suggestions
        if domain in ['software', 'engineering', 'devops']:
            suggestions.append("Technical domains often have established conventions for term capitalization")
            suggestions.append("Check documentation style guides for your technology stack")
        elif domain in ['academic', 'research']:
            suggestions.append("Academic writing requires precise proper noun identification")
            suggestions.append("Consult relevant style guides for your academic field")
        elif domain in ['legal', 'compliance']:
            suggestions.append("Legal writing demands accuracy in proper noun capitalization")
            suggestions.append("Verify official names and terms in legal contexts")
        
        # Audience-specific suggestions
        if audience in ['beginner', 'general']:
            suggestions.append("Clear capitalization helps general audiences identify important terms")
            suggestions.append("Consider adding explanation if this is a specialized term")
        elif audience in ['expert', 'developer']:
            suggestions.append("Expert audiences may expect established conventions")
            suggestions.append("Follow industry-standard capitalization patterns")
        
        # Additional contextual advice
        if len(suggestions) < 5:  # Add more general advice if needed
            suggestions.append("When uncertain, research the official spelling and capitalization")
            suggestions.append("Maintain consistency throughout your document")
            suggestions.append("Consider creating a style guide entry for this term")
        
        return suggestions[:8]  # Limit to most relevant suggestions

    # Legacy methods for backward compatibility
    def _get_contextual_message(self, token, evidence_score: float) -> str:
        """Legacy method - redirects to context-aware version."""
        return self._get_contextual_capitalization_message(token, evidence_score)

    def _generate_smart_suggestions(self, token, evidence_score: float, context: dict) -> List[str]:
        """Legacy method - redirects to context-aware version."""
        return self._generate_smart_capitalization_suggestions(token, evidence_score, context)
