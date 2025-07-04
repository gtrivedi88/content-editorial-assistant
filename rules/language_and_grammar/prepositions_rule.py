"""
Prepositions Rule
Based on IBM Style Guide topic: "Prepositions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class PrepositionsRule(BaseLanguageRule):
    """
    Checks for potentially cluttered sentences with too many prepositions.
    """
    def _get_rule_type(self) -> str:
        return 'prepositions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        # Context-aware analysis: Apply different thresholds based on content type
        # No more hardcoded heuristics - use context to determine appropriate complexity levels
        
        # Skip analysis for code blocks and technical content
        if context and context.get('block_type') in ['listing', 'literal', 'attribute_entry']:
            return errors
        
        # Determine appropriate complexity threshold based on context
        max_prepositions_threshold = self._get_context_appropriate_threshold(context)
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # Use SpaCy's linguistic analysis instead of simple counting
            preposition_analysis = self._analyze_prepositional_complexity(doc)
            
            if preposition_analysis['is_overly_complex']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=f"Sentence has {preposition_analysis['count']} prepositions creating complex structure. {preposition_analysis['complexity_reason']}",
                    suggestions=preposition_analysis['suggestions'],
                    severity=preposition_analysis['severity']
                ))
        return errors
    
    def _get_context_appropriate_threshold(self, context) -> int:
        """Determine appropriate prepositional complexity threshold based on context."""
        if not context:
            return 4  # Default threshold
        
        block_type = context.get('block_type', '')
        
        # Technical documentation can be more complex
        if block_type in ['admonition', 'sidebar']:
            return 6
        
        # Headings should be simple
        if block_type == 'heading':
            return 2
        
        # List items should be concise
        if block_type in ['list_item', 'list_item_ordered', 'list_item_unordered']:
            return 3
        
        # Regular paragraphs
        return 4
    
    def _analyze_prepositional_complexity(self, doc) -> Dict[str, Any]:
        """Analyze prepositional complexity using linguistic patterns."""
        prepositions = [token for token in doc if token.pos_ == 'ADP']
        count = len(prepositions)
        
        # Context-aware complexity analysis
        analysis = {
            'count': count,
            'is_overly_complex': False,
            'complexity_reason': '',
            'suggestions': [],
            'severity': 'low'
        }
        
        if count <= 2:
            return analysis
        
        # Check for prepositional phrase chains
        chains = self._identify_prepositional_chains(prepositions)
        nested_depth = max(len(chain) for chain in chains) if chains else 0
        
        # Determine if complex based on patterns, not just count
        if nested_depth > 2:
            analysis['is_overly_complex'] = True
            analysis['complexity_reason'] = f"Contains nested prepositional phrases (depth: {nested_depth})."
            analysis['suggestions'] = [
                "Break up nested prepositional phrases into separate sentences.",
                "Use active voice to reduce prepositional complexity."
            ]
            analysis['severity'] = 'medium'
        elif count > 5 and len([t for t in doc if t.pos_ == 'VERB']) < 2:
            analysis['is_overly_complex'] = True
            analysis['complexity_reason'] = "High preposition-to-verb ratio indicates nominal style."
            analysis['suggestions'] = [
                "Use more active verbs to reduce reliance on prepositions.",
                "Consider splitting into multiple sentences."
            ]
            analysis['severity'] = 'low'
        
        return analysis
    
    def _identify_prepositional_chains(self, prepositions) -> List[List]:
        """Identify chains of prepositional phrases."""
        chains = []
        current_chain = []
        
        for prep in prepositions:
            # Simple chain detection based on dependency structure
            if prep.head.pos_ == 'ADP' or (current_chain and prep.i == current_chain[-1].i + 1):
                current_chain.append(prep)
            else:
                if current_chain:
                    chains.append(current_chain)
                current_chain = [prep]
        
        if current_chain:
            chains.append(current_chain)
        
        return [chain for chain in chains if len(chain) > 1]
