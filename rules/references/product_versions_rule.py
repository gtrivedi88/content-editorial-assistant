"""
Product Versions Rule
Based on IBM Style Guide topic: "Product versions"
"""
from typing import List, Dict, Any
from .base_references_rule import BaseReferencesRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ProductVersionsRule(BaseReferencesRule):
    """
    Checks for incorrect formatting of product version numbers, such as
    the use of 'V.' or 'Version' prefixes.
    """
    def _get_rule_type(self) -> str:
        return 'references_product_versions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for product version formatting errors using evidence-based approach.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        
        # Linguistic Anchor: Find invalid version prefixes followed by a number.
        version_prefix_pattern = re.compile(r'\b(V|R|Version|Release)\.?\s*(\d+(\.\d+)*)\b', re.IGNORECASE)

        for i, sent in enumerate(doc.sents):
            for match in version_prefix_pattern.finditer(sent.text):
                full_match = match.group(0)
                version_number = match.group(2)
                
                # Create mock token for evidence calculation
                mock_token = type('MockToken', (), {
                    'text': full_match,
                    'lemma_': full_match.lower(),
                    'pos_': 'NOUN',
                    'ent_type_': '',
                    'like_url': False
                })()
                
                evidence_score = self._calculate_version_evidence(
                    mock_token, sent, text, context, full_match, version_number
                )
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=self._get_contextual_message_version(full_match, evidence_score),
                        suggestions=self._generate_smart_suggestions_version(full_match, version_number, context, evidence_score),
                        severity='medium',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=full_match
                    ))
        return errors
    
    def _calculate_version_evidence(self, token, sentence, text: str, context: Dict[str, Any] = None, full_match: str = '', version_number: str = '') -> float:
        """
        Calculate evidence score (0.0-1.0) for potential product version violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            token: The version token/phrase
            sentence: Sentence containing the token
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            full_match: The full matched text (e.g., "Version 2.0")
            version_number: The extracted version number (e.g., "2.0")
            
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
        
        # Version-specific guards: Don't flag quoted examples
        if self._is_version_in_actual_quotes(full_match, sentence, context):
            return 0.0  # Quoted examples are not version formatting errors
        
        # Don't flag versions in technical documentation contexts
        if self._is_version_in_technical_context(full_match, sentence, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag versions in citation or reference context
        if self._is_version_in_citation_context(full_match, sentence, context):
            return 0.0  # Academic papers, software documentation, etc.
        
        # Apply inherited zero false positive guards
        if self._apply_zero_false_positive_guards_references(token, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_version_base_evidence_score(token, sentence, context, full_match, version_number)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this token
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_references(evidence_score, token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_references(evidence_score, token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_references(evidence_score, token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_versions(evidence_score, full_match, version_number, context)
        
        # Version-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.1  # Version formatting is important but context-dependent
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_version_base_evidence_score(self, token, sentence, context: Dict[str, Any] = None, full_match: str = '', version_number: str = '') -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - "V." or "Version." with periods → 0.7 (very specific)
        - "V" or "R" single letters → 0.6 (moderate specificity)
        - "Version" or "Release" full words → 0.5 (needs context analysis)
        """
        if not self._meets_basic_criteria_references(token):
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_version_violation(full_match, version_number):
            return 0.7  # Very specific, clear violation (reduced from 0.9)
        elif self._is_pattern_version_violation(full_match, version_number):
            return 0.6  # Pattern-based, moderate specificity (reduced from 0.8)
        elif self._is_minor_version_issue(full_match, version_number):
            return 0.5  # Minor issue, needs context (reduced from 0.7)
        else:
            return 0.4  # Possible issue, needs more evidence (reduced from 0.6)
    
    def _get_contextual_message_version(self, version_text: str, evidence_score: float) -> str:
        """
        Generate contextual error message based on evidence strength.
        """
        if evidence_score > 0.85:
            return f"Avoid using version identifiers like 'V' or 'Version'. Use only the number."
        elif evidence_score > 0.6:
            return f"Consider removing version prefix from '{version_text}' and use only the number."
        else:
            return f"Version format '{version_text}' may be simplified to just the number."
    
    def _generate_smart_suggestions_version(self, version_text: str, version_number: str, context: Dict[str, Any] = None, evidence_score: float = 0.5) -> List[str]:
        """
        Generate evidence-aware suggestions for version formatting issues.
        """
        suggestions = []
        
        if evidence_score > 0.8:
            suggestions.append(f"Refer to the version as just '{version_number}'.")
            suggestions.append("Use only the version number without prefixes like 'V' or 'Version'.")
        elif evidence_score > 0.6:
            suggestions.append(f"Consider simplifying to '{version_number}'.")
            suggestions.append("Version numbers are clearer without prefixes.")
        else:
            suggestions.append(f"Review version format: '{version_number}'.")
        
        return suggestions[:3]
    
    def _is_version_in_actual_quotes(self, version_text: str, sentence, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the version actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not hasattr(sentence, 'text'):
            return False
        
        sent_text = sentence.text
        
        # Look for quote pairs that actually enclose the version
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
                if version_text.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_version_in_technical_context(self, version_text: str, sentence, context: Dict[str, Any] = None) -> bool:
        """
        Check if version appears in technical documentation context.
        """
        if not hasattr(sentence, 'text'):
            return False
        
        sentence_text = sentence.text.lower()
        
        # Check for technical documentation indicators (be more selective)
        technical_indicators = [
            'api', 'sdk', 'documentation', 'specification', 'protocol',
            'framework', 'library', 'package', 'module', 'component',
            'changelog', 'release notes', 'git', 'commit', 'branch', 'tag',
            'repository', 'dockerfile', 'makefile', 'npm', 'pip', 'maven'
        ]
        
        for indicator in technical_indicators:
            if indicator in sentence_text:
                return True
        
        # Check for version patterns that might be acceptable in technical contexts
        if any(pattern in sentence_text for pattern in ['v1.', 'v2.', 'v3.', 'version 1', 'version 2']):
            # Common in software versioning
            content_type = context.get('content_type', '') if context else ''
            if content_type in ['technical', 'documentation']:
                return True
        
        # Only protect if we have strong technical context indicators
        # Generic words like "software", "system", "platform" are not enough
        strong_technical_context = any(strong_indicator in sentence_text for strong_indicator in [
            'technical documentation', 'api documentation', 'developer guide',
            'software documentation', 'system documentation', 'release notes',
            'changelog', 'installation guide', 'configuration guide'
        ])
        
        return strong_technical_context
    
    def _is_version_in_citation_context(self, version_text: str, sentence, context: Dict[str, Any] = None) -> bool:
        """
        Check if version appears in citation or reference context.
        """
        if not hasattr(sentence, 'text'):
            return False
        
        sentence_text = sentence.text.lower()
        
        # Check for citation indicators
        citation_indicators = [
            'published', 'source:', 'reference:', 'cited in', 'according to',
            'doi:', 'isbn:', 'url:', 'retrieved from', 'available at',
            'documentation:', 'manual:', 'guide:', 'specification:',
            'see also', 'refer to', 'as described in'
        ]
        
        for indicator in citation_indicators:
            if indicator in sentence_text:
                return True
        
        # Check for reference formatting patterns
        if any(pattern in sentence_text for pattern in ['(19', '(20', '[19', '[20']):  # Years in citations
            return True
        
        # Check for software documentation patterns
        if any(pattern in sentence_text for pattern in ['readme', 'changelog', 'license', 'copyright']):
            return True
        
        return False
    
    def _is_exact_version_violation(self, full_match: str, version_number: str) -> bool:
        """
        Check if version represents an exact formatting violation.
        """
        prefix = full_match.replace(version_number, '').strip()
        
        # Exact violations with periods
        if prefix.lower() in ['v.', 'version.', 'release.', 'r.']:
            return True
        
        return False
    
    def _is_pattern_version_violation(self, full_match: str, version_number: str) -> bool:
        """
        Check if version shows a pattern of formatting violation.
        """
        prefix = full_match.replace(version_number, '').strip()
        
        # Single letter prefixes without periods
        if prefix.lower() in ['v', 'r']:
            return True
        
        return False
    
    def _is_minor_version_issue(self, full_match: str, version_number: str) -> bool:
        """
        Check if version has minor formatting issues.
        """
        prefix = full_match.replace(version_number, '').strip()
        
        # Full word prefixes
        if prefix.lower() in ['version', 'release']:
            return True
        
        return False
    
    def _apply_feedback_clues_versions(self, evidence_score: float, full_match: str, version_number: str, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to version formatting.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_versions()
        
        prefix = full_match.replace(version_number, '').strip()
        prefix_lower = prefix.lower()
        
        # Consistently Accepted Version Formats
        if prefix_lower in feedback_patterns.get('accepted_version_formats', set()):
            evidence_score -= 0.5  # Users consistently accept this format
        
        # Consistently Rejected Suggestions
        if prefix_lower in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Version format acceptance rates
        format_acceptance = feedback_patterns.get('version_format_acceptance', {})
        acceptance_rate = format_acceptance.get(prefix_lower, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance, likely valid in some contexts
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Version formats in different content types
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_version_acceptance', {})
        
        acceptance_rate = content_patterns.get(prefix_lower, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Context-specific acceptance
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        context_patterns = feedback_patterns.get(f'{block_type}_version_patterns', {})
        
        if prefix_lower in context_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif prefix_lower in context_patterns.get('flagged', set()):
            evidence_score += 0.2
        
        # Pattern: Frequency-based adjustment for version formats
        term_frequency = feedback_patterns.get('version_format_frequencies', {}).get(prefix_lower, 0)
        if term_frequency > 10:  # Commonly seen format
            acceptance_rate = feedback_patterns.get('version_format_acceptance', {}).get(prefix_lower, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        # Pattern: Version number complexity handling
        if '.' in version_number:  # Complex version numbers like 2.1.3
            complex_patterns = feedback_patterns.get('complex_version_acceptance', {})
            acceptance_rate = complex_patterns.get(prefix_lower, 0.5)
            if acceptance_rate > 0.8:
                evidence_score -= 0.2  # Complex versions often acceptable with prefix
        
        return evidence_score
    
    def _get_cached_feedback_patterns_versions(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for version formatting.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_version_formats': {'v1', 'v2', 'v3'},  # Common in software
            'rejected_suggestions': set(),  # Formats users don't want flagged
            'version_format_acceptance': {
                'v.': 0.1,            # Almost always should be simplified
                'version.': 0.1,      # Almost always should be simplified
                'release.': 0.1,      # Almost always should be simplified
                'r.': 0.1,            # Almost always should be simplified
                'v': 0.2,             # Should usually be simplified (reduced from 0.3)
                'r': 0.2,             # Should usually be simplified (reduced from 0.4)
                'version': 0.3,       # Should usually be simplified (reduced from 0.5)
                'release': 0.3,       # Should usually be simplified (reduced from 0.5)
                'rev': 0.6,           # Often acceptable abbreviation
                'build': 0.7,         # Often acceptable in software contexts
                'update': 0.8         # Very acceptable in update contexts
            },
            'technical_version_acceptance': {
                'v': 0.7,             # More acceptable in technical writing
                'r': 0.6,             # Acceptable in technical writing
                'version': 0.4,       # Less preferred in technical writing
                'release': 0.4,       # Less preferred in technical writing
                'build': 0.9,         # Very acceptable in technical writing
                'rev': 0.8,           # Very acceptable in technical writing
                'patch': 0.9,         # Very acceptable in technical writing
                'update': 0.9         # Very acceptable in technical writing
            },
            'marketing_version_acceptance': {
                'v.': 0.05,           # Should almost never be used in marketing
                'version.': 0.05,     # Should almost never be used in marketing
                'v': 0.2,             # Sometimes acceptable in marketing
                'version': 0.6,       # Often acceptable in marketing
                'release': 0.7,       # Often acceptable in marketing
                'edition': 0.9,       # Very acceptable in marketing
                'update': 0.8         # Very acceptable in marketing
            },
            'documentation_version_acceptance': {
                'v': 0.5,             # Moderately acceptable in documentation
                'version': 0.7,       # Often acceptable in documentation
                'release': 0.7,       # Often acceptable in documentation
                'r': 0.4,             # Sometimes acceptable in documentation
                'build': 0.8,         # Very acceptable in documentation
                'update': 0.8,        # Very acceptable in documentation
                'patch': 0.8          # Very acceptable in documentation
            },
            'version_format_frequencies': {
                'v': 200,             # Very common abbreviation
                'version': 150,       # Common full word
                'release': 100,       # Common in release contexts
                'r': 80,              # Common abbreviation
                'build': 120,         # Common in software contexts
                'update': 90,         # Common in update contexts
                'patch': 70,          # Common in patch contexts
                'rev': 60             # Common abbreviation
            },
            'complex_version_acceptance': {
                'v': 0.6,             # More acceptable with complex versions
                'version': 0.7,       # More acceptable with complex versions
                'release': 0.7,       # More acceptable with complex versions
                'build': 0.8,         # Very acceptable with complex versions
                'patch': 0.9,         # Very acceptable with complex versions
                'update': 0.8         # Very acceptable with complex versions
            },
            'paragraph_version_patterns': {
                'accepted': {'v', 'version', 'release'},
                'flagged': {'v.', 'version.', 'release.'}
            },
            'heading_version_patterns': {
                'accepted': {'v', 'version', 'release', 'update'},  # More acceptable in headings
                'flagged': {'v.', 'version.'}
            },
            'list_version_patterns': {
                'accepted': {'v', 'r', 'build', 'patch'},  # Abbreviations common in lists
                'flagged': {'v.', 'version.', 'release.'}
            }
        }
