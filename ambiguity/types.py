"""
Ambiguity Detection Types and Enums
Defines the core data structures and types for ambiguity detection in technical writing.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, NamedTuple, Set, Tuple
from dataclasses import dataclass


class AmbiguityType(Enum):
    """Types of ambiguity that can be detected."""
    
    # Passive voice without clear actors
    MISSING_ACTOR = "missing_actor"
    
    # Ambiguous pronoun references
    AMBIGUOUS_PRONOUN = "ambiguous_pronoun"
    
    # Unclear antecedent for pronouns (e.g., "It" with multiple possible referents)
    UNCLEAR_ANTECEDENT = "unclear_antecedent"
    
    # Unclear subject references
    UNCLEAR_SUBJECT = "unclear_subject"
    
    # Ambiguous modifier placement
    AMBIGUOUS_MODIFIER = "ambiguous_modifier"
    
    # Vague quantifiers (some, many, several without context)
    VAGUE_QUANTIFIER = "vague_quantifier"
    
    # Unclear temporal references (then, later, after without clear timing)
    UNCLEAR_TEMPORAL = "unclear_temporal"
    
    # Unsupported claims and promises that can't be substantiated
    UNSUPPORTED_CLAIMS = "unsupported_claims"
    
    # Risk of information fabrication or adding details not in original
    FABRICATION_RISK = "fabrication_risk"
    
    # Overly strong claims that could be weakened for accuracy
    EXCESSIVE_CERTAINTY = "excessive_certainty"


class AmbiguityCategory(Enum):
    """Categories of ambiguity for grouping and priority."""
    
    REFERENTIAL = "referential"  # Pronouns, subjects, references
    STRUCTURAL = "structural"    # Modifiers, sentence structure
    SEMANTIC = "semantic"        # Meaning, context, vagueness
    TEMPORAL = "temporal"        # Time references, sequence


class AmbiguitySeverity(Enum):
    """Severity levels for ambiguity detection."""
    
    LOW = "low"        # Minor ambiguity, might be clear from context
    MEDIUM = "medium"  # Moderate ambiguity, should be clarified
    HIGH = "high"      # Significant ambiguity, requires resolution
    CRITICAL = "critical"  # Severe ambiguity, completely unclear


class ResolutionStrategy(Enum):
    """Strategies for resolving different types of ambiguity."""
    
    IDENTIFY_ACTOR = "identify_actor"           # Find missing subject/actor
    CLARIFY_PRONOUN = "clarify_pronoun"         # Replace pronoun with noun
    RESTRUCTURE_SENTENCE = "restructure_sentence"  # Rewrite sentence structure
    ADD_CONTEXT = "add_context"                 # Add contextual information
    SPECIFY_REFERENCE = "specify_reference"     # Make reference more specific
    QUANTIFY_PRECISELY = "quantify_precisely"   # Replace vague with specific


@dataclass
class AmbiguityContext:
    """Context information for ambiguity detection."""
    
    sentence_index: int
    sentence: str
    paragraph_context: Optional[str] = None
    preceding_sentences: Optional[List[str]] = None
    following_sentences: Optional[List[str]] = None
    document_context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.preceding_sentences is None:
            self.preceding_sentences = []
        if self.following_sentences is None:
            self.following_sentences = []


@dataclass
class AmbiguityEvidence:
    """Evidence supporting an ambiguity detection."""
    
    tokens: List[str]  # Specific tokens that indicate ambiguity
    linguistic_pattern: str  # Pattern that matches ambiguity
    confidence: float  # Confidence score (0.0 to 1.0)
    spacy_features: Optional[Dict[str, Any]] = None  # SpaCy analysis results
    context_clues: Optional[Dict[str, Any]] = None  # Context analysis


@dataclass
class AmbiguityDetection:
    """Complete ambiguity detection result."""
    
    ambiguity_type: AmbiguityType
    category: AmbiguityCategory
    severity: AmbiguitySeverity
    context: AmbiguityContext
    evidence: AmbiguityEvidence
    resolution_strategies: List[ResolutionStrategy]
    
    # AI Rewriter instructions
    ai_instructions: List[str]
    examples: Optional[List[str]] = None
    
    # CRITICAL: Add span information for error consolidation
    span: Optional[Tuple[int, int]] = None
    flagged_text: Optional[str] = None
    
    def to_error_dict(self) -> Dict[str, Any]:
        """
        Convert to error dictionary compatible with Level 2 Enhanced Validation.
        
        Complies with:
        - confidence.md: Universal threshold (0.35), top-level confidence field
        - evidence_based_rule_development.md: Evidence-based confidence scoring
        - level_2_implementation.adoc: Enhanced validation compatibility
        """
        error_dict = {
            'type': 'ambiguity',
            'subtype': self.ambiguity_type.value,
            'category': self.category.value,
            'message': self._generate_message(),
            'suggestions': self._generate_suggestions(),
            'sentence': self.context.sentence,
            'sentence_index': self.context.sentence_index,
            'severity': self.severity.value,
            'confidence': self.evidence.confidence,  # Top-level confidence for confidence.md compliance
            'ai_instructions': self.ai_instructions,
            'examples': self.examples or [],
            'evidence': {
                'tokens': self.evidence.tokens,
                'pattern': self.evidence.linguistic_pattern,
                'spacy_features': getattr(self.evidence, 'spacy_features', {}),
                'context_clues': getattr(self.evidence, 'context_clues', []),
                'semantic_analysis': getattr(self.evidence, 'semantic_analysis', [])
            },
            'resolution_strategies': [s.value for s in self.resolution_strategies],
            # Level 2 Enhanced Validation compatibility
            'enhanced_validation_available': True,
            'confidence_score': self.evidence.confidence  # Alias for backward compatibility
        }
        
        # CRITICAL: Add span information for consolidation
        if self.span:
            error_dict['span'] = self.span
        if self.flagged_text:
            error_dict['flagged_text'] = self.flagged_text
        
        return error_dict
    
    def _generate_message(self) -> str:
        """Generate human-readable message for the ambiguity."""
        messages = {
            AmbiguityType.MISSING_ACTOR: f"Passive voice without clear actor: '{' '.join(self.evidence.tokens)}'",
            AmbiguityType.AMBIGUOUS_PRONOUN: f"Ambiguous pronoun reference: '{' '.join(self.evidence.tokens)}'",
            AmbiguityType.UNCLEAR_ANTECEDENT: f"Unclear antecedent for pronoun: '{' '.join(self.evidence.tokens)}'",
            AmbiguityType.UNCLEAR_SUBJECT: f"Unclear subject reference: '{' '.join(self.evidence.tokens)}'",
            AmbiguityType.AMBIGUOUS_MODIFIER: f"Ambiguous modifier placement: '{' '.join(self.evidence.tokens)}'",
            AmbiguityType.VAGUE_QUANTIFIER: f"Vague quantifier: '{' '.join(self.evidence.tokens)}'",
            AmbiguityType.UNCLEAR_TEMPORAL: f"Unclear temporal reference: '{' '.join(self.evidence.tokens)}'",
            AmbiguityType.UNSUPPORTED_CLAIMS: f"Unsupported claim or promise: '{' '.join(self.evidence.tokens)}'",
            AmbiguityType.FABRICATION_RISK: f"Risk of adding unverified information: '{' '.join(self.evidence.tokens)}'",
            AmbiguityType.EXCESSIVE_CERTAINTY: f"Overly strong claim: '{' '.join(self.evidence.tokens)}'"
        }
        return messages.get(self.ambiguity_type, "Ambiguity detected")
    
    def _generate_suggestions(self) -> List[str]:
        """Generate suggestions based on resolution strategies."""
        suggestions = []
        
        for strategy in self.resolution_strategies:
            if strategy == ResolutionStrategy.IDENTIFY_ACTOR:
                suggestions.append("Identify and specify the actor performing the action (e.g., 'The system generates...' or 'You generate...')")
            elif strategy == ResolutionStrategy.CLARIFY_PRONOUN:
                suggestions.append("Replace the pronoun with a specific noun to clarify the reference")
            elif strategy == ResolutionStrategy.RESTRUCTURE_SENTENCE:
                suggestions.append("Restructure the sentence to eliminate ambiguity")
            elif strategy == ResolutionStrategy.ADD_CONTEXT:
                suggestions.append("Add contextual information to clarify the meaning")
            elif strategy == ResolutionStrategy.SPECIFY_REFERENCE:
                suggestions.append("Make the reference more specific and clear")
            elif strategy == ResolutionStrategy.QUANTIFY_PRECISELY:
                suggestions.append("Replace vague quantifiers with specific numbers or ranges")
        
        # Add type-specific suggestions
        if self.ambiguity_type == AmbiguityType.UNSUPPORTED_CLAIMS:
            suggestions.append("Avoid making promises or guarantees that cannot be substantiated")
        elif self.ambiguity_type == AmbiguityType.FABRICATION_RISK:
            suggestions.append("Do not add information that is not present in the original text")
        elif self.ambiguity_type == AmbiguityType.EXCESSIVE_CERTAINTY:
            suggestions.append("Use more measured language that accurately reflects the certainty level")
        elif self.ambiguity_type == AmbiguityType.UNCLEAR_ANTECEDENT:
            suggestions.append("Replace the pronoun with the specific noun it refers to, or restructure the sentence to make the reference clear")
        elif self.ambiguity_type == AmbiguityType.UNCLEAR_SUBJECT:
            suggestions.append("Replace the pronoun with the specific noun it refers to, or restructure the sentence to make the reference clear")
        
        return suggestions


# Configuration data structures
@dataclass
class AmbiguityPattern:
    """Pattern for detecting specific ambiguity types."""
    
    name: str
    ambiguity_type: AmbiguityType
    category: AmbiguityCategory
    linguistic_pattern: str
    spacy_dependencies: List[str]
    context_required: bool = True
    confidence_threshold: float = 0.7
    
    # Resolution configuration
    resolution_strategies: Optional[List[ResolutionStrategy]] = None
    ai_instructions: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.resolution_strategies is None:
            self.resolution_strategies = []
        if self.ai_instructions is None:
            self.ai_instructions = []


class AmbiguityConfig:
    """Configuration for ambiguity detection system."""
    
    def __init__(self):
        self.patterns: Dict[str, AmbiguityPattern] = {}
        self.severity_mappings: Dict[AmbiguityType, AmbiguitySeverity] = {}
        self.category_mappings: Dict[AmbiguityType, AmbiguityCategory] = {}
        self.enabled_types: Set[AmbiguityType] = set()
        
        # Default configuration
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialize default configuration."""
        # Default severity mappings
        self.severity_mappings = {
            AmbiguityType.MISSING_ACTOR: AmbiguitySeverity.HIGH,
            AmbiguityType.AMBIGUOUS_PRONOUN: AmbiguitySeverity.MEDIUM,
            AmbiguityType.UNCLEAR_ANTECEDENT: AmbiguitySeverity.MEDIUM,
            AmbiguityType.UNCLEAR_SUBJECT: AmbiguitySeverity.MEDIUM,
            AmbiguityType.AMBIGUOUS_MODIFIER: AmbiguitySeverity.LOW,
            AmbiguityType.VAGUE_QUANTIFIER: AmbiguitySeverity.LOW,
            AmbiguityType.UNCLEAR_TEMPORAL: AmbiguitySeverity.MEDIUM,
            AmbiguityType.UNSUPPORTED_CLAIMS: AmbiguitySeverity.CRITICAL,
            AmbiguityType.FABRICATION_RISK: AmbiguitySeverity.CRITICAL,
            AmbiguityType.EXCESSIVE_CERTAINTY: AmbiguitySeverity.HIGH
        }
        
        # Default category mappings
        self.category_mappings = {
            AmbiguityType.MISSING_ACTOR: AmbiguityCategory.REFERENTIAL,
            AmbiguityType.AMBIGUOUS_PRONOUN: AmbiguityCategory.REFERENTIAL,
            AmbiguityType.UNCLEAR_ANTECEDENT: AmbiguityCategory.REFERENTIAL,
            AmbiguityType.UNCLEAR_SUBJECT: AmbiguityCategory.REFERENTIAL,
            AmbiguityType.AMBIGUOUS_MODIFIER: AmbiguityCategory.STRUCTURAL,
            AmbiguityType.VAGUE_QUANTIFIER: AmbiguityCategory.SEMANTIC,
            AmbiguityType.UNCLEAR_TEMPORAL: AmbiguityCategory.TEMPORAL,
            AmbiguityType.UNSUPPORTED_CLAIMS: AmbiguityCategory.SEMANTIC,
            AmbiguityType.FABRICATION_RISK: AmbiguityCategory.SEMANTIC,
            AmbiguityType.EXCESSIVE_CERTAINTY: AmbiguityCategory.SEMANTIC
        }
        
        # Enable all types by default
        self.enabled_types = set(AmbiguityType)
    
    def add_pattern(self, pattern: AmbiguityPattern):
        """Add a new ambiguity pattern."""
        self.patterns[pattern.name] = pattern
    
    def get_severity(self, ambiguity_type: AmbiguityType) -> AmbiguitySeverity:
        """Get severity for ambiguity type."""
        return self.severity_mappings.get(ambiguity_type, AmbiguitySeverity.MEDIUM)
    
    def get_category(self, ambiguity_type: AmbiguityType) -> AmbiguityCategory:
        """Get category for ambiguity type."""
        return self.category_mappings.get(ambiguity_type, AmbiguityCategory.SEMANTIC)
    
    def is_enabled(self, ambiguity_type: AmbiguityType) -> bool:
        """Check if ambiguity type is enabled."""
        return ambiguity_type in self.enabled_types 