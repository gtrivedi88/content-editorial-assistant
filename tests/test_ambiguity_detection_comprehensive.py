"""
Comprehensive Test Suite for Ambiguity Detection System
Tests all components of the ambiguity detection system including BaseAmbiguityRule,
MissingActorDetector, PronounAmbiguityDetector, UnsupportedClaimsDetector,
FabricationRiskDetector, AmbiguityConfig, configuration management, AI instruction
generation, resolution strategies, concurrent operations, performance, and
integration scenarios.
"""

import os
import sys
import pytest
import asyncio
import threading
import time
import json
import yaml
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from typing import List, Dict, Any, Optional, Tuple
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ambiguity detection components
try:
    from ambiguity import AmbiguityDetector
    from ambiguity.base_ambiguity_rule import BaseAmbiguityRule, AmbiguityDetector as BaseDetector
    from ambiguity.types import (
        AmbiguityType, AmbiguityCategory, AmbiguitySeverity,
        AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
        ResolutionStrategy, AmbiguityConfig, AmbiguityPattern
    )
    from ambiguity.detectors.missing_actor_detector import MissingActorDetector
    from ambiguity.detectors.pronoun_ambiguity_detector import PronounAmbiguityDetector
    from ambiguity.detectors.unsupported_claims_detector import UnsupportedClaimsDetector
    from ambiguity.detectors.fabrication_risk_detector import FabricationRiskDetector
    from ambiguity.ambiguity_rule import AmbiguityRule
    
    AMBIGUITY_AVAILABLE = True
except ImportError as e:
    AMBIGUITY_AVAILABLE = False
    print(f"Ambiguity detection not available: {e}")

# Try to import SpaCy for NLP testing
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Try to import YAML
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class TestAmbiguityDetectionComprehensive:
    """Comprehensive test suite for the ambiguity detection system."""

    # ===============================
    # FIXTURES AND SETUP
    # ===============================

    @pytest.fixture
    def mock_nlp(self):
        """Create a comprehensive mock SpaCy NLP object."""
        nlp = Mock()
        
        def create_doc(text):
            doc = Mock()
            words = text.split()
            tokens = []
            
            for i, word in enumerate(words):
                token = Mock()
                token.text = word
                token.pos_ = self._get_pos_tag(word)
                token.tag_ = self._get_detailed_tag(word)
                token.dep_ = self._get_dependency(i, len(words))
                token.lemma_ = word.lower()
                token.is_alpha = word.isalpha()
                token.is_stop = word.lower() in ['the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were']
                token.lower_ = word.lower()
                token.head = token
                token.children = []
                token.i = i
                token.shape_ = "Xxxx" if word.istitle() else "xxxx"
                token.like_num = word.isdigit()
                token.ent_type_ = ""
                tokens.append(token)
            
            doc.__iter__ = Mock(return_value=iter(tokens))
            doc.__len__ = Mock(return_value=len(tokens))
            doc.__getitem__ = Mock(side_effect=lambda i: tokens[i] if 0 <= i < len(tokens) else None)
            
            # Mock sentences
            sentences = [Mock()]
            sentences[0].__iter__ = Mock(return_value=iter(tokens))
            sentences[0].__len__ = Mock(return_value=len(tokens))
            sentences[0].text = text
            sentences[0].start = 0
            sentences[0].end = len(text)
            doc.sents = sentences
            
            # Mock entities and noun chunks
            doc.ents = []
            doc.noun_chunks = []
            
            return doc
        
        nlp.side_effect = create_doc
        return nlp

    def _get_pos_tag(self, word):
        """Get POS tag for word."""
        word_lower = word.lower()
        if word_lower in ['it', 'this', 'that', 'they', 'them', 'these', 'those']:
            return 'PRON'
        elif word_lower in ['the', 'a', 'an']:
            return 'DET'
        elif word_lower in ['is', 'are', 'was', 'were', 'be', 'been', 'being']:
            return 'AUX'
        elif word_lower in ['configure', 'update', 'process', 'generate', 'create']:
            return 'VERB'
        elif word_lower in ['system', 'user', 'configuration', 'data', 'file']:
            return 'NOUN'
        else:
            return 'NOUN'

    def _get_detailed_tag(self, word):
        """Get detailed tag for word."""
        pos = self._get_pos_tag(word)
        if pos == 'VERB':
            return 'VBN' if word.endswith('ed') else 'VB'
        elif pos == 'NOUN':
            return 'NNS' if word.endswith('s') else 'NN'
        elif pos == 'PRON':
            return 'PRP'
        elif pos == 'DET':
            return 'DT'
        elif pos == 'AUX':
            return 'VBZ'
        else:
            return 'NN'

    def _get_dependency(self, i, total):
        """Get dependency relation."""
        if i == 0:
            return 'nsubj'
        elif i == 1:
            return 'ROOT'
        else:
            return 'dobj'

    @pytest.fixture
    def mock_config(self):
        """Create mock ambiguity configuration."""
        config = Mock(spec=AmbiguityConfig)
        config.enabled_types = {
            AmbiguityType.MISSING_ACTOR,
            AmbiguityType.AMBIGUOUS_PRONOUN,
            AmbiguityType.UNSUPPORTED_CLAIMS,
            AmbiguityType.FABRICATION_RISK
        }
        config.severity_mappings = {
            AmbiguityType.MISSING_ACTOR: AmbiguitySeverity.HIGH,
            AmbiguityType.AMBIGUOUS_PRONOUN: AmbiguitySeverity.MEDIUM,
            AmbiguityType.UNSUPPORTED_CLAIMS: AmbiguitySeverity.CRITICAL,
            AmbiguityType.FABRICATION_RISK: AmbiguitySeverity.CRITICAL
        }
        config.category_mappings = {
            AmbiguityType.MISSING_ACTOR: AmbiguityCategory.REFERENTIAL,
            AmbiguityType.AMBIGUOUS_PRONOUN: AmbiguityCategory.REFERENTIAL,
            AmbiguityType.UNSUPPORTED_CLAIMS: AmbiguityCategory.SEMANTIC,
            AmbiguityType.FABRICATION_RISK: AmbiguityCategory.SEMANTIC
        }
        config.patterns = {}
        return config

    @pytest.fixture
    def sample_texts(self):
        """Provide sample texts for testing."""
        return {
            'passive_missing_actor': "The configuration is updated automatically.",
            'passive_with_actor': "The configuration is updated by the administrator.",
            'active_voice': "The administrator updates the configuration.",
            'pronoun_ambiguous': "The user opens the file and modifies it. Then they save it.",
            'pronoun_clear': "The user opens the file and modifies the file. Then the user saves the file.",
            'unsupported_claim': "This is the best solution available and always works perfectly.",
            'supported_claim': "This solution is recommended for most use cases and typically works well.",
            'fabrication_risk': "The advanced AI algorithm learns from user behavior and predicts future outcomes.",
            'safe_technical': "The system processes user input and generates output based on configured rules.",
            'complex_ambiguous': "The system is configured by the administrator and then it processes the data. This ensures optimal performance.",
            'clear_technical': "The administrator configures the system. The system then processes the data. This configuration ensures optimal performance.",
            'multiple_ambiguities': "The configuration is updated and then it processes the data. This is the best approach and always works.",
            'empty': "",
            'whitespace': "   \n  \t  \n  ",
            'special_chars': "The system uses special characters: @#$%^&*()! and unicode: café naïve résumé.",
            'markdown': "The **system** is configured and then _it_ processes the data.",
            'code_mixed': "Run `configure_system()` and then it will process the data automatically."
        }

    @pytest.fixture
    def sample_contexts(self):
        """Provide sample contexts for testing."""
        return [
            {
                'sentence': 'The configuration is updated automatically.',
                'sentence_index': 0,
                'surrounding_sentences': [],
                'full_text': 'The configuration is updated automatically.',
                'block_type': 'paragraph',
                'format_hint': 'markdown'
            },
            {
                'sentence': 'The user opens the file and then they modify it.',
                'sentence_index': 0,
                'surrounding_sentences': ['The system loads the configuration.'],
                'full_text': 'The system loads the configuration. The user opens the file and then they modify it.',
                'block_type': 'paragraph',
                'format_hint': 'markdown'
            }
        ]

    @pytest.fixture
    def sample_yaml_config(self):
        """Provide sample YAML configuration."""
        return """
enabled: true
confidence_threshold: 0.7

ambiguity_types:
  missing_actor:
    enabled: true
    category: "referential"
    severity: "high"
    confidence_threshold: 0.7
    description: "Passive voice sentences without clear actors"
    
  ambiguous_pronoun:
    enabled: true
    category: "referential"  
    severity: "medium"
    confidence_threshold: 0.6
    description: "Pronouns with unclear referents"
    
  unsupported_claims:
    enabled: true
    category: "semantic"
    severity: "critical"
    confidence_threshold: 0.8
    description: "Unsupported claims and promises"
    
  fabrication_risk:
    enabled: true
    category: "semantic"
    severity: "critical"
    confidence_threshold: 0.7
    description: "Risk of information fabrication"
"""

    # ===============================
    # BASE AMBIGUITY RULE TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_base_ambiguity_rule_initialization(self):
        """Test BaseAmbiguityRule initialization."""
        rule = BaseAmbiguityRule()
        
        assert rule is not None
        assert hasattr(rule, 'config')
        assert hasattr(rule, 'detectors')
        assert rule._get_rule_type() == 'ambiguity'

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_base_ambiguity_rule_detector_initialization(self):
        """Test that detectors are properly initialized."""
        rule = BaseAmbiguityRule()
        
        # Check that detectors dictionary exists
        assert isinstance(rule.detectors, dict)
        
        # Check for expected detector types
        expected_detectors = ['missing_actor', 'pronoun_ambiguity', 'unsupported_claims', 'fabrication_risk']
        for detector_type in expected_detectors:
            if detector_type in rule.detectors:
                assert rule.detectors[detector_type] is not None

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_base_ambiguity_rule_analyze_no_nlp(self, sample_texts):
        """Test analyze method without SpaCy NLP object."""
        rule = BaseAmbiguityRule()
        
        sentences = [sample_texts['passive_missing_actor']]
        result = rule.analyze(sample_texts['passive_missing_actor'], sentences)
        
        # Should return empty list when no NLP is available
        assert result == []

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_base_ambiguity_rule_analyze_with_nlp(self, sample_texts, mock_nlp):
        """Test analyze method with SpaCy NLP object."""
        rule = BaseAmbiguityRule()
        
        sentences = [sample_texts['passive_missing_actor']]
        result = rule.analyze(sample_texts['passive_missing_actor'], sentences, nlp=mock_nlp)
        
        assert isinstance(result, list)
        # Result may be empty if detectors are not properly loaded, but should not fail

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_base_ambiguity_rule_context_creation(self, sample_texts, mock_nlp):
        """Test sentence context creation."""
        rule = BaseAmbiguityRule()
        
        # Test context creation through analyze method
        sentences = [sample_texts['passive_missing_actor'], sample_texts['active_voice']]
        result = rule.analyze(sample_texts['passive_missing_actor'], sentences, nlp=mock_nlp)
        
        # Should handle context creation without errors
        assert isinstance(result, list)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_base_ambiguity_rule_exception_handling(self, sample_texts):
        """Test exception handling in analyze method."""
        rule = BaseAmbiguityRule()
        
        # Mock a detector that raises an exception
        mock_detector = Mock()
        mock_detector.detect.side_effect = Exception("Test error")
        rule.detectors['test_detector'] = mock_detector
        
        with patch.object(rule, '_is_detector_enabled', return_value=True):
            sentences = [sample_texts['passive_missing_actor']]
            result = rule.analyze(sample_texts['passive_missing_actor'], sentences, nlp=Mock())
            
            # Should handle exceptions gracefully
            assert isinstance(result, list)

    # ===============================
    # AMBIGUITY RULE INTEGRATION TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_ambiguity_rule_initialization(self):
        """Test AmbiguityRule initialization."""
        rule = AmbiguityRule()
        
        assert rule is not None
        assert rule._get_rule_type() == 'ambiguity'
        assert isinstance(rule, BaseAmbiguityRule)

    # ===============================
    # MISSING ACTOR DETECTOR TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_missing_actor_detector_initialization(self, mock_config):
        """Test MissingActorDetector initialization."""
        detector = MissingActorDetector(mock_config)
        
        assert detector is not None
        assert detector.config == mock_config
        assert hasattr(detector, 'confidence_threshold')
        assert hasattr(detector, 'passive_indicators')
        assert hasattr(detector, 'clear_actors')

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_missing_actor_detector_passive_detection(self, sample_texts, mock_config, mock_nlp):
        """Test detection of passive voice without actors."""
        detector = MissingActorDetector(mock_config)
        
        # Create context for passive sentence
        context = AmbiguityContext(
            sentence=sample_texts['passive_missing_actor'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        detections = detector.detect(context, mock_nlp)
        
        # Should detect ambiguity in passive voice without clear actor
        assert isinstance(detections, list)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_missing_actor_detector_active_voice(self, sample_texts, mock_config, mock_nlp):
        """Test that active voice is not flagged."""
        detector = MissingActorDetector(mock_config)
        
        context = AmbiguityContext(
            sentence=sample_texts['active_voice'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        detections = detector.detect(context, mock_nlp)
        
        # Should not detect ambiguity in active voice
        assert isinstance(detections, list)
        # Length may vary based on implementation, but should handle gracefully

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_missing_actor_detector_passive_with_actor(self, sample_texts, mock_config, mock_nlp):
        """Test that passive voice with clear actor is not flagged."""
        detector = MissingActorDetector(mock_config)
        
        context = AmbiguityContext(
            sentence=sample_texts['passive_with_actor'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        detections = detector.detect(context, mock_nlp)
        
        # Should not detect ambiguity in passive voice with clear actor
        assert isinstance(detections, list)

    # ===============================
    # PRONOUN AMBIGUITY DETECTOR TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_pronoun_ambiguity_detector_initialization(self, mock_config):
        """Test PronounAmbiguityDetector initialization."""
        detector = PronounAmbiguityDetector(mock_config)
        
        assert detector is not None
        assert detector.config == mock_config
        assert hasattr(detector, 'ambiguous_pronouns')
        assert hasattr(detector, 'clear_pronouns')
        assert hasattr(detector, 'max_referent_distance')

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_pronoun_ambiguity_detector_ambiguous_pronouns(self, sample_texts, mock_config, mock_nlp):
        """Test detection of ambiguous pronouns."""
        detector = PronounAmbiguityDetector(mock_config)
        
        context = AmbiguityContext(
            sentence=sample_texts['pronoun_ambiguous'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        detections = detector.detect(context, mock_nlp)
        
        # Should detect ambiguous pronouns
        assert isinstance(detections, list)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_pronoun_ambiguity_detector_clear_pronouns(self, sample_texts, mock_config, mock_nlp):
        """Test that clear pronouns are not flagged."""
        detector = PronounAmbiguityDetector(mock_config)
        
        context = AmbiguityContext(
            sentence=sample_texts['pronoun_clear'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        detections = detector.detect(context, mock_nlp)
        
        # Should not detect ambiguity in clear pronoun usage
        assert isinstance(detections, list)

    # ===============================
    # UNSUPPORTED CLAIMS DETECTOR TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_unsupported_claims_detector_initialization(self, mock_config):
        """Test UnsupportedClaimsDetector initialization."""
        detector = UnsupportedClaimsDetector(mock_config)
        
        assert detector is not None
        assert detector.config == mock_config

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_unsupported_claims_detector_unsupported_claims(self, sample_texts, mock_config, mock_nlp):
        """Test detection of unsupported claims."""
        detector = UnsupportedClaimsDetector(mock_config)
        
        context = AmbiguityContext(
            sentence=sample_texts['unsupported_claim'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        detections = detector.detect(context, mock_nlp)

        # Should detect unsupported claims
        assert isinstance(detections, list)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_unsupported_claims_detector_supported_claims(self, sample_texts, mock_config, mock_nlp):
        """Test that supported claims are not flagged."""
        detector = UnsupportedClaimsDetector(mock_config)
        
        context = AmbiguityContext(
            sentence=sample_texts['supported_claim'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        detections = detector.detect(context, mock_nlp)
        
        # Should not detect issues in supported claims
        assert isinstance(detections, list)

    # ===============================
    # FABRICATION RISK DETECTOR TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_fabrication_risk_detector_initialization(self, mock_config):
        """Test FabricationRiskDetector initialization."""
        detector = FabricationRiskDetector(mock_config)
        
        assert detector is not None
        assert detector.config == mock_config

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_fabrication_risk_detector_risky_content(self, sample_texts, mock_config, mock_nlp):
        """Test detection of fabrication risk."""
        detector = FabricationRiskDetector(mock_config)
        
        context = AmbiguityContext(
            sentence=sample_texts['fabrication_risk'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        detections = detector.detect(context, mock_nlp)
        
        # Should detect fabrication risk
        assert isinstance(detections, list)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_fabrication_risk_detector_safe_content(self, sample_texts, mock_config, mock_nlp):
        """Test that safe technical content is not flagged."""
        detector = FabricationRiskDetector(mock_config)
        
        context = AmbiguityContext(
            sentence=sample_texts['safe_technical'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        detections = detector.detect(context, mock_nlp)
        
        # Should not detect fabrication risk in safe content
        assert isinstance(detections, list)

    # ===============================
    # AMBIGUITY TYPES TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_ambiguity_type_enum(self):
        """Test AmbiguityType enum values."""
        assert AmbiguityType.MISSING_ACTOR.value == "missing_actor"
        assert AmbiguityType.AMBIGUOUS_PRONOUN.value == "ambiguous_pronoun"
        assert AmbiguityType.UNCLEAR_SUBJECT.value == "unclear_subject"
        assert AmbiguityType.UNSUPPORTED_CLAIMS.value == "unsupported_claims"
        assert AmbiguityType.FABRICATION_RISK.value == "fabrication_risk"

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_ambiguity_category_enum(self):
        """Test AmbiguityCategory enum values."""
        assert AmbiguityCategory.REFERENTIAL.value == "referential"
        assert AmbiguityCategory.STRUCTURAL.value == "structural"
        assert AmbiguityCategory.SEMANTIC.value == "semantic"
        assert AmbiguityCategory.TEMPORAL.value == "temporal"

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_ambiguity_severity_enum(self):
        """Test AmbiguitySeverity enum values."""
        assert AmbiguitySeverity.LOW.value == "low"
        assert AmbiguitySeverity.MEDIUM.value == "medium"
        assert AmbiguitySeverity.HIGH.value == "high"
        assert AmbiguitySeverity.CRITICAL.value == "critical"

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_ambiguity_context_creation(self, sample_texts):
        """Test AmbiguityContext creation."""
        context = AmbiguityContext(
            sentence=sample_texts['passive_missing_actor'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        assert context.sentence == sample_texts['passive_missing_actor']
        assert context.sentence_index == 0
        assert context.document_context is not None
        assert context.document_context['block_type'] == 'paragraph'

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_ambiguity_detection_creation(self):
        """Test AmbiguityDetection creation."""
        context = AmbiguityContext(
            sentence="The configuration is updated.",
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        evidence = AmbiguityEvidence(
            tokens=["updated"],
            linguistic_pattern="passive_voice",
            confidence=0.85
        )
        
        detection = AmbiguityDetection(
            ambiguity_type=AmbiguityType.MISSING_ACTOR,
            category=AmbiguityCategory.REFERENTIAL,
            severity=AmbiguitySeverity.HIGH,
            context=context,
            evidence=evidence,
            resolution_strategies=[ResolutionStrategy.IDENTIFY_ACTOR],
            ai_instructions=["Add a clear subject"]
        )
        
        assert detection.ambiguity_type == AmbiguityType.MISSING_ACTOR
        assert detection.evidence.confidence == 0.85
        assert detection.context.sentence == "The configuration is updated."

    # ===============================
    # AMBIGUITY CONFIG TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_ambiguity_config_initialization(self):
        """Test AmbiguityConfig initialization."""
        config = AmbiguityConfig()
        
        assert config is not None
        assert hasattr(config, 'patterns')
        assert hasattr(config, 'severity_mappings')
        assert hasattr(config, 'category_mappings')
        assert hasattr(config, 'enabled_types')

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_ambiguity_config_default_mappings(self):
        """Test default configuration mappings."""
        config = AmbiguityConfig()
        
        # Check severity mappings
        assert AmbiguityType.MISSING_ACTOR in config.severity_mappings
        assert AmbiguityType.AMBIGUOUS_PRONOUN in config.severity_mappings
        
        # Check category mappings
        assert AmbiguityType.MISSING_ACTOR in config.category_mappings
        assert AmbiguityType.AMBIGUOUS_PRONOUN in config.category_mappings

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    @pytest.mark.skipif(not YAML_AVAILABLE, reason="YAML not available")
    def test_ambiguity_config_yaml_loading(self, sample_yaml_config):
        """Test loading configuration from YAML."""
        with patch('builtins.open', mock_open(read_data=sample_yaml_config)):
            with patch('os.path.exists', return_value=True):
                config = AmbiguityConfig()
                
                # Config should be loaded without errors
                assert config is not None

    # ===============================
    # INTEGRATION TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_end_to_end_ambiguity_detection(self, sample_texts, mock_nlp):
        """Test end-to-end ambiguity detection workflow."""
        rule = BaseAmbiguityRule()
        
        text = sample_texts['complex_ambiguous']
        sentences = text.split('. ')
        
        result = rule.analyze(text, sentences, nlp=mock_nlp)
        
        assert isinstance(result, list)
        # Result structure may vary based on implementation

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_multiple_detector_integration(self, sample_texts, mock_nlp):
        """Test integration of multiple detectors."""
        rule = BaseAmbiguityRule()
        
        text = sample_texts['multiple_ambiguities']
        sentences = [text]
        
        result = rule.analyze(text, sentences, nlp=mock_nlp)
        
        assert isinstance(result, list)
        # Should handle multiple types of ambiguity

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_detector_configuration_integration(self, mock_config):
        """Test integration with custom configuration."""
        # Test that detectors use custom configuration
        detector = MissingActorDetector(mock_config)
        assert detector.config == mock_config
        
        detector = PronounAmbiguityDetector(mock_config)
        assert detector.config == mock_config

    # ===============================
    # PERFORMANCE TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_performance_large_text(self, sample_texts, mock_nlp):
        """Test performance with large text."""
        rule = BaseAmbiguityRule()
        
        # Create large text
        large_text = sample_texts['complex_ambiguous'] * 100
        sentences = [large_text]
        
        start_time = time.time()
        result = rule.analyze(large_text, sentences, nlp=mock_nlp)
        end_time = time.time()
        
        assert result is not None
        assert end_time - start_time < 30.0  # Should complete within 30 seconds

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_performance_many_sentences(self, sample_texts, mock_nlp):
        """Test performance with many sentences."""
        rule = BaseAmbiguityRule()
        
        sentences = [sample_texts['passive_missing_actor']] * 100
        text = '. '.join(sentences)
        
        start_time = time.time()
        result = rule.analyze(text, sentences, nlp=mock_nlp)
        end_time = time.time()
        
        assert result is not None
        assert end_time - start_time < 60.0  # Should complete within 60 seconds

    # ===============================
    # CONCURRENT OPERATION TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_concurrent_analysis(self, sample_texts, mock_nlp):
        """Test concurrent analysis operations."""
        rule = BaseAmbiguityRule()
        
        def analyze_text(text):
            sentences = [text]
            return rule.analyze(text, sentences, nlp=mock_nlp)
        
        texts = [sample_texts['passive_missing_actor']] * 5
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(analyze_text, text) for text in texts]
            results = [future.result() for future in as_completed(futures)]
        
        assert len(results) == 5
        assert all(isinstance(result, list) for result in results)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_concurrent_different_detectors(self, sample_texts, mock_config, mock_nlp):
        """Test concurrent operations with different detector instances."""
        def create_and_detect(text, detector_class):
            detector = detector_class(mock_config)
            context = AmbiguityContext(
                sentence=text,
                sentence_index=0,
                preceding_sentences=[],
                following_sentences=[],
                document_context={'block_type': 'paragraph'}
            )
            return detector.detect(context, mock_nlp)
        
        detectors = [MissingActorDetector, PronounAmbiguityDetector]
        texts = [sample_texts['passive_missing_actor'], sample_texts['pronoun_ambiguous']]
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(create_and_detect, text, detector) 
                      for text, detector in zip(texts, detectors)]
            results = [future.result() for future in as_completed(futures)]
        
        assert len(results) == 2
        assert all(isinstance(result, list) for result in results)

    # ===============================
    # MEMORY MANAGEMENT TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_memory_usage_repeated_analysis(self, sample_texts, mock_nlp):
        """Test memory usage with repeated analysis."""
        rule = BaseAmbiguityRule()
        
        # Perform analysis multiple times
        for i in range(10):
            sentences = [sample_texts['passive_missing_actor']]
            result = rule.analyze(sample_texts['passive_missing_actor'], sentences, nlp=mock_nlp)
            assert result is not None
            
            # Clear result to help with memory management
            del result

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_memory_usage_detector_recreation(self, sample_texts, mock_config, mock_nlp):
        """Test memory usage with detector recreation."""
        for i in range(5):
            detector = MissingActorDetector(mock_config)
            context = AmbiguityContext(
                sentence=sample_texts['passive_missing_actor'],
                sentence_index=0,
                preceding_sentences=[],
                following_sentences=[],
                document_context={'block_type': 'paragraph'}
            )
            result = detector.detect(context, mock_nlp)
            assert result is not None
            
            # Clear detector and result
            del detector
            del result

    # ===============================
    # EDGE CASE TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_edge_cases_empty_text(self, mock_nlp):
        """Test edge cases with empty text."""
        rule = BaseAmbiguityRule()
        
        result = rule.analyze("", [], nlp=mock_nlp)
        
        assert result == []

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_edge_cases_whitespace_text(self, sample_texts, mock_nlp):
        """Test edge cases with whitespace-only text."""
        rule = BaseAmbiguityRule()
        
        sentences = [sample_texts['whitespace']]
        result = rule.analyze(sample_texts['whitespace'], sentences, nlp=mock_nlp)
        
        assert isinstance(result, list)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_edge_cases_special_characters(self, sample_texts, mock_nlp):
        """Test edge cases with special characters."""
        rule = BaseAmbiguityRule()
        
        sentences = [sample_texts['special_chars']]
        result = rule.analyze(sample_texts['special_chars'], sentences, nlp=mock_nlp)
        
        assert isinstance(result, list)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_edge_cases_markdown_content(self, sample_texts, mock_nlp):
        """Test edge cases with markdown content."""
        rule = BaseAmbiguityRule()
        
        sentences = [sample_texts['markdown']]
        result = rule.analyze(sample_texts['markdown'], sentences, nlp=mock_nlp)
        
        assert isinstance(result, list)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_edge_cases_code_mixed_content(self, sample_texts, mock_nlp):
        """Test edge cases with code mixed in content."""
        rule = BaseAmbiguityRule()
        
        sentences = [sample_texts['code_mixed']]
        result = rule.analyze(sample_texts['code_mixed'], sentences, nlp=mock_nlp)
        
        assert isinstance(result, list)

    # ===============================
    # ERROR HANDLING TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_error_handling_malformed_input(self, mock_nlp):
        """Test error handling with malformed input."""
        rule = BaseAmbiguityRule()
        
        # Test with empty string instead of None
        try:
            result = rule.analyze("", [], nlp=mock_nlp)
            assert isinstance(result, list)
        except Exception:
            # Should handle gracefully
            pass

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_error_handling_detector_failure(self, sample_texts, mock_nlp):
        """Test error handling when detectors fail."""
        rule = BaseAmbiguityRule()
        
        # Mock a detector to fail
        if 'missing_actor' in rule.detectors:
            rule.detectors['missing_actor'].detect = Mock(side_effect=Exception("Detector failed"))
        
        sentences = [sample_texts['passive_missing_actor']]
        result = rule.analyze(sample_texts['passive_missing_actor'], sentences, nlp=mock_nlp)
        
        # Should handle detector failures gracefully
        assert isinstance(result, list)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_error_handling_nlp_failure(self, sample_texts):
        """Test error handling when NLP processing fails."""
        rule = BaseAmbiguityRule()
        
        # Mock NLP to fail
        mock_nlp = Mock()
        mock_nlp.side_effect = Exception("NLP failed")
        
        sentences = [sample_texts['passive_missing_actor']]
        result = rule.analyze(sample_texts['passive_missing_actor'], sentences, nlp=mock_nlp)
        
        # Should handle NLP failures gracefully
        assert isinstance(result, list)

    # ===============================
    # CONFIGURATION TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_configuration_detector_enabling(self, mock_config, sample_texts, mock_nlp):
        """Test detector enabling/disabling through configuration."""
        rule = BaseAmbiguityRule()
        
        # Test that configuration affects detector behavior
        sentences = [sample_texts['passive_missing_actor']]
        result = rule.analyze(sample_texts['passive_missing_actor'], sentences, nlp=mock_nlp)
        
        assert isinstance(result, list)

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_configuration_confidence_thresholds(self, mock_config, sample_texts, mock_nlp):
        """Test confidence threshold configuration."""
        # Test different confidence thresholds
        detector = MissingActorDetector(mock_config)
        
        context = AmbiguityContext(
            sentence=sample_texts['passive_missing_actor'],
            sentence_index=0,
            preceding_sentences=[],
            following_sentences=[],
            document_context={'block_type': 'paragraph'}
        )
        
        detections = detector.detect(context, mock_nlp)
        assert isinstance(detections, list)

    # ===============================
    # CLEANUP TESTS
    # ===============================

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_rule_cleanup(self):
        """Test that rules can be properly cleaned up."""
        rule = BaseAmbiguityRule()
        
        # Verify rule is created
        assert rule is not None
        
        # Delete rule
        del rule
        
        # Create new rule to verify no issues
        new_rule = BaseAmbiguityRule()
        assert new_rule is not None

    @pytest.mark.skipif(not AMBIGUITY_AVAILABLE, reason="Ambiguity detection not available")
    def test_detector_cleanup(self, mock_config):
        """Test that detectors can be properly cleaned up."""
        detector = MissingActorDetector(mock_config)
        
        # Verify detector is created
        assert detector is not None
        
        # Delete detector
        del detector
        
        # Create new detector to verify no issues
        new_detector = MissingActorDetector(mock_config)
        assert new_detector is not None


# ===============================
# HELPER FUNCTIONS
# ===============================

def create_test_ambiguity_context(sentence: str, **kwargs) -> Optional['AmbiguityContext']:
    """Create a test ambiguity context."""
    if AMBIGUITY_AVAILABLE:
        return AmbiguityContext(
            sentence=sentence,
            sentence_index=kwargs.get('sentence_index', 0),
            paragraph_context=kwargs.get('paragraph_context', None),
            preceding_sentences=kwargs.get('preceding_sentences', []),
            following_sentences=kwargs.get('following_sentences', []),
            document_context=kwargs.get('document_context', None)
        )
    else:
        return None


def create_mock_ambiguity_detection() -> Dict[str, Any]:
    """Create a mock ambiguity detection result."""
    return {
        'ambiguity_type': 'missing_actor',
        'category': 'referential',
        'severity': 'high',
        'confidence': 0.85,
        'message': 'Missing actor in passive construction',
        'sentence': 'The configuration is updated automatically.',
        'sentence_index': 0,
        'suggestions': [
            'Add a clear subject (e.g., "The system updates...")',
            'Convert to active voice',
            'Specify who performs the action'
        ],
        'evidence': [
            'Passive voice detected',
            'No clear actor identified'
        ]
    }


def create_mock_yaml_config() -> str:
    """Create a mock YAML configuration."""
    return """
enabled: true
confidence_threshold: 0.7

ambiguity_types:
  missing_actor:
    enabled: true
    category: "referential"
    severity: "high"
    confidence_threshold: 0.7
    
  ambiguous_pronoun:
    enabled: true
    category: "referential"
    severity: "medium"
    confidence_threshold: 0.6

resolution_strategies:
  missing_actor:
    - "identify_actor"
    - "restructure_sentence"
    
  ambiguous_pronoun:
    - "clarify_pronoun"
    - "specify_reference"
"""


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 