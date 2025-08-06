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
                                message=self._get_contextual_message(token, evidence_score),
                                suggestions=self._generate_smart_suggestions(token, evidence_score, context),
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
        """Apply linguistic analysis clues for capitalization."""
        
        # === ENTITY BOUNDARY ANALYSIS ===
        # Strong entity boundaries indicate higher confidence
        if token.ent_iob_ == 'B':  # Beginning of entity
            evidence_score += 0.1
        elif token.ent_iob_ == 'I':  # Inside entity
            evidence_score += 0.05
        
        # === POS TAG ANALYSIS ===
        # Proper nouns are more likely to need capitalization
        if token.pos_ == 'PROPN':
            evidence_score += 0.2
        elif token.pos_ == 'NOUN' and token.ent_type_:
            evidence_score += 0.1  # Common noun but recognized as entity
        
        # === MORPHOLOGICAL FEATURES ===
        # Check for proper noun morphological indicators
        if hasattr(token, 'morph') and token.morph:
            if 'NounType=Prop' in str(token.morph):
                evidence_score += 0.2
        
        # === LENGTH AND CHARACTER ANALYSIS ===
        # Very short words are less likely to be proper nouns
        if len(token.text) <= 2:
            evidence_score -= 0.3  # Short words less likely proper nouns
        elif len(token.text) >= 8:
            evidence_score += 0.1  # Longer words more likely proper nouns
        
        # === COMMON WORD FILTERING ===
        # Common technical terms that are often misclassified
        common_tech_words = {
            'user', 'data', 'file', 'system', 'admin', 'guest', 'client', 'server',
            'api', 'url', 'http', 'json', 'xml', 'html', 'css', 'sql', 'email',
            'config', 'log', 'debug', 'test', 'code', 'app', 'web', 'site'
        }
        
        if token.text.lower() in common_tech_words:
            evidence_score -= 0.4  # Strong reduction for common tech words
        
        # === BRAND/PRODUCT NAME PATTERNS ===
        # Check for typical brand name patterns
        if self._has_brand_name_pattern(token.text):
            evidence_score += 0.2
        elif self._has_technical_name_pattern(token.text):
            evidence_score -= 0.2  # Technical names may have variant capitalization
        
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
        feedback_patterns = self._get_cached_feedback_patterns()
        
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

    def _has_high_technical_density(self, text: str) -> bool:
        """Check if text has high density of technical terms."""
        words = text.lower().split()
        technical_words = {
            'api', 'server', 'client', 'database', 'system', 'application', 'service',
            'module', 'component', 'interface', 'endpoint', 'protocol', 'configuration',
            'deployment', 'authentication', 'authorization', 'validation', 'optimization',
            'processing', 'analysis', 'implementation', 'integration', 'documentation',
            'json', 'xml', 'html', 'css', 'sql', 'http', 'https', 'url', 'uri',
            'github', 'gitlab', 'docker', 'kubernetes', 'aws', 'azure', 'gcp'
        }
        
        if len(words) == 0:
            return False
        
        technical_count = sum(1 for word in words if word in technical_words)
        technical_ratio = technical_count / len(words)
        
        return technical_ratio > 0.15  # More than 15% technical terms

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

    def _get_cached_feedback_patterns(self):
        """Load feedback patterns from cache or feedback analysis."""
        # This would load from feedback analysis system
        # For now, return patterns based on common capitalization usage
        return {
            'accepted_lowercase_terms': {
                # Technical terms commonly accepted lowercase
                'api', 'url', 'http', 'json', 'xml', 'html', 'css', 'sql',
                'github', 'npm', 'node', 'react', 'vue', 'docker', 'git',
                'linux', 'ubuntu', 'windows', 'macos', 'ios', 'android',
                'app', 'web', 'email', 'wifi', 'bluetooth', 'usb'
            },
            'flagged_for_capitalization': {
                # Terms users commonly correct to capitalize
                'microsoft', 'apple', 'google', 'amazon', 'facebook', 'twitter',
                'netflix', 'spotify', 'youtube', 'instagram', 'linkedin',
                'adobe', 'oracle', 'salesforce', 'github', 'gitlab',
                'new york', 'san francisco', 'los angeles', 'washington'
            },
            'person_patterns': {
                'acceptable_lowercase': set(),
                'needs_capitalization': {
                    'john', 'jane', 'smith', 'johnson', 'williams', 'brown',
                    'davis', 'miller', 'wilson', 'moore', 'taylor', 'anderson'
                }
            },
            'org_patterns': {
                'acceptable_lowercase': {
                    'api', 'github', 'npm', 'docker', 'kubernetes'
                },
                'needs_capitalization': {
                    'microsoft', 'apple', 'google', 'amazon', 'facebook',
                    'netflix', 'adobe', 'oracle', 'salesforce'
                }
            },
            'gpe_patterns': {
                'acceptable_lowercase': set(),
                'needs_capitalization': {
                    'america', 'california', 'texas', 'florida', 'newyork',
                    'london', 'paris', 'tokyo', 'sydney', 'toronto'
                }
            },
            'paragraph_capitalization_patterns': {
                'acceptable_lowercase': {
                    'api', 'json', 'xml', 'html', 'css', 'sql', 'http',
                    'email', 'app', 'web', 'wifi', 'usb'
                },
                'needs_capitalization': {
                    'microsoft', 'apple', 'google', 'amazon'
                }
            },
            'code_block_capitalization_patterns': {
                'acceptable_lowercase': {
                    # Most terms acceptable lowercase in code context
                    'api', 'json', 'xml', 'html', 'css', 'sql', 'http',
                    'github', 'docker', 'kubernetes', 'linux', 'windows',
                    'microsoft', 'apple', 'google', 'amazon'
                },
                'needs_capitalization': set()
            }
        }

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_message(self, token, evidence_score: float) -> str:
        """Generate context-aware error messages for capitalization."""
        
        if evidence_score > 0.8:
            return f"'{token.text}' should be capitalized as it appears to be a proper noun."
        elif evidence_score > 0.5:
            return f"Consider capitalizing '{token.text}' if it refers to a specific entity."
        else:
            return f"'{token.text}' might need capitalization depending on context."

    def _generate_smart_suggestions(self, token, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions for capitalization."""
        
        suggestions = []
        
        # Base suggestion
        suggestions.append(f"Capitalize '{token.text}' to '{token.text.capitalize()}'.")
        
        # Entity-specific advice
        if token.ent_type_ == 'PERSON':
            suggestions.append("Person names should be capitalized.")
        elif token.ent_type_ == 'ORG':
            suggestions.append("Organization names typically require capitalization.")
        elif token.ent_type_ == 'GPE':
            suggestions.append("Geographic and political entities should be capitalized.")
        elif token.ent_type_ == 'PRODUCT':
            suggestions.append("Product names often require capitalization.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            if content_type == 'technical':
                suggestions.append("In technical writing, verify if this is a proper noun or technical term.")
            elif content_type in ['academic', 'legal']:
                suggestions.append("Formal writing requires consistent proper noun capitalization.")
            elif content_type == 'marketing':
                suggestions.append("Consider brand style guidelines for capitalization.")
        
        # Evidence-based advice
        if evidence_score < 0.3:
            suggestions.append("This may be acceptable as-is in technical contexts.")
        elif evidence_score > 0.8:
            suggestions.append("This appears to be a clear proper noun requiring capitalization.")
        
        return suggestions
