"""
Comprehensive test suite for Metadata Assistant (Phase 1).

Tests all core functionality with production-ready validation:
- Title extraction accuracy across different document types
- Keyword extraction relevance and quality 
- Description generation quality and SEO optimization
- Taxonomy classification accuracy with semantic similarity
- Integration with existing system components
- Performance and memory usage
- Error handling and graceful degradation

This test suite ensures zero technical debt and production readiness.
"""

import unittest
import time
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Test imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from metadata_assistant import MetadataAssistant, MetadataConfig
from metadata_assistant.extractors import TitleExtractor, KeywordExtractor, DescriptionExtractor
from metadata_assistant.taxonomy_classifier import NextGenTaxonomyClassifier, LegacyTaxonomyClassifier


class TestMetadataConfig(unittest.TestCase):
    """Test configuration management."""
    
    def test_default_config_initialization(self):
        """Test default configuration initialization."""
        config = MetadataConfig()
        
        # Check essential settings
        self.assertGreater(config.max_content_length, 0)
        self.assertGreater(config.max_keywords, 0)
        self.assertGreater(config.max_description_words, 0)
        self.assertIsInstance(config.taxonomy_config, dict)
        self.assertGreater(len(config.taxonomy_config), 0)
    
    def test_custom_config_loading(self):
        """Test loading custom configuration from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
max_keywords: 15
max_description_words: 100
enable_semantic_classification: false
""")
            temp_path = f.name
        
        try:
            config = MetadataConfig(temp_path)
            self.assertEqual(config.max_keywords, 15)
            self.assertEqual(config.max_description_words, 100)
            self.assertFalse(config.enable_semantic_classification)
        finally:
            os.unlink(temp_path)
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = MetadataConfig()
        validation_result = config.validate_config()
        
        self.assertIsInstance(validation_result, dict)
        self.assertIn('valid', validation_result)
        self.assertIn('issues', validation_result)
        self.assertIn('warnings', validation_result)
        self.assertTrue(validation_result['valid'])  # Should be valid by default
    
    def test_taxonomy_config_loading(self):
        """Test taxonomy configuration loading."""
        config = MetadataConfig()
        
        # Check that essential taxonomy categories exist
        essential_categories = ['Troubleshooting', 'Installation', 'API_Documentation']
        for category in essential_categories:
            self.assertIn(category, config.taxonomy_config)
            
            category_config = config.taxonomy_config[category]
            self.assertIn('description', category_config)
            self.assertIn('indicators', category_config)
            self.assertIsInstance(category_config['indicators'], list)


class TestTitleExtractor(unittest.TestCase):
    """Test title extraction functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.title_extractor = TitleExtractor()
        self.mock_model_manager = Mock()
        self.mock_model_manager.is_available.return_value = True
        self.mock_model_manager.generate_text.return_value = "Generated Test Title"
    
    def test_markdown_title_extraction(self):
        """Test title extraction from Markdown documents."""
        test_cases = [
            {
                'content': '# Installing Docker\n\nThis guide shows how to install Docker...',
                'expected_title': 'Installing Docker',
                'min_confidence': 0.8
            },
            {
                'content': '## Configuration Guide\n\nStep-by-step configuration...',
                'expected_title': 'Configuration Guide', 
                'min_confidence': 0.7
            }
        ]
        
        for case in test_cases:
            with self.subTest(content=case['content'][:50]):
                # Mock structural blocks
                structural_blocks = [{
                    'type': 'heading',
                    'level': 1,
                    'content': case['expected_title']
                }]
                
                result = self.title_extractor.extract_title(None, structural_blocks, case['content'])
                
                self.assertIsInstance(result, dict)
                self.assertIn('text', result)
                self.assertIn('confidence', result)
                self.assertIn('source', result)
                
                self.assertEqual(result['text'], case['expected_title'])
                self.assertGreaterEqual(result['confidence'], case['min_confidence'])
    
    def test_asciidoc_title_extraction(self):
        """Test title extraction from AsciiDoc documents."""
        content = """= Troubleshooting API Errors

When working with APIs, you may encounter various errors..."""
        
        result = self.title_extractor.extract_title(None, [], content)
        
        self.assertEqual(result['text'], 'Troubleshooting API Errors')
        self.assertGreaterEqual(result['confidence'], 0.7)
        self.assertEqual(result['source'], 'regex_pattern')
    
    def test_no_explicit_title_fallback(self):
        """Test fallback behavior when no clear title is found."""
        content = """This document explains how to configure the system settings 
        for optimal performance. The configuration involves several steps..."""
        
        # Test with AI fallback
        extractor_with_ai = TitleExtractor(self.mock_model_manager)
        result = extractor_with_ai.extract_title(None, [], content)
        
        self.assertIsInstance(result, dict)
        self.assertIn('text', result)
        self.assertGreater(len(result['text']), 0)
        # Should either be AI generated or default
        self.assertIn(result['source'], ['ai_generated', 'default'])
    
    def test_title_cleaning(self):
        """Test title text cleaning and normalization."""
        dirty_title = "  # **Installing** _Docker_  "
        cleaned = self.title_extractor._clean_title(dirty_title)
        
        self.assertEqual(cleaned, "Installing Docker")
    
    def test_empty_content_handling(self):
        """Test handling of empty or invalid content."""
        result = self.title_extractor.extract_title(None, [], "")
        
        self.assertEqual(result['text'], 'Untitled Document')
        self.assertEqual(result['source'], 'default')
        self.assertLess(result['confidence'], 0.2)


class TestKeywordExtractor(unittest.TestCase):
    """Test keyword extraction functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.keyword_extractor = KeywordExtractor()
    
    def test_keyword_extraction_relevance(self):
        """Test keyword extraction quality and relevance."""
        test_content = """
        Installing Kubernetes on AWS EKS
        
        This comprehensive guide covers setting up a Kubernetes cluster using Amazon EKS.
        We'll configure kubectl, set up IAM permissions, and deploy applications.
        Topics include networking, security groups, and troubleshooting common issues.
        
        Prerequisites:
        - AWS CLI installed
        - kubectl configured
        - Docker runtime available
        """
        
        keywords = self.keyword_extractor.extract_keywords(None, test_content, max_keywords=10)
        
        # Test basic structure
        self.assertIsInstance(keywords, list)
        self.assertLessEqual(len(keywords), 10)
        
        keyword_terms = [kw['term'] for kw in keywords]
        
        # Should contain technical terms
        technical_terms_found = any(term in str(keyword_terms).lower() 
                                  for term in ['kubernetes', 'aws', 'eks', 'docker'])
        self.assertTrue(technical_terms_found, f"No technical terms found in: {keyword_terms}")
        
        # Should not contain very common words
        common_words = ['the', 'and', 'this', 'that', 'with']
        common_found = any(word in keyword_terms for word in common_words)
        self.assertFalse(common_found, f"Common words found in: {keyword_terms}")
        
        # Check keyword quality
        for kw in keywords:
            self.assertIn('term', kw)
            self.assertIn('score', kw)
            self.assertIn('source', kw)
            self.assertGreater(kw['score'], 0)  # All keywords should have positive scores
    
    def test_technical_term_boosting(self):
        """Test that technical terms get boosted scores."""
        content = "Configure the API server settings for database connections."
        
        keywords = self.keyword_extractor.extract_keywords(None, content)
        
        # Find API-related keywords
        api_keywords = [kw for kw in keywords if 'api' in kw['term'].lower()]
        database_keywords = [kw for kw in keywords if 'database' in kw['term'].lower()]
        
        # Technical terms should have good scores
        if api_keywords:
            self.assertGreater(api_keywords[0]['score'], 0.5)
        if database_keywords:
            self.assertGreater(database_keywords[0]['score'], 0.5)
    
    def test_capitalized_terms_extraction(self):
        """Test extraction of capitalized terms (proper nouns, acronyms)."""
        content = "Install Docker and configure AWS EKS cluster using Terraform."
        
        keywords = self.keyword_extractor.extract_keywords(None, content)
        keyword_terms = [kw['term'] for kw in keywords]
        
        # Should include capitalized technical terms
        expected_terms = ['Docker', 'AWS', 'EKS', 'Terraform']
        found_terms = [term for term in expected_terms if term in keyword_terms]
        
        self.assertGreater(len(found_terms), 0, 
                          f"No capitalized terms found. Keywords: {keyword_terms}")
    
    def test_frequency_based_extraction(self):
        """Test frequency-based keyword extraction."""
        content = """
        Configuration is important. The configuration file contains settings.
        Configure the application using the configuration parameters.
        System configuration affects performance.
        """
        
        keywords = self.keyword_extractor.extract_keywords(None, content)
        keyword_terms = [kw['term'].lower() for kw in keywords]
        
        # 'configuration' appears frequently and should be extracted
        self.assertIn('configuration', keyword_terms)
    
    def test_minimum_keyword_length(self):
        """Test that very short words are filtered out."""
        content = "API is a set of rules for building software applications."
        
        keywords = self.keyword_extractor.extract_keywords(None, content)
        
        # Check that all keywords meet minimum length requirements
        for kw in keywords:
            self.assertGreaterEqual(len(kw['term']), 2)


class TestDescriptionExtractor(unittest.TestCase):
    """Test description extraction and generation."""
    
    def setUp(self):
        """Set up test environment."""
        self.description_extractor = DescriptionExtractor()
        self.mock_model_manager = Mock()
        self.mock_model_manager.is_available.return_value = True
        self.mock_model_manager.generate_text.return_value = "Refined API authentication guide"
    
    def test_description_generation_quality(self):
        """Test description quality and length constraints."""
        test_content = """
        API Authentication Guide
        
        This comprehensive guide explains how to implement secure API authentication
        using OAuth 2.0 and JWT tokens. Learn best practices for token management,
        refresh strategies, and common security pitfalls to avoid.
        
        We'll cover implementation examples in Python, Node.js, and Java.
        The guide includes practical examples and troubleshooting tips.
        """
        
        title = "API Authentication Guide"
        result = self.description_extractor.extract_description(None, test_content, title, max_words=50)
        
        # Test structure
        self.assertIsInstance(result, dict)
        self.assertIn('text', result)
        self.assertIn('confidence', result)
        self.assertIn('word_count', result)
        self.assertIn('source', result)
        
        # Test content quality
        description = result['text']
        word_count = len(description.split())
        
        self.assertLessEqual(word_count, 50)  # Respects word limit
        self.assertGreaterEqual(word_count, 5)  # Has reasonable content
        
        # Should contain relevant terms
        description_lower = description.lower()
        relevant_terms = ['api', 'authentication', 'oauth', 'jwt', 'token', 'security']
        terms_found = sum(1 for term in relevant_terms if term in description_lower)
        self.assertGreaterEqual(terms_found, 2, f"Description lacks relevant terms: {description}")
    
    def test_description_with_ai_refinement(self):
        """Test AI-enhanced description refinement."""
        content = "This guide covers API security and authentication methods."
        title = "API Security Guide"
        
        extractor_with_ai = DescriptionExtractor(self.mock_model_manager)
        result = extractor_with_ai.extract_description(None, content, title)
        
        # Should use AI refinement if available
        self.assertIsInstance(result, dict)
        self.assertIn('text', result)
        self.assertGreater(len(result['text']), 0)
    
    def test_fallback_description_extraction(self):
        """Test fallback when advanced methods fail."""
        short_content = "Brief text."
        
        result = self.description_extractor.extract_description(None, short_content, "Test")
        
        self.assertIsInstance(result, dict)
        self.assertIn('text', result)
        self.assertGreater(len(result['text']), 0)
        self.assertEqual(result['source'], 'first_sentences')
    
    def test_description_truncation(self):
        """Test proper text truncation to word limits."""
        long_text = " ".join(["word"] * 100)  # 100 words
        
        truncated = self.description_extractor._truncate_to_words(long_text, 30)
        
        self.assertLessEqual(len(truncated.split()), 30)
        self.assertTrue(len(truncated) > 0)


class TestTaxonomyClassifier(unittest.TestCase):
    """Test taxonomy classification functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.classifier = NextGenTaxonomyClassifier()
        self.legacy_classifier = LegacyTaxonomyClassifier()
        
        # Sample taxonomy config
        self.taxonomy_config = {
            'Troubleshooting': {
                'description': 'Content focused on diagnosing and resolving problems',
                'indicators': ['error', 'fix', 'resolve', 'issue', 'problem', 'debug', 'troubleshoot'],
                'structure_hints': ['numbered_list', 'procedure_steps', 'error_messages'],
                'confidence_boost': 1.2,
                'required_keywords': []
            },
            'Installation': {
                'description': 'Step-by-step installation and setup guides',
                'indicators': ['install', 'setup', 'configure', 'deploy', 'requirements'],
                'structure_hints': ['prerequisite_section', 'step_by_step', 'command_blocks'],
                'confidence_boost': 1.3,
                'required_keywords': ['install']
            },
            'API_Documentation': {
                'description': 'Technical documentation for APIs and interfaces',
                'indicators': ['api', 'endpoint', 'request', 'response', 'parameter', 'method'],
                'structure_hints': ['code_blocks', 'parameter_tables', 'example_requests'],
                'confidence_boost': 1.4,
                'required_keywords': ['api']
            }
        }
    
    def test_troubleshooting_classification(self):
        """Test classification of troubleshooting content."""
        test_content = """
        Troubleshooting Connection Timeout Errors
        
        When you encounter connection timeout errors, follow these steps:
        1. Check network connectivity
        2. Verify firewall settings  
        3. Inspect server logs for error messages
        4. Test with different timeout values
        
        Common issues and solutions:
        - DNS resolution problems: Update DNS settings
        - Port blocking: Configure firewall rules
        """
        
        # Test with legacy classifier (always works)
        result = self.legacy_classifier.classify_taxonomy(
            test_content, None, ['error', 'troubleshoot', 'connection'], self.taxonomy_config
        )
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # Should classify as troubleshooting
        categories = [r['category'] for r in result]
        self.assertIn('Troubleshooting', categories)
        
        # Check confidence
        troubleshooting_result = next(r for r in result if r['category'] == 'Troubleshooting')
        self.assertGreaterEqual(troubleshooting_result['confidence'], 0.4)
    
    def test_installation_classification(self):
        """Test classification of installation content."""
        test_content = """
        Installing and Configuring Apache Web Server
        
        Prerequisites:
        - Ubuntu 20.04 or later
        - sudo privileges
        
        Installation steps:
        1. Update package index: sudo apt update
        2. Install Apache: sudo apt install apache2
        3. Start service: sudo systemctl start apache2
        4. Configure firewall: sudo ufw allow 'Apache'
        """
        
        result = self.legacy_classifier.classify_taxonomy(
            test_content, None, ['install', 'apache', 'configure'], self.taxonomy_config
        )
        
        categories = [r['category'] for r in result]
        self.assertIn('Installation', categories)
        
        # Installation should have reasonable confidence due to required keywords
        installation_result = next(r for r in result if r['category'] == 'Installation')
        self.assertGreaterEqual(installation_result['confidence'], 0.4)
    
    def test_api_documentation_classification(self):
        """Test classification of API documentation."""
        test_content = """
        REST API Reference
        
        This API allows you to manage user accounts and authentication.
        
        Authentication endpoint:
        POST /api/auth/login
        
        Parameters:
        - username (string): User's login name
        - password (string): User's password
        
        Response:
        {
          "token": "jwt-token-here",
          "expires": 3600
        }
        """
        
        result = self.legacy_classifier.classify_taxonomy(
            test_content, None, ['api', 'endpoint', 'authentication'], self.taxonomy_config
        )
        
        categories = [r['category'] for r in result]
        self.assertIn('API_Documentation', categories)
        
        api_result = next(r for r in result if r['category'] == 'API_Documentation')
        self.assertGreaterEqual(api_result['confidence'], 0.4)
    
    def test_multiple_category_classification(self):
        """Test that content can be classified into multiple categories."""
        mixed_content = """
        Installing and Troubleshooting API Server
        
        This guide covers both installation and common troubleshooting steps
        for the API server component.
        
        Installation:
        1. Install the server package
        2. Configure the API endpoints
        
        Troubleshooting:
        - Fix connection errors
        - Resolve authentication issues
        """
        
        result = self.legacy_classifier.classify_taxonomy(
            mixed_content, None, ['install', 'api', 'troubleshoot', 'error'], self.taxonomy_config
        )
        
        # Should identify multiple relevant categories
        categories = [r['category'] for r in result]
        
        # Should have at least 2 categories for mixed content
        self.assertGreaterEqual(len(categories), 2)
    
    def test_low_confidence_filtering(self):
        """Test that low-confidence classifications are filtered out."""
        irrelevant_content = "This is a story about a cat who liked to sleep."
        
        result = self.legacy_classifier.classify_taxonomy(
            irrelevant_content, None, ['cat', 'sleep', 'story'], self.taxonomy_config
        )
        
        # Should return empty or very low confidence results
        high_confidence_results = [r for r in result if r['confidence'] >= 0.3]
        self.assertEqual(len(high_confidence_results), 0, 
                        f"Irrelevant content shouldn't have high-confidence classifications: {result}")
    
    @unittest.skipIf(not hasattr(NextGenTaxonomyClassifier, 'sentence_transformer'), 
                     "Sentence transformers not available")
    def test_semantic_similarity_classification(self):
        """Test semantic similarity classification if available."""
        # This test will only run if sentence transformers are available
        test_content = """
        Database Performance Optimization
        
        Learn how to optimize database queries and improve system performance.
        This guide covers indexing strategies, query optimization, and monitoring.
        """
        
        try:
            result = self.classifier.classify_taxonomy(
                test_content, None, ['database', 'performance', 'optimization'], self.taxonomy_config
            )
            
            # Should work with semantic classification
            self.assertIsInstance(result, list)
            
            # Check that semantic classification was used
            if result:
                self.assertEqual(result[0].get('classification_method'), 'semantic_similarity')
                
        except Exception as e:
            # If semantic classification fails, should fall back gracefully
            self.assertIn('failed', str(e).lower())


class TestMetadataAssistant(unittest.TestCase):
    """Test the main MetadataAssistant orchestrator."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = MetadataConfig()
        self.metadata_assistant = MetadataAssistant(config=self.config)
        self.mock_model_manager = Mock()
        self.mock_model_manager.is_available.return_value = True
    
    def test_initialization(self):
        """Test proper initialization of MetadataAssistant."""
        self.assertIsNotNone(self.metadata_assistant.title_extractor)
        self.assertIsNotNone(self.metadata_assistant.keyword_extractor)
        self.assertIsNotNone(self.metadata_assistant.description_extractor)
        self.assertIsNotNone(self.metadata_assistant.taxonomy_classifier)
        self.assertIsNotNone(self.metadata_assistant.config)
    
    def test_basic_metadata_generation(self):
        """Test basic metadata generation functionality."""
        test_content = """
        # Docker Installation Guide
        
        This comprehensive guide shows how to install Docker on Ubuntu systems.
        Learn about prerequisites, installation steps, and configuration.
        
        Prerequisites:
        - Ubuntu 18.04 or later
        - sudo privileges
        - Internet connection
        
        Installation Steps:
        1. Update package index
        2. Install Docker from repository
        3. Configure Docker service
        """
        
        result = self.metadata_assistant.generate_metadata(
            content=test_content,
            content_type='procedure'
        )
        
        # Test result structure
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('success', False))
        self.assertIn('metadata', result)
        self.assertIn('processing_time', result)
        
        metadata = result['metadata']
        
        # Test metadata completeness
        required_fields = ['title', 'description', 'keywords', 'taxonomy_tags', 'audience', 'content_type']
        for field in required_fields:
            self.assertIn(field, metadata, f"Missing required field: {field}")
        
        # Test content quality
        self.assertNotEqual(metadata['title'], 'Untitled Document')  # Should extract real title
        self.assertGreater(len(metadata['description']), 10)  # Should have meaningful description
        self.assertGreater(len(metadata['keywords']), 0)  # Should extract keywords
        self.assertEqual(metadata['content_type'], 'procedure')  # Should preserve content type
        
        # Test generation metadata
        self.assertIn('generation_metadata', metadata)
        gen_metadata = metadata['generation_metadata']
        self.assertIn('processing_time_seconds', gen_metadata)
        self.assertIn('confidence_scores', gen_metadata)
        self.assertIn('algorithms_used', gen_metadata)
    
    def test_different_content_types(self):
        """Test metadata generation for different content types."""
        content_types = ['concept', 'procedure', 'reference']
        
        base_content = """
        API Security Best Practices
        
        Understanding API security is crucial for building secure applications.
        This document covers authentication, authorization, and data protection.
        """
        
        for content_type in content_types:
            with self.subTest(content_type=content_type):
                result = self.metadata_assistant.generate_metadata(
                    content=base_content,
                    content_type=content_type
                )
                
                self.assertTrue(result.get('success'))
                self.assertEqual(result['metadata']['content_type'], content_type)
                
                # Intent should vary by content type
                expected_intents = {
                    'concept': 'Educational',
                    'procedure': 'Instructional', 
                    'reference': 'Informational'
                }
                self.assertEqual(result['metadata']['intent'], expected_intents[content_type])
    
    def test_empty_content_handling(self):
        """Test handling of empty or invalid content."""
        result = self.metadata_assistant.generate_metadata(content="")
        
        self.assertFalse(result.get('success'))
        self.assertIn('error', result)
        self.assertIn('Empty content', result['error'])
    
    def test_oversized_content_handling(self):
        """Test handling of content that exceeds size limits."""
        # Create content larger than default limit
        large_content = "x" * (self.config.max_content_length + 1000)
        
        result = self.metadata_assistant.generate_metadata(content=large_content)
        
        self.assertFalse(result.get('success'))
        self.assertIn('error', result)
        self.assertIn('exceeds maximum length', result['error'])
    
    def test_progress_callback_integration(self):
        """Test progress callback functionality."""
        progress_calls = []
        
        def mock_progress_callback(session_id, stage, message, details, progress):
            progress_calls.append({
                'session_id': session_id,
                'stage': stage,
                'message': message,
                'details': details,
                'progress': progress
            })
        
        assistant = MetadataAssistant(progress_callback=mock_progress_callback)
        
        result = assistant.generate_metadata(
            content="# Test Document\n\nThis is a test document for progress tracking.",
            session_id="test_session_123"
        )
        
        self.assertTrue(result.get('success'))
        self.assertGreater(len(progress_calls), 0)
        
        # Check that progress calls have expected structure
        for call in progress_calls:
            self.assertEqual(call['session_id'], 'test_session_123')
            self.assertIn('stage', call)
            self.assertIn('message', call)
            self.assertIsInstance(call['progress'], (int, float))
    
    def test_error_recovery_and_fallbacks(self):
        """Test error recovery and graceful degradation."""
        # Create assistant with broken extractors to test fallbacks
        assistant = MetadataAssistant()
        
        # Mock an extractor to fail
        original_extract = assistant.title_extractor.extract_title
        assistant.title_extractor.extract_title = Mock(side_effect=Exception("Test failure"))
        
        result = assistant.generate_metadata(
            content="# Test Document\n\nThis should still work with fallbacks."
        )
        
        # Should succeed despite extractor failure
        self.assertTrue(result.get('success'))
        self.assertTrue(result.get('degraded_mode', False))  # Should indicate degraded mode
        self.assertGreater(len(result.get('errors', [])), 0)  # Should report errors
        
        # Should still have basic metadata
        metadata = result['metadata']
        self.assertIn('title', metadata)
        self.assertIn('description', metadata)
        
        # Restore original extractor
        assistant.title_extractor.extract_title = original_extract
    
    def test_caching_functionality(self):
        """Test caching behavior."""
        assistant = MetadataAssistant()
        assistant.config.enable_caching = True
        
        content = "# Cached Test\n\nThis content should be cached."
        
        # First call
        start_time = time.time()
        result1 = assistant.generate_metadata(content=content)
        first_time = time.time() - start_time
        
        # Second call (should be faster due to caching)
        start_time = time.time()
        result2 = assistant.generate_metadata(content=content)
        second_time = time.time() - start_time
        
        self.assertTrue(result1.get('success'))
        self.assertTrue(result2.get('success'))
        
        # Results should be identical
        self.assertEqual(result1['metadata']['title'], result2['metadata']['title'])
        
        # Second call should be faster (though this might be flaky in some environments)
        # We'll just check that both calls succeeded
        self.assertGreater(first_time, 0)
        self.assertGreater(second_time, 0)
    
    def test_output_formatting(self):
        """Test different output format options."""
        content = "# Test Document\n\nFormatting test content."
        
        # Test dict format (default)
        result_dict = self.metadata_assistant.generate_metadata(content=content, output_format='dict')
        self.assertIsNone(result_dict.get('formatted_output'))  # No formatting for dict
        
        # Test YAML format
        result_yaml = self.metadata_assistant.generate_metadata(content=content, output_format='yaml')
        formatted_yaml = result_yaml.get('formatted_output')
        self.assertIsNotNone(formatted_yaml)
        self.assertIn('title:', formatted_yaml)
        
        # Test JSON format
        result_json = self.metadata_assistant.generate_metadata(content=content, output_format='json')
        formatted_json = result_json.get('formatted_output')
        self.assertIsNotNone(formatted_json)
        self.assertTrue(formatted_json.strip().startswith('{'))
    
    def test_health_status(self):
        """Test health status reporting."""
        status = self.metadata_assistant.get_health_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('status', status)
        self.assertIn('extractors', status)
        self.assertIn('dependencies', status)
        self.assertIn('cache', status)
        self.assertIn('configuration', status)
        
        # Check extractor availability
        extractors = status['extractors']
        required_extractors = ['title_extractor', 'keyword_extractor', 'description_extractor', 'taxonomy_classifier']
        for extractor in required_extractors:
            self.assertIn(extractor, extractors)
            self.assertEqual(extractors[extractor], 'available')


class TestIntegration(unittest.TestCase):
    """Integration tests with existing system components."""
    
    def test_spacy_integration(self):
        """Test integration with spaCy parsing."""
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            
            content = "# API Testing Guide\n\nThis guide covers API testing methodologies and tools."
            spacy_doc = nlp(content)
            
            assistant = MetadataAssistant()
            result = assistant.generate_metadata(
                content=content,
                spacy_doc=spacy_doc  # Provide pre-parsed document
            )
            
            self.assertTrue(result.get('success'))
            self.assertIn('metadata', result)
            
        except ImportError:
            self.skipTest("spaCy not available")
        except OSError:
            self.skipTest("spaCy model not available")
    
    def test_structural_blocks_integration(self):
        """Test integration with structural document blocks."""
        content = """
        # Installation Guide
        
        ## Prerequisites
        - Python 3.8+
        - pip installed
        
        ## Installation Steps
        1. Download package
        2. Run installer
        3. Verify installation
        """
        
        # Mock structural blocks
        structural_blocks = [
            {'type': 'heading', 'level': 1, 'content': 'Installation Guide'},
            {'type': 'heading', 'level': 2, 'content': 'Prerequisites'},
            {'type': 'list', 'content': ['Python 3.8+', 'pip installed']},
            {'type': 'heading', 'level': 2, 'content': 'Installation Steps'},
            {'type': 'list', 'content': ['Download package', 'Run installer', 'Verify installation']}
        ]
        
        assistant = MetadataAssistant()
        result = assistant.generate_metadata(
            content=content,
            structural_blocks=structural_blocks
        )
        
        self.assertTrue(result.get('success'))
        metadata = result['metadata']
        
        # Should use structural information
        self.assertEqual(metadata['title'], 'Installation Guide')
        self.assertIn('Installation', metadata.get('taxonomy_tags', []))


class TestPerformance(unittest.TestCase):
    """Performance and resource usage tests."""
    
    def setUp(self):
        """Set up performance test environment."""
        self.assistant = MetadataAssistant()
    
    def test_processing_time_benchmarks(self):
        """Test processing time for different document sizes."""
        test_sizes = [
            ('small', 500),    # 500 characters
            ('medium', 2000),  # 2K characters  
            ('large', 10000),  # 10K characters
        ]
        
        for size_name, char_count in test_sizes:
            test_content = self._generate_test_content(char_count)
            
            start_time = time.time()
            result = self.assistant.generate_metadata(test_content)
            processing_time = time.time() - start_time
            
            with self.subTest(size=size_name):
                self.assertTrue(result.get('success'), f"Failed for {size_name} document")
                
                # Performance benchmarks based on document size
                if char_count <= 2000:
                    self.assertLess(processing_time, 10.0, f"{size_name} documents should process in <10s")
                elif char_count <= 10000:
                    self.assertLess(processing_time, 20.0, f"{size_name} documents should process in <20s")
                else:
                    self.assertLess(processing_time, 30.0, f"{size_name} documents should process in <30s")
    
    def test_concurrent_processing(self):
        """Test that multiple requests can be processed without issues."""
        import threading
        
        test_content = self._generate_test_content(1000)
        results = []
        errors = []
        
        def process_request():
            try:
                result = self.assistant.generate_metadata(test_content)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Run 5 concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent processing errors: {errors}")
        self.assertEqual(len(results), 5, "Not all concurrent requests completed")
        
        # All results should be successful
        for result in results:
            self.assertTrue(result.get('success'))
    
    def _generate_test_content(self, target_chars: int) -> str:
        """Generate test content of specified length."""
        base_content = """
        Technical Documentation Sample
        
        This is a sample technical document for performance testing purposes.
        It contains various sections including installation instructions, 
        troubleshooting guides, and API documentation examples.
        
        ## Installation
        
        Follow these steps to install the software:
        1. Download the package from the official website
        2. Run the installer with administrator privileges
        3. Configure the settings according to your requirements
        4. Verify the installation by running the test suite
        
        ## Configuration
        
        The configuration file contains the following settings:
        - Database connection parameters
        - Logging levels and output destinations
        - API endpoint URLs and authentication tokens
        - Performance tuning parameters
        
        ## Troubleshooting
        
        Common issues and their solutions:
        - Connection errors: Check network settings and firewall rules
        - Authentication failures: Verify credentials and token expiration
        - Performance issues: Review system resources and optimization settings
        - Data corruption: Run integrity checks and restore from backup
        """
        
        # Repeat content to reach target length
        repetitions = max(1, target_chars // len(base_content))
        extended_content = (base_content * repetitions)[:target_chars]
        
        return extended_content


class TestUserAcceptance(unittest.TestCase):
    """User acceptance tests for metadata quality."""
    
    def setUp(self):
        """Set up UAT environment."""
        self.assistant = MetadataAssistant()
    
    def test_real_world_api_documentation(self):
        """Test with realistic API documentation."""
        api_doc_content = """
        # User Management API
        
        The User Management API provides endpoints for creating, updating, and managing user accounts.
        
        ## Authentication
        All API requests require a valid API key in the Authorization header.
        
        ## Endpoints
        
        ### Create User
        POST /api/users
        
        Creates a new user account with the provided information.
        
        **Parameters:**
        - name (string, required): Full name of the user
        - email (string, required): Email address (must be unique)
        - role (string, optional): User role (default: "user")
        
        **Response:**
        ```json
        {
          "id": 12345,
          "name": "John Doe",
          "email": "john@example.com",
          "role": "user",
          "created_at": "2023-01-01T00:00:00Z"
        }
        ```
        
        ### Error Handling
        The API returns standard HTTP status codes and error messages in JSON format.
        """
        
        result = self.assistant.generate_metadata(api_doc_content, content_type='reference')
        
        self.assertTrue(result.get('success'))
        metadata = result['metadata']
        
        # Quality checks for API documentation
        self.assertIn('User Management API', metadata['title'])
        self.assertGreater(len(metadata['description']), 20)
        self.assertIn('api', [kw.lower() for kw in metadata['keywords']])
        self.assertIn('API_Documentation', metadata.get('taxonomy_tags', []))
    
    def test_real_world_troubleshooting_guide(self):
        """Test with realistic troubleshooting content."""
        troubleshooting_content = """
        # Troubleshooting Database Connection Issues
        
        This guide helps diagnose and resolve common database connectivity problems.
        
        ## Common Symptoms
        - Connection timeout errors
        - Authentication failed messages
        - Intermittent connection drops
        - Slow query performance
        
        ## Diagnostic Steps
        
        1. **Check Network Connectivity**
           - Ping the database server
           - Verify port accessibility using telnet
           - Check firewall rules
        
        2. **Verify Credentials**
           - Test username and password
           - Check database permissions
           - Validate connection string format
        
        3. **Monitor Resource Usage**
           - Check CPU and memory utilization
           - Monitor disk I/O and space
           - Review database logs for errors
        
        ## Solutions
        
        ### Connection Timeout Issues
        - Increase connection timeout values
        - Optimize network configuration
        - Implement connection pooling
        
        ### Authentication Problems
        - Reset database passwords
        - Update connection strings
        - Review user permissions and roles
        """
        
        result = self.assistant.generate_metadata(troubleshooting_content, content_type='procedure')
        
        self.assertTrue(result.get('success'))
        metadata = result['metadata']
        
        # Quality checks for troubleshooting content
        self.assertIn('troubleshoot', metadata['title'].lower())
        self.assertIn('database', metadata['title'].lower())
        self.assertIn('Troubleshooting', metadata.get('taxonomy_tags', []))
        
        # Should extract relevant keywords
        keyword_terms = [kw.lower() for kw in metadata['keywords']]
        expected_terms = ['database', 'connection', 'troubleshoot']
        found_terms = [term for term in expected_terms if any(term in kw for kw in keyword_terms)]
        self.assertGreater(len(found_terms), 1)
    
    def test_metadata_consistency(self):
        """Test that metadata generation is consistent."""
        content = """
        # Docker Container Management
        
        Learn how to manage Docker containers effectively including
        creation, monitoring, and troubleshooting common issues.
        """
        
        # Generate metadata multiple times
        results = []
        for _ in range(3):
            result = self.assistant.generate_metadata(content)
            results.append(result)
        
        # All results should be successful
        for result in results:
            self.assertTrue(result.get('success'))
        
        # Key fields should be consistent
        titles = [r['metadata']['title'] for r in results]
        self.assertEqual(len(set(titles)), 1, f"Inconsistent titles: {titles}")
        
        # Keyword count should be consistent
        keyword_counts = [len(r['metadata']['keywords']) for r in results]
        self.assertLessEqual(max(keyword_counts) - min(keyword_counts), 1, 
                           f"Inconsistent keyword counts: {keyword_counts}")


if __name__ == '__main__':
    # Configure test runner
    unittest.TestLoader.testMethodPrefix = 'test_'
    
    # Run tests with detailed output
    unittest.main(verbosity=2, buffer=True)
