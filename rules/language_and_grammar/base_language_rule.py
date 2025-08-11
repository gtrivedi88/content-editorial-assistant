"""
Base Language and Grammar Rule
A base class that all specific language rules will inherit from.
common evidence-based utilities.
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


class BaseLanguageRule(BaseRule):
    """
    Abstract base class for all language and grammar rules.
    It defines the common interface for analyzing text and provides
    shared evidence-based utilities.
    """

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for a specific language or grammar violation.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the analyze method.")

    # === COMMON EVIDENCE-BASED UTILITIES ===

    def _extract_spacy_features(self, token, feature_set: str = 'all') -> Dict[str, Any]:
        """
        Extract common SpaCy features from a token.
        
        Args:
            token: SpaCy token to analyze
            feature_set: Which features to extract ('all', 'basic', 'advanced')
            
        Returns:
            Dict containing extracted features
        """
        if not token:
            return {}
        
        features = {}
        
        # Basic features (always included)
        features['text'] = getattr(token, 'text', '')
        features['lower'] = getattr(token, 'lower_', '')
        features['pos'] = getattr(token, 'pos_', '')
        features['lemma'] = getattr(token, 'lemma_', '')
        
        if feature_set in ['all', 'advanced']:
            # Advanced features
            features['tag'] = getattr(token, 'tag_', '')
            features['dep'] = getattr(token, 'dep_', '')
            features['ent_type'] = getattr(token, 'ent_type_', '')
            features['is_sent_start'] = getattr(token, 'is_sent_start', False)
            features['is_title'] = getattr(token, 'is_title', False)
            features['is_upper'] = getattr(token, 'is_upper', False)
            features['is_lower'] = getattr(token, 'is_lower', False)
            features['is_alpha'] = getattr(token, 'is_alpha', False)
            features['is_digit'] = getattr(token, 'is_digit', False)
            features['is_punct'] = getattr(token, 'is_punct', False)
            
            # Morphological features
            if hasattr(token, 'morph') and token.morph:
                features['morph'] = token.morph.to_dict()
            else:
                features['morph'] = {}
        
        return features

    def _get_surrounding_context(self, token, doc, window: int = 2) -> Dict[str, Any]:
        """
        Get surrounding context for a token.
        
        Args:
            token: Target token
            doc: SpaCy document
            window: Number of tokens before/after to include
            
        Returns:
            Dict with surrounding context information
        """
        if not token or not doc:
            return {}
        
        context = {
            'prev_tokens': [],
            'next_tokens': [],
            'sentence_position': 'middle'
        }
        
        # Get previous tokens
        start_idx = max(0, token.i - window)
        for i in range(start_idx, token.i):
            if i < len(doc):
                context['prev_tokens'].append(self._extract_spacy_features(doc[i], 'basic'))
        
        # Get next tokens
        end_idx = min(len(doc), token.i + window + 1)
        for i in range(token.i + 1, end_idx):
            if i < len(doc):
                context['next_tokens'].append(self._extract_spacy_features(doc[i], 'basic'))
        
        # Determine sentence position
        if hasattr(token, 'is_sent_start') and token.is_sent_start:
            context['sentence_position'] = 'start'
        elif token.i == len(doc) - 1 or (token.i + 1 < len(doc) and getattr(doc[token.i + 1], 'is_sent_start', False)):
            context['sentence_position'] = 'end'
        
        return context

    # === COMMON CONTENT TYPE DETECTION ===

    def _is_technical_documentation(self, text: str) -> bool:
        """Check if text appears to be technical documentation."""
        technical_indicators = [
            'api', 'sdk', 'configuration', 'install', 'setup', 'deployment',
            'architecture', 'system', 'database', 'server', 'client',
            'framework', 'library', 'module', 'component', 'interface'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in technical_indicators if indicator in text_lower) >= 3

    def _is_procedural_documentation(self, text: str) -> bool:
        """Check if text appears to be procedural documentation."""
        procedural_indicators = [
            'step', 'procedure', 'process', 'workflow', 'instructions',
            'how to', 'getting started', 'tutorial', 'guide', 'walkthrough',
            'click', 'select', 'enter', 'configure', 'follow these steps'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in procedural_indicators if indicator in text_lower) >= 3

    def _is_api_documentation(self, text: str) -> bool:
        """Check if text appears to be API documentation."""
        api_indicators = [
            'api', 'endpoint', 'method', 'parameter', 'request', 'response',
            'authentication', 'authorization', 'rest', 'graphql', 'sdk',
            'integration', 'webhook', 'callback', 'json', 'xml'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in api_indicators if indicator in text_lower) >= 3

    def _is_user_documentation(self, text: str) -> bool:
        """Check if text appears to be user-facing documentation."""
        user_doc_indicators = [
            'user guide', 'user manual', 'help', 'documentation',
            'instructions', 'how to use', 'getting started', 'quick start',
            'user interface', 'end user', 'customer', 'client'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in user_doc_indicators if indicator in text_lower) >= 2

    # === COMMON EVIDENCE UTILITIES ===

    def _calculate_base_evidence_score(self, confidence_factors: Dict[str, float]) -> float:
        """
        Calculate a base evidence score from multiple confidence factors.
        
        Args:
            confidence_factors: Dict of factor_name -> score pairs
            
        Returns:
            Weighted average evidence score
        """
        if not confidence_factors:
            return 0.0
        
        # Default weights for common factors
        default_weights = {
            'linguistic': 0.3,
            'structural': 0.2, 
            'semantic': 0.25,
            'contextual': 0.15,
            'feedback': 0.1
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for factor, score in confidence_factors.items():
            weight = default_weights.get(factor, 0.1)  # Default weight for unknown factors
            total_score += score * weight
            total_weight += weight
        
        return max(0.0, min(1.0, total_score / total_weight if total_weight > 0 else 0.0))

    def _adjust_evidence_for_context(self, base_evidence: float, context: Dict[str, Any]) -> float:
        """
        Apply common context-based evidence adjustments.
        
        Args:
            base_evidence: Initial evidence score
            context: Document context information
            
        Returns:
            Adjusted evidence score
        """
        adjusted_evidence = base_evidence
        
        if not context:
            return adjusted_evidence
        
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type == 'technical':
            adjusted_evidence *= 0.9  # Technical content more permissive
        elif content_type == 'legal':
            adjusted_evidence *= 1.1  # Legal content stricter
        elif content_type == 'marketing':
            adjusted_evidence *= 0.8  # Marketing more flexible
        
        # Audience adjustments
        audience = context.get('audience', 'general')
        if audience in ['expert', 'developer']:
            adjusted_evidence *= 0.9  # Expert audience more permissive
        elif audience in ['beginner', 'general']:
            adjusted_evidence *= 1.05  # General audience needs clearer language
        
        # Block type adjustments
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['code_block', 'literal_block']:
            adjusted_evidence *= 0.1  # Code blocks very permissive
        elif block_type == 'heading':
            adjusted_evidence *= 1.1  # Headings should be clear
        
        return max(0.0, min(1.0, adjusted_evidence))

    def _has_technical_context_words(self, text: str, distance: int = 10) -> bool:
        """
        Check if text has technical context words nearby.
        
        Args:
            text: Text to analyze
            distance: Word distance to consider
            
        Returns:
            True if technical context detected
        """
        technical_words = {
            'api', 'sdk', 'json', 'xml', 'http', 'https', 'url', 'uri',
            'database', 'server', 'client', 'framework', 'library',
            'configuration', 'parameter', 'variable', 'function', 'method'
        }
        
        words = text.lower().split()
        return any(word in technical_words for word in words)

    # === ADDITIONAL CONTENT TYPE DETECTION ===

    def _is_specification_documentation(self, text: str) -> bool:
        """Check if text appears to be specification documentation."""
        spec_indicators = [
            'specification', 'spec', 'requirements', 'protocol', 'standard',
            'rfc', 'ieee', 'iso', 'format', 'schema', 'interface definition',
            'contract', 'agreement', 'compliance', 'conformance'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in spec_indicators if indicator in text_lower) >= 3

    def _is_technical_specification(self, text: str) -> bool:
        """Check if text appears to be technical specification."""
        tech_spec_indicators = [
            'technical specification', 'tech spec', 'design document',
            'architecture spec', 'system specification', 'api spec',
            'protocol specification', 'data format', 'file format'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in tech_spec_indicators if indicator in text_lower) >= 2

    def _is_reference_documentation(self, text: str) -> bool:
        """Check if text appears to be reference documentation."""
        reference_indicators = [
            'reference', 'manual', 'handbook', 'documentation',
            'command reference', 'function reference', 'class reference',
            'method reference', 'property reference', 'parameter reference'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in reference_indicators if indicator in text_lower) >= 3

    def _is_installation_documentation(self, text: str) -> bool:
        """Check if text appears to be installation documentation."""
        install_indicators = [
            'install', 'installation', 'setup', 'deploy', 'deployment',
            'configure', 'configuration', 'getting started', 'quick start',
            'prerequisites', 'requirements', 'dependencies'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in install_indicators if indicator in text_lower) >= 3

    def _is_policy_documentation(self, text: str) -> bool:
        """Check if text appears to be policy documentation."""
        policy_indicators = [
            'policy', 'policies', 'guidelines', 'standards', 'governance',
            'compliance', 'regulation', 'rule', 'procedure', 'protocol',
            'best practices', 'coding standards', 'style guide'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in policy_indicators if indicator in text_lower) >= 3

    def _is_troubleshooting_documentation(self, text: str) -> bool:
        """Check if text appears to be troubleshooting documentation."""
        troubleshoot_indicators = [
            'troubleshoot', 'troubleshooting', 'debug', 'debugging',
            'error', 'problem', 'issue', 'fix', 'solution', 'resolve',
            'common problems', 'known issues', 'faq', 'frequently asked'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in troubleshoot_indicators if indicator in text_lower) >= 3

    def _is_user_interface_documentation(self, text: str) -> bool:
        """Check if text appears to be user interface documentation."""
        ui_indicators = [
            'user interface', 'ui', 'gui', 'interface', 'screen', 'dialog',
            'window', 'menu', 'button', 'field', 'form', 'tab', 'panel'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in ui_indicators if indicator in text_lower) >= 3

    def _is_configuration_documentation(self, text: str) -> bool:
        """Check if text appears to be configuration documentation."""
        config_indicators = [
            'configuration', 'config', 'settings', 'options', 'preferences',
            'parameters', 'variables', 'environment', 'properties', 'ini',
            'yaml', 'json', 'xml', 'configure'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in config_indicators if indicator in text_lower) >= 3

    def _is_tutorial_content(self, text: str) -> bool:
        """Check if text appears to be tutorial content."""
        tutorial_indicators = [
            'tutorial', 'walkthrough', 'guide', 'lesson', 'chapter',
            'step by step', 'learn', 'example', 'demonstration', 'exercise'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in tutorial_indicators if indicator in text_lower) >= 2

    def _is_training_content(self, text: str) -> bool:
        """Check if text appears to be training content."""
        training_indicators = [
            'training', 'course', 'curriculum', 'syllabus', 'module',
            'lesson plan', 'workshop', 'seminar', 'certification', 'learning'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in training_indicators if indicator in text_lower) >= 2

    def _is_migration_documentation(self, text: str) -> bool:
        """Check if text appears to be migration documentation."""
        migration_indicators = [
            'migration', 'upgrade', 'transition', 'conversion', 'porting',
            'legacy', 'deprecated', 'new version', 'breaking changes'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in migration_indicators if indicator in text_lower) >= 2

    def _has_high_technical_density(self, text: str, threshold: float = 0.15) -> bool:
        """Check if text has high density of technical terms."""
        technical_terms = {
            'api', 'sdk', 'framework', 'library', 'database', 'server',
            'client', 'protocol', 'algorithm', 'function', 'method',
            'class', 'object', 'interface', 'implementation', 'configuration',
            'deployment', 'authentication', 'authorization', 'encryption'
        }
        
        words = text.lower().split()
        if not words:
            return False
        
        technical_word_count = sum(1 for word in words if word in technical_terms)
        density = technical_word_count / len(words)
        return density >= threshold

    # === COMMON MESSAGING UTILITIES ===

    def _get_contextual_message(self, violation_type: str, evidence_score: float, 
                               context: Dict[str, Any], **kwargs) -> str:
        """
        Generate contextual error message based on violation type and context.
        
        Args:
            violation_type: Type of violation detected
            evidence_score: Confidence score for the violation
            context: Document context information
            **kwargs: Additional context for specific violation types
            
        Returns:
            Contextual error message
        """
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        
        # Base message templates
        base_messages = {
            'high_confidence': f"Strong evidence suggests this {violation_type} should be addressed",
            'medium_confidence': f"Consider reviewing this {violation_type}",
            'low_confidence': f"Potential {violation_type} detected - please verify"
        }
        
        # Confidence level based on evidence score
        if evidence_score >= 0.7:
            confidence_level = 'high_confidence'
        elif evidence_score >= 0.4:
            confidence_level = 'medium_confidence'
        else:
            confidence_level = 'low_confidence'
        
        base_message = base_messages[confidence_level]
        
        # Add context-specific guidance
        if content_type == 'technical' and audience == 'developer':
            return f"{base_message} for technical accuracy and developer clarity."
        elif content_type == 'procedural':
            return f"{base_message} to ensure clear user instructions."
        elif content_type == 'legal':
            return f"{base_message} to maintain legal precision and clarity."
        else:
            return f"{base_message} for improved readability."

    def _generate_smart_suggestions(self, violation_type: str, original_text: str,
                                   context: Dict[str, Any], **kwargs) -> List[str]:
        """
        Generate smart suggestions based on violation type and context.
        
        Args:
            violation_type: Type of violation detected
            original_text: Original text with the violation
            context: Document context information
            **kwargs: Additional context for specific violation types
            
        Returns:
            List of contextual suggestions
        """
        content_type = context.get('content_type', 'general')
        suggestions = []
        
        # Context-aware suggestion generation
        if content_type == 'technical':
            suggestions.extend([
                "Consider technical documentation standards",
                "Ensure clarity for developer audience",
                "Maintain consistency with technical terminology"
            ])
        elif content_type == 'procedural':
            suggestions.extend([
                "Use clear, actionable language",
                "Ensure step-by-step clarity",
                "Consider user experience flow"
            ])
        elif content_type == 'legal':
            suggestions.extend([
                "Maintain legal precision",
                "Ensure compliance terminology",
                "Consider regulatory requirements"
            ])
        
        # Add violation-specific suggestions (to be overridden by specific rules)
        suggestions.append(f"Review {violation_type} for context appropriateness")
        
        return suggestions[:3]  # Return top 3 suggestions

    # === COMMON FEEDBACK PATTERN UTILITIES ===

    def _get_default_feedback_patterns(self) -> Dict[str, Any]:
        """
        Get default feedback patterns structure.
        
        Returns:
            Dict with standard feedback pattern structure
        """
        return {
            'accepted_terms': set(),
            'rejected_terms': set(),
            'context_patterns': {},
            'correction_success': {},
            'frequency_data': {},
            'domain_patterns': {}
        }

    def _get_cached_feedback_patterns(self, rule_type: str) -> Dict[str, Any]:
        """
        Get cached feedback patterns for a specific rule type.
        
        Args:
            rule_type: Type of rule requesting feedback patterns
            
        Returns:
            Cached feedback patterns or default structure
        """
        # This would typically load from cache/storage
        # For now, return default structure
        patterns = self._get_default_feedback_patterns()
        patterns['rule_type'] = rule_type
        return patterns
