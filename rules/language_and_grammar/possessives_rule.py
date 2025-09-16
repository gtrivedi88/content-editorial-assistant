"""
Possessives Rule
Based on IBM Style Guide topic: "Possessives"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PossessivesRule(BaseLanguageRule):
    """
    Checks for incorrect use of possessives, specifically flagging the use
    of apostrophe-s with uppercase abbreviations.
    """
    def _get_rule_type(self) -> str:
        return 'possessives'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for possessive constructions with abbreviations using evidence-based scoring.
        
        Uses sophisticated linguistic and contextual analysis to distinguish between legitimate 
        possessive usage and situations where prepositional phrases would be more appropriate.
        
        Args:
            text: Full document text
            sentences: List of sentences (for compatibility)
            nlp: SpaCy NLP pipeline
            context: Document context information
            
        Returns:
            List of error dictionaries with evidence-based scoring
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for sentence_index, sentence in enumerate(doc.sents):
            # Find all potential possessive issues in this sentence
            for potential_issue in self._find_potential_issues(sentence, doc):
                # Calculate nuanced evidence score
                evidence_score = self._calculate_possessive_evidence(
                    potential_issue, sentence, text, context
                )
                
                # Only create error if evidence suggests it's worth evaluating
                if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                    error = self._create_error(
                        sentence=sentence.text,
                        sentence_index=sentence_index,
                        message=self._get_contextual_possessive_message(potential_issue, evidence_score),
                        suggestions=self._generate_smart_possessive_suggestions(potential_issue, evidence_score, context),
                        severity='medium',
                        text=text,      # Level 2 ✅
                        context=context, # Level 2 ✅
                        evidence_score=evidence_score,  # Your nuanced assessment
                        flagged_text=potential_issue['flagged_text'],
                        span=potential_issue['span']
                    )
                    errors.append(error)
        return errors

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _find_potential_issues(self, sentence, doc) -> List[Dict[str, Any]]:
        """
        Find all potential possessive issues in a sentence.
        
        Args:
            sentence: SpaCy sentence object
            doc: Full SpaCy document
            
        Returns:
            List of potential issue dictionaries containing:
            - abbreviation: The abbreviation token
            - possessive_token: The 's token
            - flagged_text: The full abbreviation's text
            - span: Character span of the issue
            - possessive_object: What is being "possessed" (if found)
        """
        potential_issues = []
        
        for token in sentence:
            if token.text == "'s" and token.i > 0:
                prev_token = doc[token.i - 1]
                
                # Check if this is a potential abbreviation possessive
                if self._detect_potential_abbreviation_possessive(prev_token):
                    # Find what comes after the possessive (the object)
                    possessive_object = None
                    for i in range(token.i + 1, len(doc)):
                        if not doc[i].is_punct and not doc[i].is_space:
                            possessive_object = doc[i]
                            break
                    
                    potential_issue = {
                        'abbreviation': prev_token,
                        'possessive_token': token,
                        'flagged_text': f"{prev_token.text}{token.text}",
                        'span': (prev_token.idx, token.idx + len(token.text)),
                        'possessive_object': possessive_object,
                        'abbreviation_text': prev_token.text,
                        'sentence_context': sentence
                    }
                    potential_issues.append(potential_issue)
        
        return potential_issues

    def _detect_potential_abbreviation_possessive(self, token) -> bool:
        """Detect tokens that could potentially be abbreviation possessives."""
        return token.is_upper and len(token.text) > 1

    def _calculate_possessive_evidence(self, potential_issue: Dict[str, Any], sentence, text: str, context: dict) -> float:
        """
        Calculate evidence score (0.0-1.0) for abbreviation possessive concerns.
        
        Higher scores indicate stronger evidence that the possessive should be flagged.
        Lower scores indicate acceptable usage in specific contexts.
        
        Args:
            potential_issue: Dictionary containing possessive analysis data
            sentence: Sentence containing the possessive
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be flagged)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        if not self._meets_basic_possessive_criteria(potential_issue):
            return 0.0  # No evidence, skip this possessive
        
        evidence_score = self._get_base_possessive_evidence(potential_issue, sentence)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this possessive
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_possessive(evidence_score, potential_issue, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_possessive(evidence_score, potential_issue, context or {})
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_possessive(evidence_score, potential_issue, text, context or {})
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_possessive(evidence_score, potential_issue, context or {})
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    # === POSSESSIVE EVIDENCE METHODS ===

    def _meets_basic_possessive_criteria(self, potential_issue: Dict[str, Any]) -> bool:
        """
        Check if the potential issue meets basic criteria for possessive analysis.
        
        Args:
            potential_issue: Dictionary containing possessive analysis data
            
        Returns:
            bool: True if this possessive should be analyzed further
        """
        abbreviation = potential_issue['abbreviation']
        
        # Must be uppercase abbreviation
        if not abbreviation.is_upper:
            return False
            
        # Must be longer than single character
        if len(abbreviation.text) <= 1:
            return False
        
        # Must have possessive token
        if not potential_issue.get('possessive_token'):
            return False
            
        return True

    def _get_base_possessive_evidence(self, potential_issue: Dict[str, Any], sentence) -> float:
        """
        Get a strong base evidence score for abbreviation possessive usage,
        aligned with the strict IBM Style Guide rule.
        
        The IBM Style Guide is absolute: "Do not use an apostrophe and the letter s ('s) 
        to show the possessive form of an abbreviation". No exceptions for context or type.
        """
        abbreviation_token = potential_issue['abbreviation']
        abbreviation_text = abbreviation_token.text

        # GUARD: Company names like 'IBM' are sometimes allowed possessives in marketing.
        # We can give them a very low score to avoid flagging them, but the style guide
        # generally advises against this as well. For now, we will treat them as exceptions.
        brand_exceptions = {'IBM'}
        if abbreviation_text in brand_exceptions:
            return 0.0  # Do not flag

        # For nearly all other technical abbreviations (API, SDK, HTML, etc.), the rule is absolute.
        # Start with a very high base evidence score.
        # The style guide does not differentiate between types of abbreviations for this rule.
        return 0.9  # High confidence, as per the style guide's direct instruction.

    def _apply_linguistic_clues_possessive(self, evidence_score: float, potential_issue: Dict[str, Any], sentence) -> float:
        """
        Apply linguistic analysis clues for possessive detection.
        
        Analyzes SpaCy-based linguistic features:
        - Part-of-speech analysis
        - Dependency parsing
        - Named entity recognition
        - Possessive object analysis
        - Surrounding context patterns
        
        CRITICAL: When base evidence is high (0.9), the IBM Style Guide rule is absolute.
        Linguistic clues should not override this strict rule.
        """
        
        prev_token = potential_issue['abbreviation']
        possessive_token = potential_issue['possessive_token']
        possessive_object = potential_issue.get('possessive_object')
        
        # === IBM STYLE GUIDE ENFORCEMENT ===
        # If we started with high evidence (0.9), the rule is absolute - don't let linguistic 
        # clues talk us out of flagging clear violations like "API's documentation"
        if evidence_score >= 0.85:  # High base evidence from style guide rule
            # Only allow minimal adjustments for truly exceptional cases
            # The style guide rule should not be overridden by contextual analysis
            original_evidence = evidence_score
        
        # === GRAMMATICAL CLASSIFICATION ===
        # Analyze the fundamental grammatical nature of the token
        # Note: Only apply ONE adjustment per token to avoid triple-penalizing
        
        grammatical_adjustment_applied = False
        
        # Check named entity first (most specific classification)
        if hasattr(prev_token, 'ent_type_') and prev_token.ent_type_:
            ent_type = prev_token.ent_type_
            if ent_type == 'ORG':
                evidence_score -= 0.1  # Organizations commonly use possessives
                grammatical_adjustment_applied = True
            elif ent_type == 'PRODUCT':
                evidence_score -= 0.05  # Products may use possessives for branding
                grammatical_adjustment_applied = True
            elif ent_type == 'GPE':
                evidence_score += 0.05  # Geographic entities often use prepositions
                grammatical_adjustment_applied = True
            elif ent_type == 'FAC':
                evidence_score -= 0.05  # Facilities may appropriately use possessives
                grammatical_adjustment_applied = True
        
        # If no named entity classification, check POS tags
        elif hasattr(prev_token, 'pos_') and not grammatical_adjustment_applied:
            if prev_token.pos_ == 'PROPN':
                evidence_score -= 0.1  # Proper nouns commonly use possessives
                grammatical_adjustment_applied = True
            elif prev_token.pos_ == 'NOUN':
                evidence_score += 0.1  # Generic nouns often better with prepositions
                grammatical_adjustment_applied = True
        
        # === DEPENDENCY ANALYSIS ===
        # Analyze dependency relationships for context clues (independent of grammatical type)
        if hasattr(prev_token, 'dep_'):
            if prev_token.dep_ in ['nsubj', 'nsubjpass']:
                evidence_score -= 0.05  # Subjects often appropriate with possessives
            elif prev_token.dep_ in ['dobj', 'pobj']:
                evidence_score += 0.05  # Objects often better with prepositions
        
        # === MORPHOLOGICAL FEATURES ===
        # Analyze morphological features for additional context
        if hasattr(prev_token, 'morph') and prev_token.morph:
            morph_str = str(prev_token.morph)
            # Number analysis
            if 'Number=Sing' in morph_str:
                evidence_score -= 0.05  # Singular forms often work with possessives
            elif 'Number=Plur' in morph_str:
                evidence_score += 0.05  # Plural forms may be awkward with possessives
        
        # === NAMED ENTITY ANALYSIS COMPLETED ABOVE ===
        # (Moved to grammatical classification section to avoid double-counting)
        
        # === POSSESSIVE OBJECT ANALYSIS ===
        # Look at what the abbreviation "possesses" - what comes after 's
        
        if possessive_object:
            # === OBJECT POS ANALYSIS ===
            # Analyze the part-of-speech of the possessed object
            if hasattr(possessive_object, 'pos_'):
                # Abstract nouns work well with possessives
                if possessive_object.pos_ == 'NOUN':
                    evidence_score -= 0.05  # Nouns generally work with possessives
                # Adjectives may suggest descriptive possessives
                elif possessive_object.pos_ == 'ADJ':
                    evidence_score += 0.05  # Adjectives may be awkward with possessives
            
            # === OBJECT DEPENDENCY ANALYSIS ===
            if hasattr(possessive_object, 'dep_'):
                # Direct objects of possessives are natural
                if possessive_object.dep_ == 'poss':
                    evidence_score -= 0.1  # Proper possessive relationship
                # Attributes and modifiers work well
                elif possessive_object.dep_ in ['attr', 'amod']:
                    evidence_score -= 0.05  # Attributes work with possessives
            
            # === OBJECT TYPE ANALYSIS ===
            # Some objects work better with possessives than others
            
            # Properties, features, attributes work well with possessives
            possession_friendly_objects = {
                'features', 'properties', 'attributes', 'characteristics', 'capabilities',
                'benefits', 'advantages', 'strengths', 'weaknesses', 'limitations',
                'documentation', 'guide', 'manual', 'tutorial', 'reference',
                'headquarters', 'office', 'location', 'address', 'website',
                'mission', 'vision', 'goals', 'objectives', 'strategy',
                'team', 'staff', 'employees', 'members', 'users'
            }
            
            if hasattr(possessive_object, 'lemma_') and possessive_object.lemma_.lower() in possession_friendly_objects:
                evidence_score -= 0.2  # Possessives work well with these objects
            
            # Technical specifications better with prepositional phrases
            specification_objects = {
                'syntax', 'format', 'structure', 'schema', 'specification',
                'configuration', 'settings', 'parameters', 'options',
                'implementation', 'architecture', 'design', 'framework'
            }
            
            if hasattr(possessive_object, 'lemma_') and possessive_object.lemma_.lower() in specification_objects:
                evidence_score += 0.2  # Technical specs better with prepositions
        
        # === SENTENCE CONTEXT ===
        # Look for patterns that suggest formal vs. informal context
        sentence_text = sentence.text.lower()
        
        # Formal language indicators suggest prepositional phrases
        formal_indicators = ['according to', 'in accordance with', 'pursuant to', 'as per']
        if any(indicator in sentence_text for indicator in formal_indicators):
            evidence_score += 0.1  # Formal context prefers prepositional phrases
        
        # Conversational indicators may accept possessives
        conversational_indicators = ['check out', 'take a look', 'let\'s see', 'here\'s']
        if any(indicator in sentence_text for indicator in conversational_indicators):
            evidence_score -= 0.1  # Conversational context more tolerant
        
        # === IBM STYLE GUIDE ENFORCEMENT (FINAL CHECK) ===
        # Prevent linguistic clues from overriding the absolute style guide rule
        if 'original_evidence' in locals() and original_evidence >= 0.85:
            # Don't allow evidence to drop below 0.7 when we started with high confidence
            # The IBM Style Guide rule is absolute and should not be contextually overridden
            evidence_score = max(evidence_score, 0.7)
        
        return evidence_score

    def _apply_structural_clues_possessive(self, evidence_score: float, potential_issue: Dict[str, Any], context: dict) -> float:
        """
        Apply document structure-based clues for possessive detection.
        
        Analyzes document structure and block context:
        - Technical documentation contexts
        - Formal documentation contexts  
        - Conversational contexts
        - List contexts
        """
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL DOCUMENTATION CONTEXTS ===
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.3  # Code context may reference object properties
        elif block_type == 'inline_code':
            evidence_score -= 0.2  # Inline code may show object.property patterns
        
        # === FORMAL DOCUMENTATION CONTEXTS ===
        if block_type in ['table_cell', 'table_header']:
            evidence_score += 0.2  # Tables often formal, prefer prepositional phrases
        elif block_type in ['heading', 'title']:
            evidence_score += 0.1  # Headings often formal
        
        # === CONVERSATIONAL CONTEXTS ===
        if block_type in ['admonition']:
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP']:
                evidence_score -= 0.1  # Notes/tips more conversational
            elif admonition_type in ['WARNING', 'IMPORTANT']:
                evidence_score += 0.1  # Warnings more formal
        
        # === LIST CONTEXTS ===
        if block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.1  # Lists may use compact possessive forms
        
        return evidence_score

    def _apply_semantic_clues_possessive(self, evidence_score: float, potential_issue: Dict[str, Any], text: str, context: dict) -> float:
        """
        Apply semantic and content-type clues for possessive detection.
        
        Analyzes meaning and content type:
        - Content type adjustments (technical, academic, legal, marketing)
        - Domain-specific patterns
        - Document length context
        - Audience level considerations
        - Brand context analysis
        
        CRITICAL: IBM Style Guide rule enforcement - prevent overriding absolute rule.
        """
        
        # Store original evidence for enforcement
        original_evidence = evidence_score
        
        prev_token = potential_issue['abbreviation']
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        if content_type == 'technical':
            evidence_score += 0.1  # Technical writing often prefers formal constructions
        elif content_type == 'api':
            evidence_score += 0.2  # API docs typically formal and precise
        elif content_type == 'academic':
            evidence_score += 0.3  # Academic writing strongly prefers prepositional phrases
        elif content_type == 'legal':
            evidence_score += 0.3  # Legal writing must be unambiguous
        elif content_type == 'marketing':
            evidence_score -= 0.2  # Marketing may use possessives for brand connection
        elif content_type == 'procedural':
            evidence_score += 0.1  # Procedures prefer clarity
        elif content_type == 'narrative':
            evidence_score -= 0.1  # Narrative writing more flexible
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score += 0.1  # Technical domains prefer precision
        elif domain in ['specification', 'documentation']:
            evidence_score += 0.2  # Specification writing prefers formal constructions
        elif domain in ['marketing', 'branding']:
            evidence_score -= 0.2  # Marketing domains accept brand possessives
        elif domain in ['tutorial', 'user-guide']:
            evidence_score -= 0.1  # User guides may be more conversational
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score += 0.1  # Technical audiences prefer precise language
        elif audience in ['beginner', 'general', 'user']:
            evidence_score -= 0.1  # General audiences may prefer simpler possessives
        
        # === DOCUMENT PURPOSE ANALYSIS ===
        # Use enhanced helper methods for semantic analysis
        if self._is_brand_focused_content(text):
            evidence_score -= 0.2  # Brand-focused content often uses possessives
        
        if self._is_specification_documentation(text):
            evidence_score += 0.2  # Specification docs prefer formal constructions
        
        if self._is_api_documentation(text):
            evidence_score += 0.1  # API docs prefer precise prepositional phrases
        
        if self._is_technical_documentation(text):
            evidence_score += 0.2  # Technical reference prefers formal constructions
        
        if self._is_marketing_content_possessive(text, context):
            evidence_score -= 0.3  # Marketing content accepts brand possessives
        
        if self._is_legal_documentation_possessive(text, context):
            evidence_score += 0.3  # Legal contexts strongly prefer prepositional phrases
        
        # === POSSESSIVE DENSITY ANALYSIS ===
        if self._has_high_possessive_density(text):
            evidence_score -= 0.1  # High possessive density suggests informal/brand context
        
        # === IBM STYLE GUIDE ENFORCEMENT (FINAL CHECK) ===
        # Prevent semantic clues from overriding the absolute style guide rule
        if original_evidence >= 0.85:  # Started with high confidence from style guide
            # Don't allow evidence to drop below 0.7 when IBM Style Guide rule applies
            evidence_score = max(evidence_score, 0.7)
        
        return evidence_score

    def _apply_feedback_clues_possessive(self, evidence_score: float, potential_issue: Dict[str, Any], context: dict) -> float:
        """
        Apply clues learned from user feedback patterns for possessive detection.
        
        Incorporates learned patterns from user feedback including:
        - Consistently accepted terms
        - Consistently rejected suggestions  
        - Context-specific patterns
        - Brand possession patterns
        - Frequency-based adjustments
        
        CRITICAL: IBM Style Guide rule enforcement - prevent overriding absolute rule.
        """
        
        # Store original evidence for enforcement
        original_evidence = evidence_score
        
        prev_token = potential_issue['abbreviation']
        feedback_patterns = self._get_cached_feedback_patterns('possessives')
        
        # === ABBREVIATION-SPECIFIC FEEDBACK ===
        abbreviation = prev_token.text.upper()
        
        # Check if this abbreviation commonly has accepted possessive usage
        accepted_possessives = feedback_patterns.get('accepted_possessive_abbreviations', set())
        if abbreviation in accepted_possessives:
            evidence_score -= 0.3  # Users consistently accept possessives for this abbreviation
        
        flagged_possessives = feedback_patterns.get('flagged_possessive_abbreviations', set())
        if abbreviation in flagged_possessives:
            evidence_score += 0.3  # Users consistently flag possessives for this abbreviation
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get(f'{content_type}_possessive_patterns', {})
        
        if abbreviation in context_patterns.get('acceptable', set()):
            evidence_score -= 0.2
        elif abbreviation in context_patterns.get('problematic', set()):
            evidence_score += 0.2
        
        # === BRAND POSSESSION PATTERNS ===
        # Check if this is a commonly accepted brand possessive pattern
        brand_possessives = feedback_patterns.get('accepted_brand_possessives', set())
        if abbreviation in brand_possessives:
            evidence_score -= 0.2  # Brand possessives often accepted
        
        # === IBM STYLE GUIDE ENFORCEMENT (FINAL CHECK) ===
        # Prevent feedback patterns from overriding the absolute style guide rule
        if original_evidence >= 0.85:  # Started with high confidence from style guide
            # Don't allow evidence to drop below 0.7 when IBM Style Guide rule applies
            evidence_score = max(evidence_score, 0.7)
        
        return evidence_score

    # === HELPER METHODS FOR SEMANTIC ANALYSIS ===

    def _is_brand_focused_content(self, text: str) -> bool:
        """Check if text appears to be brand or company-focused content."""
        brand_indicators = [
            'company', 'brand', 'product', 'service', 'solution',
            'headquarters', 'founded', 'established', 'mission', 'vision',
            'about us', 'our company', 'our products', 'our services'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in brand_indicators if indicator in text_lower) >= 2

    def _is_marketing_content_possessive(self, text: str, context: dict) -> bool:
        """
        Detect marketing content that commonly uses possessives for brand connection.
        
        Specialized for possessive analysis - marketing content often uses possessives
        to create emotional attachment (e.g., "Microsoft's innovative solutions").
        """
        # Marketing content indicators specific to possessive usage
        marketing_indicators = {
            'solution', 'innovative', 'leading', 'premier', 'trusted',
            'award-winning', 'industry-leading', 'cutting-edge',
            'customer', 'client', 'partner', 'benefit', 'advantage'
        }
        
        # Brand connection phrases that often use possessives
        brand_connection_phrases = [
            'our company', 'our solution', 'our product', 'our service',
            'company\'s mission', 'brand\'s vision', 'team\'s expertise',
            'organization\'s commitment', 'industry\'s leading'
        ]
        
        text_lower = text.lower()
        marketing_score = sum(1 for indicator in marketing_indicators if indicator in text_lower)
        possessive_marketing_score = sum(1 for phrase in brand_connection_phrases if phrase in text_lower)
        
        # Marketing content type or domain
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        context_marketing = (content_type in {'marketing', 'promotional', 'sales', 'branding'} or
                           domain in {'marketing', 'sales', 'branding', 'advertising'})
        
        return marketing_score >= 3 or possessive_marketing_score >= 1 or context_marketing

    def _is_legal_documentation_possessive(self, text: str, context: dict) -> bool:
        """
        Detect legal content that strongly prefers prepositional phrases over possessives.
        
        Specialized for possessive analysis - legal documents prefer precision.
        """
        # Legal content indicators
        legal_indicators = {
            'accordance', 'pursuant', 'compliance', 'regulation', 'statute',
            'provision', 'clause', 'section', 'agreement', 'contract',
            'license', 'terms', 'conditions', 'liability', 'warranty'
        }
        
        # Possessive-sensitive legal terms
        possessive_sensitive_terms = [
            'intellectual property rights', 'proprietary rights', 'ownership rights',
            'trademark rights', 'copyright ownership', 'patent rights'
        ]
        
        text_lower = text.lower()
        legal_score = sum(1 for indicator in legal_indicators if indicator in text_lower)
        possessive_legal_score = sum(1 for term in possessive_sensitive_terms if term in text_lower)
        
        # Legal content type or domain
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        context_legal = (content_type in {'legal', 'formal', 'compliance', 'contract', 'agreement'} or
                        domain in {'legal', 'compliance', 'regulatory', 'governance'})
        
        return legal_score >= 3 or possessive_legal_score >= 1 or context_legal

    def _has_high_possessive_density(self, text: str) -> bool:
        """
        Check if document has high density of possessive constructions.
        
        High possessive density may indicate informal or brand-focused content
        where possessives are more acceptable.
        
        Args:
            text: Document text
            
        Returns:
            bool: True if high possessive density detected
        """
        # Count possessive patterns
        possessive_patterns = ["'s ", "'s.", "'s,", "'s;", "'s:", "'s!", "'s?"]
        possessive_count = sum(text.count(pattern) for pattern in possessive_patterns)
        
        # Count total words
        word_count = len(text.split())
        
        # Consider high density if > 1% of content has possessives
        return possessive_count > 0 and (possessive_count / max(word_count, 1)) > 0.01

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_possessive_message(self, potential_issue: Dict[str, Any], evidence_score: float) -> str:
        """
        Generate contextual message based on evidence strength and possessive type.
        
        Provides messaging that reflects the absolute nature of the IBM Style Guide rule
        when evidence score is high (indicating clear abbreviation violation).
        """
        
        abbreviation = potential_issue['abbreviation_text']
        
        if evidence_score > 0.8:
            return f"IBM Style Guide: Do not use 's with abbreviations like '{abbreviation}'. Use a prepositional phrase instead."
        elif evidence_score > 0.6:
            return f"Avoid using the possessive 's with the abbreviation '{abbreviation}'. Use 'the [property] of {abbreviation}' instead."
        else:
            return f"Consider using a prepositional phrase instead of '{abbreviation}'s' for clarity."

    def _generate_smart_possessive_suggestions(self, potential_issue: Dict[str, Any], evidence_score: float, context: dict) -> List[str]:
        """
        Generate smart, context-aware suggestions for possessive patterns.
        
        Provides specific guidance that emphasizes the IBM Style Guide rule
        when evidence score is high (indicating clear abbreviation violation).
        """
        
        suggestions = []
        prev_token = potential_issue['abbreviation']
        abbreviation = potential_issue['abbreviation_text']
        possessive_object = potential_issue.get('possessive_object')
        
        # Get the specific object being "possessed" for better suggestions
        object_text = possessive_object.text if possessive_object else "[property]"
        
        # High-confidence suggestions (IBM Style Guide rule)
        if evidence_score > 0.8:
            suggestions.append(f"Replace '{abbreviation}'s {object_text}' with 'the {object_text} of {abbreviation}'.")
            suggestions.append(f"IBM Style Guide rule: Abbreviations like '{abbreviation}' should not use possessive 's.")
            suggestions.append("Consider rephrasing to avoid possessive constructions with abbreviations entirely.")
        
        # Moderate-confidence suggestions
        elif evidence_score > 0.6:
            suggestions.append(f"Use 'the {object_text} of {abbreviation}' instead of '{abbreviation}'s {object_text}'.")
            suggestions.append("Prepositional phrases are preferred over possessives with technical abbreviations.")
            
        # Lower confidence suggestions
        else:
            suggestions.append(f"Consider 'the {object_text} of {abbreviation}' for formal writing.")
            suggestions.append("Prepositional phrases often provide clearer meaning than possessives.")
        
        # Context-specific guidance (only for moderate/low evidence scores)
        if evidence_score <= 0.6 and context:
            content_type = context.get('content_type', 'general')
            if content_type in ['technical', 'api', 'academic']:
                suggestions.append("Technical writing typically prefers prepositional phrases over possessives.")
            elif content_type == 'marketing':
                suggestions.append("Marketing content may accept possessives for brand connection.")
        
        return suggestions[:3]
