"""
LinguisticAnchors Class
Runtime component for linguistic pattern detection and confidence adjustment.
Uses LinguisticAnchorsConfig to apply patterns and calculate confidence effects.
"""

import re
import time
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path

from ..config.linguistic_anchors_config import LinguisticAnchorsConfig


@dataclass
class AnchorMatch:
    """Represents a matched linguistic anchor pattern."""
    
    anchor_type: str  # 'boosting' or 'reducing'
    category: str     # e.g., 'generic_patterns', 'technical_patterns'
    anchor_name: str  # e.g., 'determiners', 'programming_terms'
    pattern: str      # The regex pattern that matched
    match_text: str   # The actual text that matched
    match_start: int  # Start position of match in context
    match_end: int    # End position of match in context
    confidence_effect: float  # The confidence adjustment value
    distance_from_error: int  # Distance in words from error position
    weighted_effect: float    # Effect after distance and rule weighting
    description: str  # Human-readable description of the anchor


@dataclass
class AnchorAnalysis:
    """Complete analysis result from linguistic anchors."""
    
    text: str                    # Original text analyzed
    error_position: int          # Character position of the error
    error_word_index: int        # Word index of the error
    context_text: str            # Extracted context around error
    context_start: int           # Start position of context in original text
    context_end: int             # End position of context in original text
    
    matches: List[AnchorMatch]   # All pattern matches found
    boosting_matches: List[AnchorMatch]   # Confidence-boosting matches
    reducing_matches: List[AnchorMatch]   # Confidence-reducing matches
    
    total_boost: float           # Total confidence boost applied
    total_reduction: float       # Total confidence reduction applied
    net_effect: float            # Final net confidence effect
    
    rule_type: Optional[str]     # Rule type for specialized weighting
    content_type: Optional[str]  # Content type for specialized adjustments
    
    explanation: str             # Human-readable explanation
    performance_stats: Dict[str, Any]  # Performance metrics


class LinguisticAnchors:
    """
    Runtime component for linguistic pattern detection and confidence adjustment.
    
    Uses the LinguisticAnchorsConfig to load patterns and apply them to text
    for calculating confidence adjustments in error detection.
    """
    
    def __init__(self, config_file: Optional[Path] = None, cache_compiled_patterns: bool = True):
        """
        Initialize the LinguisticAnchors analyzer.
        
        Args:
            config_file: Optional path to linguistic anchors configuration file
            cache_compiled_patterns: Whether to cache compiled regex patterns
        """
        self.config = LinguisticAnchorsConfig(config_file)
        self.cache_compiled_patterns = cache_compiled_patterns
        self._pattern_cache: Dict[str, List[re.Pattern]] = {}
        self._analysis_cache: Dict[str, AnchorAnalysis] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Load initial configuration
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load and cache configuration data."""
        # Load the configuration to ensure it's valid
        self.config.load_config()
        
        # Pre-compile frequently used patterns if caching is enabled
        if self.cache_compiled_patterns:
            self._precompile_patterns()
    
    def _precompile_patterns(self) -> None:
        """Pre-compile all regex patterns for better performance."""
        start_time = time.time()
        pattern_count = 0
        
        # Compile boosting anchor patterns
        boosting_anchors = self.config.get_boosting_anchors()
        for category_name, category in boosting_anchors.items():
            for anchor_name, anchor_config in category.items():
                cache_key = f"boosting:{category_name}:{anchor_name}"
                patterns = self.config.get_compiled_patterns('boosting', category_name, anchor_name)
                self._pattern_cache[cache_key] = patterns
                pattern_count += len(patterns)
        
        # Compile reducing anchor patterns
        reducing_anchors = self.config.get_reducing_anchors()
        for category_name, category in reducing_anchors.items():
            for anchor_name, anchor_config in category.items():
                cache_key = f"reducing:{category_name}:{anchor_name}"
                patterns = self.config.get_compiled_patterns('reducing', category_name, anchor_name)
                self._pattern_cache[cache_key] = patterns
                pattern_count += len(patterns)
        
        compilation_time = time.time() - start_time
        print(f"✓ Pre-compiled {pattern_count} regex patterns in {compilation_time:.3f}s")
    
    def analyze_text(self, text: str, error_position: int, 
                    rule_type: Optional[str] = None, 
                    content_type: Optional[str] = None,
                    max_context_window: Optional[int] = None) -> AnchorAnalysis:
        """
        Analyze text for linguistic anchors and calculate confidence effects.
        
        Args:
            text: The full text containing the error
            error_position: Character position of the error in the text
            rule_type: Type of rule for specialized weighting (e.g., 'grammar', 'pronouns')
            content_type: Type of content for specialized adjustments (e.g., 'technical', 'narrative')
            max_context_window: Maximum context window size (overrides config)
            
        Returns:
            Complete anchor analysis with confidence effects and explanations
        """
        start_time = time.time()
        
        # Create cache key for repeated analyses
        cache_key = f"{hash(text)}:{error_position}:{rule_type}:{content_type}"
        if cache_key in self._analysis_cache:
            self._cache_hits += 1
            return self._analysis_cache[cache_key]
        
        self._cache_misses += 1
        
        # Extract context around the error
        context_info = self._extract_context(text, error_position, max_context_window)
        
        # Find all pattern matches in the context
        matches = self._find_pattern_matches(
            context_info['context_text'], 
            context_info['error_word_index'],
            rule_type, 
            content_type
        )
        
        # Calculate confidence effects
        effects = self._calculate_confidence_effects(matches)
        
        # Generate explanation
        explanation = self._generate_explanation(matches, effects, rule_type, content_type)
        
        # Separate matches by type
        boosting_matches = [m for m in matches if m.anchor_type == 'boosting']
        reducing_matches = [m for m in matches if m.anchor_type == 'reducing']
        
        # Create performance stats
        analysis_time = time.time() - start_time
        performance_stats = {
            'analysis_time_ms': analysis_time * 1000,
            'total_patterns_checked': self._count_patterns_checked(),
            'matches_found': len(matches),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses
        }
        
        # Create analysis result
        analysis = AnchorAnalysis(
            text=text,
            error_position=error_position,
            error_word_index=context_info['error_word_index'],
            context_text=context_info['context_text'],
            context_start=context_info['context_start'],
            context_end=context_info['context_end'],
            matches=matches,
            boosting_matches=boosting_matches,
            reducing_matches=reducing_matches,
            total_boost=effects['total_boost'],
            total_reduction=effects['total_reduction'],
            net_effect=effects['net_effect'],
            rule_type=rule_type,
            content_type=content_type,
            explanation=explanation,
            performance_stats=performance_stats
        )
        
        # Cache the result
        self._analysis_cache[cache_key] = analysis
        
        return analysis
    
    def _extract_context(self, text: str, error_position: int, 
                        max_context_window: Optional[int] = None) -> Dict[str, Any]:
        """Extract context around the error position."""
        words = text.split()
        
        # Find word index for error position
        error_word_index = self._find_word_index(text, error_position)
        if error_word_index == -1:
            error_word_index = 0  # Default to first word if position not found
        
        # Get context window size
        if max_context_window is None:
            pattern_settings = self.config.get_pattern_matching_settings()
            max_context_window = pattern_settings.get('max_context_window', 15)
        
        # Calculate context bounds
        context_window = min(max_context_window, len(words) // 2)  # Don't exceed half the text
        start_index = max(0, error_word_index - context_window)
        end_index = min(len(words), error_word_index + context_window + 1)
        
        # Extract context
        context_words = words[start_index:end_index]
        context_text = ' '.join(context_words)
        
        # Calculate context positions in original text
        context_start = self._find_position_of_word_index(text, start_index)
        context_end = self._find_position_of_word_index(text, end_index - 1) + len(words[end_index - 1]) if end_index > 0 else len(text)
        
        # Adjust error word index relative to context
        relative_error_index = error_word_index - start_index
        
        return {
            'context_text': context_text,
            'context_start': context_start,
            'context_end': context_end,
            'error_word_index': relative_error_index,
            'total_words': len(words),
            'context_window_used': context_window
        }
    
    def _find_word_index(self, text: str, char_position: int) -> int:
        """Find the word index for a character position."""
        words = text.split()
        current_position = 0
        
        for i, word in enumerate(words):
            word_start = current_position
            word_end = current_position + len(word)
            
            if word_start <= char_position <= word_end:
                return i
            
            current_position = word_end + 1  # +1 for space
        
        return -1
    
    def _find_position_of_word_index(self, text: str, word_index: int) -> int:
        """Find the character position of a word index."""
        if word_index <= 0:
            return 0
        
        words = text.split()
        if word_index >= len(words):
            return len(text)
        
        # Calculate position by summing word lengths and spaces
        position = 0
        for i in range(word_index):
            position += len(words[i]) + 1  # +1 for space
        
        return position
    
    def _find_pattern_matches(self, context_text: str, error_word_index: int,
                             rule_type: Optional[str] = None, 
                             content_type: Optional[str] = None) -> List[AnchorMatch]:
        """Find all pattern matches in the context text."""
        matches = []
        
        # Process boosting anchors
        boosting_anchors = self.config.get_boosting_anchors()
        for category_name, category in boosting_anchors.items():
            for anchor_name, anchor_config in category.items():
                anchor_matches = self._find_anchor_matches(
                    'boosting', category_name, anchor_name, anchor_config,
                    context_text, error_word_index, rule_type, content_type
                )
                matches.extend(anchor_matches)
        
        # Process reducing anchors
        reducing_anchors = self.config.get_reducing_anchors()
        for category_name, category in reducing_anchors.items():
            for anchor_name, anchor_config in category.items():
                anchor_matches = self._find_anchor_matches(
                    'reducing', category_name, anchor_name, anchor_config,
                    context_text, error_word_index, rule_type, content_type
                )
                matches.extend(anchor_matches)
        
        return matches
    
    def _find_anchor_matches(self, anchor_type: str, category_name: str, anchor_name: str,
                            anchor_config: Dict[str, Any], context_text: str, 
                            error_word_index: int, rule_type: Optional[str] = None,
                            content_type: Optional[str] = None) -> List[AnchorMatch]:
        """Find matches for a specific anchor."""
        matches = []
        
        # Get compiled patterns
        cache_key = f"{anchor_type}:{category_name}:{anchor_name}"
        if cache_key in self._pattern_cache:
            compiled_patterns = self._pattern_cache[cache_key]
        else:
            compiled_patterns = self.config.get_compiled_patterns(anchor_type, category_name, anchor_name)
        
        # Get anchor configuration
        context_window = anchor_config.get('context_window', 3)
        base_effect = anchor_config.get('confidence_boost' if anchor_type == 'boosting' else 'confidence_reduction', 0.0)
        description = anchor_config.get('description', f'{anchor_name} pattern')
        
        # Check context window constraint
        if context_window == 0:
            # Special case: pattern must match at exact error position
            error_char_pos = self._word_index_to_char_position(context_text, error_word_index)
            search_start = max(0, error_char_pos - 10)  # Small buffer around error
            search_end = min(len(context_text), error_char_pos + 10)
            search_text = context_text[search_start:search_end]
        else:
            # Normal case: search within context window
            search_text = context_text
            search_start = 0
        
        # Find pattern matches
        for pattern in compiled_patterns:
            for match in pattern.finditer(search_text):
                match_start = search_start + match.start()
                match_end = search_start + match.end()
                match_text = match.group()
                
                # Calculate distance from error position
                match_word_index = self._char_position_to_word_index(context_text, match_start)
                distance = abs(match_word_index - error_word_index)
                
                # Check if match is within context window
                if context_window > 0 and distance > context_window:
                    continue
                
                # Calculate weighted effect
                weighted_effect = self._calculate_weighted_effect(
                    base_effect, distance, rule_type, content_type, 
                    category_name, anchor_type
                )
                
                # Create match object
                anchor_match = AnchorMatch(
                    anchor_type=anchor_type,
                    category=category_name,
                    anchor_name=anchor_name,
                    pattern=pattern.pattern,
                    match_text=match_text,
                    match_start=match_start,
                    match_end=match_end,
                    confidence_effect=base_effect,
                    distance_from_error=distance,
                    weighted_effect=weighted_effect,
                    description=description
                )
                
                matches.append(anchor_match)
        
        return matches
    
    def _word_index_to_char_position(self, text: str, word_index: int) -> int:
        """Convert word index to approximate character position."""
        words = text.split()
        if word_index >= len(words):
            return len(text)
        
        position = 0
        for i in range(word_index):
            position += len(words[i]) + 1  # +1 for space
        
        return position
    
    def _char_position_to_word_index(self, text: str, char_position: int) -> int:
        """Convert character position to word index."""
        words = text.split()
        current_position = 0
        
        for i, word in enumerate(words):
            word_start = current_position
            word_end = current_position + len(word)
            
            if word_start <= char_position <= word_end:
                return i
            
            current_position = word_end + 1  # +1 for space
        
        return len(words) - 1  # Default to last word
    
    def _calculate_weighted_effect(self, base_effect: float, distance: int,
                                  rule_type: Optional[str], content_type: Optional[str],
                                  category_name: str, anchor_type: str) -> float:
        """Calculate weighted effect considering distance, rule type, and content type."""
        effect = base_effect
        
        # Apply distance weighting
        pattern_settings = self.config.get_pattern_matching_settings()
        if pattern_settings.get('distance_weighting', {}).get('enabled', True):
            max_distance = pattern_settings.get('distance_weighting', {}).get('max_distance', 10)
            decay_factor = pattern_settings.get('distance_weighting', {}).get('distance_decay_factor', 0.9)
            min_effect = pattern_settings.get('distance_weighting', {}).get('min_distance_effect', 0.3)
            
            if distance <= max_distance:
                distance_multiplier = max(decay_factor ** distance, min_effect)
                effect *= distance_multiplier
        
        # Apply rule-specific weighting
        if rule_type:
            rule_weights = self.config.get_rule_specific_weights(rule_type)
            weight_key = f"{category_name}_weight"
            if weight_key in rule_weights:
                effect *= rule_weights[weight_key]
        
        # Apply content-type adjustments
        if content_type:
            adjustments = self.config.get_content_type_adjustments(content_type)
            adjustment_key = f"{category_name}_multiplier"
            if adjustment_key in adjustments:
                effect *= adjustments[adjustment_key]
        
        return effect
    
    def _calculate_confidence_effects(self, matches: List[AnchorMatch]) -> Dict[str, float]:
        """Calculate total confidence effects from all matches."""
        boosting_effects = [m.weighted_effect for m in matches if m.anchor_type == 'boosting']
        reducing_effects = [m.weighted_effect for m in matches if m.anchor_type == 'reducing']
        
        # Get combination rules
        combination_rules = self.config.get_combination_rules()
        
        # Calculate total effects using specified combination method
        total_boost = self._combine_effects(boosting_effects, combination_rules)
        total_reduction = self._combine_effects(reducing_effects, combination_rules)
        
        # Apply limits
        max_boost = combination_rules.get('max_total_boost', 0.30)
        max_reduction = combination_rules.get('max_total_reduction', 0.35)
        
        total_boost = min(total_boost, max_boost)
        total_reduction = min(total_reduction, max_reduction)
        
        # Calculate net effect
        net_effect = total_boost - total_reduction
        
        return {
            'total_boost': total_boost,
            'total_reduction': total_reduction,
            'net_effect': net_effect
        }
    
    def _combine_effects(self, effects: List[float], combination_rules: Dict[str, Any]) -> float:
        """Combine multiple effects using the specified method."""
        if not effects:
            return 0.0
        
        method = combination_rules.get('combination_method', 'diminishing_returns')
        
        if method == 'additive':
            return sum(effects)
        
        elif method == 'weighted_average':
            return sum(effects) / len(effects)
        
        elif method == 'diminishing_returns':
            # Sort effects in descending order
            effects = sorted(effects, reverse=True)
            
            # Get diminishing returns settings
            dr_config = combination_rules.get('diminishing_returns', {})
            decay = dr_config.get('effectiveness_decay', 0.8)
            min_effectiveness = dr_config.get('min_effectiveness', 0.2)
            
            total_effect = 0.0
            current_multiplier = 1.0
            
            for effect in effects:
                total_effect += effect * current_multiplier
                current_multiplier = max(current_multiplier * decay, min_effectiveness)
            
            return total_effect
        
        else:
            # Default to additive
            return sum(effects)
    
    def _generate_explanation(self, matches: List[AnchorMatch], effects: Dict[str, float],
                             rule_type: Optional[str], content_type: Optional[str]) -> str:
        """Generate human-readable explanation of the anchor analysis."""
        explanation_parts = []
        
        # Summary
        net_effect = effects['net_effect']
        if net_effect > 0.05:
            explanation_parts.append(f"🔼 Confidence increased by {net_effect:+.3f}")
        elif net_effect < -0.05:
            explanation_parts.append(f"🔽 Confidence decreased by {net_effect:+.3f}")
        else:
            explanation_parts.append(f"➡️ Confidence mostly unchanged ({net_effect:+.3f})")
        
        # Add context information
        if rule_type or content_type:
            context_info = []
            if rule_type:
                context_info.append(f"rule: {rule_type}")
            if content_type:
                context_info.append(f"content: {content_type}")
            explanation_parts.append(f"Context: {', '.join(context_info)}")
        
        # Boosting factors
        boosting_matches = [m for m in matches if m.anchor_type == 'boosting']
        if boosting_matches:
            explanation_parts.append(f"\n📈 Boosting factors ({len(boosting_matches)}):")
            for match in sorted(boosting_matches, key=lambda x: x.weighted_effect, reverse=True)[:3]:
                explanation_parts.append(
                    f"  • {match.anchor_name.replace('_', ' ').title()}: "
                    f"'{match.match_text}' (+{match.weighted_effect:.3f})"
                )
            if len(boosting_matches) > 3:
                explanation_parts.append(f"  • ... and {len(boosting_matches) - 3} more")
        
        # Reducing factors
        reducing_matches = [m for m in matches if m.anchor_type == 'reducing']
        if reducing_matches:
            explanation_parts.append(f"\n📉 Reducing factors ({len(reducing_matches)}):")
            for match in sorted(reducing_matches, key=lambda x: x.weighted_effect, reverse=True)[:3]:
                explanation_parts.append(
                    f"  • {match.anchor_name.replace('_', ' ').title()}: "
                    f"'{match.match_text}' (-{match.weighted_effect:.3f})"
                )
            if len(reducing_matches) > 3:
                explanation_parts.append(f"  • ... and {len(reducing_matches) - 3} more")
        
        # No matches case
        if not matches:
            explanation_parts.append("\n🔍 No significant linguistic patterns detected")
        
        return '\n'.join(explanation_parts)
    
    def _count_patterns_checked(self) -> int:
        """Count total number of patterns that were checked."""
        # This would be more accurate with actual tracking, but estimate for now
        boosting_anchors = self.config.get_boosting_anchors()
        reducing_anchors = self.config.get_reducing_anchors()
        
        pattern_count = 0
        for category in boosting_anchors.values():
            for anchor_config in category.values():
                pattern_count += len(anchor_config.get('patterns', []))
        
        for category in reducing_anchors.values():
            for anchor_config in category.values():
                pattern_count += len(anchor_config.get('patterns', []))
        
        return pattern_count
    
    def get_anchor_categories(self) -> Dict[str, List[str]]:
        """Get available anchor categories."""
        return {
            'boosting': self.config.get_all_anchor_categories('boosting'),
            'reducing': self.config.get_all_anchor_categories('reducing')
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / max(1, self._cache_hits + self._cache_misses),
            'compiled_patterns_cached': len(self._pattern_cache),
            'analysis_results_cached': len(self._analysis_cache)
        }
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        self._pattern_cache.clear()
        self._analysis_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
    
    def reload_configuration(self) -> None:
        """Reload configuration and clear caches."""
        self.clear_caches()
        self._load_configuration()