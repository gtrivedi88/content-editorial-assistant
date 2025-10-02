"""
Feature-Test Mapping System
Automatically tracks which tests cover which features to ensure complete coverage.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Any
import json
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Feature:
    """Represents a feature in the codebase."""
    name: str
    file_path: str
    description: str
    tests: List[str]
    last_modified: str
    coverage_percentage: float


@dataclass
class TestMapping:
    """Represents the mapping between features and tests."""
    feature_name: str
    test_files: List[str]
    test_count: int
    last_updated: str


class FeatureTestMapper:
    """
    Automatically maps features to their tests.
    Helps ensure that all features have corresponding tests.
    """
    
    def __init__(self, project_root: Path = Path(".")):
        """Initialize the feature-test mapper."""
        self.project_root = project_root
        self.mappings: Dict[str, TestMapping] = {}
        self.features: Dict[str, Feature] = {}
    
    def scan_features(self) -> Dict[str, Feature]:
        """
        Scan the codebase to identify features.
        Features are identified by:
        - Module docstrings
        - Class definitions
        - Major functions
        """
        features = {}
        
        # Define feature directories
        feature_dirs = [
            'app_modules',
            'rewriter',
            'style_analyzer',
            'rules',
            'ambiguity',
            'metadata_assistant',
            'structural_parsing',
            'validation',
            'error_consolidation'
        ]
        
        for feature_dir in feature_dirs:
            dir_path = self.project_root / feature_dir
            if not dir_path.exists():
                continue
            
            for py_file in dir_path.rglob('*.py'):
                if '__pycache__' in str(py_file):
                    continue
                
                feature_info = self._extract_feature_info(py_file)
                if feature_info:
                    features[feature_info['name']] = Feature(
                        name=feature_info['name'],
                        file_path=str(py_file.relative_to(self.project_root)),
                        description=feature_info['description'],
                        tests=[],
                        last_modified=datetime.fromtimestamp(py_file.stat().st_mtime).isoformat(),
                        coverage_percentage=0.0
                    )
        
        self.features = features
        return features
    
    def _extract_feature_info(self, file_path: Path) -> Dict[str, str]:
        """Extract feature information from a Python file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Get module docstring
            docstring = ast.get_docstring(tree)
            
            if docstring:
                # Use first line of docstring as feature name
                feature_name = docstring.split('\n')[0].strip()
                
                return {
                    'name': feature_name,
                    'description': docstring[:200]  # First 200 chars
                }
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        
        return None
    
    def scan_tests(self) -> Dict[str, List[str]]:
        """
        Scan test files to identify what they test.
        Uses test names, imports, and patterns to infer coverage.
        """
        test_mappings = {}
        
        tests_dir = self.project_root / 'tests'
        if not tests_dir.exists():
            return test_mappings
        
        for test_file in tests_dir.rglob('test_*.py'):
            if '__pycache__' in str(test_file):
                continue
            
            tested_features = self._identify_tested_features(test_file)
            
            for feature in tested_features:
                if feature not in test_mappings:
                    test_mappings[feature] = []
                test_mappings[feature].append(str(test_file.relative_to(self.project_root)))
        
        return test_mappings
    
    def _identify_tested_features(self, test_file: Path) -> Set[str]:
        """Identify which features a test file tests."""
        tested_features = set()
        
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check imports to see what modules are tested
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Extract top-level module name
                        module_parts = node.module.split('.')
                        if module_parts:
                            tested_features.add(module_parts[0])
        
        except Exception as e:
            print(f"Error parsing test file {test_file}: {e}")
        
        return tested_features
    
    def generate_mapping(self) -> Dict[str, TestMapping]:
        """Generate complete feature-test mapping."""
        features = self.scan_features()
        test_mappings = self.scan_tests()
        
        mappings = {}
        
        for feature_name, feature in features.items():
            # Find tests for this feature
            test_files = []
            
            # Look for exact matches
            if feature_name in test_mappings:
                test_files.extend(test_mappings[feature_name])
            
            # Look for tests in feature directory
            feature_dir = Path(feature.file_path).parent
            test_pattern = f"test_{feature_dir.name}*.py"
            test_files.extend([
                str(f.relative_to(self.project_root))
                for f in (self.project_root / 'tests').rglob(test_pattern)
            ])
            
            # Remove duplicates
            test_files = list(set(test_files))
            
            mappings[feature_name] = TestMapping(
                feature_name=feature_name,
                test_files=test_files,
                test_count=len(test_files),
                last_updated=datetime.now().isoformat()
            )
        
        self.mappings = mappings
        return mappings
    
    def identify_untested_features(self) -> List[Feature]:
        """Identify features that have no tests."""
        untested = []
        
        for feature_name, mapping in self.mappings.items():
            if mapping.test_count == 0:
                if feature_name in self.features:
                    untested.append(self.features[feature_name])
        
        return untested
    
    def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate a report on feature test coverage."""
        if not self.mappings:
            self.generate_mapping()
        
        total_features = len(self.features)
        tested_features = sum(1 for m in self.mappings.values() if m.test_count > 0)
        untested_features = self.identify_untested_features()
        
        coverage_percentage = (tested_features / total_features * 100) if total_features > 0 else 0
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_features': total_features,
                'tested_features': tested_features,
                'untested_features': len(untested_features),
                'coverage_percentage': round(coverage_percentage, 2)
            },
            'untested': [
                {
                    'name': f.name,
                    'file_path': f.file_path,
                    'description': f.description
                }
                for f in untested_features
            ],
            'detailed_mappings': {
                name: asdict(mapping)
                for name, mapping in self.mappings.items()
            }
        }
        
        return report
    
    def save_mapping(self, output_path: Path = Path("testing_agent/data/feature_test_mapping.json")):
        """Save feature-test mapping to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_coverage_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Feature-test mapping saved to {output_path}")
        print(f"Coverage: {report['summary']['coverage_percentage']}%")
        print(f"Untested features: {report['summary']['untested_features']}")
    
    def suggest_missing_tests(self) -> List[Dict[str, str]]:
        """Suggest tests that should be created for untested features."""
        suggestions = []
        
        untested = self.identify_untested_features()
        
        for feature in untested:
            # Determine test file name
            file_path = Path(feature.file_path)
            test_name = f"test_{file_path.stem}.py"
            test_location = f"tests/{file_path.parent}/{test_name}"
            
            suggestions.append({
                'feature': feature.name,
                'feature_file': feature.file_path,
                'suggested_test_file': test_location,
                'priority': 'high' if 'core' in feature.file_path or 'api' in feature.file_path else 'medium'
            })
        
        return suggestions


def main():
    """CLI entry point for feature-test mapper."""
    mapper = FeatureTestMapper()
    
    print("Scanning features and tests...")
    mapper.generate_mapping()
    
    print("\nGenerating coverage report...")
    mapper.save_mapping()
    
    print("\nSuggesting missing tests...")
    suggestions = mapper.suggest_missing_tests()
    
    if suggestions:
        print(f"\n{len(suggestions)} features need tests:")
        for suggestion in suggestions[:10]:  # Show first 10
            print(f"  [{suggestion['priority']}] {suggestion['feature']}")
            print(f"      Create: {suggestion['suggested_test_file']}")
    else:
        print("\n✅ All features have tests!")


if __name__ == '__main__':
    main()

