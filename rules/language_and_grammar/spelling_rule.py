"""
Spelling Rule
Based on IBM Style Guide topic: "Spelling"
"""
from typing import List, Dict, Any
import re
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class SpellingRule(BaseLanguageRule):
    """
    Checks for common non-US spellings and suggests the preferred US spelling,
    as required by the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'spelling'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for common non-US English spellings.
        Calculates a nuanced evidence score for each detected case using
        linguistic, structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)

        spelling_map = {
            "centre": "center", "colour": "color", "flavour": "flavor",
            "licence": "license", "organise": "organize", "analyse": "analyze",
            "catalogue": "catalog", "dialogue": "dialog", "grey": "gray",
            "behaviour": "behavior", "programme": "program",
        }

        for i, sent in enumerate(doc.sents):
            for non_us, us_spelling in spelling_map.items():
                pattern = r'\b' + re.escape(non_us) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    char_start = sent.start_char + match.start()
                    char_end = sent.start_char + match.end()
                    matched_text = match.group(0)

                    # Try to find a spaCy token that aligns with the match
                    token = None
                    for t in sent:
                        if t.idx == char_start and t.idx + len(t.text) == char_end:
                            token = t
                            break

                    evidence_score = self._calculate_spelling_evidence(
                        non_us=matched_text,
                        us=us_spelling,
                        token=token,
                        sentence=sent,
                        text=text,
                        context=context or {}
                    )

                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_spelling_message(matched_text, us_spelling, evidence_score),
                            suggestions=self._generate_smart_spelling_suggestions(matched_text, us_spelling, evidence_score, sent, context or {}),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(char_start, char_end),
                            flagged_text=matched_text
                        ))

        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_spelling_evidence(self, non_us: str, us: str, token, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for non-US spelling concerns.
        
        Higher scores indicate stronger evidence that non-US spelling should be corrected.
        Lower scores indicate acceptable usage in specific contexts.
        
        Args:
            non_us: The non-US spelling found
            us: The preferred US spelling
            token: The SpaCy token (if found)
            sentence: Sentence containing the spelling
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be corrected)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_spelling_evidence(non_us, us, token, sentence)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this spelling
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_spelling(evidence_score, token, sentence, non_us, us)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_spelling(evidence_score, context, non_us)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_spelling(evidence_score, non_us, us, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_spelling(evidence_score, non_us, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    # === SPELLING EVIDENCE METHODS ===

    def _get_base_spelling_evidence(self, non_us: str, us: str, token, sentence) -> float:
        """Get base evidence score for non-US spelling."""
        
        # === SPELLING TYPE ANALYSIS ===
        # Different non-US spellings have different evidence strengths
        
        # High-priority corrections (common and important)
        high_priority_corrections = {
            'colour': 'color', 'centre': 'center', 'organisation': 'organization',
            'realise': 'realize', 'analyse': 'analyze', 'catalogue': 'catalog'
        }
        
        # Medium-priority corrections (less critical but still important)
        medium_priority_corrections = {
            'grey': 'gray', 'licence': 'license', 'programme': 'program',
            'dialogue': 'dialog', 'flavour': 'flavor', 'behaviour': 'behavior'
        }
        
        # Check priority level
        non_us_lower = non_us.lower()
        if non_us_lower in high_priority_corrections:
            return 0.8  # High evidence for important corrections
        elif non_us_lower in medium_priority_corrections:
            return 0.6  # Medium evidence for less critical corrections
        else:
            return 0.7  # Default evidence for other non-US spellings

    def _apply_linguistic_clues_spelling(self, evidence_score: float, token, sentence, non_us: str, us: str) -> float:
        """
        Apply linguistic analysis clues for spelling detection.
        
        Analyzes SpaCy linguistic features including POS tags, NER, morphological features,
        and surrounding context to determine evidence strength for spelling corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            token: The SpaCy token (if found)
            sentence: Sentence containing the spelling
            non_us: The non-US spelling found
            us: The preferred US spelling
            
        Returns:
            float: Modified evidence score based on linguistic analysis
        """
        
        sentence_text = sentence.text
        
        # === NAMED ENTITY RECOGNITION ===
        # Named entities that are organizations/products should not be corrected
        if token is not None:
            ent_type = getattr(token, 'ent_type_', '')
            
            if ent_type in ['ORG', 'PRODUCT', 'WORK_OF_ART']:
                evidence_score -= 0.8  # Strong reduction for named entities
            elif ent_type in ['PERSON', 'GPE']:
                evidence_score -= 0.6  # Moderate reduction for person/place names
            elif ent_type in ['EVENT', 'LAW']:
                evidence_score -= 0.5  # Some reduction for events/laws
            
            # === CAPITALIZATION PATTERNS ===
            token_text = getattr(token, 'text', '')
            
            # All caps likely an acronym/brand
            if token_text.isupper() and len(token_text) <= 10:
                evidence_score -= 0.6  # Acronyms should not be corrected
            
            # Title case mid-sentence might be a proper noun
            if token_text.istitle() and not getattr(token, 'is_sent_start', False):
                evidence_score -= 0.3  # Proper nouns often maintain original spelling
            
            # === PART-OF-SPEECH ANALYSIS ===
            pos = getattr(token, 'pos_', '')
            
            if pos == 'PROPN':  # Proper noun
                evidence_score -= 0.4  # Proper nouns may maintain original spelling
            elif pos in ['NOUN', 'VERB', 'ADJ']:
                evidence_score += 0.1  # Common words should follow US conventions
            
            # === MORPHOLOGICAL FEATURES ===
            if hasattr(token, 'morph') and token.morph:
                morph_dict = token.morph.to_dict()
                
                # Check for foreign language markers
                if morph_dict.get('Foreign') == 'Yes':
                    evidence_score -= 0.5  # Foreign words may keep original spelling
        
        # === SURROUNDING CONTEXT ===
        # Look for contextual clues in surrounding text
        
        # Quoted text often reports speech or specific names
        if '"' in sentence_text or "'" in sentence_text:
            evidence_score -= 0.2  # Quoted text may preserve original spelling
        
        # Code context indicators
        if '`' in sentence_text:
            evidence_score -= 0.3  # Code examples may use specific spellings
        
        # Parenthetical explanations might preserve original terms
        if '(' in sentence_text and ')' in sentence_text:
            # Check if the spelling is within parentheses
            import re
            paren_content = re.findall(r'\([^)]*\)', sentence_text)
            if any(non_us in content for content in paren_content):
                evidence_score -= 0.2  # Parenthetical content may explain original terms
        
        # === LINGUISTIC PATTERNS ===
        # Check for patterns that suggest intentional non-US usage
        
        # Multiple non-US spellings in the same sentence suggest intentional usage
        other_non_us = ['colour', 'centre', 'organisation', 'realise', 'analyse', 
                       'grey', 'licence', 'programme', 'dialogue', 'flavour', 'behaviour']
        
        sentence_lower = sentence_text.lower()
        non_us_count = sum(1 for word in other_non_us if word in sentence_lower and word != non_us.lower())
        
        if non_us_count >= 1:
            evidence_score -= 0.2  # Multiple non-US spellings suggest intentional style
        elif non_us_count >= 2:
            evidence_score -= 0.4  # Many non-US spellings strongly suggest intentional style
        
        # === COMPOUND WORD ANALYSIS ===
        # Check if this is part of a compound word or technical term
        if '-' in sentence_text:
            # Look for hyphenated compounds containing the word
            import re
            hyphenated_words = re.findall(r'\b[\w]+-[\w-]+\b', sentence_text)
            if any(non_us.lower() in word.lower() for word in hyphenated_words):
                evidence_score -= 0.1  # Compound words may preserve original spelling
        
        # === FREQUENCY AND FAMILIARITY ===
        # More common non-US spellings have higher evidence for correction
        very_common_non_us = ['colour', 'centre', 'organisation', 'realise', 'analyse']
        if non_us.lower() in very_common_non_us:
            evidence_score += 0.1  # Very common non-US spellings should be corrected
        
        return evidence_score

    def _apply_structural_clues_spelling(self, evidence_score: float, context: Dict[str, Any], non_us: str) -> float:
        """
        Apply document structure clues for spelling detection.
        
        Analyzes document structure context including block types, heading levels,
        list depth, and other structural elements to determine appropriate evidence
        adjustments for spelling corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            context: Document context dictionary
            non_us: The non-US spelling found
            
        Returns:
            float: Modified evidence score based on structural analysis
        """
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL DOCUMENTATION CONTEXTS ===
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.9  # Code blocks often contain specific spellings
        elif block_type == 'inline_code':
            evidence_score -= 0.7  # Inline code may reference specific terms
        
        # === HEADING CONTEXT ===
        if block_type == 'heading':
            heading_level = context.get('block_level', 1)
            if heading_level == 1:  # H1 - Main headings
                evidence_score += 0.1  # Main headings should follow US conventions
            elif heading_level == 2:  # H2 - Section headings  
                evidence_score += 0.05  # Section headings should be consistent
            elif heading_level >= 3:  # H3+ - Subsection headings
                evidence_score += 0.02  # Subsection headings less critical
        
        # === LIST CONTEXT ===
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.05  # Lists should use consistent spelling
            
            # Nested list items may be more technical
            if context.get('list_depth', 1) > 1:
                evidence_score -= 0.02  # Nested items may use specific terms
        
        # === TABLE CONTEXT ===
        elif block_type in ['table_cell', 'table_header']:
            if block_type == 'table_header':
                evidence_score += 0.1  # Table headers should be consistent
            else:
                evidence_score += 0.05  # Table cells should follow conventions
        
        # === ADMONITION CONTEXT ===
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score += 0.05  # Notes should be consistent
            elif admonition_type in ['WARNING', 'CAUTION', 'DANGER']:
                evidence_score += 0.1  # Warnings should be clear and consistent
            elif admonition_type in ['IMPORTANT', 'ATTENTION']:
                evidence_score += 0.08  # Important notices should be consistent
        
        # === QUOTE/CITATION CONTEXT ===
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.4  # Quotes may preserve original spelling
        
        # === SIDEBAR/CALLOUT CONTEXT ===
        elif block_type in ['sidebar', 'callout']:
            evidence_score += 0.02  # Side content should be consistent
        
        # === EXAMPLE/SAMPLE CONTEXT ===
        elif block_type in ['example', 'sample']:
            evidence_score -= 0.2  # Examples may show specific spellings
        
        # === FOOTNOTE/REFERENCE CONTEXT ===
        elif block_type in ['footnote', 'reference']:
            evidence_score -= 0.1  # References may preserve original spelling
        
        # === METADATA CONTEXT ===
        elif block_type in ['metadata', 'frontmatter']:
            evidence_score -= 0.3  # Metadata may preserve original terms
        
        return evidence_score

    def _apply_semantic_clues_spelling(self, evidence_score: float, non_us: str, us: str, text: str, context: Dict[str, Any]) -> float:
        """
        Apply semantic and content-type clues for spelling detection.
        
        Analyzes high-level semantic context including content type, domain, audience,
        document purpose, and regional indicators to determine evidence strength
        for spelling corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            non_us: The non-US spelling found
            us: The preferred US spelling
            text: Full document text
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on semantic analysis
        """
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # IBM Style: prefer US spellings broadly; slightly stronger in formal docs
        if content_type == 'technical':
            evidence_score += 0.15  # Technical writing should be consistent
        elif content_type == 'api':
            evidence_score += 0.2  # API docs need global consistency
        elif content_type == 'legal':
            evidence_score += 0.25  # Legal writing must be precise and consistent
        elif content_type == 'academic':
            evidence_score += 0.2  # Academic writing should follow standards
        elif content_type == 'procedural':
            evidence_score += 0.15  # Procedures should be clear and consistent
        elif content_type == 'marketing':
            evidence_score += 0.1  # Marketing should appeal to US audience
        elif content_type == 'narrative':
            evidence_score += 0.05  # Narrative may be more flexible
        elif content_type == 'tutorial':
            evidence_score += 0.15  # Tutorials should be accessible and consistent
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        if domain in ['software', 'engineering', 'devops']:
            evidence_score += 0.1  # Technical domains prefer US standards
        elif domain in ['legal', 'finance', 'medical']:
            evidence_score += 0.15  # Formal domains require consistency
        elif domain in ['compliance', 'regulatory']:
            evidence_score += 0.2  # Regulatory domains need strict consistency
        elif domain in ['user-documentation', 'help']:
            evidence_score += 0.1  # User-facing docs should be consistent
        elif domain in ['international', 'global']:
            evidence_score += 0.05  # International docs may be more flexible
        
        # === AUDIENCE CONSIDERATIONS ===
        if audience in ['beginner', 'general', 'consumer']:
            evidence_score += 0.1  # General audiences need consistency
        elif audience in ['professional', 'business']:
            evidence_score += 0.15  # Professional content should be polished
        elif audience in ['developer', 'technical', 'expert']:
            evidence_score += 0.1  # Technical audiences expect consistency
        elif audience in ['academic', 'scientific']:
            evidence_score += 0.15  # Academic audiences value precision
        elif audience in ['international', 'global']:
            evidence_score += 0.05  # International audiences may be more flexible
        
        # === DOCUMENT LENGTH CONTEXT ===
        doc_length = len(text.split())
        if doc_length < 100:  # Short documents
            evidence_score += 0.05  # Even brief content should be consistent
        elif doc_length > 5000:  # Long documents
            evidence_score += 0.1  # Consistency very important in long docs
        
        # === DOCUMENT PURPOSE ANALYSIS ===
        if self._is_specification_documentation(text):
            evidence_score += 0.2  # Specifications must be precise and consistent
        
        if self._is_policy_documentation(text):
            evidence_score += 0.25  # Policies must be consistent
        
        if self._is_training_content(text):
            evidence_score += 0.15  # Training should be clear and consistent
        
        if self._is_user_documentation(text):
            evidence_score += 0.1  # User docs should be accessible
        
        if self._is_api_documentation(text):
            evidence_score += 0.2  # API docs need global consistency
        
        # === REGIONAL CONTEXT ANALYSIS ===
        # If document shows strong UK indicators, reduce evidence
        uk_indicators = {
            'behaviour', 'colour', 'organise', 'licence', 'programme', 'grey',
            'centre', 'realise', 'analyse', 'catalogue', 'dialogue', 'flavour'
        }
        
        text_lower = text.lower()
        uk_count = sum(1 for word in uk_indicators if word in text_lower)
        
        if uk_count >= 3:
            evidence_score -= 0.2  # Strong UK usage suggests intentional style
        elif uk_count >= 5:
            evidence_score -= 0.3  # Very strong UK usage
        elif uk_count >= 8:
            evidence_score -= 0.4  # Consistent UK style throughout document
        
        # === BRAND/COMPANY CONTEXT ===
        # Check for British company names or references
        british_indicators = [
            'british', 'uk', 'united kingdom', 'england', 'scotland', 'wales',
            'london', 'manchester', 'birmingham', 'glasgow', 'edinburgh',
            'oxford', 'cambridge', 'bbc', 'reuters'
        ]
        
        if any(indicator in text_lower for indicator in british_indicators):
            evidence_score -= 0.1  # British context may justify non-US spelling
        
        # === INDUSTRY STANDARDS ===
        # Some industries may have established spelling conventions
        if self._is_academic_publication(text):
            evidence_score += 0.1  # Academic publications should be consistent
        
        if self._is_technical_specification(text):
            evidence_score += 0.15  # Technical specs should be precise
        
        # === CONSISTENCY ANALYSIS ===
        # Check document-wide spelling consistency
        total_words = len(text.split())
        if total_words > 500:  # Only analyze for substantial documents
            consistency_score = self._analyze_spelling_consistency(text, non_us, us)
            evidence_score += consistency_score  # Adjust based on overall consistency
        
        return evidence_score

    def _apply_feedback_clues_spelling(self, evidence_score: float, non_us: str, context: Dict[str, Any]) -> float:
        """
        Apply feedback patterns for spelling detection.
        
        Incorporates learned patterns from user feedback including acceptance rates,
        context-specific patterns, and correction success rates to refine evidence
        scoring for spelling corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            non_us: The non-US spelling found
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on feedback analysis
        """
        
        feedback_patterns = self._get_cached_feedback_patterns_spelling()
        
        # === WORD-SPECIFIC FEEDBACK ===
        non_us_lower = non_us.lower()
        
        # Check if this specific spelling is commonly accepted by users
        accepted_terms = feedback_patterns.get('accepted_non_us_terms', set())
        if non_us_lower in accepted_terms:
            evidence_score -= 0.4  # Users consistently accept this spelling
        
        flagged_terms = feedback_patterns.get('often_flagged_non_us', set())
        if non_us_lower in flagged_terms:
            evidence_score += 0.2  # Users consistently flag this spelling
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get(f'{content_type}_spelling_patterns', {})
        
        if non_us_lower in context_patterns.get('acceptable', set()):
            evidence_score -= 0.3
        elif non_us_lower in context_patterns.get('problematic', set()):
            evidence_score += 0.2
        
        # === FREQUENCY-BASED PATTERNS ===
        # Pattern: Frequency of this spelling in documents
        spelling_frequency = feedback_patterns.get('spelling_frequencies', {}).get(non_us_lower, 0)
        if spelling_frequency > 20:  # Commonly seen spelling
            acceptance_rate = feedback_patterns.get('spelling_acceptance', {}).get(non_us_lower, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.2  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.3  # Frequently corrected
        
        # === CORRECTION SUCCESS PATTERNS ===
        # Check success rate of corrections for this spelling
        correction_patterns = feedback_patterns.get('correction_success', {})
        correction_success = correction_patterns.get(non_us_lower, 0.5)
        
        if correction_success > 0.8:
            evidence_score += 0.1  # Corrections highly successful
        elif correction_success < 0.3:
            evidence_score -= 0.2  # Corrections often rejected
        
        # === BRAND/PRODUCT NAME PATTERNS ===
        # Check if this is a known brand/product that uses non-US spelling
        brand_patterns = feedback_patterns.get('brand_spellings', set())
        if non_us_lower in brand_patterns:
            evidence_score -= 0.5  # Brand names should not be corrected
        
        # === REGIONAL PREFERENCE PATTERNS ===
        # Check if users in certain contexts prefer this spelling
        regional_patterns = feedback_patterns.get('regional_preferences', {})
        if non_us_lower in regional_patterns.get('uk_preferred', set()):
            # Check if document context suggests UK audience
            domain = context.get('domain', 'general')
            if domain in ['international', 'global']:
                evidence_score -= 0.1  # International docs may prefer original spelling
        
        return evidence_score

    def _get_cached_feedback_patterns_spelling(self) -> Dict[str, Any]:
        """Load feedback patterns from cache or feedback analysis for spelling."""
        # This would load from feedback analysis system
        # For now, return patterns based on common spelling usage
        return {
            'accepted_non_us_terms': {
                # Common product/project names that intentionally use British variants
                'greylog', 'dialogflow', 'colour-picker', 'grey-scale',
                'centre-align', 'behaviour-driven'  # Technical compound terms
            },
            'often_flagged_non_us': {
                # Spellings commonly flagged by users for correction
                'colour', 'organise', 'programme', 'centre', 'realise', 'analyse'
            },
            'technical_spelling_patterns': {
                'acceptable': {
                    # Spellings acceptable in technical contexts
                    'greylog', 'dialogflow', 'colour-picker', 'grey-scale'
                },
                'problematic': {
                    # Spellings problematic even in technical contexts
                    'colour', 'centre', 'organisation'
                }
            },
            'academic_spelling_patterns': {
                'acceptable': {
                    # Spellings acceptable in academic contexts
                    'honour', 'favour'  # May be acceptable in academic citations
                },
                'problematic': {
                    # Spellings problematic in academic contexts
                    'colour', 'centre', 'realise', 'analyse'
                }
            },
            'marketing_spelling_patterns': {
                'acceptable': {
                    # Spellings acceptable in marketing contexts
                    # (Usually none - marketing should be consistent)
                },
                'problematic': {
                    # Spellings problematic in marketing contexts
                    'colour', 'centre', 'programme', 'grey'
                }
            },
            'spelling_frequencies': {
                # Frequency of spelling usage (would be calculated from corpus)
                'colour': 150, 'centre': 100, 'organisation': 80, 'programme': 90,
                'grey': 70, 'realise': 60, 'analyse': 85
            },
            'spelling_acceptance': {
                # Historical acceptance rates (would be calculated from feedback)
                'colour': 0.2, 'centre': 0.3, 'organisation': 0.1, 'programme': 0.2,
                'grey': 0.4, 'greylog': 0.9, 'dialogflow': 0.95
            },
            'correction_success': {
                # Success rate of correction suggestions
                'colour': 0.8, 'centre': 0.9, 'organisation': 0.85, 'programme': 0.75,
                'grey': 0.6, 'greylog': 0.1, 'dialogflow': 0.1
            },
            'brand_spellings': {
                # Known brand/product names that use non-US spelling
                'greylog', 'dialogflow', 'grey-scale', 'colour-picker',
                'centre-point', 'behaviour-driven'
            },
            'regional_preferences': {
                'uk_preferred': {
                    # Spellings that may be preferred in UK contexts
                    'colour', 'centre', 'organisation', 'realise', 'honour'
                }
            }
        }

    # === HELPER METHODS FOR SEMANTIC ANALYSIS ===

    def _is_specification_documentation(self, text: str) -> bool:
        """Check if text appears to be specification documentation."""
        spec_indicators = [
            'specification', 'spec', 'standard', 'protocol', 'definition',
            'schema', 'format', 'syntax', 'implementation', 'reference',
            'requirements', 'compliance'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in spec_indicators if indicator in text_lower) >= 2

    def _is_policy_documentation(self, text: str) -> bool:
        """Check if text appears to be policy documentation."""
        policy_indicators = [
            'policy', 'policies', 'guideline', 'guidelines', 'standard',
            'standards', 'procedure', 'procedures', 'compliance', 'regulation',
            'code of conduct', 'best practice', 'governance'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in policy_indicators if indicator in text_lower) >= 2

    def _is_training_content(self, text: str) -> bool:
        """Check if text appears to be training content."""
        training_indicators = [
            'training', 'tutorial', 'course', 'lesson', 'workshop',
            'learning', 'education', 'instruction', 'guide', 'walkthrough',
            'getting started', 'how to', 'step by step'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in training_indicators if indicator in text_lower) >= 2

    def _is_user_documentation(self, text: str) -> bool:
        """Check if text appears to be user-facing documentation."""
        user_doc_indicators = [
            'user guide', 'user manual', 'help', 'documentation',
            'instructions', 'how to use', 'getting started', 'quick start',
            'user interface', 'end user', 'customer', 'client'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in user_doc_indicators if indicator in text_lower) >= 2

    def _is_api_documentation(self, text: str) -> bool:
        """Check if text appears to be API documentation."""
        api_indicators = [
            'api', 'endpoint', 'method', 'parameter', 'request', 'response',
            'authentication', 'authorization', 'rest', 'graphql', 'sdk',
            'integration', 'webhook', 'callback'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in api_indicators if indicator in text_lower) >= 3

    def _is_academic_publication(self, text: str) -> bool:
        """Check if text appears to be an academic publication."""
        academic_indicators = [
            'abstract', 'introduction', 'methodology', 'conclusion', 'references',
            'bibliography', 'citation', 'journal', 'conference', 'paper',
            'research', 'study', 'analysis', 'findings'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in academic_indicators if indicator in text_lower) >= 3

    def _is_technical_specification(self, text: str) -> bool:
        """Check if text appears to be a technical specification."""
        tech_spec_indicators = [
            'specification', 'requirements', 'architecture', 'design',
            'implementation', 'protocol', 'algorithm', 'interface',
            'system', 'component', 'module', 'framework'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in tech_spec_indicators if indicator in text_lower) >= 4

    def _analyze_spelling_consistency(self, text: str, non_us: str, us: str) -> float:
        """
        Analyze overall spelling consistency in the document.
        
        Returns adjustment factor based on document-wide spelling patterns.
        """
        text_lower = text.lower()
        
        # Count US vs non-US spelling variants
        us_variants = [us.lower()]
        non_us_variants = [non_us.lower()]
        
        # Add related variants for comprehensive analysis
        spelling_pairs = {
            'color': 'colour', 'center': 'centre', 'organize': 'organise',
            'realize': 'realise', 'analyze': 'analyse', 'catalog': 'catalogue',
            'dialog': 'dialogue', 'flavor': 'flavour', 'behavior': 'behaviour',
            'gray': 'grey', 'license': 'licence', 'program': 'programme'
        }
        
        us_count = 0
        non_us_count = 0
        
        for us_word, non_us_word in spelling_pairs.items():
            us_count += text_lower.count(us_word)
            non_us_count += text_lower.count(non_us_word)
        
        total_count = us_count + non_us_count
        if total_count == 0:
            return 0.0  # No evidence either way
        
        # Calculate consistency factor
        us_ratio = us_count / total_count
        
        if us_ratio > 0.8:
            return 0.1  # Document mostly uses US spelling - correct this one too
        elif us_ratio < 0.2:
            return -0.2  # Document mostly uses non-US spelling - may be intentional
        else:
            return 0.05  # Mixed usage - slight preference for consistency

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_spelling_message(self, non_us: str, us: str, evidence_score: float) -> str:
        """Generate context-aware error messages for spelling patterns."""
        
        if evidence_score > 0.9:
            return f"Non-US spelling '{non_us}' detected. IBM Style prefers US spelling: '{us}'."
        elif evidence_score > 0.7:
            return f"Consider using US spelling '{us}' instead of '{non_us}'."
        elif evidence_score > 0.5:
            return f"US spelling '{us}' is preferred over '{non_us}' for consistency."
        else:
            return f"The spelling '{non_us}' may benefit from US variant '{us}' for consistency."

    def _generate_smart_spelling_suggestions(self, non_us: str, us: str, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for spelling patterns."""
        
        suggestions = []
        
        # Base suggestions based on evidence strength
        if evidence_score > 0.8:
            suggestions.append(f"Replace '{non_us}' with '{us}' to follow US spelling conventions.")
            suggestions.append("Ensure consistent US spelling throughout the document.")
        else:
            suggestions.append(f"Consider using '{us}' instead of '{non_us}' for consistency.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type in ['technical', 'api']:
                suggestions.append("Technical documentation should use consistent US spelling for global audience.")
            elif content_type in ['academic', 'legal']:
                suggestions.append("Formal writing should follow established US spelling conventions.")
            elif content_type == 'marketing':
                suggestions.append("Marketing content should use US spelling for target audience.")
        
        # Special handling for quoted/code contexts
        sentence_text = getattr(sentence, 'text', '')
        if '"' in sentence_text or "'" in sentence_text:
            suggestions.append("If this is a quoted name or reference, consider leaving as-is.")
        elif '`' in sentence_text:
            suggestions.append("If this is code or a technical term, verify it's not a specific identifier.")
        
        # Brand/product name handling
        if any(char.isupper() for char in non_us) or '-' in non_us:
            suggestions.append("If this is a brand or product name, the original spelling may be correct.")
        
        return suggestions[:3]
