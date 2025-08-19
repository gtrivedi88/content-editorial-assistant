"""
Geographic Locations Rule
Based on IBM Style Guide topic: "Geographic locations"
"""
from typing import List, Dict, Any
from .base_references_rule import BaseReferencesRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class GeographicLocationsRule(BaseReferencesRule):
    """
    Uses SpaCy's Named Entity Recognition (NER) to check for correct
    capitalization of geographic locations.
    """
    def _get_rule_type(self) -> str:
        return 'references_geographic_locations'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text to find improperly capitalized geographic locations using evidence-based approach.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for ent in sent.ents:
                # Linguistic Anchor: Check for geographic entities (GPE, LOC, FAC).
                if ent.label_ in ['GPE', 'LOC', 'FAC']:
                    # Check if geographic location has capitalization issues
                    if not all(token.is_title or not token.is_alpha for token in ent):
                        evidence_score = self._calculate_geographic_evidence(
                            ent, sent, text, context
                        )
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_message_geographic(ent.text, evidence_score),
                                suggestions=self._generate_smart_suggestions_geographic(ent.text, context, evidence_score),
                                severity='medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(ent.start_char, ent.end_char),
                                flagged_text=ent.text
                            ))
        return errors
    
    def _calculate_geographic_evidence(self, entity, sentence, text: str, context: Dict[str, Any] = None) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential geographic location violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            entity: The geographic entity/phrase
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
        
        # Geographic-specific guards: Don't flag quoted examples
        if self._is_location_in_actual_quotes(entity, sentence, context):
            return 0.0  # Quoted examples are not geographic capitalization errors
        
        # Don't flag locations that are part of proper names or brands
        if self._is_location_part_of_proper_name(entity, sentence):
            return 0.0  # Brand names, product names with locations
        
        # Apply inherited zero false positive guards
        if self._apply_zero_false_positive_guards_references(first_token, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_geographic_base_evidence_score(entity, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this entity
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_references(evidence_score, first_token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_references(evidence_score, first_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_references(evidence_score, first_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_geographic(evidence_score, entity, context)
        
        # Geographic-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.1  # Geographic capitalization is important but context-dependent
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_geographic_base_evidence_score(self, entity, sentence, context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Complete lowercase like "new york" → 0.7 (very specific)
        - Partial capitalization like "New york" → 0.6 (moderate specificity)
        - Minor issues like "NEW YORK" → 0.5 (needs context analysis)
        """
        if not entity:
            return 0.0
        
        # Check severity of capitalization error
        tokens = list(entity)
        alpha_tokens = [t for t in tokens if t.is_alpha]
        
        if not alpha_tokens:
            return 0.0
        
        incorrectly_capitalized = [t for t in alpha_tokens if not t.is_title]
        error_ratio = len(incorrectly_capitalized) / len(alpha_tokens)
        
        # Enhanced specificity analysis
        if self._is_exact_geographic_violation(entity):
            return 0.7  # Very specific, clear violation (reduced from 0.9)
        elif self._is_pattern_geographic_violation(entity, error_ratio):
            return 0.6  # Pattern-based, moderate specificity (reduced from 0.8)
        elif self._is_minor_geographic_issue(entity, error_ratio):
            return 0.5  # Minor issue, needs context (reduced from 0.7)
        else:
            return 0.4  # Possible issue, needs more evidence (reduced from 0.6)
    
    def _get_contextual_message_geographic(self, location_text: str, evidence_score: float) -> str:
        """
        Generate contextual error message based on evidence strength.
        """
        if evidence_score > 0.85:
            return f"Geographic location '{location_text}' has incorrect capitalization."
        elif evidence_score > 0.6:
            return f"Geographic location '{location_text}' may have incorrect capitalization."
        else:
            return f"Geographic location '{location_text}' could benefit from capitalization review."
    
    def _generate_smart_suggestions_geographic(self, location_text: str, context: Dict[str, Any] = None, evidence_score: float = 0.5) -> List[str]:
        """
        Generate evidence-aware suggestions for geographic location issues.
        """
        suggestions = []
        
        if evidence_score > 0.8:
            suggestions.append(f"Ensure all parts of the location name are capitalized correctly (e.g., '{location_text.title()}').")
            suggestions.append("Geographic locations should use proper title case capitalization.")
        elif evidence_score > 0.6:
            suggestions.append(f"Consider proper capitalization: '{location_text.title()}'.")
            suggestions.append("Geographic names should be capitalized appropriately.")
        else:
            suggestions.append(f"Review capitalization: '{location_text.title()}'.")
        
        return suggestions[:3]
    
    def _is_location_in_actual_quotes(self, entity, sentence, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the location actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not hasattr(entity, 'text') or not hasattr(sentence, 'text'):
            return False
        
        location = entity.text
        sent_text = sentence.text
        
        # Look for quote pairs that actually enclose the location
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
                if location.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_location_part_of_proper_name(self, entity, sentence) -> bool:
        """
        Check if location is part of a brand name or proper noun compound.
        """
        if not hasattr(sentence, 'ents'):
            return False
        
        location_text = entity.text.lower()
        
        # Check if this location is part of a larger organization or product entity
        for ent in sentence.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'PERSON'] and ent != entity:
                if location_text in ent.text.lower():
                    return True  # Location is part of company/product name
        
        # Check for common brand/company patterns
        brand_indicators = ['corp', 'inc', 'ltd', 'company', 'enterprises', 'solutions']
        sentence_text = sentence.text.lower()
        
        for indicator in brand_indicators:
            if indicator in sentence_text and location_text in sentence_text:
                # Check if they're close together (within 5 words)
                words = sentence_text.split()
                try:
                    location_idx = next(i for i, word in enumerate(words) if location_text in word)
                    indicator_idx = next(i for i, word in enumerate(words) if indicator in word)
                    if abs(location_idx - indicator_idx) <= 5:
                        return True
                except StopIteration:
                    continue
        
        return False
    
    def _is_exact_geographic_violation(self, entity) -> bool:
        """
        Check if entity represents an exact geographic capitalization violation.
        """
        tokens = list(entity)
        alpha_tokens = [t for t in tokens if t.is_alpha]
        
        if not alpha_tokens:
            return False
        
        # All tokens lowercase = exact violation
        all_lowercase = all(t.text.islower() for t in alpha_tokens)
        
        # Multi-word location with all lowercase
        if len(alpha_tokens) > 1 and all_lowercase:
            return True
        
        # Single word location that's completely lowercase
        if len(alpha_tokens) == 1 and alpha_tokens[0].text.islower():
            return True
        
        return False
    
    def _is_pattern_geographic_violation(self, entity, error_ratio: float) -> bool:
        """
        Check if entity shows a pattern of geographic capitalization violation.
        """
        # Partial capitalization errors (some words correct, some not)
        if 0.3 <= error_ratio <= 0.7:
            return True
        
        # Check for mixed case issues within single words
        tokens = list(entity)
        for token in tokens:
            if token.is_alpha and len(token.text) > 1:
                # Mixed case like "neW York" or "NEW york"
                if not (token.text.istitle() or token.text.islower() or token.text.isupper()):
                    return True
        
        return False
    
    def _is_minor_geographic_issue(self, entity, error_ratio: float) -> bool:
        """
        Check if entity has minor geographic capitalization issues.
        """
        tokens = list(entity)
        alpha_tokens = [t for t in tokens if t.is_alpha]
        
        # All caps (might be acceptable in some contexts)
        all_caps = all(t.text.isupper() for t in alpha_tokens if len(t.text) > 1)
        
        # Minor ratio of errors
        minor_errors = error_ratio <= 0.3
        
        return all_caps or minor_errors
    
    def _apply_feedback_clues_geographic(self, evidence_score: float, entity, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to geographic locations.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_geographic()
        
        if not hasattr(entity, 'text'):
            return evidence_score
        
        location_text = entity.text.lower()
        
        # Consistently Accepted Terms
        if location_text in feedback_patterns.get('accepted_locations', set()):
            evidence_score -= 0.5  # Users consistently accept this capitalization
        
        # Consistently Rejected Suggestions
        if location_text in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Common location names in different contexts
        location_acceptance = feedback_patterns.get('location_name_acceptance', {})
        acceptance_rate = location_acceptance.get(location_text, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance, likely valid in some contexts
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Location names in different content types
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_location_acceptance', {})
        
        acceptance_rate = content_patterns.get(location_text, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Context-specific acceptance
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        context_patterns = feedback_patterns.get(f'{block_type}_location_patterns', {})
        
        if location_text in context_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif location_text in context_patterns.get('flagged', set()):
            evidence_score += 0.2
        
        # Pattern: Frequency-based adjustment for geographic locations
        term_frequency = feedback_patterns.get('location_term_frequencies', {}).get(location_text, 0)
        if term_frequency > 10:  # Commonly seen location
            acceptance_rate = feedback_patterns.get('location_term_acceptance', {}).get(location_text, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        # Pattern: Multi-word location handling
        if ' ' in location_text:
            multiword_patterns = feedback_patterns.get('multiword_location_acceptance', {})
            acceptance_rate = multiword_patterns.get(location_text, 0.5)
            if acceptance_rate > 0.8:
                evidence_score -= 0.2  # Multi-word locations often have context exceptions
        
        return evidence_score
    
    def _get_cached_feedback_patterns_geographic(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for geographic locations.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_locations': {'usa', 'uk', 'eu'},  # Common abbreviations sometimes acceptable
            'rejected_suggestions': set(),  # Locations users don't want flagged
            'location_name_acceptance': {
                'new york': 0.1,      # Almost always should be capitalized
                'san francisco': 0.1,  # Almost always should be capitalized
                'los angeles': 0.1,    # Almost always should be capitalized
                'united states': 0.2,  # Usually should be capitalized
                'north america': 0.3,  # Sometimes acceptable lowercase in certain contexts
                'usa': 0.7,           # Often acceptable as abbreviation
                'uk': 0.8,            # Often acceptable as abbreviation
                'eu': 0.8             # Often acceptable as abbreviation
            },
            'technical_location_acceptance': {
                'usa': 0.9,           # Very acceptable in technical writing
                'uk': 0.9,            # Very acceptable in technical writing
                'eu': 0.9,            # Very acceptable in technical writing
                'api': 0.0,           # Not a location, technical term
                'sql': 0.0            # Not a location, technical term
            },
            'marketing_location_acceptance': {
                'new york': 0.05,     # Should almost always be capitalized in marketing
                'san francisco': 0.05, # Should almost always be capitalized in marketing
                'usa': 0.5,           # Sometimes acceptable in marketing copy
                'america': 0.3        # Sometimes acceptable but usually capitalized
            },
            'documentation_location_acceptance': {
                'new york': 0.1,      # Should usually be capitalized in docs
                'usa': 0.6,           # More acceptable in documentation
                'api': 0.0,           # Not a location
                'server locations': 0.4  # Technical context may allow variations
            },
            'location_term_frequencies': {
                'new york': 100,      # Very common location
                'san francisco': 80,   # Common location
                'usa': 150,           # Very common abbreviation
                'uk': 120,            # Common abbreviation
                'california': 90      # Common state name
            },
            'location_term_acceptance': {
                'new york': 0.05,     # Almost never acceptable lowercase
                'san francisco': 0.05, # Almost never acceptable lowercase
                'usa': 0.7,           # Often acceptable
                'uk': 0.8,            # Often acceptable
                'california': 0.1     # Rarely acceptable lowercase
            },
            'multiword_location_acceptance': {
                'new york city': 0.05,     # Should be capitalized
                'san francisco bay': 0.1,   # Should be capitalized
                'los angeles county': 0.1,  # Should be capitalized
                'north america': 0.3,       # Sometimes acceptable
                'south america': 0.3        # Sometimes acceptable
            },
            'paragraph_location_patterns': {
                'accepted': {'usa', 'uk', 'eu'},
                'flagged': {'new york', 'california'}
            },
            'heading_location_patterns': {
                'accepted': {'usa', 'uk', 'api'},  # Abbreviations more acceptable in headings
                'flagged': {'new york', 'san francisco'}
            },
            'list_location_patterns': {
                'accepted': {'usa', 'uk', 'ca', 'ny'},  # Abbreviations common in lists
                'flagged': {'new york', 'california'}
            }
        }
