"""
Test Suite for Phase 1, Step 1: Directory Structure Setup
Tests all aspects of the validation module directory structure.
"""

import os
import unittest
import importlib
import sys
from pathlib import Path


class TestDirectoryStructure(unittest.TestCase):
    """Test the validation module directory structure and setup."""
    
    def setUp(self):
        """Set up test environment."""
        self.base_path = Path(__file__).parent.parent  # validation/ directory
        self.expected_structure = {
            'validation': {
                '__init__.py': 'file',
                'tests': {
                    '__init__.py': 'file',
                    'test_confidence': {
                        '__init__.py': 'file'
                    },
                    'test_multi_pass': {
                        '__init__.py': 'file'
                    },
                    'test_config': {
                        '__init__.py': 'file'
                    },
                    'test_feedback': {
                        '__init__.py': 'file'
                    }
                },
                'confidence': {
                    '__init__.py': 'file'
                },
                'multi_pass': {
                    '__init__.py': 'file'
                },
                'config': 'directory',
                'feedback': {
                    '__init__.py': 'file'
                }
            }
        }
    
    def test_all_directories_exist(self):
        """Test that all required directories are created correctly."""
        # Test main validation directory
        self.assertTrue(self.base_path.exists(), 
                       f"Main validation directory should exist: {self.base_path}")
        self.assertTrue(self.base_path.is_dir(), 
                       "validation should be a directory")
        
        # Test subdirectories
        required_dirs = [
            'tests',
            'tests/test_confidence', 
            'tests/test_multi_pass',
            'tests/test_config',
            'tests/test_feedback',
            'confidence',
            'multi_pass', 
            'config',
            'feedback'
        ]
        
        for dir_path in required_dirs:
            full_path = self.base_path / dir_path
            self.assertTrue(full_path.exists(), 
                           f"Directory should exist: {full_path}")
            self.assertTrue(full_path.is_dir(), 
                           f"Path should be a directory: {full_path}")
    
    def test_all_init_files_exist(self):
        """Test that all required __init__.py files exist."""
        required_init_files = [
            '__init__.py',
            'tests/__init__.py',
            'tests/test_confidence/__init__.py',
            'tests/test_multi_pass/__init__.py', 
            'tests/test_config/__init__.py',
            'tests/test_feedback/__init__.py',
            'confidence/__init__.py',
            'multi_pass/__init__.py',
            'feedback/__init__.py'
        ]
        
        for init_file in required_init_files:
            full_path = self.base_path / init_file
            self.assertTrue(full_path.exists(), 
                           f"__init__.py file should exist: {full_path}")
            self.assertTrue(full_path.is_file(), 
                           f"__init__.py should be a file: {full_path}")
    
    def test_python_can_import_modules(self):
        """Test that Python can import from all __init__.py files."""
        # Add the parent directory to sys.path to enable imports
        parent_dir = str(self.base_path.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Test main validation module import
        try:
            import validation
            self.assertIsNotNone(validation, "Should be able to import validation module")
            # Test module has expected attributes
            self.assertTrue(hasattr(validation, '__version__'), 
                           "validation module should have __version__")
            self.assertTrue(hasattr(validation, '__author__'), 
                           "validation module should have __author__")
        except ImportError as e:
            self.fail(f"Failed to import validation module: {e}")
        
        # Test submodule imports
        submodules_to_test = [
            'validation.tests',
            'validation.confidence', 
            'validation.multi_pass',
            'validation.feedback',
            'validation.tests.test_confidence',
            'validation.tests.test_multi_pass',
            'validation.tests.test_config', 
            'validation.tests.test_feedback'
        ]
        
        for module_name in submodules_to_test:
            try:
                module = importlib.import_module(module_name)
                self.assertIsNotNone(module, 
                                   f"Should be able to import {module_name}")
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")
    
    def test_directory_structure_matches_expected(self):
        """Test that the directory structure exactly matches expected layout."""
        def check_structure(current_path, expected_dict, relative_path=""):
            """Recursively check directory structure."""
            for name, expected_type in expected_dict.items():
                item_path = current_path / name
                full_relative_path = f"{relative_path}/{name}" if relative_path else name
                
                # Check item exists
                self.assertTrue(item_path.exists(), 
                               f"Item should exist: {full_relative_path}")
                
                if isinstance(expected_type, dict):
                    # It's a directory with contents
                    self.assertTrue(item_path.is_dir(), 
                                   f"Should be directory: {full_relative_path}")
                    # Recursively check contents
                    check_structure(item_path, expected_type, full_relative_path)
                elif expected_type == 'directory':
                    # It's just a directory
                    self.assertTrue(item_path.is_dir(), 
                                   f"Should be directory: {full_relative_path}")
                elif expected_type == 'file':
                    # It's a file
                    self.assertTrue(item_path.is_file(), 
                                   f"Should be file: {full_relative_path}")
        
        # Start checking from validation directory
        check_structure(self.base_path, self.expected_structure['validation'])
    
    def test_file_permissions_and_accessibility(self):
        """Test file permissions and accessibility."""
        # Test that __init__.py files are readable
        init_files = [
            '__init__.py',
            'tests/__init__.py',
            'tests/test_confidence/__init__.py',
            'tests/test_multi_pass/__init__.py',
            'tests/test_config/__init__.py', 
            'tests/test_feedback/__init__.py',
            'confidence/__init__.py',
            'multi_pass/__init__.py',
            'feedback/__init__.py'
        ]
        
        for init_file in init_files:
            file_path = self.base_path / init_file
            # Test file is readable
            self.assertTrue(os.access(file_path, os.R_OK), 
                           f"File should be readable: {init_file}")
            
            # Test file has content (not empty)
            self.assertGreater(file_path.stat().st_size, 0, 
                              f"__init__.py should not be empty: {init_file}")
        
        # Test that directories are accessible
        directories = [
            'tests',
            'tests/test_confidence',
            'tests/test_multi_pass', 
            'tests/test_config',
            'tests/test_feedback',
            'confidence',
            'multi_pass',
            'config',
            'feedback'
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            # Test directory is accessible
            self.assertTrue(os.access(dir_path, os.R_OK), 
                           f"Directory should be readable: {directory}")
            self.assertTrue(os.access(dir_path, os.X_OK), 
                           f"Directory should be executable: {directory}")
    
    def test_init_file_contents(self):
        """Test that __init__.py files have appropriate content."""
        # Test main validation __init__.py
        main_init = self.base_path / '__init__.py'
        with open(main_init, 'r') as f:
            content = f.read()
            self.assertIn('__version__', content, 
                         "Main __init__.py should contain __version__")
            self.assertIn('__author__', content, 
                         "Main __init__.py should contain __author__")
            self.assertIn('Validation Module', content, 
                         "Main __init__.py should contain module description")
        
        # Test that test __init__.py files contain appropriate content
        test_init_files = [
            ('tests/__init__.py', 'Test suite'),
            ('tests/test_confidence/__init__.py', 'confidence calculation'),
            ('tests/test_multi_pass/__init__.py', 'multi-pass validation'),
            ('tests/test_config/__init__.py', 'configuration'),
            ('tests/test_feedback/__init__.py', 'feedback collection')
        ]
        
        for init_file, expected_content in test_init_files:
            file_path = self.base_path / init_file
            with open(file_path, 'r') as f:
                content = f.read()
                self.assertIn(expected_content, content, 
                             f"{init_file} should contain '{expected_content}'")
    
    def test_module_imports_work_from_project_root(self):
        """Test that modules can be imported from project root context."""
        # This simulates how the modules will be imported in the actual application
        original_path = sys.path.copy()
        
        try:
            # Add project root to path (parent of validation directory)
            project_root = str(self.base_path.parent)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Test imports that will be used in the application
            from validation import __version__, __author__
            self.assertIsInstance(__version__, str)
            self.assertIsInstance(__author__, str)
            
            # Test that submodule structure is accessible
            import validation.confidence
            import validation.multi_pass  
            import validation.feedback
            
            # These should not raise import errors
            self.assertTrue(True, "All imports successful")
            
        except ImportError as e:
            self.fail(f"Import failed from project root context: {e}")
        finally:
            # Restore original sys.path
            sys.path = original_path


class TestDirectoryStructureIntegration(unittest.TestCase):
    """Integration tests for directory structure with existing codebase."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.validation_path = Path(__file__).parent.parent
        self.project_root = self.validation_path.parent
    
    def test_validation_directory_in_project_root(self):
        """Test that validation directory is properly placed in project root."""
        # Check that validation is in the same directory as other main modules
        expected_siblings = ['style_analyzer', 'rules', 'app_modules', 'ui']
        
        for sibling in expected_siblings:
            sibling_path = self.project_root / sibling
            if sibling_path.exists():  # Only test existing siblings
                self.assertTrue(sibling_path.is_dir(), 
                               f"Expected sibling {sibling} should be a directory")
        
        # Validation should be at the same level
        self.assertTrue(self.validation_path.exists(), 
                       "validation directory should exist at project root level")
    
    def test_validation_not_conflicting_with_existing_modules(self):
        """Test that validation module doesn't conflict with existing imports."""
        # Test that we can still import existing modules
        original_path = sys.path.copy()
        
        try:
            project_root = str(self.project_root)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Test that existing imports still work
            existing_modules_to_test = []
            
            # Check if these modules exist before testing import
            potential_modules = ['style_analyzer', 'rules', 'app_modules']
            for module_name in potential_modules:
                module_path = self.project_root / module_name / '__init__.py'
                if module_path.exists():
                    existing_modules_to_test.append(module_name)
            
            for module_name in existing_modules_to_test:
                try:
                    module = importlib.import_module(module_name)
                    self.assertIsNotNone(module, 
                                       f"Existing module {module_name} should still be importable")
                except ImportError as e:
                    self.fail(f"Existing module {module_name} import failed: {e}")
            
        finally:
            sys.path = original_path


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)