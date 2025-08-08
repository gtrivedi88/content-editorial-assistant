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
        Get base evidence score for abbreviation possessive usage.
        
        Analyzes the type of abbreviation and provides initial evidence assessment.
        """
        
        prev_token = potential_issue['abbreviation']
        abbreviation = prev_token.text.upper()
        
        # === ENTITY TYPE ANALYSIS ===
        # Check if this is a named entity (organization, person, etc.)
        if prev_token.ent_type_ in ['ORG', 'PERSON', 'GPE']:
            return 0.2  # Low evidence - named entities often use possessives appropriately
        
        # === BRAND/PRODUCT NAME ANALYSIS ===
        # Well-known brand names and products often use possessives appropriately
        brand_names = {
            'IBM', 'NASA', 'GOOGLE', 'MICROSOFT', 'APPLE', 'ORACLE', 'SAP',
            'AWS', 'AZURE', 'GCP', 'API', 'SDK', 'IDE', 'OS', 'CPU', 'GPU',
            'SQL', 'JSON', 'XML', 'HTML', 'CSS', 'REST', 'SOAP', 'HTTP', 'HTTPS'
        }
        
        if abbreviation in brand_names:
            return 0.3  # Low evidence - brand names commonly use possessives
        
        # === TECHNICAL ACRONYM ANALYSIS ===
        # Technical acronyms in certain contexts may be acceptable
        technical_acronyms = {
            'API', 'SDK', 'IDE', 'OS', 'CPU', 'GPU', 'RAM', 'ROM', 'SSD', 'HDD',
            'SQL', 'JSON', 'XML', 'HTML', 'CSS', 'JS', 'PHP', 'PDF', 'CSV',
            'REST', 'SOAP', 'HTTP', 'HTTPS', 'FTP', 'SSH', 'SSL', 'TLS',
            'DNS', 'IP', 'TCP', 'UDP', 'VPN', 'LAN', 'WAN', 'WiFi', 'USB'
        }
        
        if abbreviation in technical_acronyms:
            return 0.5  # Moderate evidence - technical acronyms often better with prepositions
        
        # === GENERIC ABBREVIATIONS ===
        # Generic abbreviations typically should use prepositional phrases
        return 0.7  # High evidence for generic abbreviations

    def _apply_linguistic_clues_possessive(self, evidence_score: float, potential_issue: Dict[str, Any], sentence) -> float:
        """
        Apply linguistic analysis clues for possessive detection.
        
        Analyzes SpaCy-based linguistic features:
        - Part-of-speech analysis
        - Dependency parsing
        - Named entity recognition
        - Possessive object analysis
        - Surrounding context patterns
        """
        
        prev_token = potential_issue['abbreviation']
        possessive_token = potential_issue['possessive_token']
        possessive_object = potential_issue.get('possessive_object')
        
        # === POSSESSIVE OBJECT ANALYSIS ===
        # Look at what the abbreviation "possesses" - what comes after 's
        
        if possessive_object:
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
        """
        
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
        
        # === BRAND CONTEXT ANALYSIS ===
        if self._is_brand_focused_content(text):
            evidence_score -= 0.2  # Brand-focused content often uses possessives
        
        if self._is_specification_documentation(text):
            evidence_score += 0.2  # Specification docs prefer formal constructions
        
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
        """
        
        prev_token = potential_issue['abbreviation']
        feedback_patterns = self._get_cached_feedback_patterns_possessive()
        
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

    def _is_specification_documentation(self, text: str) -> bool:
        """Check if text appears to be specification documentation."""
        spec_indicators = [
            'specification', 'spec', 'format', 'syntax', 'structure',
            'schema', 'standard', 'protocol', 'implementation',
            'definition', 'reference', 'documentation'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in spec_indicators if indicator in text_lower) >= 3

    def _get_cached_feedback_patterns_possessive(self):
        """Load feedback patterns from cache or feedback analysis for possessives."""
        # This would load from feedback analysis system
        # For now, return patterns based on common possessive usage
        return {
            'accepted_possessive_abbreviations': {
                # Brand names commonly accepted with possessives
                'IBM', 'NASA', 'GOOGLE', 'MICROSOFT', 'APPLE', 'ORACLE',
                'AWS', 'AZURE', 'GCP'
            },
            'flagged_possessive_abbreviations': {
                # Technical acronyms commonly flagged with possessives
                'JSON', 'XML', 'HTML', 'CSS', 'SQL', 'REST', 'HTTP'
            },
            'technical_possessive_patterns': {
                'acceptable': {
                    # Possessives acceptable in technical contexts
                    'API', 'SDK', 'IDE', 'OS'
                },
                'problematic': {
                    # Possessives problematic in technical contexts
                    'JSON', 'XML', 'HTML', 'CSS', 'SQL'
                }
            },
            'marketing_possessive_patterns': {
                'acceptable': {
                    # Possessives acceptable in marketing contexts
                    'IBM', 'GOOGLE', 'MICROSOFT', 'APPLE', 'AWS', 'API'
                },
                'problematic': {
                    # Possessives problematic even in marketing
                    'HTTP', 'HTTPS', 'FTP', 'SSH'
                }
            },
            'accepted_brand_possessives': {
                # Brand possessives commonly accepted across contexts
                'IBM', 'NASA', 'GOOGLE', 'MICROSOFT', 'APPLE', 'ORACLE',
                'AWS', 'AZURE', 'GCP'
            }
        }

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_possessive_message(self, potential_issue: Dict[str, Any], evidence_score: float) -> str:
        """
        Generate contextual message based on evidence strength and possessive type.
        
        Provides nuanced messaging that adapts to:
        - Evidence strength (high/medium/low confidence)
        - Abbreviation type and entity classification
        - Context-specific considerations
        """
        
        abbreviation = potential_issue['abbreviation_text']
        
        if evidence_score > 0.8:
            return f"Avoid using the possessive 's with the abbreviation '{abbreviation}'."
        elif evidence_score > 0.5:
            return f"Consider using a prepositional phrase instead of '{abbreviation}'s'."
        else:
            return f"The possessive '{abbreviation}'s' may be acceptable but consider a prepositional phrase for clarity."

    def _generate_smart_possessive_suggestions(self, potential_issue: Dict[str, Any], evidence_score: float, context: dict) -> List[str]:
        """
        Generate smart, context-aware suggestions for possessive patterns.
        
        Provides specific guidance based on:
        - Evidence strength and confidence level
        - Content type and writing context  
        - Abbreviation-specific usage patterns
        - Domain and audience considerations
        """
        
        suggestions = []
        prev_token = potential_issue['abbreviation']
        abbreviation = potential_issue['abbreviation_text']
        
        # Base suggestions based on evidence strength
        if evidence_score > 0.7:
            suggestions.append(f"Use a prepositional phrase: 'the [property] of {abbreviation}' instead of '{abbreviation}'s [property]'.")
            suggestions.append("Rewrite to avoid the possessive construction entirely.")
        else:
            suggestions.append(f"Consider using 'the [property] of {abbreviation}' for formal writing.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type in ['technical', 'api', 'academic']:
                suggestions.append("Technical and academic writing typically prefer prepositional phrases.")
            elif content_type == 'marketing':
                suggestions.append("Brand possessives may be acceptable in marketing contexts.")
            elif content_type == 'specification':
                suggestions.append("Specification documents should use precise prepositional constructions.")
        
        # Abbreviation-specific advice
        if prev_token.ent_type_ in ['ORG', 'PERSON']:
            suggestions.append("Named entities may appropriately use possessive forms.")
        
        return suggestions[:3]
