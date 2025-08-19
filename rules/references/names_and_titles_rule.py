"""
Names and Titles Rule
Based on IBM Style Guide topic: "Names and titles"
"""
from typing import List, Dict, Any
from .base_references_rule import BaseReferencesRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NamesAndTitlesRule(BaseReferencesRule):
    """
    Checks for correct capitalization of professional titles, distinguishing
    between titles used with names versus standalone usage.
    """
    def _get_rule_type(self) -> str:
        return 'references_names_titles'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for incorrect capitalization of professional titles using evidence-based approach.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        professional_titles = {"ceo", "director", "manager", "president", "officer", "engineer"}

        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.lemma_.lower() in professional_titles:
                    # Enhanced detection: Check if the title is with a person's name using multiple indicators
                    is_with_name = self._is_title_with_person_name(token, sent)
                    
                    # Rule: Titles with names should be capitalized.
                    if is_with_name and not token.is_title:
                        evidence_score = self._calculate_title_evidence(
                            token, sent, text, context, issue_type='title_with_name_uncapitalized'
                        )
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text, 
                                sentence_index=i,
                                message=self._get_contextual_message_title(token.text, evidence_score, 'title_with_name_uncapitalized'),
                                suggestions=self._generate_smart_suggestions_title(token.text, context, evidence_score, 'title_with_name_uncapitalized'),
                                severity='medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))
                    
                    # Rule: Standalone titles should be lowercase.
                    elif not is_with_name and token.is_title and self._is_standalone_title_context(token, sent):
                        evidence_score = self._calculate_title_evidence(
                            token, sent, text, context, issue_type='standalone_title_capitalized'
                        )
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text, 
                                sentence_index=i,
                                message=self._get_contextual_message_title(token.text, evidence_score, 'standalone_title_capitalized'),
                                suggestions=self._generate_smart_suggestions_title(token.text, context, evidence_score, 'standalone_title_capitalized'),
                                severity='medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))
        return errors
    
    def _calculate_title_evidence(self, token, sentence, text: str, context: Dict[str, Any] = None, issue_type: str = 'general') -> float:
        """
        Calculate evidence score (0.0-1.0) for potential professional title violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            token: The title token/phrase
            sentence: Sentence containing the token
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            issue_type: Type of title issue (title_with_name_uncapitalized, standalone_title_capitalized)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return 0.0  # Code has its own rules
        
        # Don't flag technical identifiers, URLs, file paths
        if hasattr(token, 'like_url') and token.like_url:
            return 0.0
        if hasattr(token, 'text') and ('/' in token.text or '\\' in token.text):
            return 0.0
        
        # Title-specific guards: Don't flag quoted examples
        if self._is_title_in_actual_quotes(token, sentence, context):
            return 0.0  # Quoted examples are not title capitalization errors
        
        # Don't flag titles that are part of proper names or brands
        if self._is_title_part_of_proper_name(token, sentence):
            return 0.0  # Brand names, product names with titles
        
        # Don't flag titles in academic citations or references
        if self._is_title_in_citation_context(token, sentence, context):
            return 0.0  # Academic papers, book titles, etc.
        
        # Apply inherited zero false positive guards
        if self._apply_zero_false_positive_guards_references(token, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_title_base_evidence_score(token, sentence, context, issue_type)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this token
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_references(evidence_score, token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_references(evidence_score, token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_references(evidence_score, token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_titles(evidence_score, token, context, issue_type)
        
        # Title-specific final adjustments (moderate to avoid evidence inflation)
        if issue_type == 'title_with_name_uncapitalized':
            evidence_score += 0.1  # Important for professional presentation
        elif issue_type == 'standalone_title_capitalized':
            evidence_score += 0.05  # Consistency important but context-dependent
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_title_base_evidence_score(self, token, sentence, context: Dict[str, Any] = None, issue_type: str = 'general') -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Executive titles with names like "ceo john" → 0.7 (very specific)
        - Standalone capitalized titles like "Manager" → 0.6 (moderate specificity)
        - Common titles in complex contexts → 0.5 (needs context analysis)
        """
        if not self._meets_basic_criteria_references(token):
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_title_violation(token, issue_type):
            return 0.7  # Very specific, clear violation (reduced from 0.9)
        elif self._is_pattern_title_violation(token, sentence, issue_type):
            return 0.6  # Pattern-based, moderate specificity (reduced from 0.8)
        elif self._is_minor_title_issue(token, sentence, issue_type):
            return 0.5  # Minor issue, needs context (reduced from 0.7)
        else:
            return 0.4  # Possible issue, needs more evidence (reduced from 0.6)
    
    def _get_contextual_message_title(self, title_text: str, evidence_score: float, issue_type: str) -> str:
        """
        Generate contextual error message based on evidence strength.
        """
        if issue_type == 'title_with_name_uncapitalized':
            if evidence_score > 0.85:
                return f"Professional title '{title_text}' should be capitalized when used with a name."
            elif evidence_score > 0.6:
                return f"Consider capitalizing the title '{title_text}' when used with a name."
            else:
                return f"Title '{title_text}' may need capitalization when used with a name."
                
        elif issue_type == 'standalone_title_capitalized':
            if evidence_score > 0.85:
                return f"Standalone professional title '{title_text}' should be lowercase."
            elif evidence_score > 0.6:
                return f"Consider using lowercase for the standalone title '{title_text}'."
            else:
                return f"Standalone title '{title_text}' may need lowercase formatting."
        
        return f"Title formatting issue detected with '{title_text}'."
    
    def _generate_smart_suggestions_title(self, title_text: str, context: Dict[str, Any] = None, evidence_score: float = 0.5, issue_type: str = 'general') -> List[str]:
        """
        Generate evidence-aware suggestions for title issues.
        """
        suggestions = []
        
        if issue_type == 'title_with_name_uncapitalized':
            if evidence_score > 0.8:
                suggestions.append(f"Capitalize the title: '{title_text.title()}'.")
                suggestions.append("Professional titles should be capitalized when used with names.")
            elif evidence_score > 0.6:
                suggestions.append(f"Consider capitalizing: '{title_text.title()}'.")
                suggestions.append("Titles with names are typically capitalized.")
            else:
                suggestions.append(f"Review capitalization: '{title_text.title()}'.")
                
        elif issue_type == 'standalone_title_capitalized':
            if evidence_score > 0.8:
                suggestions.append(f"Use lowercase for the title: '{title_text.lower()}'.")
                suggestions.append("Standalone professional titles should be lowercase.")
            elif evidence_score > 0.6:
                suggestions.append(f"Consider lowercase: '{title_text.lower()}'.")
                suggestions.append("Standalone titles are typically lowercase.")
            else:
                suggestions.append(f"Review formatting: '{title_text.lower()}'.")
        
        return suggestions[:3]
    
    def _is_title_with_person_name(self, token, sentence) -> bool:
        """
        Enhanced check: Is the title used with a person's name?
        Uses multiple indicators beyond just dependency parsing.
        """
        # Original check: appositional modifier with person entity
        if hasattr(token, 'head') and hasattr(token.head, 'ent_type_'):
            if token.head.ent_type_ == 'PERSON' and token.dep_ == 'appos':
                return True
        
        # Check for PERSON entities nearby (within 3 tokens)
        for ent in sentence.ents:
            if ent.label_ == 'PERSON':
                # Check if title token is close to person entity
                if abs(token.i - ent.start) <= 3 or abs(token.i - ent.end) <= 3:
                    return True
        
        # Check for proper nouns nearby that look like names
        for other_token in sentence:
            if (other_token.pos_ == 'PROPN' and 
                abs(token.i - other_token.i) <= 2 and 
                other_token.text[0].isupper() and 
                len(other_token.text) > 2):
                # Additional check: not likely to be organization/place
                if not any(indicator in sentence.text.lower() 
                          for indicator in ['company', 'corp', 'inc', 'ltd', 'street', 'road', 'city']):
                    return True
        
        # Check for title patterns: "Title FirstName LastName"
        if token.i < len(sentence) - 2:
            next_token = sentence[token.i + 1]
            next_next_token = sentence[token.i + 2]
            if (next_token.pos_ == 'PROPN' and next_next_token.pos_ == 'PROPN' and
                next_token.text[0].isupper() and next_next_token.text[0].isupper()):
                return True
        
        # Check for common name prefixes
        name_prefixes = ['mr.', 'ms.', 'mrs.', 'dr.', 'prof.']
        sentence_words = [t.text.lower() for t in sentence]
        
        if any(prefix in sentence_words for prefix in name_prefixes):
            return True
        
        return False
    
    def _is_standalone_title_context(self, token, sentence) -> bool:
        """
        Check if the title is clearly in a standalone context (not with a name).
        """
        # Check for typical standalone patterns
        if token.i > 0:
            prev_token = sentence[token.i - 1]
            # Patterns like "the Manager", "a Director", "our CEO"
            if prev_token.text.lower() in ['the', 'a', 'an', 'our', 'your', 'their', 'each', 'every', 'this', 'that']:
                return True
        
        # Check that it's NOT clearly with a person's name
        if self._is_title_with_person_name(token, sentence):
            return False
        
        # Check for sentence-level indicators of standalone usage
        sentence_text = sentence.text.lower()
        standalone_indicators = [
            'the ' + token.text.lower(),
            'a ' + token.text.lower(),
            'an ' + token.text.lower(),
            'our ' + token.text.lower(),
            'your ' + token.text.lower(),
            'their ' + token.text.lower()
        ]
        
        if any(indicator in sentence_text for indicator in standalone_indicators):
            return True
        
        return True  # Default to standalone if not clearly with name
    
    def _is_title_in_actual_quotes(self, token, sentence, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the title actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not hasattr(token, 'text') or not hasattr(sentence, 'text'):
            return False
        
        title = token.text
        sent_text = sentence.text
        
        # Look for quote pairs that actually enclose the title
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
                if title.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_title_part_of_proper_name(self, token, sentence) -> bool:
        """
        Check if title is part of a brand name or proper noun compound.
        """
        if not hasattr(sentence, 'ents'):
            return False
        
        title_text = token.text.lower()
        
        # Check if this title is part of a larger organization or product entity
        for ent in sentence.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'PERSON'] and token not in ent:
                if title_text in ent.text.lower():
                    return True  # Title is part of company/product name
        
        # Check for common brand/company patterns
        brand_indicators = ['corp', 'inc', 'ltd', 'company', 'enterprises', 'solutions', 'group']
        sentence_text = sentence.text.lower()
        
        for indicator in brand_indicators:
            if indicator in sentence_text and title_text in sentence_text:
                # Check if they're close together (within 5 words)
                words = sentence_text.split()
                try:
                    title_idx = next(i for i, word in enumerate(words) if title_text in word)
                    indicator_idx = next(i for i, word in enumerate(words) if indicator in word)
                    if abs(title_idx - indicator_idx) <= 5:
                        return True
                except StopIteration:
                    continue
        
        return False
    
    def _is_title_in_citation_context(self, token, sentence, context: Dict[str, Any] = None) -> bool:
        """
        Check if title appears in academic citation or reference context.
        """
        if not hasattr(sentence, 'text'):
            return False
        
        sentence_text = sentence.text.lower()
        title_text = token.text.lower()
        
        # Check for citation indicators
        citation_indicators = [
            'published by', 'author:', 'title:', 'journal:', 'vol.', 'pp.',
            'doi:', 'isbn:', 'edited by', 'et al.', 'proceedings of',
            'conference on', 'symposium on', 'workshop on', 'review of'
        ]
        
        for indicator in citation_indicators:
            if indicator in sentence_text:
                return True
        
        # Check for bibliography/reference formatting patterns
        if any(pattern in sentence_text for pattern in ['(19', '(20', '[19', '[20']):  # Years in citations
            return True
        
        # Check for book/paper title patterns (often have titles in them)
        if any(pattern in sentence_text for pattern in ['"', '"', '"', '«', '»']):
            return True
        
        return False
    
    def _is_exact_title_violation(self, token, issue_type: str) -> bool:
        """
        Check if token represents an exact title capitalization violation.
        """
        title_text = token.lemma_.lower()
        token_text = token.text
        
        # High-level executive titles are more critical
        if title_text in ['ceo', 'president', 'director']:
            if issue_type == 'title_with_name_uncapitalized':
                return not token.is_title  # Should be capitalized
            elif issue_type == 'standalone_title_capitalized':
                return token.is_title  # Should be lowercase
        
        return False
    
    def _is_pattern_title_violation(self, token, sentence, issue_type: str) -> bool:
        """
        Check if token shows a pattern of title capitalization violation.
        """
        title_text = token.lemma_.lower()
        
        # Mid-level titles in clear violation patterns
        if title_text in ['manager', 'officer', 'engineer', 'analyst']:
            if issue_type == 'title_with_name_uncapitalized':
                # Check if clearly with a person's name
                return self._is_clearly_with_person_name(token, sentence) and not token.is_title
            elif issue_type == 'standalone_title_capitalized':
                # Check if clearly standalone
                return self._is_clearly_standalone_title(token, sentence) and token.is_title
        
        return False
    
    def _is_minor_title_issue(self, token, sentence, issue_type: str) -> bool:
        """
        Check if token has minor title capitalization issues.
        """
        title_text = token.lemma_.lower()
        
        # Common titles that might have context exceptions
        common_titles = ['manager', 'director', 'officer', 'engineer', 'analyst', 'coordinator']
        
        if title_text in common_titles:
            # Minor issues when context is ambiguous
            if issue_type == 'title_with_name_uncapitalized':
                return self._is_ambiguous_name_context(token, sentence)
            elif issue_type == 'standalone_title_capitalized':
                return self._is_ambiguous_standalone_context(token, sentence)
        
        return False
    
    def _is_clearly_with_person_name(self, token, sentence) -> bool:
        """
        Check if title is clearly used with a person's name.
        """
        # Check for PERSON entities nearby
        for ent in sentence.ents:
            if ent.label_ == 'PERSON':
                # Check if title token is close to person entity
                if abs(token.i - ent.start) <= 3 or abs(token.i - ent.end) <= 3:
                    return True
        
        # Check for common name patterns
        name_patterns = ['mr.', 'ms.', 'mrs.', 'dr.', 'prof.']
        sent_words = [t.text.lower() for t in sentence]
        
        if any(pattern in sent_words for pattern in name_patterns):
            return True
        
        # Check for typical name-title constructions
        if token.dep_ == 'appos':  # Appositional modifier
            return True
        
        return False
    
    def _is_clearly_standalone_title(self, token, sentence) -> bool:
        """
        Check if title is clearly used standalone (not with a name).
        """
        # Check that it's NOT with a person's name
        if self._is_clearly_with_person_name(token, sentence):
            return False
        
        # Check for typical standalone usage patterns
        standalone_patterns = [
            'the manager', 'a director', 'an engineer', 'our ceo',
            'your manager', 'their director', 'each officer'
        ]
        
        # Get preceding tokens
        if token.i > 0:
            prev_token = sentence[token.i - 1]
            if prev_token.text.lower() in ['the', 'a', 'an', 'our', 'your', 'their', 'each', 'every']:
                return True
        
        return True  # Default to standalone if not clearly with name
    
    def _is_ambiguous_name_context(self, token, sentence) -> bool:
        """
        Check if the name context is ambiguous for title capitalization.
        """
        # Look for mixed signals - both name and standalone indicators
        has_name_indicators = self._is_clearly_with_person_name(token, sentence)
        has_standalone_indicators = len([t for t in sentence if t.text.lower() in ['the', 'a', 'an']]) > 0
        
        return has_name_indicators and has_standalone_indicators
    
    def _is_ambiguous_standalone_context(self, token, sentence) -> bool:
        """
        Check if the standalone context is ambiguous for title capitalization.
        """
        # Look for mixed signals - both standalone and name indicators
        has_standalone_indicators = self._is_clearly_standalone_title(token, sentence)
        has_name_nearby = len([ent for ent in sentence.ents if ent.label_ == 'PERSON']) > 0
        
        return has_standalone_indicators and has_name_nearby
    
    def _apply_feedback_clues_titles(self, evidence_score: float, token, context: Dict[str, Any] = None, issue_type: str = 'general') -> float:
        """
        Apply clues learned from user feedback patterns specific to professional titles.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_titles()
        
        if not hasattr(token, 'text'):
            return evidence_score
        
        title_text = token.text.lower()
        
        # Consistently Accepted Terms
        if title_text in feedback_patterns.get('accepted_titles', set()):
            evidence_score -= 0.5  # Users consistently accept this capitalization
        
        # Consistently Rejected Suggestions
        if title_text in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Title type acceptance rates
        title_acceptance = feedback_patterns.get('title_type_acceptance', {})
        acceptance_rate = title_acceptance.get(title_text, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance, likely valid in some contexts
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Issue-specific acceptance
        issue_patterns = feedback_patterns.get(f'{issue_type}_acceptance', {})
        acceptance_rate = issue_patterns.get(title_text, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted for this specific issue type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged for this issue type
        
        # Pattern: Content type specific acceptance
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_title_acceptance', {})
        
        acceptance_rate = content_patterns.get(title_text, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Context-specific acceptance
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        context_patterns = feedback_patterns.get(f'{block_type}_title_patterns', {})
        
        if title_text in context_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif title_text in context_patterns.get('flagged', set()):
            evidence_score += 0.2
        
        # Pattern: Frequency-based adjustment for titles
        term_frequency = feedback_patterns.get('title_term_frequencies', {}).get(title_text, 0)
        if term_frequency > 10:  # Commonly seen title
            acceptance_rate = feedback_patterns.get('title_term_acceptance', {}).get(title_text, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        # Pattern: Executive vs. common title handling
        executive_titles = ['ceo', 'president', 'director', 'vp', 'cfo', 'cto']
        if title_text in executive_titles:
            executive_patterns = feedback_patterns.get('executive_title_acceptance', {})
            acceptance_rate = executive_patterns.get(title_text, 0.3)  # Lower default for executives
            if acceptance_rate > 0.6:
                evidence_score -= 0.2  # Some executives titles acceptable
        
        return evidence_score
    
    def _get_cached_feedback_patterns_titles(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for professional titles.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_titles': {'pm', 'qa', 'hr'},  # Common abbreviations sometimes acceptable
            'rejected_suggestions': set(),  # Titles users don't want flagged
            'title_type_acceptance': {
                'ceo': 0.1,           # Almost always should be handled correctly
                'president': 0.15,    # Almost always should be handled correctly
                'director': 0.2,      # Usually should be handled correctly
                'manager': 0.4,       # More flexible, context-dependent
                'engineer': 0.5,      # Often acceptable in different contexts
                'analyst': 0.5,       # Often acceptable in different contexts
                'coordinator': 0.6,   # Often acceptable in various contexts
                'specialist': 0.6,    # Often acceptable in various contexts
                'lead': 0.7,          # Often acceptable as either title or verb
                'admin': 0.8,         # Often acceptable abbreviation
                'support': 0.8        # Often acceptable in different contexts
            },
            'title_with_name_uncapitalized_acceptance': {
                'ceo': 0.05,          # Should almost always be capitalized with names
                'president': 0.05,    # Should almost always be capitalized with names
                'director': 0.1,      # Should usually be capitalized with names
                'manager': 0.2,       # Usually capitalized with names
                'engineer': 0.3,      # Sometimes acceptable depending on context
                'lead': 0.4           # Often acceptable as regular word
            },
            'standalone_title_capitalized_acceptance': {
                'ceo': 0.2,           # Sometimes acceptable when standalone
                'president': 0.3,     # Sometimes acceptable when standalone (country president)
                'director': 0.4,      # Often acceptable when standalone
                'manager': 0.5,       # Often acceptable when standalone
                'engineer': 0.6,      # Often acceptable when standalone
                'lead': 0.8           # Very acceptable when standalone (not always a title)
            },
            'technical_title_acceptance': {
                'engineer': 0.8,      # Very acceptable in technical writing
                'developer': 0.8,     # Very acceptable in technical writing
                'analyst': 0.7,       # Acceptable in technical writing
                'architect': 0.7,     # Acceptable in technical writing
                'admin': 0.9,         # Very acceptable in technical writing
                'support': 0.9,       # Very acceptable in technical writing
                'lead': 0.9           # Very acceptable in technical writing
            },
            'business_title_acceptance': {
                'ceo': 0.1,           # Should usually be handled correctly in business
                'president': 0.15,    # Should usually be handled correctly in business
                'director': 0.2,      # Should usually be handled correctly in business
                'manager': 0.3,       # Moderately acceptable in business
                'officer': 0.2,       # Should usually be handled correctly in business
                'coordinator': 0.4    # More acceptable in business contexts
            },
            'marketing_title_acceptance': {
                'director': 0.3,      # Sometimes acceptable in marketing
                'manager': 0.4,       # Sometimes acceptable in marketing
                'specialist': 0.6,    # Often acceptable in marketing
                'coordinator': 0.7,   # Often acceptable in marketing
                'lead': 0.8,          # Very acceptable in marketing
                'support': 0.8        # Very acceptable in marketing
            },
            'documentation_title_acceptance': {
                'engineer': 0.7,      # Often acceptable in documentation
                'developer': 0.7,     # Often acceptable in documentation
                'admin': 0.8,         # Very acceptable in documentation
                'support': 0.8,       # Very acceptable in documentation
                'lead': 0.9,          # Very acceptable in documentation
                'manager': 0.4        # Moderately acceptable in documentation
            },
            'title_term_frequencies': {
                'manager': 200,       # Very common title
                'director': 150,      # Common title
                'engineer': 180,      # Very common title
                'ceo': 80,            # Common executive title
                'president': 90,      # Common executive title
                'lead': 120,          # Common title/word
                'support': 100,       # Common title/word
                'admin': 110          # Common title/abbreviation
            },
            'title_term_acceptance': {
                'manager': 0.3,       # Usually needs correct capitalization
                'director': 0.2,      # Usually needs correct capitalization
                'engineer': 0.5,      # More flexible
                'ceo': 0.1,           # Almost always needs correct capitalization
                'president': 0.15,    # Almost always needs correct capitalization
                'lead': 0.7,          # Often acceptable as regular word
                'support': 0.8,       # Often acceptable as regular word
                'admin': 0.7          # Often acceptable abbreviation
            },
            'executive_title_acceptance': {
                'ceo': 0.1,           # Low acceptance for incorrect executive titles
                'president': 0.2,     # Low acceptance for incorrect executive titles
                'cfo': 0.1,           # Low acceptance for incorrect executive titles
                'cto': 0.1,           # Low acceptance for incorrect executive titles
                'vp': 0.3,            # Slightly more acceptable abbreviation
                'director': 0.2       # Low acceptance for incorrect executive titles
            },
            'paragraph_title_patterns': {
                'accepted': {'lead', 'support', 'admin'},
                'flagged': {'ceo', 'president'}
            },
            'heading_title_patterns': {
                'accepted': {'manager', 'director', 'lead'},  # More acceptable in headings
                'flagged': {'ceo', 'president'}
            },
            'list_title_patterns': {
                'accepted': {'pm', 'qa', 'hr', 'admin'},  # Abbreviations common in lists
                'flagged': {'ceo', 'president'}
            }
        }
