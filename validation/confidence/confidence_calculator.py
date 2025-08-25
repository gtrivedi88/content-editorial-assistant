"""
ConfidenceCalculator Class
Unified confidence calculation engine that integrates all confidence components.
Provides weighted averaging, breakdown tracking, and comprehensive explanations.
"""

import time
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from .linguistic_anchors import LinguisticAnchors, AnchorAnalysis
from .context_analyzer import ContextAnalyzer, ContextAnalysis, ContentType, ContentTypeResult
from .domain_classifier import DomainClassifier, DomainAnalysis
from .rule_reliability import get_rule_reliability_coefficient


class ConfidenceLayer(Enum):
    """Enumeration of confidence layers."""
    LINGUISTIC_ANCHORS = "linguistic_anchors"
    CONTEXT_ANALYSIS = "context_analysis" 
    DOMAIN_CLASSIFICATION = "domain_classification"


@dataclass
class LayerContribution:
    """Represents a single layer's contribution to confidence."""
    
    layer: ConfidenceLayer
    raw_score: float              # Original score from the layer
    weighted_score: float         # Score after applying weight
    weight: float                 # Weight applied to this layer
    confidence: float             # Layer's confidence in its own analysis
    explanation: str              # Layer's explanation
    processing_time: float        # Time taken for this layer's analysis
    metadata: Dict[str, Any]      # Additional layer-specific data


@dataclass
class ConfidenceBreakdown:
    """Detailed breakdown of confidence calculation."""
    
    text: str                     # Original text analyzed
    error_position: int           # Character position of the error
    rule_type: Optional[str]      # Rule type context
    content_type: Optional[str]   # Content type context
    
    # Layer contributions
    layer_contributions: List[LayerContribution]
    
    # Final results
    final_confidence: float       # Final calculated confidence (0-1)
    confidence_effect: float      # Effect on original confidence (-1 to +1)
    confidence_adjustment: str    # Description of adjustment (boost/reduce/neutral)
    
    # Meta-analysis
    layer_agreement: float        # How much layers agree (0-1)
    confidence_certainty: float   # How certain we are about the final confidence (0-1)
    outlier_layers: List[str]     # Layers with significantly different scores
    
    # Performance data
    total_processing_time: float  # Total time for all analyses
    cache_performance: Dict[str, Any]  # Cache hit rates and performance
    
    # Comprehensive explanation
    explanation: str              # Human-readable explanation of the calculation


@dataclass
class ConfidenceWeights:
    """Configuration for layer weights."""
    
    linguistic_anchors: float = 0.40  # Pattern-based evidence weight
    context_analysis: float = 0.35    # Semantic and structural weight
    domain_classification: float = 0.25  # Content-type and domain weight
    
    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = self.linguistic_anchors + self.context_analysis + self.domain_classification
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def normalize(self) -> 'ConfidenceWeights':
        """Return normalized weights that sum to 1.0."""
        total = self.linguistic_anchors + self.context_analysis + self.domain_classification
        return ConfidenceWeights(
            linguistic_anchors=self.linguistic_anchors / total,
            context_analysis=self.context_analysis / total,
            domain_classification=self.domain_classification / total
        )


class ConfidenceCalculator:
    """
    Unified confidence calculation engine.
    
    Integrates LinguisticAnchors, ContextAnalyzer, and DomainClassifier
    to provide comprehensive confidence scoring with weighted averaging,
    detailed breakdowns, and rich explanations.
    """
    
    def __init__(self, 
                 weights: Optional[ConfidenceWeights] = None,
                 cache_results: bool = True,
                 enable_layer_caching: bool = True):
        """
        Initialize the ConfidenceCalculator.
        
        Args:
            weights: Layer weights for averaging (defaults to balanced weights)
            cache_results: Whether to cache final calculation results
            enable_layer_caching: Whether to enable caching in individual layers
        """
        self.weights = weights or ConfidenceWeights()
        self.cache_results = cache_results
        self.enable_layer_caching = enable_layer_caching
        
        # Initialize component analyzers
        self.linguistic_anchors = LinguisticAnchors(cache_compiled_patterns=enable_layer_caching)
        self.context_analyzer = ContextAnalyzer(cache_nlp_results=enable_layer_caching)
        self.domain_classifier = DomainClassifier(cache_classifications=enable_layer_caching)
        
        # Result cache
        self._calculation_cache: Dict[str, ConfidenceBreakdown] = {}
        
        # Performance tracking
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_calculations = 0
    
    def calculate_confidence(self, 
                           text: str, 
                           error_position: int,
                           rule_type: Optional[str] = None,
                           content_type: Optional[str] = None,
                           base_confidence: float = 0.5) -> ConfidenceBreakdown:
        """
        Calculate comprehensive confidence score.
        
        Args:
            text: The text containing the error
            error_position: Character position of the error
            rule_type: Type of rule being validated (e.g., 'grammar', 'style')
            content_type: Type of content (e.g., 'technical', 'narrative')
            base_confidence: Starting confidence level (0-1)
            
        Returns:
            Complete confidence breakdown with all layer analyses
        """
        start_time = time.time()
        self._total_calculations += 1
        
        # Check cache first
        cache_key = self._generate_cache_key(text, error_position, rule_type, content_type, base_confidence)
        if self.cache_results and cache_key in self._calculation_cache:
            self._cache_hits += 1
            return self._calculation_cache[cache_key]
        
        self._cache_misses += 1
        
        # Perform individual layer analyses
        layer_contributions = self._analyze_all_layers(text, error_position, rule_type, content_type)
        
        # Calculate weighted confidence
        final_confidence, confidence_effect = self._calculate_weighted_confidence(
            layer_contributions, base_confidence
        )
        
        # Analyze layer agreement and certainty
        layer_agreement = self._calculate_layer_agreement(layer_contributions)
        confidence_certainty = self._calculate_confidence_certainty(layer_contributions, layer_agreement)
        outlier_layers = self._identify_outlier_layers(layer_contributions)
        
        # Determine confidence adjustment description
        confidence_adjustment = self._describe_confidence_adjustment(confidence_effect)
        
        # Generate comprehensive explanation
        explanation = self._generate_comprehensive_explanation(
            layer_contributions, final_confidence, confidence_effect, 
            layer_agreement, confidence_certainty, outlier_layers
        )
        
        # Collect performance data
        total_processing_time = time.time() - start_time
        cache_performance = self._collect_cache_performance()
        
        # Create breakdown result
        breakdown = ConfidenceBreakdown(
            text=text,
            error_position=error_position,
            rule_type=rule_type,
            content_type=content_type,
            layer_contributions=layer_contributions,
            final_confidence=final_confidence,
            confidence_effect=confidence_effect,
            confidence_adjustment=confidence_adjustment,
            layer_agreement=layer_agreement,
            confidence_certainty=confidence_certainty,
            outlier_layers=outlier_layers,
            total_processing_time=total_processing_time,
            cache_performance=cache_performance,
            explanation=explanation
        )
        
        # Cache result
        if self.cache_results:
            self._calculation_cache[cache_key] = breakdown
        
        return breakdown
    
    def calculate_normalized_confidence(self, 
                                      text: str, 
                                      error_position: int,
                                      rule_type: str,
                                      content_type: Optional[str] = None,
                                       rule_reliability: Optional[float] = None,
                                       base_confidence: float = 0.5,
                                       evidence_score: Optional[float] = None,
                                       return_breakdown: bool = False) -> Union[float, Tuple[float, 'ConfidenceBreakdown']]:
        """
        Calculate normalized confidence that's comparable across all rules.
        
        This is the enhanced method that integrates content-type detection
        and rule reliability for consistent confidence scoring.
        
        Args:
            text: The text containing the error
            error_position: Character position of the error
            rule_type: Type of rule being validated (required for reliability)
            content_type: Type of content (auto-detected if not provided)
            rule_reliability: Rule reliability coefficient (auto-calculated if not provided)
            base_confidence: Starting confidence level (0-1)
            evidence_score: Optional rule-level evidence score (0-1) to blend into final confidence
            return_breakdown: If True, return tuple of (confidence, breakdown) with provenance
            
        Returns:
            If return_breakdown=False: Normalized confidence score in range [0.0, 1.0]
            If return_breakdown=True: Tuple of (confidence, ConfidenceBreakdown with provenance)
        """
        # Auto-detect content type if not provided
        if content_type is None:
            content_result = self.context_analyzer.detect_content_type(text)
            content_type = content_result.content_type.value
        
        # Auto-calculate rule reliability if not provided
        if rule_reliability is None:
            rule_reliability = get_rule_reliability_coefficient(rule_type)
        
        # Use existing calculate_confidence but add normalization layer
        confidence_breakdown = self.calculate_confidence(
            text=text,
            error_position=error_position, 
            rule_type=rule_type,
            content_type=content_type,
            base_confidence=base_confidence
        )
        
        # Apply rule reliability coefficient
        raw_confidence = confidence_breakdown.final_confidence
        normalized_confidence = raw_confidence * rule_reliability
        
        # Apply content-type modifier (enhance confidence based on content type)
        content_modifier = self._get_content_type_modifier(content_type, rule_type)
        normalized_confidence *= content_modifier
        
        # Initialize provenance tracking
        evidence_weight = 0.0
        model_weight = 1.0
        floor_guard_triggered = False
        
        # Blend in rule-provided evidence score when available
        # Dynamic weighting favors stronger evidence while maintaining stability
        if evidence_score is not None:
            try:
                evidence_score = max(0.0, min(1.0, float(evidence_score)))
                # Evidence weight scales with evidence strength: 0.2 → 0.7
                evidence_weight = max(0.2, min(0.7, 0.2 + 0.5 * evidence_score))
                model_weight = 1.0 - evidence_weight
                normalized_confidence = (normalized_confidence * model_weight) + (evidence_score * evidence_weight)
            except Exception:
                # Ignore evidence if it's malformed and proceed with normalized confidence
                pass
        
        # Confidence policy guard: ensure strong, reliable evidence isn't underrepresented
        if evidence_score is not None:
            try:
                if evidence_score >= 0.85 and rule_reliability >= 0.85:
                    original_confidence = normalized_confidence
                    normalized_confidence = max(normalized_confidence, 0.75)
                    floor_guard_triggered = (normalized_confidence > original_confidence)
            except Exception:
                pass

        # Ensure final range [0.0, 1.0]
        final_confidence = max(0.0, min(1.0, normalized_confidence))
        
        # Create provenance data for explainability
        provenance = {
            'evidence_weight': evidence_weight,
            'model_weight': model_weight,
            'rule_reliability': rule_reliability,
            'content_modifier': content_modifier,
            'floor_guard_triggered': floor_guard_triggered,
            'raw_confidence': raw_confidence,
            'evidence_score': evidence_score,
            'final_confidence': final_confidence
        }
        
        # Store provenance in the confidence breakdown
        confidence_breakdown.metadata = getattr(confidence_breakdown, 'metadata', {})
        confidence_breakdown.metadata['provenance'] = provenance
        
        # For backward compatibility, also store as a separate attribute
        confidence_breakdown.confidence_provenance = provenance
        
        # Return based on requested format
        if return_breakdown:
            return final_confidence, confidence_breakdown
        else:
            return final_confidence
    
    def _get_content_type_modifier(self, content_type: str, rule_type: str) -> float:
        """
        Get content-type modifier for rule-content combinations.
        
        This provides fine-tuned confidence adjustments based on the combination
        of content type and rule type, reflecting real-world accuracy patterns.
        
        Args:
            content_type: The content type (e.g., 'technical', 'narrative')
            rule_type: The rule type (e.g., 'grammar', 'commands')
            
        Returns:
            Modifier coefficient in range [0.7, 1.3]
        """
        # Content-rule modifier matrix based on empirical accuracy
        modifier_matrix = {
            # Technical content modifiers
            'technical': {
                'commands': 1.2,           # Commands very accurate in technical content
                'programming_elements': 1.2, # Programming elements very accurate
                'terminology': 1.1,        # Terminology rules work well
                'grammar': 0.9,           # Grammar less reliable in technical docs
                'tone': 0.8,              # Tone less relevant in technical content
                'narrative': 0.7,         # Narrative patterns don't apply
                'default': 1.0
            },
            # Procedural content modifiers
            'procedural': {
                'procedures': 1.2,        # Procedure rules very accurate
                'lists': 1.1,            # List formatting important
                'headings': 1.1,          # Structure important
                'grammar': 1.0,           # Grammar accuracy normal
                'tone': 0.9,              # Tone somewhat relevant
                'default': 1.0
            },
            # Narrative content modifiers
            'narrative': {
                'tone': 1.2,              # Tone very important in narrative
                'grammar': 1.1,           # Grammar accuracy higher
                'inclusive_language': 1.1, # Inclusive language important
                'commands': 0.8,          # Commands less relevant
                'programming_elements': 0.7, # Programming not relevant
                'default': 1.0
            },
            # Legal content modifiers
            'legal': {
                'claims': 1.3,            # Claims detection very accurate
                'personal_information': 1.2, # Personal info very important
                'grammar': 1.1,           # Grammar very important
                'tone': 1.1,              # Formal tone important
                'commands': 0.8,          # Commands less relevant
                'default': 1.0
            },
            # Marketing content modifiers
            'marketing': {
                'tone': 1.2,              # Tone very important
                'claims': 1.1,            # Claims oversight important
                'inclusive_language': 1.1, # Inclusive language important
                'grammar': 1.0,           # Grammar normal importance
                'commands': 0.8,          # Commands less relevant
                'default': 1.0
            },
            # General content (fallback)
            'general': {
                'default': 1.0            # No specific modifiers
            }
        }
        
        content_modifiers = modifier_matrix.get(content_type, modifier_matrix['general'])
        modifier = content_modifiers.get(rule_type, content_modifiers.get('default', 1.0))
        
        # Ensure modifier is in reasonable range
        return max(0.7, min(1.3, modifier))
    
    def _analyze_all_layers(self, text: str, error_position: int, 
                          rule_type: Optional[str], content_type: Optional[str]) -> List[LayerContribution]:
        """Perform analysis on all confidence layers."""
        contributions = []
        
        # Linguistic Anchors Analysis
        start_time = time.time()
        anchor_analysis = self.linguistic_anchors.analyze_text(
            text, error_position, rule_type, content_type
        )
        anchor_time = time.time() - start_time
        
        anchor_contribution = LayerContribution(
            layer=ConfidenceLayer.LINGUISTIC_ANCHORS,
            raw_score=anchor_analysis.net_effect,
            weighted_score=anchor_analysis.net_effect * self.weights.linguistic_anchors,
            weight=self.weights.linguistic_anchors,
            confidence=self._calculate_anchor_confidence(anchor_analysis),
            explanation=anchor_analysis.explanation,
            processing_time=anchor_time,
            metadata={
                'total_matches': len(anchor_analysis.matches),
                'boosting_matches': len(anchor_analysis.boosting_matches),
                'reducing_matches': len(anchor_analysis.reducing_matches),
                'total_boost': anchor_analysis.total_boost,
                'total_reduction': anchor_analysis.total_reduction
            }
        )
        contributions.append(anchor_contribution)
        
        # Context Analysis
        start_time = time.time()
        context_analysis = self.context_analyzer.analyze_context(text, error_position)
        context_time = time.time() - start_time
        
        context_contribution = LayerContribution(
            layer=ConfidenceLayer.CONTEXT_ANALYSIS,
            raw_score=context_analysis.net_context_effect,
            weighted_score=context_analysis.net_context_effect * self.weights.context_analysis,
            weight=self.weights.context_analysis,
            confidence=self._calculate_context_confidence(context_analysis),
            explanation=context_analysis.explanation,
            processing_time=context_time,
            metadata={
                'sentence_count': len(context_analysis.sentence_structures),
                'coreference_count': len(context_analysis.coreference_matches),
                'structural_confidence': context_analysis.structural_confidence,
                'coreference_confidence': context_analysis.coreference_confidence,
                'coherence_confidence': context_analysis.coherence_confidence,
                'discourse_confidence': context_analysis.discourse_confidence
            }
        )
        contributions.append(context_contribution)
        
        # Domain Classification
        start_time = time.time()
        domain_analysis = self.domain_classifier.classify_content(text)
        domain_time = time.time() - start_time
        
        # Calculate domain total effect
        domain_total_effect = (
            domain_analysis.domain_confidence_modifier +
            domain_analysis.content_type_modifier +
            domain_analysis.formality_modifier
        )
        
        domain_contribution = LayerContribution(
            layer=ConfidenceLayer.DOMAIN_CLASSIFICATION,
            raw_score=domain_total_effect,
            weighted_score=domain_total_effect * self.weights.domain_classification,
            weight=self.weights.domain_classification,
            confidence=domain_analysis.classification_confidence,
            explanation=domain_analysis.explanation,
            processing_time=domain_time,
            metadata={
                'content_type': domain_analysis.content_type.content_type,
                'content_type_confidence': domain_analysis.content_type.confidence,
                'primary_domain': domain_analysis.domain_identification.primary_domain,
                'domain_confidence': domain_analysis.domain_identification.confidence,
                'formality_level': domain_analysis.formality_assessment.formality_level,
                'formality_score': domain_analysis.formality_assessment.formality_score,
                'mixed_content_detected': domain_analysis.mixed_content_detected
            }
        )
        contributions.append(domain_contribution)
        
        return contributions
    
    def _calculate_anchor_confidence(self, analysis: AnchorAnalysis) -> float:
        """Calculate confidence in the anchor analysis itself."""
        if not analysis.matches:
            return 0.3  # Low confidence when no patterns match
        
        # Factor in the number and strength of matches
        match_strength = min(len(analysis.matches) / 10.0, 1.0)  # Normalize to 10 matches
        effect_magnitude = min(abs(analysis.net_effect) * 2, 1.0)  # Stronger effects = higher confidence
        
        return min(0.5 + (match_strength * 0.3) + (effect_magnitude * 0.2), 1.0)
    
    def _calculate_context_confidence(self, analysis: ContextAnalysis) -> float:
        """Calculate confidence in the context analysis itself."""
        # Base confidence from processing success
        base_confidence = 0.6
        
        # Adjust based on sentence structure quality
        if len(analysis.sentence_structures) > 0:
            avg_complexity = sum(s.complexity_score for s in analysis.sentence_structures) / len(analysis.sentence_structures)
            # Moderate complexity indicates good analysis confidence
            if 0.3 <= avg_complexity <= 0.7:
                base_confidence += 0.2
        
        # Adjust based on coreference clarity
        if analysis.coreference_matches:
            avg_coreference_conf = sum(m.confidence for m in analysis.coreference_matches) / len(analysis.coreference_matches)
            base_confidence += avg_coreference_conf * 0.2
        
        return min(base_confidence, 1.0)
    
    def _calculate_weighted_confidence(self, contributions: List[LayerContribution], 
                                     base_confidence: float) -> Tuple[float, float]:
        """Calculate final weighted confidence and effect."""
        # Calculate total weighted effect
        total_weighted_effect = sum(contrib.weighted_score for contrib in contributions)
        
        # Apply effect to base confidence
        final_confidence = base_confidence + total_weighted_effect
        
        # Clamp to valid range [0, 1]
        final_confidence = max(0.0, min(1.0, final_confidence))
        
        # Calculate the net effect
        confidence_effect = final_confidence - base_confidence
        
        return final_confidence, confidence_effect
    
    def _calculate_layer_agreement(self, contributions: List[LayerContribution]) -> float:
        """Calculate how much the layers agree with each other."""
        if len(contributions) < 2:
            return 1.0
        
        # Get raw scores
        scores = [contrib.raw_score for contrib in contributions]
        
        # Calculate variance
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        # Convert variance to agreement (lower variance = higher agreement)
        # Normalize by typical confidence effect range
        normalized_variance = min(variance / 0.1, 1.0)  # 0.1 is typical range
        agreement = 1.0 - normalized_variance
        
        return max(0.0, agreement)
    
    def _calculate_confidence_certainty(self, contributions: List[LayerContribution], 
                                      layer_agreement: float) -> float:
        """Calculate how certain we are about the final confidence."""
        # Start with layer agreement
        certainty = layer_agreement * 0.4
        
        # Add individual layer confidences
        avg_layer_confidence = sum(contrib.confidence for contrib in contributions) / len(contributions)
        certainty += avg_layer_confidence * 0.4
        
        # Add effect magnitude (stronger effects = higher certainty)
        total_effect_magnitude = sum(abs(contrib.raw_score) for contrib in contributions)
        effect_certainty = min(total_effect_magnitude * 2, 1.0)  # Normalize
        certainty += effect_certainty * 0.2
        
        return min(certainty, 1.0)
    
    def _identify_outlier_layers(self, contributions: List[LayerContribution]) -> List[str]:
        """Identify layers with significantly different scores."""
        if len(contributions) < 2:
            return []
        
        scores = [contrib.raw_score for contrib in contributions]
        mean_score = sum(scores) / len(scores)
        std_dev = (sum((score - mean_score) ** 2 for score in scores) / len(scores)) ** 0.5
        
        outliers = []
        threshold = 2 * std_dev  # 2 standard deviations
        
        for contrib in contributions:
            if abs(contrib.raw_score - mean_score) > threshold and std_dev > 0.05:  # Only if significant deviation
                outliers.append(contrib.layer.value)
        
        return outliers
    
    def _describe_confidence_adjustment(self, confidence_effect: float) -> str:
        """Describe the type of confidence adjustment."""
        if confidence_effect > 0.05:
            return "boost"
        elif confidence_effect < -0.05:
            return "reduce"
        else:
            return "neutral"
    
    def _generate_comprehensive_explanation(self, contributions: List[LayerContribution],
                                          final_confidence: float, confidence_effect: float,
                                          layer_agreement: float, confidence_certainty: float,
                                          outlier_layers: List[str]) -> str:
        """Generate comprehensive explanation of confidence calculation."""
        parts = []
        
        # Overall result
        if confidence_effect > 0.05:
            parts.append(f"🔼 Comprehensive analysis increased confidence by {confidence_effect:+.3f}")
        elif confidence_effect < -0.05:
            parts.append(f"🔽 Comprehensive analysis decreased confidence by {confidence_effect:+.3f}")
        else:
            parts.append(f"➡️ Comprehensive analysis had minimal effect ({confidence_effect:+.3f})")
        
        parts.append(f"   Final confidence: {final_confidence:.3f}")
        
        # Layer breakdown
        parts.append(f"\n📊 LAYER CONTRIBUTIONS:")
        for contrib in contributions:
            layer_name = contrib.layer.value.replace('_', ' ').title()
            parts.append(f"   {layer_name}: {contrib.raw_score:+.3f} "
                        f"(weight: {contrib.weight:.0%}, "
                        f"weighted: {contrib.weighted_score:+.3f})")
        
        # Meta-analysis
        parts.append(f"\n🔍 ANALYSIS QUALITY:")
        parts.append(f"   Layer agreement: {layer_agreement:.2f}")
        parts.append(f"   Confidence certainty: {confidence_certainty:.2f}")
        
        if outlier_layers:
            outlier_names = [name.replace('_', ' ').title() for name in outlier_layers]
            parts.append(f"   ⚠️ Outlier layers: {', '.join(outlier_names)}")
        
        # Performance summary
        total_time = sum(contrib.processing_time for contrib in contributions) * 1000
        parts.append(f"\n⚡ PERFORMANCE:")
        parts.append(f"   Total processing: {total_time:.1f}ms")
        
        for contrib in contributions:
            layer_name = contrib.layer.value.replace('_', ' ').title()
            parts.append(f"   {layer_name}: {contrib.processing_time*1000:.1f}ms")
        
        # Individual layer insights
        parts.append(f"\n💡 KEY INSIGHTS:")
        for contrib in contributions:
            layer_name = contrib.layer.value.replace('_', ' ').title()
            
            if contrib.layer == ConfidenceLayer.LINGUISTIC_ANCHORS:
                match_count = contrib.metadata['total_matches']
                if match_count > 0:
                    parts.append(f"   {layer_name}: {match_count} pattern matches found")
            
            elif contrib.layer == ConfidenceLayer.CONTEXT_ANALYSIS:
                sentence_count = contrib.metadata['sentence_count']
                coreference_count = contrib.metadata['coreference_count']
                parts.append(f"   {layer_name}: {sentence_count} sentences, {coreference_count} coreferences")
            
            elif contrib.layer == ConfidenceLayer.DOMAIN_CLASSIFICATION:
                content_type = contrib.metadata['content_type']
                domain = contrib.metadata['primary_domain']
                formality = contrib.metadata['formality_level']
                parts.append(f"   {layer_name}: {content_type.title()}, {domain.replace('_', ' ').title()}, {formality.title()}")
        
        return '\n'.join(parts)
    
    def _collect_cache_performance(self) -> Dict[str, Any]:
        """Collect cache performance data from all layers."""
        anchor_stats = self.linguistic_anchors.get_performance_stats()
        context_stats = self.context_analyzer.get_performance_stats()
        domain_stats = self.domain_classifier.get_performance_stats()
        
        return {
            'calculator_cache_hit_rate': self._cache_hits / max(1, self._cache_hits + self._cache_misses),
            'total_calculations': self._total_calculations,
            'layer_cache_performance': {
                'linguistic_anchors': {
                    'hit_rate': anchor_stats['cache_hit_rate'],
                    'cached_results': anchor_stats['analysis_results_cached']
                },
                'context_analysis': {
                    'hit_rate': context_stats['cache_hit_rate'],
                    'cached_results': context_stats['analysis_results_cached']
                },
                'domain_classification': {
                    'hit_rate': domain_stats['cache_hit_rate'],
                    'cached_results': domain_stats['classifications_cached']
                }
            }
        }
    
    def _generate_cache_key(self, text: str, error_position: int, 
                          rule_type: Optional[str], content_type: Optional[str], 
                          base_confidence: float) -> str:
        """Generate cache key for calculation results."""
        return f"{hash(text)}:{error_position}:{rule_type}:{content_type}:{base_confidence}"
    
    def update_weights(self, weights: ConfidenceWeights) -> None:
        """Update the layer weights."""
        self.weights = weights.normalize()
    
    def get_layer_weights(self) -> ConfidenceWeights:
        """Get current layer weights."""
        return self.weights
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        base_stats = {
            'total_calculations': self._total_calculations,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / max(1, self._cache_hits + self._cache_misses),
            'cached_calculations': len(self._calculation_cache),
            'current_weights': {
                'linguistic_anchors': self.weights.linguistic_anchors,
                'context_analysis': self.weights.context_analysis,
                'domain_classification': self.weights.domain_classification
            }
        }
        
        # Add layer performance
        base_stats.update(self._collect_cache_performance())
        
        return base_stats
    
    def clear_caches(self) -> None:
        """Clear all caches (calculator and layer caches)."""
        self._calculation_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_calculations = 0
        
        # Clear individual layer caches
        self.linguistic_anchors.clear_caches()
        self.context_analyzer.clear_caches()
        self.domain_classifier.clear_cache()
    
    def analyze_confidence_factors(self, text: str, error_position: int,
                                 rule_type: Optional[str] = None,
                                 content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze what factors are influencing confidence for debugging/tuning.
        
        Returns detailed factor analysis without changing caches.
        """
        # Temporarily disable caching for analysis
        original_cache_setting = self.cache_results
        self.cache_results = False
        
        try:
            breakdown = self.calculate_confidence(text, error_position, rule_type, content_type)
            
            factor_analysis = {
                'strongest_positive_factor': None,
                'strongest_negative_factor': None,
                'most_confident_layer': None,
                'least_confident_layer': None,
                'agreement_analysis': {
                    'agreement_score': breakdown.layer_agreement,
                    'outliers': breakdown.outlier_layers,
                    'consensus': breakdown.layer_agreement > 0.7
                },
                'layer_details': {}
            }
            
            # Analyze strongest factors
            positive_contributions = [c for c in breakdown.layer_contributions if c.raw_score > 0]
            negative_contributions = [c for c in breakdown.layer_contributions if c.raw_score < 0]
            
            if positive_contributions:
                strongest_positive = max(positive_contributions, key=lambda x: x.raw_score)
                factor_analysis['strongest_positive_factor'] = {
                    'layer': strongest_positive.layer.value,
                    'score': strongest_positive.raw_score,
                    'confidence': strongest_positive.confidence
                }
            
            if negative_contributions:
                strongest_negative = min(negative_contributions, key=lambda x: x.raw_score)
                factor_analysis['strongest_negative_factor'] = {
                    'layer': strongest_negative.layer.value,
                    'score': strongest_negative.raw_score,
                    'confidence': strongest_negative.confidence
                }
            
            # Analyze layer confidence
            most_confident = max(breakdown.layer_contributions, key=lambda x: x.confidence)
            least_confident = min(breakdown.layer_contributions, key=lambda x: x.confidence)
            
            factor_analysis['most_confident_layer'] = {
                'layer': most_confident.layer.value,
                'confidence': most_confident.confidence,
                'score': most_confident.raw_score
            }
            
            factor_analysis['least_confident_layer'] = {
                'layer': least_confident.layer.value,
                'confidence': least_confident.confidence,
                'score': least_confident.raw_score
            }
            
            # Layer details
            for contrib in breakdown.layer_contributions:
                factor_analysis['layer_details'][contrib.layer.value] = {
                    'raw_score': contrib.raw_score,
                    'weighted_score': contrib.weighted_score,
                    'confidence': contrib.confidence,
                    'weight': contrib.weight,
                    'metadata': contrib.metadata
                }
            
            return factor_analysis
            
        finally:
            self.cache_results = original_cache_setting
    
    def simulate_weight_changes(self, text: str, error_position: int,
                              weight_scenarios: List[ConfidenceWeights],
                              rule_type: Optional[str] = None,
                              content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate how different weight configurations affect confidence.
        
        Useful for tuning and understanding weight sensitivity.
        """
        original_weights = self.weights
        original_cache_setting = self.cache_results
        self.cache_results = False  # Disable caching for simulation
        
        try:
            results = {
                'baseline': None,
                'scenarios': [],
                'weight_sensitivity': {}
            }
            
            # Baseline with current weights
            baseline = self.calculate_confidence(text, error_position, rule_type, content_type)
            results['baseline'] = {
                'weights': {
                    'linguistic_anchors': original_weights.linguistic_anchors,
                    'context_analysis': original_weights.context_analysis,
                    'domain_classification': original_weights.domain_classification
                },
                'final_confidence': baseline.final_confidence,
                'confidence_effect': baseline.confidence_effect
            }
            
            # Test each scenario
            for i, scenario_weights in enumerate(weight_scenarios):
                self.weights = scenario_weights.normalize()
                scenario_result = self.calculate_confidence(text, error_position, rule_type, content_type)
                
                results['scenarios'].append({
                    'scenario_id': i,
                    'weights': {
                        'linguistic_anchors': self.weights.linguistic_anchors,
                        'context_analysis': self.weights.context_analysis,
                        'domain_classification': self.weights.domain_classification
                    },
                    'final_confidence': scenario_result.final_confidence,
                    'confidence_effect': scenario_result.confidence_effect,
                    'difference_from_baseline': scenario_result.confidence_effect - baseline.confidence_effect
                })
            
            # Calculate weight sensitivity
            for layer in ['linguistic_anchors', 'context_analysis', 'domain_classification']:
                layer_effects = []
                for scenario in results['scenarios']:
                    weight_value = scenario['weights'][layer]
                    effect_value = scenario['confidence_effect']
                    layer_effects.append((weight_value, effect_value))
                
                # Simple sensitivity: range of effects across weight changes
                if layer_effects:
                    effect_values = [effect for _, effect in layer_effects]
                    sensitivity = max(effect_values) - min(effect_values)
                    results['weight_sensitivity'][layer] = sensitivity
            
            return results
            
        finally:
            self.weights = original_weights
            self.cache_results = original_cache_setting