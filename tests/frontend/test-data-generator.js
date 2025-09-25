/**
 * Test Data Generator for Filter Testing
 * Production-ready test data generation with realistic error distributions
 * 
 * Supports various testing scenarios:
 * - Unit testing with controlled datasets
 * - Performance testing with large datasets
 * - Edge case testing with malformed data
 * - Integration testing with realistic error patterns
 */

/**
 * Generate mock analysis data with configurable error distribution
 * @param {Object} config - Configuration for data generation
 * @returns {Object} - Complete mock analysis result
 */
function generateMockAnalysisData(config = {}) {
    const {
        criticalCount = 2,
        errorCount = 5,
        warningCount = 8,
        suggestionCount = 3,
        includeConsolidated = false,
        includeValidationResults = false,
        includeAdvancedFields = false,
        contentType = 'concept',
        processingTime = 1.23
    } = config;
    
    const errors = [];
    let errorIndex = 0;
    
    // Error type templates with realistic patterns
    const errorTypes = {
        critical: [
            'legal_compliance', 'claims_verification', 'fabrication_risk',
            'personal_information', 'security_violation', 'data_privacy'
        ],
        error: [
            'grammar_error', 'passive_voice', 'unclear_antecedent',
            'ambiguous_pronoun', 'sentence_fragment', 'run_on_sentence'
        ],
        warning: [
            'readability_issue', 'word_choice', 'tone_inconsistency',
            'unclear_modifier', 'vague_quantifier', 'repetition'
        ],
        suggestion: [
            'style_improvement', 'clarity_enhancement', 'conciseness',
            'vocabulary_variation', 'flow_improvement', 'engagement'
        ]
    };
    
    // Generate critical errors
    for (let i = 0; i < criticalCount; i++) {
        const errorType = errorTypes.critical[i % errorTypes.critical.length];
        errors.push(createRealisticError({
            index: errorIndex++,
            type: errorType,
            severityLevel: 'critical',
            confidence: 0.85 + (Math.random() * 0.15),
            includeConsolidated,
            includeValidationResults,
            includeAdvancedFields
        }));
    }
    
    // Generate error-level issues
    for (let i = 0; i < errorCount; i++) {
        const errorType = errorTypes.error[i % errorTypes.error.length];
        errors.push(createRealisticError({
            index: errorIndex++,
            type: errorType,
            severityLevel: 'error',
            confidence: 0.70 + (Math.random() * 0.15),
            includeConsolidated,
            includeValidationResults,
            includeAdvancedFields
        }));
    }
    
    // Generate warnings
    for (let i = 0; i < warningCount; i++) {
        const errorType = errorTypes.warning[i % errorTypes.warning.length];
        errors.push(createRealisticError({
            index: errorIndex++,
            type: errorType,
            severityLevel: 'warning',
            confidence: 0.50 + (Math.random() * 0.20),
            includeConsolidated,
            includeValidationResults,
            includeAdvancedFields
        }));
    }
    
    // Generate suggestions
    for (let i = 0; i < suggestionCount; i++) {
        const errorType = errorTypes.suggestion[i % errorTypes.suggestion.length];
        errors.push(createRealisticError({
            index: errorIndex++,
            type: errorType,
            severityLevel: 'suggestion',
            confidence: 0.30 + (Math.random() * 0.20),
            includeConsolidated,
            includeValidationResults,
            includeAdvancedFields
        }));
    }
    
    // Add some consolidated errors if requested
    if (includeConsolidated && errors.length > 5) {
        const consolidatedError = createConsolidatedError(errors.slice(0, 3));
        errors.push(consolidatedError);
    }
    
    return {
        success: true,
        errors: errors,
        processing_time: processingTime,
        content_type: contentType,
        statistics: generateMockStatistics(errors),
        metadata: {
            generated_at: new Date().toISOString(),
            generator_version: '1.0.0',
            config: config
        }
    };
}

/**
 * Create a realistic error object with optional advanced fields
 * @param {Object} options - Error generation options
 * @returns {Object} - Realistic error object
 */
function createRealisticError(options) {
    const {
        index,
        type,
        severityLevel,
        confidence,
        includeConsolidated = false,
        includeValidationResults = false,
        includeAdvancedFields = false
    } = options;
    
    const severityMap = {
        critical: 'high',
        error: 'medium',
        warning: 'medium',
        suggestion: 'low'
    };
    
    const messageTemplates = {
        legal_compliance: 'This content may violate legal compliance standards. Review required.',
        claims_verification: 'Unsubstantiated claim detected. Provide evidence or modify language.',
        fabrication_risk: 'Content shows high risk of fabrication. Verify accuracy.',
        grammar_error: 'Grammatical error affects readability and professionalism.',
        passive_voice: 'Consider using active voice for clearer communication.',
        readability_issue: 'Sentence structure may impede reader comprehension.',
        style_improvement: 'Content could benefit from stylistic enhancement.'
    };
    
    const suggestionTemplates = {
        legal_compliance: ['Review with legal team', 'Add appropriate disclaimers', 'Modify language to reduce risk'],
        claims_verification: ['Add supporting evidence', 'Use qualifying language', 'Cite reliable sources'],
        fabrication_risk: ['Verify all facts', 'Add uncertainty qualifiers', 'Remove speculative content'],
        grammar_error: ['Check subject-verb agreement', 'Review sentence structure', 'Use grammar checking tools'],
        passive_voice: ['Identify the actor', 'Restructure as active voice', 'Use stronger action verbs']
    };
    
    // Base error object
    const error = {
        type: type,
        message: messageTemplates[type] || `${type.replace(/_/g, ' ')} issue detected`,
        suggestions: suggestionTemplates[type] || [`Fix ${type.replace(/_/g, ' ')} issue`],
        severity: severityMap[severityLevel] || 'medium',
        confidence: confidence,
        confidence_score: confidence, // Alternative field name
        sentence: generateRealisticSentence(type, index),
        sentence_index: index
    };
    
    // Add advanced fields if requested
    if (includeAdvancedFields) {
        error.error_position = Math.floor(Math.random() * 200) + 10;
        error.end_position = error.error_position + Math.floor(Math.random() * 30) + 5;
        error.line_number = Math.floor(index / 5) + 1;
        error.column_number = (index % 5) * 15 + 1;
        error.text_segment = generateTextSegment(type);
        error.context_before = `Context before error ${index}`;
        error.context_after = `Context after error ${index}`;
        
        // Add rule metadata
        error.rule_metadata = {
            rule_version: '2.1.0',
            last_updated: '2024-01-15',
            category: getCategoryForType(type),
            priority: severityLevel
        };
    }
    
    // Add validation results if requested
    if (includeValidationResults) {
        error.validation_result = {
            decision: confidence > 0.7 ? 'accept' : confidence > 0.5 ? 'review' : 'uncertain',
            confidence_score: confidence,
            consensus_score: Math.min(confidence + 0.1, 1.0),
            passes_count: Math.floor(confidence * 5) + 1,
            validation_method: 'multi_pass_consensus',
            validation_timestamp: new Date().toISOString()
        };
    }
    
    return error;
}

/**
 * Generate a realistic sentence for the given error type
 * @param {string} type - Error type
 * @param {number} index - Error index for uniqueness
 * @returns {string} - Realistic sentence
 */
function generateRealisticSentence(type, index) {
    const sentences = {
        legal_compliance: [
            'This product will cure all your health problems within days.',
            'Our service guarantees 100% success in all legal matters.',
            'We can definitely help you avoid all tax obligations legally.'
        ],
        claims_verification: [
            'Studies show that our approach is the most effective available.',
            'Experts agree that this is the best solution on the market.',
            'Research proves this method works better than alternatives.'
        ],
        grammar_error: [
            'The team are working hard on this project.',
            'Each of the students have submitted their assignments.',
            'There is many reasons why this approach works well.'
        ],
        passive_voice: [
            'The report was written by the analysis team.',
            'Mistakes were made during the implementation process.',
            'The decision was reached after careful consideration.'
        ],
        readability_issue: [
            'The implementation of the comprehensive solution methodology requires extensive analysis.',
            'Utilizing sophisticated approaches to problem-solving enables optimal outcomes achievement.',
            'The aforementioned considerations necessitate careful evaluation of alternatives.'
        ]
    };
    
    const typesentences = sentences[type] || [
        'This is a sample sentence with a potential issue.',
        'Another example sentence that demonstrates the problem.',
        'A third sentence showing the error pattern.'
    ];
    
    return typesentences[index % typesentences.length];
}

/**
 * Generate text segment for advanced error fields
 * @param {string} type - Error type
 * @returns {string} - Text segment
 */
function generateTextSegment(type) {
    const segments = {
        legal_compliance: 'will cure all',
        claims_verification: 'studies show',
        grammar_error: 'team are working',
        passive_voice: 'was written by',
        readability_issue: 'aforementioned considerations'
    };
    
    return segments[type] || `${type.replace(/_/g, ' ')} segment`;
}

/**
 * Get category for error type
 * @param {string} type - Error type
 * @returns {string} - Error category
 */
function getCategoryForType(type) {
    const categories = {
        legal_compliance: 'legal',
        claims_verification: 'content',
        fabrication_risk: 'content',
        grammar_error: 'language',
        passive_voice: 'style',
        readability_issue: 'readability',
        style_improvement: 'style'
    };
    
    return categories[type] || 'general';
}

/**
 * Create a consolidated error from multiple base errors
 * @param {Array} baseErrors - Base errors to consolidate
 * @returns {Object} - Consolidated error
 */
function createConsolidatedError(baseErrors) {
    if (!baseErrors || baseErrors.length === 0) {
        return null;
    }
    
    const consolidatedTypes = baseErrors.map(e => e.type).join(', ');
    const avgConfidence = baseErrors.reduce((sum, e) => sum + e.confidence, 0) / baseErrors.length;
    
    return {
        type: 'consolidated_error',
        message: `Multiple issues detected in the same text region: ${consolidatedTypes}`,
        suggestions: ['Review and address each identified issue', 'Consider rewriting this section'],
        severity: 'high',
        confidence: Math.min(avgConfidence * 1.1, 1.0), // Boost confidence for consolidated
        confidence_score: Math.min(avgConfidence * 1.1, 1.0),
        sentence: baseErrors[0].sentence,
        sentence_index: baseErrors[0].sentence_index,
        is_consolidated: true,
        consolidated_from: baseErrors.map(e => ({
            type: e.type,
            confidence: e.confidence,
            original_message: e.message
        })),
        consolidation_type: 'spatial_overlap',
        span_start: 45,
        span_end: 67,
        text_span: 'consolidated text span'
    };
}

/**
 * Generate mock statistics for analysis results
 * @param {Array} errors - Array of errors
 * @returns {Object} - Mock statistics
 */
function generateMockStatistics(errors) {
    const errorCounts = errors.reduce((counts, error) => {
        const severity = error.severity || 'low';
        counts[severity] = (counts[severity] || 0) + 1;
        return counts;
    }, {});
    
    return {
        total_errors: errors.length,
        error_distribution: errorCounts,
        avg_confidence: errors.length > 0 ? 
            errors.reduce((sum, e) => sum + e.confidence, 0) / errors.length : 0,
        sentence_count: Math.max(...errors.map(e => e.sentence_index || 0), 0) + 1,
        word_count: Math.floor(Math.random() * 500) + 200,
        readability_score: Math.random() * 100,
        complexity_score: Math.random() * 10
    };
}

/**
 * Generate edge case test data for robust testing
 * @param {string} caseType - Type of edge case to generate
 * @returns {Object} - Edge case test data
 */
function generateEdgeCaseData(caseType) {
    switch (caseType) {
        case 'empty':
            return {
                success: true,
                errors: [],
                processing_time: 0.1,
                content_type: 'concept'
            };
            
        case 'malformed_errors':
            return {
                success: true,
                errors: [
                    { type: 'test', message: 'Missing confidence' },
                    { confidence: 0.8, message: 'Missing type' },
                    { type: 'incomplete' }, // Missing message
                    null, // Null error
                    undefined, // Undefined error
                    { type: 'weird_confidence', confidence: 'not_a_number' },
                    { type: 'negative_confidence', confidence: -0.5 }
                ],
                processing_time: 0.5,
                content_type: 'concept'
            };
            
        case 'extreme_values':
            return {
                success: true,
                errors: [
                    { type: 'max_confidence', confidence: 1.0, message: 'Maximum confidence' },
                    { type: 'min_confidence', confidence: 0.0, message: 'Minimum confidence' },
                    { type: 'over_confidence', confidence: 1.5, message: 'Over maximum confidence' },
                    { type: 'large_sentence_index', confidence: 0.5, sentence_index: 99999 }
                ],
                processing_time: 0.3,
                content_type: 'concept'
            };
            
        case 'unicode_content':
            return {
                success: true,
                errors: [
                    {
                        type: 'unicode_test',
                        message: 'Error with unicode: 你好世界 🌍 émojis',
                        confidence: 0.7,
                        sentence: 'This sentence contains unicode characters: café, naïve, 日本語',
                        suggestions: ['Handle unicode properly', 'Test with émojis 🎉']
                    }
                ],
                processing_time: 0.4,
                content_type: 'multilingual'
            };
            
        case 'very_large':
            return generateMockAnalysisData({
                criticalCount: 1000,
                errorCount: 2000,
                warningCount: 3000,
                suggestionCount: 4000,
                includeAdvancedFields: true
            });
            
        default:
            return generateMockAnalysisData();
    }
}

/**
 * Generate performance test datasets with specific characteristics
 * @param {string} perfType - Type of performance test
 * @returns {Object} - Performance test data
 */
function generatePerformanceTestData(perfType) {
    switch (perfType) {
        case 'small_balanced':
            return generateMockAnalysisData({
                criticalCount: 5,
                errorCount: 10,
                warningCount: 15,
                suggestionCount: 10
            });
            
        case 'medium_balanced':
            return generateMockAnalysisData({
                criticalCount: 25,
                errorCount: 50,
                warningCount: 75,
                suggestionCount: 50
            });
            
        case 'large_balanced':
            return generateMockAnalysisData({
                criticalCount: 100,
                errorCount: 200,
                warningCount: 300,
                suggestionCount: 400
            });
            
        case 'critical_heavy':
            return generateMockAnalysisData({
                criticalCount: 500,
                errorCount: 100,
                warningCount: 50,
                suggestionCount: 25
            });
            
        case 'suggestion_heavy':
            return generateMockAnalysisData({
                criticalCount: 5,
                errorCount: 10,
                warningCount: 25,
                suggestionCount: 500
            });
            
        default:
            return generateMockAnalysisData();
    }
}

/**
 * Generate realistic content strings for testing display components
 * @param {number} length - Approximate length of content
 * @returns {string} - Realistic content string
 */
function generateRealisticContent(length = 500) {
    const paragraphs = [
        'In the rapidly evolving landscape of modern technology, organizations must adapt their strategies to remain competitive. The integration of artificial intelligence and machine learning has revolutionized how businesses operate, creating new opportunities for growth and innovation.',
        
        'However, with these advancements come significant challenges. Data privacy concerns, ethical considerations, and the need for skilled professionals have become paramount. Companies must carefully balance technological progress with responsible implementation.',
        
        'The future of work is being reshaped by automation and digital transformation. While some traditional roles may become obsolete, new positions requiring different skill sets are emerging. Continuous learning and adaptation have become essential for professional success.',
        
        'Collaboration between humans and machines is becoming increasingly sophisticated. Rather than replacing human workers entirely, technology is augmenting human capabilities and enabling more efficient workflows. This symbiotic relationship represents the next phase of workplace evolution.'
    ];
    
    let content = '';
    while (content.length < length) {
        const paragraph = paragraphs[Math.floor(Math.random() * paragraphs.length)];
        content += paragraph + '\n\n';
    }
    
    return content.substring(0, length).trim();
}

// Export functions for use in tests and other modules
if (typeof window !== 'undefined') {
    window.TestDataGenerator = {
        generateMockAnalysisData,
        createRealisticError,
        generateEdgeCaseData,
        generatePerformanceTestData,
        generateRealisticContent,
        generateMockStatistics
    };
}

// Node.js compatibility
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generateMockAnalysisData,
        createRealisticError,
        generateEdgeCaseData,
        generatePerformanceTestData,
        generateRealisticContent,
        generateMockStatistics
    };
}

console.log('✅ Test Data Generator loaded and ready to use');
