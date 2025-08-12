"""
Base Technical Elements Rule (Production-Grade)
Production-grade base class with surgical zero false positive guards for technical elements.
Implements common technical context analysis and evidence-based rule development standards.
"""

from typing import List, Dict, Any, Optional
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

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None


class BaseTechnicalRule(BaseRule):
    """
    PRODUCTION-GRADE: Abstract base class for all technical element rules with surgical zero false positive guards.
    
    Provides common technical context analysis including:
    - Technical domain detection and appropriateness checking
    - Code context identification and protection
    - Technical terminology validation
    - API/SDK/library reference handling
    - File path and identifier recognition
    
    Features:
    - Surgical zero false positive guards for technical contexts
    - Evidence-based rule development support
    - Technical linguistic anchor utilities
    - Context-aware messaging for technical documentation
    """

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for a specific technical element violation.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the analyze method.")
    
    # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR TECHNICAL ELEMENTS ===
    
    def _apply_surgical_zero_false_positive_guards_technical(self, token, context: Dict[str, Any]) -> bool:
        """
        Apply ultra-precise technical-specific guards that eliminate false positives
        while preserving ALL legitimate technical element violations.
        
        Returns True if this token should be ignored (zero evidence).
        """
        
        # === GUARD 1: CODE BLOCKS AND TECHNICAL LITERALS ===
        # Never flag content in code blocks, inline code, or literal blocks
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return True  # Code has its own formatting rules
            
        # === GUARD 2: TECHNICAL IDENTIFIERS ===
        # Don't flag technical identifiers, file paths, URLs, etc.
        if hasattr(token, 'text'):
            token_text = token.text
            
            # File paths and directory structures
            if '/' in token_text or '\\' in token_text:
                return True  # File paths are technical identifiers
                
            # URLs and domain names
            if hasattr(token, 'like_url') and token.like_url:
                return True  # URLs have their own conventions
                
            # Common technical patterns
            if re.match(r'^[A-Z_][A-Z0-9_]*$', token_text):  # CONSTANTS
                return True  # Programming constants
                
            if re.match(r'^[a-z]+[A-Z][a-zA-Z0-9]*$', token_text):  # camelCase
                return True  # Programming identifiers
                
            if re.match(r'^[a-z]+(_[a-z0-9]+)*$', token_text):  # snake_case
                return True  # Programming identifiers
                
            # Version numbers and technical codes
            if re.match(r'^v?\d+\.\d+(\.\d+)?(-[a-zA-Z0-9]+)*$', token_text):
                return True  # Version numbers
        
        # === GUARD 3: NAMED ENTITIES (TECHNICAL) ===
        # Don't flag recognized technical entities
        if hasattr(token, 'ent_type_') and token.ent_type_:
            if token.ent_type_ in ['ORG', 'PRODUCT', 'GPE', 'PERSON']:
                return True  # Company names, product names, etc.
        
        # === GUARD 4: TECHNICAL TERMINOLOGY CONTEXT ===
        # Don't flag technical terms in technical documentation contexts
        if self._is_in_technical_context(token, context):
            return True  # Technical documentation allows technical language
            
        # === GUARD 5: API/SDK/LIBRARY REFERENCES ===
        # Don't flag references to APIs, SDKs, libraries, frameworks
        if self._is_api_or_library_reference(token, context):
            return True  # API references have their own naming conventions
            
        return False  # No guards triggered, proceed with analysis
    
    def _is_in_technical_context(self, token, context: Dict[str, Any]) -> bool:
        """
        Check if token is in a context where technical language is appropriate.
        Only returns True for genuine technical contexts.
        """
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        # Technical content types
        if content_type in ['technical', 'api', 'sdk', 'developer', 'engineering']:
            return True
            
        # Technical domains
        if domain in ['software', 'programming', 'devops', 'engineering', 'technology']:
            return True
            
        # Check for technical indicators in surrounding context
        if hasattr(token, 'sent'):
            sent_text = token.sent.text.lower()
            technical_indicators = [
                'api', 'sdk', 'framework', 'library', 'database', 'server',
                'function', 'method', 'class', 'object', 'variable', 'parameter',
                'configuration', 'installation', 'deployment', 'repository'
            ]
            
            if any(indicator in sent_text for indicator in technical_indicators):
                return True
        
        return False
    
    def _is_api_or_library_reference(self, token, context: Dict[str, Any]) -> bool:
        """
        Check if token is referencing an API, SDK, library, or framework.
        Only returns True for genuine technical references.
        """
        if not hasattr(token, 'text'):
            return False
            
        token_text = token.text.lower()
        
        # Common API/SDK patterns
        api_patterns = [
            'api', 'sdk', 'framework', 'library', 'plugin', 'extension',
            'service', 'endpoint', 'namespace', 'module', 'package'
        ]
        
        if any(pattern in token_text for pattern in api_patterns):
            return True
            
        # Check for common technical prefixes/suffixes
        technical_affixes = [
            'json', 'xml', 'http', 'https', 'rest', 'soap', 'grpc',
            'oauth', 'jwt', 'ssl', 'tls', 'tcp', 'udp', 'smtp', 'ftp'
        ]
        
        if any(affix in token_text for affix in technical_affixes):
            return True
            
        # Check surrounding context for API references
        if hasattr(token, 'sent'):
            sent_text = token.sent.text.lower()
            api_context_indicators = [
                'documentation', 'reference', 'guide', 'tutorial',
                'implementation', 'integration', 'configuration'
            ]
            
            if any(indicator in sent_text for indicator in api_context_indicators):
                # Look for technical terms nearby
                if any(tech in sent_text for tech in api_patterns + technical_affixes):
                    return True
        
        return False
    
    # === TECHNICAL LINGUISTIC ANCHORS ===
    
    def _get_technical_linguistic_anchors(self) -> Dict[str, Any]:
        """
        Get technical-specific linguistic anchors for evidence calculation.
        Returns patterns and terms specific to technical documentation.
        """
        return {
            'technical_terms': {
                'programming': ['function', 'method', 'class', 'object', 'variable', 'parameter'],
                'infrastructure': ['server', 'database', 'network', 'cloud', 'container'],
                'api': ['endpoint', 'request', 'response', 'authentication', 'authorization'],
                'tools': ['framework', 'library', 'plugin', 'extension', 'compiler', 'debugger']
            },
            'acceptable_abbreviations': [
                'API', 'SDK', 'JSON', 'XML', 'HTTP', 'HTTPS', 'REST', 'SOAP',
                'OAuth', 'JWT', 'SSL', 'TLS', 'TCP', 'UDP', 'SMTP', 'FTP',
                'SQL', 'NoSQL', 'CLI', 'GUI', 'IDE', 'VM', 'OS', 'CPU', 'RAM'
            ],
            'technical_file_extensions': [
                '.js', '.py', '.java', '.cpp', '.c', '.h', '.php', '.rb',
                '.go', '.rs', '.swift', '.kt', '.ts', '.jsx', '.vue',
                '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.conf'
            ],
            'technical_patterns': {
                'version_numbers': r'v?\d+\.\d+(\.\d+)?(-[a-zA-Z0-9]+)*',
                'camel_case': r'[a-z]+[A-Z][a-zA-Z0-9]*',
                'snake_case': r'[a-z]+(_[a-z0-9]+)*',
                'kebab_case': r'[a-z]+(-[a-z0-9]+)*',
                'constants': r'[A-Z_][A-Z0-9_]*',
                'file_paths': r'[a-zA-Z0-9_/\\.-]+\.[a-zA-Z0-9]+',
                'urls': r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9._~:/?#[\]@!$&\'()*+,;=-]*)?'
            }
        }
    
    # === EVIDENCE-AWARE MESSAGING FOR TECHNICAL RULES ===
    
    def _generate_evidence_aware_message(self, issue: Dict[str, Any], evidence_score: float, rule_type: str) -> str:
        """
        Generate evidence-aware error message for technical rules.
        Higher evidence = more confident, direct messaging.
        Lower evidence = softer, more tentative messaging.
        """
        flagged_text = issue.get('text', issue.get('flagged_text', ''))
        
        if evidence_score > 0.85:
            # High confidence -> Direct, authoritative message
            return f"Technical element '{flagged_text}' requires formatting adjustment for professional documentation."
        elif evidence_score > 0.6:
            # Medium confidence -> Balanced suggestion
            return f"Consider adjusting the formatting of '{flagged_text}' to match technical writing standards."
        else:
            # Low confidence -> Gentle, context-aware suggestion
            return f"'{flagged_text}' may benefit from formatting adjustment for consistency with technical documentation."
    
    def _generate_evidence_aware_suggestions(self, issue: Dict[str, Any], evidence_score: float, context: Dict[str, Any], rule_type: str) -> List[str]:
        """
        Generate evidence-aware suggestions for technical rules.
        Higher evidence = more confident, direct suggestions.
        Lower evidence = softer, more optional suggestions.
        """
        suggestions = []
        flagged_text = issue.get('text', issue.get('flagged_text', ''))
        
        if evidence_score > 0.8:
            # High confidence -> Direct, confident suggestions
            suggestions.append(f"Format '{flagged_text}' according to technical documentation standards.")
            suggestions.append("This formatting is required for professional technical writing.")
        elif evidence_score > 0.6:
            # Medium confidence -> Balanced suggestions  
            suggestions.append(f"Consider reformatting '{flagged_text}' for better consistency.")
            suggestions.append("Proper formatting improves technical documentation readability.")
        else:
            # Low confidence -> Gentle, optional suggestions
            suggestions.append(f"'{flagged_text}' formatting is acceptable but could be optimized.")
            suggestions.append("This is a minor formatting suggestion for consistency.")
        
        # Add context-specific suggestions
        content_type = context.get('content_type', '')
        if content_type == 'api':
            suggestions.append("API documentation benefits from consistent technical formatting.")
        elif content_type == 'tutorial':
            suggestions.append("Tutorial consistency helps readers follow technical steps.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # === TECHNICAL CLUE METHODS ===
    
    def _apply_technical_linguistic_clues(self, evidence_score: float, token, sentence) -> float:
        """Apply linguistic clues specific to technical elements."""
        if not hasattr(token, 'text'):
            return evidence_score
            
        # Technical abbreviations in all caps are often acceptable
        if token.text.isupper() and len(token.text) <= 5:
            evidence_score -= 0.2  # Likely technical acronym
            
        # Technical compounds are often acceptable
        if hasattr(token, 'dep_') and token.dep_ == 'compound':
            evidence_score -= 0.1  # Technical compound terms
            
        # Check for technical context words nearby
        if hasattr(token, 'sent'):
            sent_text = token.sent.text.lower()
            technical_words = ['api', 'sdk', 'framework', 'library', 'documentation']
            if any(word in sent_text for word in technical_words):
                evidence_score -= 0.1  # Technical context
        
        return evidence_score
    
    def _apply_technical_structural_clues(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """Apply structural clues specific to technical documentation."""
        block_type = context.get('block_type', 'paragraph')
        
        # Technical documentation structures
        if block_type in ['heading', 'title']:
            evidence_score -= 0.2  # Headings often use technical terms
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.3  # Tables often abbreviate
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.1  # Lists can be more concise
        elif block_type in ['admonition']:
            admonition_type = context.get('admonition_type', '').lower()
            if admonition_type in ['note', 'tip', 'warning']:
                evidence_score -= 0.1  # Technical notes can be brief
        
        return evidence_score
    
    def _apply_technical_semantic_clues(self, evidence_score: float, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic clues specific to technical content."""
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Technical content types are more permissive
        if content_type in ['technical', 'api', 'sdk', 'developer']:
            evidence_score -= 0.2
        elif content_type in ['tutorial', 'guide']:
            evidence_score -= 0.1  # Tutorials can use technical shortcuts
        
        # Technical domains
        if domain in ['software', 'programming', 'engineering', 'devops']:
            evidence_score -= 0.2
        
        # Technical audiences expect technical language
        if audience in ['developer', 'engineer', 'expert']:
            evidence_score -= 0.2
        elif audience in ['technical_writer', 'administrator']:
            evidence_score -= 0.1
        
        return evidence_score
