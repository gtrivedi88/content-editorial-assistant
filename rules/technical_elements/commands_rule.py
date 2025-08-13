"""
Commands Rule (Production-Grade)
Based on IBM Style Guide topic: "Commands"
Evidence-based analysis with surgical zero false positive guards for command usage.
Uses YAML-based configuration for maintainable pattern management.
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
from .services.technical_config_service import TechnicalConfigServices, TechnicalContext
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CommandsRule(BaseTechnicalRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect use of command names as verbs.
    
    Implements rule-specific evidence calculation for:
    - Command names used as verbs instead of proper command syntax
    - Context-aware detection of genuine command misuse vs. legitimate verb usage
    - Technical domain appropriateness checking
    
    Features:
    - YAML-based configuration for maintainable pattern management
    - Surgical zero false positive guards for command contexts
    - Dynamic base evidence scoring based on command specificity
    - Evidence-aware messaging and suggestions for command formatting
    """
    
    def __init__(self):
        """Initialize with YAML configuration service."""
        super().__init__()
        self.config_service = TechnicalConfigServices.commands()
    
    def _get_rule_type(self) -> str:
        return 'technical_commands'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        PRODUCTION-GRADE: Evidence-based analysis for command usage violations.
        
        Implements the required production pattern:
        1. Find potential command misuse using rule-specific detection
        2. Calculate evidence using rule-specific _calculate_command_evidence()
        3. Apply zero false positive guards specific to command analysis
        4. Use evidence-aware messaging and suggestions
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        context = context or {}

        # === STEP 1: Find potential command misuse ===
        potential_issues = self._find_potential_command_issues(doc, text, context)
        
        # === STEP 2: Process each potential issue with evidence calculation ===
        for issue in potential_issues:
            # Calculate rule-specific evidence score
            evidence_score = self._calculate_command_evidence(
                issue, doc, text, context
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                error = self._create_error(
                    sentence=issue['sentence'],
                    sentence_index=issue['sentence_index'],
                    message=self._generate_evidence_aware_message(issue, evidence_score, "command"),
                    suggestions=self._generate_evidence_aware_suggestions(issue, evidence_score, context, "command"),
                    severity='low' if evidence_score < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=issue.get('span', [0, 0]),
                    flagged_text=issue.get('command_word', issue.get('text', ''))
                )
                errors.append(error)
        
        return errors
    
    # === RULE-SPECIFIC METHODS ===
    
    def _find_potential_command_issues(self, doc, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find potential command misuse for evidence assessment.
        Detects command words used as verbs in inappropriate contexts.
        Uses YAML-based configuration for maintainable pattern management.
        """
        issues = []
        
        # Load command patterns from YAML configuration
        command_patterns = self.config_service.get_patterns()
        
        # Build command words dictionary from YAML patterns
        command_words = {}
        for pattern_id, pattern_config in command_patterns.items():
            command_word = pattern_config.pattern
            command_words[command_word] = pattern_config.evidence
        
        for i, sent in enumerate(doc.sents):
            for token in sent:
                command_word = token.lemma_.lower()
                
                # Check if this is a known command word used as a verb
                if (command_word in command_words and 
                    hasattr(token, 'pos_') and token.pos_ == 'VERB'):
                    
                    # Find the pattern config for this command
                    pattern_config = None
                    for pid, pconfig in command_patterns.items():
                        if pconfig.pattern == command_word:
                            pattern_config = pconfig
                            break
                    
                    issues.append({
                        'type': 'command',
                        'subtype': 'command_as_verb',
                        'command_word': command_word,
                        'text': token.text,
                        'sentence': sent.text,
                        'sentence_index': i,
                        'span': [token.idx, token.idx + len(token.text)],
                        'base_evidence': command_words[command_word],
                        'token': token,
                        'sentence_obj': sent,
                        'pattern_config': pattern_config  # Include pattern config for legitimate patterns
                    })
        
        return issues
    
    def _calculate_command_evidence(self, issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for command violations.
        
        Implements rule-specific evidence calculation with:
        - Zero false positive guards for command analysis
        - Dynamic base evidence based on command specificity
        - Context-aware adjustments for technical documentation
        """
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR COMMANDS ===
        # Apply ultra-precise command-specific guards that eliminate false positives
        # while preserving ALL legitimate command violations
        
        token = issue.get('token')
        if not token:
            return 0.0
            
        command_word = issue.get('command_word', '')
        sentence_obj = issue.get('sentence_obj')
        
        # === GUARD 1: LEGITIMATE VERB USAGE ===
        # Don't flag when command words are used as legitimate verbs
        if self._is_legitimate_verb_usage(command_word, token, sentence_obj, context):
            return 0.0  # Legitimate verb usage, not command misuse
            
        # === GUARD 2: QUOTED COMMAND EXAMPLES ===
        # Don't flag command words in direct quotes or examples
        if self._is_in_quoted_command_example(token, sentence_obj, context):
            return 0.0  # Quoted examples are not violations
            
        # === GUARD 3: PROPER COMMAND SYNTAX CONTEXT ===
        # Don't flag when proper command syntax is already present
        if self._has_proper_command_syntax(command_word, sentence_obj, context):
            return 0.0  # Proper command syntax already used
            
        # === GUARD 4: NON-TECHNICAL CONTEXT ===
        # Don't flag common verbs in non-technical contexts
        if self._is_non_technical_verb_context(command_word, sentence_obj, context):
            return 0.0  # Non-technical usage is acceptable
            
        # Apply selective technical guards (skip technical context guard for commands)
        # Commands are violations even in technical contexts when used as verbs
        
        # Check code blocks and literal blocks
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return 0.0  # Code has its own formatting rules
            
        # Check entities (but not technical context)
        if hasattr(token, 'ent_type_') and token.ent_type_:
            if token.ent_type_ in ['ORG', 'PRODUCT', 'GPE', 'PERSON']:
                return 0.0  # Company names, product names, etc.
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = issue.get('base_evidence', 0.7)  # Command-specific base score
        
        # === LINGUISTIC CLUES (COMMAND-SPECIFIC) ===
        evidence_score = self._apply_command_linguistic_clues(evidence_score, issue, sentence_obj)
        
        # === STRUCTURAL CLUES ===
        evidence_score = self._apply_technical_structural_clues(evidence_score, context)
        
        # === SEMANTIC CLUES ===
        evidence_score = self._apply_command_semantic_clues(evidence_score, issue, text, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    # === SURGICAL ZERO FALSE POSITIVE GUARD METHODS ===
    
    def _is_legitimate_verb_usage(self, command_word: str, token, sentence_obj, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this command word being used as a legitimate verb?
        Only returns True for genuine verb usage, not command misuse.
        Uses YAML-based configuration for legitimate patterns.
        """
        sent_text = sentence_obj.text.lower()
        
        # Get pattern config for this command word
        command_patterns = self.config_service.get_patterns()
        pattern_config = None
        for pattern_id, pconfig in command_patterns.items():
            if pconfig.pattern == command_word:
                pattern_config = pconfig
                break
        
        if not pattern_config:
            return False  # Unknown command, conservative approach
        
        # Check against legitimate patterns from YAML
        if pattern_config.legitimate_patterns:
            for legitimate_pattern in pattern_config.legitimate_patterns:
                if legitimate_pattern.lower() in sent_text:
                    return True
        
        # Use YAML-based context analysis for evidence adjustment
        tech_context = TechnicalContext(
            content_type=context.get('content_type', ''),
            audience=context.get('audience', ''),
            domain=context.get('domain', ''),
            block_type=context.get('block_type', '')
        )
        
        # Calculate context-adjusted evidence
        adjusted_evidence = self.config_service.calculate_context_evidence(
            pattern_config.evidence, tech_context
        )
        
        # If context adjustments significantly reduce evidence, likely legitimate usage
        if adjusted_evidence < 0.3:
            return True
        
        return False  # Conservative: flag if uncertain
    
    def _is_in_quoted_command_example(self, token, sentence_obj, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this command word in a quoted example or code block?
        Only returns True for genuine quoted examples, not style violations.
        """
        sent_text = sentence_obj.text
        
        # Check for various quote patterns around the token
        quote_chars = ['"', "'", '`', '"', '"', ''', ''']
        
        # Look for the token within quotes
        for quote_char in quote_chars:
            if quote_char in sent_text:
                # Find quote pairs and check if token is within them
                quote_positions = [i for i, c in enumerate(sent_text) if c == quote_char]
                if len(quote_positions) >= 2:
                    token_start = token.idx - sentence_obj.start_char
                    for i in range(0, len(quote_positions) - 1, 2):
                        if quote_positions[i] < token_start < quote_positions[i + 1]:
                            return True
        
        # Check for code block indicators
        code_indicators = ['```', '`', '<code>', '</code>', '<pre>', '</pre>']
        if any(indicator in sent_text for indicator in code_indicators):
            return True
        
        return False
    
    def _has_proper_command_syntax(self, command_word: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Does the sentence already use proper command syntax?
        Only returns True when proper syntax is genuinely present.
        """
        sent_text = sentence_obj.text.lower()
        
        # Proper command syntax patterns
        proper_syntax_patterns = [
            f'use the {command_word} command',
            f'run the {command_word} command',
            f'execute the {command_word} command',
            f'the {command_word} command',
            f'{command_word} command',
            f'`{command_word}`',  # Inline code
            f'"{command_word}"',  # Quoted command
            f"'{command_word}'",  # Single quoted command
        ]
        
        # Check if proper syntax is already used
        for pattern in proper_syntax_patterns:
            if pattern in sent_text:
                return True
        
        # Check for command syntax indicators (only if they relate to this specific command)
        command_syntax_indicators = [
            f'run {command_word}', f'execute {command_word}', f'use {command_word}',
            'command line', 'command syntax', 'command usage'
        ]
        
        if any(indicator in sent_text for indicator in command_syntax_indicators):
            return True
        
        return False
    
    def _is_non_technical_verb_context(self, command_word: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this command word used in a non-technical context?
        Only returns True for genuine non-technical usage.
        """
        sent_text = sentence_obj.text.lower()
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        # Non-technical content types
        if content_type in ['marketing', 'narrative', 'general', 'business']:
            # Common verbs that are acceptable in non-technical contexts
            non_technical_verbs = ['load', 'save', 'run', 'stop', 'start', 'update', 'remove', 'restore']
            if command_word in non_technical_verbs:
                return True
        
        # Non-technical domains
        if domain in ['business', 'marketing', 'general', 'finance', 'healthcare']:
            non_technical_verbs = ['load', 'save', 'run', 'stop', 'start', 'update', 'remove', 'restore']
            if command_word in non_technical_verbs:
                return True
        
        # Check for non-technical context indicators
        non_technical_indicators = [
            'business', 'company', 'organization', 'team', 'meeting',
            'project', 'client', 'customer', 'user experience', 'human resources'
        ]
        
        if any(indicator in sent_text for indicator in non_technical_indicators):
            # Only for common verbs, not technical commands
            common_verbs = ['save', 'run', 'start', 'stop', 'update', 'load']
            if command_word in common_verbs:
                return True
        
        return False
    
    # === CLUE METHODS ===

    def _apply_command_linguistic_clues(self, evidence_score: float, issue: Dict[str, Any], sentence_obj) -> float:
        """Apply linguistic clues specific to command analysis."""
        sent_text = sentence_obj.text
        command_word = issue.get('command_word', '')
        
        # Check for imperative mood (command-like usage)
        if sent_text.strip().startswith(command_word.capitalize()):
            evidence_score += 0.2  # Imperative mood suggests command usage
        
        # Check for direct object that suggests technical usage
        technical_objects = [
            'file', 'data', 'database', 'table', 'record', 'system',
            'application', 'program', 'script', 'module', 'package'
        ]
        
        if any(obj in sent_text.lower() for obj in technical_objects):
            evidence_score += 0.1  # Technical objects suggest command context
        
        # Check for lack of proper command formatting
        if '`' not in sent_text and '"' not in sent_text and "'" not in sent_text:
            evidence_score += 0.1  # No code formatting suggests misuse
        
        return evidence_score

    def _apply_command_semantic_clues(self, evidence_score: float, issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Apply semantic clues specific to command usage."""
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        command_word = issue.get('command_word', '')
        
        # Stricter standards for technical documentation
        if content_type in ['technical', 'api', 'developer', 'tutorial']:
            evidence_score += 0.2  # Technical docs should use proper command syntax
        elif content_type in ['procedural', 'guide']:
            evidence_score += 0.1  # Procedural docs benefit from proper syntax
        
        # Domain-specific adjustments
        if domain in ['software', 'programming', 'devops', 'engineering']:
            evidence_score += 0.15  # Technical domains require proper command syntax
        elif domain in ['database', 'system_administration']:
            evidence_score += 0.2  # System domains are very strict about command usage
        
        # Audience-specific adjustments
        if audience in ['developer', 'engineer', 'system_administrator']:
            evidence_score += 0.1  # Technical audiences expect proper syntax
        elif audience in ['beginner', 'general']:
            evidence_score += 0.15  # Beginners need clear command examples
        
        # Command-specific adjustments
        highly_technical_commands = ['import', 'export', 'install', 'uninstall', 'configure', 'deploy']
        if command_word in highly_technical_commands:
            evidence_score += 0.1  # These are clearly technical commands
        
        return evidence_score
