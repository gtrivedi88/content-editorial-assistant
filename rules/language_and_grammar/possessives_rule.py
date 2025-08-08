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
        Analyzes sentences for possessive constructions with abbreviations using evidence-based scoring.
        Uses sophisticated linguistic and contextual analysis to distinguish between legitimate 
        possessive usage and situations where prepositional phrases would be more appropriate.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.text == "'s":
                    if token.i > 0:
                        prev_token = doc[token.i - 1]
                        
                        # Detect potential abbreviation possessive
                        potential_possessive = self._detect_potential_abbreviation_possessive(prev_token)
                        
                        if potential_possessive:
                            # Calculate evidence score for this possessive construction
                            evidence_score = self._calculate_possessive_evidence(
                                prev_token, token, sent, text, context
                            )
                            
                            # Only create error if evidence suggests it's worth flagging
                            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                                errors.append(self._create_error(
                                    sentence=sent.text,
                                    sentence_index=i,
                                    message=self._get_contextual_possessive_message(prev_token, evidence_score),
                                    suggestions=self._generate_smart_possessive_suggestions(prev_token, evidence_score, context),
                                    severity='medium',
                                    text=text,
                                    context=context,
                                    evidence_score=evidence_score,  # Your nuanced assessment
                                    span=(prev_token.idx, token.idx + len(token.text)),
                                    flagged_text=f"{prev_token.text}{token.text}"
                                ))
        return errors

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _detect_potential_abbreviation_possessive(self, token) -> bool:
        """Detect tokens that could potentially be abbreviation possessives."""
        return token.is_upper and len(token.text) > 1

    def _calculate_possessive_evidence(self, prev_token, possessive_token, sentence, text: str, context: dict) -> float:
        """
        Calculate evidence score (0.0-1.0) for abbreviation possessive concerns.
        
        Higher scores indicate stronger evidence that the possessive should be flagged.
        Lower scores indicate acceptable usage in specific contexts.
        
        Args:
            prev_token: The abbreviation token before 's
            possessive_token: The 's token
            sentence: Sentence containing the possessive
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be flagged)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_possessive_evidence(prev_token, sentence)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this possessive
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_possessive(evidence_score, prev_token, possessive_token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_possessive(evidence_score, prev_token, context or {})
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_possessive(evidence_score, prev_token, text, context or {})
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_possessive(evidence_score, prev_token, context or {})
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    # === POSSESSIVE EVIDENCE METHODS ===

    def _get_base_possessive_evidence(self, prev_token, sentence) -> float:
        """Get base evidence score for abbreviation possessive usage."""
        
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

    def _apply_linguistic_clues_possessive(self, evidence_score: float, prev_token, possessive_token, sentence) -> float:
        """Apply linguistic analysis clues for possessive detection."""
        
        # === POSSESSIVE OBJECT ANALYSIS ===
        # Look at what the abbreviation "possesses" - what comes after 's
        doc = sentence.doc
        possessive_object = None
        
        # Find the object being possessed (next meaningful token)
        for i in range(possessive_token.i + 1, len(doc)):
            if not doc[i].is_punct and not doc[i].is_space:
                possessive_object = doc[i]
                break
        
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
            
            if possessive_object.lemma_.lower() in possession_friendly_objects:
                evidence_score -= 0.2  # Possessives work well with these objects
            
            # Technical specifications better with prepositional phrases
            specification_objects = {
                'syntax', 'format', 'structure', 'schema', 'specification',
                'configuration', 'settings', 'parameters', 'options',
                'implementation', 'architecture', 'design', 'framework'
            }
            
            if possessive_object.lemma_.lower() in specification_objects:
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

    def _apply_structural_clues_possessive(self, evidence_score: float, prev_token, context: dict) -> float:
        """Apply document structure clues for possessive detection."""
        
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

    def _apply_semantic_clues_possessive(self, evidence_score: float, prev_token, text: str, context: dict) -> float:
        """Apply semantic and content-type clues for possessive detection."""
        
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

    def _apply_feedback_clues_possessive(self, evidence_score: float, prev_token, context: dict) -> float:
        """Apply feedback patterns for possessive detection."""
        
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

    def _get_contextual_possessive_message(self, prev_token, evidence_score: float) -> str:
        """Generate context-aware error messages for possessive patterns."""
        
        abbreviation = prev_token.text
        
        if evidence_score > 0.8:
            return f"Avoid using the possessive 's with the abbreviation '{abbreviation}'."
        elif evidence_score > 0.5:
            return f"Consider using a prepositional phrase instead of '{abbreviation}'s'."
        else:
            return f"The possessive '{abbreviation}'s' may be acceptable but consider a prepositional phrase for clarity."

    def _generate_smart_possessive_suggestions(self, prev_token, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions for possessive patterns."""
        
        suggestions = []
        abbreviation = prev_token.text
        
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
