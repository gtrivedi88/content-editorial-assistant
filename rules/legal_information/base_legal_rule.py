"""
Base Legal Information Rule (Production-Grade)
Enhanced base class following evidence-based rule development standards.
Provides shared utilities for legal information rules while enforcing rule-specific evidence calculation.
Each rule must implement its own _calculate_[RULE_TYPE]_evidence() method for surgical precision.
"""

from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict
import re

# A generic base rule to be inherited from a central location
# in a real application. The # type: ignore comments prevent the
# static type checker from getting confused by the fallback class.
try:
    from ..base_rule import BaseRule  # type: ignore
except ImportError:
    class BaseRule:  # type: ignore
        def _get_rule_type(self) -> str:
            return 'base'
        def _create_error(self, sentence: str, sentence_index: int, message: str, 
                         suggestions: List[str], severity: str = 'medium', 
                         text: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                         **extra_data) -> Dict[str, Any]:
            """Fallback _create_error implementation when main BaseRule import fails."""
            # Create basic error structure for fallback scenarios
            error = {
                'type': getattr(self, 'rule_type', 'unknown'),
                'message': str(message),
                'suggestions': [str(s) for s in suggestions],
                'sentence': str(sentence),
                'sentence_index': int(sentence_index),
                'severity': severity,
                'enhanced_validation_available': False  # Mark as fallback
            }
            # Add any extra data
            error.update(extra_data)
            return error
        def _analyze_formality_level(self, token) -> float:
            return 0.5
        def _calculate_morphological_complexity(self, token) -> float:
            return 1.0
        def _get_morphological_features(self, token) -> Dict[str, Any]:
            return {}
        def _has_latinate_morphology(self, token) -> bool:
            return False
        def _analyze_semantic_field(self, token, doc=None) -> str:
            return 'unknown'
        def _token_to_dict(self, token) -> Optional[Dict[str, Any]]:
            return None
        def _analyze_sentence_structure(self, sentence: str, nlp=None):
            return nlp(sentence) if nlp and sentence.strip() else None
        def _estimate_syllables_morphological(self, token) -> int:
            return 1
        def _analyze_word_frequency_class(self, token, doc=None) -> str:
            return 'medium'


class BaseLegalRule(BaseRule):
    """
    Production-grade base class for legal information rules.
    
    IMPORTANT: This class provides shared utilities but does NOT implement centralized
    evidence calculation. Each rule must implement its own _calculate_[RULE_TYPE]_evidence()
    method for optimal surgical precision and near 100% false positive elimination.
    
    Provides:
    - Legal-specific linguistic analysis utilities
    - Regulatory compliance pattern detection
    - Legal terminology validation helpers
    - Evidence-aware legal messaging and suggestions
    """

    def __init__(self):
        super().__init__()
        # Initialize legal-specific linguistic anchors
        self._initialize_legal_linguistic_anchors()
    
    def _initialize_legal_linguistic_anchors(self):
        """Initialize morphological and semantic anchors for legal information analysis."""
        
        # Legal terminology indicators
        self.legal_terminology_patterns = {
            'regulatory_indicators': {
                'gdpr_terms': ['gdpr', 'personal data', 'data subject', 'data controller', 'data processor'],
                'hipaa_terms': ['hipaa', 'phi', 'protected health information', 'covered entity'],
                'ccpa_terms': ['ccpa', 'consumer', 'personal information', 'sale of personal information'],
                'sox_terms': ['sarbanes-oxley', 'sox', 'internal controls', 'financial reporting']
            },
            'claim_indicators': {
                'absolute_claims': ['guarantee', 'ensure', 'promise', 'always', 'never', 'all', 'every'],
                'performance_claims': ['fastest', 'best', 'most secure', 'completely safe', '100%'],
                'temporal_claims': ['forever', 'permanent', 'indefinitely', 'never expires']
            },
            'liability_patterns': {
                'disclaimer_required': ['warranty', 'guarantee', 'promise', 'ensure', 'liability'],
                'risk_language': ['may', 'might', 'could', 'potential', 'possible', 'risk']
            }
        }
        
        # Company and entity recognition patterns
        self.entity_recognition_patterns = {
            'company_suffixes': {
                'incorporated': ['inc', 'incorporated', 'corp', 'corporation', 'ltd', 'limited'],
                'partnerships': ['llp', 'lp', 'partnership'],
                'llc_patterns': ['llc', 'limited liability company', 'l.l.c.'],
                'international': ['gmbh', 'sa', 'ag', 'spa', 'bv', 'pty']
            },
            'legal_entity_indicators': {
                'trademark_indicators': ['™', '®', 'trademark', 'registered trademark'],
                'copyright_indicators': ['©', 'copyright', 'all rights reserved'],
                'patent_indicators': ['patent', 'patented', 'patent pending', 'pat. no.']
            }
        }
        
        # Personal information classification patterns
        self.personal_info_classification = {
            'pii_categories': {
                'direct_identifiers': ['ssn', 'social security', 'driver license', 'passport'],
                'financial_identifiers': ['credit card', 'bank account', 'routing number'],
                'biometric_identifiers': ['fingerprint', 'retina', 'facial recognition', 'dna'],
                'behavioral_identifiers': ['browsing history', 'location data', 'device fingerprint']
            },
            'sensitivity_levels': {
                'high_sensitivity': ['medical', 'health', 'genetic', 'biometric', 'financial'],
                'medium_sensitivity': ['employment', 'education', 'demographic'],
                'regulated_categories': ['children', 'minors', 'under 13', 'under 16']
            }
        }

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        ABSTRACT: Each rule must implement its own analyze method.
        
        PRODUCTION STANDARD: Rules must implement rule-specific evidence calculation
        rather than using centralized evidence methods for surgical precision.
        
        Required implementation pattern:
        1. Find potential issues using rule-specific detection
        2. Calculate evidence using rule-specific _calculate_[RULE_TYPE]_evidence()
        3. Apply surgical zero false positive guards specific to legal domain
        4. Use evidence-aware legal messaging and suggestions
        
        Returns:
            List of errors with rule-specific evidence scores
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement its own analyze() method "
            f"with rule-specific evidence calculation for surgical legal precision."
        )
    
    # === PRODUCTION-GRADE SHARED UTILITIES ===
    # These methods provide common functionality for all legal information rules
    # while each rule implements its own evidence calculation for precision
    
    def _apply_surgical_zero_false_positive_guards_legal(self, token, context: Dict[str, Any]) -> bool:
        """
        Apply surgical zero false positive guards for legal information rules.
        Returns True if evidence should be killed immediately.
        
        CRITICAL: These guards must be surgical - eliminate false positives while 
        preserving ALL legitimate legal violations. Individual rules should extend with 
        rule-specific guards.
        """
        if not token or not hasattr(token, 'text'):
            return True
            
        # === STRUCTURAL CONTEXT GUARDS ===
        # Code blocks, configuration files have different rules
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block', 'config']:
            return True
            
        # === ENTITY AND PROPER NOUN GUARDS ===
        # PRODUCTION FIX: Only block entities that are clearly not relevant to legal rules
        # Legal rules NEED to check entities (companies, products, etc.)
        # Only block entities that are definitively non-legal (events, locations)
        if hasattr(token, 'ent_type_') and token.ent_type_ in ['EVENT', 'GPE']:
            return True  # Only block events and geo-political entities
            
        # === TECHNICAL IDENTIFIER GUARDS ===
        # URLs, file paths, technical identifiers
        if hasattr(token, 'like_url') and token.like_url:
            return True
        if hasattr(token, 'text') and ('/' in token.text or '\\' in token.text or token.text.startswith('http')):
            return True
            
        # === LEGAL DOCUMENT CONTEXT GUARDS ===
        # Don't flag content in legal disclaimers, terms of service, privacy policies
        if self._is_in_legal_disclaimer_context(token, context):
            return True
            
        # === QUOTED CONTENT GUARDS ===
        # Don't flag content in quotes (examples, citations, legal references)
        if self._is_in_quoted_context_legal(token, context):
            return True
            
        # === REGULATORY REFERENCE GUARDS ===
        # Don't flag legitimate regulatory references or citations
        if self._is_legitimate_regulatory_reference(token, context):
            return True
            
        # === FOREIGN LANGUAGE GUARDS ===
        # Don't flag tokens identified as foreign language
        if hasattr(token, 'lang_') and token.lang_ != 'en':
            return True
            
        return False
    
    def _is_in_legal_disclaimer_context(self, token, context: Dict[str, Any]) -> bool:
        """
        Check if token appears in legal disclaimer context.
        Surgical check - only genuine legal disclaimers, not content that needs review.
        """
        if not context:
            return False
            
        block_type = context.get('block_type', '')
        content_type = context.get('content_type', '')
        
        # Explicit legal document sections
        if block_type in ['disclaimer', 'terms_of_service', 'privacy_policy', 'legal_notice']:
            return True
            
        if content_type in ['legal', 'regulatory', 'compliance']:
            return True
            
        # Check for legal disclaimer indicators in nearby text
        if hasattr(token, 'sent'):
            sent_text = token.sent.text.lower()
            disclaimer_indicators = [
                'this disclaimer', 'legal notice', 'terms of service', 
                'privacy policy', 'for legal purposes', 'compliance with'
            ]
            return any(indicator in sent_text for indicator in disclaimer_indicators)
            
        return False
    
    def _is_in_quoted_context_legal(self, token, context: Dict[str, Any]) -> bool:
        """
        Check if token appears in quoted context (legal citations, examples).
        Surgical check - only genuine quotes, not legitimate content with apostrophes.
        """
        if not hasattr(token, 'doc') or not token.doc:
            return False
            
        # Look for actual quotation marks around the token
        sent = token.sent
        token_idx = token.i - sent.start
        
        # Check for quotation marks in reasonable proximity
        quote_chars = ['"', '"', '"', "'", "'", "'"]
        
        # Look backwards and forwards for quote pairs
        before_quotes = 0
        after_quotes = 0
        
        # Search backwards
        for i in range(max(0, token_idx - 15), token_idx):
            if i < len(sent) and sent[i].text in quote_chars:
                before_quotes += 1
                
        # Search forwards  
        for i in range(token_idx + 1, min(len(sent), token_idx + 15)):
            if i < len(sent) and sent[i].text in quote_chars:
                after_quotes += 1
        
        # If we have quotes both before and after, likely quoted content
        return before_quotes > 0 and after_quotes > 0
    
    def _is_legitimate_regulatory_reference(self, token, context: Dict[str, Any]) -> bool:
        """
        Check if token is part of a legitimate regulatory reference or citation.
        Surgical check - only genuine regulatory references, not unsupported claims.
        """
        if not hasattr(token, 'sent'):
            return False
            
        sent_text = token.sent.text.lower()
        
        # Citation patterns
        citation_patterns = [
            r'\b\d+\s*cfr\s*\d+',  # Federal regulations
            r'\b\d+\s*usc\s*\d+',  # US Code
            r'\bsec\.\s*\d+',      # Section references
            r'\bpub\.\s*l\.',      # Public law
            r'\b\d+\s*stat\.',     # Statutes
        ]
        
        # Check for citation patterns
        for pattern in citation_patterns:
            if re.search(pattern, sent_text):
                return True
                
        # Reference indicators
        reference_indicators = [
            'as required by', 'in accordance with', 'pursuant to',
            'as defined in', 'under regulation', 'federal law',
            'state law', 'applicable law', 'legal requirement'
        ]
        
        return any(indicator in sent_text for indicator in reference_indicators)
    
    def _generate_evidence_aware_legal_message(self, issue: Dict[str, Any], evidence_score: float, 
                                             rule_type: str = "legal") -> str:
        """
        Generate evidence-aware error messages for legal information rules.
        Adapts message tone based on evidence confidence and legal severity.
        """
        token_text = issue.get('text', issue.get('phrase', ''))
        
        if evidence_score > 0.9:
            # Very high confidence -> Critical legal issue
            return f"CRITICAL: The {rule_type} issue '{token_text}' may create legal liability and requires immediate review."
        elif evidence_score > 0.75:
            # High confidence -> Direct, authoritative message
            return f"The {rule_type} concern '{token_text}' violates legal compliance guidelines and should be reviewed by legal counsel."
        elif evidence_score > 0.6:
            # Medium confidence -> Balanced suggestion
            return f"Consider reviewing '{token_text}' for potential {rule_type} compliance issues."
        else:
            # Low confidence -> Gentle, optional suggestion
            return f"'{token_text}' may benefit from legal review to ensure compliance."
    
    def _generate_evidence_aware_legal_suggestions(self, issue: Dict[str, Any], evidence_score: float,
                                                 context: Dict[str, Any], rule_type: str = "legal") -> List[str]:
        """
        Generate evidence-aware suggestions for legal information rules.
        Higher evidence = more urgent, specific legal guidance.
        """
        suggestions = []
        token_text = issue.get('text', issue.get('phrase', ''))
        
        if evidence_score > 0.85:
            # High confidence -> Urgent, specific legal guidance
            suggestions.append(f"URGENT: Consult legal counsel immediately regarding '{token_text}'.")
            suggestions.append("This issue may create significant legal liability if not addressed.")
            suggestions.append("Consider adding appropriate disclaimers or removing the problematic content.")
        elif evidence_score > 0.7:
            # Medium-high confidence -> Clear legal guidance
            suggestions.append(f"Review '{token_text}' with legal team for compliance requirements.")
            suggestions.append("Consider adding qualifying language or disclaimers.")
            suggestions.append("Ensure all claims are substantiated and legally defensible.")
        elif evidence_score > 0.5:
            # Medium confidence -> Balanced legal suggestions  
            suggestions.append(f"Consider reviewing '{token_text}' for legal compliance.")
            suggestions.append("Add qualifying language if claims cannot be substantiated.")
            suggestions.append("Consult legal guidelines for your industry and jurisdiction.")
        else:
            # Low confidence -> Gentle, optional suggestions
            suggestions.append(f"'{token_text}' may benefit from legal review.")
            suggestions.append("Consider whether additional context or disclaimers would be helpful.")
            suggestions.append("Ensure all statements align with legal and regulatory requirements.")
        
        # Add context-specific legal suggestions based on evidence
        if evidence_score > 0.6:
            content_type = context.get('content_type', 'general')
            if content_type in ['marketing', 'advertising']:
                suggestions.append("Marketing claims must be substantiated and comply with FTC guidelines.")
            elif content_type in ['privacy', 'data']:
                suggestions.append("Data handling statements must comply with applicable privacy laws (GDPR, CCPA, etc.).")
            elif content_type in ['financial', 'investment']:
                suggestions.append("Financial statements must comply with SEC regulations and disclosure requirements.")
        
        return suggestions[:4]  # Limit to 4 suggestions for legal clarity
    
    # === SHARED LEGAL ANALYSIS UTILITIES ===
    
    def _get_shared_legal_indicators(self, token) -> Dict[str, Any]:
        """Get legal indicators that are shared across legal information rules."""
        if not token or not hasattr(token, 'text'):
            return {}
            
        return {
            'is_regulatory_term': self._is_regulatory_term(token),
            'is_claim_language': self._is_claim_language(token),
            'is_liability_term': self._is_liability_term(token),
            'is_company_identifier': self._is_company_identifier(token),
            'is_personal_info_term': self._is_personal_info_term(token),
            'legal_risk_level': self._assess_legal_risk_level(token)
        }
    
    def _is_regulatory_term(self, token) -> bool:
        """Check if token is a regulatory term that requires special handling."""
        if not hasattr(token, 'text'):
            return False
            
        text_lower = token.text.lower()
        
        # Check all regulatory term categories
        for category, terms in self.legal_terminology_patterns['regulatory_indicators'].items():
            if any(term in text_lower for term in terms):
                return True
                
        return False
    
    def _is_claim_language(self, token) -> bool:
        """Check if token contains claim language that may require substantiation."""
        if not hasattr(token, 'text'):
            return False
            
        text_lower = token.text.lower()
        
        # Check all claim indicator categories
        for category, terms in self.legal_terminology_patterns['claim_indicators'].items():
            if text_lower in terms or any(term in text_lower for term in terms):
                return True
                
        return False
    
    def _is_liability_term(self, token) -> bool:
        """Check if token relates to liability or warranty language."""
        if not hasattr(token, 'text'):
            return False
            
        text_lower = token.text.lower()
        
        # Check liability pattern categories
        for category, terms in self.legal_terminology_patterns['liability_patterns'].items():
            if text_lower in terms or any(term in text_lower for term in terms):
                return True
                
        return False
    
    def _is_company_identifier(self, token) -> bool:
        """Check if token is part of a company name or legal entity."""
        if not hasattr(token, 'text'):
            return False
            
        text_lower = token.text.lower()
        
        # Check company suffix patterns
        for category, suffixes in self.entity_recognition_patterns['company_suffixes'].items():
            if text_lower in suffixes or any(suffix in text_lower for suffix in suffixes):
                return True
                
        return False
    
    def _is_personal_info_term(self, token) -> bool:
        """Check if token relates to personal information that may be regulated."""
        if not hasattr(token, 'text'):
            return False
            
        text_lower = token.text.lower()
        
        # Check PII category patterns
        for category, terms in self.personal_info_classification['pii_categories'].items():
            if any(term in text_lower for term in terms):
                return True
                
        return False
    
    def _assess_legal_risk_level(self, token) -> str:
        """Assess the legal risk level of a token based on its content."""
        if not hasattr(token, 'text'):
            return 'low'
            
        text_lower = token.text.lower()
        
        # High-risk terms
        high_risk_terms = ['guarantee', 'promise', 'ensure', 'always', 'never', '100%', 'completely safe']
        if any(term in text_lower for term in high_risk_terms):
            return 'high'
            
        # Medium-risk terms
        medium_risk_terms = ['warranty', 'liability', 'compliance', 'regulatory', 'personal data']
        if any(term in text_lower for term in medium_risk_terms):
            return 'medium'
            
        return 'low'
    
    def _detect_common_legal_patterns(self, doc) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect common patterns that multiple legal rules care about.
        Returns categorized findings for rules to use in their specific evidence calculation.
        """
        if not doc:
            return {}
            
        patterns = {
            'claim_statements': [],
            'regulatory_references': [],
            'liability_language': [],
            'company_identifiers': [],
            'personal_info_references': []
        }
        
        try:
            for token in doc:
                if not token.is_alpha or token.is_stop:
                    continue
                    
                legal_indicators = self._get_shared_legal_indicators(token)
                
                # Categorize based on legal indicators
                if legal_indicators['is_claim_language']:
                    patterns['claim_statements'].append({
                        'token': token,
                        'risk_level': legal_indicators['legal_risk_level'],
                        'indicators': legal_indicators
                    })
                
                if legal_indicators['is_regulatory_term']:
                    patterns['regulatory_references'].append({
                        'token': token,
                        'indicators': legal_indicators
                    })
                
                if legal_indicators['is_liability_term']:
                    patterns['liability_language'].append({
                        'token': token,
                        'risk_level': legal_indicators['legal_risk_level'],
                        'indicators': legal_indicators
                    })
                
                if legal_indicators['is_company_identifier']:
                    patterns['company_identifiers'].append({
                        'token': token,
                        'indicators': legal_indicators
                    })
                
                if legal_indicators['is_personal_info_term']:
                    patterns['personal_info_references'].append({
                        'token': token,
                        'indicators': legal_indicators
                    })
        
        except Exception:
            pass  # Graceful degradation
            
        return patterns