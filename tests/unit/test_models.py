"""
Unit Tests for Models Module
Tests model factory, model manager, and providers
"""

import pytest
from unittest.mock import Mock, patch

from models.factory import ModelFactory
from models.model_manager import ModelManager
from models.config import ModelConfig


@pytest.mark.unit
class TestModelFactory:
    """Test ModelFactory class"""
    
    def test_factory_initialization(self):
        """Test ModelFactory initializes"""
        factory = ModelFactory()
        assert factory is not None
    
    @patch('models.factory.ollama')
    def test_create_model(self, mock_ollama):
        """Test creating a model instance"""
        factory = ModelFactory()
        
        model = factory.create_model('llama2')
        assert model is not None
    
    def test_list_available_models(self):
        """Test listing available models"""
        factory = ModelFactory()
        
        models = factory.list_available_models()
        assert isinstance(models, list)
    
    def test_get_model_info(self):
        """Test getting model information"""
        factory = ModelFactory()
        
        info = factory.get_model_info('llama2')
        assert isinstance(info, dict)


@pytest.mark.unit
class TestModelManager:
    """Test ModelManager class"""
    
    def test_manager_initialization(self):
        """Test ModelManager initializes"""
        manager = ModelManager()
        assert manager is not None
    
    @patch('models.model_manager.ollama')
    def test_load_model(self, mock_ollama):
        """Test loading a model"""
        mock_ollama.list.return_value = {'models': [{'name': 'llama2'}]}
        
        manager = ModelManager()
        result = manager.load_model('llama2')
        
        assert result is True or result is not None
    
    def test_get_active_model(self):
        """Test getting active model"""
        manager = ModelManager()
        
        active = manager.get_active_model()
        assert active is not None or active is False
    
    def test_switch_model(self):
        """Test switching between models"""
        manager = ModelManager()
        
        result = manager.switch_model('llama2')
        assert isinstance(result, bool)


@pytest.mark.unit
class TestModelConfig:
    """Test ModelConfig class"""
    
    def test_config_initialization(self):
        """Test ModelConfig initializes"""
        config = ModelConfig()
        assert config is not None
    
    def test_get_config_value(self):
        """Test getting config values"""
        config = ModelConfig()
        
        value = config.get('model_name')
        assert value is not None
    
    def test_set_config_value(self):
        """Test setting config values"""
        config = ModelConfig()
        
        config.set('temperature', 0.7)
        assert config.get('temperature') == 0.7
    
    def test_validate_config(self):
        """Test config validation"""
        config = ModelConfig()
        
        is_valid = config.validate()
        assert isinstance(is_valid, bool)


@pytest.mark.integration
class TestModelIntegration:
    """Integration tests for model components"""
    
    @patch('models.factory.ollama')
    def test_complete_model_workflow(self, mock_ollama):
        """Test complete model usage workflow"""
        mock_ollama.list.return_value = {'models': [{'name': 'llama2'}]}
        mock_ollama.chat.return_value = {
            'message': {'content': 'Test response'}
        }
        
        # Create factory
        factory = ModelFactory()
        
        # Get manager
        manager = ModelManager()
        
        # Load model
        manager.load_model('llama2')
        
        # Use model
        model = factory.create_model('llama2')
        
        assert model is not None

