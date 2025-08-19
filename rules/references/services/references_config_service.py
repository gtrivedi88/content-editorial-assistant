"""
References Configuration Service

Manages YAML-based configuration for all references rules with caching,
pattern matching, and context-aware evidence calculation.
"""

import os
import yaml
import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CitationPattern:
    """Represents a citation pattern with evidence scoring."""
    phrase: str
    evidence: float
    severity: str
    message: str
    alternatives: List[str] = field(default_factory=list)

@dataclass
class ProductInfo:
    """Represents IBM product information."""
    name: str
    evidence: float
    requires_ibm_prefix: bool
    category: str
    variants: List[str] = field(default_factory=list)

@dataclass
class TitleInfo:
    """Represents professional title information."""
    title: str
    evidence: float
    capitalization_rules: Dict[str, str]
    priority: str
    variants: List[str] = field(default_factory=list)

@dataclass
class VersionPattern:
    """Represents version formatting pattern."""
    prefix: str
    evidence: float
    severity: str
    message: str
    alternatives: List[str] = field(default_factory=list)

@dataclass
class ReferenceContext:
    """Context information for references analysis."""
    content_type: str = ""
    domain: str = ""
    block_type: str = ""
    has_citations: bool = False

class ReferencesConfigService:
    """
    Configuration management service for references rules.
    
    Features:
    - YAML-based configuration management
    - Pattern caching for performance
    - Context-aware evidence calculation
    - Runtime configuration updates
    - Feedback pattern learning
    """
    
    _instances: Dict[str, 'ReferencesConfigService'] = {}
    
    def __new__(cls, config_name: str):
        """Singleton pattern for each configuration type."""
        if config_name not in cls._instances:
            cls._instances[config_name] = super(ReferencesConfigService, cls).__new__(cls)
        return cls._instances[config_name]
    
    def __init__(self, config_name: str):
        """Initialize references config service for a specific config."""
        if hasattr(self, '_initialized'):
            return
            
        self.config_name = config_name
        self.config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', f'{config_name}.yaml'
        )
        self._config: Dict[str, Any] = {}
        self._pattern_cache: Dict[str, Any] = {}
        
        # Initialize all possible attributes to avoid AttributeError
        self._citation_patterns = {}
        self._reference_terms = set()
        self._geographic_entities = {}
        self._location_patterns = {}
        self._ibm_products = {}
        self._competitor_companies = set()
        self._ui_elements = set()
        self._professional_titles = {}
        self._name_prefixes = set()
        self._version_prefixes = {}
        self._valid_patterns = []
        
        self._load_configuration()
        self._initialized = True
    
    def _load_configuration(self):
        """Load configuration from YAML file."""
        logger.info(f"Loading references config from {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            
            # Process configuration based on type
            if self.config_name == 'citation_patterns':
                self._process_citation_config()
            elif self.config_name == 'geographic_patterns':
                self._process_geographic_config()
            elif self.config_name == 'product_patterns':
                self._process_product_config()
            elif self.config_name == 'professional_titles':
                self._process_titles_config()
            elif self.config_name == 'version_patterns':
                self._process_version_config()
            
            logger.info(f"Loaded references configuration: {self.config_name}")
            
        except FileNotFoundError:
            logger.error(f"References config file not found: {self.config_path}")
            self._config = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing references YAML: {e}")
            self._config = {}
        except Exception as e:
            logger.error(f"Unexpected error loading references config: {e}")
            self._config = {}
    
    def _process_citation_config(self):
        """Process citation patterns configuration."""
        self._citation_patterns = {}
        self._reference_terms = set()
        
        # Load problematic link patterns
        problematic = self._config.get('problematic_link_patterns', {})
        exact_violations = problematic.get('exact_violations', [])
        
        for violation in exact_violations:
            pattern = CitationPattern(
                phrase=violation['phrase'],
                evidence=violation['evidence'],
                severity=violation['severity'],
                message=violation['message'],
                alternatives=violation.get('alternatives', [])
            )
            self._citation_patterns[violation['phrase']] = pattern
        
        # Load reference capitalization terms
        ref_cap = self._config.get('reference_capitalization', {})
        document_parts = ref_cap.get('document_parts', [])
        
        for part in document_parts:
            self._reference_terms.add(part['phrase'])
    
    def _process_geographic_config(self):
        """Process geographic patterns configuration."""
        self._geographic_entities = self._config.get('geographic_entities', {})
        self._location_patterns = {}
        
        # Load capitalization rules
        cap_rules = self._config.get('location_capitalization', {})
        always_cap = cap_rules.get('always_capitalize', [])
        
        for rule in always_cap:
            for example in rule.get('examples', []):
                self._location_patterns[example.lower()] = rule['evidence']
    
    def _process_product_config(self):
        """Process product patterns configuration."""
        self._ibm_products = {}
        self._competitor_companies = set()
        self._ui_elements = set()
        
        # Load IBM products
        ibm_products = self._config.get('ibm_products', {})
        well_known = ibm_products.get('well_known_products', [])
        
        for product in well_known:
            product_info = ProductInfo(
                name=product['name'],
                evidence=product['evidence'],
                requires_ibm_prefix=product['requires_ibm_prefix'],
                category=product['category'],
                variants=product.get('variants', [])
            )
            self._ibm_products[product['name'].lower()] = product_info
            
            # Add variants
            for variant in product.get('variants', []):
                self._ibm_products[variant.lower()] = product_info
        
        # Load competitor companies
        competitors = self._config.get('competitor_companies', {})
        major_competitors = competitors.get('major_competitors', [])
        self._competitor_companies.update(comp.lower() for comp in major_competitors)
        
        # Load UI elements
        ui_elements = self._config.get('ui_elements', {})
        interface_terms = ui_elements.get('interface_terms', [])
        self._ui_elements.update(term.lower() for term in interface_terms)
    
    def _process_titles_config(self):
        """Process professional titles configuration."""
        self._professional_titles = {}
        self._name_prefixes = set()
        
        # Load professional titles from all categories
        titles_config = self._config.get('professional_titles', {})
        
        for category_name, titles_list in titles_config.items():
            if isinstance(titles_list, list):
                for title_info in titles_list:
                    title = TitleInfo(
                        title=title_info['title'],
                        evidence=title_info['evidence'],
                        capitalization_rules=title_info['capitalization_rules'],
                        priority=title_info['priority'],
                        variants=title_info.get('variants', [])
                    )
                    self._professional_titles[title_info['title'].lower()] = title
                    
                    # Add variants
                    for variant in title_info.get('variants', []):
                        self._professional_titles[variant.lower()] = title
        
        # Load name prefixes
        prefixes = self._config.get('name_prefixes', {})
        common_prefixes = prefixes.get('common_prefixes', [])
        self._name_prefixes.update(prefix.lower() for prefix in common_prefixes)
    
    def _process_version_config(self):
        """Process version patterns configuration."""
        self._version_prefixes = {}
        self._valid_patterns = []
        
        # Load version prefixes
        prefixes = self._config.get('version_prefixes', {})
        
        for category_name, prefix_list in prefixes.items():
            if isinstance(prefix_list, list):
                for prefix_info in prefix_list:
                    pattern = VersionPattern(
                        prefix=prefix_info['prefix'],
                        evidence=prefix_info['evidence'],
                        severity=prefix_info['severity'],
                        message=prefix_info['message'],
                        alternatives=prefix_info.get('alternatives', [])
                    )
                    self._version_prefixes[prefix_info['prefix'].lower()] = pattern
        
        # Load valid patterns
        patterns = self._config.get('version_patterns', {})
        self._valid_patterns = patterns.get('valid_patterns', [])
    
    # Citation patterns methods
    def get_citation_pattern(self, phrase: str) -> Optional[CitationPattern]:
        """Get citation pattern for a phrase."""
        if self.config_name != 'citation_patterns':
            return None
        return self._citation_patterns.get(phrase.lower())
    
    def is_problematic_link_text(self, text: str) -> bool:
        """Check if text is problematic link text."""
        if self.config_name != 'citation_patterns':
            return False
        return text.lower() in self._citation_patterns
    
    def is_reference_term(self, term: str) -> bool:
        """Check if term is a reference term (chapter, section, etc.)."""
        if self.config_name != 'citation_patterns':
            return False
        return term.lower() in self._reference_terms
    
    def get_reference_indicators(self) -> List[str]:
        """Get list of reference indicators."""
        if self.config_name != 'citation_patterns':
            return []
        ref_cap = self._config.get('reference_capitalization', {})
        return ref_cap.get('reference_indicators', [])
    
    # Geographic patterns methods
    def get_geographic_entities(self) -> Dict[str, Any]:
        """Get geographic entity configuration."""
        if self.config_name != 'geographic_patterns':
            return {}
        return self._geographic_entities
    
    def get_location_evidence(self, location: str) -> float:
        """Get evidence score for a location."""
        if self.config_name != 'geographic_patterns':
            return 0.5
        return self._location_patterns.get(location.lower(), 0.5)
    
    def get_brand_indicators(self) -> List[str]:
        """Get brand context indicators."""
        if self.config_name != 'geographic_patterns':
            return []
        brand_context = self._config.get('brand_context', {})
        return brand_context.get('corporate_indicators', [])
    
    # Product patterns methods
    def get_ibm_product(self, name: str) -> Optional[ProductInfo]:
        """Get IBM product information."""
        if self.config_name != 'product_patterns':
            return None
        return self._ibm_products.get(name.lower())
    
    def is_competitor_company(self, name: str) -> bool:
        """Check if name is a competitor company."""
        if self.config_name != 'product_patterns':
            return False
        return name.lower() in self._competitor_companies
    
    def is_ui_element(self, term: str) -> bool:
        """Check if term is a UI element."""
        if self.config_name != 'product_patterns':
            return False
        return term.lower() in self._ui_elements
    
    def get_product_indicators(self) -> List[str]:
        """Get product naming indicators."""
        if self.config_name != 'product_patterns':
            return []
        indicators = self._config.get('ibm_products', {}).get('product_indicators', {})
        return indicators.get('suffixes', [])
    
    # Professional titles methods
    def get_title_info(self, title: str) -> Optional[TitleInfo]:
        """Get professional title information."""
        if self.config_name != 'professional_titles':
            return None
        return self._professional_titles.get(title.lower())
    
    def is_name_prefix(self, prefix: str) -> bool:
        """Check if text is a name prefix."""
        if self.config_name != 'professional_titles':
            return False
        return prefix.lower() in self._name_prefixes
    
    def get_standalone_indicators(self) -> List[str]:
        """Get standalone title indicators."""
        if self.config_name != 'professional_titles':
            return []
        context = self._config.get('context_detection', {})
        standalone = context.get('standalone_indicators', {})
        return standalone.get('determiners', [])
    
    # Version patterns methods
    def get_version_pattern(self, prefix: str) -> Optional[VersionPattern]:
        """Get version pattern for a prefix."""
        if self.config_name != 'version_patterns':
            return None
        return self._version_prefixes.get(prefix.lower())
    
    def is_valid_version_pattern(self, version: str) -> bool:
        """Check if version matches valid patterns."""
        if self.config_name != 'version_patterns':
            return True
        
        for pattern in self._valid_patterns:
            if re.match(pattern['regex'], version):
                return True
        return False
    
    def get_technical_indicators(self) -> List[str]:
        """Get technical context indicators."""
        if self.config_name != 'version_patterns':
            return []
        tech_contexts = self._config.get('technical_contexts', {})
        return tech_contexts.get('technical_indicators', [])
    
    # Common methods
    def get_feedback_patterns(self) -> Dict[str, Any]:
        """Get feedback patterns for learning."""
        return self._config.get('feedback_patterns', {})
    
    def get_content_type_config(self, content_type: str) -> Dict[str, Any]:
        """Get configuration for specific content type."""
        content_config = self._config.get('content_type_appropriateness', {})
        return content_config.get(content_type, {})
    
    def get_block_type_config(self, block_type: str) -> Dict[str, Any]:
        """Get configuration for specific block type."""
        block_config = self._config.get('block_type_adjustments', {})
        return block_config.get(block_type, {})
    
    def should_skip_analysis(self, context: ReferenceContext) -> bool:
        """Check if analysis should be skipped for this context."""
        block_config = self.get_block_type_config(context.block_type)
        return block_config.get('skip_analysis', False)
    
    def calculate_context_adjusted_evidence(self, base_evidence: float, context: ReferenceContext) -> float:
        """Calculate evidence score adjusted for context."""
        evidence = base_evidence
        
        # Apply content type adjustments
        content_config = self.get_content_type_config(context.content_type)
        evidence += content_config.get('evidence_increase', 0.0)
        evidence -= content_config.get('evidence_reduction', 0.0)
        evidence += content_config.get('evidence_adjustment', 0.0)
        
        # Apply block type adjustments
        block_config = self.get_block_type_config(context.block_type)
        evidence -= block_config.get('evidence_reduction', 0.0)
        
        return max(0.0, min(1.0, evidence))
    
    def reload_configuration(self):
        """Reload configuration from YAML file."""
        logger.info(f"Reloading references configuration: {self.config_name}")
        self._config.clear()
        self._pattern_cache.clear()
        self._load_configuration()
    
    @classmethod
    def reload_all_configurations(cls):
        """Reload all configuration instances."""
        for instance in cls._instances.values():
            instance.reload_configuration()

# Factory functions for easy access
def get_citation_config() -> ReferencesConfigService:
    """Get citation patterns configuration service."""
    return ReferencesConfigService('citation_patterns')

def get_geographic_config() -> ReferencesConfigService:
    """Get geographic patterns configuration service."""
    return ReferencesConfigService('geographic_patterns')

def get_product_config() -> ReferencesConfigService:
    """Get product patterns configuration service."""
    return ReferencesConfigService('product_patterns')

def get_titles_config() -> ReferencesConfigService:
    """Get professional titles configuration service."""
    return ReferencesConfigService('professional_titles')

def get_version_config() -> ReferencesConfigService:
    """Get version patterns configuration service."""
    return ReferencesConfigService('version_patterns')
