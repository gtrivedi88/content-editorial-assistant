"""
Claims and Recommendations Rule
Based on IBM Style Guide topic: "Claims and recommendations"
"""
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ClaimsRule(BaseLegalRule):
    """
    Checks for unsupported claims and subjective words that could have
    legal implications, such as "secure," "easy," or "best practice."
    """
    def _get_rule_type(self) -> str:
        return 'legal_claims'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for legally problematic claims.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)

        # Linguistic Anchor: A list of words that make subjective or absolute claims.
        claim_words = {
            "secure", "easy", "effortless", "best practice", "future-proof"
        }

        for i, sent in enumerate(doc.sents):
            for word in claim_words:
                # Use re.finditer to get match objects for every occurrence
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', sent.text, re.IGNORECASE):
                    # Generate context-aware suggestions using spaCy morphological analysis
                    suggestions = self._generate_contextual_suggestions(match.group().lower(), sent)
                    
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"The term '{match.group()}' makes a subjective or unsupported claim that should be avoided.",
                        suggestions=suggestions,
                        severity='high',
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
    
    def _generate_contextual_suggestions(self, word: str, sentence) -> List[str]:
        """Generate context-aware suggestions using spaCy morphological analysis."""
        suggestions = []
        
        # Context-specific replacements using linguistic patterns
        if word == "easy":
            # Analyze surrounding context for better suggestions
            if any(token.lemma_ in ["process", "step", "procedure"] for token in sentence):
                suggestions.append("Replace with 'straightforward' or 'simple'")
                suggestions.append("Example: 'This is a straightforward process'")
            elif any(token.lemma_ in ["use", "configure", "setup"] for token in sentence):
                suggestions.append("Replace with 'quick' or 'direct'")
                suggestions.append("Example: 'This provides a direct setup method'")
            else:
                suggestions.append("Replace with 'accessible' or 'user-friendly'")
        
        elif word == "future-proof":
            # Check if it's about technology/architecture
            if any(token.lemma_ in ["system", "architecture", "design", "solution"] for token in sentence):
                suggestions.append("Replace with 'scalable' or 'adaptable'")
                suggestions.append("Example: 'This is a scalable solution'")
            elif any(token.lemma_ in ["process", "approach", "method"] for token in sentence):
                suggestions.append("Replace with 'sustainable' or 'long-term'")
                suggestions.append("Example: 'This is a sustainable approach'")
            else:
                suggestions.append("Replace with 'durable' or 'robust'")
        
        elif word == "secure":
            suggestions.append("Replace with 'security-enhanced' or specify the security feature")
            suggestions.append("Example: 'encrypted' or 'access-controlled'")
        
        elif word == "best practice":
            suggestions.append("Replace with 'recommended approach' or 'standard method'")
            suggestions.append("Example: 'Use the recommended configuration'")
        
        elif word == "effortless":
            if any(token.lemma_ in ["install", "setup", "configure"] for token in sentence):
                suggestions.append("Replace with 'automated' or 'streamlined'")
                suggestions.append("Example: 'automated installation'")
            else:
                suggestions.append("Replace with 'smooth' or 'simplified'")
        
        # Fallback suggestion if no specific context found
        if not suggestions:
            suggestions.append(f"Replace '{word}' with a more specific, objective description")
            suggestions.append("Describe the actual feature or benefit instead of using subjective language")
        
        return suggestions
