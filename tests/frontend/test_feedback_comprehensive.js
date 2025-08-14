/**
 * Comprehensive Feedback System Tests
 * Tests all aspects of the feedback mechanism to ensure production-grade reliability
 */

// Mock dependencies for testing
const mockError = {
    type: 'grammar_error',
    message: 'Subject-verb disagreement detected',
    line_number: 5,
    sentence_index: 2,
    text_segment: 'The cats is sleeping',
    confidence_score: 0.85
};

const mockErrorLowConfidence = {
    type: 'style_suggestion',
    message: 'Consider using active voice',
    line_number: 10,
    sentence_index: 5,
    text_segment: 'The report was written by John',
    confidence_score: 0.45
};

// Test suite
describe('Feedback System Comprehensive Tests', () => {
    
    beforeEach(() => {
        // Clear session storage
        sessionStorage.clear();
        
        // Reset DOM
        document.body.innerHTML = `
            <div id="test-container">
                <div class="feedback-section" data-error-id="test-error-id"></div>
            </div>
        `;
        
        // Reset global state
        if (window.FeedbackSystem) {
            window.FeedbackSystem.FeedbackTracker.feedback = {};
        }
    });
    
    describe('Error ID Generation', () => {
        test('should generate consistent IDs for same error', () => {
            const id1 = window.FeedbackSystem.FeedbackTracker.generateErrorId(mockError);
            const id2 = window.FeedbackSystem.FeedbackTracker.generateErrorId(mockError);
            
            expect(id1).toBe(id2);
            expect(id1).toBeTruthy();
            expect(id1.length).toBeGreaterThan(0);
        });
        
        test('should generate different IDs for different errors', () => {
            const id1 = window.FeedbackSystem.FeedbackTracker.generateErrorId(mockError);
            const id2 = window.FeedbackSystem.FeedbackTracker.generateErrorId(mockErrorLowConfidence);
            
            expect(id1).not.toBe(id2);
        });
        
        test('should handle errors with missing properties', () => {
            const incompleteError = { type: 'test' };
            const id = window.FeedbackSystem.FeedbackTracker.generateErrorId(incompleteError);
            
            expect(id).toBeTruthy();
            expect(typeof id).toBe('string');
        });
    });
    
    describe('Feedback Recording', () => {
        test('should record positive feedback correctly', () => {
            const errorId = window.FeedbackSystem.FeedbackTracker.recordFeedback(
                mockError, 
                'helpful', 
                null
            );
            
            const feedback = window.FeedbackSystem.FeedbackTracker.getFeedback(mockError);
            
            expect(feedback).toBeTruthy();
            expect(feedback.type).toBe('helpful');
            expect(feedback.error_type).toBe(mockError.type);
            expect(feedback.original_error).toBeTruthy();
            expect(feedback.original_error.type).toBe(mockError.type);
        });
        
        test('should record negative feedback with reason', () => {
            const reason = {
                category: 'incorrect',
                comment: 'This is not actually an error'
            };
            
            const errorId = window.FeedbackSystem.FeedbackTracker.recordFeedback(
                mockError, 
                'not_helpful', 
                reason
            );
            
            const feedback = window.FeedbackSystem.FeedbackTracker.getFeedback(mockError);
            
            expect(feedback).toBeTruthy();
            expect(feedback.type).toBe('not_helpful');
            expect(feedback.reason).toEqual(reason);
        });
        
        test('should persist feedback to session storage', () => {
            window.FeedbackSystem.FeedbackTracker.recordFeedback(mockError, 'helpful', null);
            
            const stored = sessionStorage.getItem('error_feedback');
            expect(stored).toBeTruthy();
            
            const parsed = JSON.parse(stored);
            expect(Object.keys(parsed)).toHaveLength(1);
        });
    });
    
    describe('Feedback UI Generation', () => {
        test('should create feedback buttons for new error', () => {
            const html = window.FeedbackSystem.createFeedbackButtons(mockError);
            
            expect(html).toContain('Was this helpful?');
            expect(html).toContain('fa-thumbs-up');
            expect(html).toContain('fa-thumbs-down');
            expect(html).toContain('feedback-btn');
        });
        
        test('should create confirmation for existing feedback', () => {
            // Record feedback first
            window.FeedbackSystem.FeedbackTracker.recordFeedback(mockError, 'helpful', null);
            
            const html = window.FeedbackSystem.createFeedbackButtons(mockError);
            
            expect(html).toContain('Marked as helpful');
            expect(html).toContain('feedback-change-btn');
            expect(html).toContain('Change');
        });
    });
    
    describe('Change Feedback Functionality', () => {
        test('should allow changing feedback in same session', () => {
            // Setup: record initial feedback
            const errorId = window.FeedbackSystem.FeedbackTracker.recordFeedback(
                mockError, 
                'helpful', 
                null
            );
            
            // Create DOM element with feedback confirmation
            const container = document.querySelector(`[data-error-id="test-error-id"]`);
            container.innerHTML = window.FeedbackSystem.createFeedbackButtons(mockError);
            container.setAttribute('data-error-id', errorId);
            
            // Test: change feedback
            window.FeedbackSystem.changeFeedback(errorId);
            
            // Verify: feedback was removed and UI updated
            const feedback = window.FeedbackSystem.FeedbackTracker.getFeedback(mockError);
            expect(feedback).toBeNull();
            
            // Verify: UI now shows feedback buttons
            expect(container.innerHTML).toContain('Was this helpful?');
        });
        
        test('should handle missing feedback section gracefully', () => {
            const errorId = 'non-existent-id';
            
            // Should not throw error
            expect(() => {
                window.FeedbackSystem.changeFeedback(errorId);
            }).not.toThrow();
        });
        
        test('should handle missing feedback data gracefully', () => {
            const errorId = 'non-existent-feedback';
            
            // Create DOM element but no feedback data
            const container = document.querySelector(`[data-error-id="test-error-id"]`);
            container.setAttribute('data-error-id', errorId);
            
            // Should not throw error
            expect(() => {
                window.FeedbackSystem.changeFeedback(errorId);
            }).not.toThrow();
        });
    });
    
    describe('Feedback Submission Process', () => {
        test('should prevent multiple submissions', (done) => {
            const container = document.querySelector(`[data-error-id="test-error-id"]`);
            const errorId = window.FeedbackSystem.FeedbackTracker.generateErrorId(mockError);
            container.setAttribute('data-error-id', errorId);
            container.innerHTML = window.FeedbackSystem.createFeedbackButtons(mockError);
            
            const encodedError = btoa(JSON.stringify(mockError));
            
            // Simulate rapid clicking
            window.FeedbackSystem.submitFeedback(errorId, 'helpful', encodedError);
            window.FeedbackSystem.submitFeedback(errorId, 'helpful', encodedError);
            
            // Check that processing flag is set
            expect(container.dataset.processing).toBe('true');
            
            // Allow async operations to complete
            setTimeout(() => {
                // Should only have one feedback entry
                const feedback = window.FeedbackSystem.FeedbackTracker.getFeedback(mockError);
                expect(feedback).toBeTruthy();
                expect(feedback.type).toBe('helpful');
                done();
            }, 100);
        });
        
        test('should handle decode errors gracefully', () => {
            const container = document.querySelector(`[data-error-id="test-error-id"]`);
            const errorId = 'test-error-id';
            container.innerHTML = window.FeedbackSystem.createFeedbackButtons(mockError);
            
            const invalidEncodedError = 'invalid-base64';
            
            // Should not throw error
            expect(() => {
                window.FeedbackSystem.submitFeedback(errorId, 'helpful', invalidEncodedError);
            }).not.toThrow();
            
            // Should re-enable buttons on error
            setTimeout(() => {
                const buttons = container.querySelectorAll('.feedback-btn');
                buttons.forEach(btn => {
                    expect(btn.disabled).toBe(false);
                });
            }, 100);
        });
    });
    
    describe('Session Management', () => {
        test('should generate session ID if not available', () => {
            delete window.currentSessionId;
            
            const sessionId = window.FeedbackSystem.generateSessionId();
            
            expect(sessionId).toBeTruthy();
            expect(sessionId).toContain('sess_');
            expect(window.currentSessionId).toBe(sessionId);
        });
        
        test('should reuse existing session ID', () => {
            window.currentSessionId = 'existing-session-123';
            
            const sessionId = window.FeedbackSystem.generateSessionId();
            
            expect(sessionId).toBe('existing-session-123');
        });
    });
    
    describe('Backend Integration', () => {
        test('should submit feedback to backend', (done) => {
            // Mock fetch
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ success: true })
            });
            
            const errorId = 'test-error-id';
            
            window.FeedbackSystem.submitFeedbackToBackend(
                errorId, 
                'helpful', 
                mockError, 
                null
            );
            
            setTimeout(() => {
                expect(fetch).toHaveBeenCalledWith('/api/feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: expect.stringContaining('correct')
                });
                done();
            }, 100);
        });
        
        test('should handle backend errors gracefully', (done) => {
            // Mock fetch to fail
            global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));
            
            const errorId = 'test-error-id';
            
            // Should not throw error
            expect(() => {
                window.FeedbackSystem.submitFeedbackToBackend(
                    errorId, 
                    'helpful', 
                    mockError, 
                    null
                );
            }).not.toThrow();
            
            done();
        });
    });
    
    describe('Error Handling and Resilience', () => {
        test('should handle malformed error objects', () => {
            const malformedError = null;
            
            expect(() => {
                window.FeedbackSystem.FeedbackTracker.generateErrorId(malformedError);
            }).not.toThrow();
        });
        
        test('should handle missing DOM elements', () => {
            document.body.innerHTML = '';
            
            expect(() => {
                window.FeedbackSystem.changeFeedback('non-existent');
            }).not.toThrow();
        });
        
        test('should handle corrupted session storage', () => {
            sessionStorage.setItem('error_feedback', 'invalid-json');
            
            expect(() => {
                window.FeedbackSystem.FeedbackTracker.loadFromSession();
            }).not.toThrow();
            
            // Should fallback to empty feedback object
            expect(window.FeedbackSystem.FeedbackTracker.feedback).toEqual({});
        });
    });
    
    describe('Performance', () => {
        test('should handle large numbers of feedback entries', () => {
            const startTime = performance.now();
            
            // Create 1000 feedback entries
            for (let i = 0; i < 1000; i++) {
                const error = { ...mockError, line_number: i };
                window.FeedbackSystem.FeedbackTracker.recordFeedback(error, 'helpful', null);
            }
            
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            // Should complete in reasonable time (< 1 second)
            expect(duration).toBeLessThan(1000);
            
            // Should have all entries
            expect(Object.keys(window.FeedbackSystem.FeedbackTracker.feedback)).toHaveLength(1000);
        });
    });
});

// Integration tests
describe('Feedback System Integration Tests', () => {
    test('should work end-to-end with error card', () => {
        // Create error card with feedback
        const errorCard = document.createElement('div');
        errorCard.innerHTML = window.ErrorCards ? 
            window.ErrorCards.createErrorCard(mockError, 0) :
            `<div class="feedback-section" data-error-id="${window.FeedbackSystem.FeedbackTracker.generateErrorId(mockError)}">
                ${window.FeedbackSystem.createFeedbackButtons(mockError)}
            </div>`;
        
        document.body.appendChild(errorCard);
        
        // Find and click thumbs up button
        const thumbsUpBtn = errorCard.querySelector('.feedback-helpful');
        expect(thumbsUpBtn).toBeTruthy();
        
        // Simulate click
        thumbsUpBtn.click();
        
        // Verify feedback was recorded
        const feedback = window.FeedbackSystem.FeedbackTracker.getFeedback(mockError);
        expect(feedback.type).toBe('helpful');
    });
});

// Run tests if in test environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        mockError,
        mockErrorLowConfidence
    };
}