"""
Dynamic Example Selector for Multi-Shot Prompting
Intelligently selects the best examples for AI learning based on context, success rates, and similarity.
"""

import logging
import yaml
import os
import random
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class ExampleSelector:
    """
    Intelligent example selection for multi-shot prompting.
    Provides contextual, success-optimized examples for AI learning.
    """
    
    def __init__(self):
        """Initialize the example selector with database loading."""
        self.examples_db = {}
        self.selection_strategies = {}
        self.learning_config = {}
        self.performance_config = {}
        self._load_examples_database()
    
    def _load_examples_database(self) -> None:
        """Load the multi-shot examples database from YAML."""
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'multi_shot_examples.yaml')
            with open(db_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            self.examples_db = data.get('examples', {})
            self.selection_strategies = data.get('selection_strategies', {})
            self.learning_config = data.get('learning', {})
            self.performance_config = data.get('performance', {})
            
            # Calculate total examples loaded
            total_examples = sum(len(examples) for examples in self.examples_db.values())
            error_types_covered = len(self.examples_db)
            
            logger.info(f"📚 Loaded {total_examples} examples across {error_types_covered} error types")
            
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"Failed to load examples database: {e}")
            self.examples_db = {}
    
    def select_examples(self, error_type: str, current_text: str, context: str = "text", 
                       num_examples: Optional[int] = None, include_negative: bool = True) -> List[Dict[str, Any]]:
        """
        Select the best examples for multi-shot prompting.
        
        Args:
            error_type: The type of error being fixed
            current_text: The current problematic text
            context: The context type (heading, instruction, etc.)
            num_examples: Number of examples to select (auto-determined if None)
            
        Returns:
            List of selected examples optimized for learning
        """
        if error_type not in self.examples_db:
            logger.warning(f"No examples found for error type: {error_type}")
            return []
        
        available_examples = self.examples_db[error_type]
        
        if not available_examples:
            return []
        
        # Determine optimal number of examples
        if num_examples is None:
            num_examples = self._calculate_optimal_example_count(available_examples, current_text)
        
        # Score and rank examples
        scored_examples = self._score_examples(
            available_examples, current_text, context, error_type
        )
        
        # Select top examples
        selected = scored_examples[:num_examples]
        
        logger.debug(f"Selected {len(selected)} examples for {error_type} from {len(available_examples)} available")
        
        return [example['data'] for example in selected]
    
    def _score_examples(self, examples: List[Dict], current_text: str, 
                       context: str, error_type: str) -> List[Dict[str, Any]]:
        """
        Score examples based on multiple criteria and return sorted by relevance.
        
        Args:
            examples: Available examples for the error type
            current_text: Current text being fixed
            context: Context type
            error_type: Error type being addressed
            
        Returns:
            Examples sorted by score (highest first)
        """
        scored_examples = []
        
        for example in examples:
            score = 0.0
            
            # Context matching score
            context_score = self._calculate_context_score(example, context)
            score += context_score * self._get_strategy_weight('by_context')
            
            # Success rate score
            success_score = example.get('success_rate', 0.8)
            score += success_score * self._get_strategy_weight('by_success_rate')
            
            # Similarity score
            similarity_score = self._calculate_similarity_score(example, current_text)
            score += similarity_score * self._get_strategy_weight('by_similarity')
            
            # Difficulty progression score
            difficulty_score = self._calculate_difficulty_score(example, error_type)
            score += difficulty_score * self._get_strategy_weight('by_difficulty')
            
            scored_examples.append({
                'data': example,
                'score': score,
                'context_score': context_score,
                'success_score': success_score,
                'similarity_score': similarity_score,
                'difficulty_score': difficulty_score
            })
        
        # Sort by score (descending)
        scored_examples.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_examples
    
    def _calculate_context_score(self, example: Dict, target_context: str) -> float:
        """Calculate how well example context matches target context."""
        example_context = example.get('context', 'text')
        
        # Exact match
        if example_context == target_context:
            return 1.0
        
        # Similar context types
        context_similarity = {
            'heading': ['title', 'header'],
            'instruction': ['procedure', 'step', 'command'],
            'explanation': ['description', 'text', 'paragraph'],
            'reference': ['link', 'citation'],
            'warning': ['alert', 'notice', 'caution']
        }
        
        for main_type, similar_types in context_similarity.items():
            if target_context == main_type and example_context in similar_types:
                return 0.8
            if example_context == main_type and target_context in similar_types:
                return 0.8
        
        # Default partial match
        return 0.3
    
    def _calculate_similarity_score(self, example: Dict, current_text: str) -> float:
        """Calculate text similarity between example and current text."""
        example_text = example.get('before', '')
        
        if not example_text or not current_text:
            return 0.5
        
        # Use sequence matcher for similarity
        similarity = SequenceMatcher(None, example_text.lower(), current_text.lower()).ratio()
        
        # Boost score for length similarity
        length_ratio = min(len(example_text), len(current_text)) / max(len(example_text), len(current_text))
        length_bonus = length_ratio * 0.2
        
        return min(1.0, similarity + length_bonus)
    
    def _calculate_difficulty_score(self, example: Dict, error_type: str) -> float:
        """Calculate difficulty appropriateness score."""
        difficulty = example.get('difficulty', 'medium')
        
        # Progressive difficulty strategy
        if self.selection_strategies.get('by_difficulty', {}).get('enabled', True):
            # Prefer progression: simple → medium → complex
            difficulty_weights = {
                'simple': 0.9,   # High weight for foundational examples
                'medium': 0.7,   # Good for most cases
                'complex': 0.5   # Use sparingly for advanced cases
            }
            return difficulty_weights.get(difficulty, 0.6)
        
        return 0.6
    
    def _get_strategy_weight(self, strategy_name: str) -> float:
        """Get the weight for a selection strategy."""
        strategy = self.selection_strategies.get(strategy_name, {})
        if strategy.get('enabled', True):
            return strategy.get('weight', 0.25)
        return 0.0
    
    def _calculate_optimal_example_count(self, available_examples: List[Dict], 
                                       current_text: str) -> int:
        """
        Calculate the optimal number of examples to include.
        
        Args:
            available_examples: Examples available for selection
            current_text: Text being processed
            
        Returns:
            Optimal number of examples for this case
        """
        # Base configuration
        min_examples = self.learning_config.get('minimum_examples', 2)
        max_examples = self.learning_config.get('maximum_examples', 5)
        
        # Adjust based on available examples
        available_count = len(available_examples)
        
        if available_count <= min_examples:
            return available_count
        
        # Adjust based on text complexity
        text_complexity = self._assess_text_complexity(current_text)
        
        if text_complexity == 'simple':
            return min(3, available_count)
        elif text_complexity == 'medium':
            return min(4, available_count)
        else:  # complex
            return min(max_examples, available_count)
    
    def _assess_text_complexity(self, text: str) -> str:
        """Assess the complexity of the text being processed."""
        if not text:
            return 'simple'
        
        # Simple heuristics for complexity assessment
        word_count = len(text.split())
        char_count = len(text)
        
        # Count complex indicators
        complex_indicators = [
            ',' in text,  # Has commas
            '(' in text,  # Has parentheses  
            len([w for w in text.split() if len(w) > 8]) > 0,  # Has long words
            word_count > 10,  # Long sentence
            any(word.isupper() for word in text.split())  # Has acronyms
        ]
        
        complexity_score = sum(complex_indicators)
        
        if complexity_score <= 1:
            return 'simple'
        elif complexity_score <= 3:
            return 'medium'
        else:
            return 'complex'
    
    def format_examples_for_prompt(self, examples: List[Dict[str, Any]], 
                                  error_type: str) -> str:
        """
        Format selected examples into a multi-shot prompt section.
        
        Args:
            examples: Selected examples to format
            error_type: Error type being addressed
            
        Returns:
            Formatted string for inclusion in AI prompt
        """
        if not examples:
            return f"Apply standard {error_type.replace('_', ' ')} guidelines."
        
        formatted_examples = []
        
        for i, example in enumerate(examples, 1):
            before = example.get('before', '')
            after = example.get('after', '')
            reasoning = example.get('reasoning', '')
            context = example.get('context', 'text')
            
            example_text = f"""**Example {i}** ({context}):
- Original: "{before}"
- Corrected: "{after}"
- Why: {reasoning}"""
            
            formatted_examples.append(example_text)
        
        examples_section = "\n\n".join(formatted_examples)
        
        return f"""**Multi-Shot Learning Examples:**

{examples_section}

**Your Task:** Apply the same pattern demonstrated in these examples to fix the current text."""
    
    def track_example_success(self, error_type: str, example: Dict[str, Any], 
                            success: bool) -> None:
        """
        Track the success/failure of an example for learning improvement.
        
        Args:
            error_type: Error type that was processed
            example: The example that was used
            success: Whether the example led to successful correction
        """
        if not self.learning_config.get('track_success', False):
            return
        
        # This would be implemented with persistent storage
        # For now, log the feedback for future implementation
        before_text = example.get('before', 'unknown')
        success_status = 'SUCCESS' if success else 'FAILURE'
        
        logger.info(f"Example tracking: {error_type} | {before_text[:30]}... | {success_status}")
    
    def get_example_stats(self) -> Dict[str, Any]:
        """Get statistics about the example database."""
        if not self.examples_db:
            return {'error': 'No examples database loaded'}
        
        stats = {
            'total_error_types': len(self.examples_db),
            'total_examples': sum(len(examples) for examples in self.examples_db.values()),
            'error_type_coverage': {},
            'average_success_rate': 0.0,
            'difficulty_distribution': {'simple': 0, 'medium': 0, 'complex': 0}
        }
        
        total_success_sum = 0
        total_examples = 0
        
        for error_type, examples in self.examples_db.items():
            stats['error_type_coverage'][error_type] = len(examples)
            
            for example in examples:
                total_examples += 1
                total_success_sum += example.get('success_rate', 0.8)
                difficulty = example.get('difficulty', 'medium')
                stats['difficulty_distribution'][difficulty] += 1
        
        if total_examples > 0:
            stats['average_success_rate'] = total_success_sum / total_examples
        
        return stats
