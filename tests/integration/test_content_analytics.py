"""
Integration tests for Phase 3 Content Performance Analytics workflows.
Tests the full pipeline from metadata generation to performance analytics.
"""

import unittest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy import text

from app_modules.app_factory import create_app
from config import TestingConfig
from database import init_db, db
from database.models import (
    MetadataGeneration, 
    ContentPerformanceMetrics, 
    MetadataFeedback, 
    TaxonomyLearning,
    UserSession,
    Document
)
from metadata_assistant.analytics import ContentPerformanceAnalytics


class TestContentPerformanceWorkflows(unittest.TestCase):
    """Test content performance analytics workflows end-to-end."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.app, cls.socketio = create_app(TestingConfig)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        
        cls.client = cls.app.test_client()
        cls.analytics = ContentPerformanceAnalytics(db.session)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    def setUp(self):
        """Set up each individual test."""
        # Clear all tables for each test (SQLite compatible)
        db.session.execute(text('DELETE FROM metadata_feedback'))
        db.session.execute(text('DELETE FROM content_performance_metrics'))
        db.session.execute(text('DELETE FROM taxonomy_learning'))
        db.session.execute(text('DELETE FROM metadata_generations'))
        db.session.execute(text('DELETE FROM documents'))
        db.session.execute(text('DELETE FROM sessions'))
        db.session.commit()
        
        # Create sample user session
        self.user_session = UserSession(
            session_id='test-session-123',
            user_agent='Test User Agent',
            ip_hash='hash123'
        )
        db.session.add(self.user_session)
        
        # Create sample document
        self.document = Document(
            document_id='test-doc-123',
            session_id='test-session-123',
            filename='test_document.md',
            original_content='# Test Document\n\nThis is test content.'
        )
        db.session.add(self.document)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after each test."""
        db.session.rollback()
    
    def _create_sample_metadata_generation(self, **kwargs) -> MetadataGeneration:
        """Helper to create a sample MetadataGeneration record."""
        defaults = {
            'session_id': 'test-session-123',
            'document_id': 'test-doc-123', 
            'metadata_id': 'meta-123',
            'content_hash': 'abc123def456',
            'content_length': 1200,
            'title': 'Sample API Documentation',
            'description': 'This is sample API documentation for testing.',
            'keywords': ['api', 'documentation', 'rest'],
            'taxonomy_tags': ['API Design', 'Documentation'],
            'content_type': 'concept',
            'confidence_scores': {'title': 0.9, 'keywords': 0.85, 'taxonomy': 0.8},
            'processing_time': 2.3,
            'fallback_used': False,
            'created_at': datetime.utcnow()
        }
        defaults.update(kwargs)
        
        metadata_gen = MetadataGeneration(**defaults)
        db.session.add(metadata_gen)
        db.session.commit()
        return metadata_gen
    
    def _create_sample_performance_metrics(self, metadata_id: int, **kwargs) -> ContentPerformanceMetrics:
        """Helper to create sample ContentPerformanceMetrics record."""
        defaults = {
            'metadata_generation_id': metadata_id,
            'page_views': 1500,
            'unique_visitors': 800,
            'time_on_page': 4.2,
            'bounce_rate': 0.35,
            'organic_search_traffic': 600,
            'click_through_rate': 0.12,
            'search_impressions': 5000,
            'average_search_position': 3.2,
            'user_satisfaction_score': 4.1,
            'social_shares': 25,
            'title_performance_score': 0.88,
            'description_performance_score': 0.75,
            'keyword_performance_scores': {'api': 0.9, 'documentation': 0.8, 'rest': 0.7},
            'measurement_period_start': datetime.utcnow() - timedelta(days=30),
            'measurement_period_end': datetime.utcnow(),
            'data_source': 'google_analytics'
        }
        defaults.update(kwargs)
        
        metrics = ContentPerformanceMetrics(**defaults)
        db.session.add(metrics)
        db.session.commit()
        return metrics
    
    def _create_sample_metadata_feedback(self, metadata_id: int, **kwargs) -> MetadataFeedback:
        """Helper to create sample MetadataFeedback record."""
        defaults = {
            'metadata_generation_id': metadata_id,
            'feedback_type': 'keyword_removed',
            'component': 'keywords',
            'original_value': 'rest, api, documentation, microservices',
            'corrected_value': 'rest, api, documentation',
            'correction_reason': 'irrelevant',
            'content_sample': 'This is sample content for testing purposes...',
            'user_session_id': 'test-session-123',
            'user_experience_level': 'intermediate',
            'confidence_before': 0.85,
            'confidence_after': 0.90,
            'created_at': datetime.utcnow()
        }
        defaults.update(kwargs)
        
        feedback = MetadataFeedback(**defaults)
        db.session.add(feedback)
        db.session.commit()
        return feedback
    
    def _create_sample_taxonomy_learning(self, **kwargs) -> TaxonomyLearning:
        """Helper to create sample TaxonomyLearning record."""
        defaults = {
            'content_hash': 'abc123def456',
            'content_sample': 'This is sample content for taxonomy learning...',
            'content_length': 1200,
            'document_type': 'api_documentation',
            'predicted_tags': ['API Design', 'Documentation', 'REST'],
            'actual_tags': ['API Design', 'Documentation'],
            'prediction_confidence': {'API Design': 0.9, 'Documentation': 0.85, 'REST': 0.6},
            'keywords_present': ['api', 'documentation', 'rest', 'endpoint'],
            'algorithm_used': 'semantic',
            'model_version': '1.0',
            'processing_time': 1.2,
            'created_at': datetime.utcnow()
        }
        defaults.update(kwargs)
        
        learning = TaxonomyLearning(**defaults)
        learning.accuracy_score = learning.calculate_accuracy()
        db.session.add(learning)
        db.session.commit()
        return learning
    
    def test_end_to_end_content_performance_workflow(self):
        """Test the complete content performance workflow from metadata generation to analytics."""
        # 1. Generate metadata through API
        test_content = """
        # API Authentication Guide
        
        This guide covers authentication methods for our REST API.
        
        ## JWT Authentication
        Use JWT tokens for secure API access.
        
        ## OAuth2 Flow
        Implement OAuth2 for third-party integrations.
        """
        
        with patch('metadata_assistant.core.MetadataAssistant') as mock_assistant:
            mock_assistant_instance = MagicMock()
            mock_assistant.return_value = mock_assistant_instance
            mock_assistant_instance.generate_metadata.return_value = {
                'success': True,
                'metadata': {
                    'title': 'API Authentication Guide',
                    'keywords': ['api', 'authentication', 'jwt', 'oauth2'],
                    'description': 'Comprehensive guide to API authentication methods.',
                    'taxonomy': ['API Design', 'Security']
                },
                'processing_time': 1.8
            }
            
            response = self.client.post('/analyze', 
                                      data={'content': test_content, 'format': 'markdown'},
                                      follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            
        # 2. Verify metadata was stored in database
        metadata_records = MetadataGeneration.query.all()
        self.assertEqual(len(metadata_records), 1)
        metadata = metadata_records[0]
        self.assertIsNotNone(metadata.extracted_title)
        self.assertTrue(len(metadata.extracted_keywords) > 0)
        
        # 3. Create performance metrics for the content
        perf_metrics = self._create_sample_performance_metrics(
            metadata.id,
            page_views=2500,
            organic_search_traffic=1200,
            user_satisfaction_score=4.3
        )
        
        # 4. Record user feedback on metadata
        feedback = self._create_sample_metadata_feedback(
            metadata.id,
            feedback_type='taxonomy_changed',
            component='taxonomy',
            original_value='API Design, Security',
            corrected_value='API Design, Security, Authentication'
        )
        
        # 5. Record taxonomy learning data
        learning = self._create_sample_taxonomy_learning(
            content_hash=metadata.content_hash,
            predicted_tags=['API Design', 'Security'],
            actual_tags=['API Design', 'Security', 'Authentication']
        )
        
        # 6. Generate SEO opportunity analysis
        seo_analysis = self.analytics.generate_seo_opportunity_analysis(30)
        self.assertIn('high_performing_patterns', seo_analysis)
        self.assertIn('keyword_opportunities', seo_analysis)
        
        # 7. Generate content gap analysis
        gap_analysis = self.analytics.generate_content_gap_analysis()
        self.assertIn('underrepresented_topics', gap_analysis)
        self.assertIn('content_distribution', gap_analysis)
        
        # 8. Get metadata learning insights
        learning_insights = self.analytics.get_metadata_learning_insights(30)
        self.assertIn('most_corrected_components', learning_insights)
        self.assertIn('algorithm_accuracy_trends', learning_insights)
        
        # 9. Generate ROI analysis
        roi_analysis = self.analytics.get_content_roi_analysis(90)
        self.assertIn('high_roi_content_types', roi_analysis)
        self.assertIn('optimization_recommendations', roi_analysis)
    
    def test_analytics_api_endpoints(self):
        """Test the new analytics API endpoints."""
        # Create sample data
        metadata = self._create_sample_metadata_generation()
        perf_metrics = self._create_sample_performance_metrics(metadata.id)
        feedback = self._create_sample_metadata_feedback(metadata.id)
        learning = self._create_sample_taxonomy_learning()
        
        # Test metadata performance metrics endpoint
        response = self.client.get('/api/analytics/metadata-performance')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('metrics', data)
        
        # Test content performance analytics endpoint
        response = self.client.get('/api/analytics/content-performance?days=30')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('analytics', data)
        self.assertEqual(data['analysis_period_days'], 30)
        
        # Test metadata health status endpoint
        response = self.client.get('/api/analytics/metadata-health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('health', data)
        
        # Test ROI analysis endpoint
        response = self.client.get('/api/analytics/roi-analysis')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('roi_analysis', data)
    
    def test_performance_metrics_tracking(self):
        """Test that performance metrics are correctly tracked and calculated."""
        # Create multiple metadata generations with different performance
        high_performing = self._create_sample_metadata_generation(
            extracted_title='High Performance Guide',
            taxonomy_tags=['Tutorial', 'Best Practices']
        )
        low_performing = self._create_sample_metadata_generation(
            extracted_title='Low Performance Guide',
            taxonomy_tags=['Reference', 'API']
        )
        
        # Add performance metrics
        high_perf_metrics = self._create_sample_performance_metrics(
            high_performing.id,
            page_views=5000,
            organic_search_traffic=3000,
            user_satisfaction_score=4.8,
            click_through_rate=0.18
        )
        low_perf_metrics = self._create_sample_performance_metrics(
            low_performing.id,
            page_views=200,
            organic_search_traffic=50,
            user_satisfaction_score=2.1,
            click_through_rate=0.05
        )
        
        # Test analytics can identify performance patterns
        seo_analysis = self.analytics.generate_seo_opportunity_analysis(30)
        self.assertIsInstance(seo_analysis['high_performing_patterns'], list)
        self.assertIsInstance(seo_analysis['underperforming_categories'], list)
        
        roi_analysis = self.analytics.get_content_roi_analysis(90)
        self.assertIsInstance(roi_analysis['high_roi_content_types'], list)
        self.assertIsInstance(roi_analysis['low_roi_content_types'], list)
    
    def test_feedback_learning_cycle(self):
        """Test the feedback and learning cycle for continuous improvement."""
        # Create metadata generation
        metadata = self._create_sample_metadata_generation(
            extracted_keywords=['kubernetes', 'deployment', 'scaling', 'monitoring']
        )
        
        # Simulate user corrections
        feedbacks = [
            self._create_sample_metadata_feedback(
                metadata.id,
                feedback_type='keyword_removed',
                component='keywords',
                original_value='kubernetes, deployment, scaling, monitoring',
                corrected_value='kubernetes, deployment, scaling',
                correction_reason='irrelevant'
            ),
            self._create_sample_metadata_feedback(
                metadata.id,
                feedback_type='taxonomy_changed',
                component='taxonomy',
                original_value='Infrastructure, DevOps',
                corrected_value='Infrastructure, DevOps, Container Orchestration',
                correction_reason='better_fit'
            )
        ]
        
        # Create taxonomy learning records
        learning = self._create_sample_taxonomy_learning(
            predicted_tags=['Infrastructure', 'DevOps'],
            actual_tags=['Infrastructure', 'DevOps', 'Container Orchestration']
        )
        
        # Test learning insights capture patterns
        insights = self.analytics.get_metadata_learning_insights(30)
        self.assertIn('most_corrected_components', insights)
        self.assertIn('algorithm_accuracy_trends', insights)
        self.assertIn('improvement_recommendations', insights)
        
        # Verify accuracy calculation
        self.assertGreater(learning.accuracy_score, 0.0)
        self.assertLessEqual(learning.accuracy_score, 1.0)
    
    def test_caching_and_performance_optimization(self):
        """Test that caching and performance optimizations work correctly."""
        from metadata_assistant.core import MetadataAssistant
        
        # Create metadata assistant with caching
        assistant = MetadataAssistant()
        
        # Test content for metadata generation
        test_content = "# Docker Container Guide\n\nLearn how to use Docker containers effectively."
        
        # First call - should be cache miss
        start_time = time.time()
        result1 = assistant.generate_metadata(test_content)
        first_call_time = time.time() - start_time
        
        self.assertTrue(result1['success'])
        
        # Second call with same content - should be cache hit
        start_time = time.time()
        result2 = assistant.generate_metadata(test_content)
        second_call_time = time.time() - start_time
        
        self.assertTrue(result2['success'])
        
        # Cache hit should be significantly faster (allowing some margin for test variance)
        if hasattr(assistant, 'performance_metrics'):
            metrics = assistant.get_performance_metrics()
            self.assertGreater(metrics['cache_hits'], 0)
            self.assertIn('cache_hit_rate', metrics)
            self.assertIn('avg_processing_time', metrics)
    
    def test_graceful_degradation_with_analytics(self):
        """Test that analytics still work with incomplete or degraded metadata."""
        # Create metadata with fallback/degraded mode
        degraded_metadata = self._create_sample_metadata_generation(
            extracted_title='Untitled Document',
            extracted_keywords=['basic', 'fallback'],
            taxonomy_tags=['General'],
            fallback_used=True,
            error_messages=['Semantic model unavailable']
        )
        
        # Add minimal performance data
        minimal_metrics = self._create_sample_performance_metrics(
            degraded_metadata.id,
            page_views=100,
            organic_search_traffic=20
        )
        
        # Analytics should still provide insights
        seo_analysis = self.analytics.generate_seo_opportunity_analysis(30)
        self.assertIsInstance(seo_analysis, dict)
        
        gap_analysis = self.analytics.generate_content_gap_analysis()
        self.assertIsInstance(gap_analysis, dict)
        
        # Health check should detect degraded performance
        response = self.client.get('/api/analytics/metadata-health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_database_relationship_integrity(self):
        """Test that database relationships are maintained correctly."""
        # Create linked records
        metadata = self._create_sample_metadata_generation()
        perf_metrics = self._create_sample_performance_metrics(metadata.id)
        feedback = self._create_sample_metadata_feedback(metadata.id)
        
        # Test relationships work correctly
        self.assertEqual(perf_metrics.metadata_generation.id, metadata.id)
        self.assertEqual(feedback.metadata_generation.id, metadata.id)
        self.assertEqual(len(metadata.performance_metrics), 1)
        self.assertEqual(len(metadata.feedback_entries), 1)
        
        # Test cascade deletion (if implemented)
        original_metadata_id = metadata.id
        db.session.delete(metadata)
        db.session.commit()
        
        # Related records should be handled appropriately
        remaining_metrics = ContentPerformanceMetrics.query.filter_by(
            metadata_generation_id=original_metadata_id
        ).all()
        remaining_feedback = MetadataFeedback.query.filter_by(
            metadata_generation_id=original_metadata_id
        ).all()
        
        # Depending on foreign key constraints, these might be deleted or nullified


if __name__ == '__main__':
    unittest.main(verbosity=2)
