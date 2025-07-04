"""
Core Analyzer Module
Main StyleAnalyzer class that coordinates all analysis with zero false positives.
Implements mutually exclusive analysis paths to prevent conflicts.
Supports structural parsing for context-aware analysis.
"""

import logging
from typing import Dict, List, Any, Optional

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    import rules
    RULES_AVAILABLE = True
    from rules import get_registry
except ImportError:
    RULES_AVAILABLE = False
    get_registry = None

try:
    from structural_parsing.parser_factory import StructuralParserFactory
    from structural_parsing.asciidoc.types import AsciiDocDocument, AsciiDocBlockType
    from structural_parsing.markdown.types import MarkdownDocument, MarkdownBlockType
    STRUCTURAL_PARSING_AVAILABLE = True
except ImportError:
    STRUCTURAL_PARSING_AVAILABLE = False

from .base_types import (
    AnalysisResult, AnalysisMode, AnalysisMethod, ErrorDict,
    create_analysis_result, create_error
)
from .readability_analyzer import ReadabilityAnalyzer
from .sentence_analyzer import SentenceAnalyzer
from .statistics_calculator import StatisticsCalculator
from .suggestion_generator import SuggestionGenerator

logger = logging.getLogger(__name__)


class StyleAnalyzer:
    """Main style analyzer with zero false positives design and structural parsing support."""
    
    def __init__(self, rules: Optional[dict] = None):
        """Initialize the style analyzer with components."""
        self.rules = rules or {}
        
        # Initialize components
        self.readability_analyzer = ReadabilityAnalyzer(rules)
        self.sentence_analyzer = SentenceAnalyzer(rules)
        self.statistics_calculator = StatisticsCalculator(rules)
        self.suggestion_generator = SuggestionGenerator(rules)
        
        # Initialize structural parser factory if available
        self.parser_factory = None
        if STRUCTURAL_PARSING_AVAILABLE:
            try:
                self.parser_factory = StructuralParserFactory()
                logger.info("Structural parsing enabled - context-aware analysis available")
            except Exception as e:
                logger.warning(f"Failed to initialize structural parser: {e}")
                self.parser_factory = None
        
        # Initialize rules registry
        self.rules_registry = None
        if RULES_AVAILABLE and get_registry:
            try:
                self.rules_registry = get_registry()
                logger.info("Rules registry loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load rules registry: {e}")
                self.rules_registry = None
        
        # Initialize NLP model if available
        self.nlp = None
        if SPACY_AVAILABLE:
            self._initialize_spacy()
    
    def _initialize_spacy(self):
        """Initialize SpaCy model safely."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
        except OSError:
            logger.warning("SpaCy model not found, using fallback methods")
            self.nlp = None
    
    def analyze(self, text: str, format_hint: str = 'auto') -> AnalysisResult:
        """Perform comprehensive style analysis with structural awareness."""
        if not text or not text.strip():
            return create_analysis_result(
                errors=[],
                suggestions=[],
                statistics={},
                technical_metrics={},
                overall_score=0,
                analysis_mode=AnalysisMode.NONE,
                spacy_available=SPACY_AVAILABLE,
                modular_rules_available=RULES_AVAILABLE
            )
        
        try:
            # Determine analysis mode based on available capabilities
            analysis_mode = self._determine_analysis_mode()
            
            # Try structural parsing for context-aware analysis
            parsed_document = None
            if self.parser_factory:
                try:
                    # Ensure format_hint is a valid value and cast to Literal type
                    from typing import cast, Literal
                    if format_hint in ['asciidoc', 'markdown', 'auto']:
                        validated_hint = cast(Literal['asciidoc', 'markdown', 'auto'], format_hint)
                    else:
                        validated_hint = 'auto'
                    parse_result = self.parser_factory.parse(text, format_hint=validated_hint)
                    if parse_result.success:
                        parsed_document = parse_result.document
                        logger.info(f"Successfully parsed as {type(parsed_document).__name__}")
                except Exception as e:
                    logger.warning(f"Structural parsing failed, falling back to text analysis: {e}")
            
            # Prepare text for analysis
            if parsed_document:
                # Use structural parsing for context-aware analysis
                errors = self._analyze_with_structure(parsed_document, analysis_mode)
                sentences = self._extract_content_sentences(parsed_document)
                paragraphs = self._extract_content_paragraphs(parsed_document)
                
                # Check if structural parsing extracted meaningful content
                # If not, fall back to direct text analysis
                if not sentences and text.strip():
                    logger.info("Structural parsing produced empty sentences, falling back to direct text analysis")
                    sentences = self._split_sentences(text)
                    paragraphs = self.statistics_calculator.split_paragraphs_safe(text)
                    errors = self._analyze_without_structure(text, sentences, analysis_mode)
            else:
                # Fall back to traditional text analysis
                sentences = self._split_sentences(text)
                paragraphs = self.statistics_calculator.split_paragraphs_safe(text)
                errors = self._analyze_without_structure(text, sentences, analysis_mode)
            
            # Calculate statistics and metrics
            statistics = self.statistics_calculator.calculate_safe_statistics(
                text, sentences, paragraphs
            )
            
            technical_metrics = self.statistics_calculator.calculate_safe_technical_metrics(
                text, sentences, len(errors)
            )
            
            # Generate suggestions
            suggestions = self.suggestion_generator.generate_suggestions(
                errors, statistics, technical_metrics
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                errors, technical_metrics, statistics
            )
            
            return create_analysis_result(
                errors=errors,
                suggestions=suggestions,
                statistics=statistics,
                technical_metrics=technical_metrics,
                overall_score=overall_score,
                analysis_mode=analysis_mode,
                spacy_available=SPACY_AVAILABLE,
                modular_rules_available=RULES_AVAILABLE
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return create_analysis_result(
                errors=[create_error(
                    error_type='system',
                    message=f'Analysis failed: {str(e)}',
                    suggestions=['Check text input and system configuration']
                )],
                suggestions=[],
                statistics={},
                technical_metrics={},
                overall_score=0,
                analysis_mode=AnalysisMode.ERROR,
                spacy_available=SPACY_AVAILABLE,
                modular_rules_available=RULES_AVAILABLE
            )
    
    def _analyze_with_structure(self, parsed_document, analysis_mode: AnalysisMode) -> List[ErrorDict]:
        """Analyze document using structural information for context-aware analysis."""
        errors = []
        
        try:
            # Extract content blocks that should be analyzed
            content_blocks = self._get_analyzable_blocks(parsed_document)
            
            for block in content_blocks:
                block_content = block.get_text_content()
                if not block_content.strip():
                    continue
                
                # Apply context-specific analysis based on block type
                block_errors = self._analyze_block_content(block, block_content, analysis_mode)
                errors.extend(block_errors)
            
            logger.info(f"Structural analysis completed: {len(errors)} issues found across {len(content_blocks)} blocks")
            
        except Exception as e:
            logger.error(f"Structural analysis failed: {e}")
            # Fall back to text-based analysis
            full_text = self._extract_all_text(parsed_document)
            sentences = self._split_sentences(full_text)
            errors = self._analyze_without_structure(full_text, sentences, analysis_mode)
        
        return errors
    
    def _get_analyzable_blocks(self, parsed_document):
        """Get blocks that should be analyzed for style issues."""
        analyzable_blocks = []
        
        try:
            if hasattr(parsed_document, 'get_content_blocks'):
                # Use document's built-in method to get content blocks
                content_blocks = parsed_document.get_content_blocks()
                for block in content_blocks:
                    if hasattr(block, 'should_skip_analysis') and not block.should_skip_analysis():
                        analyzable_blocks.append(block)
                    elif not hasattr(block, 'should_skip_analysis'):
                        # If should_skip_analysis doesn't exist, include the block
                        analyzable_blocks.append(block)
            else:
                # Fall back to manual filtering
                all_blocks = getattr(parsed_document, 'blocks', [])
                for block in all_blocks:
                    if hasattr(block, 'is_content_block') and block.is_content_block():
                        if hasattr(block, 'should_skip_analysis') and not block.should_skip_analysis():
                            analyzable_blocks.append(block)
                        elif not hasattr(block, 'should_skip_analysis'):
                            analyzable_blocks.append(block)
                        
        except Exception as e:
            logger.error(f"Error getting analyzable blocks: {e}")
            
        return analyzable_blocks
    
    def _analyze_block_content(self, block, content: str, analysis_mode: AnalysisMode) -> List[ErrorDict]:
        """Analyze content within a specific block context."""
        errors = []
        
        try:
            # Get block-specific context
            block_type = getattr(block, 'block_type', None)
            block_context = getattr(block, 'get_context_info', lambda: {})()
            
            # Apply different analysis based on block type
            if self._is_asciidoc_block(block_type):
                errors.extend(self._analyze_asciidoc_block(block, content, analysis_mode, block_context))
            elif self._is_markdown_block(block_type):
                errors.extend(self._analyze_markdown_block(block, content, analysis_mode, block_context))
            else:
                # Generic content analysis
                errors.extend(self._analyze_generic_content(content, analysis_mode, block_context))
                
        except Exception as e:
            logger.error(f"Error analyzing block content: {e}")
            
        return errors
    
    def _is_asciidoc_block(self, block_type) -> bool:
        """Check if block is an AsciiDoc block type."""
        if not STRUCTURAL_PARSING_AVAILABLE:
            return False
        try:
            return isinstance(block_type, AsciiDocBlockType)
        except:
            return False
    
    def _is_markdown_block(self, block_type) -> bool:
        """Check if block is a Markdown block type."""
        if not STRUCTURAL_PARSING_AVAILABLE:
            return False
        try:
            return isinstance(block_type, MarkdownBlockType)
        except:
            return False
    
    def _analyze_asciidoc_block(self, block, content: str, analysis_mode: AnalysisMode, block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Apply AsciiDoc-specific analysis rules."""
        errors = []
        
        try:
            block_type = block.block_type
            
            # Skip code/literal blocks
            if block_type in [AsciiDocBlockType.LISTING, AsciiDocBlockType.LITERAL, AsciiDocBlockType.PASS]:
                return errors
            
            # Apply special rules for admonitions
            if block_type == AsciiDocBlockType.ADMONITION:
                errors.extend(self._analyze_admonition_content(block, content, block_context))
            
            # Apply general content analysis for other blocks
            if block_type in [AsciiDocBlockType.PARAGRAPH, AsciiDocBlockType.HEADING, AsciiDocBlockType.QUOTE]:
                errors.extend(self._analyze_generic_content(content, analysis_mode, block_context))
                
        except Exception as e:
            logger.error(f"Error in AsciiDoc block analysis: {e}")
            
        return errors
    
    def _analyze_markdown_block(self, block, content: str, analysis_mode: AnalysisMode, block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Apply Markdown-specific analysis rules."""
        errors = []
        
        try:
            block_type = block.block_type
            
            # Skip code blocks
            if block_type in [MarkdownBlockType.CODE_BLOCK, MarkdownBlockType.INLINE_CODE]:
                return errors
            
            # Apply general content analysis for text blocks
            if block_type in [MarkdownBlockType.PARAGRAPH, MarkdownBlockType.HEADING, MarkdownBlockType.BLOCKQUOTE]:
                errors.extend(self._analyze_generic_content(content, analysis_mode, block_context))
                
        except Exception as e:
            logger.error(f"Error in Markdown block analysis: {e}")
            
        return errors
    
    def _analyze_admonition_content(self, block, content: str, block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Special analysis for AsciiDoc admonition blocks."""
        errors = []
        
        try:
            admonition_type = getattr(block, 'admonition_type', None)
            if admonition_type:
                # Apply admonition-specific rules using the rules registry
                if self.rules_registry:
                    try:
                        # Look for admonitions rule
                        admonition_rule = getattr(self.rules_registry, 'get_rule', lambda x: None)('admonitions')
                        if admonition_rule:
                            rule_errors = admonition_rule.analyze(content, [content], self.nlp, block_context)
                            for error in rule_errors:
                                converted_error = self._convert_rules_error(error)
                                errors.append(converted_error)
                    except Exception as e:
                        logger.warning(f"Admonition rule analysis failed: {e}")
                        
        except Exception as e:
            logger.error(f"Error analyzing admonition content: {e}")
            
        return errors
    
    def _analyze_generic_content(self, content: str, analysis_mode: AnalysisMode, block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Apply general style analysis to content."""
        errors = []
        
        try:
            sentences = self._split_sentences(content)
            
            if analysis_mode == AnalysisMode.SPACY_WITH_MODULAR_RULES:
                errors = self._analyze_spacy_with_modular_rules(content, sentences, block_context)
            elif analysis_mode == AnalysisMode.MODULAR_RULES_WITH_FALLBACKS:
                errors = self._analyze_modular_rules_with_fallbacks(content, sentences, block_context)
            elif analysis_mode == AnalysisMode.SPACY_LEGACY_ONLY:
                errors = self._analyze_spacy_legacy_only(content, sentences, block_context)
            elif analysis_mode == AnalysisMode.MINIMAL_SAFE_MODE:
                errors = self._analyze_minimal_safe_mode(content, sentences, block_context)
                
        except Exception as e:
            logger.error(f"Error in generic content analysis: {e}")
            
        return errors
    
    def _extract_content_sentences(self, parsed_document) -> List[str]:
        """Extract sentences from content blocks only."""
        sentences = []
        try:
            content_blocks = self._get_analyzable_blocks(parsed_document)
            for block in content_blocks:
                block_content = block.get_text_content()
                if block_content.strip():
                    block_sentences = self._split_sentences(block_content)
                    sentences.extend(block_sentences)
        except Exception as e:
            logger.error(f"Error extracting content sentences: {e}")
            # Fall back to full text
            full_text = self._extract_all_text(parsed_document)
            sentences = self._split_sentences(full_text)
        return sentences
    
    def _extract_content_paragraphs(self, parsed_document) -> List[str]:
        """Extract paragraphs from content blocks only."""
        paragraphs = []
        try:
            content_blocks = self._get_analyzable_blocks(parsed_document)
            for block in content_blocks:
                block_content = block.get_text_content()
                if block_content.strip():
                    paragraphs.append(block_content)
        except Exception as e:
            logger.error(f"Error extracting content paragraphs: {e}")
            # Fall back to full text
            full_text = self._extract_all_text(parsed_document)
            paragraphs = self.statistics_calculator.split_paragraphs_safe(full_text)
        return paragraphs
    
    def _extract_all_text(self, parsed_document) -> str:
        """Extract all text from the parsed document."""
        try:
            all_text = []
            blocks = getattr(parsed_document, 'blocks', [])
            for block in blocks:
                if hasattr(block, 'get_all_text'):
                    # Use the block's get_all_text method which includes children
                    text = block.get_all_text()
                    if text.strip():
                        all_text.append(text)
                elif hasattr(block, 'get_text_content'):
                    # Fallback to get_text_content
                    text = block.get_text_content()
                    if text.strip():
                        all_text.append(text)
            return '\n\n'.join(all_text)
        except Exception as e:
            logger.error(f"Error extracting all text: {e}")
            return ""
    
    def _analyze_without_structure(self, text: str, sentences: List[str], analysis_mode: AnalysisMode) -> List[ErrorDict]:
        """Fall back to traditional text-based analysis."""
        errors = []
        
        if analysis_mode == AnalysisMode.SPACY_WITH_MODULAR_RULES:
            errors = self._analyze_spacy_with_modular_rules(text, sentences, None)
        elif analysis_mode == AnalysisMode.MODULAR_RULES_WITH_FALLBACKS:
            errors = self._analyze_modular_rules_with_fallbacks(text, sentences, None)
        elif analysis_mode == AnalysisMode.SPACY_LEGACY_ONLY:
            errors = self._analyze_spacy_legacy_only(text, sentences, None)
        elif analysis_mode == AnalysisMode.MINIMAL_SAFE_MODE:
            errors = self._analyze_minimal_safe_mode(text, sentences, None)
        else:
            # Error mode
            errors = [create_error(
                error_type='system',
                message='Analysis system could not determine safe analysis mode.',
                suggestions=['Check system configuration and dependencies']
            )]
        
        return errors
    
    def _determine_analysis_mode(self) -> AnalysisMode:
        """Determine the safest analysis mode based on available capabilities."""
        if SPACY_AVAILABLE and RULES_AVAILABLE and self.nlp:
            return AnalysisMode.SPACY_WITH_MODULAR_RULES
        elif RULES_AVAILABLE:
            return AnalysisMode.MODULAR_RULES_WITH_FALLBACKS
        elif SPACY_AVAILABLE and self.nlp:
            return AnalysisMode.SPACY_LEGACY_ONLY
        else:
            return AnalysisMode.MINIMAL_SAFE_MODE
    
    def _analyze_spacy_with_modular_rules(self, text: str, sentences: List[str], block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using SpaCy enhanced with modular rules (highest accuracy)."""
        errors = []
        
        try:
            # SpaCy-enhanced readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_spacy_enhanced(
                text, self.nlp
            )
            errors.extend(readability_errors)
            
            # SpaCy-enhanced sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_spacy(
                sentences, self.nlp
            )
            errors.extend(sentence_errors)
            
            # Integrate modular rules analysis
            if self.rules_registry:
                try:
                    rules_errors = self.rules_registry.analyze_with_all_rules(text, sentences, self.nlp, block_context)
                    # Convert rules errors to our error format
                    for error in rules_errors:
                        converted_error = self._convert_rules_error(error)
                        errors.append(converted_error)
                    logger.info(f"Modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Modular rules analysis failed: {e}")
            
        except Exception as e:
            logger.error(f"SpaCy with modular rules analysis failed: {e}")
            # Fall back to next best mode
            return self._analyze_modular_rules_with_fallbacks(text, sentences, block_context)
        
        return errors
    
    def _analyze_modular_rules_with_fallbacks(self, text: str, sentences: List[str], block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using modular rules with conservative fallbacks."""
        errors = []
        
        try:
            # Conservative readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_conservative(text)
            errors.extend(readability_errors)
            
            # Conservative sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_conservative(sentences)
            errors.extend(sentence_errors)
            
            # Integrate modular rules analysis
            if self.rules_registry:
                try:
                    rules_errors = self.rules_registry.analyze_with_all_rules(text, sentences, self.nlp, block_context)
                    # Convert rules errors to our error format
                    for error in rules_errors:
                        converted_error = self._convert_rules_error(error)
                        errors.append(converted_error)
                    logger.info(f"Modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Modular rules analysis failed: {e}")
            
        except Exception as e:
            logger.error(f"Modular rules with fallbacks analysis failed: {e}")
            # Fall back to next best mode
            return self._analyze_spacy_legacy_only(text, sentences, block_context)
        
        return errors
    
    def _analyze_spacy_legacy_only(self, text: str, sentences: List[str], block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using only SpaCy (legacy mode)."""
        errors = []
        
        try:
            # SpaCy-only readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_spacy_enhanced(
                text, self.nlp
            )
            errors.extend(readability_errors)
            
            # SpaCy-only sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_spacy(
                sentences, self.nlp
            )
            errors.extend(sentence_errors)
            
        except Exception as e:
            logger.error(f"SpaCy legacy analysis failed: {e}")
            # Fall back to minimal safe mode
            return self._analyze_minimal_safe_mode(text, sentences, block_context)
        
        return errors
    
    def _analyze_minimal_safe_mode(self, text: str, sentences: List[str], block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using minimal safe methods (most conservative)."""
        errors = []
        
        try:
            # Minimal safe readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_minimal_safe(text)
            errors.extend(readability_errors)
            
            # Minimal safe sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_minimal_safe(sentences)
            errors.extend(sentence_errors)
            
        except Exception as e:
            logger.error(f"Minimal safe analysis failed: {e}")
            # This is the safest mode, so we just return empty errors
            return []
        
        return errors
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences safely."""
        try:
            if self.nlp:
                return self.sentence_analyzer.split_sentences_safe(text, self.nlp)
            else:
                return self.sentence_analyzer.split_sentences_safe(text)
        except Exception as e:
            logger.error(f"Error splitting sentences: {e}")
            # Ultimate fallback
            import re
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_overall_score(self, errors: List[ErrorDict], technical_metrics: Dict[str, Any], statistics: Dict[str, Any]) -> float:
        """Calculate overall style score safely."""
        try:
            # Base score
            base_score = 85.0
            
            # Deduct points for errors
            error_penalty = min(len(errors) * 5, 30)  # Max 30 points penalty
            
            # Adjust for readability
            readability_score = technical_metrics.get('readability_score', 60.0)
            if readability_score < 60:
                readability_penalty = (60 - readability_score) * 0.3
            else:
                readability_penalty = 0
            
            # Final score
            final_score = base_score - error_penalty - readability_penalty
            
            # Ensure score is between 0 and 100
            return max(0, min(100, final_score))
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 50.0  # Safe default
    
    def _convert_rules_error(self, rules_error: Dict[str, Any]) -> ErrorDict:
        """Convert rules system error to our standardized error format."""
        try:
            # Extract information from rules error
            error_type = rules_error.get('type', 'unknown')
            message = rules_error.get('message', 'Unknown error')
            suggestions = rules_error.get('suggestions', [])
            severity = rules_error.get('severity', 'low')
            sentence = rules_error.get('sentence', '')
            sentence_index = rules_error.get('sentence_index', -1)
            
            # Create standardized error
            return create_error(
                error_type=error_type,
                message=message,
                suggestions=suggestions,
                severity=severity,
                sentence=sentence,
                sentence_index=sentence_index,
                confidence=0.85,  # High confidence for rules-based detection
                analysis_method=AnalysisMethod.SPACY_ENHANCED
            )
        except Exception as e:
            logger.error(f"Error converting rules error: {e}")
            return create_error(
                error_type='system',
                message=f'Error processing rule: {str(e)}',
                suggestions=['Check rule implementation']
            ) 