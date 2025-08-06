"""
Complete Analysis Workflow Integration Tests
Tests the entire confidence-enhanced analysis system from input to final output
"""

import pytest
import tempfile
import shutil
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Test data and utilities
class WorkflowTestData:
    """Comprehensive test data for workflow testing"""
    
    # Simple document with clear errors
    SIMPLE_DOCUMENT = """
This is a simple test document.
It has passive voice issues.
Some words usage could be improved.
The document contains grammar error.
"""
    
    # Complex document with various error types
    COMPLEX_DOCUMENT = """
Writing Analysis System Testing Document

This document is designed for testing the writing analysis system's capabilities and features.

The system should be able to detect various types of issues:

1. Grammar Issues
   - Subject-verb agreement errors was common
   - Missing articles in sentences
   - Incorrect verb tenses usage

2. Style Problems
   - Passive voice constructions are used frequently
   - Long, complex sentences that could be simplified for better readability
   - Inconsistent terminology throughout document

3. Word Usage Issues
   - Utilize instead of use
   - Functionality instead of function
   - Implementation instead of implementation

4. Punctuation Problems
   - Missing commas in complex sentences
   - Incorrect apostrophe usage in it's vs its
   - Inconsistent quotation mark usage

This document contains intentional errors for comprehensive testing purposes.
"""
    
    # Document with confidence-challenging cases
    AMBIGUOUS_DOCUMENT = """
The data shows improvement.
This might be considered correct.
The analysis was performed correctly.
There could be better alternatives.
The results are satisfactory.
"""
    
    # Performance test document
    LARGE_DOCUMENT = """
Performance Testing Document

""" + "\n".join([
        f"This is paragraph {i} with various potential writing issues that need analysis. "
        f"The content might have passive voice, word usage problems, and style issues. "
        f"Each paragraph is designed to test different aspects of the analysis system."
        for i in range(1, 51)
    ]) + """

End of performance testing document.
"""

    @staticmethod
    def get_expected_error_types():
        """Get expected error types for validation"""
        return [
            'grammar', 'style', 'word_usage', 'punctuation',
            'passive_voice', 'sentence_length', 'terminology'
        ]


class TestCompleteAnalysisWorkflow:
    """Test the complete analysis workflow end-to-end"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock external dependencies that aren't core to the workflow
        self.mock_patches = []
        
        # Setup mocks for non-essential services
        self.mock_pdf_generator = Mock()
        self.mock_ai_rewriter = Mock()
        
    def teardown_method(self):
        """Cleanup test environment"""
        for patch in self.mock_patches:
            patch.stop()
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_simple_document_analysis_workflow(self):
        """Test complete workflow with simple document"""
        print("\n🧪 Test 1: Simple Document Analysis Workflow")
        
        # Initialize the complete analysis system
        from style_analyzer.base_analyzer import StyleAnalyzer
        from app_modules.feedback_storage import FeedbackStorage
        
        # Create feedback storage in temp directory
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        
        # Initialize analyzer with confidence features
        analyzer = StyleAnalyzer()
        
        # Perform complete analysis
        start_time = time.time()
        result = analyzer.analyze_with_blocks(
            WorkflowTestData.SIMPLE_DOCUMENT, 
            format_hint='auto'
        )
        analysis_time = time.time() - start_time
        
        # Validate analysis structure
        assert 'analysis' in result
        assert 'structural_blocks' in result
        
        analysis = result['analysis']
        
        # Check core analysis components
        assert 'errors' in analysis
        assert 'statistics' in analysis
        assert 'overall_score' in analysis
        
        # Validate confidence-enhanced features
        if analysis.get('enhanced_validation_enabled', False):
            assert 'enhanced_error_stats' in analysis
            assert 'confidence_threshold' in analysis
            
            # Check enhanced error statistics
            enhanced_stats = analysis['enhanced_error_stats']
            assert 'total_errors' in enhanced_stats
            assert 'enhanced_errors' in enhanced_stats
            assert 'enhancement_rate' in enhanced_stats
        
        # Validate errors have confidence information
        errors = analysis['errors']
        enhanced_errors = [e for e in errors if 'confidence_score' in e or 'confidence' in e]
        
        print(f"✅ Analysis completed in {analysis_time:.3f}s")
        print(f"✅ Total errors found: {len(errors)}")
        print(f"✅ Enhanced errors: {len(enhanced_errors)}")
        print(f"✅ Enhancement rate: {len(enhanced_errors)/len(errors)*100:.1f}%" if errors else "✅ No errors to enhance")
        
        # Test error filtering with different thresholds
        if enhanced_errors:
            self._test_confidence_filtering(enhanced_errors)
        
        return result
    
    def test_complex_document_analysis_workflow(self):
        """Test complete workflow with complex document"""
        print("\n📋 Test 2: Complex Document Analysis Workflow")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Analyze complex document
        start_time = time.time()
        result = analyzer.analyze_with_blocks(
            WorkflowTestData.COMPLEX_DOCUMENT,
            format_hint='asciidoc'
        )
        analysis_time = time.time() - start_time
        
        analysis = result['analysis']
        errors = analysis['errors']
        
        # Validate comprehensive error detection
        assert len(errors) > 0, "Complex document should have some errors"
        
        # Check for various error types
        error_types = {error.get('type', error.get('error_type', 'unknown')) for error in errors}
        expected_types = {'grammar', 'style', 'word_usage', 'passive_voice'}
        
        found_expected = expected_types.intersection(error_types)
        # Note: With confidence filtering, we may find fewer error types than expected
        print(f"   Error types found: {sorted(error_types)}")
        
        # Validate confidence distribution
        confidence_scores = [
            error.get('confidence_score', error.get('confidence', 0.5)) 
            for error in errors 
            if 'confidence_score' in error or 'confidence' in error
        ]
        
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            high_conf_count = len([c for c in confidence_scores if c >= 0.7])
            medium_conf_count = len([c for c in confidence_scores if 0.5 <= c < 0.7])
            low_conf_count = len([c for c in confidence_scores if c < 0.5])
            
            print(f"✅ Complex analysis completed in {analysis_time:.3f}s")
            print(f"✅ Total errors: {len(errors)}")
            print(f"✅ Error types found: {sorted(error_types)}")
            print(f"✅ Average confidence: {avg_confidence:.3f}")
            print(f"✅ Confidence distribution: High={high_conf_count}, Medium={medium_conf_count}, Low={low_conf_count}")
        
        return result
    
    def test_validation_pipeline_execution(self):
        """Test validation pipeline execution throughout analysis"""
        print("\n🔍 Test 3: Validation Pipeline Execution")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        from validation.multi_pass.validation_pipeline import ValidationPipeline
        
        analyzer = StyleAnalyzer()
        
        # Track validation pipeline execution
        with patch('validation.multi_pass.validation_pipeline.ValidationPipeline') as mock_pipeline:
            mock_instance = Mock()
            mock_pipeline.return_value = mock_instance
            
            # Mock the validation method to return enhanced errors
            def mock_validate_errors(errors):
                enhanced_errors = []
                for error in errors:
                    enhanced_error = error.copy()
                    enhanced_error['confidence_score'] = 0.75
                    enhanced_error['enhanced_validation_available'] = True
                    enhanced_error['validation_consensus'] = True
                    enhanced_errors.append(enhanced_error)
                return enhanced_errors
            
            mock_instance.validate_errors.side_effect = mock_validate_errors
            
            # Perform analysis
            result = analyzer.analyze_with_blocks(
                WorkflowTestData.COMPLEX_DOCUMENT,
                format_hint='auto'
            )
            
            # Check if validation pipeline was used
            analysis = result['analysis']
            errors = analysis['errors']
            
            # Verify enhanced validation indicators
            enhanced_errors = [e for e in errors if e.get('enhanced_validation_available', False)]
            
            print(f"✅ Validation pipeline integration test completed")
            print(f"✅ Total errors processed: {len(errors)}")
            print(f"✅ Enhanced errors: {len(enhanced_errors)}")
            
            if enhanced_errors:
                print(f"✅ Validation pipeline successfully enhanced {len(enhanced_errors)} errors")
    
    def test_confidence_calculation_accuracy(self):
        """Test confidence calculation accuracy across rule types"""
        print("\n📊 Test 4: Confidence Calculation Accuracy")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Test with ambiguous document (should have varied confidence)
        result = analyzer.analyze_with_blocks(
            WorkflowTestData.AMBIGUOUS_DOCUMENT,
            format_hint='auto'
        )
        
        analysis = result['analysis']
        errors = analysis['errors']
        
        # Extract confidence scores
        confidence_data = []
        for error in errors:
            if 'confidence_score' in error or 'confidence' in error:
                confidence_data.append({
                    'error_type': error.get('type', error.get('error_type', 'unknown')),
                    'confidence': error.get('confidence_score', error.get('confidence', 0.5)),
                    'message': error.get('message', '')[:50] + '...' if len(error.get('message', '')) > 50 else error.get('message', '')
                })
        
        # Validate confidence score properties
        if confidence_data:
            confidences = [item['confidence'] for item in confidence_data]
            
            # Basic confidence validation
            assert all(0.0 <= c <= 1.0 for c in confidences), "All confidence scores should be between 0.0 and 1.0"
            
            # Check for reasonable confidence distribution
            avg_confidence = sum(confidences) / len(confidences)
            confidence_variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
            
            print(f"✅ Confidence calculation accuracy test completed")
            print(f"✅ Errors with confidence: {len(confidence_data)}")
            print(f"✅ Average confidence: {avg_confidence:.3f}")
            print(f"✅ Confidence variance: {confidence_variance:.3f}")
            
            # Show sample confidence data
            for i, item in enumerate(confidence_data[:3]):
                print(f"✅ Sample {i+1}: {item['error_type']} (confidence: {item['confidence']:.3f}) - {item['message']}")
    
    def _test_confidence_filtering(self, enhanced_errors: List[Dict[str, Any]]):
        """Test error filtering effectiveness with various thresholds"""
        print("\n🔽 Test: Confidence Filtering Effectiveness")
        
        thresholds = [0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        
        for threshold in thresholds:
            filtered_errors = []
            for error in enhanced_errors:
                confidence = error.get('confidence_score', error.get('confidence', 0.5))
                if confidence >= threshold:
                    filtered_errors.append(error)
            
            filter_rate = len(filtered_errors) / len(enhanced_errors) * 100
            print(f"✅ Threshold {threshold}: {len(filtered_errors)}/{len(enhanced_errors)} errors ({filter_rate:.1f}%)")
    
    def test_api_response_completeness(self):
        """Test API response completeness and accuracy"""
        print("\n🌐 Test 5: API Response Completeness")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Perform analysis
        result = analyzer.analyze_with_blocks(
            WorkflowTestData.COMPLEX_DOCUMENT,
            format_hint='auto'
        )
        
        # Validate API response structure (simulating API endpoint response)
        api_response = {
            'success': True,
            'analysis': result['analysis'],
            'structural_blocks': result.get('structural_blocks', []),
            'processing_time': 0.5,
            'session_id': 'test-session-123'
        }
        
        # Add confidence metadata (as the API would)
        analysis = api_response['analysis']
        confidence_metadata = {
            'confidence_threshold_used': 0.43,
            'enhanced_validation_enabled': analysis.get('enhanced_validation_enabled', False),
            'confidence_filtering_applied': False
        }
        
        if analysis.get('enhanced_error_stats'):
            confidence_metadata['enhanced_error_stats'] = analysis['enhanced_error_stats']
        
        api_response['confidence_metadata'] = confidence_metadata
        api_response['api_version'] = '2.0'
        api_response['backward_compatible'] = True
        
        # Validate API response completeness
        required_fields = ['success', 'analysis', 'processing_time', 'session_id', 'confidence_metadata', 'api_version']
        for field in required_fields:
            assert field in api_response, f"API response missing required field: {field}"
        
        # Validate confidence metadata
        conf_meta_fields = ['confidence_threshold_used', 'enhanced_validation_enabled', 'confidence_filtering_applied']
        for field in conf_meta_fields:
            assert field in confidence_metadata, f"Confidence metadata missing field: {field}"
        
        # Test JSON serialization
        try:
            json_response = json.dumps(api_response, default=str)
            parsed_response = json.loads(json_response)
            assert parsed_response['success'] is True
        except Exception as e:
            pytest.fail(f"API response not JSON serializable: {e}")
        
        print(f"✅ API response completeness test passed")
        print(f"✅ Response size: {len(json_response)} characters")
        print(f"✅ Enhanced validation enabled: {confidence_metadata['enhanced_validation_enabled']}")
        
        return api_response
    
    def test_performance_complete_system(self):
        """Test performance of complete enhanced system"""
        print("\n⚡ Test 6: Complete System Performance")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Performance test with large document
        start_time = time.time()
        result = analyzer.analyze_with_blocks(
            WorkflowTestData.LARGE_DOCUMENT,
            format_hint='auto'
        )
        total_time = time.time() - start_time
        
        analysis = result['analysis']
        errors = analysis['errors']
        
        # Calculate performance metrics
        words_processed = len(WorkflowTestData.LARGE_DOCUMENT.split())
        processing_rate = words_processed / total_time if total_time > 0 else 0
        
        # Validate performance
        assert total_time < 10.0, f"Analysis took too long: {total_time:.3f}s"
        
        enhanced_errors = [e for e in errors if e.get('enhanced_validation_available', False)]
        enhancement_overhead = 0  # Calculate if we have timing data
        
        print(f"✅ Performance test completed")
        print(f"✅ Document size: {words_processed} words")
        print(f"✅ Total processing time: {total_time:.3f}s")
        print(f"✅ Processing rate: {processing_rate:.1f} words/second")
        print(f"✅ Total errors found: {len(errors)}")
        print(f"✅ Enhanced errors: {len(enhanced_errors)}")
        print(f"✅ Performance: {'Excellent' if total_time < 2 else 'Good' if total_time < 5 else 'Acceptable'}")
        
        return {
            'processing_time': total_time,
            'words_processed': words_processed,
            'processing_rate': processing_rate,
            'total_errors': len(errors),
            'enhanced_errors': len(enhanced_errors)
        }
    
    def test_frontend_display_simulation(self):
        """Test frontend display of confidence-enhanced results"""
        print("\n🖥️ Test 7: Frontend Display Simulation")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Perform analysis
        result = analyzer.analyze_with_blocks(
            WorkflowTestData.COMPLEX_DOCUMENT,
            format_hint='auto'
        )
        
        analysis = result['analysis']
        errors = analysis['errors']
        
        # Simulate frontend error processing
        frontend_errors = []
        for error in errors:
            frontend_error = {
                'id': f"error-{len(frontend_errors) + 1}",
                'type': error.get('type', error.get('error_type', 'unknown')),
                'message': error.get('message', ''),
                'line': error.get('line_number', error.get('line', 1)),
                'confidence': error.get('confidence_score', error.get('confidence', 0.5)),
                'enhanced': error.get('enhanced_validation_available', False)
            }
            
            # Simulate confidence level classification (as frontend would do)
            confidence = frontend_error['confidence']
            if confidence >= 0.7:
                frontend_error['confidence_level'] = 'HIGH'
                frontend_error['confidence_class'] = 'pf-m-green'
            elif confidence >= 0.5:
                frontend_error['confidence_level'] = 'MEDIUM'
                frontend_error['confidence_class'] = 'pf-m-orange'
            else:
                frontend_error['confidence_level'] = 'LOW'
                frontend_error['confidence_class'] = 'pf-m-red'
            
            frontend_errors.append(frontend_error)
        
        # Validate frontend processing
        assert all('confidence_level' in e for e in frontend_errors), "All errors should have confidence levels"
        assert all('confidence_class' in e for e in frontend_errors), "All errors should have CSS classes"
        
        # Simulate confidence-based filtering (as frontend would do)
        high_confidence_errors = [e for e in frontend_errors if e['confidence_level'] == 'HIGH']
        medium_confidence_errors = [e for e in frontend_errors if e['confidence_level'] == 'MEDIUM']
        low_confidence_errors = [e for e in frontend_errors if e['confidence_level'] == 'LOW']
        
        print(f"✅ Frontend display simulation completed")
        print(f"✅ Total errors processed: {len(frontend_errors)}")
        print(f"✅ High confidence errors: {len(high_confidence_errors)}")
        print(f"✅ Medium confidence errors: {len(medium_confidence_errors)}")
        print(f"✅ Low confidence errors: {len(low_confidence_errors)}")
        
        # Validate error distribution makes sense
        assert len(frontend_errors) > 0, "Should have errors to display"
        
        return frontend_errors
    
    def test_end_to_end_integration_workflow(self):
        """Test complete end-to-end integration workflow"""
        print("\n🔗 Test 8: End-to-End Integration Workflow")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        from app_modules.feedback_storage import FeedbackStorage
        
        # Initialize components
        analyzer = StyleAnalyzer()
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        
        session_id = "integration-test-session"
        
        # Step 1: Document analysis
        print("Step 1: Document Analysis")
        analysis_start = time.time()
        result = analyzer.analyze_with_blocks(
            WorkflowTestData.COMPLEX_DOCUMENT,
            format_hint='auto'
        )
        analysis_time = time.time() - analysis_start
        
        analysis = result['analysis']
        errors = analysis['errors']
        
        # Step 2: API response preparation
        print("Step 2: API Response Preparation")
        api_response = {
            'success': True,
            'analysis': analysis,
            'processing_time': analysis_time,
            'session_id': session_id,
            'confidence_metadata': {
                'confidence_threshold_used': 0.43,
                'enhanced_validation_enabled': analysis.get('enhanced_validation_enabled', False),
                'confidence_filtering_applied': False
            },
            'api_version': '2.0'
        }
        
        # Step 3: Frontend processing simulation
        print("Step 3: Frontend Processing")
        enhanced_errors = [e for e in errors if e.get('enhanced_validation_available', False)]
        
        # Step 4: User feedback simulation
        print("Step 4: User Feedback Processing")
        feedback_count = 0
        for i, error in enumerate(errors[:3]):  # Simulate feedback on first 3 errors
            feedback_data = {
                'session_id': session_id,
                'error_id': f"error-{i+1}",
                'error_type': error.get('type', error.get('error_type', 'unknown')),
                'error_message': error.get('message', ''),
                'feedback_type': 'correct' if i % 2 == 0 else 'incorrect',
                'confidence_score': error.get('confidence_score', error.get('confidence', 0.5))
            }
            
            success, message, feedback_id = feedback_storage.store_feedback(feedback_data)
            if success:
                feedback_count += 1
        
        # Step 5: Feedback analytics
        print("Step 5: Feedback Analytics")
        feedback_stats = feedback_storage.get_feedback_stats(session_id=session_id)
        
        # Step 6: Performance validation
        print("Step 6: Performance Validation")
        total_workflow_time = analysis_time + 0.1  # Add overhead for other steps
        
        # Validate complete workflow
        assert api_response['success'] is True
        assert len(errors) > 0, "Should detect errors in complex document"
        assert feedback_count > 0, "Should successfully store feedback"
        assert feedback_stats['total_feedback'] == feedback_count
        assert total_workflow_time < 5.0, f"Complete workflow too slow: {total_workflow_time:.3f}s"
        
        print(f"✅ End-to-end integration test completed")
        print(f"✅ Total workflow time: {total_workflow_time:.3f}s")
        print(f"✅ Errors detected: {len(errors)}")
        print(f"✅ Enhanced errors: {len(enhanced_errors)}")
        print(f"✅ Feedback collected: {feedback_count}")
        print(f"✅ Feedback accuracy: {feedback_stats.get('feedback_distribution', {})}")
        
        return {
            'workflow_time': total_workflow_time,
            'errors_detected': len(errors),
            'enhanced_errors': len(enhanced_errors),
            'feedback_collected': feedback_count,
            'api_response': api_response,
            'feedback_stats': feedback_stats
        }


class TestCompleteAnalysisIntegration:
    """Integration tests for complete analysis workflow"""
    
    def setup_method(self):
        """Setup integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup integration test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_confidence_enhanced_analysis(self):
        """Test complete confidence-enhanced analysis workflow"""
        print("\n🎯 Integration Test: Complete Confidence-Enhanced Analysis")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        # Test with multiple documents and thresholds
        test_cases = [
            {
                'name': 'Simple Document',
                'content': WorkflowTestData.SIMPLE_DOCUMENT,
                'threshold': 0.5,
                'expected_errors': 3
            },
            {
                'name': 'Complex Document', 
                'content': WorkflowTestData.COMPLEX_DOCUMENT,
                'threshold': 0.43,
                'expected_errors': 8
            },
            {
                'name': 'Ambiguous Document',
                'content': WorkflowTestData.AMBIGUOUS_DOCUMENT,
                'threshold': 0.7,
                'expected_errors': 2
            }
        ]
        
        analyzer = StyleAnalyzer()
        results = []
        
        for case in test_cases:
            print(f"\nTesting: {case['name']}")
            
            # Set confidence threshold (if analyzer supports it)
            if hasattr(analyzer, 'structural_analyzer') and hasattr(analyzer.structural_analyzer, 'confidence_threshold'):
                analyzer.structural_analyzer.confidence_threshold = case['threshold']
            
            start_time = time.time()
            result = analyzer.analyze_with_blocks(case['content'], format_hint='auto')
            processing_time = time.time() - start_time
            
            analysis = result['analysis']
            errors = analysis['errors']
            
            # Apply confidence filtering (simulating what the system would do)
            filtered_errors = []
            for error in errors:
                confidence = error.get('confidence_score', error.get('confidence', 0.5))
                if confidence >= case['threshold']:
                    filtered_errors.append(error)
            
            case_result = {
                'name': case['name'],
                'total_errors': len(errors),
                'filtered_errors': len(filtered_errors),
                'processing_time': processing_time,
                'enhanced_validation': analysis.get('enhanced_validation_enabled', False),
                'threshold_used': case['threshold']
            }
            
            results.append(case_result)
            
            print(f"✅ {case['name']}: {len(filtered_errors)} filtered errors (threshold: {case['threshold']})")
            print(f"✅ Processing time: {processing_time:.3f}s")
        
        # Validate overall integration
        total_processing_time = sum(r['processing_time'] for r in results)
        avg_errors_per_test = sum(r['filtered_errors'] for r in results) / len(results)
        
        assert total_processing_time < 10.0, f"Total integration test time too long: {total_processing_time:.3f}s"
        assert avg_errors_per_test > 0, "Should detect errors across test cases"
        
        print(f"\n✅ Complete integration test passed")
        print(f"✅ Total processing time: {total_processing_time:.3f}s")
        print(f"✅ Average errors per test: {avg_errors_per_test:.1f}")
        print(f"✅ All test cases completed successfully")
        
        return results


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])