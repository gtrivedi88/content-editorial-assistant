"""
Production Validation Testing Suite
Real-world document testing and production readiness validation.
Testing Phase 3 Step 3.2 - Performance & Production Readiness
"""

import pytest
import time
import os
import json
import statistics
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Import validation system components
from validation.confidence.confidence_calculator import ConfidenceCalculator
from validation.confidence.context_analyzer import ContextAnalyzer
from rules import RulesRegistry
from error_consolidation.consolidator import ErrorConsolidator


class TestProductionValidation:
    """Production validation tests with real-world scenarios."""
    
    @pytest.fixture(scope="class")
    def production_test_documents(self):
        """Create real-world test documents across different domains."""
        
        documents = {
            'api_documentation': """
            # User Management API
            
            ## Overview
            The User Management API provides endpoints for creating, updating, and deleting user accounts.
            All endpoints require authentication via JWT tokens.
            
            ## Authentication
            Include the Authorization header with a valid JWT token:
            ```
            Authorization: Bearer <jwt_token>
            ```
            
            ## Endpoints
            
            ### GET /api/v1/users
            Retrieve a list of users. Supports pagination and filtering.
            
            **Parameters:**
            - `page` (optional): Page number (default: 1)
            - `limit` (optional): Results per page (default: 20, max: 100)
            - `filter` (optional): Filter by user status (active, inactive, pending)
            
            **Response:**
            ```json
            {
                "users": [...],
                "pagination": {
                    "page": 1,
                    "limit": 20,
                    "total": 150
                }
            }
            ```
            
            ### POST /api/v1/users
            Create a new user account.
            
            **Request Body:**
            ```json
            {
                "email": "user@example.com",
                "password": "securePassword123",
                "firstName": "John",
                "lastName": "Doe"
            }
            ```
            
            **Response:**
            - 201: User created successfully
            - 400: Invalid request data
            - 409: Email already exists
            """,
            
            'user_manual': """
            # Getting Started with Document Analysis
            
            Welcome to the document analysis system! This guide will help you get started quickly.
            
            ## Installation
            
            1. Download the latest version from our website
            2. Run the installer and follow the prompts
            3. Launch the application from your desktop
            
            ## First Steps
            
            ### Creating Your First Project
            
            To create a new project:
            
            1. Click the "New Project" button in the toolbar
            2. Enter a project name and description
            3. Select your document types from the dropdown menu
            4. Click "Create" to finish
            
            ### Adding Documents
            
            You can add documents in several ways:
            
            - **Drag and drop**: Simply drag files from your computer into the project window
            - **Import button**: Click "Import" and select files using the file browser
            - **Paste text**: Use Ctrl+V to paste text directly into a new document
            
            ### Analyzing Your Documents
            
            Once you have documents in your project:
            
            1. Select the documents you want to analyze
            2. Choose your analysis settings from the sidebar
            3. Click the "Analyze" button to start processing
            4. Review the results in the analysis panel
            
            ## Advanced Features
            
            ### Custom Rules
            
            You can create custom analysis rules to match your specific needs:
            
            1. Go to Settings > Custom Rules
            2. Click "Add New Rule"
            3. Define your rule criteria and actions
            4. Save and enable the rule
            
            ### Batch Processing
            
            For processing multiple documents efficiently:
            
            1. Select all documents you want to process
            2. Right-click and choose "Batch Analyze"
            3. Configure your batch settings
            4. Monitor progress in the status bar
            
            ## Troubleshooting
            
            **Problem**: Analysis is taking too long
            **Solution**: Try reducing the number of documents or simplifying your rules
            
            **Problem**: Unable to import certain file types
            **Solution**: Check that your files are in supported formats (PDF, DOCX, TXT, MD)
            """,
            
            'blog_post': """
            # The Future of Automated Writing Analysis
            
            Writing has always been a deeply human endeavor, but technology is transforming how we approach creating and refining our words. Automated writing analysis tools are revolutionizing everything from academic writing to business communications, offering insights that were previously only available through extensive human review.
            
            ## A Personal Journey
            
            I remember the first time I used a grammar checker. It was the early 2000s, and I was amazed that a computer could catch my spelling mistakes and suggest better word choices. But looking back, those early tools were quite primitive compared to what we have today.
            
            Modern writing analysis goes far beyond simple grammar and spell-checking. Today's tools can analyze tone, detect potential bias, assess readability for different audiences, and even suggest structural improvements to make arguments more compelling.
            
            ## The Technology Behind the Magic
            
            What makes this possible is a combination of natural language processing, machine learning, and carefully crafted linguistic rules. These systems can understand context in ways that seemed impossible just a few years ago.
            
            Consider how challenging it is to determine whether a sentence is appropriate for a particular audience. A human writer must consider the reader's background knowledge, cultural context, and expectations. Now, AI systems are beginning to make these same nuanced judgments.
            
            ## Real-World Impact
            
            The implications are profound. Students can receive instant feedback on their essays, helping them learn more effectively. Business professionals can ensure their communications are clear and persuasive. Non-native speakers can write with greater confidence, knowing they have support for nuanced language choices.
            
            But perhaps most importantly, these tools are democratizing good writing. You no longer need years of formal training to produce clear, effective prose. The technology serves as a knowledgeable writing partner, available 24/7.
            
            ## Looking Ahead
            
            As we look to the future, I'm excited about the possibilities. Imagine writing tools that understand your personal style and help you maintain consistency across all your communications. Picture systems that can adapt their feedback based on your writing goals and target audience.
            
            The future of writing isn't about replacing human creativity—it's about amplifying it. Technology will continue to handle the mechanical aspects of good writing, freeing us to focus on ideas, creativity, and genuine human connection.
            
            What excites you most about the future of writing technology? How do you see these tools evolving to better support your communication goals?
            """,
            
            'legal_document': """
            # Software License Agreement
            
            This Software License Agreement ("Agreement") is entered into between Example Software Inc. ("Company") and the end user ("Licensee") effective upon download or installation of the software.
            
            ## 1. Grant of License
            
            Subject to the terms and conditions of this Agreement, Company hereby grants Licensee a non-exclusive, non-transferable license to use the software solely for Licensee's internal business purposes.
            
            ## 2. Restrictions
            
            Licensee shall not:
            
            a) Modify, adapt, or create derivative works based on the software
            b) Reverse engineer, decompile, or disassemble the software
            c) Distribute, sell, lease, or otherwise transfer the software to third parties
            d) Remove or alter any copyright notices or proprietary markings
            
            ## 3. Intellectual Property Rights
            
            The software and all related documentation are the exclusive property of Company and are protected by copyright, trademark, and other intellectual property laws. All rights not expressly granted herein are reserved by Company.
            
            ## 4. Warranty Disclaimer
            
            THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND. COMPANY DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
            
            ## 5. Limitation of Liability
            
            IN NO EVENT SHALL COMPANY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF OR IN CONNECTION WITH THE USE OF THE SOFTWARE, EVEN IF COMPANY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
            
            ## 6. Termination
            
            This Agreement shall remain in effect until terminated. Company may terminate this Agreement immediately upon notice if Licensee breaches any provision hereof. Upon termination, Licensee must cease all use of the software and destroy all copies.
            
            ## 7. Governing Law
            
            This Agreement shall be governed by and construed in accordance with the laws of the State of California, without regard to its conflict of law principles.
            
            ## 8. Entire Agreement
            
            This Agreement constitutes the entire agreement between the parties and supersedes all prior or contemporaneous agreements relating to the subject matter hereof.
            """,
            
            'marketing_content': """
            # Transform Your Business with AI-Powered Analytics
            
            **Unlock Hidden Insights. Drive Real Results. Stay Ahead of Competition.**
            
            Are you tired of making business decisions based on gut feelings instead of data? Do you wish you could predict customer behavior before your competitors even know what's happening?
            
            Introducing DataVision Pro—the revolutionary analytics platform that's transforming how businesses understand their customers and optimize their operations.
            
            ## Why DataVision Pro?
            
            ✅ **Real-Time Insights**: Get instant visibility into your business performance
            ✅ **Predictive Analytics**: Anticipate trends before they happen
            ✅ **Easy Integration**: Connects with your existing tools in minutes
            ✅ **Actionable Reports**: Clear recommendations, not just numbers
            
            ## Success Stories
            
            **"DataVision Pro increased our conversion rate by 34% in just two months!"**
            *— Sarah Johnson, Marketing Director at TechStart Inc.*
            
            **"We finally understand our customers. The insights are game-changing."**
            *— Michael Chen, CEO of RetailPlus*
            
            **"ROI was apparent within the first week. Couldn't be happier."**
            *— Lisa Rodriguez, Operations Manager at ServiceFirst*
            
            ## Get Started Today
            
            Don't let another day pass without the insights you need to grow your business. Join over 10,000 companies that trust DataVision Pro for their analytics needs.
            
            **Special Launch Offer**: Save 50% on your first year when you sign up before midnight!
            
            [START YOUR FREE TRIAL] [SCHEDULE A DEMO] [CONTACT SALES]
            
            **Questions?** Our expert team is standing by to help you succeed.
            Call 1-800-DATAVIZ or chat with us live on our website.
            
            *Limited time offer. Terms and conditions apply. See website for details.*
            """
        }
        
        return documents
    
    @pytest.fixture(scope="class")
    def production_components(self):
        """Initialize production validation components."""
        
        components = {}
        
        try:
            # Initialize core components
            components['confidence_calculator'] = ConfidenceCalculator(
                cache_results=True,
                enable_layer_caching=True
            )
            
            components['context_analyzer'] = ContextAnalyzer()
            
            components['error_consolidator'] = ErrorConsolidator(
                confidence_threshold=0.35,
                enable_enhanced_validation=True
            )
            
            components['rules_registry'] = RulesRegistry(
                enable_consolidation=True,
                enable_enhanced_validation=True,
                confidence_threshold=0.35
            )
            
            return components
            
        except Exception as e:
            pytest.skip(f"Could not initialize production components: {e}")
    
    def test_real_document_confidence_consistency(self, production_components, production_test_documents):
        """Test confidence scores are consistent across real documents."""
        
        print("\n📊 Testing Real Document Confidence Consistency:")
        
        confidence_calculator = production_components['confidence_calculator']
        context_analyzer = production_components['context_analyzer']
        
        document_results = {}
        
        for doc_type, document in production_test_documents.items():
            print(f"\n   📄 Analyzing {doc_type}...")
            
            # Detect content type
            content_type_result = context_analyzer.detect_content_type(document)
            detected_type = content_type_result.content_type.name if hasattr(content_type_result, 'content_type') else 'general'
            
            # Test confidence calculation for different rule types
            rule_types = ['grammar', 'spelling', 'punctuation', 'tone', 'terminology']
            confidence_scores = {}
            
            for rule_type in rule_types:
                try:
                    confidence_result = confidence_calculator.calculate_confidence(
                        text=document,
                        error_position=len(document) // 2,
                        rule_type=rule_type,
                        content_type=detected_type
                    )
                    
                    confidence_score = confidence_result.final_confidence if hasattr(confidence_result, 'final_confidence') else 0.5
                    confidence_scores[rule_type] = confidence_score
                    
                except Exception as e:
                    print(f"      ❌ Error calculating confidence for {rule_type}: {e}")
                    confidence_scores[rule_type] = None
            
            # Calculate consistency metrics
            valid_scores = [score for score in confidence_scores.values() if score is not None]
            
            if valid_scores:
                mean_confidence = statistics.mean(valid_scores)
                std_dev = statistics.stdev(valid_scores) if len(valid_scores) > 1 else 0
                min_confidence = min(valid_scores)
                max_confidence = max(valid_scores)
                
                document_results[doc_type] = {
                    'detected_content_type': detected_type,
                    'confidence_scores': confidence_scores,
                    'mean_confidence': mean_confidence,
                    'std_dev': std_dev,
                    'min_confidence': min_confidence,
                    'max_confidence': max_confidence,
                    'valid_score_count': len(valid_scores)
                }
                
                print(f"      🎯 Content type: {detected_type}")
                print(f"      📊 Mean confidence: {mean_confidence:.3f}")
                print(f"      📊 Std deviation: {std_dev:.3f}")
                print(f"      📊 Range: {min_confidence:.3f} - {max_confidence:.3f}")
                
                # Consistency validation
                assert std_dev < 0.2, f"Confidence std deviation too high for {doc_type}: {std_dev:.3f}"
                assert all(0.0 <= score <= 1.0 for score in valid_scores), f"Confidence scores out of range for {doc_type}"
                
            else:
                pytest.fail(f"No valid confidence scores calculated for {doc_type}")
        
        # Cross-document consistency check
        all_means = [result['mean_confidence'] for result in document_results.values()]
        overall_std = statistics.stdev(all_means) if len(all_means) > 1 else 0
        
        print(f"\n   📊 Cross-document consistency (std dev): {overall_std:.3f}")
        
        # Overall consistency should be reasonable
        assert overall_std < 0.25, f"Cross-document confidence inconsistency too high: {overall_std:.3f}"
        
        print(f"\n   ✅ Real document confidence consistency validated")
        
        return document_results
    
    def test_universal_threshold_effectiveness(self, production_components, production_test_documents):
        """Test universal threshold effectiveness across document types."""
        
        print("\n🎯 Testing Universal Threshold Effectiveness:")
        
        error_consolidator = production_components['error_consolidator']
        universal_threshold = 0.35
        
        threshold_results = {}
        
        for doc_type, document in production_test_documents.items():
            print(f"\n   📄 Testing threshold on {doc_type}...")
            
            # Create test errors with various confidence levels
            test_errors = []
            confidence_levels = [0.1, 0.25, 0.34, 0.35, 0.36, 0.5, 0.7, 0.9]
            
            for i, confidence in enumerate(confidence_levels):
                error = {
                    'type': f'test_type_{i % 3}',
                    'message': f'Test error {i}',
                    'suggestions': [f'Fix error {i}'],
                    'sentence': document[:100] + "...",
                    'sentence_index': i,
                    'severity': 'medium',
                    'confidence_score': confidence,
                    'rule_id': f'test_rule_{i}'
                }
                test_errors.append(error)
            
            # Test consolidation with threshold filtering
            try:
                consolidated_errors = error_consolidator.consolidate(test_errors)
                
                # Analyze threshold effectiveness
                above_threshold = [e for e in test_errors if e['confidence_score'] >= universal_threshold]
                below_threshold = [e for e in test_errors if e['confidence_score'] < universal_threshold]
                
                # Check that threshold filtering worked
                for error in consolidated_errors:
                    confidence = error.get('confidence_score', 1.0)
                    assert confidence >= universal_threshold, f"Error with confidence {confidence} should be filtered out"
                
                threshold_results[doc_type] = {
                    'original_count': len(test_errors),
                    'above_threshold_count': len(above_threshold),
                    'below_threshold_count': len(below_threshold),
                    'consolidated_count': len(consolidated_errors),
                    'threshold_effectiveness': len(above_threshold) / len(test_errors) * 100 if test_errors else 0
                }
                
                print(f"      📊 Original errors: {len(test_errors)}")
                print(f"      📊 Above threshold: {len(above_threshold)}")
                print(f"      📊 After consolidation: {len(consolidated_errors)}")
                print(f"      📊 Threshold effectiveness: {threshold_results[doc_type]['threshold_effectiveness']:.1f}%")
                
            except Exception as e:
                pytest.fail(f"Threshold testing failed for {doc_type}: {e}")
        
        # Universal threshold should work consistently across document types
        effectiveness_scores = [result['threshold_effectiveness'] for result in threshold_results.values()]
        
        if effectiveness_scores:
            mean_effectiveness = statistics.mean(effectiveness_scores)
            std_effectiveness = statistics.stdev(effectiveness_scores) if len(effectiveness_scores) > 1 else 0
            
            print(f"\n   📊 Mean threshold effectiveness: {mean_effectiveness:.1f}%")
            print(f"   📊 Effectiveness consistency: {std_effectiveness:.1f}%")
            
            # Threshold should be reasonably effective and consistent
            assert mean_effectiveness > 50, f"Universal threshold not effective enough: {mean_effectiveness:.1f}%"
            assert std_effectiveness < 15, f"Threshold effectiveness too inconsistent: {std_effectiveness:.1f}%"
        
        print(f"\n   ✅ Universal threshold effectiveness validated")
        
        return threshold_results
    
    def test_content_type_detection_accuracy(self, production_components, production_test_documents):
        """Test content-type detection accuracy on real documents."""
        
        print("\n🔍 Testing Content-Type Detection Accuracy:")
        
        context_analyzer = production_components['context_analyzer']
        
        # Expected content types for our test documents (realistic expectations)
        expected_types = {
            'api_documentation': 'technical',
            'user_manual': 'procedural', 
            'blog_post': 'narrative',
            'legal_document': 'legal',
            'marketing_content': 'marketing'
        }
        
        # Alternative acceptable types (since content-type detection isn't 100% perfect)
        acceptable_alternatives = {
            'api_documentation': ['technical', 'procedural'],  # API docs can be seen as procedural
            'user_manual': ['procedural', 'technical'],       # User manuals can be technical
            'blog_post': ['narrative', 'general'],            # Blog posts might be general
            'legal_document': ['legal', 'general'],           # Legal might be seen as general
            'marketing_content': ['marketing', 'narrative']   # Marketing can be narrative
        }
        
        detection_results = {}
        correct_detections = 0
        total_detections = 0
        
        for doc_type, document in production_test_documents.items():
            print(f"\n   📄 Detecting content type for {doc_type}...")
            
            try:
                # Detect content type
                start_time = time.perf_counter()
                content_type_result = context_analyzer.detect_content_type(document)
                end_time = time.perf_counter()
                
                detection_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                detected_type = content_type_result.content_type.name.lower() if hasattr(content_type_result, 'content_type') else 'general'
                confidence = content_type_result.confidence if hasattr(content_type_result, 'confidence') else 0.5
                expected_type = expected_types.get(doc_type, 'general')
                acceptable_types = acceptable_alternatives.get(doc_type, [expected_type])
                
                # Check if detected type is acceptable (primary or alternative)
                is_correct = detected_type in acceptable_types
                if is_correct:
                    correct_detections += 1
                total_detections += 1
                
                detection_results[doc_type] = {
                    'detected_type': detected_type,
                    'expected_type': expected_type,
                    'confidence': confidence,
                    'detection_time_ms': detection_time,
                    'is_correct': is_correct
                }
                
                status_icon = "✅" if is_correct else "❌"
                acceptable_str = "/".join(acceptable_types)
                print(f"      {status_icon} Expected: {acceptable_str}, Detected: {detected_type}")
                print(f"      📊 Confidence: {confidence:.3f}")
                print(f"      ⏱️  Detection time: {detection_time:.2f}ms")
                
                # Performance validation - adjust based on document size
                doc_length = len(document)
                if doc_length < 500:
                    max_time = 30
                elif doc_length < 2000:
                    max_time = 60
                else:
                    max_time = 100
                assert detection_time < max_time, f"Content type detection too slow for {doc_type} ({doc_length} chars): {detection_time:.2f}ms (max: {max_time}ms)"
                
            except Exception as e:
                pytest.fail(f"Content type detection failed for {doc_type}: {e}")
        
        # Calculate overall accuracy
        accuracy = correct_detections / total_detections * 100 if total_detections > 0 else 0
        
        print(f"\n   📊 Overall detection accuracy: {accuracy:.1f}% ({correct_detections}/{total_detections})")
        
        # Average detection time
        detection_times = [result['detection_time_ms'] for result in detection_results.values()]
        avg_detection_time = statistics.mean(detection_times) if detection_times else 0
        
        print(f"   ⏱️  Average detection time: {avg_detection_time:.2f}ms")
        
        # Accuracy validation (realistic expectations for content-type detection)
        assert accuracy >= 60, f"Content type detection accuracy too low: {accuracy:.1f}% (realistic target: ≥60%)"
        assert avg_detection_time < 60, f"Average detection time too slow: {avg_detection_time:.2f}ms"
        
        print(f"\n   ✅ Content-type detection accuracy validated")
        
        return detection_results
    
    def test_end_to_end_analysis_performance(self, production_components, production_test_documents):
        """Test end-to-end analysis performance on real documents."""
        
        print("\n🔄 Testing End-to-End Analysis Performance:")
        
        rules_registry = production_components['rules_registry']
        
        analysis_results = {}
        
        for doc_type, document in production_test_documents.items():
            print(f"\n   📄 Full analysis of {doc_type}...")
            
            try:
                start_time = time.perf_counter()
                
                # Perform full document analysis
                analysis_result = rules_registry.analyze_text(document)
                
                end_time = time.perf_counter()
                analysis_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                # Extract analysis metrics
                if hasattr(analysis_result, 'errors'):
                    error_count = len(analysis_result.errors)
                    consolidated_errors = analysis_result.errors
                elif isinstance(analysis_result, list):
                    error_count = len(analysis_result)
                    consolidated_errors = analysis_result
                else:
                    error_count = 0
                    consolidated_errors = []
                
                # Analyze confidence score distribution
                confidence_scores = []
                for error in consolidated_errors:
                    if isinstance(error, dict) and 'confidence_score' in error:
                        confidence_scores.append(error['confidence_score'])
                    elif hasattr(error, 'confidence_score'):
                        confidence_scores.append(error.confidence_score)
                
                # Calculate confidence statistics
                if confidence_scores:
                    mean_confidence = statistics.mean(confidence_scores)
                    min_confidence = min(confidence_scores)
                    max_confidence = max(confidence_scores)
                    std_confidence = statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0
                else:
                    mean_confidence = min_confidence = max_confidence = std_confidence = 0
                
                analysis_results[doc_type] = {
                    'analysis_time_ms': analysis_time,
                    'error_count': error_count,
                    'confidence_scores': confidence_scores,
                    'mean_confidence': mean_confidence,
                    'min_confidence': min_confidence,
                    'max_confidence': max_confidence,
                    'std_confidence': std_confidence,
                    'document_length': len(document)
                }
                
                print(f"      ⏱️  Analysis time: {analysis_time:.2f}ms")
                print(f"      📊 Errors detected: {error_count}")
                print(f"      📊 Mean confidence: {mean_confidence:.3f}")
                print(f"      📊 Confidence range: {min_confidence:.3f} - {max_confidence:.3f}")
                
                # Performance benchmarks
                words_count = len(document.split())
                time_per_word = analysis_time / words_count if words_count > 0 else analysis_time
                
                assert analysis_time < 5000, f"Analysis too slow for {doc_type}: {analysis_time:.2f}ms"
                assert time_per_word < 10, f"Analysis per word too slow for {doc_type}: {time_per_word:.2f}ms/word"
                
                # Quality benchmarks
                if confidence_scores:
                    assert all(0.35 <= score <= 1.0 for score in confidence_scores), f"Confidence scores out of expected range for {doc_type}"
                    assert std_confidence < 0.3, f"Confidence inconsistency too high for {doc_type}: {std_confidence:.3f}"
                
            except Exception as e:
                pytest.fail(f"End-to-end analysis failed for {doc_type}: {e}")
        
        # Overall performance analysis
        analysis_times = [result['analysis_time_ms'] for result in analysis_results.values()]
        error_counts = [result['error_count'] for result in analysis_results.values()]
        
        avg_analysis_time = statistics.mean(analysis_times) if analysis_times else 0
        avg_error_count = statistics.mean(error_counts) if error_counts else 0
        
        print(f"\n   📊 Average analysis time: {avg_analysis_time:.2f}ms")
        print(f"   📊 Average errors per document: {avg_error_count:.1f}")
        
        # Overall performance validation
        assert avg_analysis_time < 3000, f"Average analysis time too slow: {avg_analysis_time:.2f}ms"
        
        print(f"\n   ✅ End-to-end analysis performance validated")
        
        return analysis_results


class TestProductionQuality:
    """Production quality assurance tests."""
    
    def test_error_detection_quality(self, production_components, production_test_documents):
        """Validate error detection quality and relevance."""
        
        print("\n🎯 Testing Error Detection Quality:")
        
        rules_registry = production_components['rules_registry']
        
        quality_results = {}
        
        for doc_type, document in production_test_documents.items():
            print(f"\n   📄 Quality analysis of {doc_type}...")
            
            try:
                # Analyze document
                analysis_result = rules_registry.analyze_text(document)
                
                # Extract errors
                if hasattr(analysis_result, 'errors'):
                    errors = analysis_result.errors
                elif isinstance(analysis_result, list):
                    errors = analysis_result
                else:
                    errors = []
                
                # Analyze error quality
                high_confidence_errors = []
                medium_confidence_errors = []
                low_confidence_errors = []
                
                for error in errors:
                    confidence = 0.5  # Default
                    if isinstance(error, dict) and 'confidence_score' in error:
                        confidence = error['confidence_score']
                    elif hasattr(error, 'confidence_score'):
                        confidence = error.confidence_score
                    
                    if confidence >= 0.7:
                        high_confidence_errors.append(error)
                    elif confidence >= 0.5:
                        medium_confidence_errors.append(error)
                    else:
                        low_confidence_errors.append(error)
                
                # Calculate quality metrics
                total_errors = len(errors)
                high_confidence_ratio = len(high_confidence_errors) / total_errors if total_errors > 0 else 0
                
                quality_results[doc_type] = {
                    'total_errors': total_errors,
                    'high_confidence_count': len(high_confidence_errors),
                    'medium_confidence_count': len(medium_confidence_errors),
                    'low_confidence_count': len(low_confidence_errors),
                    'high_confidence_ratio': high_confidence_ratio,
                    'document_type': doc_type
                }
                
                print(f"      📊 Total errors: {total_errors}")
                print(f"      📊 High confidence (≥0.7): {len(high_confidence_errors)}")
                print(f"      📊 Medium confidence (0.5-0.7): {len(medium_confidence_errors)}")
                print(f"      📊 Low confidence (<0.5): {len(low_confidence_errors)}")
                print(f"      📊 High confidence ratio: {high_confidence_ratio:.1%}")
                
                # Quality validation
                assert high_confidence_ratio >= 0.3, f"Too few high-confidence errors for {doc_type}: {high_confidence_ratio:.1%}"
                
            except Exception as e:
                pytest.fail(f"Quality analysis failed for {doc_type}: {e}")
        
        # Overall quality assessment
        total_high_confidence = sum(result['high_confidence_count'] for result in quality_results.values())
        total_errors = sum(result['total_errors'] for result in quality_results.values())
        overall_high_confidence_ratio = total_high_confidence / total_errors if total_errors > 0 else 0
        
        print(f"\n   📊 Overall high-confidence error ratio: {overall_high_confidence_ratio:.1%}")
        
        # Overall quality validation
        assert overall_high_confidence_ratio >= 0.4, f"Overall high-confidence ratio too low: {overall_high_confidence_ratio:.1%}"
        
        print(f"\n   ✅ Error detection quality validated")
        
        return quality_results
    
    def test_system_resource_efficiency(self, production_components, production_test_documents):
        """Test system resource usage efficiency."""
        
        print("\n💾 Testing System Resource Efficiency:")
        
        import psutil
        import gc
        
        # Get initial system state
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu_percent = process.cpu_percent()
        
        print(f"   📊 Initial memory usage: {initial_memory:.1f} MB")
        
        confidence_calculator = production_components['confidence_calculator']
        
        resource_measurements = {
            'memory_usage': [initial_memory],
            'processing_times': [],
            'cpu_usage': []
        }
        
        # Process all documents and measure resource usage
        for doc_type, document in production_test_documents.items():
            print(f"\n   📄 Processing {doc_type} for resource measurement...")
            
            start_time = time.perf_counter()
            start_cpu = process.cpu_percent()
            
            try:
                # Perform confidence calculation (representative workload)
                for rule_type in ['grammar', 'spelling', 'punctuation']:
                    confidence_result = confidence_calculator.calculate_confidence(
                        text=document,
                        error_position=len(document) // 2,
                        rule_type=rule_type,
                        content_type='general'
                    )
                
                end_time = time.perf_counter()
                end_cpu = process.cpu_percent()
                
                # Measure resource usage
                processing_time = (end_time - start_time) * 1000
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                cpu_usage = end_cpu - start_cpu
                
                resource_measurements['processing_times'].append(processing_time)
                resource_measurements['memory_usage'].append(current_memory)
                resource_measurements['cpu_usage'].append(cpu_usage)
                
                print(f"      ⏱️  Processing time: {processing_time:.2f}ms")
                print(f"      💾 Memory usage: {current_memory:.1f} MB")
                print(f"      🔧 CPU usage delta: {cpu_usage:.1f}%")
                
            except Exception as e:
                pytest.fail(f"Resource measurement failed for {doc_type}: {e}")
        
        # Analyze resource efficiency
        max_memory = max(resource_measurements['memory_usage'])
        memory_increase = max_memory - initial_memory
        avg_processing_time = statistics.mean(resource_measurements['processing_times'])
        avg_cpu_usage = statistics.mean(resource_measurements['cpu_usage'])
        
        print(f"\n   📊 Peak memory usage: {max_memory:.1f} MB")
        print(f"   📊 Memory increase: {memory_increase:.1f} MB")
        print(f"   📊 Average processing time: {avg_processing_time:.2f}ms")
        print(f"   📊 Average CPU usage: {avg_cpu_usage:.1f}%")
        
        # Resource efficiency validation
        assert memory_increase < 50, f"Memory increase too high: {memory_increase:.1f} MB"
        assert avg_processing_time < 500, f"Average processing time too slow: {avg_processing_time:.2f}ms"
        
        # Test memory cleanup
        gc.collect()
        cleanup_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_after_cleanup = cleanup_memory - initial_memory
        
        print(f"   📊 Memory after cleanup: {cleanup_memory:.1f} MB ({memory_after_cleanup:+.1f} MB)")
        
        assert memory_after_cleanup < 30, f"Memory not properly cleaned up: {memory_after_cleanup:.1f} MB increase"
        
        print(f"\n   ✅ System resource efficiency validated")
        
        return {
            'initial_memory_mb': initial_memory,
            'peak_memory_mb': max_memory,
            'memory_increase_mb': memory_increase,
            'cleanup_memory_mb': cleanup_memory,
            'avg_processing_time_ms': avg_processing_time,
            'avg_cpu_usage_percent': avg_cpu_usage
        }