"""
Error Station Mapper - Single Source of Truth
Eliminates duplication in error-to-station categorization across the system.
"""

import logging
from typing import List, Dict, Set
import fnmatch

logger = logging.getLogger(__name__)


class ErrorStationMapper:
    """
    Single source of truth for error categorization into assembly line stations.
    Replaces scattered hardcoded mappings throughout the system.
    """
    
    # Definitive mapping of error types to processing stations
    # COMPREHENSIVE COVERAGE: All 93+ rule types from rules directory
    STATION_RULES = {
        'urgent': [
            # Legal & Critical Issues (legal compliance, critical content accuracy)
            'legal_claims', 'legal_company_names', 'legal_personal_information',
            'inclusive_language', 'second_person', 'claims',
            'company_names', 'personal_information'
        ],
        'high': [
            # Structural & Organization Issues (document structure, clarity, organization)
            'passive_voice', 'sentence_length', 'subjunctive_mood', 'verbs', 
            'headings', 'ambiguity', 'pronouns', 
            
            # Document Structure  
            'messages', 'procedures', 'lists', 'paragraphs', 'notes',
            'admonitions', 'glossaries', 'highlighting',
            
            # Modular Compliance (document organization)
            'modular_compliance', 'concept_module', 'procedure_module', 'reference_module'
        ],
        'medium': [
            # Grammar & Language Correctness
            'contractions', 'spelling', 'terminology', 'anthropomorphism',
            'capitalization', 'prefixes', 'plurals', 'abbreviations',
            'possessives', 'prepositions', 'articles', 'conjunctions',
            'adverbs_only',
            
            # Technical Elements - Use wildcard (all follow technical_* pattern)
            'technical_*',  # Covers technical_commands, technical_files_directories, etc.
            
            # Word Usage - Use wildcard (all follow word_usage_* pattern)  
            'word_usage_*',  # Covers word_usage_a through word_usage_z
            
            # Numbers & Measurement (precision matters)  
            'numbers_currency', 'currency'
        ],
        'low': [
            # Style & Polish (final formatting and style consistency)
            'tone', 'citations', 'conversational_style', 'global_audiences',
            'llm_consumability',
            
            # Numbers & Dates (formatting style)
            'dates_and_times', 'numbers_general', 'numerals_vs_words', 
            'units_of_measurement',
            
            # Punctuation Rules (most don't follow punctuation_* pattern)
            'colons', 'commas', 'dashes', 'ellipses', 'exclamation_points',
            'hyphens', 'parentheses', 'periods', 'quotation_marks', 
            'semicolons', 'slashes', 'punctuation_and_symbols',
            
            # References - Use wildcard (all follow references_* pattern)
            'references_*'  # Covers references_citations, references_product_names, etc.
        ]
    }
    
    # Priority order for processing
    STATION_PRIORITY = ['urgent', 'high', 'medium', 'low']
    
    # Human-readable display names
    STATION_DISPLAY_NAMES = {
        'urgent': 'Critical/Legal Pass',
        'high': 'Structural Pass', 
        'medium': 'Grammar Pass',
        'low': 'Style Pass'
    }
    
    @classmethod
    def get_station_for_error(cls, error_type: str) -> str:
        """
        Get the appropriate station for a given error type.
        
        Args:
            error_type: The error type to categorize
            
        Returns:
            Station name ('urgent', 'high', 'medium', 'low')
            Returns 'medium' as default for unknown error types
        """
        if not error_type:
            return 'medium'
            
        for station, patterns in cls.STATION_RULES.items():
            for pattern in patterns:
                if '*' in pattern:
                    # Handle wildcard patterns (e.g., 'word_usage_*')
                    if fnmatch.fnmatch(error_type, pattern):
                        return station
                else:
                    # Exact match
                    if error_type == pattern:
                        return station
        
        # Default fallback for unknown error types
        logger.warning(f"Unknown error type '{error_type}', assigning to 'medium' station")
        return 'medium'
    
    @classmethod
    def get_applicable_stations(cls, error_types: List[str]) -> List[str]:
        """
        Get list of stations needed for a set of error types, in priority order.
        
        Args:
            error_types: List of error type strings
            
        Returns:
            List of station names in priority order
        """
        if not error_types:
            return []
            
        stations_needed = set()
        
        for error_type in error_types:
            station = cls.get_station_for_error(error_type)
            stations_needed.add(station)
        
        # Return in priority order
        return [station for station in cls.STATION_PRIORITY if station in stations_needed]
    
    @classmethod
    def get_errors_for_station(cls, errors: List[Dict], station: str) -> List[Dict]:
        """
        Filter errors that belong to a specific station.
        
        Args:
            errors: List of error dictionaries with 'type' field
            station: Station name to filter for
            
        Returns:
            List of errors belonging to the specified station
        """
        if not errors or not station:
            return []
            
        station_errors = []
        
        for error in errors:
            error_type = error.get('type', '')
            if cls.get_station_for_error(error_type) == station:
                station_errors.append(error)
        
        return station_errors
    
    @classmethod
    def get_station_display_name(cls, station: str) -> str:
        """
        Get user-friendly display name for a station.
        
        Args:
            station: Station identifier
            
        Returns:
            Human-readable display name
        """
        return cls.STATION_DISPLAY_NAMES.get(station, f'{station.title()} Pass')
    
    @classmethod
    def get_station_stats(cls) -> Dict[str, int]:
        """
        Get statistics about station coverage.
        
        Returns:
            Dictionary with station names and error type counts
        """
        stats = {}
        
        for station, patterns in cls.STATION_RULES.items():
            # Count explicit patterns (wildcards count as 1)
            stats[station] = len(patterns)
        
        return stats
    
    @classmethod
    def validate_error_coverage(cls, actual_error_types: Set[str]) -> Dict[str, List[str]]:
        """
        Validate that all actual error types are covered by station mappings.
        
        Args:
            actual_error_types: Set of error types found in the system
            
        Returns:
            Dictionary with 'covered' and 'uncovered' lists
        """
        covered = []
        uncovered = []
        
        for error_type in actual_error_types:
            station = cls.get_station_for_error(error_type)
            if station != 'medium' or cls._is_explicitly_mapped(error_type):
                covered.append(error_type)
            else:
                uncovered.append(error_type)
        
        return {
            'covered': covered,
            'uncovered': uncovered,
            'coverage_percentage': len(covered) / len(actual_error_types) * 100 if actual_error_types else 0
        }
    
    @classmethod
    def _is_explicitly_mapped(cls, error_type: str) -> bool:
        """Check if error type is explicitly mapped (not defaulted to medium)."""
        for station, patterns in cls.STATION_RULES.items():
            for pattern in patterns:
                if '*' in pattern:
                    if fnmatch.fnmatch(error_type, pattern):
                        return True
                else:
                    if error_type == pattern:
                        return True
        return False
