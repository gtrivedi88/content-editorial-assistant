"""
DomainValidator Class
Concrete implementation of BasePassValidator for domain-specific and audience-aware validation.
Uses domain classification to validate errors based on rule applicability, terminology usage, 
style consistency, and audience appropriateness.
"""

import time
import re
from typing import Dict, List, Tuple, Optional, Any, Set, Union
from dataclasses import dataclass
from collections import defaultdict, Counter

from ..base_validator import (
    BasePassValidator, ValidationDecision, ValidationConfidence,
    ValidationEvidence, ValidationResult, ValidationContext
)

# Import domain classification capability from confidence system
try:
    from ...confidence import DomainClassifier, DomainAnalysis
except ImportError:
    # Fallback if confidence system not available
    DomainClassifier = None
    DomainAnalysis = None


@dataclass
class RuleApplicabilityAssessment:
    """Rule applicability assessment results."""
    
    rule_type: str                      # Type of rule being assessed
    rule_name: str                      # Name of the specific rule
    domain_relevance: float             # How relevant rule is to domain (0-1)
    content_type_match: bool            # Whether rule matches content type
    audience_alignment: float           # How well rule aligns with audience (0-1)
    applicability_score: float          # Overall applicability score (0-1)
    applicability_factors: List[str]    # Factors affecting applicability
    rule_exceptions: List[str]          # Known exceptions for this domain
    confidence_modifier: float          # Modifier to apply to rule confidence


@dataclass
class TerminologyValidation:
    """Terminology usage validation results."""
    
    domain: str                         # Identified domain context
    terminology_type: str               # Type of terminology (technical, business, etc.)
    appropriateness_score: float        # How appropriate terminology is (0-1)
    precision_level: str               # Expected precision (high, medium, low)
    actual_precision: float            # Actual precision detected (0-1)
    terminology_consistency: float     # Consistency with domain expectations (0-1)
    inappropriate_terms: List[str]     # Terms inappropriate for domain
    missing_terminology: List[str]     # Expected terminology not found
    alternative_suggestions: List[str] # Better terminology alternatives


@dataclass
class StyleConsistencyCheck:
    """Style consistency within domain context."""
    
    domain_style_expectations: Dict[str, Any]  # Expected style for domain
    detected_style_features: Dict[str, Any]    # Actually detected style features
    consistency_score: float                   # Overall style consistency (0-1)
    style_violations: List[str]                # Detected style violations
    formality_alignment: float                 # Formality level alignment (0-1)
    structure_appropriateness: float           # Document structure appropriateness (0-1)
    tone_consistency: float                    # Tone consistency within domain (0-1)
    style_recommendations: List[str]           # Recommendations for improvement


@dataclass
class AudienceAppropriatenessAssessment:
    """Audience appropriateness assessment results."""
    
    target_audience: str                # Identified target audience
    content_accessibility: float       # How accessible content is (0-1)
    technical_level_match: bool         # Whether technical level matches audience
    language_complexity: str            # Complexity level (simple, moderate, complex)
    assumed_knowledge: List[str]        # Knowledge assumptions detected
    accessibility_barriers: List[str]   # Barriers to audience comprehension
    appropriateness_score: float        # Overall audience appropriateness (0-1)
    audience_recommendations: List[str] # Recommendations for audience alignment


class DomainValidator(BasePassValidator):
    """
    Domain-specific validator for multi-pass validation.
    
    This validator focuses on:
    - Rule applicability based on domain and content type
    - Terminology usage validation within domain context
    - Style consistency checking for domain-specific expectations
    - Audience appropriateness assessment
    
    It leverages domain classification to provide context-aware validation
    decisions for domain-sensitive rules and content appropriateness.
    """
    
    def __init__(self,
                 enable_domain_classification: bool = True,
                 enable_terminology_validation: bool = True,
                 enable_style_consistency: bool = True,
                 enable_audience_assessment: bool = True,
                 cache_domain_analyses: bool = True,
                 min_confidence_threshold: float = 0.60):
        """
        Initialize the domain validator.
        
        Args:
            enable_domain_classification: Whether to use domain classification
            enable_terminology_validation: Whether to validate terminology usage
            enable_style_consistency: Whether to check style consistency
            enable_audience_assessment: Whether to assess audience appropriateness
            cache_domain_analyses: Whether to cache domain analysis results
            min_confidence_threshold: Minimum confidence for decisive decisions
        """
        super().__init__(
            validator_name="domain_validator",
            min_confidence_threshold=min_confidence_threshold
        )
        
        # Configuration
        self.enable_domain_classification = enable_domain_classification
        self.enable_terminology_validation = enable_terminology_validation
        self.enable_style_consistency = enable_style_consistency
        self.enable_audience_assessment = enable_audience_assessment
        self.cache_domain_analyses = cache_domain_analyses
        
        # Initialize domain classifier if available
        self.domain_classifier = None
        if enable_domain_classification and DomainClassifier:
            try:
                self.domain_classifier = DomainClassifier(cache_classifications=cache_domain_analyses)
                print(f"✓ Initialized domain classifier for domain validation")
            except Exception as e:
                print(f"⚠️ Could not initialize domain classifier: {e}")
        
        # Analysis cache
        self._domain_cache: Dict[str, Any] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Initialize domain-specific validation rules and patterns
        self._initialize_domain_rules()
        self._initialize_terminology_patterns()
        self._initialize_style_expectations()
        self._initialize_audience_criteria()
        
        # Performance tracking
        self._analysis_times = {
            'rule_applicability': [],
            'terminology_validation': [],
            'style_consistency': [],
            'audience_assessment': []
        }
    
    def _initialize_domain_rules(self):
        """Initialize domain-specific rule applicability mappings."""
        
        # Rule applicability by domain
        self.domain_rule_applicability = {
            'technical': {
                'high_applicability': [
                    'technical_writing', 'api_documentation', 'code_comments',
                    'system_documentation', 'user_manuals', 'specifications'
                ],
                'medium_applicability': [
                    'business_writing', 'academic_writing'
                ],
                'low_applicability': [
                    'creative_writing', 'casual_communication', 'marketing_copy'
                ]
            },
            'business': {
                'high_applicability': [
                    'business_writing', 'corporate_communication', 'reports',
                    'proposals', 'professional_email', 'policy_documents'
                ],
                'medium_applicability': [
                    'general_writing', 'technical_writing', 'academic_writing'
                ],
                'low_applicability': [
                    'creative_writing', 'casual_communication', 'personal_writing'
                ]
            },
            'academic': {
                'high_applicability': [
                    'academic_writing', 'research_papers', 'scholarly_articles',
                    'thesis_writing', 'conference_papers', 'citations'
                ],
                'medium_applicability': [
                    'technical_writing', 'business_writing', 'formal_writing'
                ],
                'low_applicability': [
                    'creative_writing', 'casual_communication', 'marketing_copy'
                ]
            },
            'creative': {
                'high_applicability': [
                    'creative_writing', 'storytelling', 'narrative_writing',
                    'descriptive_writing', 'literary_writing', 'fiction'
                ],
                'medium_applicability': [
                    'marketing_copy', 'blog_writing'
                ],
                'low_applicability': [
                    'technical_writing', 'academic_writing', 'legal_writing'
                ]
            },
            'general': {
                'high_applicability': [
                    'blog_writing', 'content_writing',
                    'web_content', 'social_media', 'informal_communication'
                ],
                'medium_applicability': [
                    'business_writing', 'technical_writing', 'creative_writing'
                ],
                'low_applicability': [
                    'legal_writing', 'medical_writing', 'highly_specialized'
                ]
            }
        }
        
        # Rule type to domain relevance mapping
        self.rule_type_domain_relevance = {
            'grammar': {
                'technical': 0.9, 'business': 0.9, 'academic': 0.95,
                'creative': 0.7, 'general': 0.8
            },
            'style': {
                'technical': 0.8, 'business': 0.85, 'academic': 0.9,
                'creative': 0.95, 'general': 0.75
            },
            'terminology': {
                'technical': 0.95, 'business': 0.85, 'academic': 0.9,
                'creative': 0.5, 'general': 0.6
            },
            'tone': {
                'technical': 0.7, 'business': 0.9, 'academic': 0.8,
                'creative': 0.95, 'general': 0.8
            },
            'punctuation': {
                'technical': 0.85, 'business': 0.9, 'academic': 0.95,
                'creative': 0.8, 'general': 0.8
            },
            'formatting': {
                'technical': 0.9, 'business': 0.85, 'academic': 0.9,
                'creative': 0.6, 'general': 0.7
            }
        }
        
        # Content type to audience expectations
        self.content_type_audiences = {
            'technical': ['developers', 'engineers', 'technical_users', 'system_administrators'],
            'business': ['executives', 'managers', 'business_users', 'stakeholders'],
            'academic': ['researchers', 'students', 'scholars', 'academics'],
            'creative': ['readers', 'general_audience', 'entertainment_seekers'],
            'instructional': ['learners', 'users', 'trainees', 'practitioners'],
            'general': ['general_public', 'broad_audience', 'consumers']
        }
    
    def _initialize_terminology_patterns(self):
        """Initialize terminology validation patterns and expectations."""
        
        # Domain-specific terminology expectations
        self.domain_terminology = {
            'technical': {
                'expected_patterns': [
                    r'\b(?:API|SDK|JSON|XML|HTTP|REST|SQL|database|server|client|function|method|class|object|algorithm|implementation|configuration|deployment|architecture|framework|library|protocol|interface|authentication|authorization|encryption|security|performance|optimization|scalability|middleware|backend|frontend|repository|version|branch|commit|build|deployment|testing|debugging|logging|monitoring|metrics|analytics|documentation|specification|requirement|feature|bug|issue|patch|release|update|upgrade|migration|integration|compatibility|dependency|module|package|namespace|endpoint|parameter|response|request|status|error|exception|timeout|latency|throughput|bandwidth|capacity|load|stress|unit|integration|regression|automation|continuous|delivery|pipeline|workflow|infrastructure|cloud|container|virtual|machine|instance|cluster|node|network|firewall|load_balancer|cache|redis|mongodb|postgresql|mysql|kubernetes|docker|jenkins|github|gitlab|aws|azure|gcp)\b',
                    r'\b(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b',
                    r'\b(?:200|201|400|401|403|404|500|502|503)\b',
                    r'\b(?:\.js|\.py|\.java|\.cpp|\.cs|\.php|\.rb|\.go|\.rs|\.ts|\.html|\.css|\.sql|\.json|\.xml|\.yaml|\.yml|\.md|\.txt|\.log|\.conf|\.ini|\.env)\b'
                ],
                'precision_level': 'high',
                'formality_level': 'formal',
                'jargon_acceptable': True
            },
            'business': {
                'expected_patterns': [
                    r'\b(?:revenue|profit|loss|ROI|KPI|metric|analytics|strategy|objective|goal|target|budget|forecast|projection|quarter|fiscal|annual|growth|market|customer|client|stakeholder|shareholder|investment|funding|capital|equity|debt|asset|liability|cash_flow|income|expense|cost|pricing|margin|discount|promotion|campaign|brand|marketing|sales|lead|conversion|retention|acquisition|churn|segment|demographics|psychographics|persona|journey|experience|satisfaction|feedback|survey|analysis|report|dashboard|presentation|meeting|conference|workshop|training|development|performance|evaluation|review|assessment|improvement|optimization|efficiency|productivity|process|workflow|procedure|policy|compliance|regulation|standard|quality|assurance|control|risk|management|leadership|executive|director|manager|supervisor|team|department|division|organization|enterprise|corporation|company|business|industry|sector|vertical|horizontal|competitive|advantage|differentiation|value|proposition|offering|solution|service|product|feature|benefit)\b'
                ],
                'precision_level': 'medium',
                'formality_level': 'formal',
                'jargon_acceptable': True
            },
            'academic': {
                'expected_patterns': [
                    r'\b(?:research|study|analysis|methodology|hypothesis|theory|framework|model|paradigm|approach|method|technique|procedure|experiment|observation|data|evidence|finding|result|conclusion|implication|significance|correlation|causation|variable|sample|population|statistical|quantitative|qualitative|empirical|theoretical|literature|review|survey|meta_analysis|case_study|longitudinal|cross_sectional|randomized|controlled|trial|peer_review|publication|journal|conference|proceedings|citation|reference|bibliography|abstract|introduction|discussion|limitation|future|work|contribution|novelty|original|innovative|comprehensive|systematic|rigorous|objective|subjective|bias|validity|reliability|reproducibility|replication|generalizability|ethics|consent|institutional|review|board|funding|grant|collaboration|interdisciplinary|multidisciplinary|field|discipline|domain|expert|scholar|researcher|scientist|professor|student|graduate|undergraduate|doctoral|postdoctoral|thesis|dissertation|manuscript|paper|article|chapter|book|monograph|encyclopedia|handbook|textbook|curriculum|pedagogy|education|learning|teaching|assessment|evaluation)\b'
                ],
                'precision_level': 'high',
                'formality_level': 'formal',
                'jargon_acceptable': True
            },
            'creative': {
                'expected_patterns': [
                    r'\b(?:story|narrative|plot|character|protagonist|antagonist|setting|theme|motif|symbol|metaphor|simile|imagery|dialogue|monologue|voice|tone|mood|atmosphere|tension|conflict|resolution|climax|denouement|exposition|rising|action|falling|scene|chapter|act|stanza|verse|line|rhyme|rhythm|meter|alliteration|assonance|consonance|personification|hyperbole|irony|satire|humor|comedy|tragedy|drama|romance|mystery|thriller|horror|fantasy|science_fiction|historical|biography|autobiography|memoir|essay|poem|sonnet|haiku|short_story|novel|novella|play|screenplay|script|adaptation|inspiration|creativity|imagination|expression|emotion|feeling|passion|beauty|aesthetic|artistic|literary|poetic|prose|fiction|non_fiction|genre|style|technique|craft|workshop|draft|revision|editing|publishing|audience|reader|viewer|critique|review|feedback|award|prize|recognition|legacy|influence|tradition|canon|classic|contemporary|modern|postmodern)\b'
                ],
                'precision_level': 'medium',
                'formality_level': 'varied',
                'jargon_acceptable': False
            },
            'general': {
                'expected_patterns': [
                    r'\b(?:information|content|article|blog|post|news|update|announcement|notice|guide|tutorial|instruction|help|support|service|product|feature|benefit|advantage|solution|problem|issue|question|answer|explanation|description|overview|summary|detail|example|illustration|demonstration|step|process|procedure|method|way|approach|technique|tip|advice|recommendation|suggestion|idea|concept|topic|subject|matter|point|aspect|factor|element|component|part|section|chapter|paragraph|sentence|word|phrase|term|definition|meaning|purpose|goal|objective|target|result|outcome|effect|impact|influence|change|improvement|development|progress|success|failure|challenge|opportunity|trend|pattern|comparison|contrast|similarity|difference|relationship|connection|link|association|correlation|cause|reason|explanation|justification|evidence|proof|support|argument|claim|statement|opinion|view|perspective|position|stance|belief|assumption|expectation|requirement|need|want|desire|preference|choice|option|alternative|possibility|probability|likelihood|chance|risk|benefit|cost|value|price|quality|quantity|amount|number|percentage|ratio|rate|level|degree|extent|range|scope|scale|size|magnitude|importance|significance|relevance|priority|urgency|time|date|period|duration|frequency|occasion|event|situation|circumstance|condition|context|environment|background|history|future|past|present|current|recent|latest|new|old|original|final|complete|partial|full|empty|total|overall|general|specific|particular|individual|personal|private|public|official|formal|informal|simple|complex|easy|difficult|hard|soft|strong|weak|good|bad|positive|negative|true|false|correct|wrong|right|left|up|down|high|low|big|small|large|tiny|major|minor|main|secondary|primary|first|last|next|previous|best|worst|better|worse|more|less|most|least|all|none|some|many|few|several|various|different|same|similar|equal|unequal|greater|smaller|higher|lower|faster|slower|earlier|later|before|after|during|while|since|until|through|across|over|under|above|below|inside|outside|within|beyond|around|near|far|close|distant|local|global|national|international|regional|urban|rural|indoor|outdoor|online|offline|digital|analog|virtual|real|actual|potential|possible|impossible|probable|improbable|certain|uncertain|sure|unsure)\b'
                ],
                'precision_level': 'low',
                'formality_level': 'varied',
                'jargon_acceptable': False
            }
        }
        
        # Inappropriate terminology by domain
        self.inappropriate_terminology = {
            'technical': {
                'overly_casual': ['awesome', 'cool', 'neat', 'sweet', 'sick', 'dope', 'lit', 'fire'],
                'vague_terms': ['thing', 'stuff', 'whatever', 'somehow', 'kinda', 'sorta'],
                'business_jargon': ['synergy', 'leverage', 'paradigm shift', 'low-hanging fruit']
            },
            'business': {
                'overly_technical': ['algorithm', 'API', 'JSON', 'SQL', 'regex', 'compilation'],
                'overly_casual': ['awesome', 'cool', 'super', 'mega', 'ultra'],
                'creative_terms': ['magical', 'enchanting', 'whimsical', 'poetic']
            },
            'academic': {
                'casual_language': ['awesome', 'cool', 'super', 'really', 'very', 'a lot'],
                'business_buzzwords': ['synergy', 'leverage', 'disrupt', 'monetize'],
                'emotional_language': ['amazing', 'incredible', 'fantastic', 'terrible']
            },
            'creative': {
                'technical_jargon': ['API', 'JSON', 'algorithm', 'implementation', 'optimization'],
                'business_terms': ['ROI', 'KPI', 'stakeholder', 'deliverable', 'actionable'],
                'overly_formal': ['utilize', 'facilitate', 'demonstrate', 'implement']
            }
        }
    
    def _initialize_style_expectations(self):
        """Initialize domain-specific style expectations."""
        
        self.domain_style_expectations = {
            'technical': {
                'sentence_length': {'preferred': (10, 25), 'max_acceptable': 35},
                'paragraph_length': {'preferred': (3, 8), 'max_acceptable': 12},
                'formality_level': 'formal',
                'tone': 'objective',
                'structure': 'logical',
                'voice': 'active_preferred',
                'terminology_precision': 'high',
                'examples_expected': True,
                'code_formatting': True,
                'headings_structured': True
            },
            'business': {
                'sentence_length': {'preferred': (15, 30), 'max_acceptable': 40},
                'paragraph_length': {'preferred': (4, 10), 'max_acceptable': 15},
                'formality_level': 'formal',
                'tone': 'professional',
                'structure': 'hierarchical',
                'voice': 'active_preferred',
                'terminology_precision': 'medium',
                'examples_expected': True,
                'bullet_points': True,
                'executive_summary': True
            },
            'academic': {
                'sentence_length': {'preferred': (20, 35), 'max_acceptable': 50},
                'paragraph_length': {'preferred': (5, 12), 'max_acceptable': 20},
                'formality_level': 'formal',
                'tone': 'objective',
                'structure': 'systematic',
                'voice': 'varied',
                'terminology_precision': 'high',
                'citations_expected': True,
                'methodology_section': True,
                'literature_review': True
            },
            'creative': {
                'sentence_length': {'preferred': (8, 40), 'max_acceptable': 60},
                'paragraph_length': {'preferred': (2, 15), 'max_acceptable': 25},
                'formality_level': 'varied',
                'tone': 'expressive',
                'structure': 'narrative',
                'voice': 'varied',
                'terminology_precision': 'medium',
                'descriptive_language': True,
                'dialogue_acceptable': True,
                'emotional_expression': True
            },
            'general': {
                'sentence_length': {'preferred': (12, 25), 'max_acceptable': 30},
                'paragraph_length': {'preferred': (3, 8), 'max_acceptable': 12},
                'formality_level': 'neutral',
                'tone': 'conversational',
                'structure': 'clear',
                'voice': 'active_preferred',
                'terminology_precision': 'medium',
                'accessibility': True,
                'readability': True,
                'engagement': True
            }
        }
    
    def _initialize_audience_criteria(self):
        """Initialize audience-specific criteria and expectations."""
        
        self.audience_criteria = {
            'developers': {
                'technical_level': 'high',
                'assumed_knowledge': ['programming', 'software_development', 'technical_concepts'],
                'preferred_style': 'direct',
                'detail_level': 'high',
                'examples': 'code_samples',
                'documentation_format': 'structured'
            },
            'business_users': {
                'technical_level': 'low',
                'assumed_knowledge': ['business_processes', 'industry_terminology'],
                'preferred_style': 'professional',
                'detail_level': 'medium',
                'examples': 'use_cases',
                'documentation_format': 'executive'
            },
            'general_audience': {
                'technical_level': 'minimal',
                'assumed_knowledge': ['basic_literacy', 'common_knowledge'],
                'preferred_style': 'conversational',
                'detail_level': 'accessible',
                'examples': 'relatable',
                'documentation_format': 'user_friendly'
            },
            'academics': {
                'technical_level': 'high',
                'assumed_knowledge': ['research_methods', 'domain_expertise', 'scholarly_conventions'],
                'preferred_style': 'formal',
                'detail_level': 'comprehensive',
                'examples': 'peer_reviewed',
                'documentation_format': 'scholarly'
            },
            'students': {
                'technical_level': 'learning',
                'assumed_knowledge': ['foundational_concepts', 'educational_context'],
                'preferred_style': 'instructional',
                'detail_level': 'progressive',
                'examples': 'educational',
                'documentation_format': 'pedagogical'
            }
        }
        
        # Content complexity indicators
        self.complexity_indicators = {
            'simple': {
                'avg_sentence_length': (8, 15),
                'syllables_per_word': (1, 2),
                'technical_terms_ratio': (0, 0.1),
                'abstract_concepts': 'minimal'
            },
            'moderate': {
                'avg_sentence_length': (15, 25),
                'syllables_per_word': (2, 3),
                'technical_terms_ratio': (0.1, 0.3),
                'abstract_concepts': 'some'
            },
            'complex': {
                'avg_sentence_length': (25, 40),
                'syllables_per_word': (3, 4),
                'technical_terms_ratio': (0.3, 0.6),
                'abstract_concepts': 'frequent'
            },
            'highly_complex': {
                'avg_sentence_length': (40, 60),
                'syllables_per_word': (4, 6),
                'technical_terms_ratio': (0.6, 1.0),
                'abstract_concepts': 'dominant'
            }
        }
    
    def _validate_error(self, context: ValidationContext) -> ValidationResult:
        """
        Validate an error using domain-specific analysis.
        
        Args:
            context: Validation context containing error and metadata
            
        Returns:
            ValidationResult with domain-specific analysis and decision
        """
        start_time = time.time()
        
        try:
            # Get or classify domain context
            domain_analysis = self._get_domain_analysis(context.text, context.content_type)
            
            if not domain_analysis:
                return self._create_uncertain_result(
                    context,
                    "Could not determine domain context for validation",
                    time.time() - start_time
                )
            
            # Perform domain-specific analyses
            evidence = []
            
            # 1. Rule applicability assessment
            rule_applicability = self._assess_rule_applicability(domain_analysis, context)
            if rule_applicability:
                evidence.append(self._create_applicability_evidence(rule_applicability, context))
            
            # 2. Terminology validation
            if self.enable_terminology_validation:
                terminology_validation = self._validate_terminology(domain_analysis, context)
                if terminology_validation:
                    evidence.append(self._create_terminology_evidence(terminology_validation, context))
            
            # 3. Style consistency checking
            if self.enable_style_consistency:
                style_consistency = self._check_style_consistency(domain_analysis, context)
                if style_consistency:
                    evidence.append(self._create_style_evidence(style_consistency, context))
            
            # 4. Audience appropriateness assessment
            if self.enable_audience_assessment:
                audience_assessment = self._assess_audience_appropriateness(domain_analysis, context)
                if audience_assessment:
                    evidence.append(self._create_audience_evidence(audience_assessment, context))
            
            # Make validation decision based on domain evidence
            decision, confidence_score, reasoning = self._make_domain_decision(evidence, domain_analysis, context)
            
            return ValidationResult(
                validator_name=self.validator_name,
                decision=decision,
                confidence=self._convert_confidence_to_level(confidence_score),
                confidence_score=confidence_score,
                evidence=evidence,
                reasoning=reasoning,
                error_text=context.error_text,
                error_position=context.error_position,
                rule_type=context.rule_type,
                rule_name=context.rule_name,
                validation_time=time.time() - start_time,
                metadata={
                    'domain_analysis': domain_analysis.domain_identification.primary_domain if domain_analysis and hasattr(domain_analysis, 'domain_identification') else 'unknown',
                    'content_type': domain_analysis.content_type.content_type if domain_analysis and hasattr(domain_analysis, 'content_type') and hasattr(domain_analysis.content_type, 'content_type') else context.content_type,
                    'domain_evidence_count': len(evidence),
                    'rule_applicability_score': rule_applicability.applicability_score if rule_applicability else 0.0,
                    'domain_classification_used': self.domain_classifier is not None
                }
            )
            
        except Exception as e:
            return self._create_error_result(context, str(e), time.time() - start_time)
    
    def _get_domain_analysis(self, text: str, content_type: Optional[str] = None) -> Optional[Any]:
        """Get domain analysis using domain classifier or fallback methods."""
        
        # Check cache first
        cache_key = f"{text[:100]}_{content_type or 'unknown'}"
        if self.cache_domain_analyses and cache_key in self._domain_cache:
            self._cache_hits += 1
            return self._domain_cache[cache_key]
        
        self._cache_misses += 1
        
        # Use domain classifier if available
        if self.domain_classifier:
            try:
                domain_analysis = self.domain_classifier.classify_content(text)
                if self.cache_domain_analyses:
                    self._domain_cache[cache_key] = domain_analysis
                return domain_analysis
            except Exception:
                pass
        
        # Fallback to simple domain detection
        fallback_analysis = self._simple_domain_detection(text, content_type)
        if self.cache_domain_analyses:
            self._domain_cache[cache_key] = fallback_analysis
        
        return fallback_analysis
    
    def _simple_domain_detection(self, text: str, content_type: Optional[str] = None) -> Any:
        """Simple fallback domain detection when domain classifier unavailable."""
        
        # Simple pattern-based domain detection
        domain_scores = {}
        text_lower = text.lower()
        
        # Check for domain-specific patterns
        for domain, patterns in self.domain_terminology.items():
            score = 0
            for pattern in patterns['expected_patterns']:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            domain_scores[domain] = score / max(1, len(text.split()))  # Normalize by text length
        
        # Determine primary domain
        primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0] if domain_scores else 'general'
        
        # Create minimal analysis object
        class SimpleAnalysis:
            def __init__(self, domain, content_type):
                self.primary_domain = domain
                self.content_type = content_type or 'general'
                self.confidence = domain_scores.get(domain, 0.0)
        
        return SimpleAnalysis(primary_domain, content_type)
    
    def _assess_rule_applicability(self, domain_analysis: Any, context: ValidationContext) -> Optional[RuleApplicabilityAssessment]:
        """Assess how applicable a rule is to the given domain and context."""
        start_time = time.time()
        
        try:
            rule_type = context.rule_type
            rule_name = context.rule_name
            primary_domain = domain_analysis.domain_identification.primary_domain
            content_type = domain_analysis.content_type.content_type if hasattr(domain_analysis.content_type, 'content_type') else context.content_type or 'general'
            
            # Get base domain relevance for rule type
            domain_relevance = self.rule_type_domain_relevance.get(rule_type, {}).get(primary_domain, 0.5)
            
            # Check content type match
            content_type_match = self._check_content_type_match(rule_name, content_type, primary_domain)
            
            # Assess audience alignment
            audience_alignment = self._assess_audience_alignment(rule_type, rule_name, primary_domain, content_type)
            
            # Calculate overall applicability score
            applicability_score = (domain_relevance * 0.4 + 
                                 (0.8 if content_type_match else 0.2) * 0.3 +
                                 audience_alignment * 0.3)
            
            # Identify applicability factors
            applicability_factors = self._identify_applicability_factors(
                rule_type, rule_name, primary_domain, content_type, domain_relevance
            )
            
            # Check for rule exceptions
            rule_exceptions = self._get_rule_exceptions(rule_type, rule_name, primary_domain)
            
            # Calculate confidence modifier
            confidence_modifier = self._calculate_confidence_modifier(applicability_score, rule_exceptions)
            
            assessment = RuleApplicabilityAssessment(
                rule_type=rule_type,
                rule_name=rule_name,
                domain_relevance=domain_relevance,
                content_type_match=content_type_match,
                audience_alignment=audience_alignment,
                applicability_score=applicability_score,
                applicability_factors=applicability_factors,
                rule_exceptions=rule_exceptions,
                confidence_modifier=confidence_modifier
            )
            
            self._analysis_times['rule_applicability'].append(time.time() - start_time)
            return assessment
            
        except Exception:
            return None
    
    def _validate_terminology(self, domain_analysis: Any, context: ValidationContext) -> Optional[TerminologyValidation]:
        """Validate terminology usage within domain context."""
        start_time = time.time()
        
        try:
            primary_domain = domain_analysis.domain_identification.primary_domain
            error_text = context.error_text
            
            # Get domain terminology expectations
            domain_info = self.domain_terminology.get(primary_domain, self.domain_terminology['general'])
            
            # Assess terminology appropriateness
            appropriateness_score = self._assess_terminology_appropriateness(error_text, primary_domain, context.text)
            
            # Determine terminology type
            terminology_type = self._classify_terminology_type(error_text, primary_domain)
            
            # Check precision level
            expected_precision = domain_info.get('precision_level', 'medium')
            actual_precision = self._assess_terminology_precision(error_text, context.text, primary_domain)
            
            # Check terminology consistency
            terminology_consistency = self._check_terminology_consistency(context.text, primary_domain)
            
            # Find inappropriate terms
            inappropriate_terms = self._find_inappropriate_terms(context.text, primary_domain)
            
            # Identify missing terminology
            missing_terminology = self._identify_missing_terminology(context.text, primary_domain, context.rule_type)
            
            # Generate alternative suggestions
            alternative_suggestions = self._generate_terminology_alternatives(error_text, primary_domain)
            
            validation = TerminologyValidation(
                domain=primary_domain,
                terminology_type=terminology_type,
                appropriateness_score=appropriateness_score,
                precision_level=expected_precision,
                actual_precision=actual_precision,
                terminology_consistency=terminology_consistency,
                inappropriate_terms=inappropriate_terms,
                missing_terminology=missing_terminology,
                alternative_suggestions=alternative_suggestions
            )
            
            self._analysis_times['terminology_validation'].append(time.time() - start_time)
            return validation
            
        except Exception:
            return None
    
    def _check_style_consistency(self, domain_analysis: Any, context: ValidationContext) -> Optional[StyleConsistencyCheck]:
        """Check style consistency within domain context."""
        start_time = time.time()
        
        try:
            primary_domain = domain_analysis.domain_identification.primary_domain
            
            # Get domain style expectations
            domain_expectations = self.domain_style_expectations.get(primary_domain, self.domain_style_expectations['general'])
            
            # Detect actual style features
            detected_features = self._detect_style_features(context.text)
            
            # Calculate consistency score
            consistency_score = self._calculate_style_consistency(domain_expectations, detected_features)
            
            # Identify style violations
            style_violations = self._identify_style_violations(domain_expectations, detected_features, context)
            
            # Assess formality alignment
            formality_alignment = self._assess_formality_alignment(
                domain_expectations.get('formality_level', 'neutral'),
                detected_features.get('formality_level', 'neutral')
            )
            
            # Check structure appropriateness
            structure_appropriateness = self._assess_structure_appropriateness(
                domain_expectations, detected_features, context.text
            )
            
            # Assess tone consistency
            tone_consistency = self._assess_tone_consistency(
                domain_expectations.get('tone', 'neutral'),
                detected_features.get('tone', 'neutral'),
                context.text
            )
            
            # Generate style recommendations
            style_recommendations = self._generate_style_recommendations(
                domain_expectations, detected_features, style_violations
            )
            
            check = StyleConsistencyCheck(
                domain_style_expectations=domain_expectations,
                detected_style_features=detected_features,
                consistency_score=consistency_score,
                style_violations=style_violations,
                formality_alignment=formality_alignment,
                structure_appropriateness=structure_appropriateness,
                tone_consistency=tone_consistency,
                style_recommendations=style_recommendations
            )
            
            self._analysis_times['style_consistency'].append(time.time() - start_time)
            return check
            
        except Exception:
            return None
    
    def _assess_audience_appropriateness(self, domain_analysis: Any, context: ValidationContext) -> Optional[AudienceAppropriatenessAssessment]:
        """Assess appropriateness for target audience."""
        start_time = time.time()
        
        try:
            primary_domain = domain_analysis.domain_identification.primary_domain
            content_type = domain_analysis.content_type.content_type if hasattr(domain_analysis.content_type, 'content_type') else 'general'
            
            # Determine target audience
            target_audience = self._determine_target_audience(primary_domain, content_type, context)
            
            # Assess content accessibility
            content_accessibility = self._assess_content_accessibility(context.text, target_audience)
            
            # Check technical level match
            technical_level_match = self._check_technical_level_match(context.text, target_audience)
            
            # Assess language complexity
            language_complexity = self._assess_language_complexity(context.text)
            
            # Identify assumed knowledge
            assumed_knowledge = self._identify_assumed_knowledge(context.text, primary_domain)
            
            # Find accessibility barriers
            accessibility_barriers = self._find_accessibility_barriers(context.text, target_audience)
            
            # Calculate overall appropriateness score
            appropriateness_score = self._calculate_audience_appropriateness(
                content_accessibility, technical_level_match, language_complexity, 
                assumed_knowledge, accessibility_barriers, target_audience
            )
            
            # Generate audience recommendations
            audience_recommendations = self._generate_audience_recommendations(
                target_audience, accessibility_barriers, language_complexity, assumed_knowledge
            )
            
            assessment = AudienceAppropriatenessAssessment(
                target_audience=target_audience,
                content_accessibility=content_accessibility,
                technical_level_match=technical_level_match,
                language_complexity=language_complexity,
                assumed_knowledge=assumed_knowledge,
                accessibility_barriers=accessibility_barriers,
                appropriateness_score=appropriateness_score,
                audience_recommendations=audience_recommendations
            )
            
            self._analysis_times['audience_assessment'].append(time.time() - start_time)
            return assessment
            
        except Exception:
            return None
    
    # Helper methods for rule applicability
    def _check_content_type_match(self, rule_name: str, content_type: str, domain: str) -> bool:
        """Check if rule matches the content type and domain."""
        domain_rules = self.domain_rule_applicability.get(domain, {})
        
        # Check high applicability rules
        high_applicable = domain_rules.get('high_applicability', [])
        if any(rule_type in rule_name.lower() for rule_type in high_applicable):
            return True
        
        # Check medium applicability rules
        medium_applicable = domain_rules.get('medium_applicability', [])
        if any(rule_type in rule_name.lower() for rule_type in medium_applicable):
            return True
        
        # Default to partial match for general rules
        return content_type in ['general', 'mixed'] or 'general' in rule_name.lower()
    
    def _assess_audience_alignment(self, rule_type: str, rule_name: str, domain: str, content_type: str) -> float:
        """Assess how well the rule aligns with the expected audience."""
        expected_audiences = self.content_type_audiences.get(domain, ['general_audience'])
        
        # Different rule types have different audience relevance
        audience_relevance = {
            'grammar': 0.8,      # Grammar important for all audiences
            'style': 0.9,        # Style very important for audience matching
            'terminology': 0.95,  # Terminology critical for audience
            'tone': 0.9,         # Tone very important for audience
            'punctuation': 0.7,   # Punctuation moderately important
            'formatting': 0.6     # Formatting less audience-dependent
        }
        
        base_score = audience_relevance.get(rule_type, 0.7)
        
        # Adjust based on audience sophistication
        if 'technical' in expected_audiences or 'developers' in expected_audiences:
            if rule_type in ['terminology', 'formatting']:
                base_score += 0.1
        elif 'general_audience' in expected_audiences:
            if rule_type in ['style', 'tone']:
                base_score += 0.1
        
        return min(1.0, base_score)
    
    def _identify_applicability_factors(self, rule_type: str, rule_name: str, domain: str, 
                                      content_type: str, domain_relevance: float) -> List[str]:
        """Identify factors affecting rule applicability."""
        factors = []
        
        if domain_relevance > 0.8:
            factors.append('high_domain_relevance')
        elif domain_relevance < 0.5:
            factors.append('low_domain_relevance')
        
        if rule_type == 'terminology' and domain in ['technical', 'academic']:
            factors.append('domain_specific_terminology')
        
        if rule_type == 'style' and domain in ['creative', 'business']:
            factors.append('style_critical_domain')
        
        if content_type == 'technical' and rule_type in ['grammar', 'punctuation']:
            factors.append('technical_precision_required')
        
        return factors
    
    def _get_rule_exceptions(self, rule_type: str, rule_name: str, domain: str) -> List[str]:
        """Get known exceptions for rule in specific domain."""
        exceptions = []
        
        # Domain-specific rule exceptions
        if domain == 'creative' and rule_type == 'grammar':
            exceptions.append('artistic_license_acceptable')
        
        if domain == 'technical' and rule_type == 'style':
            exceptions.append('precision_over_style')
        
        if domain == 'business' and 'casual' in rule_name.lower():
            exceptions.append('professional_tone_required')
        
        return exceptions
    
    def _calculate_confidence_modifier(self, applicability_score: float, rule_exceptions: List[str]) -> float:
        """Calculate confidence modifier based on applicability."""
        base_modifier = applicability_score
        
        # Reduce confidence if many exceptions
        if len(rule_exceptions) > 2:
            base_modifier *= 0.8
        elif len(rule_exceptions) > 0:
            base_modifier *= 0.9
        
        return base_modifier
    
    # Helper methods for terminology validation
    def _assess_terminology_appropriateness(self, error_text: str, domain: str, full_text: str) -> float:
        """Assess how appropriate terminology is for the domain."""
        inappropriate_terms = self.inappropriate_terminology.get(domain, {})
        error_lower = error_text.lower()
        
        # Check if term is inappropriate for domain
        for category, terms in inappropriate_terms.items():
            if error_lower in terms:
                return 0.2  # Very inappropriate
        
        # Check if term fits domain expectations
        domain_patterns = self.domain_terminology.get(domain, {}).get('expected_patterns', [])
        for pattern in domain_patterns:
            if re.search(pattern, error_text, re.IGNORECASE):
                return 0.9  # Very appropriate
        
        # Default moderate appropriateness
        return 0.6
    
    def _classify_terminology_type(self, error_text: str, domain: str) -> str:
        """Classify the type of terminology."""
        error_lower = error_text.lower()
        
        # Technical terminology
        if re.search(r'\b(?:API|JSON|HTTP|database|algorithm|function|method|class)\b', error_lower):
            return 'technical'
        
        # Business terminology
        if re.search(r'\b(?:ROI|KPI|revenue|strategy|stakeholder|customer)\b', error_lower):
            return 'business'
        
        # Academic terminology
        if re.search(r'\b(?:methodology|hypothesis|analysis|research|study)\b', error_lower):
            return 'academic'
        
        # General terminology
        return 'general'
    
    def _assess_terminology_precision(self, error_text: str, full_text: str, domain: str) -> float:
        """Assess the precision level of terminology."""
        expected_precision = self.domain_terminology.get(domain, {}).get('precision_level', 'medium')
        
        # Measure word specificity (longer, technical words are generally more precise)
        word_length = len(error_text)
        has_technical_suffix = error_text.endswith(('tion', 'ment', 'ness', 'ity', 'ism', 'ology'))
        
        precision_score = 0.5  # Base score
        
        if word_length > 8:
            precision_score += 0.2
        if has_technical_suffix:
            precision_score += 0.2
        if error_text.isupper():  # Acronyms are often precise
            precision_score += 0.1
        
        return min(1.0, precision_score)
    
    def _check_terminology_consistency(self, text: str, domain: str) -> float:
        """Check consistency of terminology usage throughout text."""
        # Simple consistency check: do all domain-specific terms align?
        domain_patterns = self.domain_terminology.get(domain, {}).get('expected_patterns', [])
        
        total_terms = 0
        consistent_terms = 0
        
        for pattern in domain_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            total_terms += len(matches)
            consistent_terms += len(matches)  # All matched terms are consistent by definition
        
        # Check for inconsistent terminology from other domains
        for other_domain, other_info in self.domain_terminology.items():
            if other_domain != domain:
                for pattern in other_info.get('expected_patterns', []):
                    inconsistent_matches = re.findall(pattern, text, re.IGNORECASE)
                    total_terms += len(inconsistent_matches)
                    # Don't add to consistent_terms
        
        return consistent_terms / max(1, total_terms)
    
    def _find_inappropriate_terms(self, text: str, domain: str) -> List[str]:
        """Find terms inappropriate for the domain."""
        inappropriate = []
        inappropriate_categories = self.inappropriate_terminology.get(domain, {})
        
        text_lower = text.lower()
        for category, terms in inappropriate_categories.items():
            for term in terms:
                if term in text_lower:
                    inappropriate.append(term)
        
        return inappropriate
    
    def _identify_missing_terminology(self, text: str, domain: str, rule_type: str) -> List[str]:
        """Identify expected terminology that's missing."""
        # This is a simplified implementation
        missing = []
        
        if domain == 'technical' and rule_type == 'terminology':
            # Check for missing technical terms in technical content
            if 'API' in text and 'endpoint' not in text:
                missing.append('endpoint')
            if 'database' in text and 'query' not in text:
                missing.append('query')
        
        return missing
    
    def _generate_terminology_alternatives(self, error_text: str, domain: str) -> List[str]:
        """Generate alternative terminology suggestions."""
        alternatives = []
        error_lower = error_text.lower()
        
        # Domain-specific alternatives
        if domain == 'technical':
            tech_alternatives = {
                'use': 'utilize', 'make': 'implement', 'get': 'retrieve',
                'put': 'insert', 'change': 'modify', 'fix': 'resolve'
            }
            alternatives.extend(tech_alternatives.get(error_lower, []))
        
        elif domain == 'business':
            business_alternatives = {
                'use': 'leverage', 'help': 'facilitate', 'show': 'demonstrate',
                'get': 'acquire', 'make': 'develop', 'do': 'execute'
            }
            alternatives.extend(business_alternatives.get(error_lower, []))
        
        return alternatives
    
    # Helper methods for style consistency
    def _detect_style_features(self, text: str) -> Dict[str, Any]:
        """Detect actual style features in the text."""
        sentences = text.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Calculate sentence length statistics
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_sentence_length = sum(sentence_lengths) / max(1, len(sentence_lengths))
        
        # Calculate paragraph statistics (simplified)
        paragraphs = text.split('\n\n')
        paragraph_lengths = [len(p.split('.')) for p in paragraphs if p.strip()]
        avg_paragraph_length = sum(paragraph_lengths) / max(1, len(paragraph_lengths))
        
        # Detect formality level
        formal_indicators = len(re.findall(r'\b(?:utilize|demonstrate|facilitate|implement|establish)\b', text, re.IGNORECASE))
        informal_indicators = len(re.findall(r'\b(?:use|show|help|do|make|get|put)\b', text, re.IGNORECASE))
        
        if formal_indicators > informal_indicators:
            formality_level = 'formal'
        elif informal_indicators > formal_indicators * 2:
            formality_level = 'informal'
        else:
            formality_level = 'neutral'
        
        # Detect tone (simplified)
        positive_words = len(re.findall(r'\b(?:excellent|great|good|effective|successful)\b', text, re.IGNORECASE))
        negative_words = len(re.findall(r'\b(?:poor|bad|ineffective|failed|problematic)\b', text, re.IGNORECASE))
        
        if positive_words > negative_words:
            tone = 'positive'
        elif negative_words > positive_words:
            tone = 'negative'
        else:
            tone = 'neutral'
        
        return {
            'avg_sentence_length': avg_sentence_length,
            'avg_paragraph_length': avg_paragraph_length,
            'formality_level': formality_level,
            'tone': tone,
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs)
        }
    
    def _calculate_style_consistency(self, expectations: Dict[str, Any], features: Dict[str, Any]) -> float:
        """Calculate overall style consistency score."""
        consistency_scores = []
        
        # Check sentence length
        expected_range = expectations.get('sentence_length', {}).get('preferred', (10, 25))
        actual_length = features.get('avg_sentence_length', 15)
        if expected_range[0] <= actual_length <= expected_range[1]:
            consistency_scores.append(1.0)
        else:
            # Calculate distance from preferred range
            if actual_length < expected_range[0]:
                distance = expected_range[0] - actual_length
            else:
                distance = actual_length - expected_range[1]
            consistency_scores.append(max(0.0, 1.0 - distance / 10))
        
        # Check formality alignment
        expected_formality = expectations.get('formality_level', 'neutral')
        actual_formality = features.get('formality_level', 'neutral')
        if expected_formality == actual_formality:
            consistency_scores.append(1.0)
        elif (expected_formality == 'neutral') or (actual_formality == 'neutral'):
            consistency_scores.append(0.7)
        else:
            consistency_scores.append(0.3)
        
        return sum(consistency_scores) / len(consistency_scores)
    
    def _identify_style_violations(self, expectations: Dict[str, Any], features: Dict[str, Any], 
                                 context: ValidationContext) -> List[str]:
        """Identify specific style violations."""
        violations = []
        
        # Check sentence length violations
        max_acceptable = expectations.get('sentence_length', {}).get('max_acceptable', 40)
        actual_length = features.get('avg_sentence_length', 15)
        if actual_length > max_acceptable:
            violations.append(f'sentences_too_long (avg: {actual_length:.1f}, max: {max_acceptable})')
        
        # Check formality violations
        expected_formality = expectations.get('formality_level', 'neutral')
        actual_formality = features.get('formality_level', 'neutral')
        if expected_formality == 'formal' and actual_formality == 'informal':
            violations.append('informal_language_in_formal_context')
        elif expected_formality == 'informal' and actual_formality == 'formal':
            violations.append('overly_formal_language')
        
        return violations
    
    def _assess_formality_alignment(self, expected: str, actual: str) -> float:
        """Assess alignment between expected and actual formality levels."""
        if expected == actual:
            return 1.0
        elif 'neutral' in [expected, actual]:
            return 0.7
        else:
            return 0.3
    
    def _assess_structure_appropriateness(self, expectations: Dict[str, Any], features: Dict[str, Any], text: str) -> float:
        """Assess appropriateness of document structure."""
        structure_score = 0.7  # Base score
        
        # Check for expected structural elements
        if expectations.get('headings_structured', False):
            if re.search(r'^#+\s', text, re.MULTILINE):  # Markdown headings
                structure_score += 0.2
        
        if expectations.get('bullet_points', False):
            if re.search(r'^[-*+]\s', text, re.MULTILINE):  # Bullet points
                structure_score += 0.1
        
        return min(1.0, structure_score)
    
    def _assess_tone_consistency(self, expected: str, actual: str, text: str) -> float:
        """Assess tone consistency throughout the text."""
        if expected == actual:
            return 0.9
        
        # Check for tone consistency within text
        emotional_words = len(re.findall(r'\b(?:love|hate|amazing|terrible|fantastic|awful)\b', text, re.IGNORECASE))
        neutral_words = len(re.findall(r'\b(?:is|are|will|can|should|may|might)\b', text, re.IGNORECASE))
        
        # More neutral words suggest consistent neutral tone
        if neutral_words > emotional_words * 3:
            return 0.8
        else:
            return 0.6
    
    def _generate_style_recommendations(self, expectations: Dict[str, Any], features: Dict[str, Any], 
                                      violations: List[str]) -> List[str]:
        """Generate style improvement recommendations."""
        recommendations = []
        
        for violation in violations:
            if 'sentences_too_long' in violation:
                recommendations.append('Break long sentences into shorter, clearer statements')
            elif 'informal_language' in violation:
                recommendations.append('Use more formal vocabulary and sentence structures')
            elif 'overly_formal' in violation:
                recommendations.append('Use more conversational and accessible language')
        
        # General recommendations based on domain
        expected_structure = expectations.get('structure', 'clear')
        if expected_structure == 'logical' and not any('structure' in r for r in recommendations):
            recommendations.append('Organize content in logical, sequential order')
        
        return recommendations
    
    # Helper methods for audience assessment
    def _determine_target_audience(self, domain: str, content_type: str, context: ValidationContext) -> str:
        """Determine the target audience based on domain and context."""
        domain_audiences = self.content_type_audiences.get(domain, ['general_audience'])
        
        # Use the first (primary) audience for the domain
        primary_audience = domain_audiences[0] if domain_audiences else 'general_audience'
        
        # Adjust based on rule type
        if context.rule_type == 'terminology' and domain == 'technical':
            return 'developers'
        elif context.rule_type == 'style' and domain == 'business':
            return 'business_users'
        elif context.rule_type == 'academic':
            return 'academics'
        
        return primary_audience
    
    def _assess_content_accessibility(self, text: str, target_audience: str) -> float:
        """Assess how accessible content is for target audience."""
        audience_info = self.audience_criteria.get(target_audience, self.audience_criteria['general_audience'])
        expected_technical_level = audience_info.get('technical_level', 'minimal')
        
        # Count technical terms
        technical_terms = len(re.findall(r'\b(?:API|JSON|HTTP|algorithm|implementation|configuration|optimization)\b', text, re.IGNORECASE))
        total_words = len(text.split())
        technical_ratio = technical_terms / max(1, total_words)
        
        # Assess based on expected technical level
        if expected_technical_level == 'high':
            # Technical audience expects technical terms
            return min(1.0, 0.7 + technical_ratio * 2)
        elif expected_technical_level == 'minimal':
            # General audience prefers minimal technical terms
            return max(0.2, 1.0 - technical_ratio * 3)
        else:  # medium or learning
            # Moderate technical level acceptable
            return max(0.4, 1.0 - abs(technical_ratio - 0.2) * 2)
    
    def _check_technical_level_match(self, text: str, target_audience: str) -> bool:
        """Check if technical level matches target audience."""
        audience_info = self.audience_criteria.get(target_audience, self.audience_criteria['general_audience'])
        expected_level = audience_info.get('technical_level', 'minimal')
        
        # Simple technical level detection
        technical_indicators = len(re.findall(r'\b(?:API|JSON|algorithm|database|server|client|function|method|class|implementation|configuration|deployment|architecture|framework|protocol|interface|authentication|optimization|scalability|performance|debugging|testing|integration|documentation|specification)\b', text, re.IGNORECASE))
        
        if expected_level == 'high' and technical_indicators >= 3:
            return True
        elif expected_level == 'minimal' and technical_indicators <= 1:
            return True
        elif expected_level in ['medium', 'learning'] and 1 <= technical_indicators <= 3:
            return True
        
        return False
    
    def _assess_language_complexity(self, text: str) -> str:
        """Assess the complexity level of language used."""
        words = text.split()
        total_words = len(words)
        
        # Count syllables (simplified)
        syllable_count = sum(self._count_syllables(word) for word in words)
        avg_syllables = syllable_count / max(1, total_words)
        
        # Count sentence length
        sentences = text.split('.')
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        avg_sentence_length = sum(sentence_lengths) / max(1, len(sentence_lengths))
        
        # Classify complexity
        if avg_syllables <= 1.5 and avg_sentence_length <= 15:
            return 'simple'
        elif avg_syllables <= 2.5 and avg_sentence_length <= 25:
            return 'moderate'
        elif avg_syllables <= 3.5 and avg_sentence_length <= 35:
            return 'complex'
        else:
            return 'highly_complex'
    
    def _count_syllables(self, word: str) -> int:
        """Simple syllable counting."""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _identify_assumed_knowledge(self, text: str, domain: str) -> List[str]:
        """Identify knowledge assumptions in the text."""
        assumptions = []
        
        # Domain-specific knowledge assumptions
        if domain == 'technical':
            if re.search(r'\b(?:API|REST|JSON)\b', text, re.IGNORECASE):
                assumptions.append('web_development_knowledge')
            if re.search(r'\b(?:database|SQL|query)\b', text, re.IGNORECASE):
                assumptions.append('database_knowledge')
            if re.search(r'\b(?:server|client|deployment)\b', text, re.IGNORECASE):
                assumptions.append('system_administration_knowledge')
        
        elif domain == 'business':
            if re.search(r'\b(?:ROI|KPI|revenue)\b', text, re.IGNORECASE):
                assumptions.append('business_metrics_knowledge')
            if re.search(r'\b(?:stakeholder|shareholder)\b', text, re.IGNORECASE):
                assumptions.append('corporate_structure_knowledge')
        
        return assumptions
    
    def _find_accessibility_barriers(self, text: str, target_audience: str) -> List[str]:
        """Find barriers to audience comprehension."""
        barriers = []
        audience_info = self.audience_criteria.get(target_audience, self.audience_criteria['general_audience'])
        
        # Check for overly complex language
        complexity = self._assess_language_complexity(text)
        expected_complexity = 'simple' if audience_info.get('technical_level') == 'minimal' else 'moderate'
        
        if complexity == 'highly_complex' and expected_complexity in ['simple', 'moderate']:
            barriers.append('overly_complex_language')
        
        # Check for unexplained jargon
        technical_terms = re.findall(r'\b(?:API|JSON|HTTP|algorithm|implementation)\b', text, re.IGNORECASE)
        if len(technical_terms) > 2 and audience_info.get('technical_level') == 'minimal':
            barriers.append('unexplained_technical_jargon')
        
        # Check for assumed knowledge barriers
        assumptions = self._identify_assumed_knowledge(text, audience_info.get('assumed_knowledge', []))
        if len(assumptions) > 0:
            barriers.append('excessive_knowledge_assumptions')
        
        return barriers
    
    def _calculate_audience_appropriateness(self, accessibility: float, technical_match: bool, 
                                         complexity: str, assumptions: List[str], 
                                         barriers: List[str], audience: str) -> float:
        """Calculate overall audience appropriateness score."""
        score = accessibility * 0.4
        score += (0.3 if technical_match else 0.1) * 0.3
        
        # Penalty for complexity mismatch
        complexity_scores = {'simple': 0.9, 'moderate': 0.7, 'complex': 0.5, 'highly_complex': 0.3}
        expected_complexity = 'simple' if 'general' in audience else 'moderate'
        if complexity == expected_complexity:
            score += 0.2
        else:
            score += complexity_scores.get(complexity, 0.5) * 0.2
        
        # Penalty for barriers
        score -= len(barriers) * 0.05
        score -= len(assumptions) * 0.03
        
        return max(0.0, min(1.0, score))
    
    def _generate_audience_recommendations(self, audience: str, barriers: List[str], 
                                         complexity: str, assumptions: List[str]) -> List[str]:
        """Generate recommendations for better audience alignment."""
        recommendations = []
        
        if 'overly_complex_language' in barriers:
            recommendations.append('Simplify language and sentence structure')
        
        if 'unexplained_technical_jargon' in barriers:
            recommendations.append('Define technical terms or provide glossary')
        
        if 'excessive_knowledge_assumptions' in barriers:
            recommendations.append('Provide more background context and explanations')
        
        if complexity == 'highly_complex' and 'general' in audience:
            recommendations.append('Break complex concepts into simpler explanations')
        
        return recommendations
    
    # Evidence creation methods
    def _create_applicability_evidence(self, assessment: RuleApplicabilityAssessment, 
                                     context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from rule applicability assessment."""
        confidence = assessment.applicability_score
        
        description = f"Rule applicability: {assessment.rule_type}/{assessment.rule_name} "
        description += f"in {assessment.rule_type} domain (score: {assessment.applicability_score:.2f})"
        
        if not assessment.content_type_match:
            description += " [content type mismatch]"
        
        if assessment.rule_exceptions:
            description += f" [exceptions: {', '.join(assessment.rule_exceptions[:2])}]"
        
        return ValidationEvidence(
            evidence_type="rule_applicability",
            confidence=confidence,
            description=description,
            source_data={
                'rule_type': assessment.rule_type,
                'rule_name': assessment.rule_name,
                'domain_relevance': assessment.domain_relevance,
                'content_type_match': assessment.content_type_match,
                'audience_alignment': assessment.audience_alignment,
                'applicability_score': assessment.applicability_score,
                'applicability_factors': assessment.applicability_factors,
                'rule_exceptions': assessment.rule_exceptions,
                'confidence_modifier': assessment.confidence_modifier
            }
        )
    
    def _create_terminology_evidence(self, validation: TerminologyValidation, 
                                   context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from terminology validation."""
        confidence = (validation.appropriateness_score + validation.actual_precision + 
                     validation.terminology_consistency) / 3
        
        description = f"Terminology validation: {validation.terminology_type} in {validation.domain} domain "
        description += f"(appropriateness: {validation.appropriateness_score:.2f})"
        
        if validation.inappropriate_terms:
            description += f" [inappropriate terms: {', '.join(validation.inappropriate_terms[:2])}]"
        
        if validation.alternative_suggestions:
            description += f" [alternatives available]"
        
        return ValidationEvidence(
            evidence_type="terminology_validation",
            confidence=confidence,
            description=description,
            source_data={
                'domain': validation.domain,
                'terminology_type': validation.terminology_type,
                'appropriateness_score': validation.appropriateness_score,
                'precision_level': validation.precision_level,
                'actual_precision': validation.actual_precision,
                'terminology_consistency': validation.terminology_consistency,
                'inappropriate_terms': validation.inappropriate_terms,
                'missing_terminology': validation.missing_terminology,
                'alternative_suggestions': validation.alternative_suggestions
            }
        )
    
    def _create_style_evidence(self, check: StyleConsistencyCheck, 
                             context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from style consistency check."""
        confidence = (check.consistency_score + check.formality_alignment + 
                     check.structure_appropriateness + check.tone_consistency) / 4
        
        description = f"Style consistency: {check.consistency_score:.2f} overall consistency"
        
        if check.style_violations:
            description += f" [violations: {', '.join(check.style_violations[:2])}]"
        
        if check.style_recommendations:
            description += f" [recommendations available]"
        
        return ValidationEvidence(
            evidence_type="style_consistency",
            confidence=confidence,
            description=description,
            source_data={
                'domain_style_expectations': check.domain_style_expectations,
                'detected_style_features': check.detected_style_features,
                'consistency_score': check.consistency_score,
                'style_violations': check.style_violations,
                'formality_alignment': check.formality_alignment,
                'structure_appropriateness': check.structure_appropriateness,
                'tone_consistency': check.tone_consistency,
                'style_recommendations': check.style_recommendations
            }
        )
    
    def _create_audience_evidence(self, assessment: AudienceAppropriatenessAssessment, 
                                context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from audience appropriateness assessment."""
        confidence = assessment.appropriateness_score
        
        description = f"Audience appropriateness: {assessment.target_audience} audience "
        description += f"(accessibility: {assessment.content_accessibility:.2f})"
        
        if not assessment.technical_level_match:
            description += " [technical level mismatch]"
        
        if assessment.accessibility_barriers:
            description += f" [barriers: {', '.join(assessment.accessibility_barriers[:2])}]"
        
        return ValidationEvidence(
            evidence_type="audience_appropriateness",
            confidence=confidence,
            description=description,
            source_data={
                'target_audience': assessment.target_audience,
                'content_accessibility': assessment.content_accessibility,
                'technical_level_match': assessment.technical_level_match,
                'language_complexity': assessment.language_complexity,
                'assumed_knowledge': assessment.assumed_knowledge,
                'accessibility_barriers': assessment.accessibility_barriers,
                'appropriateness_score': assessment.appropriateness_score,
                'audience_recommendations': assessment.audience_recommendations
            }
        )
    
    def _make_domain_decision(self, evidence: List[ValidationEvidence], domain_analysis: Any,
                            context: ValidationContext) -> Tuple[ValidationDecision, float, str]:
        """Make validation decision based on domain evidence."""
        if not evidence:
            return ValidationDecision.UNCERTAIN, 0.3, "No domain evidence available for validation"
        
        # Calculate weighted average confidence
        total_weight = sum(e.confidence * e.weight for e in evidence)
        total_weights = sum(e.weight for e in evidence)
        avg_confidence = total_weight / total_weights if total_weights > 0 else 0.3
        
        # Analyze evidence types
        evidence_types = [e.evidence_type for e in evidence]
        domain = domain_analysis.domain_identification.primary_domain if domain_analysis and hasattr(domain_analysis, 'domain_identification') else 'unknown'
        
        # Decision logic based on domain and rule type
        if context.rule_type == "terminology":
            # Terminology rules highly dependent on domain appropriateness
            if avg_confidence >= 0.8 and any(et in ['terminology_validation', 'rule_applicability'] for et in evidence_types):
                decision = ValidationDecision.ACCEPT
                reasoning = f"Strong domain evidence ({avg_confidence:.2f}) supports terminology validation in {domain} domain"
                
            elif avg_confidence < 0.4:
                decision = ValidationDecision.REJECT
                reasoning = f"Poor domain fit ({avg_confidence:.2f}) suggests terminology rule not applicable to {domain} domain"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Moderate domain evidence ({avg_confidence:.2f}) - terminology validation uncertain for {domain} domain"
        
        elif context.rule_type == "style":
            # Style rules benefit from domain-specific style consistency
            if avg_confidence >= 0.7 and any(et in ['style_consistency', 'audience_appropriateness'] for et in evidence_types):
                decision = ValidationDecision.ACCEPT
                reasoning = f"Domain-specific style evidence ({avg_confidence:.2f}) supports style validation"
                
            elif avg_confidence < 0.4:
                decision = ValidationDecision.REJECT
                reasoning = f"Domain style mismatch ({avg_confidence:.2f}) suggests style rule not appropriate for {domain} context"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Mixed domain style evidence ({avg_confidence:.2f}) - style validation uncertain"
        
        elif context.rule_type in ["grammar", "punctuation"]:
            # Grammar and punctuation have universal applicability but domain may modify confidence
            if avg_confidence >= 0.6:
                decision = ValidationDecision.ACCEPT
                reasoning = f"Domain context ({avg_confidence:.2f}) supports {context.rule_type} validation"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Domain context provides moderate support ({avg_confidence:.2f}) for {context.rule_type} validation"
        
        else:
            # Other rule types: conservative approach
            if avg_confidence >= 0.8:
                decision = ValidationDecision.ACCEPT
                reasoning = f"Strong domain evidence ({avg_confidence:.2f}) supports validation"
                
            elif avg_confidence < 0.3:
                decision = ValidationDecision.REJECT
                reasoning = f"Poor domain fit ({avg_confidence:.2f}) suggests rule not applicable"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Domain evidence ({avg_confidence:.2f}) inconclusive for {context.rule_type} rule"
        
        return decision, avg_confidence, reasoning
    
    def _create_uncertain_result(self, context: ValidationContext, reason: str, validation_time: float) -> ValidationResult:
        """Create an uncertain validation result."""
        return ValidationResult(
            validator_name=self.validator_name,
            decision=ValidationDecision.UNCERTAIN,
            confidence=ValidationConfidence.LOW,
            confidence_score=0.3,
            evidence=[ValidationEvidence(
                evidence_type="error",
                confidence=0.0,
                description=reason,
                source_data={"error_type": "analysis_failure"}
            )],
            reasoning=f"Domain validation uncertain: {reason}",
            error_text=context.error_text,
            error_position=context.error_position,
            rule_type=context.rule_type,
            rule_name=context.rule_name,
            validation_time=validation_time,
            metadata={"validation_failure": True}
        )
    
    def _create_error_result(self, context: ValidationContext, error_msg: str, validation_time: float) -> ValidationResult:
        """Create an error validation result."""
        return ValidationResult(
            validator_name=self.validator_name,
            decision=ValidationDecision.UNCERTAIN,
            confidence=ValidationConfidence.LOW,
            confidence_score=0.0,
            evidence=[ValidationEvidence(
                evidence_type="error",
                confidence=0.0,
                description=f"Validation error: {error_msg}",
                source_data={"error_message": error_msg}
            )],
            reasoning=f"Domain validation failed due to error: {error_msg}",
            error_text=context.error_text,
            error_position=context.error_position,
            rule_type=context.rule_type,
            rule_name=context.rule_name,
            validation_time=validation_time,
            metadata={"validation_error": True}
        )
    
    def get_validator_info(self) -> Dict[str, Any]:
        """Get comprehensive information about this validator."""
        return {
            "name": self.validator_name,
            "type": "domain_validator",
            "version": "1.0.0",
            "description": "Validates errors using domain-specific analysis and audience appropriateness",
            "capabilities": [
                "rule_applicability_assessment",
                "terminology_validation",
                "style_consistency_checking",
                "audience_appropriateness_assessment",
                "domain_classification"
            ],
            "specialties": [
                "domain_specific_validation",
                "terminology_appropriateness",
                "audience_targeting",
                "style_consistency",
                "rule_applicability"
            ],
            "configuration": {
                "domain_classification_enabled": self.enable_domain_classification,
                "terminology_validation_enabled": self.enable_terminology_validation,
                "style_consistency_enabled": self.enable_style_consistency,
                "audience_assessment_enabled": self.enable_audience_assessment,
                "domain_caching_enabled": self.cache_domain_analyses,
                "min_confidence_threshold": self.min_confidence_threshold,
                "domain_classifier_available": self.domain_classifier is not None
            },
            "performance_characteristics": {
                "best_for_rule_types": ["terminology", "style", "audience"],
                "moderate_for_rule_types": ["grammar", "tone"],
                "limited_for_rule_types": ["punctuation", "formatting"],
                "avg_processing_time_ms": self._get_average_processing_time(),
                "cache_hit_rate": self._get_cache_hit_rate()
            },
            "domain_knowledge": {
                "supported_domains": list(self.domain_terminology.keys()),
                "supported_audiences": list(self.audience_criteria.keys()),
                "rule_applicability_mappings": len(self.domain_rule_applicability),
                "terminology_patterns": sum(len(info.get('expected_patterns', [])) for info in self.domain_terminology.values()),
                "style_expectations": len(self.domain_style_expectations)
            }
        }
    
    def _get_average_processing_time(self) -> float:
        """Get average processing time across all analysis types."""
        all_times = []
        for analysis_type, times in self._analysis_times.items():
            all_times.extend(times)
        
        return (sum(all_times) / len(all_times) * 1000) if all_times else 0.0
    
    def _get_cache_hit_rate(self) -> float:
        """Get domain analysis cache hit rate."""
        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total > 0 else 0.0
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        self._domain_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Clear performance tracking
        for analysis_type in self._analysis_times:
            self._analysis_times[analysis_type].clear()
        
        # Clear domain classifier cache if available
        if self.domain_classifier and hasattr(self.domain_classifier, 'clear_cache'):
            self.domain_classifier.clear_cache()
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get detailed analysis statistics."""
        return {
            "domain_cache": {
                "cached_analyses": len(self._domain_cache),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate": self._get_cache_hit_rate()
            },
            "analysis_performance": {
                analysis_type: {
                    "total_analyses": len(times),
                    "average_time_ms": (sum(times) / len(times) * 1000) if times else 0.0,
                    "min_time_ms": (min(times) * 1000) if times else 0.0,
                    "max_time_ms": (max(times) * 1000) if times else 0.0
                }
                for analysis_type, times in self._analysis_times.items()
            },
            "configuration_status": {
                "domain_classifier_available": self.domain_classifier is not None,
                "terminology_validation": self.enable_terminology_validation,
                "style_consistency": self.enable_style_consistency,
                "audience_assessment": self.enable_audience_assessment,
                "domain_caching": self.cache_domain_analyses
            },
            "domain_knowledge_stats": {
                "domains_supported": len(self.domain_terminology),
                "audiences_supported": len(self.audience_criteria),
                "rule_mappings": len(self.domain_rule_applicability),
                "inappropriate_term_categories": sum(len(cats) for cats in self.inappropriate_terminology.values()),
                "style_expectation_domains": len(self.domain_style_expectations)
            }
        }