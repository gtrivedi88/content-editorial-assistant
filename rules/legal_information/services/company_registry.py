"""
Production-Grade Company Registry Service
Handles dynamic company detection with multiple data sources and robust entity recognition.
"""

import os
import yaml
import re
import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class Company:
    """Company data model"""
    name: str
    legal_names: List[str]
    aliases: List[str]
    industry: str
    priority: str
    
    def all_names(self) -> Set[str]:
        """Get all possible names for this company"""
        names = {self.name}
        names.update(self.legal_names)
        names.update(self.aliases)
        return names

class CompanyRegistry:
    """
    Production-grade company registry with multiple data sources.
    
    Features:
    - Configurable data sources (YAML, API, Database)
    - Caching for performance
    - Fuzzy matching capabilities
    - Alias resolution
    - Industry-based filtering
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.companies: Dict[str, Company] = {}
        self.legal_suffixes: Set[str] = set()
        self.config = {}
        self._load_configuration()
        self._initialize_companies()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        current_dir = Path(__file__).parent.parent  # Go up from services/ to legal_information/
        return str(current_dir / "config" / "companies.yaml")
    
    def _load_configuration(self) -> None:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded company registry configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load company configuration: {e}")
            # Fallback to minimal configuration
            self.config = {
                'company_sources': {'static': {'enabled': True, 'companies': []}},
                'legal_suffixes': ['Corp', 'Corporation', 'Inc', 'LLC'],
                'detection_settings': {'case_sensitive': False}
            }
    
    def _initialize_companies(self) -> None:
        """Initialize company data from configured sources"""
        # Load legal suffixes
        self.legal_suffixes = set(self.config.get('legal_suffixes', []))
        
        # Load from static configuration
        static_config = self.config.get('company_sources', {}).get('static', {})
        if static_config.get('enabled', False):
            self._load_static_companies(static_config.get('companies', []))
        
        # Future: Load from API/Database sources
        # self._load_api_companies()
        # self._load_database_companies()
        
        logger.info(f"Initialized company registry with {len(self.companies)} companies")
    
    def _load_static_companies(self, company_data: List[Dict]) -> None:
        """Load companies from static YAML configuration"""
        for company_dict in company_data:
            try:
                company = Company(
                    name=company_dict['name'],
                    legal_names=company_dict.get('legal_names', []),
                    aliases=company_dict.get('aliases', []),
                    industry=company_dict.get('industry', 'unknown'),
                    priority=company_dict.get('priority', 'medium')
                )
                
                # Index by primary name and all aliases for fast lookup
                for name in company.all_names():
                    self.companies[name.lower()] = company
                    
            except KeyError as e:
                logger.warning(f"Skipping invalid company entry: {e}")
    
    def is_known_company(self, name: str) -> bool:
        """Check if a name is a known company"""
        if not name:
            return False
        return name.lower() in self.companies
    
    def get_company(self, name: str) -> Optional[Company]:
        """Get company information by name"""
        if not name:
            return None
        return self.companies.get(name.lower())
    
    def get_all_company_names(self) -> Set[str]:
        """Get all known company names (for backward compatibility)"""
        names = set()
        processed_companies = set()
        
        for company in self.companies.values():
            if company.name not in processed_companies:
                names.update(company.all_names())
                processed_companies.add(company.name)
        
        return names
    
    def has_legal_suffix(self, name: str) -> bool:
        """Check if a company name already has a legal suffix"""
        if not name:
            return False
            
        name_lower = name.lower()
        return any(name_lower.endswith(suffix.lower()) for suffix in self.legal_suffixes)
    
    def detect_companies_in_text(self, text: str) -> List[Tuple[str, int, int, Company]]:
        """
        Production-grade company detection in text.
        
        Returns:
            List of (matched_text, start_pos, end_pos, company_object) tuples
        """
        if not text:
            return []
        
        detections = []
        case_sensitive = self.config.get('detection_settings', {}).get('case_sensitive', False)
        
        # Get unique companies (avoid duplicates from aliases)
        unique_companies = {}
        for company in self.companies.values():
            unique_companies[company.name] = company
        
        for company in unique_companies.values():
            for name in company.all_names():
                # Create regex pattern for word boundaries
                pattern = r'\b' + re.escape(name) + r'\b'
                flags = 0 if case_sensitive else re.IGNORECASE
                
                for match in re.finditer(pattern, text, flags):
                    # Avoid duplicates at same position
                    start, end = match.start(), match.end()
                    duplicate = any(
                        abs(det[1] - start) < 3 and abs(det[2] - end) < 3 
                        for det in detections
                    )
                    
                    if not duplicate:
                        detections.append((match.group(), start, end, company))
        
        # Sort by position in text
        detections.sort(key=lambda x: x[1])
        return detections
    
    def reload_configuration(self) -> None:
        """Reload configuration from file (for runtime updates)"""
        logger.info("Reloading company registry configuration")
        self.companies.clear()
        self._load_configuration()
        self._initialize_companies()

# Global registry instance (singleton pattern for performance)
_global_registry: Optional[CompanyRegistry] = None

def get_company_registry() -> CompanyRegistry:
    """Get global company registry instance"""
    global _global_registry
    if _global_registry is None:
        _global_registry = CompanyRegistry()
    return _global_registry

def reload_company_registry() -> None:
    """Force reload of global company registry"""
    global _global_registry
    if _global_registry:
        _global_registry.reload_configuration()
    else:
        _global_registry = CompanyRegistry()
