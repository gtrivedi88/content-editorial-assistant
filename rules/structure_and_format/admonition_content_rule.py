"""
Admonition Content Rule - Evidence-Based Analysis
Based on Editorial Enhancement Plan Phase 2

"""
from typing import List, Dict, Any, Optional, Tuple
import re
from .base_structure_rule import BaseStructureRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class AdmonitionContentRule(BaseStructureRule):
    """
    Checks for inappropriate content in admonitions using evidence-based analysis:
    - Code blocks within admonitions (backticks, code fences)
    - Complex procedures that belong in procedure modules  
    - Long explanations that belong in concept modules
    - Tables or complex formatting inappropriate for admonitions
    - Content that doesn't match admonition type (e.g., warnings vs. notes)
    Enhanced with spaCy morphological analysis and contextual awareness.
    """
    def __init__(self):
        """Initialize the rule with admonition content patterns."""
        super().__init__()
        self._initialize_admonition_patterns()
    
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'admonition_content'
    
    def _initialize_admonition_patterns(self):
        """Initialize admonition content detection patterns."""
        self.prohibited_content_patterns = {
            # Code blocks and inline code
            'code_blocks': re.compile(r'```[\s\S]*?```|`[^`\n]+`', re.MULTILINE),
            
            # Procedural steps (numbered lists)
            'procedure_steps': re.compile(r'^\s*\d+\.\s+.+', re.MULTILINE),
            
            # Complex tables
            'complex_tables': re.compile(r'\|.*\|.*\|', re.MULTILINE),
            
            # Long code commands
            'command_blocks': re.compile(r'\$\s+\w+.*(?:\n\s*\$\s+\w+.*)*', re.MULTILINE),
            
            # File path references that suggest code examples
            'file_paths': re.compile(r'/[\w\-./]+|[A-Z]:\\[\w\-\\/.]+|\w+\.\w+', re.MULTILINE),
            
            # Complex formatting (multiple special characters)
            'complex_formatting': re.compile(r'[*_~`]{2,}|[<>{}[\]]+', re.MULTILINE),
            
            # Long URLs
            'long_urls': re.compile(r'https?://[^\s]{50,}', re.MULTILINE)
        }
        
        # Admonition type keywords and their appropriate content
        self.admonition_types = {
            'note': {
                'keywords': ['note', 'info', 'information'],
                'appropriate': ['explanations', 'clarifications', 'additional_info'],
                'inappropriate': ['warnings', 'procedures', 'code']
            },
            'important': {
                'keywords': ['important', 'attention'],
                'appropriate': ['key_points', 'critical_info', 'emphasis'],
                'inappropriate': ['code', 'detailed_procedures']
            },
            'warning': {
                'keywords': ['warning', 'caution', 'danger', 'alert'],
                'appropriate': ['risks', 'precautions', 'consequences'],
                'inappropriate': ['code', 'procedures', 'explanations']
            },
            'tip': {
                'keywords': ['tip', 'hint', 'suggestion'],
                'appropriate': ['helpful_advice', 'shortcuts', 'best_practices'],
                'inappropriate': ['warnings', 'complex_procedures']
            }
        }
        
        # Content length thresholds
        self.length_thresholds = {
            'word_count': 100,      # Maximum words for typical admonition
            'line_count': 10,       # Maximum lines
            'character_count': 800  # Maximum characters
        }
    
    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for admonition content violations:
        - Code blocks within admonitions
        - Inappropriate content for admonition type
        - Excessive length or complexity
        - Poor admonition structure
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Only analyze admonition contexts
        if not self._is_admonition_context(context):
            return errors
        
        # Fallback analysis when nlp is not available
        if not nlp:
            return self._fallback_admonition_analysis(text, sentences, context)

        try:
            doc = nlp(text)
            
            # Analyze prohibited content patterns
            errors.extend(self._analyze_prohibited_content(text, context))
            
            # Analyze admonition content appropriateness
            errors.extend(self._analyze_content_appropriateness(doc, text, context))
            
            # Analyze content length and complexity
            errors.extend(self._analyze_content_complexity(doc, text, context))
            
        except Exception as e:
            # Graceful degradation for SpaCy errors
            return self._fallback_admonition_analysis(text, sentences, context)
        
        return errors
    
    def _is_admonition_context(self, context: Dict[str, Any]) -> bool:
        """Check if the current context is an admonition."""
        block_type = context.get('block_type', '').lower()
        admonition_type = context.get('admonition_type', '').lower()
        
        # Direct admonition context
        if block_type == 'admonition':
            return True
        
        # Check for admonition type indicators
        if admonition_type in self.admonition_types:
            return True
        
        # Check block type for admonition keywords
        for admon_type in self.admonition_types:
            if admon_type in block_type:
                return True
        
        return False
    
    def _fallback_admonition_analysis(self, text: str, sentences: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback admonition analysis without spaCy."""
        errors = []
        
        # Analyze prohibited content patterns
        errors.extend(self._analyze_prohibited_content(text, context))
        
        # Basic length analysis
        errors.extend(self._analyze_content_length_basic(text, context))
        
        return errors
    
    def _analyze_prohibited_content(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze text for prohibited content patterns in admonitions."""
        errors = []
        
        for pattern_name, pattern in self.prohibited_content_patterns.items():
            for match in pattern.finditer(text):
                evidence_score = self._calculate_prohibited_content_evidence(pattern_name, match, text, context)
                
                if evidence_score > 0.1:
                    error = self._create_error(
                        sentence=self._get_sentence_for_match(match, text),
                        sentence_index=0,
                        message=self._get_contextual_admonition_message(pattern_name, evidence_score, context),
                        suggestions=self._generate_smart_admonition_suggestions(pattern_name, evidence_score, context),
                        severity=self._get_admonition_severity(pattern_name, evidence_score),
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(match.start(), match.end()),
                        flagged_text=match.group()[:50] + "..." if len(match.group()) > 50 else match.group(),
                        violation_type=f'admonition_{pattern_name}',
                        pattern_name=pattern_name
                    )
                    errors.append(error)
        
        return errors
    
    def _analyze_content_appropriateness(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze if content is appropriate for the admonition type."""
        errors = []
        
        admonition_type = self._detect_admonition_type(text, context)
        if not admonition_type:
            return errors
        
        inappropriateness_score = self._calculate_content_inappropriateness(doc, text, admonition_type, context)
        
        if inappropriateness_score > 0.1:
            error = self._create_error(
                sentence=text[:100] + "..." if len(text) > 100 else text,
                sentence_index=0,
                message=self._get_inappropriateness_message(admonition_type, inappropriateness_score, context),
                suggestions=self._generate_inappropriateness_suggestions(admonition_type, inappropriateness_score, context),
                severity='medium' if inappropriateness_score > 0.7 else 'low',
                text=text,
                context=context,
                evidence_score=inappropriateness_score,
                span=(0, min(100, len(text))),
                flagged_text="Content appropriateness",
                violation_type='admonition_inappropriate_content',
                admonition_type=admonition_type
            )
            errors.append(error)
        
        return errors
    
    def _analyze_content_complexity(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze if admonition content is too complex or lengthy."""
        errors = []
        
        complexity_evidence = self._calculate_complexity_evidence(doc, text, context)
        
        if complexity_evidence > 0.1:
            error = self._create_error(
                sentence=text[:100] + "..." if len(text) > 100 else text,
                sentence_index=0,
                message=self._get_complexity_message(complexity_evidence, context),
                suggestions=self._generate_complexity_suggestions(complexity_evidence, context),
                severity='low' if complexity_evidence < 0.6 else 'medium',
                text=text,
                context=context,
                evidence_score=complexity_evidence,
                span=(0, len(text)),
                flagged_text="Content complexity",
                violation_type='admonition_excessive_complexity',
                complexity_metrics=self._get_complexity_metrics(doc, text)
            )
            errors.append(error)
        
        return errors
    
    def _analyze_content_length_basic(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Basic content length analysis without spaCy."""
        errors = []
        
        word_count = len(text.split())
        line_count = text.count('\n') + 1
        char_count = len(text)
        
        if (word_count > self.length_thresholds['word_count'] or
            line_count > self.length_thresholds['line_count'] or
            char_count > self.length_thresholds['character_count']):
            
            evidence_score = min(0.9, max(0.3, 
                (word_count / self.length_thresholds['word_count']) * 0.5
            ))
            
            error = self._create_error(
                sentence=text[:100] + "..." if len(text) > 100 else text,
                sentence_index=0,
                message=f"This admonition may be too lengthy for effective use.",
                suggestions=self._generate_length_suggestions(word_count, context),
                severity='low',
                text=text,
                context=context,
                evidence_score=evidence_score,
                span=(0, len(text)),
                flagged_text="Content length",
                violation_type='admonition_excessive_length',
                length_metrics={'word_count': word_count, 'line_count': line_count}
            )
            errors.append(error)
        
        return errors

    # === EVIDENCE CALCULATION ===
    
    def _calculate_prohibited_content_evidence(self, pattern_name: str, match: re.Match, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for prohibited content in admonitions."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if self._apply_zero_false_positive_guards_structure({'text': match.group()}, context):
            return 0.0
        
        # Some admonitions might legitimately reference technical elements
        if self._is_legitimate_technical_reference(match, text, context):
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        base_scores = {
            'code_blocks': 0.9,         # Very strong - code shouldn't be in admonitions
            'procedure_steps': 0.8,     # Strong - procedures belong elsewhere
            'complex_tables': 0.7,      # Good - tables are too complex for admonitions
            'command_blocks': 0.8,      # Strong - commands belong in examples
            'file_paths': 0.5,          # Medium - might be legitimate references
            'complex_formatting': 0.6,  # Medium - depends on context
            'long_urls': 0.4           # Low - might be necessary references
        }
        
        evidence_score = base_scores.get(pattern_name, 0.5)
        
        # === STEP 2: PATTERN-SPECIFIC ADJUSTMENTS ===
        if pattern_name == 'code_blocks':
            # Inline code is worse than code blocks
            if '`' in match.group() and not match.group().startswith('```'):
                evidence_score = min(0.95, evidence_score + 0.1)
            
        elif pattern_name == 'file_paths':
            # Simple file references might be OK, complex paths are not
            path_complexity = len(match.group().split('/')) + len(match.group().split('\\'))
            if path_complexity > 3:
                evidence_score += 0.2
            else:
                evidence_score -= 0.2
                
        elif pattern_name == 'procedure_steps':
            # Count the number of steps
            steps = len(re.findall(r'^\s*\d+\.', text, re.MULTILINE))
            if steps > 3:
                evidence_score += 0.2  # Many steps definitely don't belong
        
        # === STEP 3: CONTEXT CLUES ===
        admonition_type = self._detect_admonition_type(text, context)
        if admonition_type:
            # Warnings and cautions should never have code
            if admonition_type in ['warning', 'caution'] and pattern_name in ['code_blocks', 'command_blocks']:
                evidence_score += 0.2
            # Tips might legitimately reference technical elements
            elif admonition_type == 'tip' and pattern_name in ['file_paths', 'command_blocks']:
                evidence_score -= 0.2
        
        # === STEP 4: CONTENT LENGTH CONTEXT ===
        # Short content with technical elements is more suspicious
        if len(text.split()) < 20 and pattern_name in ['code_blocks', 'procedure_steps']:
            evidence_score += 0.1
        
        return max(0.0, min(1.0, evidence_score))
    
    def _calculate_content_inappropriateness(self, doc: 'Doc', text: str, admonition_type: str, context: Dict[str, Any]) -> float:
        """Calculate evidence that content doesn't match admonition type."""
        if not admonition_type or admonition_type not in self.admonition_types:
            return 0.0
        
        # === STEP 1: BASE ASSESSMENT ===
        evidence_score = 0.0
        
        # === STEP 2: CONTENT ANALYSIS ===
        text_lower = text.lower()
        
        # Check for inappropriate content based on admonition type
        inappropriate_content = self.admonition_types[admonition_type]['inappropriate']
        
        if 'warnings' in inappropriate_content and any(word in text_lower for word in ['danger', 'risk', 'warning', 'caution']):
            evidence_score += 0.3
        
        if 'code' in inappropriate_content and ('```' in text or text.count('`') > 2):
            evidence_score += 0.4
        
        if 'procedures' in inappropriate_content:
            step_count = len(re.findall(r'^\s*\d+\.', text, re.MULTILINE))
            if step_count > 2:
                evidence_score += 0.3
        
        # === STEP 3: LINGUISTIC ANALYSIS ===
        if doc:
            # Analyze tone and content using spaCy
            verbs = [token.lemma_.lower() for token in doc if token.pos_ == 'VERB']
            
            # Warning admonitions should have cautionary language
            if admonition_type == 'warning':
                cautionary_verbs = ['avoid', 'prevent', 'ensure', 'check', 'verify']
                if not any(verb in verbs for verb in cautionary_verbs):
                    evidence_score += 0.2
            
            # Note admonitions should be informational
            elif admonition_type == 'note':
                action_verbs = ['install', 'configure', 'run', 'execute', 'download']
                if any(verb in verbs for verb in action_verbs):
                    evidence_score += 0.2
        
        return max(0.0, min(1.0, evidence_score))
    
    def _calculate_complexity_evidence(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence that admonition content is too complex."""
        # === STEP 1: LENGTH ANALYSIS ===
        word_count = len(text.split())
        line_count = text.count('\n') + 1
        char_count = len(text)
        
        evidence_score = 0.0
        
        # Word count evidence
        if word_count > self.length_thresholds['word_count']:
            evidence_score += min(0.5, (word_count - self.length_thresholds['word_count']) / 100.0)
        
        # Line count evidence
        if line_count > self.length_thresholds['line_count']:
            evidence_score += min(0.3, (line_count - self.length_thresholds['line_count']) / 10.0)
        
        # === STEP 2: STRUCTURAL COMPLEXITY ===
        # Multiple paragraphs suggest complexity
        paragraph_count = text.count('\n\n') + 1
        if paragraph_count > 2:
            evidence_score += 0.2
        
        # Multiple sentences suggest complexity
        sentence_count = text.count('.') + text.count('!') + text.count('?')
        if sentence_count > 5:
            evidence_score += 0.1
        
        # === STEP 3: LINGUISTIC COMPLEXITY ===
        if doc:
            # Complex sentence structures
            complex_sentences = sum(1 for sent in doc.sents if len([token for token in sent if token.pos_ == 'VERB']) > 2)
            if complex_sentences > 2:
                evidence_score += 0.1
            
            # Technical vocabulary density
            technical_terms = sum(1 for token in doc if token.is_upper and len(token.text) > 2)
            if technical_terms > 3:
                evidence_score += 0.1
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===
    
    def _detect_admonition_type(self, text: str, context: Dict[str, Any]) -> Optional[str]:
        """Detect the type of admonition from context or content."""
        # Check context first
        admonition_type = context.get('admonition_type', '').lower()
        if admonition_type in self.admonition_types:
            return admonition_type
        
        # Check block type
        block_type = context.get('block_type', '').lower()
        for admon_type in self.admonition_types:
            if admon_type in block_type:
                return admon_type
        
        # Check content for admonition keywords
        text_lower = text.lower()
        for admon_type, config in self.admonition_types.items():
            for keyword in config['keywords']:
                if keyword in text_lower[:50]:  # Check first 50 characters
                    return admon_type
        
        return None
    
    def _is_legitimate_technical_reference(self, match: re.Match, text: str, context: Dict[str, Any]) -> bool:
        """Check if technical content might be a legitimate reference."""
        matched_text = match.group().lower()
        
        # Short file extensions or simple references might be OK
        if len(matched_text) < 10 and ('.' in matched_text and matched_text.count('.') == 1):
            return True
        
        # Simple inline code references might be OK
        if matched_text.startswith('`') and matched_text.endswith('`') and len(matched_text) < 15:
            return True
        
        return False
    
    def _get_sentence_for_match(self, match: re.Match, text: str) -> str:
        """Get a reasonable sentence containing the match."""
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        return text[start:end].strip()
    
    def _get_complexity_metrics(self, doc: 'Doc', text: str) -> Dict[str, Any]:
        """Get complexity metrics for the content."""
        metrics = {
            'word_count': len(text.split()),
            'line_count': text.count('\n') + 1,
            'paragraph_count': text.count('\n\n') + 1,
            'sentence_count': text.count('.') + text.count('!') + text.count('?')
        }
        
        if doc:
            metrics['verb_count'] = sum(1 for token in doc if token.pos_ == 'VERB')
            metrics['noun_count'] = sum(1 for token in doc if token.pos_ in ['NOUN', 'PROPN'])
        
        return metrics
    
    def _get_admonition_severity(self, pattern_name: str, evidence_score: float) -> str:
        """Determine severity based on pattern and evidence."""
        # Code in admonitions is medium to high severity
        if pattern_name in ['code_blocks', 'command_blocks']:
            return 'medium' if evidence_score < 0.8 else 'high'
        
        # Most other issues are low to medium severity
        if evidence_score > 0.8:
            return 'medium'
        elif evidence_score > 0.6:
            return 'low'
        else:
            return 'low'

    # === SMART MESSAGING ===

    def _get_contextual_admonition_message(self, pattern_name: str, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for admonition violations."""
        confidence_phrase = "clearly contains" if evidence_score > 0.8 else ("likely contains" if evidence_score > 0.6 else "may contain")
        
        messages = {
            'code_blocks': f"This admonition {confidence_phrase} code blocks that should be in examples or procedures.",
            'procedure_steps': f"This admonition {confidence_phrase} procedural steps that belong in a procedure module.",
            'complex_tables': f"This admonition {confidence_phrase} complex tables that should be in the main content.",
            'command_blocks': f"This admonition {confidence_phrase} command blocks that belong in examples.",
            'file_paths': f"This admonition {confidence_phrase} complex file references that might be better as examples.",
            'complex_formatting': f"This admonition {confidence_phrase} complex formatting that reduces readability.",
            'long_urls': f"This admonition {confidence_phrase} very long URLs that could be shortened or moved."
        }
        
        return messages.get(pattern_name, f"This admonition {confidence_phrase} content that may not be appropriate.")

    def _get_inappropriateness_message(self, admonition_type: str, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate message for content inappropriateness."""
        confidence_phrase = "clearly has" if evidence_score > 0.8 else ("likely has" if evidence_score > 0.6 else "may have")
        
        return f"This {admonition_type} admonition {confidence_phrase} content that doesn't match its intended purpose."

    def _get_complexity_message(self, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate message for content complexity."""
        confidence_phrase = "clearly is" if evidence_score > 0.8 else ("likely is" if evidence_score > 0.6 else "may be")
        
        return f"This admonition {confidence_phrase} too complex or lengthy for effective use."

    def _generate_smart_admonition_suggestions(self, pattern_name: str, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for admonition violations."""
        suggestion_map = {
            'code_blocks': [
                "Move code examples to a separate code block or procedure.",
                "Use admonitions for brief warnings or notes, not code.",
                "Consider creating an example section for code demonstrations."
            ],
            'procedure_steps': [
                "Move procedural steps to a dedicated procedure section.",
                "Use admonitions for brief warnings or tips about procedures.",
                "Create a step-by-step procedure block instead."
            ],
            'complex_tables': [
                "Move complex tables to the main content area.",
                "Simplify table content if it must remain in the admonition.",
                "Use admonitions for brief tabular summaries only."
            ],
            'command_blocks': [
                "Move command examples to a code block or example section.",
                "Reference commands briefly without showing full syntax.",
                "Create separate examples for command demonstrations."
            ],
            'file_paths': [
                "Simplify file references to essential information only.",
                "Move complex file structures to documentation sections.",
                "Use brief file references in admonitions."
            ],
            'complex_formatting': [
                "Simplify formatting within admonitions.",
                "Use plain text for better admonition readability.",
                "Move complex formatted content to main sections."
            ],
            'long_urls': [
                "Use shortened URLs or link text instead.",
                "Move detailed URL references to a references section.",
                "Keep admonition URLs brief and essential."
            ]
        }
        
        suggestions = suggestion_map.get(pattern_name, ["Simplify admonition content."])
        
        # Add context-specific advice
        admonition_type = self._detect_admonition_type(context.get('text', ''), context)
        if admonition_type:
            if admonition_type == 'warning':
                suggestions.append("Warnings should focus on risks and precautions, not procedures.")
            elif admonition_type == 'note':
                suggestions.append("Notes should provide brief clarifications, not complex examples.")
            elif admonition_type == 'tip':
                suggestions.append("Tips should offer brief helpful advice, not detailed instructions.")
        
        return suggestions[:3]

    def _generate_inappropriateness_suggestions(self, admonition_type: str, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate suggestions for inappropriate content."""
        type_guidance = {
            'note': "Use notes for brief explanations, clarifications, or additional information.",
            'warning': "Use warnings for risks, precautions, and consequences to avoid.",
            'important': "Use important admonitions for critical information that requires attention.",
            'tip': "Use tips for helpful advice, shortcuts, or best practices."
        }
        
        suggestions = [
            f"Review content to ensure it matches the purpose of a {admonition_type} admonition.",
            type_guidance.get(admonition_type, "Ensure content matches the admonition type."),
            "Consider using a different admonition type or moving content to main text."
        ]
        
        return suggestions

    def _generate_complexity_suggestions(self, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate suggestions for content complexity."""
        return [
            "Break complex content into smaller, focused admonitions.",
            "Move detailed explanations to main content sections.",
            "Keep admonitions brief and focused on key points."
        ]

    def _generate_length_suggestions(self, word_count: int, context: Dict[str, Any]) -> List[str]:
        """Generate suggestions for content length."""
        suggestions = [
            f"Consider shortening this {word_count}-word admonition.",
            "Admonitions work best when kept brief and focused.",
            "Move detailed content to main documentation sections."
        ]
        
        if word_count > 150:
            suggestions.append("This content might work better as a separate section.")
        
        return suggestions[:3]
