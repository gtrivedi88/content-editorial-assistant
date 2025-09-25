"""
Core Metadata Assistant Module

Main orchestrator class that coordinates all metadata extraction components
with production-ready error handling and performance optimization.
"""

import time
import logging
import hashlib
import gc
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# 🆕 Advanced caching support
try:
    from cachetools import TTLCache, LRUCache
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False
    logger.warning("cachetools not available - using basic dict cache")

from .config import MetadataConfig
from .extractors import TitleExtractor, KeywordExtractor, DescriptionExtractor
from .taxonomy_classifier import NextGenTaxonomyClassifier

logger = logging.getLogger(__name__)


class MetadataAssistant:
    """
    Main metadata generation orchestrator.
    
    Integrates with existing style-guide-ai components and provides
    production-ready metadata extraction with semantic understanding.
    """
    
    def __init__(self, model_manager=None, progress_callback: Optional[Callable] = None, config: Optional[MetadataConfig] = None):
        """
        Initialize the metadata assistant.
        
        Args:
            model_manager: Optional ModelManager for AI features
            progress_callback: Optional callback for progress updates
            config: Optional custom configuration
        """
        self.model_manager = model_manager
        self.progress_callback = progress_callback
        self.config = config or MetadataConfig()
        
        # 🆕 Advanced caching and performance monitoring
        self._initialize_caches()
        self._initialize_performance_monitoring()
        
        # Initialize extractors
        self._initialize_extractors()
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info("MetadataAssistant initialized successfully")
    
    def _initialize_extractors(self):
        """Initialize all extraction components."""
        try:
            self.title_extractor = TitleExtractor(self.model_manager)
            self.keyword_extractor = KeywordExtractor()
            self.description_extractor = DescriptionExtractor(self.model_manager)
            self.taxonomy_classifier = NextGenTaxonomyClassifier(self.model_manager)
            
            logger.info("All extractors initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize extractors: {e}")
            raise
    
    def _validate_configuration(self):
        """Validate configuration and log any issues."""
        validation_result = self.config.validate_config()
        
        if not validation_result['valid']:
            error_msg = f"Configuration validation failed: {validation_result['issues']}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if validation_result['warnings']:
            logger.warning(f"Configuration warnings: {validation_result['warnings']}")
    
    # 🆕 Advanced caching and performance methods
    
    def _initialize_caches(self):
        """Initialize advanced caching system."""
        if CACHING_AVAILABLE:
            # TTL Caches with different lifespans based on volatility
            self.spacy_doc_cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour - spaCy docs are stable
            self.keyword_cache = TTLCache(maxsize=500, ttl=1800)    # 30 minutes - keywords change moderately
            self.taxonomy_cache = TTLCache(maxsize=200, ttl=7200)   # 2 hours - taxonomy is more stable
            self.metadata_cache = TTLCache(maxsize=300, ttl=1800)   # 30 minutes - full metadata results
            
            logger.info("✅ Advanced TTL caching initialized")
        else:
            # Fallback to simple LRU-style dict with manual cleanup
            self._cache = {}
            self._cache_max_size = getattr(self.config, 'cache_max_size', 100)
            
            logger.info("⚠️  Basic dictionary caching initialized (TTL unavailable)")
    
    def _initialize_performance_monitoring(self):
        """Initialize performance monitoring system."""
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'processing_times': [],
            'component_times': {
                'title': [],
                'keywords': [],
                'description': [],
                'taxonomy': []
            },
            'memory_usage_samples': [],
            'last_cleanup': datetime.utcnow()
        }
        
        logger.info("📊 Performance monitoring initialized")
    
    def _get_from_cache(self, cache_key: str, cache_type: str = 'metadata') -> Optional[Any]:
        """Get item from appropriate cache."""
        if CACHING_AVAILABLE:
            cache_map = {
                'spacy': self.spacy_doc_cache,
                'keywords': self.keyword_cache,
                'taxonomy': self.taxonomy_cache,
                'metadata': self.metadata_cache
            }
            
            cache = cache_map.get(cache_type, self.metadata_cache)
            result = cache.get(cache_key)
            
            if result is not None:
                self.performance_metrics['cache_hits'] += 1
                return result
            else:
                self.performance_metrics['cache_misses'] += 1
                return None
        else:
            # Fallback cache
            result = getattr(self, '_cache', {}).get(cache_key)
            if result is not None:
                self.performance_metrics['cache_hits'] += 1
            else:
                self.performance_metrics['cache_misses'] += 1
            return result
    
    def _set_cache(self, cache_key: str, value: Any, cache_type: str = 'metadata'):
        """Set item in appropriate cache."""
        if CACHING_AVAILABLE:
            cache_map = {
                'spacy': self.spacy_doc_cache,
                'keywords': self.keyword_cache,
                'taxonomy': self.taxonomy_cache,
                'metadata': self.metadata_cache
            }
            
            cache = cache_map.get(cache_type, self.metadata_cache)
            cache[cache_key] = value
        else:
            # Fallback cache with manual cleanup
            if not hasattr(self, '_cache'):
                self._cache = {}
            
            if len(self._cache) >= self._cache_max_size:
                # Remove oldest items
                keys_to_remove = list(self._cache.keys())[:len(self._cache) // 2]
                for key in keys_to_remove:
                    self._cache.pop(key, None)
            
            self._cache[cache_key] = value
    
    def _cleanup_performance_data(self):
        """Clean up old performance data to prevent memory leaks."""
        if not hasattr(self, 'performance_metrics'):
            return
            
        now = datetime.utcnow()
        
        # Cleanup every hour
        if (now - self.performance_metrics['last_cleanup']).seconds > 3600:
            # Keep only last 1000 processing times
            if len(self.performance_metrics['processing_times']) > 1000:
                self.performance_metrics['processing_times'] = self.performance_metrics['processing_times'][-1000:]
            
            # Keep only last 500 samples for each component
            for component in self.performance_metrics['component_times']:
                times = self.performance_metrics['component_times'][component]
                if len(times) > 500:
                    self.performance_metrics['component_times'][component] = times[-500:]
            
            # Keep only last 100 memory samples
            if len(self.performance_metrics['memory_usage_samples']) > 100:
                self.performance_metrics['memory_usage_samples'] = self.performance_metrics['memory_usage_samples'][-100:]
            
            self.performance_metrics['last_cleanup'] = now
            
            # Trigger garbage collection
            gc.collect()
            
            logger.debug("Performance data cleanup completed")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for monitoring."""
        if not hasattr(self, 'performance_metrics'):
            return {}
        
        metrics = self.performance_metrics.copy()
        
        # Calculate averages and statistics
        if metrics['processing_times']:
            metrics['avg_processing_time'] = sum(metrics['processing_times']) / len(metrics['processing_times'])
            metrics['max_processing_time'] = max(metrics['processing_times'])
            metrics['min_processing_time'] = min(metrics['processing_times'])
        
        # Calculate cache hit rate
        total_cache_requests = metrics['cache_hits'] + metrics['cache_misses']
        if total_cache_requests > 0:
            metrics['cache_hit_rate'] = metrics['cache_hits'] / total_cache_requests
        else:
            metrics['cache_hit_rate'] = 0.0
        
        # Calculate success rate
        if metrics['total_requests'] > 0:
            metrics['success_rate'] = metrics['successful_requests'] / metrics['total_requests']
        else:
            metrics['success_rate'] = 0.0
        
        return metrics

    def generate_metadata(self, content: str, spacy_doc=None, 
                         structural_blocks: List[Dict] = None,
                         analysis_result: Dict = None,
                         session_id: str = None,
                         content_type: str = 'concept',
                         output_format: str = 'dict') -> Dict[str, Any]:
        """
        Generate comprehensive metadata for document.
        
        Args:
            content: Raw document text
            spacy_doc: Pre-parsed spaCy document (reuses existing analysis)
            structural_blocks: Document structure from existing parsing
            analysis_result: Style analysis results
            session_id: For progress tracking
            content_type: Type of content (concept, procedure, reference)
            output_format: 'yaml', 'json', or 'dict'
            
        Returns:
            Dictionary containing generated metadata and processing information
        """
        # 🆕 Enhanced performance monitoring and caching
        start_time = time.time()
        self.performance_metrics['total_requests'] += 1
        
        try:
            # Input validation
            if not content or not content.strip():
                self.performance_metrics['failed_requests'] += 1
                return self._create_error_response("Empty content provided")
            
            if len(content) > self.config.max_content_length:
                self.performance_metrics['failed_requests'] += 1
                return self._create_error_response(f"Content exceeds maximum length of {self.config.max_content_length} characters")
            
            # 🆕 Enhanced caching with content hash
            cache_key = self._generate_cache_key(content, content_type, output_format)
            cached_result = self._get_from_cache(cache_key, 'metadata')
            if cached_result:
                logger.debug(f"✅ Cache hit for metadata generation (key: {cache_key[:16]}...)")
                processing_time = time.time() - start_time
                self.performance_metrics['processing_times'].append(processing_time)
                return cached_result
            
            # Parse document if not provided (fallback)
            if spacy_doc is None and SPACY_AVAILABLE:
                spacy_doc = self._parse_document(content)
            
            # Initialize progress tracking
            if self.progress_callback and session_id:
                self.progress_callback(session_id, 'metadata_start', 
                                     'Starting metadata generation...', 
                                     'Analyzing document structure and content', 10)
            
            # Initialize metadata with safe defaults
            metadata = {
                'title': 'Untitled Document',
                'description': 'No description available',
                'keywords': [],
                'taxonomy_tags': [],
                'audience': 'General',
                'content_type': content_type,
                'intent': self._determine_intent(content_type),
                'generation_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'processing_time_seconds': 0.0,
                    'confidence_scores': {},
                    'algorithms_used': {},
                    'fallback_used': False
                }
            }
            
            errors = []
            processing_steps = []
            
            # Step 1: Extract title
            try:
                title_result = self.title_extractor.extract_title(
                    spacy_doc, structural_blocks or [], content
                )
                
                if title_result and title_result.get('confidence', 0) > 0.3:
                    metadata['title'] = title_result['text']
                    metadata['generation_metadata']['confidence_scores']['title'] = title_result['confidence']
                    metadata['generation_metadata']['algorithms_used']['title'] = title_result.get('method', 'unknown')
                    processing_steps.append(f"Title extracted using {title_result.get('source', 'unknown')} method")
                else:
                    errors.append("Low confidence title extraction")
                
                if self.progress_callback and session_id:
                    self.progress_callback(session_id, 'metadata_title', 
                                         f'Title extracted: {metadata["title"][:50]}...', 
                                         f'Confidence: {title_result.get("confidence", 0):.2f}', 25)
                
            except Exception as e:
                errors.append(f"Title extraction failed: {str(e)}")
                logger.warning(f"Title extraction error: {e}")
                metadata['generation_metadata']['fallback_used'] = True
            
            # Step 2: Extract keywords
            try:
                keywords_result = self.keyword_extractor.extract_keywords(
                    spacy_doc, content, max_keywords=self.config.max_keywords
                )
                
                if keywords_result:
                    metadata['keywords'] = [kw['term'] for kw in keywords_result[:self.config.max_keywords]]
                    avg_keyword_score = sum(kw['score'] for kw in keywords_result) / len(keywords_result)
                    metadata['generation_metadata']['confidence_scores']['keywords'] = avg_keyword_score
                    metadata['generation_metadata']['algorithms_used']['keywords'] = 'ensemble_extraction'
                    processing_steps.append(f"Extracted {len(metadata['keywords'])} keywords using ensemble method")
                else:
                    # Fallback to simple keyword extraction
                    metadata['keywords'] = self._simple_keyword_fallback(content)
                    errors.append("Using fallback keyword extraction")
                    metadata['generation_metadata']['fallback_used'] = True
                
                if self.progress_callback and session_id:
                    self.progress_callback(session_id, 'metadata_keywords', 
                                         f'Keywords extracted: {", ".join(metadata["keywords"][:3])}...', 
                                         f'Found {len(metadata["keywords"])} relevant terms', 50)
                
            except Exception as e:
                errors.append(f"Keyword extraction failed: {str(e)}")
                logger.warning(f"Keyword extraction error: {e}")
                metadata['keywords'] = self._simple_keyword_fallback(content)
                metadata['generation_metadata']['fallback_used'] = True
            
            # Step 3: Generate description
            try:
                description_result = self.description_extractor.extract_description(
                    spacy_doc, content, metadata['title'], max_words=self.config.max_description_words
                )
                
                if description_result and description_result.get('text'):
                    metadata['description'] = description_result['text']
                    metadata['generation_metadata']['confidence_scores']['description'] = description_result.get('confidence', 0.5)
                    metadata['generation_metadata']['algorithms_used']['description'] = description_result.get('method', 'unknown')
                    processing_steps.append(f"Description generated using {description_result.get('source', 'unknown')} method")
                else:
                    # Fallback to first sentences
                    metadata['description'] = self._extract_first_sentences(content, max_sentences=2)
                    errors.append("Using fallback description extraction")
                    metadata['generation_metadata']['fallback_used'] = True
                
                if self.progress_callback and session_id:
                    self.progress_callback(session_id, 'metadata_description', 
                                         f'Description generated: {metadata["description"][:100]}...', 
                                         f'Length: {len(metadata["description"].split())} words', 75)
                
            except Exception as e:
                errors.append(f"Description generation failed: {str(e)}")
                logger.warning(f"Description generation error: {e}")
                metadata['description'] = self._extract_first_sentences(content, max_sentences=2)
                metadata['generation_metadata']['fallback_used'] = True
            
            # Step 4: Classify taxonomy
            try:
                taxonomy_result = self.taxonomy_classifier.classify_taxonomy(
                    content, spacy_doc, metadata['keywords'], self.config.taxonomy_config
                )
                
                if taxonomy_result:
                    metadata['taxonomy_tags'] = [t['category'] for t in taxonomy_result]
                    avg_taxonomy_confidence = sum(t['confidence'] for t in taxonomy_result) / len(taxonomy_result)
                    metadata['generation_metadata']['confidence_scores']['taxonomy'] = avg_taxonomy_confidence
                    classification_method = taxonomy_result[0].get('classification_method', 'unknown')
                    metadata['generation_metadata']['algorithms_used']['taxonomy'] = classification_method
                    processing_steps.append(f"Taxonomy classified using {classification_method} method")
                else:
                    errors.append("No high-confidence taxonomy classifications found")
                
                if self.progress_callback and session_id:
                    taxonomy_tags = metadata['taxonomy_tags']
                    self.progress_callback(session_id, 'metadata_taxonomy', 
                                         f'Taxonomy classified: {", ".join(taxonomy_tags)}', 
                                         f'Applied {len(taxonomy_tags)} category tags', 90)
                
            except Exception as e:
                errors.append(f"Taxonomy classification failed: {str(e)}")
                logger.warning(f"Taxonomy classification error: {e}")
                metadata['generation_metadata']['fallback_used'] = True
            
            # Step 5: Determine audience (simple heuristic)
            try:
                metadata['audience'] = self._determine_audience(spacy_doc, content, analysis_result)
            except Exception as e:
                logger.debug(f"Audience determination failed: {e}")
                # Keep default audience
            
            # Finalize metadata
            processing_time = time.time() - start_time
            metadata['generation_metadata']['processing_time_seconds'] = processing_time
            metadata['generation_metadata']['processing_steps'] = processing_steps
            
            # Format output if requested
            formatted_output = None
            if output_format != 'dict':
                formatted_output = self._format_output(metadata, output_format)
            
            # 🆕 Enhanced caching and performance tracking
            result = {
                'success': True,
                'metadata': metadata,
                'formatted_output': formatted_output,
                'errors': errors,
                'processing_time': processing_time,
                'degraded_mode': len(errors) > 0
            }
            
            # Cache the result using new caching system
            self._set_cache(cache_key, result, 'metadata')
            
            # Update performance metrics
            self.performance_metrics['successful_requests'] += 1
            self.performance_metrics['processing_times'].append(processing_time)
            
            # Periodic cleanup
            self._cleanup_performance_data()
            
            if self.progress_callback and session_id:
                self.progress_callback(session_id, 'metadata_complete', 
                                     'Metadata generation completed successfully!', 
                                     f'Generated in {processing_time:.2f}s', 100)
            
            # Clean up resources
            self._cleanup_resources()
            
            return result
            
        except Exception as e:
            # 🆕 Track failed requests in performance metrics
            self.performance_metrics['failed_requests'] += 1
            processing_time = time.time() - start_time
            self.performance_metrics['processing_times'].append(processing_time)
            
            logger.error(f"Critical metadata generation error: {e}")
            return self._create_error_response(f"Critical failure: {str(e)}")
    
    def _parse_document(self, content: str):
        """Parse document with spaCy if available."""
        if not SPACY_AVAILABLE:
            return None
        
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            # Truncate very long documents for performance
            content_to_parse = content[:10000] if len(content) > 10000 else content
            return nlp(content_to_parse)
        except Exception as e:
            logger.debug(f"spaCy parsing failed: {e}")
            return None
    
    def _determine_intent(self, content_type: str) -> str:
        """Determine document intent based on content type."""
        intent_mapping = {
            'concept': 'Educational',
            'procedure': 'Instructional', 
            'reference': 'Informational'
        }
        return intent_mapping.get(content_type, 'Informational')
    
    def _determine_audience(self, spacy_doc, content: str, analysis_result: Dict = None) -> str:
        """Determine target audience based on content characteristics."""
        # Simple heuristic based on readability and technical terms
        technical_indicators = ['api', 'server', 'database', 'configuration', 'deployment']
        technical_score = sum(1 for term in technical_indicators if term.lower() in content.lower())
        
        if technical_score >= 3:
            return 'Technical'
        elif analysis_result and analysis_result.get('statistics', {}).get('readability_grade', 0) > 12:
            return 'Advanced'
        else:
            return 'General'
    
    def _simple_keyword_fallback(self, content: str) -> List[str]:
        """Simple keyword extraction fallback using word frequency."""
        import re
        from collections import Counter
        
        # Extract words, filter common terms
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        common_words = {
            'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 
            'were', 'said', 'each', 'which', 'their', 'time', 'would', 'there',
            'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first',
            'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only',
            'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before'
        }
        
        filtered_words = [w for w in words if w not in common_words and len(w) >= 4]
        word_freq = Counter(filtered_words)
        
        return [word for word, count in word_freq.most_common(self.config.min_keywords)]
    
    def _extract_first_sentences(self, content: str, max_sentences: int = 2) -> str:
        """Simple fallback: extract first few sentences."""
        import re
        sentences = re.split(r'[.!?]+', content)
        first_sentences = [s.strip() for s in sentences[:max_sentences] if len(s.strip()) > 5]
        result = '. '.join(first_sentences)
        return result + '.' if result and not result.endswith('.') else result or 'No description available.'
    
    def _format_output(self, metadata: Dict[str, Any], output_format: str) -> str:
        """Format metadata for different output formats."""
        try:
            if output_format.lower() == 'yaml':
                return self._to_yaml(metadata)
            elif output_format.lower() == 'json':
                import json
                return json.dumps(metadata, indent=2, default=str)
            else:
                logger.warning(f"Unsupported output format: {output_format}")
                return str(metadata)
        except Exception as e:
            logger.error(f"Output formatting failed: {e}")
            return str(metadata)
    
    def _to_yaml(self, metadata: Dict[str, Any]) -> str:
        """Convert metadata to YAML format."""
        try:
            import yaml
            return yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        except ImportError:
            logger.warning("PyYAML not available, using simple YAML format")
            return self._simple_yaml_format(metadata)
    
    def _simple_yaml_format(self, metadata: Dict[str, Any]) -> str:
        """Simple YAML formatting fallback."""
        yaml_lines = ['---']
        
        for key, value in metadata.items():
            if key == 'generation_metadata':
                continue  # Skip technical metadata in YAML output
            
            if isinstance(value, list):
                yaml_lines.append(f'{key}:')
                for item in value:
                    yaml_lines.append(f'  - "{item}"')
            elif isinstance(value, str):
                yaml_lines.append(f'{key}: "{value}"')
            else:
                yaml_lines.append(f'{key}: {value}')
        
        yaml_lines.append('---')
        return '\n'.join(yaml_lines)
    
    def _generate_cache_key(self, content: str, content_type: str, output_format: str) -> str:
        """Generate cache key for content."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        return f"{content_hash}_{content_type}_{output_format}"
    
    
    def _cleanup_resources(self):
        """Clean up resources to prevent memory leaks."""
        # Trigger garbage collection periodically
        if hasattr(self, '_cleanup_counter'):
            self._cleanup_counter += 1
        else:
            self._cleanup_counter = 1
        
        if self._cleanup_counter % 10 == 0:  # Every 10 requests
            gc.collect()
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            'success': False,
            'error': error_message,
            'metadata': None,
            'formatted_output': None,
            'errors': [error_message],
            'processing_time': 0.0,
            'fallback_available': True,
            'degraded_mode': True
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the metadata assistant."""
        return {
            'status': 'healthy',
            'extractors': {
                'title_extractor': 'available',
                'keyword_extractor': 'available',
                'description_extractor': 'available',
                'taxonomy_classifier': 'available'
            },
            'dependencies': {
                'spacy': 'available' if SPACY_AVAILABLE else 'unavailable',
                'sentence_transformers': 'available' if hasattr(self.taxonomy_classifier, 'sentence_transformer') and self.taxonomy_classifier.sentence_transformer else 'unavailable',
                'model_manager': 'available' if self.model_manager and self.model_manager.is_available() else 'unavailable'
            },
            'cache': {
                'enabled': self.config.enable_caching,
                'size': len(self._cache),
                'max_size': self._cache_max_size
            },
            'configuration': {
                'valid': self.config.validate_config()['valid'],
                'taxonomy_categories': len(self.config.taxonomy_config)
            }
        }
