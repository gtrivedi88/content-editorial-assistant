"""
Commands Rule (Production-Grade)
Based on IBM Style Guide topic: "Commands"
Evidence-based analysis with surgical zero false positive guards for command usage.
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
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
    - Surgical zero false positive guards for command contexts
    - Dynamic base evidence scoring based on command specificity
    - Evidence-aware messaging and suggestions for command formatting
    """
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
        """
        issues = []
        
        # Command words with their base evidence scores based on specificity
        command_words = {
            # High specificity command words (clearly technical commands)
            "import": 0.85,  # Very specific programming/database command
            "export": 0.85,  # Very specific data export command
            "install": 0.8,   # Specific software installation command
            "uninstall": 0.85, # Very specific software removal command
            "configure": 0.75, # Configuration command
            "deploy": 0.8,     # Deployment command
            
            # Medium specificity command words (can be legitimate verbs)
            "load": 0.6,      # Can be legitimate verb (load the truck)
            "save": 0.5,      # Common verb with legitimate uses
            "run": 0.4,       # Very common verb
            "stop": 0.4,      # Very common verb
            "start": 0.4,     # Very common verb
            
            # Lower specificity command words (need more context)
            "backup": 0.65,   # Can be noun/verb
            "restore": 0.6,   # Can be legitimate verb
            "update": 0.5,    # Common verb
            "delete": 0.6,    # Somewhat technical
            "remove": 0.5,    # Common verb
        }
        
        for i, sent in enumerate(doc.sents):
            for token in sent:
                command_word = token.lemma_.lower()
                
                # Check if this is a known command word used as a verb
                if (command_word in command_words and 
                    hasattr(token, 'pos_') and token.pos_ == 'VERB'):
                    
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
                        'sentence_obj': sent
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
            
        # Apply common technical guards (code blocks, entities, etc.)
        if self._apply_surgical_zero_false_positive_guards_technical(token, context):
            return 0.0
        
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
        """
        sent_text = sentence_obj.text.lower()
        
        # Common legitimate verb usages that should not be flagged
        legitimate_patterns = {
            'load': [
                'load the truck', 'load the car', 'load the dishwasher', 'load cargo',
                'load passengers', 'load freight', 'load materials', 'load equipment'
            ],
            'save': [
                'save money', 'save time', 'save energy', 'save lives', 'save the day',
                'save for retirement', 'save face', 'save space', 'save effort'
            ],
            'run': [
                'run a business', 'run a marathon', 'run for office', 'run errands',
                'run out of', 'run late', 'run fast', 'run smoothly', 'run efficiently'
            ],
            'stop': [
                'stop the car', 'stop talking', 'stop working', 'stop the bleeding',
                'stop sign', 'stop and think', 'stop by', 'stop over'
            ],
            'start': [
                'start the car', 'start a business', 'start over', 'start fresh',
                'start early', 'start late', 'start again', 'start now'
            ],
            'update': [
                'update the record', 'update information', 'update status',
                'update progress', 'keep you updated', 'stay updated'
            ],
            'remove': [
                'remove stains', 'remove obstacles', 'remove from office',
                'remove the lid', 'remove carefully', 'remove completely'
            ],
            'restore': [
                'restore health', 'restore peace', 'restore order', 'restore balance',
                'restore confidence', 'restore faith', 'restore trust'
            ]
        }
        
        # Check if this matches a legitimate verb pattern
        if command_word in legitimate_patterns:
            for pattern in legitimate_patterns[command_word]:
                if pattern in sent_text:
                    return True
        
        # Check for general legitimate verb indicators
        legitimate_indicators = [
            'to ' + command_word,  # Infinitive usage
            'will ' + command_word,  # Future tense
            'would ' + command_word,  # Conditional
            'should ' + command_word,  # Modal
            'can ' + command_word,  # Modal
            'must ' + command_word,  # Modal
        ]
        
        for indicator in legitimate_indicators:
            if indicator in sent_text:
                # Check if this is followed by non-technical objects
                non_technical_objects = [
                    'money', 'time', 'energy', 'life', 'day', 'business', 'office',
                    'car', 'truck', 'house', 'door', 'window', 'person', 'people'
                ]
                if any(obj in sent_text for obj in non_technical_objects):
                    return True
        
        return False
    
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
        
        # Check for command syntax indicators
        command_syntax_indicators = [
            'command line', 'terminal', 'shell', 'prompt', 'execute',
            'run command', 'command syntax', 'command usage'
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
