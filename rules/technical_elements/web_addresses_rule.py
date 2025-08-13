"""
Web, IP, and Email Addresses Rule (Production-Grade)
Based on IBM Style Guide topic: "Web, IP, and email addresses"
Evidence-based analysis with surgical zero false positive guards for web address formatting.
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
from .services.technical_config_service import TechnicalConfigServices, TechnicalContext
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class WebAddressesRule(BaseTechnicalRule):
    """
    Checks for common formatting errors in web addresses.
    
    Features:
    - YAML-based configuration for maintainable pattern management
    - Surgical zero false positive guards for web address contexts
    - Dynamic base evidence scoring based on address type specificity
    - Evidence-aware messaging for web documentation
    """
    
    def __init__(self):
        """Initialize with YAML configuration service."""
        super().__init__()
        self.config_service = TechnicalConfigServices.web_addresses()
    
    def _get_rule_type(self) -> str:
        return 'technical_web_addresses'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        PRODUCTION-GRADE: Evidence-based analysis for web address violations.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        context = context or {}

        # === STEP 1: Find potential web address issues ===
        potential_issues = self._find_potential_web_address_issues(doc, text, context)
        
        # === STEP 2: Process each potential issue with evidence calculation ===
        for issue in potential_issues:
            # Calculate rule-specific evidence score
            evidence_score = self._calculate_web_address_evidence(
                issue, doc, text, context
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                error = self._create_error(
                    sentence=issue['sentence'],
                    sentence_index=issue['sentence_index'],
                    message=self._generate_evidence_aware_message(issue, evidence_score, "web_address"),
                    suggestions=self._generate_evidence_aware_suggestions(issue, evidence_score, context, "web_address"),
                    severity='low' if evidence_score < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=issue.get('span', [0, 0]),
                    flagged_text=issue.get('flagged_text', issue.get('text', ''))
                )
                errors.append(error)
        
        return errors
    
    def _find_potential_web_address_issues(self, doc, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential web address issues for evidence assessment."""
        issues = []
        
        # Load web address patterns from YAML configuration
        all_patterns = self.config_service.get_patterns()
        web_address_patterns = {}
        
        for pattern_id, pattern_config in all_patterns.items():
            if hasattr(pattern_config, 'pattern'):
                # This is a web address pattern
                web_address_patterns[pattern_config.pattern] = {
                    'type': pattern_config.category,
                    'base_evidence': pattern_config.evidence,
                    'description': pattern_config.description,
                    'pattern_config': pattern_config
                }
        
        for i, sent in enumerate(doc.sents):
            sent_text = sent.text
            
            # Check each pattern
            for pattern, pattern_info in web_address_patterns.items():
                for match in re.finditer(pattern, sent_text):
                    # Special handling for different types
                    if pattern_info['type'] == 'trailing_slash':
                        # Only flag if it's clearly inappropriate
                        url = match.group(0)
                        if self._is_inappropriate_trailing_slash(url):
                            issues.append({
                                'type': 'web_address',
                                'subtype': pattern_info['type'],
                                'url': url,
                                'text': url,
                                'sentence': sent_text,
                                'sentence_index': i,
                                'span': [sent.start_char + match.start(), sent.start_char + match.end()],
                                'base_evidence': pattern_info['base_evidence'],
                                'flagged_text': url,
                                'match_obj': match,
                                'sentence_obj': sent,
                                'description': pattern_info['description'],
                                'pattern_config': pattern_info.get('pattern_config')
                            })
                    
                    elif pattern_info['type'] == 'missing_protocol':
                        # Only flag in documentation contexts
                        if self._should_have_protocol(sent_text, context):
                            issues.append({
                                'type': 'web_address',
                                'subtype': pattern_info['type'],
                                'url': match.group(0),
                                'text': match.group(0),
                                'sentence': sent_text,
                                'sentence_index': i,
                                'span': [sent.start_char + match.start(), sent.start_char + match.end()],
                                'base_evidence': pattern_info['base_evidence'],
                                'flagged_text': match.group(0),
                                'match_obj': match,
                                'sentence_obj': sent,
                                'description': pattern_info['description'],
                                'pattern_config': pattern_info.get('pattern_config')
                            })
                    
                    elif pattern_info['type'] == 'mixed_protocols':
                        # Flag mixed HTTP/HTTPS protocols
                        issues.append({
                            'type': 'web_address',
                            'subtype': pattern_info['type'],
                            'url': match.group(0),
                            'text': match.group(0),
                            'sentence': sent_text,
                            'sentence_index': i,
                            'span': [sent.start_char + match.start(), sent.start_char + match.end()],
                            'base_evidence': pattern_info['base_evidence'],
                            'flagged_text': match.group(0),
                            'match_obj': match,
                            'sentence_obj': sent,
                            'description': pattern_info['description'],
                            'pattern_config': pattern_info.get('pattern_config')
                        })
                    
                    elif pattern_info['type'] == 'email_format':
                        # Flag email addresses for format consideration
                        issues.append({
                            'type': 'web_address',
                            'subtype': pattern_info['type'],
                            'url': match.group(0),
                            'text': match.group(0),
                            'sentence': sent_text,
                            'sentence_index': i,
                            'span': [sent.start_char + match.start(), sent.start_char + match.end()],
                            'base_evidence': pattern_info['base_evidence'],
                            'flagged_text': match.group(0),
                            'match_obj': match,
                            'sentence_obj': sent,
                            'description': pattern_info['description'],
                            'pattern_config': pattern_info.get('pattern_config')
                        })
        
        return issues
    
    def _is_inappropriate_trailing_slash(self, url: str) -> bool:
        """Check if trailing slash is inappropriate for this URL."""
        # Don't flag if it's clearly a directory or has parameters
        if any(indicator in url.lower() for indicator in [
            '?', '#', '&', '=', 'index.', 'default.', 'home.', 'main.'
        ]):
            return False
        
        # Don't flag very short URLs (likely directories)
        if len(url.split('/')) <= 4:
            return False
        
        # Don't flag if it has file extension before the slash
        parts = url.split('/')
        if len(parts) > 1 and '.' in parts[-2]:
            return False
        
        return True
    
    def _should_have_protocol(self, sent_text: str, context: Dict[str, Any]) -> bool:
        """Check if URL should have protocol in this context."""
        # Technical documentation should include protocols
        content_type = context.get('content_type', '')
        if content_type in ['technical', 'api', 'developer', 'tutorial']:
            return True
        
        # Check for instruction context
        instruction_indicators = [
            'visit', 'go to', 'navigate to', 'access', 'browse to',
            'open', 'click', 'follow', 'use this url', 'link to'
        ]
        
        sent_lower = sent_text.lower()
        return any(indicator in sent_lower for indicator in instruction_indicators)
    
    def _calculate_web_address_evidence(self, issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence score for web address violations."""
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR WEB ADDRESSES ===
        sentence_obj = issue.get('sentence_obj')
        if not sentence_obj:
            return 0.0
            
        issue_type = issue.get('subtype', '')
        url = issue.get('url', '')
        
        # === GUARD 1: FUNCTIONAL URLS ===
        if self._is_functional_url_context(url, sentence_obj, context):
            return 0.0  # Functional URLs may need specific formatting
            
        # === GUARD 2: QUOTED EXAMPLES ===
        if self._is_quoted_url_example(sentence_obj, context):
            return 0.0  # Quoted examples may preserve original formatting
            
        # === GUARD 3: API DOCUMENTATION CONTEXT ===
        if self._is_api_documentation_url(url, sentence_obj, context):
            return 0.0  # API docs often have specific URL requirements
            
        # === GUARD 4: PLACEHOLDER OR EXAMPLE URLS (SELECTIVE) ===
        # Only protect localhost and actual placeholders, not example.com URLs
        if 'localhost' in url.lower() or '127.0.0.1' in url or 'placeholder' in url.lower():
            return 0.0  # Localhost and true placeholders don't need perfect formatting
            
        # Apply common technical guards
        mock_token = type('MockToken', (), {
            'text': url, 
            'sent': sentence_obj
        })
        # Apply selective technical guards (skip technical context guard for web addresses)  
        # Web address violations should be flagged even in technical contexts
        
        # Only check code blocks
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return 0.0  # Code blocks have their own formatting rules
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = issue.get('base_evidence', 0.7)
        
        # === CONTEXT ADJUSTMENTS FROM YAML ===
        evidence_score = self.config_service.calculate_context_evidence(evidence_score, context or {})
        
        # === LINGUISTIC CLUES ===
        evidence_score = self._apply_web_address_linguistic_clues(evidence_score, issue, sentence_obj)
        
        # === STRUCTURAL CLUES ===
        evidence_score = self._apply_technical_structural_clues(evidence_score, context)
        
        # === SEMANTIC CLUES ===
        evidence_score = self._apply_web_address_semantic_clues(evidence_score, issue, text, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _is_functional_url_context(self, url: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if URL is in functional context where specific formatting is required."""
        sent_text = sentence_obj.text.lower()
        
        # Functional contexts where URLs need specific formatting
        functional_indicators = [
            'curl', 'wget', 'fetch', 'request', 'api call', 
            'redirect', 'htaccess', 'rewrite', 'proxy', 'server config'
        ]
        
        return any(indicator in sent_text for indicator in functional_indicators)
    
    def _is_quoted_url_example(self, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if URL is in quoted example."""
        sent_text = sentence_obj.text
        
        # Check for quotes
        quote_chars = ['"', "'", '`', '"', '"', ''', ''']
        return any(quote_char in sent_text for quote_char in quote_chars)
    
    def _is_api_documentation_url(self, url: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if URL is in API documentation context."""
        sent_text = sentence_obj.text.lower()
        
        # API documentation indicators - only for strict API specifications
        api_indicators = [
            'openapi spec', 'swagger doc', 'api specification', 'rest specification',
            'graphql schema', 'webhook specification'
        ]
        
        return any(indicator in sent_text for indicator in api_indicators)
    
    def _is_placeholder_url(self, url: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if URL is a placeholder or example."""
        url_lower = url.lower()
        
        # Common placeholder patterns
        placeholder_patterns = [
            'example.com', 'example.org', 'test.com', 'demo.com',
            'your-domain', 'yourdomain', 'localhost', '127.0.0.1',
            'placeholder', 'sample', 'template'
        ]
        
        return any(pattern in url_lower for pattern in placeholder_patterns)
    
    def _apply_web_address_linguistic_clues(self, evidence_score: float, issue: Dict[str, Any], sentence_obj) -> float:
        """Apply linguistic clues specific to web address analysis."""
        sent_text = sentence_obj.text.lower()
        issue_type = issue.get('subtype', '')
        
        # Direct instruction context increases evidence
        instruction_indicators = [
            'visit', 'go to', 'navigate', 'access', 'browse', 'open',
            'click', 'follow', 'use this', 'link to'
        ]
        
        if any(indicator in sent_text for indicator in instruction_indicators):
            evidence_score += 0.15
        
        # Documentation context increases evidence for consistency
        doc_indicators = [
            'documentation', 'guide', 'tutorial', 'manual', 'reference',
            'how to', 'instructions', 'steps'
        ]
        
        if any(indicator in sent_text for indicator in doc_indicators):
            evidence_score += 0.1
        
        # Multiple URLs in same context suggest need for consistency
        url_count = len(re.findall(r'https?://', sent_text))
        if url_count > 1:
            evidence_score += 0.1
        
        return evidence_score
    
    def _apply_web_address_semantic_clues(self, evidence_score: float, issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Apply semantic clues specific to web address usage."""
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Technical documentation should have consistent URL formatting
        if content_type in ['technical', 'api', 'developer', 'tutorial']:
            evidence_score += 0.15
        elif content_type in ['guide', 'manual', 'procedural']:
            evidence_score += 0.1
        
        # Web/software domains expect proper URL formatting
        if domain in ['web', 'software', 'application', 'development']:
            evidence_score += 0.1
        elif domain in ['api', 'backend', 'frontend']:
            evidence_score += 0.15
        
        # General audiences need consistent, clear URLs
        if audience in ['beginner', 'general', 'user']:
            evidence_score += 0.1
        elif audience in ['developer', 'technical_writer']:
            evidence_score += 0.15
        
        return evidence_score
