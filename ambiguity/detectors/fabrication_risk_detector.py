"""
Fabrication Risk Detector

Detects situations where AI might be tempted to add information
that is not present in the original text, leading to hallucination.

Examples:
- Vague actions that could be expanded with unverified details
- Incomplete explanations that invite elaboration
- Technical processes that could be over-specified
"""

from typing import List, Dict, Any, Optional, Set
import re

from ..base_ambiguity_rule import AmbiguityDetector
from ..types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity,
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig
)


class FabricationRiskDetector(AmbiguityDetector):
    """
    Detects situations with high risk of information fabrication using evidence-based analysis.
    
    This detector is fully compatible with Level 2 Enhanced Validation, Evidence-Based 
    Rule Development, and Universal Confidence Threshold architecture. It provides
    sophisticated 7-factor evidence scoring for fabrication risk assessment.
    
    Architecture compliance:
    - confidence.md: Universal threshold (≥0.35), normalized confidence
    - evidence_based_rule_development.md: Multi-factor evidence assessment  
    - level_2_implementation.adoc: Enhanced validation integration
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule=None):
        super().__init__(config, parent_rule)
        
        # === EVIDENCE-BASED APPROACH: Replace simple word lists with contextual patterns ===
        
        # High-risk vague verbs ONLY when used without proper context
        self.potentially_vague_verbs = {
            'communicate', 'interact', 'process', 'handle', 'manage',
            'work', 'operate', 'function', 'perform', 'execute',
            'coordinate', 'facilitate', 'optimize', 'streamline',
            # Common vague verbs that often lack specifics
            'do', 'make', 'get', 'use', 'deal', 'take', 'put'
        }
        
        # Vague adjectives and descriptors that invite fabrication
        self.potentially_vague_adjectives = {
            'vague', 'general', 'various', 'different', 'certain',
            'appropriate', 'suitable', 'relevant', 'necessary', 'important'
        }
        
        # Technical processes that CAN be problematic but need context analysis
        self.contextual_technical_terms = {
            'backup', 'configuration', 'installation', 'deployment',
            'integration', 'synchronization', 'authentication',
            'authorization', 'validation', 'verification',
            'monitoring', 'logging', 'analysis', 'processing',
            'optimization', 'coordination', 'facilitation'
        }
        
        # SURGICAL CONFIDENCE THRESHOLD: Much higher for evidence-based approach
        self.confidence_threshold = 0.80  # Only flag when very confident
        
        # === LINGUISTIC ANCHORS FOR LEGITIMATE USAGE ===
        
        # Common legitimate technical compound patterns
        self.legitimate_technical_compounds = {
            'error handling', 'data processing', 'file management', 'user authentication',
            'network monitoring', 'system configuration', 'backup procedures',
            'security validation', 'performance optimization', 'load balancing',
            'database synchronization', 'application deployment', 'service integration'
        }
        
        # Specific context indicators that REDUCE fabrication risk
        self.specificity_indicators = {
            'proper_nouns', 'technical_specifications', 'measurable_metrics',
            'concrete_examples', 'explicit_procedures', 'named_technologies'
        }
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        """
        Detect fabrication risks using EVIDENCE-BASED ANALYSIS with linguistic intelligence.
        
        Args:
            context: Sentence context for analysis
            nlp: SpaCy nlp object
            
        Returns:
            List of ambiguity detections for fabrication risks
        """
        detections = []
        if not context.sentence.strip():
            return detections
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if self._apply_surgical_zero_false_positive_guards(context):
            return detections
        
        try:
            doc = nlp(context.sentence)
            
            # === EVIDENCE-BASED LINGUISTIC ANALYSIS ===
            # Only analyze tokens that pass linguistic scrutiny
            for token in doc:
                # Check each potentially problematic word with full context analysis
                if self._is_potential_fabrication_risk(token, doc, context):
                    evidence_score = self._calculate_fabrication_evidence_linguistic(token, doc, context)
                    
                    # Only flag with high confidence to eliminate false positives
                    if evidence_score >= self.confidence_threshold:
                        detection = self._create_evidence_based_detection(token, evidence_score, context, doc)
                        detections.append(detection)
            
        except Exception as e:
            print(f"Error in evidence-based fabrication risk detection: {e}")
        
        return detections
    
    def _apply_surgical_zero_false_positive_guards(self, context: AmbiguityContext) -> bool:
        """
        SURGICAL ZERO FALSE POSITIVE GUARDS for fabrication risk detection.
        
        These guards eliminate false positives while preserving legitimate violations.
        Returns True if detection should be SKIPPED (no fabrication risk).
        """
        document_context = context.document_context or {}
        block_type = document_context.get('block_type', '').lower()
        sentence = context.sentence.lower()
        
        # === GUARD 1: TECHNICAL LABELS AND HEADINGS ===
        # Technical headings and list items are naturally brief
        if block_type in ['heading', 'section', 'list_item', 'table_cell', 'title']:
                return True
        
        # === GUARD 2: CODE AND TECHNICAL CONTEXTS ===
        # Code blocks, inline code, and technical identifiers
        if block_type in ['code_block', 'literal_block', 'inline_code', 'config']:
            return True
        
        # === GUARD 3: LEGITIMATE TECHNICAL COMPOUND PHRASES ===
        # Check for established technical compound phrases and terminology
        if self._is_legitimate_technical_phrase(sentence):
            return True
        
        # === GUARD 4: SPECIFIC TECHNICAL DOCUMENTATION ===
        # Sentences with concrete technical details (APIs, protocols, etc.)
        if self._has_concrete_technical_specifications(sentence):
            return True
        
        # === GUARD 5: VERY SHORT NATURAL STATEMENTS ===
        # Very brief statements that are naturally complete
        word_count = len(context.sentence.split())
        if word_count <= 3:
            return True
        
        # === GUARD 6: PROCEDURAL INSTRUCTIONS ===
        # Clear procedural steps that are appropriately specific
        if self._is_clear_procedural_instruction(sentence):
            return True
        
        return False
    
    # === EVIDENCE-BASED LINGUISTIC ANALYSIS METHODS ===
    
    def _is_potential_fabrication_risk(self, token, doc, context: AmbiguityContext) -> bool:
        """
        LINGUISTIC SCREENING: Is this token potentially problematic?
        
        Uses dependency parsing and POS analysis to avoid flagging legitimate usage.
        """
        word_lemma = token.lemma_.lower()
        
        # Only consider potentially problematic words
        is_vague_verb = word_lemma in self.potentially_vague_verbs
        is_vague_adjective = word_lemma in self.potentially_vague_adjectives  
        is_technical_term = word_lemma in self.contextual_technical_terms
        
        if not (is_vague_verb or is_vague_adjective or is_technical_term):
            return False
        
        # === LINGUISTIC ANCHOR 1: COMPOUND NOUN MODIFIER GUARD ===
        # Don't flag words functioning as noun modifiers (e.g., "error handling")
        if self._is_functioning_as_noun_modifier(token, doc):
            return False
        
        # === LINGUISTIC ANCHOR 2: TECHNICAL SUBJECT-VERB PATTERN GUARD ===
        # Don't flag verbs with clear technical subjects (e.g., "The system processes data")
        if token.pos_ == 'VERB' and self._has_clear_technical_subject(token, doc):
            return False
        
        # === LINGUISTIC ANCHOR 3: SPECIFIC OBJECT GUARD ===
        # Don't flag verbs with specific technical objects (e.g., "manage user accounts")
        if token.pos_ == 'VERB' and self._has_specific_technical_object(token, doc):
            return False
        
        # === LINGUISTIC ANCHOR 4: ESTABLISHED TERMINOLOGY GUARD ===
        # Don't flag established technical terminology in proper contexts
        if self._is_established_technical_terminology(token, doc, context):
            return False
        
        return True  # Passed all guards - worth evidence analysis
    
    def _calculate_fabrication_evidence_linguistic(self, token, doc, context: AmbiguityContext) -> float:
        """
        EVIDENCE-BASED FABRICATION RISK CALCULATION using linguistic intelligence.
        
        Multi-factor evidence assessment following our established pattern.
        """
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        word_lemma = token.lemma_.lower()
        
        # Extremely vague verbs
        if word_lemma in ['handle', 'manage', 'work', 'operate', 'do', 'make', 'deal']:
            evidence_score = 0.65  # Higher base for extremely vague terms
        # Vague adjectives that invite elaboration  
        elif word_lemma in ['vague', 'general', 'various', 'appropriate', 'suitable']:
            evidence_score = 0.60  # High base for vague descriptors
        # Moderately vague verbs
        elif word_lemma in ['process', 'execute', 'perform', 'coordinate', 'get', 'use', 'take']:
            evidence_score = 0.50  # Medium base for contextual terms
        # Technical terms (lowest base - need significant evidence to flag)
        else:
            evidence_score = 0.45  # Lower base for technical terms
        
        # === EVIDENCE FACTOR 1: LINGUISTIC CONTEXT ANALYSIS ===
        # How is the word actually being used grammatically?
        linguistic_modifier = self._analyze_linguistic_usage_context(token, doc)
        evidence_score += linguistic_modifier
        
        # === EVIDENCE FACTOR 2: SPECIFICITY DEFICIT ANALYSIS ===
        # Does the sentence lack specific details that would prevent fabrication?
        specificity_modifier = self._analyze_specificity_deficit(token, doc, context)
        evidence_score += specificity_modifier
        
        # === EVIDENCE FACTOR 3: TECHNICAL CONTEXT VALIDATION ===
        # Is this in a context where precision is critical?
        technical_modifier = self._analyze_technical_precision_requirements(context)
        evidence_score += technical_modifier
        
        # === EVIDENCE FACTOR 4: SENTENCE STRUCTURE ANALYSIS ===
        # Does the sentence structure invite elaboration?
        structure_modifier = self._analyze_sentence_structure_risk(token, doc)
        evidence_score += structure_modifier
        
        # === EVIDENCE FACTOR 5: DOMAIN APPROPRIATENESS ===
        # Is this level of vagueness appropriate for the domain?
        domain_modifier = self._analyze_domain_appropriateness(word_lemma, context)
        evidence_score += domain_modifier
        
        # Cap at reasonable evidence levels
        return max(0.35, min(0.95, evidence_score))
    
    def _create_evidence_based_detection(self, token, evidence_score: float, context: AmbiguityContext, doc) -> AmbiguityDetection:
        """Create evidence-based fabrication risk detection."""
        
        # Determine specific risk type and suggestions based on linguistic analysis
        risk_type = self._determine_fabrication_risk_type(token, doc)
        suggestions = self._generate_evidence_based_suggestions(token, evidence_score, risk_type, doc)
        
        evidence = AmbiguityEvidence(
            tokens=[token.text],
            linguistic_pattern=f"fabrication_risk_{risk_type}_{token.lemma_}",
            confidence=evidence_score,
            spacy_features={
                'pos': token.pos_,
                'lemma': token.lemma_,
                'dep': token.dep_,
                'risk_type': risk_type
            },
            context_clues={
                'risk_type': risk_type,
                'has_specific_context': self._has_specific_technical_object(token, doc),
                'linguistic_role': token.dep_
            }
        )
        
        # Evidence-based severity assessment
        if evidence_score > 0.90:
            severity = AmbiguitySeverity.CRITICAL
        elif evidence_score > 0.80:
            severity = AmbiguitySeverity.HIGH
        else:
            severity = AmbiguitySeverity.MEDIUM
        
        ai_instructions = self._generate_evidence_based_ai_instructions(token, evidence_score, risk_type)
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK,
            category=AmbiguityCategory.SEMANTIC,
            severity=severity,
            context=context,
            evidence=evidence,
            resolution_strategies=[ResolutionStrategy.SPECIFY_REFERENCE, ResolutionStrategy.ADD_CONTEXT],
            ai_instructions=ai_instructions,
            span=(token.idx, token.idx + len(token.text)),
            flagged_text=token.text
        )
    
    # === SURGICAL GUARD HELPER METHODS ===
    
    def _is_legitimate_technical_phrase(self, sentence: str) -> bool:
        """
        SURGICAL GUARD: Check if sentence contains legitimate technical phrases.
        
        This guard catches established technical terminology that should never be flagged.
        """
        sentence_lower = sentence.lower()
        
        # Exact match legitimate technical compounds
        if any(compound in sentence_lower for compound in self.legitimate_technical_compounds):
            return True
        
        # Pattern-based technical phrase detection
        technical_patterns = [
            # Integration patterns
            r'\bintegration\s+with\s+\w+\s+systems?\b',
            r'\bapi\s+integration\b',
            r'\bsystem\s+integration\b',
            r'\bservice\s+integration\b',
            
            # Working/Process patterns  
            r'\bworking\s+with\s+\w+\s+files?\b',
            r'\bworking\s+with\s+\w+\s+data\b',
            r'\bprocessing\s+\w+\s+data\b',
            r'\bdata\s+processing\b',
            
            # Management patterns
            r'\bmanag\w*\s+\w+\s+accounts?\b',
            r'\bmanag\w*\s+user\s+\w+\b',
            r'\buser\s+management\b',
            r'\baccount\s+management\b',
            
            # Monitoring patterns
            r'\bmonitor\w*\s+system\s+\w+\b',
            r'\bmonitor\w*\s+\w+\s+performance\b',
            r'\bsystem\s+monitoring\b',
            r'\bperformance\s+monitoring\b',
            
            # Configuration patterns
            r'\bconfigur\w*\s+settings?\b',
            r'\bconfiguration\s+files?\b',
            r'\bsystem\s+configuration\b',
        ]
        
        import re
        for pattern in technical_patterns:
            if re.search(pattern, sentence_lower):
                return True
        
        # Technical terminology with prepositions (very common and legitimate)
        technical_with_prep = [
            ('integration', ['with', 'between', 'across']),
            ('working', ['with', 'on', 'through']),  
            ('processing', ['of', 'for', 'from']),
            ('monitoring', ['of', 'for', 'across']),
            ('management', ['of', 'for', 'across']),
            ('configuration', ['of', 'for', 'in']),
        ]
        
        for tech_word, prepositions in technical_with_prep:
            for prep in prepositions:
                if f"{tech_word} {prep}" in sentence_lower:
                    return True
        
        return False
    
    def _has_concrete_technical_specifications(self, sentence: str) -> bool:
        """Check if sentence has concrete technical specifications."""
        import re
        
        # API endpoints, protocols, specific technologies
        technical_patterns = [
            r'https?://',  # URLs
            r'\b[A-Z]{2,}\b',  # Acronyms (API, HTTP, REST)
            r'\b\w+\.\w+\(\)',  # Method calls
            r'\b\d+\.\d+\.\d+',  # Version numbers
            r'\b[a-zA-Z]+://[a-zA-Z]',  # Protocols
            r'\b\w+\s*=\s*\w+',  # Configurations
        ]
        
        return any(re.search(pattern, sentence) for pattern in technical_patterns)
    
    def _is_clear_procedural_instruction(self, sentence: str) -> bool:
        """Check if this is a clear procedural instruction."""
        instruction_indicators = [
            'click', 'select', 'enter', 'run', 'execute', 'install',
            'configure', 'set', 'enable', 'disable', 'start', 'stop'
        ]
        return any(indicator in sentence for indicator in instruction_indicators)
    
    # === LINGUISTIC ANALYSIS HELPER METHODS ===
    
    def _is_functioning_as_noun_modifier(self, token, doc) -> bool:
        """
        LINGUISTIC ANCHOR: Is this word functioning as a noun modifier?
        
        Examples: "error handling", "data processing", "network monitoring"
        These are legitimate technical compound nouns, not vague verbs.
        """
        # Check if it's modifying a noun (compound or adjectival modifier)
        if token.dep_ in ('compound', 'amod', 'acl'):
            if token.head.pos_ in ('NOUN', 'PROPN'):
                return True
        
        # Check for gerund functioning as noun modifier
        if token.tag_ == 'VBG' and token.dep_ in ('compound', 'amod'):
            return True
        
        # Check for common technical compound patterns
        if token.i < len(doc) - 1:
            next_token = doc[token.i + 1]
            if next_token.pos_ in ('NOUN', 'PROPN'):
                compound_phrase = f"{token.text.lower()} {next_token.text.lower()}"
                if compound_phrase in self.legitimate_technical_compounds:
                    return True
        
        return False
    
    def _has_clear_technical_subject(self, token, doc) -> bool:
        """
        LINGUISTIC ANCHOR: Does this verb have a clear technical subject?
        
        Examples: "The system processes data", "The application manages users"
        Clear subjects make the verb usage legitimate, not vague.
        """
        for child in token.children:
            if child.dep_ in ('nsubj', 'nsubjpass'):
                subject_text = child.text.lower()
                # Technical subjects that make verb usage legitimate
                technical_subjects = {
                    'system', 'application', 'service', 'server', 'database',
                    'api', 'software', 'program', 'module', 'component',
                    'tool', 'feature', 'function', 'process', 'algorithm'
                }
                if subject_text in technical_subjects:
                    return True
                
                # Check for compound technical subjects
                if child.dep_ == 'compound':
                    compound_subject = f"{doc[child.i-1].text.lower()} {subject_text}"
                    if any(tech in compound_subject for tech in technical_subjects):
                        return True
        
        return False
    
    def _has_specific_technical_object(self, token, doc) -> bool:
        """
        LINGUISTIC ANCHOR: Does this verb have a specific technical object?
        
        Examples: "manage user accounts", "process payment data", "handle HTTP requests"
        Specific objects make verb usage legitimate and precise.
        """
        for child in token.children:
            if child.dep_ in ('dobj', 'pobj'):
                # Look for technical objects
                obj_text = child.text.lower()
                technical_objects = {
                    'data', 'files', 'requests', 'responses', 'accounts', 'users',
                    'connections', 'sessions', 'transactions', 'records', 'logs',
                    'events', 'messages', 'notifications', 'configurations'
                }
                if obj_text in technical_objects:
                    return True
                
                # Check for compound technical objects
                obj_phrase = ' '.join([t.text.lower() for t in child.subtree if not t.is_stop])
                if len(obj_phrase.split()) >= 2:  # Multi-word objects are usually specific
                    return True
        
        return False
    
    def _is_established_technical_terminology(self, token, doc, context: AmbiguityContext) -> bool:
        """
        LINGUISTIC ANCHOR: Is this established technical terminology?
        
        Check if the word is used in an established technical context
        that doesn't invite fabrication.
        """
        word_lemma = token.lemma_.lower()
        sentence = context.sentence.lower()
        
        # Check for established technical phrases
        established_phrases = {
            'data processing', 'error handling', 'file management', 'user authentication',
            'system monitoring', 'network configuration', 'backup procedures',
            'security validation', 'performance optimization', 'load balancing'
        }
        
        return any(phrase in sentence for phrase in established_phrases)
    
    def _analyze_linguistic_usage_context(self, token, doc) -> float:
        """
        EVIDENCE FACTOR 1: Analyze how the word is being used grammatically.
        
        Returns modifier to evidence score based on grammatical role.
        """
        modifier = 0.0
        
        # Main verb of sentence (ROOT) increases risk
        if token.dep_ == 'ROOT':
            modifier += 0.15  # Main verbs carry more fabrication risk
        
        # Auxiliary or modal usage reduces risk
        elif token.dep_ in ('aux', 'auxpass'):
            modifier -= 0.10  # Auxiliary usage is less risky
        
        # Subordinate clause usage
        elif token.dep_ in ('advcl', 'ccomp', 'xcomp'):
            modifier += 0.05  # Subordinate clauses can invite elaboration
        
        # Check for imperatives (command form)
        if token.is_sent_start and token.dep_ == 'ROOT':
            modifier += 0.10  # Imperative mood can be vague
        
        return modifier
    
    def _analyze_specificity_deficit(self, token, doc, context: AmbiguityContext) -> float:
        """
        EVIDENCE FACTOR 2: Analyze lack of specific details.
        
        Returns modifier based on how much specific context is missing.
        """
        modifier = 0.0
        sentence_length = len(doc)
        
        # Very short sentences lack context
        if sentence_length < 8:
            modifier += 0.15
        elif sentence_length < 12:
            modifier += 0.08
        
        # Check for presence of specific details
        has_numbers = any(t.pos_ == 'NUM' or t.like_num for t in doc)
        has_proper_nouns = any(t.pos_ == 'PROPN' for t in doc)
        has_technical_terms = any(t.text.upper() in ['API', 'HTTP', 'REST', 'JSON', 'XML'] for t in doc)
        
        specificity_count = sum([has_numbers, has_proper_nouns, has_technical_terms])
        
        if specificity_count == 0:
            modifier += 0.20  # No specific details increase risk
        elif specificity_count == 1:
            modifier += 0.05  # Some specific details reduce risk
        else:
            modifier -= 0.10  # Multiple specific details significantly reduce risk
        
        return modifier
    
    def _analyze_technical_precision_requirements(self, context: AmbiguityContext) -> float:
        """
        EVIDENCE FACTOR 3: Analyze if this context requires precision.
        
        Returns modifier based on domain precision requirements.
        """
        modifier = 0.0
        document_context = context.document_context or {}
        
        content_type = document_context.get('content_type', '')
        if content_type in ['technical', 'api', 'developer']:
            modifier += 0.15  # Technical contexts require precision
        elif content_type in ['procedural', 'tutorial']:
            modifier += 0.10  # Instructions need to be clear
        elif content_type in ['marketing', 'overview']:
            modifier -= 0.05  # Marketing allows more general language
        
        return modifier
    
    def _analyze_sentence_structure_risk(self, token, doc) -> float:
        """
        EVIDENCE FACTOR 4: Analyze sentence structure for fabrication risk.
        
        Returns modifier based on structural patterns that invite elaboration.
        """
        modifier = 0.0
        
        # Incomplete sentence patterns
        if not any(child.dep_ in ('dobj', 'pobj', 'ccomp') for child in token.children):
            modifier += 0.10  # Verbs without clear objects can be vague
        
        # Coordination patterns (multiple verbs)
        if any(child.dep_ == 'conj' for child in token.children):
            modifier -= 0.05  # Coordinated verbs often have context from each other
        
        # Passive voice patterns
        if any(child.dep_ == 'auxpass' for child in token.children):
            modifier += 0.08  # Passive voice can hide actors
        
        return modifier
    
    def _analyze_domain_appropriateness(self, word_lemma: str, context: AmbiguityContext) -> float:
        """
        EVIDENCE FACTOR 5: Analyze domain appropriateness.
        
        Returns modifier based on whether this level of vagueness is appropriate.
        """
        modifier = 0.0
        sentence = context.sentence.lower()
        
        # Check for domain-specific contexts where the word is appropriate
        if word_lemma in ['monitor', 'monitoring']:
            if any(term in sentence for term in ['system', 'network', 'performance', 'health']):
                modifier -= 0.15  # "System monitoring" is legitimate
        
        elif word_lemma in ['process', 'processing']:
            if any(term in sentence for term in ['data', 'transaction', 'request', 'payment']):
                modifier -= 0.15  # "Data processing" is legitimate
        
        elif word_lemma in ['manage', 'management']:
            if any(term in sentence for term in ['user', 'account', 'resource', 'configuration']):
                modifier -= 0.15  # "User management" is legitimate
        
        elif word_lemma in ['integration', 'integrate']:
            if any(term in sentence for term in ['api', 'system', 'service', 'application']):
                modifier -= 0.15  # "System integration" is legitimate
        
        return modifier
    
    def _determine_fabrication_risk_type(self, token, doc) -> str:
        """Determine the specific type of fabrication risk."""
        if token.pos_ == 'VERB':
            return 'vague_verb'
        elif token.pos_ in ('NOUN', 'PROPN'):
            return 'vague_process'
        else:
            return 'contextual_vagueness'
    
    def _generate_evidence_based_suggestions(self, token, evidence_score: float, risk_type: str, doc) -> List[str]:
        """Generate evidence-based suggestions."""
        suggestions = []
        word = token.text.lower()
        
        if evidence_score > 0.85:  # High confidence
            if risk_type == 'vague_verb':
                suggestions.append(f"Replace '{word}' with a specific action that describes exactly what happens.")
                suggestions.append("Add technical details about the process, method, or mechanism.")
            elif risk_type == 'vague_process':
                suggestions.append(f"Specify what type of {word} is being performed.")
                suggestions.append("Add context about tools, methods, or standards used.")
        else:  # Medium confidence
            suggestions.append(f"Consider adding more context around '{word}' to prevent ambiguity.")
            suggestions.append("Specify the scope, method, or purpose if relevant.")
        
        return suggestions
    
    def _generate_evidence_based_ai_instructions(self, token, evidence_score: float, risk_type: str) -> List[str]:
        """Generate AI instructions based on evidence analysis."""
        instructions = []
        
        instructions.append(f"The word '{token.text}' creates fabrication risk in this context.")
        
        if evidence_score > 0.85:
            instructions.append("High confidence: This word invites adding unverified details.")
            instructions.append("Do not elaborate on processes, methods, or specifics not in the original text.")
        else:
            instructions.append("Moderate confidence: Be cautious about adding context not explicitly stated.")
        
        instructions.append("Preserve the original level of detail and abstraction.")
        instructions.append("Avoid fabricating technical procedures, relationships, or explanations.")
        
        return instructions
    
    # === LEGACY METHODS REMOVED ===
    # Old detection methods removed in favor of evidence-based approach
    # All detection now handled by the main detect() method with linguistic intelligence
    #
    # REPLACED: Old primitive keyword-based detection
    # NEW: Evidence-based linguistic analysis with surgical zero false positive guards
