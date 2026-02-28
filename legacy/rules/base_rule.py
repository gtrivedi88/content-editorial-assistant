"""
Base Rule Class - Abstract interface for all writing rules.
All rules must inherit from this class and implement the required methods.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import re
import yaml
import os
import sys

# Add project root to path for style_guides import
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import IBM Style Guide mapping utilities
try:
    from style_guides.ibm.ibm_style_mapping import (
        get_rule_mapping,
        format_citation,
        get_confidence_adjustment as get_mapping_confidence_adjustment,
        get_verification_status,
        IBM_STYLE_GUIDE_DEFAULT_CITATION
    )
    IBM_STYLE_MAPPING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: IBM Style mapping not available: {e}")
    IBM_STYLE_MAPPING_AVAILABLE = False
    IBM_STYLE_GUIDE_DEFAULT_CITATION = "IBM Style Guide"
    def get_rule_mapping(_rule_id, _category=None):
        return None
    def format_citation(_rule_id, _category=None, _include_verification=True):
        return IBM_STYLE_GUIDE_DEFAULT_CITATION
    def get_mapping_confidence_adjustment(_rule_id, _category=None):
        return 0.0
    def get_verification_status(_rule_id, _category=None):
        return {'status': 'unknown', 'verified': False}


class BaseRule(ABC):
    """
    Abstract base class for all writing rules.
    Provides exception checking, IBM Style citations, and standardized error creation.
    """

    # Class-level cache for exceptions to avoid reading the file for every rule instance.
    _exceptions = None

    def __init__(self) -> None:
        """Initializes the rule and loads the exception configuration."""
        self.rule_type = self._get_rule_type()
        self.severity_levels = ['low', 'medium', 'high']

        # Load exceptions once and cache them at the class level.
        if BaseRule._exceptions is None:
            self._load_exceptions()

        # Load IBM Style Guide mapping for this rule
        self._ibm_style_mapping = None
        self._ibm_style_citation = None
        self._ibm_style_confidence_boost = 0.0
        if IBM_STYLE_MAPPING_AVAILABLE:
            self._load_ibm_style_mapping()

    @classmethod
    def _load_exceptions(cls):
        """
        Loads the exceptions.yaml file and caches it.
        This method is called only once to optimize performance.
        """
        path = os.path.join(os.path.dirname(__file__), '..', 'config', 'exceptions.yaml')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cls._exceptions = yaml.safe_load(f)
                if not isinstance(cls._exceptions, dict):
                    print(f"Warning: exceptions.yaml at {path} is not a valid dictionary. Disabling exceptions.")
                    cls._exceptions = {}
        except FileNotFoundError:
            print(f"Warning: exceptions.yaml not found at {path}. No exceptions will be applied.")
            cls._exceptions = {}
        except Exception as e:
            print(f"Error loading or parsing exceptions.yaml: {e}")
            cls._exceptions = {}

    def _load_ibm_style_mapping(self):
        """
        Load IBM Style Guide mapping for this specific rule.
        Provides citation, confidence boost, and verification status.
        """
        try:
            category = self._get_rule_category_for_mapping()
            self._ibm_style_mapping = get_rule_mapping(self.rule_type, category)

            if self._ibm_style_mapping:
                self._ibm_style_citation = format_citation(
                    self.rule_type, category, include_verification=True
                )
                self._ibm_style_confidence_boost = get_mapping_confidence_adjustment(
                    self.rule_type, category
                )
                verification = get_verification_status(self.rule_type, category)
                if verification['verified']:
                    print(f"✓ IBM Style mapping loaded for '{self.rule_type}': {self._ibm_style_citation}")
            else:
                self._ibm_style_citation = IBM_STYLE_GUIDE_DEFAULT_CITATION
                print(f"⚠️ No IBM Style mapping found for rule '{self.rule_type}'")

        except Exception as e:
            print(f"⚠️ Error loading IBM Style mapping for '{self.rule_type}': {e}")
            self._ibm_style_citation = IBM_STYLE_GUIDE_DEFAULT_CITATION
            self._ibm_style_confidence_boost = 0.0

    def _get_rule_category_for_mapping(self) -> str:
        """
        Determine the rule category for IBM Style mapping lookup.
        Override in subclasses if category can't be inferred from class name.
        """
        category_keywords = {
            'word_usage': ['word', 'awords', 'bwords', 'cwords'],
            'language_and_grammar': ['language', 'grammar', 'spelling', 'article', 'pronoun', 'verb'],
            'structure_and_format': ['structure', 'format', 'heading', 'list', 'procedure', 'referential'],
            'audience_and_medium': ['audience', 'medium', 'tone', 'llm', 'global'],
            'legal_information': ['legal', 'claim', 'company'],
            'punctuation': ['punctuation', 'comma', 'semicolon', 'colon', 'dash', 'period'],
            'numbers_and_measurement': ['number', 'currency', 'date', 'time', 'measurement'],
            'technical_elements': ['technical', 'command', 'keyboard', 'mouse', 'file', 'directory'],
            'references': ['reference', 'citation', 'geographic', 'product']
        }

        class_name = self.__class__.__name__.lower()
        for category, keywords in category_keywords.items():
            if any(keyword in class_name for keyword in keywords):
                return category

        module = self.__class__.__module__
        for category in category_keywords:
            if category in module:
                return category

        return 'language_and_grammar'

    def _is_excepted(self, text_span: str) -> bool:
        """
        Checks if a given text span is in the global or rule-specific exception list.
        The check is case-insensitive.
        """
        if not self._exceptions or not text_span:
            return False

        text_span_lower = text_span.lower().strip()

        global_exceptions = self._exceptions.get('global_exceptions', [])
        if isinstance(global_exceptions, list):
            if text_span_lower in [str(exc).lower() for exc in global_exceptions]:
                return True

        rule_specifics = self._exceptions.get('rule_specific_exceptions', {})
        if isinstance(rule_specifics, dict):
            rule_exceptions = rule_specifics.get(self.rule_type, [])
            if isinstance(rule_exceptions, list):
                if text_span_lower in [str(exc).lower() for exc in rule_exceptions]:
                    return True

        return False

    @abstractmethod
    def _get_rule_type(self) -> str:
        """Return the rule type identifier (e.g., 'passive_voice', 'sentence_length')."""
        pass

    @abstractmethod
    def analyze(self, text: str, sentences: List[str], nlp=None, context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        """
        Analyze text and return list of errors found.

        Args:
            text: Full text to analyze
            sentences: List of sentences
            nlp: SpaCy nlp object (optional)
            context: Optional context information about the block being analyzed
            spacy_doc: Pre-created SpaCy doc object (optional, for performance optimization)

        Returns:
            List of error dictionaries.
        """
        # Skip analysis for code blocks, listings, and literal blocks
        if context and context.get('block_type') in ['listing', 'literal', 'code_block', 'inline_code']:
            return []
        pass

    def _is_technical_content(self, text_span: str) -> bool:
        """
        Check if a text span is technical content (URL, email, file path) that
        should not be flagged by style rules.
        """
        if not text_span:
            return False

        stripped = text_span.strip()

        if re.match(r'https?://', stripped) or re.match(r'www\.', stripped):
            return True

        if re.match(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', stripped):
            return True

        if re.match(r'[/~][\w./\-]+', stripped) or re.match(r'[A-Z]:\\', stripped):
            return True

        if stripped.startswith('`') and stripped.endswith('`'):
            return True

        if ' ' not in stripped and (
            re.match(r'^[a-z]+[A-Z]', stripped) or
            '_' in stripped or
            re.match(r'^[a-z]+(\.[a-z]+){2,}', stripped)
        ):
            return True

        return False

    def _create_error(self, sentence: str, sentence_index: int, message: str,
                     suggestions: List[str], severity: str = 'medium',
                     text: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                     **extra_data) -> Optional[Dict[str, Any]]:
        """
        Create standardized error dictionary.

        Returns None if the flagged text is in the exception list or is technical content,
        providing universal false positive protection for all rules.
        """
        flagged_text = extra_data.get('flagged_text', '')
        if flagged_text:
            if self._is_excepted(flagged_text):
                return None
            if self._is_technical_content(flagged_text):
                return None

        if severity not in self.severity_levels:
            severity = 'medium'

        final_message = str(message)
        if self._ibm_style_citation and not final_message.endswith(self._ibm_style_citation):
            if 'IBM Style' not in final_message and 'Red Hat' not in final_message:
                final_message = f"{final_message} Per {self._ibm_style_citation}."

        error = {
            'type': self.rule_type,
            'message': final_message,
            'suggestions': [str(s) for s in suggestions],
            'sentence': str(sentence),
            'sentence_index': int(sentence_index),
            'severity': severity,
            'style_guide_citation': self._ibm_style_citation or IBM_STYLE_GUIDE_DEFAULT_CITATION
        }

        for key, value in extra_data.items():
            try:
                error[str(key)] = self._make_serializable(value)
            except Exception as e:
                error[str(key)] = f"<serialization_error: {str(e)}>"

        return error

    def _make_serializable(self, data: Any) -> Any:
        """Recursively convert data structure to be JSON serializable."""
        if data is None:
            return None

        if hasattr(data, 'text') and hasattr(data, 'lemma_'):
            return self._token_to_dict(data)

        if (hasattr(data, '__iter__') and hasattr(data, 'get') and
            not isinstance(data, (str, dict, list, tuple))):
            try:
                return dict(data)
            except Exception:
                return str(data)

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                try:
                    result[str(key)] = self._make_serializable(value)
                except Exception:
                    result[str(key)] = str(value)
            return result

        if isinstance(data, list):
            return [self._make_serializable(item) for item in data]

        if isinstance(data, tuple):
            return [self._make_serializable(item) for item in data]

        if isinstance(data, set):
            return [self._make_serializable(item) for item in data]

        if isinstance(data, (str, int, float, bool)):
            return data

        try:
            return str(data)
        except Exception:
            return None

    def _token_to_dict(self, token) -> Optional[Dict[str, Any]]:
        """Convert SpaCy token to JSON-serializable dictionary."""
        if token is None:
            return None

        try:
            token_dict = {
                'text': token.text,
                'lemma': token.lemma_,
                'pos': token.pos_,
                'tag': token.tag_,
                'dep': token.dep_,
                'idx': token.idx,
                'i': token.i
            }

            if hasattr(token, 'morph') and token.morph:
                try:
                    token_dict['morphology'] = dict(token.morph)
                except Exception:
                    token_dict['morphology'] = str(token.morph)
            else:
                token_dict['morphology'] = {}

            return token_dict

        except Exception:
            return {
                'text': str(token),
                'lemma': getattr(token, 'lemma_', ''),
                'pos': getattr(token, 'pos_', ''),
                'tag': getattr(token, 'tag_', ''),
                'dep': getattr(token, 'dep_', ''),
                'idx': getattr(token, 'idx', 0),
                'i': getattr(token, 'i', 0),
                'morphology': {}
            }
