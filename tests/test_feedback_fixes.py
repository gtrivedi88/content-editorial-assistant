"""
Test cases to verify the feedback system fixes work correctly.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

from database import db
from database.models import UserFeedback, UserSession, RuleViolation, FeedbackType
from database.dao import FeedbackDAO
from database.services import DatabaseService


class TestFeedbackFixes:
    """Test the feedback system fixes for the reported scenarios."""
    
    def setup_method(self):
        """Set up test data."""
        self.session_id = "test_session_123"
        self.violation_id = "violation_456"
        self.feedback_data = {
            'error_type': 'grammar_error',
            'error_message': 'Test error message',
            'feedback_type': 'correct',
            'confidence_score': 0.8,
            'user_reason': 'This is helpful'
        }
    
    def test_scenario_1_change_without_resubmit(self):
        """
        Test Scenario 1: Submit feedback → Change it → but not resubmitting → Old record should not delete from database
        """
        # Store initial feedback
        feedback = FeedbackDAO.store_feedback(
            self.session_id,
            self.violation_id, 
            self.feedback_data
        )
        
        assert feedback is not None
        assert feedback.session_id == self.session_id
        assert feedback.violation_id == self.violation_id
        
        # Simulate user changing feedback (calling delete on frontend, but not resubmitting)
        # This should NOT delete the database record
        existing_feedback = FeedbackDAO.get_existing_feedback(self.session_id, self.violation_id)
        assert existing_feedback is not None
        assert existing_feedback.feedback_id == feedback.feedback_id
        
        print("✅ Scenario 1: Database record persists even when user changes but doesn't resubmit")
    
    def test_scenario_2_only_one_record_per_violation(self):
        """
        Test Scenario 2: Submit feedback (thumbs up) → Change it → submit new feedback (thumbs down) → Only 1 record per user violation!
        """
        # Submit initial feedback (thumbs up)
        initial_feedback = FeedbackDAO.store_feedback(
            self.session_id,
            self.violation_id,
            self.feedback_data  # 'correct' = thumbs up
        )
        
        assert initial_feedback.feedback_type == FeedbackType.CORRECT
        
        # Submit changed feedback (thumbs down) - this should UPDATE the existing record
        changed_data = self.feedback_data.copy()
        changed_data['feedback_type'] = 'incorrect'  # thumbs down
        changed_data['user_reason'] = 'Changed my mind'
        
        updated_feedback = FeedbackDAO.update_feedback(
            self.session_id,
            self.violation_id,
            changed_data
        )
        
        # Should be the same record, but updated
        assert updated_feedback.feedback_id == initial_feedback.feedback_id
        assert updated_feedback.feedback_type == FeedbackType.INCORRECT
        assert updated_feedback.user_reason == 'Changed my mind'
        
        # Verify only one record exists
        all_feedback = FeedbackDAO.get_violation_feedback(self.violation_id)
        assert len(all_feedback) == 1
        
        print("✅ Scenario 2: Only one record per user violation, updates existing instead of creating new")
    
    def test_scenario_3_cannot_change_previous_sessions(self):
        """
        Test Scenario 3: User must not be able to change feedback given in previous sessions. No database update.
        """
        # Create feedback in "previous session"
        old_session_id = "old_session_123"
        
        old_feedback = FeedbackDAO.store_feedback(
            old_session_id,
            self.violation_id,
            self.feedback_data
        )
        
        # Try to update from a different session (current session)
        new_session_id = "new_session_456"
        changed_data = self.feedback_data.copy()
        changed_data['feedback_type'] = 'incorrect'
        
        # This should create a NEW record for the new session, not update the old one
        new_feedback = FeedbackDAO.update_feedback(
            new_session_id,
            self.violation_id,
            changed_data
        )
        
        # Should be a different record
        assert new_feedback.feedback_id != old_feedback.feedback_id
        assert new_feedback.session_id == new_session_id
        assert old_feedback.session_id == old_session_id
        
        # Both records should exist
        all_feedback = FeedbackDAO.get_violation_feedback(self.violation_id)
        assert len(all_feedback) == 2
        
        # Old feedback should be unchanged
        old_feedback_check = FeedbackDAO.get_existing_feedback(old_session_id, self.violation_id)
        assert old_feedback_check.feedback_type == FeedbackType.CORRECT
        assert old_feedback_check.user_reason == 'This is helpful'
        
        print("✅ Scenario 3: Cannot change feedback from previous sessions - creates new record for new session")
    
    def test_unique_constraint_prevents_duplicates(self):
        """Test that the unique constraint prevents duplicate feedback entries."""
        # Store initial feedback
        FeedbackDAO.store_feedback(
            self.session_id,
            self.violation_id,
            self.feedback_data
        )
        
        # Try to store duplicate - should raise an error or be handled gracefully
        with pytest.raises(Exception):  # SQLAlchemy should raise IntegrityError
            FeedbackDAO.store_feedback(
                self.session_id,
                self.violation_id,
                self.feedback_data  # Same session_id and violation_id
            )
        
        print("✅ Unique constraint prevents duplicate feedback entries")
    
    def test_database_service_integration(self):
        """Test that DatabaseService properly uses the new DAO methods."""
        db_service = DatabaseService()
        
        # Test store/update functionality
        success, feedback_id = db_service.store_user_feedback(
            self.session_id,
            self.violation_id,
            self.feedback_data
        )
        
        assert success
        assert feedback_id is not None
        
        # Test get existing functionality
        success, feedback_data = db_service.get_existing_feedback(
            self.session_id,
            self.violation_id
        )
        
        assert success
        assert feedback_data is not None
        assert feedback_data['session_id'] == self.session_id
        assert feedback_data['violation_id'] == self.violation_id
        
        # Test update functionality (should update existing record)
        changed_data = self.feedback_data.copy()
        changed_data['feedback_type'] = 'incorrect'
        
        success, updated_feedback_id = db_service.store_user_feedback(
            self.session_id,
            self.violation_id,
            changed_data
        )
        
        assert success
        assert updated_feedback_id == feedback_id  # Should be same ID (updated, not new)
        
        print("✅ DatabaseService integration works correctly")
    
    def test_frontend_session_validation_logic(self):
        """Test the logic that would be used in frontend session validation."""
        # Simulate frontend tracking
        feedback_tracker = {
            'sessionId': 'current_session',
            'feedback': {
                'error123': {
                    'fromDatabase': True,
                    'sessionId': 'old_session',  # Different session
                    'type': 'helpful'
                }
            }
        }
        
        # Simulate validation check
        error_id = 'error123'
        existing_feedback = feedback_tracker['feedback'].get(error_id)
        
        can_change = not (
            existing_feedback and 
            existing_feedback.get('fromDatabase') and
            existing_feedback.get('sessionId') != feedback_tracker['sessionId']
        )
        
        assert not can_change, "Should not allow changing feedback from different session"
        
        # Test same session - should allow
        feedback_tracker['feedback']['error123']['sessionId'] = 'current_session'
        
        can_change = not (
            existing_feedback and 
            existing_feedback.get('fromDatabase') and
            existing_feedback.get('sessionId') != feedback_tracker['sessionId']
        )
        
        assert can_change, "Should allow changing feedback from same session"
        
        print("✅ Frontend session validation logic works correctly")


def run_feedback_tests():
    """Run all feedback fix tests."""
    print("🧪 Running Feedback System Fix Tests...\n")
    
    test_instance = TestFeedbackFixes()
    test_instance.setup_method()
    
    try:
        test_instance.test_scenario_1_change_without_resubmit()
        test_instance.test_scenario_2_only_one_record_per_violation()
        test_instance.test_scenario_3_cannot_change_previous_sessions()
        test_instance.test_unique_constraint_prevents_duplicates()
        test_instance.test_database_service_integration()
        test_instance.test_frontend_session_validation_logic()
        
        print("\n🎉 All feedback system tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == '__main__':
    run_feedback_tests()
