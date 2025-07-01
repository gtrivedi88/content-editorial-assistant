"""
Rules Registry - Automatically discovers and loads all writing rules.
This system allows for easy addition of new rules without modifying the main analyzer.
Supports automatic discovery of rules in subdirectories (e.g., punctuation/, grammar/, etc.)
"""

import importlib
import importlib.util
import pkgutil
import os
from typing import List, Dict, Any, Optional

# Import base rule with proper path handling
try:
    from .base_rule import BaseRule
except ImportError:
    # Fallback for when running from different contexts
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from base_rule import BaseRule

class RulesRegistry:
    """Registry that automatically discovers and manages all writing rules from all subdirectories up to 4 levels deep."""
    
    def __init__(self):
        self.rules = {}
        self.rule_locations = {}  # Track where each rule was found
        self._load_all_rules()
    
    def _load_all_rules(self):
        """Automatically discover and load all rule modules from main directory and nested subdirectories (up to 4 levels deep)."""
        try:
            # Get the current directory (rules directory)
            rules_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"🔍 Scanning for rules in: {rules_dir}")
            
            # Recursively walk through all subdirectories
            for root, dirs, files in os.walk(rules_dir):
                # Calculate relative path from rules directory
                rel_path = os.path.relpath(root, rules_dir)
                
                # Skip __pycache__ directories and hidden directories
                if '__pycache__' in root or any(part.startswith('.') for part in rel_path.split(os.sep)):
                    continue
                
                # Calculate nesting depth
                if rel_path == '.':
                    depth = 0
                    path_parts = []
                else:
                    path_parts = rel_path.split(os.sep)
                    depth = len(path_parts)
                
                # Limit depth to 4 levels as requested
                if depth > 4:
                    print(f"⚠️ Skipping directory too deep (>{4} levels): {rel_path}")
                    continue
                
                # Process all Python files ending with '_rule.py' or '.py' (to be more flexible)
                for filename in files:
                    if filename.endswith('_rule.py') and filename != 'base_rule.py':
                        module_name = filename[:-3]  # Remove .py extension
                        
                        try:
                            # Determine import path and display location based on directory structure
                            if rel_path == '.':
                                # Main rules directory
                                import_path = module_name
                                display_location = "main"
                            else:
                                # Nested subdirectory - convert path separators to dots
                                subdir_path = rel_path.replace(os.sep, '.')
                                import_path = f"{subdir_path}.{module_name}"
                                display_location = ' > '.join(path_parts)
                            
                            print(f"🔍 Attempting to load: {import_path} (depth: {depth})")
                            
                            # Import the module using enhanced import mechanism
                            module = self._import_rule_module_enhanced(import_path, root, filename, depth)
                            
                            if module:
                                # Find and instantiate the rule class
                                rule_instance = self._find_and_instantiate_rule_class(module, module_name)
                                
                                if rule_instance:
                                    rule_type = rule_instance.rule_type
                                    
                                    # Check for rule type conflicts
                                    if rule_type in self.rules:
                                        print(f"⚠️ Rule type conflict: {rule_type} already exists from {self.rule_locations[rule_type]}")
                                        print(f"   Keeping existing rule, skipping: {display_location}")
                                    else:
                                        self.rules[rule_type] = rule_instance
                                        self.rule_locations[rule_type] = display_location
                                    print(f"✅ Loaded rule: {rule_type} (from {display_location})")
                                else:
                                    print(f"⚠️ No valid rule class found in {import_path}")
                            else:
                                print(f"❌ Failed to import module: {import_path}")
                                
                        except Exception as e:
                            print(f"❌ Error loading rule {import_path}: {e}")
                            # Continue with next rule instead of stopping
                            
        except Exception as e:
            print(f"❌ Critical error in rules registry initialization: {e}")
            
        print(f"📊 Rules discovery complete. Loaded {len(self.rules)} rules from {len(set(self.rule_locations.values()))} locations.")
    
    def _import_rule_module_enhanced(self, import_path: str, file_dir: str, filename: str, depth: int):
        """Enhanced import method with better handling for deeply nested modules (up to 4 levels)."""
        try:
            # Method 1: Try direct file-based import (most reliable for nested modules)
            file_path = os.path.join(file_dir, filename)
            
            # Create a unique module name to avoid conflicts
            unique_module_name = f"rule_module_{import_path.replace('.', '_')}"
            
            spec = importlib.util.spec_from_file_location(unique_module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            else:
                raise ImportError(f"Could not create spec for {import_path}")
                    
        except Exception as e:
            print(f"🔄 Direct import failed for {import_path}, trying fallback methods: {e}")
            # Fallback to original methods
            return self._import_rule_module_fallback(import_path, file_dir, filename)
    
    def _import_rule_module(self, import_path: str, file_dir: str, filename: str):
        """Original import method for backward compatibility."""
        return self._import_rule_module_enhanced(import_path, file_dir, filename, 0)
    
    def _import_rule_module_fallback(self, import_path: str, file_dir: str, filename: str):
        """Fallback import methods for edge cases."""
        try:
            # Method 1: Try package-based import if we're in a package context
            if __package__:
                full_import_path = f'.{import_path}' if not import_path.startswith('.') else import_path
                try:
                    return importlib.import_module(full_import_path, __package__)
                except ImportError as package_error:
                    print(f"Package import failed: {package_error}")
            
            # Method 2: Direct file import with simple name
            file_path = os.path.join(file_dir, filename)
            simple_name = os.path.basename(filename)[:-3]  # Remove .py
            
            spec = importlib.util.spec_from_file_location(simple_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            
            raise ImportError(f"All fallback methods failed for {import_path}")
                
        except Exception as e:
            print(f"🚫 All import methods failed for {import_path}: {e}")
            return None
    
    def _find_and_instantiate_rule_class(self, module, module_name: str):
        """Find the rule class in the module and instantiate it."""
        try:
            # Look for classes that inherit from BaseRule (with flexible BaseRule matching)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    self._is_rule_class(attr) and 
                    attr.__name__ != 'BaseRule'):
                    
                    try:
                        # Instantiate the rule
                        instance = attr()
                        print(f"✅ Found and instantiated rule class: {attr.__name__}")
                        return instance
                    except Exception as inst_err:
                        print(f"⚠️ Found rule class {attr.__name__} but failed to instantiate: {inst_err}")
                        continue
            
            # If no rule class found, log warning
            print(f"⚠️ No rule class found in module {module_name}")
            return None
            
        except Exception as e:
            print(f"⚠️ Failed to find rule class in {module_name}: {e}")
            return None
    
    def _is_rule_class(self, cls) -> bool:
        """Check if a class is a rule class by examining its inheritance chain and interface."""
        try:
            # Check if it's a class
            if not isinstance(cls, type):
                return False
            
            # Check if class name suggests it's a rule
            if not cls.__name__.endswith('Rule'):
                return False
            
            # Check if it has the required methods (duck typing approach)
            required_methods = ['analyze', '_get_rule_type']
            if not all(hasattr(cls, method) for method in required_methods):
                return False
            
            # Check inheritance chain for BaseRule (flexible matching)
            for base in cls.__mro__:
                if (hasattr(base, '__name__') and 
                    base.__name__ == 'BaseRule' and
                    hasattr(base, 'analyze') and
                    hasattr(base, '_get_rule_type')):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def get_rule(self, rule_type: str) -> Optional[BaseRule]:
        """Get a specific rule by type."""
        return self.rules.get(rule_type)
    
    def get_all_rules(self) -> Dict[str, BaseRule]:
        """Get all loaded rules."""
        return self.rules
    
    def get_rules_by_category(self, category: Optional[str] = None) -> Dict[str, BaseRule]:
        """Get rules filtered by category/subdirectory."""
        if category is None:
            return self.get_all_rules()
        
        # Filter rules based on category (could be extended to track rule origins)
        filtered_rules = {}
        for rule_type, rule in self.rules.items():
            # This could be extended to track which subdirectory each rule came from
            filtered_rules[rule_type] = rule
        
        return filtered_rules
    
    def list_discovered_rules(self) -> Dict[str, Any]:
        """List all discovered rules organized by their source location."""
        rules_by_location = {}
        
        # Group rules by their source location
        for rule_type, location in self.rule_locations.items():
            if location not in rules_by_location:
                rules_by_location[location] = []
            rules_by_location[location].append(rule_type)
        
        return {
            'total_rules': len(self.rules),
            'rules_by_location': rules_by_location,
            'all_rule_types': list(self.rules.keys()),
            'locations': list(set(self.rule_locations.values()))
        }
    
    def analyze_with_all_rules(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Run analysis with all discovered rules from all directories."""
        all_errors = []
        
        for rule in self.rules.values():
            try:
                rule_errors = rule.analyze(text, sentences, nlp)
                
                # Ensure all errors are JSON serializable
                serializable_errors = []
                for error in rule_errors:
                    # Use base rule's serialization method
                    serializable_error = rule._make_serializable(error)
                    serializable_errors.append(serializable_error)
                
                all_errors.extend(serializable_errors)
                
            except Exception as e:
                print(f"❌ Error in rule {rule.__class__.__name__}: {e}")
                # Add a system error that is guaranteed to be serializable
                all_errors.append({
                    'type': 'system_error',
                    'message': f'Rule {rule.__class__.__name__} failed: {str(e)}',
                    'suggestions': ['Check rule implementation'],
                    'sentence': '',
                    'sentence_index': -1,
                    'severity': 'low'
                })
        
        return all_errors

# Global registry instance (lazy-loaded to avoid circular imports)
_registry = None

def get_registry():
    """Get the global registry instance, initializing if needed."""
    global _registry
    if _registry is None:
        _registry = RulesRegistry()
    return _registry

# Create a registry proxy that initializes only when accessed
class RegistryProxy:
    """Proxy object that initializes the registry only when accessed."""
    
    def __getattr__(self, name):
        return getattr(get_registry(), name)

# For backward compatibility
registry = RegistryProxy() 