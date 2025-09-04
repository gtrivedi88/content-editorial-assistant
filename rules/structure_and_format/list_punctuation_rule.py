"""
List Punctuation Rule - Evidence-Based Analysis

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

class ListPunctuationRule(BaseStructureRule):
    """
    Checks for list punctuation violations using evidence-based analysis:
    - Inconsistent punctuation within lists
    - Unnecessary periods in fragment-style lists
    - Missing periods in sentence-style lists
    - Context-aware validation for different list types
    Enhanced with spaCy morphological analysis and contextual awareness.
    """
    def __init__(self):
        """Initialize the rule with list punctuation patterns."""
        super().__init__()
        self._initialize_list_patterns()
    
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'list_punctuation'
    
    def _initialize_list_patterns(self):
        """Initialize list punctuation detection patterns."""
        self.list_patterns = {
            'ordered_list_marker': re.compile(r'^\s*\d+\.\s+'),
            'unordered_list_marker': re.compile(r'^\s*[-*+•]\s+'),
            'ends_with_period': re.compile(r'\.\s*$'),
            'ends_with_punctuation': re.compile(r'[.!?;:]\s*$'),
            'sentence_indicators': re.compile(r'\b(is|are|was|were|will|shall|must|should|can|could|would|has|have|had)\b'),
            'fragment_indicators': re.compile(r'^\s*[A-Z][a-z]*(\s+[a-z]+)*\s*$')  # Simple noun phrases
        }
    
    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for list punctuation violations:
        - Inconsistent punctuation within lists
        - Inappropriate periods for list item types
        - Context-aware validation for list structure
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Only analyze list contexts
        block_type = context.get('block_type', 'paragraph')
        if not self._is_list_context(block_type):
            return errors
        
        # Fallback analysis when nlp is not available
        if not nlp:
            return self._fallback_list_punctuation_analysis(text, sentences, context)

        try:
            doc = nlp(text)
            
            # Analyze list structure and punctuation
            if self._is_single_list_item(context):
                # Analyze individual list item
                errors.extend(self._analyze_single_list_item(doc, text, context))
            else:
                # Analyze multiple list items for consistency
                errors.extend(self._analyze_list_consistency(doc, text, sentences, context))
            
        except Exception as e:
            # Graceful degradation for SpaCy errors
            return self._fallback_list_punctuation_analysis(text, sentences, context)
        
        return errors
    
    def _is_list_context(self, block_type: str) -> bool:
        """Check if the current context is a list that we should analyze."""
        return block_type in [
            'ordered_list_item', 'unordered_list_item', 'list_item',
            'ordered_list', 'unordered_list', 'dlist'
        ]
    
    def _is_single_list_item(self, context: Dict[str, Any]) -> bool:
        """Check if we're analyzing a single list item vs. multiple items."""
        block_type = context.get('block_type', 'paragraph')
        return block_type in ['ordered_list_item', 'unordered_list_item', 'list_item']
    
    def _fallback_list_punctuation_analysis(self, text: str, sentences: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback analysis when spaCy is not available."""
        errors = []
        
        # Basic context guards
        if not self._is_list_context(context.get('block_type', '')):
            return errors
        
        # Simple pattern-based analysis
        if self._is_single_list_item(context):
            # Analyze single item
            item_type = self._classify_list_item_fallback(text)
            evidence_score = self._calculate_fallback_punctuation_evidence(text, item_type, context)
            
            if evidence_score > 0.1:
                error = self._create_list_punctuation_error(text, item_type, evidence_score, context)
                if error:
                    errors.append(error)
        
        return errors
    
    def _analyze_single_list_item(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze punctuation for a single list item."""
        errors = []
        
        # Classify the list item type
        item_classification = self.classify_list_item(text, doc)
        
        # Calculate evidence for punctuation issues
        evidence_score = self._calculate_list_item_punctuation_evidence(
            text, item_classification, context, doc
        )
        
        if evidence_score > 0.1:
            error = self._create_error(
                sentence=text.strip(),
                sentence_index=0,
                message=self._get_contextual_list_message(item_classification, evidence_score, context),
                suggestions=self._generate_smart_list_suggestions(item_classification, evidence_score, context),
                severity='low' if evidence_score < 0.6 else 'medium',
                text=text,
                context=context,
                evidence_score=evidence_score,
                span=(len(text.rstrip()) - 1, len(text.rstrip())) if text.rstrip().endswith('.') else (len(text), len(text)),
                flagged_text='.' if text.rstrip().endswith('.') else text[-10:],
                violation_type=f'list_punctuation_{item_classification}',
                item_classification=item_classification
            )
            errors.append(error)
        
        return errors
    
    def _analyze_list_consistency(self, doc: 'Doc', text: str, sentences: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze punctuation consistency across multiple list items."""
        errors = []
        
        # Analyze each sentence as a potential list item
        item_classifications = []
        punctuation_patterns = []
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                try:
                    sent_doc = doc if len(sentences) == 1 else doc[i:i+1] if i < len(doc.sents) else None
                    if sent_doc:
                        classification = self.classify_list_item(sentence, sent_doc)
                        has_period = sentence.rstrip().endswith('.')
                        
                        item_classifications.append(classification)
                        punctuation_patterns.append(has_period)
                except:
                    continue
        
        # Check for inconsistency
        if len(item_classifications) > 1 and len(set(punctuation_patterns)) > 1:
            evidence_score = self._calculate_consistency_evidence(
                item_classifications, punctuation_patterns, context
            )
            
            if evidence_score > 0.1:
                error = self._create_error(
                    sentence=text.strip()[:100] + "...",
                    sentence_index=0,
                    message=self._get_consistency_message(evidence_score, context),
                    suggestions=self._generate_consistency_suggestions(item_classifications, evidence_score, context),
                    severity='medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(0, len(text)),
                    flagged_text="Inconsistent list punctuation",
                    violation_type='list_punctuation_inconsistency'
                )
                errors.append(error)
        
        return errors
    
    def classify_list_item(self, item_text: str, doc: Optional['Doc'] = None) -> str:
        """
        Classify list items as:
        - 'sentence': Complete sentences (should have periods)
        - 'fragment': Phrases/words (periods optional)
        - 'mixed': Lists with both types (needs consistency)
        """
        if not item_text.strip():
            return 'fragment'
        
        # Use spaCy analysis if available
        if doc:
            return self._classify_with_spacy(item_text, doc)
        else:
            return self._classify_list_item_fallback(item_text)
    
    def _classify_with_spacy(self, item_text: str, doc: 'Doc') -> str:
        """Use spaCy to classify list item grammatical structure."""
        if not doc:
            return 'fragment'
        
        # Analyze grammatical completeness
        has_complete_syntax = self._has_complete_syntactic_structure(doc)
        has_verbs = any(token.pos_ == 'VERB' for token in doc)
        word_count = len([token for token in doc if token.is_alpha])
        
        # Classification logic
        if has_complete_syntax and has_verbs and word_count >= 4:
            return 'sentence'
        elif has_verbs and word_count >= 6:
            return 'sentence'  # Likely a complete thought
        elif word_count <= 2:
            return 'fragment'  # Very short items are fragments
        else:
            return 'fragment'  # Default to fragment for ambiguous cases
    
    def _classify_list_item_fallback(self, item_text: str) -> str:
        """Classify list item without spaCy using simple heuristics."""
        text = item_text.strip()
        word_count = len(text.split())
        
        # Very short items are usually fragments
        if word_count <= 2:
            return 'fragment'
        
        # Check for sentence indicators (verbs, complete structure)
        if self.list_patterns['sentence_indicators'].search(text.lower()):
            return 'sentence'
        
        # Check for fragment indicators (simple noun phrases)
        if word_count <= 4 and self.list_patterns['fragment_indicators'].match(text):
            return 'fragment'
        
        # Long items are more likely to be sentences
        if word_count >= 8:
            return 'sentence'
        
        # Default to fragment for ambiguous cases
        return 'fragment'

    # === EVIDENCE CALCULATION ===
    
    def _calculate_list_item_punctuation_evidence(self, text: str, item_classification: str, context: Dict[str, Any], doc: Optional['Doc'] = None) -> float:
        """Calculate evidence for list item punctuation violations."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if self._apply_zero_false_positive_guards_structure({'text': text, 'sentence': text}, context):
            return 0.0
        
        # Creative content may use different list styles
        if context.get('content_type') in ['creative', 'literary', 'poetry']:
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        has_period = text.rstrip().endswith('.')
        evidence_score = 0.0
        
        if item_classification == 'sentence':
            # Sentences should have periods
            if not has_period:
                evidence_score = 0.7  # Missing period in sentence
            else:
                evidence_score = 0.0  # Correct usage
        elif item_classification == 'fragment':
            # Fragments typically don't need periods
            if has_period:
                evidence_score = 0.6  # Unnecessary period in fragment
            else:
                evidence_score = 0.0  # Correct usage
        else:  # mixed or ambiguous
            evidence_score = 0.3  # Low evidence for ambiguous cases
        
        # === STEP 2: CONTEXT CLUES ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 3: LIST-SPECIFIC CLUES ===
        list_type = context.get('block_type', 'list_item')
        
        # Ordered lists (procedures) are more likely to be sentences
        if list_type == 'ordered_list_item' and item_classification == 'fragment' and has_period:
            evidence_score -= 0.2  # More tolerant of periods in ordered lists
        
        # Unordered lists (features, items) are more likely to be fragments
        if list_type == 'unordered_list_item' and item_classification == 'sentence' and not has_period:
            evidence_score -= 0.1  # More tolerant of missing periods in unordered lists
        
        return max(0.0, min(1.0, evidence_score))
    
    def _calculate_consistency_evidence(self, classifications: List[str], punctuation_patterns: List[bool], context: Dict[str, Any]) -> float:
        """Calculate evidence for punctuation inconsistency across list items."""
        if len(set(punctuation_patterns)) <= 1:
            return 0.0  # Already consistent
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.5  # Medium evidence for inconsistency
        
        # === STEP 2: CLASSIFICATION ANALYSIS ===
        # If all items are the same type, inconsistency is stronger evidence
        if len(set(classifications)) == 1:
            evidence_score += 0.3  # Strong evidence - same type should have same punctuation
        
        # Mixed types might justify different punctuation
        if 'sentence' in classifications and 'fragment' in classifications:
            evidence_score -= 0.2  # More tolerant of mixed punctuation
        
        # === STEP 3: CONTEXT CLUES ===
        content_type = context.get('content_type', 'general')
        if content_type == 'formal':
            evidence_score += 0.1  # Formal writing needs consistency
        elif content_type == 'technical':
            evidence_score += 0.2  # Technical docs need consistency
        
        return max(0.0, min(1.0, evidence_score))
    
    def _calculate_fallback_punctuation_evidence(self, text: str, item_type: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for fallback analysis without spaCy."""
        has_period = text.rstrip().endswith('.')
        word_count = len(text.strip().split())
        
        # Simple evidence calculation
        if item_type == 'sentence' and not has_period:
            return 0.6  # Missing period
        elif item_type == 'fragment' and has_period and word_count <= 3:
            return 0.7  # Short fragment with unnecessary period
        elif item_type == 'fragment' and has_period and word_count <= 5:
            return 0.4  # Medium fragment with period - less certain
        
        return 0.0
    
    # === HELPER METHODS ===
    
    def _create_list_punctuation_error(self, text: str, item_type: str, evidence_score: float, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create error for list punctuation violation (fallback)."""
        if evidence_score <= 0.1:
            return None
        
        return self._create_error(
            sentence=text.strip(),
            sentence_index=0,
            message=self._get_contextual_list_message(item_type, evidence_score, context),
            suggestions=self._generate_smart_list_suggestions(item_type, evidence_score, context),
            severity='low' if evidence_score < 0.6 else 'medium',
            text=text,
            context=context,
            evidence_score=evidence_score,
            span=(len(text.rstrip()) - 1, len(text.rstrip())) if text.rstrip().endswith('.') else (len(text), len(text)),
            flagged_text='.' if text.rstrip().endswith('.') else text.strip()[-10:],
            violation_type=f'list_punctuation_{item_type}'
        )

    # === SMART MESSAGING ===

    def _get_contextual_list_message(self, item_classification: str, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for list punctuation."""
        confidence_phrase = "clearly needs" if evidence_score > 0.8 else ("likely needs" if evidence_score > 0.6 else "might benefit from")
        
        block_type = context.get('block_type', 'list_item')
        list_type = 'ordered list' if 'ordered' in block_type else 'unordered list' if 'unordered' in block_type else 'list'
        
        if item_classification == 'sentence':
            return f"This {list_type} item contains a complete sentence and {confidence_phrase} a period."
        elif item_classification == 'fragment':
            return f"This {list_type} item is a fragment and {confidence_phrase} punctuation adjustment."
        else:
            return f"This {list_type} item {confidence_phrase} punctuation review for consistency."
    
    def _get_consistency_message(self, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate message for list punctuation consistency issues."""
        confidence_phrase = "clearly has" if evidence_score > 0.8 else ("likely has" if evidence_score > 0.6 else "may have")
        
        return f"This list {confidence_phrase} inconsistent punctuation across items."

    def _generate_smart_list_suggestions(self, item_classification: str, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for list punctuation."""
        suggestions = []
        
        if item_classification == 'sentence':
            if evidence_score > 0.6:
                suggestions.append("Add a period to complete this sentence.")
                suggestions.append("Complete sentences in lists should end with periods.")
            else:
                suggestions.append("Consider adding a period if this is a complete sentence.")
        
        elif item_classification == 'fragment':
            if evidence_score > 0.6:
                suggestions.append("Remove the period from this list item.")
                suggestions.append("Short phrases and fragments don't need periods.")
            else:
                suggestions.append("Consider removing the period for conciseness.")
        
        else:  # ambiguous
            suggestions.append("Review punctuation for consistency with other list items.")
            suggestions.append("Use periods for complete sentences, omit for fragments.")
        
        # Context-specific suggestions
        block_type = context.get('block_type', 'list_item')
        if 'ordered' in block_type:
            suggestions.append("Ordered lists often contain procedural steps that may be complete sentences.")
        elif 'unordered' in block_type:
            suggestions.append("Unordered lists often contain brief items that don't need periods.")
        
        content_type = context.get('content_type', 'general')
        if content_type == 'technical':
            suggestions.append("Technical documentation benefits from consistent list punctuation.")
        elif content_type == 'user_guide':
            suggestions.append("User guides should have clear, consistent list formatting.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _generate_consistency_suggestions(self, classifications: List[str], evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate suggestions for list punctuation consistency."""
        suggestions = [
            "Use consistent punctuation across all list items.",
            "Either use periods for all items or omit them for all items."
        ]
        
        # Analyze the mix of classifications
        if 'sentence' in classifications and 'fragment' in classifications:
            suggestions.append("Complete sentences should have periods; fragments typically don't.")
        else:
            suggestions.append("Since all items are similar, use consistent punctuation.")
        
        # Context-specific advice
        if evidence_score > 0.7:
            suggestions.append("This inconsistency significantly impacts readability.")
        
        return suggestions[:3]
