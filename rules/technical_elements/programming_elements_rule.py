"""
Programming Elements Rule (Production-Grade)
Based on IBM Style Guide topic: "Programming elements"
Evidence-based analysis with surgical zero false positive guards for programming keyword usage.
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
from .services.technical_config_service import TechnicalConfigServices, TechnicalContext
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ProgrammingElementsRule(BaseTechnicalRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect use of programming keywords as verbs.
    
    Features:
    - YAML-based configuration for maintainable pattern management
    - Surgical zero false positive guards for programming contexts
    - Dynamic base evidence scoring based on keyword specificity
    - Evidence-aware messaging for technical documentation
    """
    
    def __init__(self):
        """Initialize with YAML configuration service."""
        super().__init__()
        self.config_service = TechnicalConfigServices.programming()
    
    def _get_rule_type(self) -> str:
        return 'technical_programming_elements'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        PRODUCTION-GRADE: Evidence-based analysis for programming keyword violations.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        context = context or {}

        # === STEP 1: Find potential programming keyword issues ===
        potential_issues = self._find_potential_programming_issues(doc, text, context)
        
        # === STEP 2: Process each potential issue with evidence calculation ===
        for issue in potential_issues:
            # Calculate rule-specific evidence score
            evidence_score = self._calculate_programming_evidence(
                issue, doc, text, context
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                error = self._create_error(
                    sentence=issue['sentence'],
                    sentence_index=issue['sentence_index'],
                    message=self._generate_evidence_aware_message(issue, evidence_score, "programming"),
                    suggestions=self._generate_evidence_aware_suggestions(issue, evidence_score, context, "programming"),
                    severity='low' if evidence_score < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=issue.get('span', [0, 0]),
                    flagged_text=issue.get('flagged_text', issue.get('text', ''))
                )
                errors.append(error)
        
        return errors
    
    def _find_potential_programming_issues(self, doc, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential programming keyword issues for evidence assessment using YAML configuration."""
        issues = []
        
        # Load programming keywords from YAML configuration
        all_patterns = self.config_service.get_patterns()
        programming_keywords = {}
        
        for pattern_id, pattern_config in all_patterns.items():
            if hasattr(pattern_config, 'pattern'):
                # This is a programming keyword pattern
                keyword = pattern_config.pattern
                programming_keywords[keyword] = pattern_config.evidence
        
        for i, sent in enumerate(doc.sents):
            for token in sent:
                keyword = token.lemma_.lower()
                
                # Check if this is a programming keyword used as a verb
                if (keyword in programming_keywords and 
                    hasattr(token, 'pos_') and token.pos_ == 'VERB'):
                    
                    # Find corresponding pattern config for additional details
                    pattern_config = None
                    for pid, config in all_patterns.items():
                        if hasattr(config, 'pattern') and config.pattern == keyword:
                            pattern_config = config
                            break
                    
                    issues.append({
                        'type': 'programming',
                        'subtype': 'keyword_as_verb',
                        'keyword': keyword,
                        'text': token.text,
                        'sentence': sent.text,
                        'sentence_index': i,
                        'span': [token.idx, token.idx + len(token.text)],
                        'base_evidence': programming_keywords[keyword],
                        'flagged_text': token.text,
                        'token': token,
                        'sentence_obj': sent,
                        'pattern_config': pattern_config
                    })
        
        return issues
    
    def _calculate_programming_evidence(self, issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence score for programming keyword violations."""
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR PROGRAMMING ===
        token = issue.get('token')
        if not token:
            return 0.0
            
        keyword = issue.get('keyword', '')
        sentence_obj = issue.get('sentence_obj')
        
        # === GUARD 1: LEGITIMATE VERB USAGE ===
        if self._is_legitimate_verb_usage_programming(keyword, token, sentence_obj, context):
            return 0.0  # Legitimate verb usage, not keyword misuse
            
        # === GUARD 2: PROPER PROGRAMMING SYNTAX CONTEXT ===
        if self._has_proper_programming_syntax(keyword, sentence_obj, context):
            return 0.0  # Proper programming syntax already used
            
        # === GUARD 3: NON-PROGRAMMING CONTEXT ===
        if self._is_non_programming_context(keyword, sentence_obj, context):
            return 0.0  # Not referring to programming operations
            
        # === GUARD 4: CODE EXAMPLES AND DOCUMENTATION ===
        if self._is_code_documentation_context(keyword, sentence_obj, context):
            return 0.0  # Code documentation allows flexible language
            
        # Apply selective technical guards (skip technical context guard for programming elements)
        # Programming element violations should be flagged even in technical contexts
        
        # Only check code blocks and entities
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return 0.0  # Code blocks have their own formatting rules
            
        # Check entities
        if hasattr(token, 'ent_type_') and token.ent_type_:
            if token.ent_type_ in ['ORG', 'PRODUCT', 'GPE', 'PERSON']:
                return 0.0  # Company names, product names, etc.
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = issue.get('base_evidence', 0.7)
        
        # === CONTEXT ADJUSTMENTS FROM YAML ===
        evidence_score = self.config_service.calculate_context_evidence(evidence_score, context or {})
        
        # === LINGUISTIC CLUES ===
        evidence_score = self._apply_programming_linguistic_clues(evidence_score, issue, sentence_obj)
        
        # === STRUCTURAL CLUES ===
        evidence_score = self._apply_technical_structural_clues(evidence_score, context)
        
        # === SEMANTIC CLUES ===
        evidence_score = self._apply_programming_semantic_clues(evidence_score, issue, text, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _is_legitimate_verb_usage_programming(self, keyword: str, token, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if programming keyword is being used as a legitimate verb using YAML configuration."""
        sent_text = sentence_obj.text.lower()
        
        # Get legitimate patterns from YAML configuration
        all_patterns = self.config_service.get_patterns()
        legitimate_patterns = []
        
        # Find the pattern configuration for this keyword
        for pattern_id, pattern_config in all_patterns.items():
            if (hasattr(pattern_config, 'pattern') and 
                pattern_config.pattern == keyword and
                hasattr(pattern_config, 'legitimate_patterns')):
                legitimate_patterns = pattern_config.legitimate_patterns
                break
        
        # Check for legitimate patterns
        if legitimate_patterns:
            for pattern in legitimate_patterns:
                if pattern in sent_text:
                    return True
        
        # Check for general non-programming verb contexts
        non_programming_objects = [
            'file', 'document', 'content', 'text', 'image', 'item', 'option',
            'user', 'person', 'team', 'business', 'house', 'meeting'
        ]
        
        # Look for non-programming direct objects
        for child in token.children:
            if child.dep_ in ['dobj', 'pobj'] and child.lemma_.lower() in non_programming_objects:
                return True
        
        return False
    
    def _has_proper_programming_syntax(self, keyword: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if proper programming syntax is already used."""
        sent_text = sentence_obj.text.lower()
        
        # Proper programming syntax patterns
        proper_syntax_patterns = [
            f'{keyword} statement', f'{keyword} command', f'{keyword} query',
            f'{keyword} operation', f'{keyword} function', f'{keyword} method',
            f'use {keyword}', f'execute {keyword}', f'run {keyword}',
            f'the {keyword} command', f'issue {keyword}', f'perform {keyword}'
        ]
        
        # Check if proper syntax is present
        for pattern in proper_syntax_patterns:
            if pattern in sent_text:
                return True
        
        # Check for code formatting
        if '`' in sent_text or 'code' in sent_text or 'sql' in sent_text:
            return True
        
        return False
    
    def _is_non_programming_context(self, keyword: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if this is not a programming context."""
        sent_text = sentence_obj.text.lower()
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        # Non-programming content types
        if content_type in ['marketing', 'narrative', 'general', 'business']:
            # Common verbs that are acceptable in non-programming contexts
            general_verbs = ['select', 'update', 'create', 'delete', 'call', 'run', 'build']
            if keyword in general_verbs:
                return True
        
        # Non-programming domains
        if domain in ['business', 'marketing', 'general', 'finance', 'healthcare']:
            general_verbs = ['select', 'update', 'create', 'delete', 'call', 'run', 'build']
            if keyword in general_verbs:
                return True
        
        # Check for non-programming context indicators
        non_programming_indicators = [
            'business process', 'user interface', 'manual process', 'workflow',
            'procedure', 'step by step', 'instructions', 'guidelines'
        ]
        
        return any(indicator in sent_text for indicator in non_programming_indicators)
    
    def _is_code_documentation_context(self, keyword: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """Check if this is in code documentation where flexibility is allowed."""
        sent_text = sentence_obj.text.lower()
        
        # Code documentation indicators
        code_doc_indicators = [
            'api documentation', 'code example', 'sample code', 'code snippet',
            'programming guide', 'developer docs', 'technical reference'
        ]
        
        return any(indicator in sent_text for indicator in code_doc_indicators)
    
    def _apply_programming_linguistic_clues(self, evidence_score: float, issue: Dict[str, Any], sentence_obj) -> float:
        """Apply linguistic clues specific to programming analysis."""
        sent_text = sentence_obj.text.lower()
        keyword = issue.get('keyword', '')
        
        # Technical programming context increases evidence
        programming_indicators = [
            'database', 'table', 'query', 'sql', 'api', 'function',
            'method', 'object', 'class', 'variable', 'array'
        ]
        
        if any(indicator in sent_text for indicator in programming_indicators):
            evidence_score += 0.15  # Clear programming context
        
        # Imperative mood suggests command usage
        if sent_text.strip().startswith(keyword):
            evidence_score += 0.1
        
        # Direct object analysis
        token = issue.get('token')
        if token:
            # Look for technical direct objects
            technical_objects = [
                'table', 'record', 'row', 'column', 'database', 'index',
                'object', 'instance', 'variable', 'array', 'function'
            ]
            
            for child in token.children:
                if child.dep_ == 'dobj' and child.lemma_.lower() in technical_objects:
                    evidence_score += 0.2  # Technical object suggests programming misuse
        
        return evidence_score
    
    def _apply_programming_semantic_clues(self, evidence_score: float, issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Apply semantic clues specific to programming usage."""
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        keyword = issue.get('keyword', '')
        
        # Stricter standards for technical documentation
        if content_type in ['technical', 'api', 'developer', 'tutorial']:
            evidence_score += 0.2  # Technical docs should use proper programming syntax
        elif content_type in ['procedural', 'guide']:
            evidence_score += 0.1
        
        # Programming domains expect proper syntax
        if domain in ['software', 'programming', 'database', 'development']:
            evidence_score += 0.15
        elif domain in ['api', 'backend', 'frontend']:
            evidence_score += 0.1
        
        # Technical audiences expect proper programming terminology
        if audience in ['developer', 'programmer', 'engineer']:
            evidence_score += 0.1
        elif audience in ['database_admin', 'system_admin']:
            evidence_score += 0.15
        
        # Highly technical keywords get stricter treatment
        highly_technical_keywords = ['drop', 'truncate', 'alter', 'compile', 'deploy']
        if keyword in highly_technical_keywords:
            evidence_score += 0.1
        
        return evidence_score
