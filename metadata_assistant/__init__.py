"""
Metadata Assistant Module

AI-powered metadata generation that integrates with the style-guide-ai system.
Provides semantic content analysis and metadata extraction with production-ready reliability.

Key Components:
- MetadataAssistant: Main orchestrator class
- Extractors: Title, keyword, description, and taxonomy extraction algorithms
- Configuration: Taxonomy definitions and system settings
- Database integration: Metadata storage and feedback collection

Usage:
    from metadata_assistant import MetadataAssistant
    
    assistant = MetadataAssistant()
    result = assistant.generate_metadata(content, spacy_doc, structural_blocks)
"""

from .core import MetadataAssistant
from .config import MetadataConfig

__version__ = '1.0.0'
__all__ = ['MetadataAssistant', 'MetadataConfig']
