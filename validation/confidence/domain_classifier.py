"""
DomainClassifier Class
Content type classification and domain identification for confidence adjustment.
Provides intelligent domain-aware confidence modifiers based on content analysis.
"""

import re
import time
import math
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from collections import Counter, defaultdict


@dataclass
class ContentTypeScore:
    """Represents content type classification scores."""
    
    content_type: str        # 'technical', 'narrative', 'procedural'
    confidence: float        # Confidence in this classification (0-1)
    indicators: List[str]    # Evidence that led to this classification
    score_breakdown: Dict[str, float]  # Detailed scoring components


@dataclass
class DomainIdentification:
    """Represents subject domain identification."""
    
    primary_domain: str      # Main domain (e.g., 'programming', 'medical', 'legal')
    confidence: float        # Confidence in domain identification (0-1)
    secondary_domains: List[Tuple[str, float]]  # Other possible domains with scores
    domain_indicators: List[str]  # Keywords/patterns that indicate this domain
    domain_coherence: float  # How consistent the domain signals are (0-1)


@dataclass
class FormalityAssessment:
    """Represents formality level assessment."""
    
    formality_level: str     # 'formal', 'informal', 'neutral'
    formality_score: float   # Numerical formality score (0-1, higher = more formal)
    formal_indicators: List[str]    # Evidence of formal language
    informal_indicators: List[str]  # Evidence of informal language
    consistency: float       # How consistent the formality level is (0-1)


@dataclass
class DomainAnalysis:
    """Complete domain analysis result."""
    
    text: str                # Original text analyzed
    
    # Core classifications
    content_type: ContentTypeScore
    domain_identification: DomainIdentification
    formality_assessment: FormalityAssessment
    
    # Confidence modifiers
    domain_confidence_modifier: float  # Overall modifier based on domain analysis
    content_type_modifier: float       # Modifier based on content type
    formality_modifier: float          # Modifier based on formality level
    
    # Meta-analysis
    classification_confidence: float   # Overall confidence in classifications
    mixed_content_detected: bool       # Whether content appears to be mixed-domain
    
    # Performance and metadata
    processing_time: float             # Time taken for analysis
    explanation: str                   # Human-readable explanation


class DomainClassifier:
    """
    Content type and domain classification system for confidence adjustment.
    
    Analyzes text to determine content type (technical, narrative, procedural),
    subject domain (programming, medical, legal, etc.), and formality level
    to provide domain-specific confidence modifiers.
    """
    
    def __init__(self, cache_classifications: bool = True):
        """
        Initialize the DomainClassifier.
        
        Args:
            cache_classifications: Whether to cache classification results
        """
        self.cache_classifications = cache_classifications
        
        # Classification caches
        self._classification_cache: Dict[str, DomainAnalysis] = {}
        
        # Load classification patterns and indicators
        self._content_type_patterns = self._load_content_type_patterns()
        self._domain_indicators = self._load_domain_indicators()
        self._formality_patterns = self._load_formality_patterns()
        
        # Performance tracking
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _load_content_type_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns for content type classification."""
        return {
            'technical': {
                'keywords': [
                    'api', 'algorithm', 'function', 'variable', 'database', 'server',
                    'configuration', 'implementation', 'architecture', 'framework',
                    'protocol', 'interface', 'module', 'library', 'dependency',
                    'deployment', 'infrastructure', 'repository', 'authentication',
                    'optimization', 'performance', 'scalability', 'integration'
                ],
                'patterns': [
                    r'\b(?:HTTP|JSON|XML|API|SQL|CSS|HTML|JavaScript|Python|Java)\b',
                    r'\b\w+\.\w+\.\w+\b',  # Package/module notation
                    r'\b(?:class|function|method|object|property)\b',
                    r'`[^`]+`',  # Code snippets
                    r'\$\w+',   # Variables
                    r'--?\w+',  # Command line flags
                ],
                'formality_weight': 0.8,
                'typical_domains': ['programming', 'networking', 'security', 'data_science']
            },
            'narrative': {
                'keywords': [
                    'story', 'character', 'plot', 'chapter', 'scene', 'dialogue',
                    'narrative', 'protagonist', 'antagonist', 'theme', 'setting',
                    'metaphor', 'symbolism', 'irony', 'conflict', 'resolution',
                    'experience', 'journey', 'adventure', 'relationship', 'emotion'
                ],
                'patterns': [
                    r'\b(?:once upon a time|in the beginning|long ago)\b',
                    r'\b(?:he said|she said|they said)\b',
                    r'\b(?:first person|third person)\b',
                    r'"[^"]*"',  # Dialogue
                    r'\b(?:chapter|episode|part)\s+\d+\b',
                ],
                'formality_weight': 0.4,
                'typical_domains': ['literature', 'entertainment', 'personal', 'creative']
            },
            'procedural': {
                'keywords': [
                    'step', 'procedure', 'process', 'instruction', 'guide', 'tutorial',
                    'method', 'approach', 'technique', 'protocol', 'workflow',
                    'checklist', 'requirement', 'prerequisite', 'guideline',
                    'first', 'next', 'then', 'finally', 'before', 'after'
                ],
                'patterns': [
                    r'\b(?:step|phase|stage)\s+\d+\b',
                    r'\b(?:first|second|third|fourth|fifth|next|then|finally)\b',
                    r'^\s*\d+\.\s',  # Numbered lists
                    r'^\s*[a-z]\)\s',  # Lettered lists
                    r'\b(?:install|configure|setup|run|execute|perform)\b',
                ],
                'formality_weight': 0.6,
                'typical_domains': ['documentation', 'training', 'manual', 'tutorial']
            }
        }
    
    def _load_domain_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Load indicators for domain identification."""
        return {
            'programming': {
                'keywords': [
                    'code', 'programming', 'software', 'developer', 'algorithm',
                    'debug', 'compile', 'syntax', 'runtime', 'framework',
                    'repository', 'commit', 'branch', 'merge', 'deployment'
                ],
                'patterns': [
                    r'\b(?:git|github|gitlab|npm|pip|maven|gradle)\b',
                    r'\b(?:javascript|python|java|c\+\+|c#|php|ruby|go|rust)\b',
                    r'\b(?:react|angular|vue|django|flask|spring|laravel)\b',
                    r'(?:def|function|class|import|from|return|if|else|for|while)\s',
                ],
                'confidence_modifier': 0.05
            },
            'medical': {
                'keywords': [
                    'patient', 'diagnosis', 'treatment', 'symptom', 'disease',
                    'medical', 'clinical', 'therapy', 'medication', 'prescription',
                    'doctor', 'physician', 'nurse', 'hospital', 'clinic'
                ],
                'patterns': [
                    r'\b(?:mg|ml|mcg|units?)\b',  # Medical units
                    r'\b[A-Z]{2,}-\d+\b',  # Medical codes
                    r'\b(?:syndrome|disorder|condition|pathology)\b',
                ],
                'confidence_modifier': -0.02  # Medical content often needs precision
            },
            'legal': {
                'keywords': [
                    'law', 'legal', 'court', 'judge', 'attorney', 'lawyer',
                    'contract', 'agreement', 'clause', 'statute', 'regulation',
                    'compliance', 'liability', 'defendant', 'plaintiff', 'evidence'
                ],
                'patterns': [
                    r'\b(?:section|subsection|paragraph|clause)\s+\d+\b',
                    r'\b(?:whereas|therefore|notwithstanding|pursuant to)\b',
                    r'\b(?:shall|must|may not|is required to)\b',
                ],
                'confidence_modifier': -0.05  # Legal content requires high precision
            },
            'business': {
                'keywords': [
                    'business', 'company', 'corporation', 'enterprise', 'organization',
                    'strategy', 'market', 'customer', 'revenue', 'profit',
                    'management', 'executive', 'department', 'stakeholder', 'roi'
                ],
                'patterns': [
                    r'\b(?:ceo|cfo|cto|vp|director|manager)\b',
                    r'\b(?:kpi|roi|b2b|b2c|saas|enterprise)\b',
                    r'\$[\d,]+(?:\.\d{2})?\b',  # Currency amounts
                ],
                'confidence_modifier': 0.03
            },
            'academic': {
                'keywords': [
                    'research', 'study', 'analysis', 'methodology', 'hypothesis',
                    'experiment', 'data', 'results', 'conclusion', 'literature',
                    'theory', 'model', 'framework', 'peer-review', 'publication'
                ],
                'patterns': [
                    r'\b(?:et al\.|ibid\.|cf\.|e\.g\.|i\.e\.)\b',
                    r'\[[^\]]*\d{4}[^\]]*\]',  # Citations
                    r'\b(?:statistical|significant|correlation|regression)\b',
                ],
                'confidence_modifier': 0.02
            },
            'creative': {
                'keywords': [
                    'creative', 'artistic', 'design', 'aesthetic', 'visual',
                    'creative', 'inspiration', 'imagination', 'expression', 'style',
                    'color', 'composition', 'texture', 'harmony', 'contrast'
                ],
                'patterns': [
                    r'\b(?:rgb|cmyk|hex|color|palette)\b',
                    r'\b(?:font|typography|layout|composition|design)\b',
                ],
                'confidence_modifier': 0.01
            }
        }
    
    def _load_formality_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns for formality assessment."""
        return {
            'formal': {
                'indicators': [
                    'furthermore', 'moreover', 'nevertheless', 'consequently',
                    'therefore', 'however', 'subsequently', 'accordingly',
                    'demonstrate', 'indicate', 'establish', 'constitute',
                    'facilitate', 'utilize', 'implement', 'methodology'
                ],
                'patterns': [
                    r'\b(?:it is|there is|there are)\b',
                    r'\b(?:one may|one can|one should)\b',
                    r'\b(?:research indicates|studies show|evidence suggests)\b',
                    r'\b(?:in conclusion|to summarize|in summary)\b',
                ],
                'contractions_penalty': -0.3,
                'passive_voice_bonus': 0.2
            },
            'informal': {
                'indicators': [
                    'yeah', 'ok', 'okay', 'cool', 'awesome', 'great',
                    'stuff', 'things', 'kinda', 'sorta', 'gonna', 'wanna',
                    'really', 'pretty', 'super', 'totally', 'basically'
                ],
                'patterns': [
                    r"\b(?:don't|won't|can't|shouldn't|wouldn't|couldn't)\b",
                    r'\b(?:lol|omg|btw|fyi|asap)\b',
                    r'[!]{2,}',  # Multiple exclamation marks
                    r'[?]{2,}',  # Multiple question marks
                ],
                'contractions_bonus': 0.3,
                'exclamation_bonus': 0.1
            }
        }
    
    def classify_content(self, text: str) -> DomainAnalysis:
        """
        Perform complete domain classification on text.
        
        Args:
            text: The text to classify
            
        Returns:
            Complete domain analysis with classifications and confidence modifiers
        """
        start_time = time.time()
        
        # Check cache first
        text_hash = hash(text)
        cache_key = str(text_hash)
        
        if self.cache_classifications and cache_key in self._classification_cache:
            self._cache_hits += 1
            return self._classification_cache[cache_key]
        
        self._cache_misses += 1
        
        # Perform core classifications
        content_type = self._classify_content_type(text)
        domain_identification = self._identify_domain(text)
        formality_assessment = self._assess_formality(text)
        
        # Calculate confidence modifiers
        modifiers = self._calculate_confidence_modifiers(
            content_type, domain_identification, formality_assessment
        )
        
        # Detect mixed content
        mixed_content = self._detect_mixed_content(content_type, domain_identification)
        
        # Calculate overall classification confidence
        classification_confidence = self._calculate_classification_confidence(
            content_type, domain_identification, formality_assessment
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            content_type, domain_identification, formality_assessment, modifiers
        )
        
        # Create analysis result
        processing_time = time.time() - start_time
        analysis = DomainAnalysis(
            text=text,
            content_type=content_type,
            domain_identification=domain_identification,
            formality_assessment=formality_assessment,
            domain_confidence_modifier=modifiers['domain'],
            content_type_modifier=modifiers['content_type'],
            formality_modifier=modifiers['formality'],
            classification_confidence=classification_confidence,
            mixed_content_detected=mixed_content,
            processing_time=processing_time,
            explanation=explanation
        )
        
        # Cache result
        if self.cache_classifications:
            self._classification_cache[cache_key] = analysis
        
        return analysis
    
    def _classify_content_type(self, text: str) -> ContentTypeScore:
        """Classify the content type of the text."""
        text_lower = text.lower()
        type_scores = {}
        
        for content_type, patterns in self._content_type_patterns.items():
            score = 0.0
            indicators = []
            score_breakdown = {}
            
            # Keyword scoring
            keyword_score = 0.0
            for keyword in patterns['keywords']:
                if keyword in text_lower:
                    keyword_score += 1
                    indicators.append(f"keyword: {keyword}")
            
            keyword_score = min(keyword_score / len(patterns['keywords']), 1.0)
            score_breakdown['keywords'] = keyword_score
            
            # Pattern scoring
            pattern_score = 0.0
            for pattern in patterns['patterns']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    pattern_score += len(matches) * 0.1
                    indicators.append(f"pattern: {pattern[:20]}...")
            
            pattern_score = min(pattern_score, 1.0)
            score_breakdown['patterns'] = pattern_score
            
            # Calculate total score
            score = (keyword_score * 0.6) + (pattern_score * 0.4)
            type_scores[content_type] = {
                'score': score,
                'indicators': indicators,
                'breakdown': score_breakdown
            }
        
        # Find best classification
        best_type = max(type_scores.keys(), key=lambda k: type_scores[k]['score'])
        best_score = type_scores[best_type]['score']
        
        # Convert score to confidence (0-1)
        confidence = min(best_score * 1.2, 1.0)  # Boost slightly
        
        return ContentTypeScore(
            content_type=best_type,
            confidence=confidence,
            indicators=type_scores[best_type]['indicators'][:5],  # Top 5 indicators
            score_breakdown=type_scores[best_type]['breakdown']
        )
    
    def _identify_domain(self, text: str) -> DomainIdentification:
        """Identify the subject domain of the text."""
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, indicators in self._domain_indicators.items():
            score = 0.0
            found_indicators = []
            
            # Keyword scoring
            for keyword in indicators['keywords']:
                if keyword in text_lower:
                    score += 0.1
                    found_indicators.append(f"keyword: {keyword}")
            
            # Pattern scoring
            for pattern in indicators['patterns']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    score += len(matches) * 0.05
                    found_indicators.append(f"pattern: {pattern[:15]}...")
            
            domain_scores[domain] = {
                'score': score,
                'indicators': found_indicators
            }
        
        # Sort domains by score
        sorted_domains = sorted(domain_scores.items(), 
                              key=lambda x: x[1]['score'], reverse=True)
        
        if not sorted_domains or sorted_domains[0][1]['score'] == 0:
            # No clear domain identified
            return DomainIdentification(
                primary_domain='general',
                confidence=0.3,
                secondary_domains=[],
                domain_indicators=[],
                domain_coherence=0.5
            )
        
        primary_domain = sorted_domains[0][0]
        primary_score = sorted_domains[0][1]['score']
        
        # Calculate confidence and coherence
        confidence = min(primary_score / 2.0, 1.0)  # Scale down for realism
        
        # Secondary domains
        secondary_domains = [(domain, data['score']) 
                           for domain, data in sorted_domains[1:3]
                           if data['score'] > 0.1]
        
        # Domain coherence (how much primary dominates)
        total_score = sum(data['score'] for _, data in sorted_domains)
        coherence = primary_score / max(total_score, 0.1) if total_score > 0 else 0.5
        
        return DomainIdentification(
            primary_domain=primary_domain,
            confidence=confidence,
            secondary_domains=secondary_domains,
            domain_indicators=domain_scores[primary_domain]['indicators'][:5],
            domain_coherence=coherence
        )
    
    def _assess_formality(self, text: str) -> FormalityAssessment:
        """Assess the formality level of the text."""
        text_lower = text.lower()
        
        formal_score = 0.0
        informal_score = 0.0
        formal_indicators = []
        informal_indicators = []
        
        # Check formal patterns
        formal_patterns = self._formality_patterns['formal']
        for indicator in formal_patterns['indicators']:
            if indicator in text_lower:
                formal_score += 0.1
                formal_indicators.append(f"formal: {indicator}")
        
        for pattern in formal_patterns['patterns']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                formal_score += len(matches) * 0.05
                formal_indicators.append(f"formal pattern: {pattern[:15]}...")
        
        # Check informal patterns
        informal_patterns = self._formality_patterns['informal']
        for indicator in informal_patterns['indicators']:
            if indicator in text_lower:
                informal_score += 0.1
                informal_indicators.append(f"informal: {indicator}")
        
        for pattern in informal_patterns['patterns']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                informal_score += len(matches) * 0.05
                informal_indicators.append(f"informal pattern: {pattern[:15]}...")
        
        # Additional formality indicators
        # Sentence length (longer sentences tend to be more formal)
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / max(len(sentences), 1)
        if avg_sentence_length > 20:
            formal_score += 0.1
            formal_indicators.append("long sentences")
        elif avg_sentence_length < 10:
            informal_score += 0.05
            informal_indicators.append("short sentences")
        
        # Contractions (informal)
        contractions = len(re.findall(r"\b\w+'\w+\b", text))
        if contractions > 0:
            informal_score += contractions * 0.05
            informal_indicators.append(f"{contractions} contractions")
        
        # Calculate formality score and level
        total_score = formal_score + informal_score
        if total_score > 0:
            formality_score = formal_score / total_score
        else:
            formality_score = 0.5  # Neutral
        
        # Determine formality level
        if formality_score > 0.65:
            formality_level = 'formal'
        elif formality_score < 0.35:
            formality_level = 'informal'
        else:
            formality_level = 'neutral'
        
        # Calculate consistency (how clear the formality signal is)
        consistency = abs(formality_score - 0.5) * 2  # 0 = mixed, 1 = very clear
        
        return FormalityAssessment(
            formality_level=formality_level,
            formality_score=formality_score,
            formal_indicators=formal_indicators[:5],
            informal_indicators=informal_indicators[:5],
            consistency=consistency
        )
    
    def _calculate_confidence_modifiers(self, content_type: ContentTypeScore,
                                      domain: DomainIdentification,
                                      formality: FormalityAssessment) -> Dict[str, float]:
        """Calculate confidence modifiers based on classifications."""
        
        # Domain-based modifier
        domain_modifier = 0.0
        if domain.primary_domain in self._domain_indicators:
            base_modifier = self._domain_indicators[domain.primary_domain].get('confidence_modifier', 0.0)
            domain_modifier = base_modifier * domain.confidence * domain.domain_coherence
        
        # Content type modifier
        content_type_modifier = 0.0
        if content_type.content_type == 'technical':
            content_type_modifier = 0.03 * content_type.confidence  # Technical content is often precise
        elif content_type.content_type == 'procedural':
            content_type_modifier = 0.02 * content_type.confidence  # Procedural content is structured
        elif content_type.content_type == 'narrative':
            content_type_modifier = -0.01 * content_type.confidence  # Narrative allows more flexibility
        
        # Formality modifier
        formality_modifier = 0.0
        if formality.formality_level == 'formal':
            formality_modifier = 0.02 * formality.consistency
        elif formality.formality_level == 'informal':
            formality_modifier = -0.02 * formality.consistency
        
        return {
            'domain': domain_modifier,
            'content_type': content_type_modifier,
            'formality': formality_modifier
        }
    
    def _detect_mixed_content(self, content_type: ContentTypeScore, 
                            domain: DomainIdentification) -> bool:
        """Detect if content appears to be mixed-domain."""
        # Mixed content indicators:
        # 1. Low confidence in primary classifications
        # 2. Multiple domains with similar scores
        # 3. Low domain coherence
        
        low_content_confidence = content_type.confidence < 0.6
        low_domain_confidence = domain.confidence < 0.5
        low_domain_coherence = domain.domain_coherence < 0.6
        multiple_domains = len(domain.secondary_domains) >= 2
        
        return (low_content_confidence and low_domain_confidence) or \
               (low_domain_coherence and multiple_domains)
    
    def _calculate_classification_confidence(self, content_type: ContentTypeScore,
                                           domain: DomainIdentification,
                                           formality: FormalityAssessment) -> float:
        """Calculate overall confidence in the classifications."""
        # Weighted average of individual confidences
        weights = {
            'content_type': 0.4,
            'domain': 0.35,
            'formality': 0.25
        }
        
        overall_confidence = (
            content_type.confidence * weights['content_type'] +
            domain.confidence * weights['domain'] +
            formality.consistency * weights['formality']
        )
        
        return min(overall_confidence, 1.0)
    
    def _generate_explanation(self, content_type: ContentTypeScore,
                            domain: DomainIdentification,
                            formality: FormalityAssessment,
                            modifiers: Dict[str, float]) -> str:
        """Generate human-readable explanation of the classification."""
        parts = []
        
        # Overall modifier effect
        total_modifier = sum(modifiers.values())
        if abs(total_modifier) > 0.01:
            if total_modifier > 0:
                parts.append(f"🔼 Domain analysis increased confidence by {total_modifier:+.3f}")
            else:
                parts.append(f"🔽 Domain analysis decreased confidence by {total_modifier:+.3f}")
        else:
            parts.append(f"➡️ Domain analysis had minimal effect ({total_modifier:+.3f})")
        
        # Content type classification
        parts.append(f"\n📄 Content Type: {content_type.content_type.title()} (confidence: {content_type.confidence:.2f})")
        if content_type.indicators:
            parts.append(f"   Evidence: {', '.join(content_type.indicators[:3])}")
        if abs(modifiers['content_type']) > 0.005:
            parts.append(f"   Effect: {modifiers['content_type']:+.3f}")
        
        # Domain identification
        parts.append(f"\n🏷️ Primary Domain: {domain.primary_domain.replace('_', ' ').title()} (confidence: {domain.confidence:.2f})")
        if domain.domain_coherence < 0.7:
            parts.append(f"   ⚠️ Mixed domain signals detected (coherence: {domain.domain_coherence:.2f})")
        if domain.secondary_domains:
            secondary = ', '.join([f"{d.replace('_', ' ').title()} ({s:.2f})" 
                                 for d, s in domain.secondary_domains[:2]])
            parts.append(f"   Alternative domains: {secondary}")
        if abs(modifiers['domain']) > 0.005:
            parts.append(f"   Effect: {modifiers['domain']:+.3f}")
        
        # Formality assessment
        parts.append(f"\n🎩 Formality: {formality.formality_level.title()} (score: {formality.formality_score:.2f})")
        if formality.consistency < 0.5:
            parts.append(f"   ⚠️ Mixed formality signals (consistency: {formality.consistency:.2f})")
        if formality.formal_indicators and formality.formality_level == 'formal':
            parts.append(f"   Formal indicators: {', '.join(formality.formal_indicators[:3])}")
        elif formality.informal_indicators and formality.formality_level == 'informal':
            parts.append(f"   Informal indicators: {', '.join(formality.informal_indicators[:3])}")
        if abs(modifiers['formality']) > 0.005:
            parts.append(f"   Effect: {modifiers['formality']:+.3f}")
        
        return '\n'.join(parts)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / max(1, self._cache_hits + self._cache_misses),
            'classifications_cached': len(self._classification_cache),
            'content_types_supported': len(self._content_type_patterns),
            'domains_supported': len(self._domain_indicators)
        }
    
    def clear_cache(self) -> None:
        """Clear classification cache."""
        self._classification_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_supported_content_types(self) -> List[str]:
        """Get list of supported content types."""
        return list(self._content_type_patterns.keys())
    
    def get_supported_domains(self) -> List[str]:
        """Get list of supported domains."""
        return list(self._domain_indicators.keys())
    
    def get_domain_confidence_modifier(self, domain: str) -> float:
        """Get the confidence modifier for a specific domain."""
        if domain in self._domain_indicators:
            return self._domain_indicators[domain].get('confidence_modifier', 0.0)
        return 0.0