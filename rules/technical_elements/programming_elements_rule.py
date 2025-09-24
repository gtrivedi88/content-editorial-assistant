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
        """
        ENHANCED: Check if programming keyword is being used as a legitimate verb using linguistic intelligence.
        
        Similar to CommandsRule enhancement - uses dependency parsing and context analysis
        to distinguish standard verb usage from programming elements needing formatting.
        """
        sent_text = sentence_obj.text.lower()
        
        # === NEW LINGUISTIC GUARD: Passive voice constructions ===
        # Check if this is part of a passive voice construction (e.g., "is thrown", "was thrown")
        if self._is_passive_voice_construction(token):
            return True  # Passive voice usage is legitimate, not a programming element
        
        # === ENHANCED LINGUISTIC GUARD A: Modal auxiliary verbs (CONTEXT-AWARE) ===
        # Check for modal auxiliary verbs (e.g., "will update", "can select", "should create")
        # BUT only protect if not in programming context
        auxiliary_verbs = [child for child in token.children if child.dep_ == 'aux' and child.pos_ == 'AUX']
        if auxiliary_verbs:
            # Check if this is in a programming context despite modal auxiliary
            programming_context_indicators = self.config_service.get_programming_context_indicators()
            
            if any(indicator in sent_text for indicator in programming_context_indicators):
                # Programming context - check if direct object is programming-related
                programming_objects = self.config_service.get_programming_objects()
                
                for child in token.children:
                    if child.dep_ == 'dobj' and child.lemma_.lower() in programming_objects:
                        return False  # Programming context overrides auxiliary protection
                
                # No programming objects, auxiliary might be protective
                return True
            else:
                # Non-programming context, auxiliary protects verb usage
                return True
        
        # === ENHANCED LINGUISTIC GUARD B: Subject analysis (CONTEXT-AWARE) ===
        # Check the subject of the verb - personal subjects suggest standard usage
        # BUT only if not in a programming context
        subject = None
        for child in token.children:
            if child.dep_ == 'nsubj':
                subject = child
                break
        
        if subject and subject.lemma_.lower() in ['you', 'we', 'they', 'i', 'he', 'she', 'user', 'team', 'person']:
            # Check if this is in a clear programming context despite personal subject
            programming_context_indicators = self.config_service.get_programming_context_indicators()
            
            if any(indicator in sent_text for indicator in programming_context_indicators):
                # Don't treat as legitimate just because of personal subject - check objects first
                programming_objects = self.config_service.get_programming_objects()
                
                # Check if direct object is programming-related
                for child in token.children:
                    if child.dep_ == 'dobj' and child.lemma_.lower() in programming_objects:
                        return False  # Programming context overrides personal subject
                
                # If no programming objects found, personal subject might be legitimate
                return True
            else:
                # No programming context, personal subject indicates legitimate usage
                return True
        
        # === ENHANCED LINGUISTIC GUARD C: Business/general context objects ===
        # STRICT: Only truly non-programming objects that clearly indicate business/general usage
        non_programming_objects = self.config_service.get_non_programming_objects()
        programming_objects = self.config_service.get_programming_objects()
        
        # Look for non-programming direct objects or prepositional objects
        for child in token.children:
            if child.dep_ in ['dobj', 'pobj']:
                child_lemma = child.lemma_.lower()
                # Only return True for clearly non-programming objects
                if child_lemma in non_programming_objects:
                    return True  # Standard business/general usage
                # Explicitly don't return True for programming objects
                elif child_lemma in programming_objects:
                    return False  # This is a programming context that should be flagged
        
        # === ENHANCED LINGUISTIC GUARD D: Infinitive usage ===
        # Check if this is an infinitive usage (e.g., "need to update", "want to select")
        # Fixed: "to" is a child of the verb token, not the head verb
        infinitive_verbs = self.config_service.get_infinitive_verbs()
        if hasattr(token, 'head') and token.head.lemma_.lower() in infinitive_verbs:
            # Check if this token has "to" as an auxiliary child
            for child in token.children:
                if child.dep_ == 'aux' and child.lemma_.lower() == 'to':
                    return True  # Infinitive usage is standard verb usage
            
            # Additional check: if token is xcomp of an infinitive verb, it's infinitive usage
            if hasattr(token, 'dep_') and token.dep_ == 'xcomp':
                return True
        
        # === ENHANCED LINGUISTIC GUARD E: Sentence position analysis ===
        # Check if this is at the beginning of an imperative sentence without programming context
        sent_tokens = list(sentence_obj)
        token_position = None
        for i, sent_token in enumerate(sent_tokens):
            if sent_token.i == token.i:
                token_position = i
                break
        
        if token_position == 0:  # First word in sentence
            # Check if this is a general imperative, not programming command
            # Look for business/general context indicators
            general_context_indicators = self.config_service.get_general_context_indicators()
            
            if any(indicator in sent_text for indicator in general_context_indicators):
                return True  # General imperative, not programming command
        
        # === ORIGINAL YAML CONFIGURATION CHECK ===
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
        
        # Check for legitimate patterns from YAML
        if legitimate_patterns:
            for pattern in legitimate_patterns:
                if pattern in sent_text:
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
        """Enhanced linguistic clues specific to programming analysis."""
        sent_text = sentence_obj.text.lower()
        keyword = issue.get('keyword', '')
        token = issue.get('token')
        
        # === ENHANCED PROGRAMMING CONTEXT DETECTION ===
        # Load programming context indicators from YAML
        programming_indicators = self.config_service.get_programming_context_indicators()
        
        if any(indicator in sent_text for indicator in programming_indicators):
            evidence_adjustment = self.config_service.get_evidence_adjustment('programming_context_boost', 0.2)
            evidence_score += evidence_adjustment  # Clear programming context
        
        # === ENHANCED IMPERATIVE DETECTION ===
        # More sophisticated imperative detection
        if token and hasattr(token, 'tag_') and token.tag_ == 'VB':  # Base form verb (imperative)
            # Check if this is at sentence start (imperative mood)
            sent_tokens = list(sentence_obj)
            if sent_tokens and sent_tokens[0].i == token.i:
                imperative_boost = self.config_service.get_evidence_adjustment('imperative_command_boost', 0.15)
                evidence_score += imperative_boost  # Imperative programming command
        
        # === ENHANCED DIRECT OBJECT ANALYSIS ===
        if token:
            # Load technical objects from YAML configuration
            technical_objects = self.config_service.get_programming_objects()
            
            for child in token.children:
                if child.dep_ == 'dobj' and child.lemma_.lower() in technical_objects:
                    technical_object_boost = self.config_service.get_evidence_adjustment('technical_object_boost', 0.25)
                    evidence_score += technical_object_boost  # Strong technical object suggests programming misuse
                    break
        
        # === ENHANCED PROGRAMMING PATTERN DETECTION ===
        # Generate dynamic programming patterns from YAML templates
        programming_patterns = self.config_service.generate_programming_patterns(keyword)
        
        if any(pattern in sent_text for pattern in programming_patterns):
            pattern_boost = self.config_service.get_evidence_adjustment('programming_pattern_boost', 0.2)
            evidence_score += pattern_boost  # Specific programming usage patterns
        
        # === TECHNICAL PREPOSITION ANALYSIS ===
        # Check for technical prepositional phrases that indicate programming context
        if token:
            for child in token.children:
                if child.dep_ == 'prep':
                    prep_phrase = child.text.lower()
                    # Look at what follows the preposition
                    for grandchild in child.children:
                        if grandchild.dep_ == 'pobj':
                            prep_object = grandchild.lemma_.lower()
                            # Use programming objects from YAML for consistency
                            programming_objects = self.config_service.get_programming_objects()
                            if prep_object in programming_objects:
                                preposition_boost = self.config_service.get_evidence_adjustment('technical_preposition_boost', 0.15)
                                evidence_score += preposition_boost  # Technical prepositional context
                                break
        
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

    def _is_passive_voice_construction(self, token) -> bool:
        """
        Check if token is part of a passive voice construction using linguistic analysis.
        
        Returns True for cases like:
        - "is thrown" (auxiliary + past participle)
        - "was selected" (auxiliary + past participle)  
        - "will be executed" (modal + auxiliary + past participle)
        
        This prevents flagging legitimate passive voice as programming elements.
        """
        # Check if this token is a past participle (VBN) with auxiliary head
        if hasattr(token, 'tag_') and token.tag_ == 'VBN':
            # Check if the head is an auxiliary verb indicating passive voice
            if hasattr(token, 'head') and hasattr(token.head, 'pos_'):
                head = token.head
                
                # Direct auxiliary head (is thrown, was thrown)
                if head.pos_ == 'AUX' and head.lemma_.lower() in self._get_passive_auxiliaries():
                    return True
                
                # Check for auxiliary chains (will be thrown, has been thrown)
                if head.pos_ == 'VERB' and head.tag_ == 'VBN':  # Compound passive
                    for grandparent in head.children:
                        if grandparent.pos_ == 'AUX' and grandparent.lemma_.lower() in self._get_passive_auxiliaries():
                            return True
                
                # Check if any auxiliary points to this verb via auxpass dependency
                for sibling in token.head.children if token.head else []:
                    if sibling.dep_ == 'auxpass' and sibling.pos_ == 'AUX':
                        return True
        
        return False

    def _get_passive_auxiliaries(self) -> set:
        """
        Get passive auxiliary verbs from YAML configuration.
        Production-ready approach using vocabulary service.
        """
        # Get from YAML configuration using same pattern as other methods
        try:
            # Load raw YAML config to access passive_voice_patterns
            import yaml
            with open(self.config_service.config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f) or {}
            
            passive_config = full_config.get('passive_voice_patterns', {})
            auxiliaries = passive_config.get('auxiliary_verbs', [])
            
            if auxiliaries:
                return set(auxiliaries)
        except Exception:
            # If YAML loading fails, use fallback
            pass
        
        # Fallback to standard passive auxiliaries
        return {'be', 'is', 'am', 'are', 'was', 'were', 'been', 'being'}
