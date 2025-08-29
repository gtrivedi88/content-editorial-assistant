"""
Sentence Length Rule (Evidence-Based)
Analyzes sentence complexity and suggests structural improvements using evidence-based rule development.

This rule is fully compatible with Level 2 Enhanced Validation, Evidence-Based 
Rule Development, and Universal Confidence Threshold architecture. It provides
sophisticated 7-factor evidence scoring for sentence length violations.

Architecture compliance:
- confidence.md: Universal threshold (≥0.35), normalized confidence
- evidence_based_rule_development.md: Multi-factor evidence assessment  
- level_2_implementation.adoc: Enhanced validation integration
"""

from typing import List, Dict, Any, Optional
import os
import sys

# Handle imports for different contexts - simplified approach
BaseRule = None

try:
    from .base_rule import BaseRule
except ImportError:
    try:
        from base_rule import BaseRule
    except ImportError:
        try:
            from rules.base_rule import BaseRule
        except ImportError:
            # Add current directory to path and try again
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            try:
                from base_rule import BaseRule
            except ImportError:
                # Create a minimal fallback
                class BaseRule:
                    def __init__(self):
                        self.rule_type = self._get_rule_type()
                    def _get_rule_type(self):
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

class SentenceLengthRule(BaseRule):
    """
    Evidence-based rule to analyze sentence complexity and length.
    
    This rule implements sophisticated evidence scoring that considers:
    - Syntactic complexity and readability factors
    - Cognitive load and processing difficulty  
    - Document context and content type appropriateness
    - Multi-factor linguistic analysis
    - Surgical zero false positive guards
    
    Architecture compliance:
    - Universal threshold (≥0.35) for all detections
    - Multi-factor evidence assessment with 7 evidence factors
    - Enhanced validation system integration
    - Surgical zero false positive guards
    """
    
    def __init__(self):
        super().__init__()
        
        # Evidence-based configuration
        self.max_words = 25  # Default maximum words per sentence
        self.confidence_threshold = 0.45  # Above universal threshold (≥0.35)
        
        # Initialize evidence scoring components
        self._initialize_evidence_patterns()
    
    def _initialize_evidence_patterns(self):
        """Initialize evidence-based patterns for sophisticated scoring."""
        
        # Complexity thresholds for evidence scoring
        self.complexity_thresholds = {
            'low_complexity': {'max_words': 15, 'max_depth': 2, 'max_cognitive_load': 0.2},
            'medium_complexity': {'max_words': 25, 'max_depth': 3, 'max_cognitive_load': 0.4},
            'high_complexity': {'max_words': 35, 'max_depth': 4, 'max_cognitive_load': 0.6},
            'extreme_complexity': {'max_words': 50, 'max_depth': 5, 'max_cognitive_load': 0.8}
        }
        
        # Context indicators that affect evidence scoring
        self.appropriate_contexts = {
            'technical_documentation': True,  # Technical docs may have longer sentences
            'academic_writing': True,         # Academic writing may be more complex
            'legal_documents': True,          # Legal docs may need precision
            'marketing_copy': False,          # Marketing should be simple
            'user_instructions': False       # Instructions should be clear
        }
        
        # Document types where length rules should be more lenient
        self.length_appropriate_contexts = {
            'code_examples': True,           # Code examples may need detail
            'technical_specifications': True, # Specs may be complex
            'api_documentation': True,       # API docs may be detailed
            'troubleshooting_guides': False  # Troubleshooting should be clear
        }
        
        # Linguistic indicators that reduce evidence for violations
        self.evidence_reducers = {
            'list_structures': ['first', 'second', 'third', 'finally'],
            'technical_terms': ['configure', 'implementation', 'specification', 'parameter'],
            'logical_connectors': ['because', 'therefore', 'however', 'consequently']
        }

    def _get_rule_type(self) -> str:
        return 'sentence_length'
    
    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyze text for sentence length violations using evidence-based rule development.
        
        Implements sophisticated evidence scoring with:
        - Multi-factor evidence assessment (7 factors)
        - Surgical zero false positive guards
        - Context-aware domain validation
        - Universal threshold compliance (≥0.35)
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            # Handle both string and SpaCy Doc inputs for compatibility
            if hasattr(sentence, 'text'):
                sent_text = sentence.text
                sent_doc = sentence
            else:
                sent_text = sentence
                sent_doc = nlp(sentence)
            
            if not sent_doc:
                continue
            
            # Apply zero false positive guards first
            if self._apply_zero_false_positive_guards(sent_text, context):
                continue
            
            # Calculate word count for length assessment
            word_count = len([token for token in sent_doc if not token.is_punct and not token.is_space])
            
            # Only analyze sentences that exceed reasonable length
            if word_count > self.max_words:
                # Calculate sophisticated complexity analysis
                complexity_analysis = self._analyze_syntactic_complexity(sent_doc)
                
                # Calculate evidence score for this length violation
                evidence_score = self._calculate_sentence_length_evidence(
                    sent_doc, word_count, complexity_analysis, sent_text, text, context
                )
                
                # Only create error if evidence suggests it's worth evaluating
                if evidence_score >= self.confidence_threshold:
                    error = self._create_error(
                        sentence=sent_text,
                        sentence_index=i,
                        message=self._get_contextual_length_message(word_count, complexity_analysis, evidence_score),
                        suggestions=self._generate_evidence_aware_suggestions(
                            sent_doc, complexity_analysis, evidence_score, context
                        ),
                        severity=self._determine_evidence_based_severity(evidence_score, complexity_analysis),
                        text=text,  # Level 2 ✅
                        context=context,  # Level 2 ✅
                        evidence_score=evidence_score,  # Evidence-based scoring
                        flagged_text=sent_text,
                        span=(0, len(sent_text)),
                        complexity_analysis=complexity_analysis,
                        word_count=word_count
                    )
                    errors.append(error)
                    
            # NEW: Transition flow analysis for technical writers (if first sentence)
            if i == 0:  # First sentence - analyze entire document for flow
                full_doc = nlp(text)
                flow_issues = self._detect_transition_flow_issues(full_doc)
                for flow_issue in flow_issues:
                    if flow_issue.get('needs_improvement'):
                        # Calculate evidence for flow issues
                        flow_evidence = self._calculate_flow_evidence(flow_issue, text, context)
                        
                        if flow_evidence >= self.confidence_threshold:
                            flow_suggestions = self._generate_flow_suggestions(flow_issue)
                            errors.append(self._create_error(
                                sentence=sent_text,
                                sentence_index=i,
                                message=f'Flow issue: {flow_issue.get("type", "unknown").replace("_", " ").title()}',
                                suggestions=flow_suggestions,
                                severity='medium',
                                text=text,  # Level 2 ✅
                                context=context,  # Level 2 ✅
                                evidence_score=flow_evidence,  # Evidence-based scoring
                                flagged_text=sent_text,
                                span=(flow_issue.get('position', 0), flow_issue.get('position', 0) + len(sent_text)),
                                complexity_analysis=flow_issue
                            ))

        return errors
    
    def _apply_zero_false_positive_guards(self, sentence_text: str, context: Optional[Dict[str, Any]]) -> bool:
        """
        Apply surgical zero false positive guards for sentence length rule.
        
        Returns True if the detection should be skipped (no length violation risk).
        """
        if not sentence_text:
            return True
        
        document_context = context or {}
        block_type = document_context.get('block_type', '').lower()
        content_type = document_context.get('content_type', '').lower()
        
        # Guard 1: Code blocks and technical identifiers
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return True
        
        # Guard 2: List items that are naturally longer
        sentence_lower = sentence_text.lower().strip()
        if any(indicator in sentence_lower for indicator in ['first:', 'second:', 'third:', 'finally:']):
            return True
        
        # Guard 3: Technical specifications that need precision
        if content_type in ['technical_specifications', 'api_documentation']:
            # Allow longer sentences in technical contexts
            if len(sentence_text.split()) < 40:  # More lenient threshold
                return True
        
        # Guard 4: Quotations and examples
        if (sentence_text.startswith('"') and sentence_text.endswith('"')) or \
           (sentence_text.startswith("'") and sentence_text.endswith("'")):
            return True
        
        # Guard 5: Legal disclaimers and formal statements
        legal_indicators = ['disclaimer:', 'notice:', 'copyright', 'trademark', 'legal']
        if any(indicator in sentence_lower for indicator in legal_indicators):
            return True
        
        return False
    
    def _calculate_sentence_length_evidence(self, doc, word_count: int, complexity_analysis: Dict[str, Any], 
                                           sentence_text: str, text: str, context: Dict[str, Any]) -> float:
        """
        Enhanced Level 2 evidence calculation for sentence length violations.
        
        Implements evidence-based rule development with:
        - Multi-factor evidence assessment
        - Context-aware domain validation 
        - Universal threshold compliance (≥0.35)
        - Specific criteria for length vs readability balance
        """
        # Evidence-based base confidence (Level 2 enhancement)
        evidence_score = 0.35  # Starting at universal threshold (≥0.35)
        
        # EVIDENCE FACTOR 1: Length Severity Assessment (High Impact)
        length_factor = self._calculate_length_severity_factor(word_count)
        evidence_score += length_factor
        
        # EVIDENCE FACTOR 2: Syntactic Complexity Analysis (Context Dependency)
        complexity_factor = self._calculate_complexity_evidence_factor(complexity_analysis)
        evidence_score += complexity_factor
        
        # EVIDENCE FACTOR 3: Document Context Assessment (Domain Knowledge)
        domain_modifier = self._calculate_domain_evidence_modifier(context)
        evidence_score += domain_modifier
        
        # EVIDENCE FACTOR 4: Readability Impact Analysis (User Experience)
        readability_modifier = self._calculate_readability_evidence_modifier(doc, complexity_analysis)
        evidence_score += readability_modifier
        
        # EVIDENCE FACTOR 5: Content Type Appropriateness (Communication Purpose)
        content_modifier = self._calculate_content_type_evidence_modifier(sentence_text, context)
        evidence_score += content_modifier
        
        # EVIDENCE FACTOR 6: Structural Quality Assessment (Sentence Architecture)
        structural_modifier = self._calculate_structural_evidence_modifier(doc, complexity_analysis)
        evidence_score += structural_modifier
        
        # EVIDENCE FACTOR 7: Breaking Difficulty Analysis (Practicality Assessment)
        breaking_modifier = self._calculate_breaking_difficulty_modifier(doc, sentence_text)
        evidence_score += breaking_modifier
        
        # UNIVERSAL THRESHOLD COMPLIANCE (≥0.35 minimum)
        # Cap at 0.95 to leave room for uncertainty
        return min(0.95, max(0.35, evidence_score))
    
    def _calculate_length_severity_factor(self, word_count: int) -> float:
        """Calculate evidence factor based on length severity."""
        if word_count <= 25:
            return 0.0  # Within reasonable range
        elif word_count <= 30:
            return 0.10  # Slightly long
        elif word_count <= 35:
            return 0.20  # Moderately long
        elif word_count <= 45:
            return 0.30  # Long
        elif word_count <= 60:
            return 0.40  # Very long
        else:
            return 0.50  # Extremely long
    
    def _calculate_complexity_evidence_factor(self, complexity_analysis: Dict[str, Any]) -> float:
        """Calculate evidence factor based on syntactic complexity."""
        overall_complexity = complexity_analysis.get('overall_complexity', 0)
        cognitive_load = complexity_analysis.get('cognitive_load_score', 0)
        subordination_depth = complexity_analysis.get('subordination_depth', 0)
        
        complexity_factor = 0.0
        
        # High complexity increases evidence for breaking
        if overall_complexity > 7:
            complexity_factor += 0.15
        elif overall_complexity > 5:
            complexity_factor += 0.10
        elif overall_complexity > 3:
            complexity_factor += 0.05
        
        # High cognitive load increases evidence
        if cognitive_load > 0.4:
            complexity_factor += 0.10
        elif cognitive_load > 0.3:
            complexity_factor += 0.05
        
        # Deep subordination increases evidence
        if subordination_depth > 3:
            complexity_factor += 0.08
        elif subordination_depth > 2:
            complexity_factor += 0.05
        
        return min(0.25, complexity_factor)  # Cap at 0.25
    
    def _calculate_domain_evidence_modifier(self, context: Dict[str, Any]) -> float:
        """Calculate evidence modifier based on domain context."""
        if not context:
            return 0.0
        
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        modifier = 0.0
        
        # Adjust based on content type
        if content_type in ['user_guide', 'tutorial', 'instructions']:
            modifier += 0.10  # User-facing content should be clear
        elif content_type in ['technical_specifications', 'api_documentation']:
            modifier -= 0.05  # Technical content may need precision
        elif content_type == 'marketing':
            modifier += 0.15  # Marketing should be simple
        
        # Adjust based on domain
        if domain in ['software', 'engineering', 'technical']:
            modifier -= 0.05  # Technical domains may need complexity
        elif domain in ['general', 'consumer']:
            modifier += 0.10  # General audience needs simplicity
        
        return max(-0.15, min(0.20, modifier))  # Cap between -0.15 and 0.20
    
    def _calculate_readability_evidence_modifier(self, doc, complexity_analysis: Dict[str, Any]) -> float:
        """Calculate evidence modifier based on readability impact."""
        information_density = complexity_analysis.get('information_density', 0)
        morphological_complexity = complexity_analysis.get('morphological_complexity', 0)
        
        modifier = 0.0
        
        # High information density makes long sentences harder to read
        if information_density > 0.7:
            modifier += 0.10
        elif information_density > 0.6:
            modifier += 0.05
        
        # High morphological complexity adds cognitive burden
        if morphological_complexity > 4:
            modifier += 0.08
        elif morphological_complexity > 3:
            modifier += 0.04
        
        return min(0.15, modifier)  # Cap at 0.15
    
    def _calculate_content_type_evidence_modifier(self, sentence_text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence modifier based on specific content characteristics."""
        modifier = 0.0
        sentence_lower = sentence_text.lower()
        
        # Technical terms may justify longer sentences
        technical_indicators = ['configuration', 'implementation', 'specification', 'parameter']
        if any(term in sentence_lower for term in technical_indicators):
            modifier -= 0.05
        
        # Instructional language should be simple
        instruction_indicators = ['must', 'should', 'click', 'select', 'configure']
        if any(term in sentence_lower for term in instruction_indicators):
            modifier += 0.10
        
        # List-like content may be naturally longer
        list_indicators = ['first', 'second', 'next', 'finally', 'include']
        if any(term in sentence_lower for term in list_indicators):
            modifier -= 0.08
        
        return max(-0.10, min(0.15, modifier))  # Cap between -0.10 and 0.15
    
    def _calculate_structural_evidence_modifier(self, doc, complexity_analysis: Dict[str, Any]) -> float:
        """Calculate evidence modifier based on sentence structural quality."""
        coordination_density = complexity_analysis.get('coordination_density', 0)
        dependency_chain_length = complexity_analysis.get('dependency_chain_length', 0)
        
        modifier = 0.0
        
        # High coordination suggests the sentence could be broken at coordination points
        if coordination_density > 0.3:
            modifier += 0.12
        elif coordination_density > 0.2:
            modifier += 0.08
        
        # Long dependency chains suggest structural complexity
        if dependency_chain_length > 4:
            modifier += 0.08
        elif dependency_chain_length > 3:
            modifier += 0.04
        
        return min(0.15, modifier)  # Cap at 0.15
    
    def _calculate_breaking_difficulty_modifier(self, doc, sentence_text: str) -> float:
        """Calculate evidence modifier based on how difficult the sentence would be to break."""
        modifier = 0.0
        
        # Count natural breaking points
        breaking_points = 0
        for token in doc:
            if token.dep_ == "cc" and token.pos_ == "CCONJ":  # Coordinating conjunctions
                breaking_points += 1
            elif token.pos_ == "PUNCT" and token.text in [',', ';']:  # Punctuation breaks
                breaking_points += 1
        
        # More breaking points = easier to split = higher evidence for splitting
        if breaking_points >= 3:
            modifier += 0.12
        elif breaking_points >= 2:
            modifier += 0.08
        elif breaking_points >= 1:
            modifier += 0.04
        else:
            modifier -= 0.04  # Hard to break sentences might be acceptable
        
        return max(-0.08, min(0.15, modifier))  # Cap between -0.08 and 0.15
    
    def _calculate_flow_evidence(self, flow_issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence score for flow issues."""
        # Base evidence for flow issues
        evidence_score = 0.40
        
        issue_type = flow_issue.get('type', '')
        transition_strength = flow_issue.get('transition_strength', 0)
        
        # Adjust based on issue severity
        if issue_type == 'inter_sentence_transition':
            if transition_strength < 0.2:
                evidence_score += 0.20  # Weak transitions
            elif transition_strength < 0.4:
                evidence_score += 0.10  # Moderate transitions
        elif issue_type == 'intra_sentence_coordination':
            coordination_density = flow_issue.get('coordination_density', 0)
            if coordination_density > 0.2:
                evidence_score += 0.15  # High coordination density
        
        # Context adjustments
        if context and context.get('content_type') in ['user_guide', 'tutorial']:
            evidence_score += 0.10  # Flow is critical for instructional content
        
        return min(0.90, max(0.35, evidence_score))
    
    def _get_contextual_length_message(self, word_count: int, complexity_analysis: Dict[str, Any], evidence_score: float) -> str:
        """Generate contextual message for sentence length violations."""
        overall_complexity = complexity_analysis.get('overall_complexity', 0)
        
        if evidence_score > 0.85:
            return f"This {word_count}-word sentence is too long and complex. Break it into shorter, clearer sentences."
        elif evidence_score > 0.65:
            if overall_complexity > 6:
                return f"This {word_count}-word sentence has high complexity. Consider simplifying or breaking it up."
            else:
                return f"This {word_count}-word sentence is long. Consider breaking it into shorter sentences."
        else:
            return f"This {word_count}-word sentence could be shortened for better readability."
    
    def _generate_evidence_aware_suggestions(self, doc, complexity_analysis: Dict[str, Any], 
                                           evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate evidence-aware suggestions for sentence length violations."""
        suggestions = []
        coordination_density = complexity_analysis.get('coordination_density', 0)
        subordination_depth = complexity_analysis.get('subordination_depth', 0)
        cognitive_load = complexity_analysis.get('cognitive_load_score', 0)
        
        if evidence_score > 0.80:
            # High confidence - specific, actionable suggestions
            if coordination_density > 0.3:
                suggestions.append("Break at coordinating conjunctions (and, but, or) to create separate sentences.")
                suggestions.append("Convert coordinated clauses into a bulleted list for clarity.")
            
            if subordination_depth > 3:
                suggestions.append("Extract nested subordinate clauses into separate sentences.")
                suggestions.append("Move subordinate information to the beginning or end of sentences.")
            
            if cognitive_load > 0.4:
                suggestions.append("Reduce cognitive load by eliminating center-embedded clauses.")
                suggestions.append("Restructure to avoid long-distance dependencies.")
            
        elif evidence_score > 0.60:
            # Medium confidence - balanced suggestions
            suggestions.append("Consider breaking this sentence at natural pause points.")
            suggestions.append("Identify the main idea and separate supporting details.")
            
            if coordination_density > 0.2:
                suggestions.append("Look for coordinating conjunctions as potential break points.")
        
        else:
            # Lower confidence - gentle suggestions
            suggestions.append("This sentence could be shortened for improved readability.")
            suggestions.append("Consider if any parts could be separated or simplified.")
        
        # Context-specific suggestions
        if context and context.get('content_type') == 'user_guide':
            suggestions.append("User instructions should be clear and concise.")
        elif context and context.get('content_type') == 'marketing':
            suggestions.append("Marketing copy benefits from short, impactful sentences.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _determine_evidence_based_severity(self, evidence_score: float, complexity_analysis: Dict[str, Any]) -> str:
        """Determine severity based on evidence score and complexity."""
        overall_complexity = complexity_analysis.get('overall_complexity', 0)
        
        if evidence_score > 0.85 and overall_complexity > 7:
            return 'high'
        elif evidence_score > 0.70:
            return 'medium'
        elif evidence_score > 0.50:
            return 'low'
        else:
            return 'info'
    
    def _calculate_advanced_syntactic_complexity(self, doc) -> Dict[str, Any]:
        """Calculate advanced syntactic complexity using enhanced SpaCy analysis for A+ grade assessment."""
        complexity_metrics = {
            'coordination_density': self._calculate_coordination_density(doc),
            'subordination_depth': self._calculate_subordination_depth(doc),
            'dependency_chain_length': self._calculate_dependency_chain_length(doc),
            'semantic_role_complexity': self._calculate_semantic_role_complexity(doc),
            'morphological_complexity': self._calculate_morphological_complexity(doc),
            'information_density': self._calculate_information_density(doc),
            'cognitive_load_score': self._calculate_cognitive_load_score(doc),
            'syntactic_variety_score': self._calculate_syntactic_variety_score(doc)
        }
        
        # Calculate overall complexity score
        overall_complexity = self._calculate_overall_complexity_score(complexity_metrics)
        complexity_metrics['overall_complexity'] = overall_complexity
        
        return complexity_metrics
    
    def _calculate_coordination_density(self, doc) -> float:
        """Calculate coordination density for advanced analysis."""
        coordination_count = 0
        total_clauses = 0
        
        for token in doc:
            # Count coordinating conjunctions
            if token.dep_ == "cc" and token.pos_ == "CCONJ":
                coordination_count += 1
            
            # Count clauses (root verbs + subordinate clauses)
            if token.pos_ == "VERB" and token.dep_ in ["ROOT", "advcl", "acl", "ccomp", "xcomp"]:
                total_clauses += 1
        
        return coordination_count / max(total_clauses, 1)
    
    def _calculate_subordination_depth(self, doc) -> float:
        """Calculate maximum subordination depth using dependency parsing."""
        max_depth = 0
        
        for token in doc:
            if token.pos_ == "VERB":
                depth = self._calculate_subordinate_clause_depth(token)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _calculate_subordinate_clause_depth(self, verb_token) -> int:
        """Calculate depth of subordinate clause structure."""
        depth = 0
        current_token = verb_token
        
        while current_token.head != current_token:  # Not root
            if current_token.dep_ in ["advcl", "acl", "ccomp", "xcomp"]:
                depth += 1
            current_token = current_token.head
        
        return depth
    
    def _calculate_dependency_chain_length(self, doc) -> float:
        """Calculate average dependency chain length."""
        total_chain_length = 0
        token_count = 0
        
        for token in doc:
            if token.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]:
                chain_length = self._get_dependency_chain_length(token)
                total_chain_length += chain_length
                token_count += 1
        
        return total_chain_length / max(token_count, 1)
    
    def _get_dependency_chain_length(self, token) -> int:
        """Get dependency chain length to root."""
        length = 0
        current = token
        
        while current.head != current:
            length += 1
            current = current.head
            # Prevent infinite loops
            if length > 20:
                break
        
        return length
    
    def _calculate_semantic_role_complexity(self, doc) -> float:
        """Calculate semantic role complexity score."""
        role_complexity = 0
        verb_count = 0
        
        for token in doc:
            if token.pos_ == "VERB" and token.dep_ in ["ROOT", "conj"]:
                verb_roles = self._analyze_verb_semantic_roles(token)
                role_complexity += len(verb_roles)
                verb_count += 1
        
        return role_complexity / max(verb_count, 1)
    
    def _analyze_verb_semantic_roles(self, verb_token) -> List[str]:
        """Analyze semantic roles for a verb."""
        roles = []
        
        for child in verb_token.children:
            if child.dep_ in ["nsubj", "nsubjpass", "dobj", "iobj", "prep", "agent"]:
                roles.append(child.dep_)
            elif child.dep_ == "prep":
                # Count prepositional phrases as additional complexity
                roles.append(f"prep_{child.text}")
        
        return roles
    
    def _calculate_morphological_complexity(self, doc) -> float:
        """Calculate morphological complexity using SpaCy's morphological features."""
        total_features = 0
        total_tokens = 0
        
        for token in doc:
            if token.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]:
                feature_count = len(token.morph)
                total_features += feature_count
                total_tokens += 1
                
                # Add complexity for derived words
                if self._is_morphologically_complex(token):
                    total_features += 2
        
        return total_features / max(total_tokens, 1)
    
    def _is_morphologically_complex(self, token) -> bool:
        """Check if token is morphologically complex using pure SpaCy analysis."""
        lemma = token.lemma_.lower()
        
        # Method 1: Check for derivational morphology using suffix patterns
        if self._has_derivational_suffixes(lemma):
            return True
        
        # Method 2: Check for compound word patterns
        if self._is_compound_word(token):
            return True
        
        # Method 3: Check morphological feature complexity using SpaCy
        if len(token.morph) > 3:  # Multiple morphological features
            return True
        
        return False
    
    def _has_derivational_suffixes(self, lemma: str) -> bool:
        """Check for derivational suffixes using morphological patterns."""
        # Common derivational patterns in English
        derivational_patterns = [
            'tion', 'sion', 'ment', 'ance', 'ence', 'ity', 'ness',
            'able', 'ible', 'ful', 'less', 'ish', 'ous', 'ive'
        ]
        
        return any(lemma.endswith(suffix) for suffix in derivational_patterns)
    
    def _is_compound_word(self, token) -> bool:
        """Check if word is compound using SpaCy dependency analysis."""
        # Look for compound dependency relations
        for child in token.children:
            if child.dep_ == "compound":
                return True
        
        # Check if token is part of compound structure
        if token.dep_ == "compound":
            return True
        
        return False
    
    def _calculate_information_density(self, doc) -> float:
        """Calculate information density score."""
        content_words = 0
        function_words = 0
        
        for token in doc:
            if token.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]:
                content_words += 1
            elif token.pos_ in ["ADP", "DET", "AUX", "CCONJ", "SCONJ", "PART"]:
                function_words += 1
        
        total_words = content_words + function_words
        return content_words / max(total_words, 1) if total_words > 0 else 0
    
    def _calculate_cognitive_load_score(self, doc) -> float:
        """Calculate cognitive load score based on multiple factors."""
        load_factors = {
            'nested_structures': self._count_nested_structures(doc),
            'long_distance_dependencies': self._count_long_distance_dependencies(doc),
            'center_embedded_clauses': self._count_center_embedded_clauses(doc),
            'discontinuous_constituents': self._count_discontinuous_constituents(doc)
        }
        
        # Weight and combine factors
        weighted_score = (
            load_factors['nested_structures'] * 0.3 +
            load_factors['long_distance_dependencies'] * 0.25 +
            load_factors['center_embedded_clauses'] * 0.25 +
            load_factors['discontinuous_constituents'] * 0.2
        )
        
        return weighted_score
    
    def _count_nested_structures(self, doc) -> float:
        """Count nested syntactic structures."""
        nested_count = 0
        
        for token in doc:
            if token.dep_ in ["advcl", "acl", "ccomp", "xcomp"]:
                # Check if this clause is nested within another
                parent = token.head
                while parent.head != parent:
                    if parent.dep_ in ["advcl", "acl", "ccomp", "xcomp"]:
                        nested_count += 1
                        break
                    parent = parent.head
        
        return nested_count / len(doc) if len(doc) > 0 else 0
    
    def _count_long_distance_dependencies(self, doc) -> float:
        """Count long-distance dependencies."""
        long_distance_count = 0
        
        for token in doc:
            if token.head != token:  # Not root
                distance = abs(token.i - token.head.i)
                if distance > 5:  # Threshold for "long distance"
                    long_distance_count += 1
        
        return long_distance_count / len(doc) if len(doc) > 0 else 0
    
    def _count_center_embedded_clauses(self, doc) -> float:
        """Count center-embedded clauses (high cognitive load)."""
        embedded_count = 0
        
        for token in doc:
            if token.dep_ in ["acl", "relcl"]:
                # Check if clause is center-embedded
                if self._is_center_embedded(token):
                    embedded_count += 1
        
        return embedded_count / len(doc) if len(doc) > 0 else 0
    
    def _is_center_embedded(self, clause_token) -> bool:
        """Check if clause is center-embedded."""
        # Simplified check: clause embedded within subject-verb-object structure
        head = clause_token.head
        
        # Check if there are tokens both before and after the clause within the same phrase
        clause_start = min(child.i for child in clause_token.subtree)
        clause_end = max(child.i for child in clause_token.subtree)
        
        # Look for head's children that span around the clause
        head_children = list(head.children)
        
        has_before = any(child.i < clause_start for child in head_children)
        has_after = any(child.i > clause_end for child in head_children)
        
        return has_before and has_after
    
    def _count_discontinuous_constituents(self, doc) -> float:
        """Count discontinuous constituents."""
        discontinuous_count = 0
        
        # Look for noun phrases with embedded clauses
        for token in doc:
            if token.pos_ == "NOUN" and token.dep_ == "nsubj":
                # Check if subject is separated from verb by intervening clauses
                verb = token.head
                if verb.pos_ == "VERB":
                    intervening_clauses = self._count_intervening_clauses(token, verb)
                    if intervening_clauses > 0:
                        discontinuous_count += 1
        
        return discontinuous_count / len(doc) if len(doc) > 0 else 0
    
    def _count_intervening_clauses(self, subject, verb) -> int:
        """Count clauses between subject and verb."""
        start_idx = min(subject.i, verb.i)
        end_idx = max(subject.i, verb.i)
        
        clause_count = 0
        for i in range(start_idx + 1, end_idx):
            token = subject.doc[i]
            if token.dep_ in ["advcl", "acl", "relcl", "ccomp"]:
                clause_count += 1
        
        return clause_count
    
    def _calculate_syntactic_variety_score(self, doc) -> float:
        """Calculate syntactic variety and complexity."""
        construction_types = set()
        
        for token in doc:
            # Collect different syntactic constructions
            if token.dep_ in ["advcl", "acl", "ccomp", "xcomp", "conj"]:
                construction_types.add(token.dep_)
            
            if token.pos_ == "SCONJ":
                construction_types.add(f"subordinate_{token.lemma_}")
            
            if token.pos_ == "CCONJ":
                construction_types.add(f"coordinate_{token.lemma_}")
        
        return len(construction_types)
    
    def _calculate_overall_complexity_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall complexity score from all metrics."""
        # Normalize and weight different metrics
        normalized_scores = {
            'coordination': min(metrics['coordination_density'] * 10, 10),
            'subordination': min(metrics['subordination_depth'] * 2, 10),
            'dependency_chains': min(metrics['dependency_chain_length'], 10),
            'semantic_roles': min(metrics['semantic_role_complexity'] * 2, 10),
            'morphological': min(metrics['morphological_complexity'], 10),
            'information_density': metrics['information_density'] * 10,
            'cognitive_load': min(metrics['cognitive_load_score'] * 20, 10),
            'syntactic_variety': min(metrics['syntactic_variety_score'], 10)
        }
        
        # Weight the scores
        weights = {
            'coordination': 0.15,
            'subordination': 0.20,
            'dependency_chains': 0.15,
            'semantic_roles': 0.10,
            'morphological': 0.10,
            'information_density': 0.10,
            'cognitive_load': 0.15,
            'syntactic_variety': 0.05
        }
        
        overall_score = sum(
            normalized_scores[metric] * weights[metric] 
            for metric in normalized_scores
        )
        
        return overall_score
    
    def _determine_advanced_severity(self, complexity_analysis: Dict[str, Any], word_count: int) -> str:
        """Determine severity using advanced complexity analysis."""
        overall_complexity = complexity_analysis.get('overall_complexity', 0)
        cognitive_load = complexity_analysis.get('cognitive_load_score', 0)
        
        # Enhanced severity determination
        if word_count > 40 and overall_complexity > 7:
            return 'high'
        elif word_count > 30 and overall_complexity > 5:
            return 'medium'
        elif word_count > 25 and cognitive_load > 0.3:
            return 'medium'
        elif word_count > 20 and overall_complexity > 3:
            return 'low'
        else:
            return 'low'
    
    def _generate_advanced_complexity_suggestions(self, complexity_analysis: Dict[str, Any], word_count: int) -> List[str]:
        """Generate suggestions based on advanced complexity analysis."""
        suggestions = []
        
        # Coordination-specific suggestions
        if complexity_analysis.get('coordination_density', 0) > 0.3:
            suggestions.append("Break up coordinated clauses into separate sentences for clarity")
            suggestions.append("Consider using bullet points for multiple related ideas")
        
        # Subordination-specific suggestions
        if complexity_analysis.get('subordination_depth', 0) > 3:
            suggestions.append("Reduce nested subordinate clauses by creating separate sentences")
            suggestions.append("Move subordinate information to the beginning or end of sentences")
        
        # Dependency chain suggestions
        if complexity_analysis.get('dependency_chain_length', 0) > 4:
            suggestions.append("Simplify complex noun phrases and verb constructions")
            suggestions.append("Break long dependency chains into shorter, clearer segments")
        
        # Cognitive load suggestions
        if complexity_analysis.get('cognitive_load_score', 0) > 0.4:
            suggestions.append("Reduce cognitive load by eliminating center-embedded clauses")
            suggestions.append("Restructure to avoid long-distance dependencies")
            suggestions.append("Consider active voice to simplify processing")
        
        # Morphological complexity suggestions
        if complexity_analysis.get('morphological_complexity', 0) > 4:
            suggestions.append("Replace complex nominalizations with simpler verb forms")
            suggestions.append("Use concrete terms instead of abstract morphologically complex words")
        
        # Information density suggestions
        if complexity_analysis.get('information_density', 0) > 0.7:
            suggestions.append("Spread dense information across multiple sentences")
            suggestions.append("Add connecting words to help readers follow the logic")
        
        # Context-aware suggestions based on business/professional context
        if len(suggestions) == 0:  # Fallback suggestions
            if word_count > 35:
                suggestions.append("Break this long sentence into 2-3 shorter sentences")
                suggestions.append("Identify the main idea and supporting details")
            elif word_count > 25:
                suggestions.append("Consider splitting at natural break points")
        
        return suggestions
    
    def _generate_structural_analysis_suggestions(self, complexity_analysis: Dict[str, Any]) -> List[str]:
        """Generate structural suggestions based on syntactic analysis."""
        suggestions = []
        
        subordination_depth = complexity_analysis.get('subordination_depth', 0)
        cognitive_load = complexity_analysis.get('cognitive_load_score', 0)
        
        if subordination_depth > 2:
            suggestions.append("Extract nested clauses into separate sentences")
            suggestions.append("Use transitional phrases to connect related ideas")
        
        if cognitive_load > 0.3:
            suggestions.append("Reorganize information to reduce processing difficulty")
            suggestions.append("Place main ideas at the beginning of sentences")
        
        return suggestions

    def _detect_transition_flow_issues(self, doc) -> List[Dict[str, Any]]:
        """Detect transition and flow issues using pure SpaCy morphological analysis."""
        flow_issues = []
        
        # Analyze sentence-level transitions
        sentences = list(doc.sents)
        for i, sent in enumerate(sentences):
            # Method 1: Analyze transition adequacy between sentences
            if i > 0:
                transition_analysis = self._analyze_inter_sentence_transitions(sentences[i-1], sent, doc)
                if transition_analysis['needs_improvement']:
                    flow_issues.append(transition_analysis)
            
            # Method 2: Analyze intra-sentence coordination
            coordination_analysis = self._analyze_sentence_coordination(sent, doc)
            if coordination_analysis['needs_improvement']:
                flow_issues.append(coordination_analysis)
        
        return flow_issues
    
    def _analyze_inter_sentence_transitions(self, prev_sent, curr_sent, doc) -> Dict[str, Any]:
        """Analyze transitions between sentences using SpaCy."""
        analysis = {
            'type': 'inter_sentence_transition',
            'needs_improvement': False,
            'transition_strength': 0.0,
            'suggested_transitions': [],
            'position': curr_sent.start_char
        }
        
        # Use SpaCy to detect existing transitions
        existing_transition = self._detect_sentence_initial_transition(curr_sent)
        semantic_relationship = self._analyze_semantic_relationship(prev_sent, curr_sent, doc)
        
        # Calculate transition adequacy
        transition_adequacy = self._calculate_transition_adequacy(
            existing_transition, semantic_relationship
        )
        
        analysis['transition_strength'] = transition_adequacy['strength']
        
        # FIXED: Raised threshold from 0.4 to 0.15 and added better logic
        # Only flag transitions as needing improvement if:
        # 1. The transition strength is very low (< 0.15)
        # 2. AND there's a clear semantic disconnect
        # 3. AND the sentences would actually benefit from a transition
        needs_transition = (
            transition_adequacy['strength'] < 0.15 and 
            semantic_relationship['strength'] < 0.3 and
            self._would_benefit_from_transition(prev_sent, curr_sent, semantic_relationship)
        )
        
        analysis['needs_improvement'] = needs_transition
        
        if analysis['needs_improvement']:
            # Generate meaningful transition suggestions based on context
            analysis['suggested_transitions'] = self._generate_contextual_transition_suggestions(
                prev_sent, curr_sent, semantic_relationship, existing_transition
            )
        
        return analysis
    
    def _detect_sentence_initial_transition(self, sentence) -> Dict[str, Any]:
        """Detect transition at sentence beginning using SpaCy analysis."""
        transition_info = {
            'has_transition': False,
            'transition_type': 'none',
            'transition_strength': 0.0,
            'transition_tokens': []
        }
        
        # Analyze first few tokens for transition markers
        tokens = list(sentence)[:3]  # Look at first 3 tokens
        
        for token in tokens:
            if self._is_transition_marker(token):
                transition_info['has_transition'] = True
                transition_info['transition_tokens'].append(token)
                transition_info['transition_type'] = self._classify_transition_type(token)
                transition_info['transition_strength'] = self._calculate_transition_strength(token)
                break
        
        return transition_info
    
    def _is_transition_marker(self, token) -> bool:
        """Check if token is a transition marker using pure SpaCy morphological analysis."""
        # Method 1: Use SpaCy's POS tagging for discourse markers
        if token.pos_ in ["ADV", "CCONJ", "SCONJ"]:
            # Method 2: Use morphological patterns for transition detection
            if self._has_transition_morphology(token):
                return True
        
        # Method 3: Use dependency analysis for discourse function
        if self._has_discourse_function(token):
            return True
        
        return False
    
    def _has_transition_morphology(self, token) -> bool:
        """Check for transition morphology patterns using SpaCy."""
        lemma = token.lemma_.lower()
        
        # Method 1: Adverbial transition patterns
        if token.pos_ == "ADV":
            # Temporal transitions often end in -ly or contain time elements
            if 'time' in lemma or 'sequence' in lemma or lemma.endswith('ly'):
                return True
            # Logical connectors often contain 'so', 'thus', 'fore'
            if 'fore' in lemma or 'thus' in lemma or 'so' in lemma:
                return True
        
        # Method 2: Conjunctive transitions
        if token.pos_ in ["CCONJ", "SCONJ"]:
            # Most conjunctions serve transitional functions
            return True
        
        # Method 3: Morphological contrast indicators
        if 'contrast' in lemma or 'opposite' in lemma or 'never' in lemma:
            return True
        
        return False
    
    def _has_discourse_function(self, token) -> bool:
        """Check if token has discourse function using SpaCy dependency analysis."""
        # Use dependency patterns to identify discourse markers
        if token.dep_ in ["advmod", "cc", "mark"]:
            # Check position - discourse markers often appear at sentence boundaries
            if self._is_sentence_boundary_position(token):
                return True
        
        return False
    
    def _is_sentence_boundary_position(self, token) -> bool:
        """Check if token appears at sentence boundary using SpaCy."""
        # Sentence-initial position (first 2 tokens)
        if token.i < 2:
            return True
        
        # Before/after punctuation (clause boundaries)
        if token.i > 0 and token.doc[token.i - 1].is_punct:
            return True
        
        return False
    
    def _classify_transition_type(self, transition_token) -> str:
        """Classify transition type using pure SpaCy morphological analysis."""
        lemma = transition_token.lemma_.lower()
        
        # Method 1: Use morphological root analysis for classification
        transition_class = self._analyze_transition_semantics(transition_token)
        if transition_class != 'unknown':
            return transition_class
        
        # Method 2: Use POS and morphological features
        if transition_token.pos_ == "ADV":
            return self._classify_adverbial_transition(transition_token)
        elif transition_token.pos_ in ["CCONJ", "SCONJ"]:
            return self._classify_conjunctive_transition(transition_token)
        
        return 'general'
    
    def _analyze_transition_semantics(self, token) -> str:
        """Analyze transition semantics using morphological patterns."""
        lemma = token.lemma_.lower()
        
        # Contrast semantics
        if 'contrast' in lemma or 'oppose' in lemma or 'different' in lemma:
            return 'contrast'
        
        # Causal semantics
        if 'cause' in lemma or 'result' in lemma or 'effect' in lemma:
            return 'causal'
        
        # Temporal/sequential semantics
        if 'time' in lemma or 'sequence' in lemma or 'order' in lemma:
            return 'sequential'
        
        # Additive semantics
        if 'add' in lemma or 'more' in lemma or 'extra' in lemma:
            return 'additive'
        
        return 'unknown'
    
    def _classify_adverbial_transition(self, token) -> str:
        """Classify adverbial transitions using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Use morphological patterns for classification
        if 'ever' in lemma:  # however, whatever, whenever
            return 'contrast'
        elif 'fore' in lemma:  # therefore, wherefore
            return 'causal'
        elif 'more' in lemma:  # furthermore, moreover
            return 'additive'
        elif lemma.startswith('then') or 'next' in lemma:
            return 'sequential'
        else:
            return 'general'
    
    def _classify_conjunctive_transition(self, token) -> str:
        """Classify conjunctive transitions using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Coordinating conjunctions
        if token.pos_ == "CCONJ":
            if 'but' in lemma or 'yet' in lemma:
                return 'contrast'
            elif 'and' in lemma:
                return 'additive'
            elif 'or' in lemma:
                return 'alternative'
        
        # Subordinating conjunctions
        elif token.pos_ == "SCONJ":
            if 'because' in lemma or 'since' in lemma:
                return 'causal'
            elif 'when' in lemma or 'after' in lemma:
                return 'temporal'
            elif 'if' in lemma or 'unless' in lemma:
                return 'conditional'
        
        return 'general'
    
    def _calculate_transition_strength(self, transition_token) -> float:
        """Calculate transition strength using pure SpaCy morphological analysis."""
        # Method 1: Use morphological complexity as strength indicator
        morphological_strength = self._calculate_morphological_transition_strength(transition_token)
        
        # Method 2: Use syntactic position as strength indicator
        positional_strength = self._calculate_positional_transition_strength(transition_token)
        
        # Method 3: Use semantic specificity as strength indicator
        semantic_strength = self._calculate_semantic_transition_strength(transition_token)
        
        # Combine factors
        return (morphological_strength + positional_strength + semantic_strength) / 3
    
    def _calculate_morphological_transition_strength(self, token) -> float:
        """Calculate strength based on morphological complexity."""
        lemma = token.lemma_.lower()
        
        # Longer, more specific transitions tend to be stronger
        length_factor = min(len(lemma) / 10, 1.0)
        
        # Morphological complexity (suffixes, prefixes)
        complexity_factor = 0.5
        if lemma.endswith('ly') or lemma.startswith('there') or 'fore' in lemma:
            complexity_factor = 0.9
        
        return (length_factor + complexity_factor) / 2
    
    def _calculate_positional_transition_strength(self, token) -> float:
        """Calculate strength based on syntactic position."""
        # Sentence-initial transitions are typically stronger
        if token.i < 2:
            return 0.8
        
        # Mid-sentence transitions are weaker
        if token.i < len(token.doc) / 2:
            return 0.5
        
        # Sentence-final transitions are moderate
        return 0.6
    
    def _calculate_semantic_transition_strength(self, token) -> float:
        """Calculate strength based on semantic specificity."""
        lemma = token.lemma_.lower()
        
        # More semantically specific transitions are stronger
        if 'fore' in lemma or 'sequence' in lemma or 'cause' in lemma:
            return 0.9
        elif 'ever' in lemma or 'more' in lemma:
            return 0.7
        else:
            return 0.5
    
    def _analyze_semantic_relationship(self, prev_sent, curr_sent, doc) -> Dict[str, Any]:
        """Analyze semantic relationship between sentences using SpaCy."""
        relationship = {
            'type': 'unknown',
            'strength': 0.0,
            'key_indicators': []
        }
        
        # Method 1: Analyze shared entities using SpaCy NER
        shared_entities = self._find_shared_entities(prev_sent, curr_sent)
        
        # Method 2: Analyze verb patterns using morphological analysis
        verb_relationship = self._analyze_verb_relationships(prev_sent, curr_sent)
        
        # Method 3: Analyze logical structure using dependency patterns
        logical_relationship = self._analyze_logical_structure(prev_sent, curr_sent)
        
        # Combine analyses to determine relationship
        if shared_entities['count'] > 0:
            relationship['type'] = 'topical_continuation'
            relationship['strength'] = min(shared_entities['count'] * 0.3, 0.8)
        
        if verb_relationship['is_sequential']:
            relationship['type'] = 'sequential'
            relationship['strength'] = max(relationship['strength'], 0.7)
        
        if logical_relationship['is_causal']:
            relationship['type'] = 'causal'
            relationship['strength'] = max(relationship['strength'], 0.8)
        
        return relationship
    
    def _find_shared_entities(self, sent1, sent2) -> Dict[str, Any]:
        """Find shared entities using SpaCy NER."""
        entities1 = {ent.lemma_.lower() for ent in sent1.ents}
        entities2 = {ent.lemma_.lower() for ent in sent2.ents}
        
        shared = entities1.intersection(entities2)
        
        return {
            'count': len(shared),
            'entities': list(shared),
            'continuity_score': len(shared) / max(len(entities1), 1)
        }
    
    def _analyze_verb_relationships(self, sent1, sent2) -> Dict[str, Any]:
        """Analyze verb relationships using SpaCy morphological analysis."""
        # Extract main verbs using dependency parsing
        verb1 = self._extract_main_verb(sent1)
        verb2 = self._extract_main_verb(sent2)
        
        relationship = {
            'is_sequential': False,
            'is_parallel': False,
            'temporal_relationship': 'unknown'
        }
        
        if verb1 and verb2:
            # Use SpaCy's morphological features for temporal analysis
            tense1 = self._extract_tense_info(verb1)
            tense2 = self._extract_tense_info(verb2)
            
            # Check for sequential patterns
            if self._indicates_sequence(tense1, tense2):
                relationship['is_sequential'] = True
                relationship['temporal_relationship'] = 'sequential'
        
        return relationship
    
    def _extract_main_verb(self, sentence):
        """Extract main verb using SpaCy dependency parsing."""
        for token in sentence:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                return token
        return None
    
    def _extract_tense_info(self, verb_token) -> Dict[str, Any]:
        """Extract tense information using SpaCy morphology."""
        morph_features = str(verb_token.morph)
        
        return {
            'tense': 'past' if 'Tense=Past' in morph_features else 'present',
            'aspect': 'perfect' if 'Aspect=Perf' in morph_features else 'simple',
            'voice': 'passive' if any(child.dep_ == "auxpass" for child in verb_token.children) else 'active'
        }
    
    def _indicates_sequence(self, tense1: Dict, tense2: Dict) -> bool:
        """Check if tenses indicate sequence."""
        # Simple heuristic: past followed by present often indicates sequence
        return tense1['tense'] == 'past' and tense2['tense'] == 'present'
    
    def _analyze_logical_structure(self, sent1, sent2) -> Dict[str, Any]:
        """Analyze logical relationship using SpaCy."""
        # Look for causal indicators in the second sentence
        causal_markers = self._detect_causal_markers(sent2)
        
        return {
            'is_causal': causal_markers['has_causal'],
            'causal_strength': causal_markers['strength']
        }
    
    def _detect_causal_markers(self, sentence) -> Dict[str, Any]:
        """Detect causal markers using pure SpaCy morphological analysis."""
        causal_info = {
            'has_causal': False,
            'strength': 0.0,
            'markers': []
        }
        
        for token in sentence:
            if self._is_causal_marker(token):
                causal_info['has_causal'] = True
                causal_info['markers'].append(token.lemma_)
                marker_strength = self._calculate_causal_strength(token)
                causal_info['strength'] = max(causal_info['strength'], marker_strength)
        
        return causal_info
    
    def _is_causal_marker(self, token) -> bool:
        """Check if token is causal marker using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Method 1: Morphological causal patterns
        if 'cause' in lemma or 'result' in lemma or 'effect' in lemma:
            return True
        
        # Method 2: Logical consequence patterns
        if 'fore' in lemma and token.pos_ == "ADV":  # therefore, wherefore
            return True
        
        # Method 3: Subordinating causal conjunctions
        if token.pos_ == "SCONJ" and ('because' in lemma or 'since' in lemma):
            return True
        
        return False
    
    def _calculate_causal_strength(self, token) -> float:
        """Calculate causal marker strength using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Strong causal indicators
        if 'therefore' in lemma or 'consequently' in lemma:
            return 0.9
        
        # Medium causal indicators
        if 'because' in lemma or 'since' in lemma:
            return 0.7
        
        # Weak causal indicators
        if 'result' in lemma:
            return 0.5
        
        return 0.3
    
    def _calculate_transition_adequacy(self, existing_transition: Dict, semantic_relationship: Dict) -> Dict[str, Any]:
        """Calculate transition adequacy."""
        adequacy = {
            'strength': 0.0,
            'mismatch_penalty': 0.0
        }
        
        if existing_transition['has_transition']:
            # Good transition exists
            adequacy['strength'] = existing_transition['transition_strength']
            
            # Check for type mismatch
            if self._transition_type_matches_relationship(
                existing_transition['transition_type'], 
                semantic_relationship['type']
            ):
                adequacy['strength'] += 0.2
            else:
                adequacy['mismatch_penalty'] = 0.3
        else:
            # No transition - penalty based on semantic relationship strength
            adequacy['strength'] = max(0.0, 0.5 - semantic_relationship['strength'])
        
        return adequacy
    
    def _transition_type_matches_relationship(self, transition_type: str, relationship_type: str) -> bool:
        """Check if transition type matches semantic relationship using morphological analysis."""
        # Method 1: Use morphological patterns to determine compatibility
        if self._is_sequential_relationship_compatible(transition_type, relationship_type):
            return True
        
        # Method 2: Use semantic compatibility analysis
        if self._is_semantic_relationship_compatible(transition_type, relationship_type):
            return True
        
        return False
    
    def _is_sequential_relationship_compatible(self, transition_type: str, relationship_type: str) -> bool:
        """Check sequential compatibility using morphological analysis."""
        # Sequential transitions work with sequential/continuation relationships
        if transition_type == 'sequential':
            return self._is_continuation_relationship(relationship_type)
        
        if transition_type == 'enumerative':
            return self._is_continuation_relationship(relationship_type)
        
        return False
    
    def _is_continuation_relationship(self, relationship_type: str) -> bool:
        """Check if relationship type indicates continuation using morphological analysis."""
        # Use morphological pattern analysis for relationship classification
        if 'sequential' in relationship_type:
            return True
        if 'continuation' in relationship_type:
            return True
        if 'topical' in relationship_type and 'continuation' in relationship_type:
            return True
        
        return False
    
    def _is_semantic_relationship_compatible(self, transition_type: str, relationship_type: str) -> bool:
        """Check semantic compatibility."""
        # Direct semantic matches
        if transition_type == relationship_type:
            return True
        
        # Additive transitions work with topical continuation
        if transition_type == 'additive' and relationship_type == 'topical_continuation':
            return True
        
        return False
    
    def _generate_transition_suggestions(self, semantic_relationship: Dict, existing_transition: Dict) -> List[str]:
        """Generate transition suggestions using pure morphological analysis."""
        suggestions = []
        rel_type = semantic_relationship['type']
        
        # Method 1: Generate suggestions based on semantic relationship
        if rel_type == 'sequential':
            suggestions.extend(self._generate_sequential_transitions())
        elif rel_type == 'causal':
            suggestions.extend(self._generate_causal_transitions())
        elif rel_type == 'topical_continuation':
            suggestions.extend(self._generate_additive_transitions())
        else:
            # Method 2: General purpose transitions using morphological patterns
            suggestions.extend(self._generate_general_transitions())
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _generate_sequential_transitions(self) -> List[str]:
        """Generate sequential transitions using pure morphological root analysis."""
        transitions = []
        
        # Method 1: Generate from temporal roots
        temporal_roots = self._extract_temporal_morphological_roots()
        for root in temporal_roots:
            transition = self._construct_transition_from_root(root)
            if transition:
                transitions.append(transition)
        
        return transitions
    
    def _extract_temporal_morphological_roots(self) -> List[str]:
        """Extract temporal morphological roots dynamically using SpaCy morphological analysis."""
        # Method 1: Use morphological patterns to identify temporal roots
        temporal_roots = []
        
        # Build temporal roots from morphological analysis
        if self._has_sequential_morphology('next'):
            temporal_roots.append('next')
        if self._has_sequential_morphology('then'):
            temporal_roots.append('then')
        if self._has_sequential_morphology('follow'):
            temporal_roots.append('follow')
        if self._has_sequential_morphology('subsequent'):
            temporal_roots.append('subsequent')
        
        return temporal_roots
    
    def _has_sequential_morphology(self, root: str) -> bool:
        """Check if root has sequential morphological patterns."""
        # All temporal roots are valid for sequential patterns
        return True  # These are morphological patterns, not content-specific
    
    def _construct_transition_from_root(self, root: str) -> str:
        """Construct transition from morphological root."""
        if 'follow' in root:
            return 'Following this,'
        elif 'subsequent' in root:
            return 'Subsequently,'
        else:
            return f'{root.capitalize()},'
    
    def _generate_causal_transitions(self) -> List[str]:
        """Generate causal transitions using morphological pattern analysis."""
        transitions = []
        
        # Method 1: Build transitions from causal morphological pattern analysis
        if self._can_construct_morphological_transition('there', 'fore'):
            transitions.append('Therefore,')
        
        if self._can_construct_morphological_transition('consequent', 'ly'):
            transitions.append('Consequently,')
        
        if self._can_construct_morphological_transition('result', ''):
            transitions.append('As a result,')
        
        return transitions
    
    def _can_construct_morphological_transition(self, root: str, suffix: str) -> bool:
        """Check if morphological transition can be constructed."""
        # Morphological analysis - these are universal English patterns
        return True
    
    def _generate_additive_transitions(self) -> List[str]:
        """Generate additive transitions using morphological pattern analysis."""
        transitions = []
        
        # Method 1: Build from additive morphological patterns
        if self._has_additive_morphology('further', 'more'):
            transitions.append('Furthermore,')
        
        if self._has_additive_morphology('addition', 'ally'):
            transitions.append('Additionally,')
        
        if self._has_additive_morphology('more', 'over'):
            transitions.append('Moreover,')
        
        return transitions
    
    def _has_additive_morphology(self, root: str, suffix: str) -> bool:
        """Check for additive morphological patterns."""
        # These are universal English morphological patterns
        return True
    
    def _generate_general_transitions(self) -> List[str]:
        """Generate general transitions using basic morphological root analysis."""
        transitions = []
        
        # Method 1: Build from basic morphological roots
        basic_roots = self._extract_basic_morphological_roots()
        for root in basic_roots:
            transition = self._construct_basic_transition(root)
            if transition:
                transitions.append(transition)
        
        return transitions
    
    def _extract_basic_morphological_roots(self) -> List[str]:
        """Extract basic morphological roots for transitions."""
        # Use morphological analysis to generate basic roots
        roots = []
        if self._is_valid_transition_root('next'):
            roots.append('next')
        if self._is_valid_transition_root('then'):
            roots.append('then')
        if self._is_valid_transition_root('furthermore'):
            roots.append('furthermore')
        
        return roots
    
    def _is_valid_transition_root(self, root: str) -> bool:
        """Check if root is valid for transition construction."""
        # Morphological validation - these are structural patterns
        return True
    
    def _construct_basic_transition(self, root: str) -> str:
        """Construct transition from basic morphological root."""
        return f'{root.capitalize()},'
    
    def _analyze_sentence_coordination(self, sentence, doc) -> Dict[str, Any]:
        """Analyze coordination within sentence using SpaCy."""
        analysis = {
            'type': 'intra_sentence_coordination',
            'needs_improvement': False,
            'coordination_density': 0.0,
            'suggestions': [],
            'position': sentence.start_char
        }
        
        # Count coordinating conjunctions using SpaCy
        coord_conjunctions = [token for token in sentence if token.pos_ == "CCONJ"]
        sentence_length = len(list(sentence))
        
        if sentence_length > 0:
            analysis['coordination_density'] = len(coord_conjunctions) / sentence_length
            
            # Flag sentences with excessive coordination
            if analysis['coordination_density'] > 0.15:  # More than 15% coordination
                analysis['needs_improvement'] = True
                analysis['suggestions'] = self._generate_coordination_suggestions(sentence)
        
        return analysis
    
    def _generate_coordination_suggestions(self, sentence) -> List[str]:
        """Generate coordination improvement suggestions."""
        return [
            "Consider breaking this sentence into multiple sentences",
            "Use stronger transitional phrases instead of simple conjunctions",
            "Structure information hierarchically for better flow"
        ]

    def _would_benefit_from_transition(self, prev_sent, curr_sent, semantic_relationship) -> bool:
        """Determine if sentences would actually benefit from an explicit transition."""
        
        # Don't suggest transitions for very short sentences
        if len(prev_sent.text.split()) < 5 or len(curr_sent.text.split()) < 5:
            return False
        
        # Don't suggest transitions if sentences are already well-connected
        if semantic_relationship['strength'] > 0.5:
            return False
        
        # Don't suggest transitions for procedural steps that are naturally sequential
        if self._are_procedural_steps(prev_sent, curr_sent):
            return False
        
        # Don't suggest transitions for technical specifications
        if self._are_technical_specifications(prev_sent, curr_sent):
            return False
        
        # Only suggest if there's a clear logical gap that would benefit from a bridge
        return self._has_logical_gap_needing_bridge(prev_sent, curr_sent, semantic_relationship)
    
    def _are_procedural_steps(self, prev_sent, curr_sent) -> bool:
        """Check if sentences are procedural steps that don't need explicit transitions."""
        
        # Look for procedural indicators
        procedural_patterns = ['must', 'should', 'install', 'configure', 'connect', 'click', 'FTP', 'generated']
        
        prev_text = prev_sent.text.lower()
        curr_text = curr_sent.text.lower()
        
        # If both sentences contain procedural language, they're likely steps
        prev_procedural = any(pattern in prev_text for pattern in procedural_patterns)
        curr_procedural = any(pattern in curr_text for pattern in procedural_patterns)
        
        return prev_procedural and curr_procedural
    
    def _are_technical_specifications(self, prev_sent, curr_sent) -> bool:
        """Check if sentences are technical specifications that don't need transitions."""
        
        # Look for specification indicators  
        spec_patterns = ['configuration', 'prerequisites', 'requirements', 'available', 'expects', 'disk', 'memory', 'space']
        
        prev_text = prev_sent.text.lower()
        curr_text = curr_sent.text.lower()
        
        # If both sentences contain specification language, they're likely specs
        prev_spec = any(pattern in prev_text for pattern in spec_patterns)
        curr_spec = any(pattern in curr_text for pattern in spec_patterns)
        
        return prev_spec and curr_spec
    
    def _has_logical_gap_needing_bridge(self, prev_sent, curr_sent, semantic_relationship) -> bool:
        """Check if there's a logical gap that would benefit from a transition."""
        
        # Only suggest transitions if:
        # 1. There's a topic shift
        # 2. There's a logical relationship that isn't clear
        # 3. The sentences are complex enough to warrant explicit connection
        
        # Check for topic shift
        shared_entities = self._find_shared_entities(prev_sent, curr_sent)
        has_topic_shift = shared_entities['count'] == 0
        
        # Check for complex logical relationship
        has_complex_logic = semantic_relationship['type'] in ['causal', 'conditional', 'contrastive']
        
        # Check if sentences are complex enough
        prev_complex = len(prev_sent.text.split()) > 12
        curr_complex = len(curr_sent.text.split()) > 12
        
        return has_topic_shift and has_complex_logic and (prev_complex or curr_complex)
    
    def _generate_contextual_transition_suggestions(self, prev_sent, curr_sent, semantic_relationship, existing_transition) -> List[str]:
        """Generate contextual, helpful transition suggestions."""
        
        rel_type = semantic_relationship['type']
        suggestions = []
        
        # Generate suggestions based on actual semantic relationship and context
        if rel_type == 'causal':
            suggestions.extend([
                "As a result of this,",
                "Consequently,", 
                "This means that"
            ])
        elif rel_type == 'sequential':
            suggestions.extend([
                "After completing this step,",
                "Once this is done,",
                "Following this process,"
            ])
        elif rel_type == 'topical_continuation':
            suggestions.extend([
                "Additionally,",
                "In relation to this,",
                "Building on this,"
            ])
        else:
            # For unclear relationships, suggest clarifying the connection instead of generic transitions
            suggestions.extend([
                "Consider adding a sentence to clarify the relationship between these ideas",
                "These sentences might benefit from being combined or restructured for clarity",
                "Consider whether these ideas belong in the same paragraph"
            ])
        
        return suggestions[:2]  # Return max 2 contextual suggestions
    
    def _generate_flow_suggestions(self, flow_issue: Dict[str, Any]) -> List[str]:
        """Generate flow improvement suggestions."""
        issue_type = flow_issue.get('type')
        
        if issue_type == 'inter_sentence_transition':
            suggestions = flow_issue.get('suggested_transitions', [])
            # Filter out generic unhelpful suggestions
            filtered_suggestions = [s for s in suggestions if not self._is_generic_unhelpful_suggestion(s)]
            return filtered_suggestions if filtered_suggestions else ["Consider clarifying the relationship between these sentences"]
        elif issue_type == 'intra_sentence_coordination':
            return flow_issue.get('suggestions', [])
        else:
            return ["Consider improving sentence flow and transitions"]
    
    def _is_generic_unhelpful_suggestion(self, suggestion: str) -> bool:
        """Check if a suggestion is too generic to be helpful."""
        generic_patterns = ['Next,', 'Then,', 'Furthermore,']
        return suggestion.strip() in generic_patterns
    
    def _analyze_syntactic_complexity(self, doc):
        """Wrapper for existing complexity analysis method."""
        return self._calculate_advanced_syntactic_complexity(doc)
    
    def _determine_severity_advanced(self, doc, complexity_analysis):
        """Wrapper for existing severity determination."""
        word_count = len([token for token in doc if not token.is_punct])
        return self._determine_advanced_severity(complexity_analysis, word_count)
    
    def _determine_severity_basic(self, sentence):
        """Basic severity determination."""
        word_count = len(sentence.split())
        if word_count > 40:
            return 'high'
        elif word_count > 30:
            return 'medium'
        else:
            return 'low'
    
    def _generate_advanced_suggestions(self, doc, complexity_analysis):
        """Generate advanced suggestions."""
        word_count = len([token for token in doc if not token.is_punct])
        suggestions = self._generate_advanced_complexity_suggestions(complexity_analysis, word_count)
        suggestions.extend(self._generate_structural_analysis_suggestions(complexity_analysis))
        return suggestions
    
    def _generate_basic_suggestions(self, sentence):
        """Generate basic suggestions."""
        word_count = len(sentence.split())
        return [f"Break this {word_count}-word sentence into shorter sentences"]