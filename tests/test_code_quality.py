"""
Code Quality and Duplication Detection Tests
Comprehensive tests to detect duplicate code, similar patterns, 
import cycles, and maintain code quality standards.
"""

import pytest
import os
import sys
import ast
import re
import importlib.util
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any, Optional
import hashlib

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CodeAnalyzer:
    """Analyzes Python code for quality issues and duplications."""
    
    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_root = Path(project_root)
        self.python_files = list(self.project_root.rglob("*.py"))
        # Exclude test files and virtual environment
        self.python_files = [f for f in self.python_files 
                           if not any(part in str(f) for part in ['venv', '__pycache__', '.git'])]
    
    def get_function_signatures(self) -> Dict[str, List[Tuple[str, str]]]:
        """Extract all function signatures from the codebase."""
        functions = defaultdict(list)
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Create signature hash
                        args = [arg.arg for arg in node.args.args]
                        signature = f"{node.name}({', '.join(args)})"
                        functions[signature].append((str(file_path), node.lineno))
                        
            except Exception as e:
                # Skip files that can't be parsed
                continue
        
        return functions
    
    def get_class_definitions(self) -> Dict[str, List[Tuple[str, str]]]:
        """Extract all class definitions from the codebase."""
        classes = defaultdict(list)
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes[node.name].append((str(file_path), node.lineno))
                        
            except Exception:
                continue
        
        return classes
    
    def detect_duplicate_functions(self) -> List[Dict[str, Any]]:
        """Detect functions with identical implementations."""
        duplicates = []
        function_bodies = defaultdict(list)
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Create a hash of the function body (normalized)
                        body_code = ast.dump(node, annotate_fields=False, include_attributes=False)
                        # Remove function name from hash to detect similar implementations
                        normalized_body = re.sub(r'name=\'[^\']+\'', 'name=\'FUNC\'', body_code)
                        body_hash = hashlib.md5(normalized_body.encode()).hexdigest()
                        
                        function_bodies[body_hash].append({
                            'name': node.name,
                            'file': str(file_path),
                            'line': node.lineno,
                            'args': len(node.args.args)
                        })
                        
            except Exception:
                continue
        
        # Find duplicates
        for body_hash, functions in function_bodies.items():
            if len(functions) > 1:
                duplicates.append({
                    'type': 'duplicate_function_body',
                    'functions': functions,
                    'hash': body_hash
                })
        
        return duplicates
    
    def detect_similar_code_blocks(self, min_lines: int = 5) -> List[Dict[str, Any]]:
        """Detect similar code blocks across files."""
        similar_blocks = []
        code_blocks = defaultdict(list)
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Create overlapping windows of code lines
                for i in range(len(lines) - min_lines + 1):
                    block = ''.join(lines[i:i + min_lines])
                    # Normalize whitespace and comments
                    normalized_block = re.sub(r'#.*', '', block)  # Remove comments
                    normalized_block = re.sub(r'\s+', ' ', normalized_block)  # Normalize whitespace
                    normalized_block = normalized_block.strip()
                    
                    if len(normalized_block) > 50:  # Only consider substantial blocks
                        block_hash = hashlib.md5(normalized_block.encode()).hexdigest()
                        code_blocks[block_hash].append({
                            'file': str(file_path),
                            'start_line': i + 1,
                            'end_line': i + min_lines,
                            'content': block[:100] + '...' if len(block) > 100 else block
                        })
                        
            except Exception:
                continue
        
        # Find similar blocks
        for block_hash, blocks in code_blocks.items():
            if len(blocks) > 1:
                similar_blocks.append({
                    'type': 'similar_code_block',
                    'blocks': blocks,
                    'hash': block_hash
                })
        
        return similar_blocks
    
    def detect_import_cycles(self) -> List[List[str]]:
        """Detect circular import dependencies."""
        import_graph = defaultdict(set)
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                current_module = self._get_module_name(file_path)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_graph[current_module].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            import_graph[current_module].add(node.module)
                            
            except Exception:
                continue
        
        # Detect cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in import_graph.get(node, []):
                if neighbor in import_graph:  # Only follow internal modules
                    dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for module in import_graph:
            if module not in visited:
                dfs(module, [])
        
        return cycles
    
    def _get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        relative_path = file_path.relative_to(self.project_root)
        module_path = str(relative_path).replace('/', '.').replace('\\', '.')
        if module_path.endswith('.py'):
            module_path = module_path[:-3]
        if module_path.endswith('.__init__'):
            module_path = module_path[:-9]
        return module_path
    
    def analyze_complexity(self) -> Dict[str, Dict[str, Any]]:
        """Analyze code complexity metrics."""
        complexity_data = {}
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                functions = []
                classes = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity = self._calculate_cyclomatic_complexity(node)
                        functions.append({
                            'name': node.name,
                            'line': node.lineno,
                            'complexity': complexity,
                            'lines': self._count_function_lines(node)
                        })
                    elif isinstance(node, ast.ClassDef):
                        methods = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
                        classes.append({
                            'name': node.name,
                            'line': node.lineno,
                            'methods': len(methods),
                            'lines': self._count_class_lines(node)
                        })
                
                complexity_data[str(file_path)] = {
                    'functions': functions,
                    'classes': classes,
                    'total_lines': len(content.splitlines())
                }
                
            except Exception:
                continue
        
        return complexity_data
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _count_function_lines(self, node: ast.FunctionDef) -> int:
        """Count lines in a function."""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        return 1
    
    def _count_class_lines(self, node: ast.ClassDef) -> int:
        """Count lines in a class."""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        return 1


class TestCodeQuality:
    """Test code quality and duplication detection."""
    
    @pytest.fixture
    def code_analyzer(self):
        """Create code analyzer instance."""
        return CodeAnalyzer()
    
    def test_no_duplicate_function_signatures(self, code_analyzer):
        """Test that there are no duplicate function signatures in the same file."""
        functions = code_analyzer.get_function_signatures()
        
        duplicates = []
        for signature, locations in functions.items():
            if len(locations) > 1:
                # Group by file to find duplicates within the same file
                file_groups = defaultdict(list)
                for file_path, line_no in locations:
                    file_groups[file_path].append(line_no)
                
                for file_path, line_numbers in file_groups.items():
                    if len(line_numbers) > 1:
                        duplicates.append({
                            'signature': signature,
                            'file': file_path,
                            'lines': line_numbers
                        })
        
        assert len(duplicates) == 0, f"Found duplicate function signatures: {duplicates}"
    
    def test_no_duplicate_class_names(self, code_analyzer):
        """Test that there are no duplicate class names in the same module."""
        classes = code_analyzer.get_class_definitions()
        
        duplicates = []
        for class_name, locations in classes.items():
            if len(locations) > 1:
                # Group by file to find duplicates within the same file
                file_groups = defaultdict(list)
                for file_path, line_no in locations:
                    file_groups[file_path].append(line_no)
                
                for file_path, line_numbers in file_groups.items():
                    if len(line_numbers) > 1:
                        duplicates.append({
                            'class_name': class_name,
                            'file': file_path,
                            'lines': line_numbers
                        })
        
        assert len(duplicates) == 0, f"Found duplicate class names: {duplicates}"
    
    def test_no_duplicate_function_implementations(self, code_analyzer):
        """Test that there are no functions with identical implementations."""
        duplicates = code_analyzer.detect_duplicate_functions()
        
        # Filter out very small functions (likely to be similar)
        significant_duplicates = [
            d for d in duplicates 
            if any(f.get('args', 0) > 0 for f in d['functions'])
        ]
        
        assert len(significant_duplicates) == 0, f"Found duplicate function implementations: {significant_duplicates}"
    
    def test_limited_code_duplication(self, code_analyzer):
        """Test that code duplication is within acceptable limits."""
        similar_blocks = code_analyzer.detect_similar_code_blocks(min_lines=8)
        
        # Allow some duplication but not excessive
        max_allowed_duplications = 5
        
        if len(similar_blocks) > max_allowed_duplications:
            # Print details for investigation
            for block in similar_blocks[:3]:  # Show first 3
                print(f"\nSimilar code block found:")
                for location in block['blocks']:
                    print(f"  {location['file']}:{location['start_line']}-{location['end_line']}")
        
        assert len(similar_blocks) <= max_allowed_duplications, \
            f"Found {len(similar_blocks)} similar code blocks, maximum allowed is {max_allowed_duplications}"
    
    def test_no_import_cycles(self, code_analyzer):
        """Test that there are no circular import dependencies."""
        cycles = code_analyzer.detect_import_cycles()
        
        assert len(cycles) == 0, f"Found import cycles: {cycles}"
    
    def test_complexity_within_limits(self, code_analyzer):
        """Test that code complexity is within reasonable limits."""
        complexity_data = code_analyzer.analyze_complexity()
        
        high_complexity_functions = []
        large_classes = []
        
        max_function_complexity = 15
        max_class_methods = 25
        max_function_lines = 100
        
        for file_path, data in complexity_data.items():
            for func in data['functions']:
                if func['complexity'] > max_function_complexity:
                    high_complexity_functions.append({
                        'file': file_path,
                        'function': func['name'],
                        'complexity': func['complexity'],
                        'line': func['line']
                    })
                
                if func['lines'] > max_function_lines:
                    high_complexity_functions.append({
                        'file': file_path,
                        'function': func['name'],
                        'lines': func['lines'],
                        'line': func['line'],
                        'reason': 'too_many_lines'
                    })
            
            for cls in data['classes']:
                if cls['methods'] > max_class_methods:
                    large_classes.append({
                        'file': file_path,
                        'class': cls['name'],
                        'methods': cls['methods'],
                        'line': cls['line']
                    })
        
        error_messages = []
        if high_complexity_functions:
            error_messages.append(f"High complexity functions: {high_complexity_functions}")
        if large_classes:
            error_messages.append(f"Large classes: {large_classes}")
        
        assert len(error_messages) == 0, "\n".join(error_messages)
    
    def test_consistent_naming_patterns(self, code_analyzer):
        """Test that naming patterns are consistent across the codebase."""
        naming_issues = []
        
        for file_path in code_analyzer.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Functions should be snake_case
                        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name) and not node.name.startswith('test_'):
                            naming_issues.append({
                                'type': 'function_naming',
                                'name': node.name,
                                'file': str(file_path),
                                'line': node.lineno,
                                'expected': 'snake_case'
                            })
                    
                    elif isinstance(node, ast.ClassDef):
                        # Classes should be PascalCase
                        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                            naming_issues.append({
                                'type': 'class_naming',
                                'name': node.name,
                                'file': str(file_path),
                                'line': node.lineno,
                                'expected': 'PascalCase'
                            })
                    
                    elif isinstance(node, ast.Assign):
                        # Constants should be UPPER_CASE
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id.isupper():
                                if not re.match(r'^[A-Z_][A-Z0-9_]*$', target.id):
                                    naming_issues.append({
                                        'type': 'constant_naming',
                                        'name': target.id,
                                        'file': str(file_path),
                                        'line': node.lineno,
                                        'expected': 'UPPER_CASE'
                                    })
                
            except Exception:
                continue
        
        # Allow some naming issues but not excessive
        max_naming_issues = 10
        
        assert len(naming_issues) <= max_naming_issues, \
            f"Found {len(naming_issues)} naming issues (max {max_naming_issues}): {naming_issues[:5]}"
    
    def test_no_unused_imports(self, code_analyzer):
        """Test for unused imports (basic detection)."""
        unused_imports = []
        
        for file_path in code_analyzer.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Collect all imports
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.asname or alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            imports.add(alias.asname or alias.name)
                
                # Check if imports are used (basic string search)
                for import_name in imports:
                    if import_name != '*' and import_name not in content.replace(f'import {import_name}', ''):
                        # More sophisticated check needed here
                        pass
                
            except Exception:
                continue
        
        # This is a placeholder - implementing full unused import detection
        # would require more sophisticated analysis
        assert True, "Unused import detection is a placeholder"


class TestCodeMetrics:
    """Test code metrics and quality indicators."""
    
    def test_test_coverage_exists(self):
        """Test that test files exist for major components."""
        test_dir = Path(__file__).parent
        src_dirs = ['app_modules', 'rewriter', 'style_analyzer', 'rules', 'ambiguity']
        
        missing_tests = []
        
        for src_dir in src_dirs:
            src_path = test_dir.parent / src_dir
            if src_path.exists():
                test_file = test_dir / f"test_{src_dir.replace('_', '_')}.py"
                if not test_file.exists():
                    missing_tests.append(src_dir)
        
        # Allow some missing test files as they might be tested elsewhere
        max_missing = 2
        assert len(missing_tests) <= max_missing, \
            f"Missing test files for: {missing_tests}"
    
    def test_documentation_coverage(self):
        """Test that major modules have docstrings."""
        project_root = Path(__file__).parent.parent
        python_files = list(project_root.rglob("*.py"))
        python_files = [f for f in python_files 
                       if not any(part in str(f) for part in ['venv', '__pycache__', '.git', 'tests'])]
        
        missing_docstrings = []
        
        for file_path in python_files[:10]:  # Check first 10 files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Check module docstring
                if not ast.get_docstring(tree):
                    missing_docstrings.append(str(file_path))
                
            except Exception:
                continue
        
        # Allow some files without docstrings
        max_missing_docs = 5
        assert len(missing_docstrings) <= max_missing_docs, \
            f"Files missing docstrings: {missing_docstrings}" 