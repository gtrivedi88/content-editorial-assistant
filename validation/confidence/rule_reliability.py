"""
Rule Reliability Coefficient System
Formalized system for assigning reliability coefficients to different rule types.
Based on existing ErrorConsolidator logic but centralized and extensible.
"""

from typing import Dict, Optional
from functools import lru_cache


class RuleReliabilityCalculator:
    """
    Centralized system for calculating rule reliability coefficients.
    
    Replaces hardcoded reliability logic with a maintainable, extensible system
    that provides consistent reliability coefficients across all rule types.
    """
    
    def __init__(self):
        """Initialize the rule reliability calculator."""
        self._reliability_matrix = self._build_reliability_matrix()
    
    def _build_reliability_matrix(self) -> Dict[str, float]:
        """
        Build the comprehensive rule reliability matrix.
        
        Based on analysis of existing ErrorConsolidator logic and domain expertise.
        Coefficients represent typical accuracy/reliability of each rule type.
        
        Returns:
            Dictionary mapping rule types to reliability coefficients [0.5, 1.0]
        """
        return {
            # Legal/Compliance Rules (High Reliability)
            'claims': 0.85,
            'personal_information': 0.90,
            'company_names': 0.88,
            
            # Language/Grammar Rules (High-Medium Reliability)
            'inclusive_language': 0.88,
            'grammar': 0.85,
            'spelling': 0.90,
            'terminology': 0.85,
            'capitalization': 0.82,
            'contractions': 0.80,
            'pronouns': 0.75,
            'verbs': 0.80,
            'articles': 0.78,
            'conjunctions': 0.75,
            'prepositions': 0.75,
            'plurals': 0.80,
            'prefixes': 0.78,
            'anthropomorphism': 0.82,
            'adverbs_only': 0.75,
            
            # Technical Elements (High Reliability)
            'commands': 0.90,
            'programming_elements': 0.88,
            'ui_elements': 0.85,
            'keyboard_keys': 0.85,
            'mouse_buttons': 0.85,
            'files_and_directories': 0.82,
            'web_addresses': 0.88,
            
            # Punctuation Rules (Medium-High Reliability)
            'punctuation': 0.80,
            'commas': 0.78,
            'periods': 0.85,
            'semicolons': 0.80,
            'colons': 0.80,
            'quotation_marks': 0.82,
            'parentheses': 0.80,
            'dashes': 0.75,
            'hyphens': 0.75,
            'ellipses': 0.78,
            'exclamation_points': 0.75,
            'slashes': 0.80,
            'punctuation_and_symbols': 0.78,
            
            # Structure/Format Rules (Medium Reliability)
            'headings': 0.80,
            'lists': 0.78,
            'paragraphs': 0.75,
            'procedures': 0.80,
            'notes': 0.75,
            'messages': 0.78,
            'admonitions': 0.78,
            'glossaries': 0.80,
            'highlighting': 0.75,
            
            # Audience/Medium Rules (Medium Reliability)
            'tone': 0.72,
            'conversational_style': 0.70,
            'global_audiences': 0.75,
            'llm_consumability': 0.70,
            
            # Numbers/Measurement Rules (High Reliability)
            'numbers': 0.85,
            'currency': 0.88,
            'dates_and_times': 0.85,
            'units_of_measurement': 0.88,
            'numerals_vs_words': 0.80,
            
            # Reference Rules (Medium-High Reliability)
            'citations': 0.82,
            'geographic_locations': 0.80,
            'names_and_titles': 0.78,
            'product_names': 0.80,
            'product_versions': 0.82,
            
            # Word Usage Rules (Medium Reliability)
            'word_usage': 0.75,
            'a_words': 0.75, 'b_words': 0.75, 'c_words': 0.75, 'd_words': 0.75,
            'e_words': 0.75, 'f_words': 0.75, 'g_words': 0.75, 'h_words': 0.75,
            'i_words': 0.75, 'j_words': 0.75, 'k_words': 0.75, 'l_words': 0.75,
            'm_words': 0.75, 'n_words': 0.75, 'o_words': 0.75, 'p_words': 0.75,
            'q_words': 0.75, 'r_words': 0.75, 's_words': 0.75, 't_words': 0.75,
            'u_words': 0.75, 'v_words': 0.75, 'w_words': 0.75, 'x_words': 0.75,
            'y_words': 0.75, 'z_words': 0.75, 'special_chars': 0.75,
            
            # Sentence/Style Rules (Medium Reliability)
            'sentence_length': 0.70,
            'second_person': 0.68,
            
            # Ambiguity Rules (Medium Reliability)  
            'ambiguity': 0.72,
            'missing_actor': 0.70,
            'pronoun_ambiguity': 0.70,
            'fabrication_risk': 0.75,
            'unsupported_claims': 0.78,
            
            # Default fallback
            'default': 0.75,
            'unknown': 0.70
        }
    
    @lru_cache(maxsize=1000)
    def get_rule_reliability_coefficient(self, rule_type: str) -> float:
        """
        Get reliability coefficient for a specific rule type.
        
        Args:
            rule_type: The rule type identifier (e.g., 'claims', 'grammar')
            
        Returns:
            Reliability coefficient in range [0.5, 1.0]
        """
        if not rule_type:
            return self._reliability_matrix['unknown']
        
        # Direct lookup
        coefficient = self._reliability_matrix.get(rule_type)
        if coefficient is not None:
            return coefficient
        
        # Try partial matches for complex rule types
        for matrix_key, matrix_value in self._reliability_matrix.items():
            if matrix_key in rule_type or rule_type in matrix_key:
                return matrix_value
        
        # Return default
        return self._reliability_matrix['default']
    
    def get_rule_category(self, rule_type: str) -> str:
        """
        Classify rule type into a reliability category.
        
        Args:
            rule_type: The rule type identifier
            
        Returns:
            Category name: 'high', 'medium_high', 'medium', 'medium_low'
        """
        coefficient = self.get_rule_reliability_coefficient(rule_type)
        
        if coefficient >= 0.85:
            return 'high'
        elif coefficient >= 0.80:
            return 'medium_high' 
        elif coefficient >= 0.70:
            return 'medium'
        else:
            return 'medium_low'
    
    def get_all_rule_types(self) -> Dict[str, float]:
        """
        Get all rule types and their reliability coefficients.
        
        Returns:
            Complete mapping of rule types to coefficients
        """
        return self._reliability_matrix.copy()
    
    def validate_coefficient_ranges(self) -> bool:
        """
        Validate that all coefficients are in the valid range [0.5, 1.0].
        
        Returns:
            True if all coefficients are valid, False otherwise
        """
        for rule_type, coefficient in self._reliability_matrix.items():
            if not (0.5 <= coefficient <= 1.0):
                print(f"Invalid coefficient for {rule_type}: {coefficient}")
                return False
        return True
    
    def get_performance_stats(self) -> Dict[str, any]:
        """
        Get performance statistics for the reliability system.
        
        Returns:
            Performance statistics including cache info
        """
        cache_info = self.get_rule_reliability_coefficient.cache_info()
        return {
            'total_rule_types': len(self._reliability_matrix),
            'cache_hits': cache_info.hits,
            'cache_misses': cache_info.misses,
            'cache_hit_rate': cache_info.hits / max(1, cache_info.hits + cache_info.misses),
            'coefficient_range': {
                'min': min(self._reliability_matrix.values()),
                'max': max(self._reliability_matrix.values()),
                'mean': sum(self._reliability_matrix.values()) / len(self._reliability_matrix)
            }
        }


# Global instance for efficient reuse
_rule_reliability_calculator = None


def get_rule_reliability_coefficient(rule_type: str) -> float:
    """
    Get reliability coefficient for a rule type (global function interface).
    
    Args:
        rule_type: The rule type identifier
        
    Returns:
        Reliability coefficient in range [0.5, 1.0]
    """
    global _rule_reliability_calculator
    if _rule_reliability_calculator is None:
        _rule_reliability_calculator = RuleReliabilityCalculator()
    
    return _rule_reliability_calculator.get_rule_reliability_coefficient(rule_type)


def get_rule_category(rule_type: str) -> str:
    """
    Get reliability category for a rule type (global function interface).
    
    Args:
        rule_type: The rule type identifier
        
    Returns:
        Category: 'high', 'medium_high', 'medium', 'medium_low'
    """
    global _rule_reliability_calculator
    if _rule_reliability_calculator is None:
        _rule_reliability_calculator = RuleReliabilityCalculator()
    
    return _rule_reliability_calculator.get_rule_category(rule_type)


def validate_all_coefficients() -> bool:
    """
    Validate all reliability coefficients are in valid range.
    
    Returns:
        True if all coefficients are valid
    """
    global _rule_reliability_calculator
    if _rule_reliability_calculator is None:
        _rule_reliability_calculator = RuleReliabilityCalculator()
    
    return _rule_reliability_calculator.validate_coefficient_ranges()


if __name__ == "__main__":
    # Self-test
    calculator = RuleReliabilityCalculator()
    
    print("🧪 Rule Reliability System Self-Test")
    print("=" * 50)
    
    # Test coefficient validation
    print(f"✅ All coefficients valid: {calculator.validate_coefficient_ranges()}")
    
    # Test some lookups
    test_rules = ['claims', 'grammar', 'commands', 'unknown_rule', 'sentence_length']
    for rule in test_rules:
        coeff = calculator.get_rule_reliability_coefficient(rule)
        category = calculator.get_rule_category(rule)
        print(f"   {rule}: {coeff:.2f} ({category})")
    
    # Performance stats
    stats = calculator.get_performance_stats()
    print(f"\n📊 Performance Stats:")
    print(f"   Total rule types: {stats['total_rule_types']}")
    print(f"   Coefficient range: {stats['coefficient_range']['min']:.2f} - {stats['coefficient_range']['max']:.2f}")
    print(f"   Mean coefficient: {stats['coefficient_range']['mean']:.2f}")