#!/usr/bin/env python3
"""
Model Testing Utility
Quick script to test your model configuration and connectivity.

USAGE:
======
python -m models.test_models

This script will:
1. Check configuration
2. Test provider connectivity  
3. Run a sample generation
4. Provide troubleshooting tips

RUN THIS AFTER:
===============
- Setting up new models
- Changing configuration
- Troubleshooting issues
"""

import sys
import logging
from typing import Dict, Any

# Set up logging for the test
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_configuration():
    """Test the current configuration."""
    print("=" * 60)
    print("TESTING MODEL CONFIGURATION")
    print("=" * 60)
    
    try:
        from .config import ModelConfig
        
        config = ModelConfig.get_active_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   Provider Type: {config['provider_type']}")
        print(f"   Model: {config.get('model', 'Unknown')}")
        
        if config['provider_type'] == 'ollama':
            print(f"   Ollama URL: {config.get('base_url', 'Unknown')}")
        elif config['provider_type'] == 'api':
            print(f"   API Provider: {config.get('provider_name', 'Unknown')}")
            print(f"   API URL: {config.get('base_url', 'Unknown')}")
            print(f"   Has API Key: {'Yes' if config.get('api_key') else 'No'}")
        
        # Validate configuration
        is_valid = ModelConfig.validate_config()
        if is_valid:
            print(f"✅ Configuration is valid")
        else:
            print(f"❌ Configuration is invalid")
            return False
            
        print()
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_model_manager():
    """Test the ModelManager interface."""
    print("=" * 60)
    print("TESTING MODEL MANAGER")
    print("=" * 60)
    
    try:
        from .model_manager import ModelManager
        
        manager = ModelManager()
        print(f"✅ ModelManager created successfully")
        
        # Test availability
        is_available = manager.is_available()
        if is_available:
            print(f"✅ Model is available and ready")
        else:
            print(f"❌ Model is not available")
            print(f"   Last error: {manager.get_last_error()}")
            return False
        
        # Get status
        status = manager.get_status()
        quick_info = status.get('quick_info', {})
        print(f"   Provider: {quick_info.get('provider', 'Unknown')}")
        print(f"   Model: {quick_info.get('model', 'Unknown')}")
        print(f"   Status: {quick_info.get('status', 'Unknown')}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ ModelManager test failed: {e}")
        return False

def test_health_check():
    """Run a comprehensive health check."""
    print("=" * 60)
    print("RUNNING HEALTH CHECK")
    print("=" * 60)
    
    try:
        from .model_manager import ModelManager
        
        manager = ModelManager()
        health = manager.health_check()
        
        overall = health.get('overall_health', 'unknown')
        if overall == 'healthy':
            print(f"✅ Overall health: {overall}")
        else:
            print(f"❌ Overall health: {overall}")
        
        print(f"   Config valid: {health.get('config_valid', False)}")
        print(f"   Provider available: {health.get('provider_available', False)}")
        
        recommendations = health.get('recommendations', [])
        if recommendations:
            print(f"\nRecommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print()
        return overall == 'healthy'
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_generation():
    """Test actual text generation."""
    print("=" * 60)
    print("TESTING TEXT GENERATION")
    print("=" * 60)
    
    try:
        from .model_manager import ModelManager
        
        manager = ModelManager()
        
        # Simple test
        test_prompt = "Please respond with exactly: 'Test successful'"
        print(f"Test prompt: {test_prompt}")
        print("Generating response...")
        
        result = manager.test_generation(test_prompt)
        
        if result['success']:
            print(f"✅ Generation successful!")
            print(f"   Duration: {result['duration_seconds']} seconds")
            print(f"   Response length: {result['result_length']} characters")
            print(f"   Response: {result['result'][:100]}...")
        else:
            print(f"❌ Generation failed")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            
        print()
        return result['success']
        
    except Exception as e:
        print(f"❌ Generation test failed: {e}")
        return False

def print_configuration_help():
    """Print help for configuration."""
    print("=" * 60)
    print("CONFIGURATION HELP")
    print("=" * 60)
    print()
    print("TO USE OLLAMA (Recommended for local development):")
    print("1. Install Ollama: https://ollama.com/")
    print("2. Start Ollama: ollama serve")
    print("3. Pull a model: ollama pull llama3:8b")
    print("4. In models/config.py:")
    print("   ACTIVE_PROVIDER = 'ollama'")
    print("   OLLAMA_MODEL = 'llama3:8b'")
    print()
    print("TO USE GROQ API:")
    print("1. Get API key from: https://console.groq.com/")
    print("2. Set environment variable: export API_KEY='your-groq-key'")
    print("3. In models/config.py:")
    print("   ACTIVE_PROVIDER = 'api'")
    print("   API_PROVIDER = 'groq'")
    print("   API_MODEL = 'llama3-70b-8192'")
    print()
    print("TO USE HUGGINGFACE API:")
    print("1. Get API key from: https://huggingface.co/settings/tokens")
    print("2. Set environment variable: export API_KEY='your-hf-token'")
    print("3. In models/config.py:")
    print("   ACTIVE_PROVIDER = 'api'")
    print("   API_PROVIDER = 'huggingface'")
    print("   API_MODEL = 'meta-llama/Llama-2-70b-chat-hf'")
    print()

def main():
    """Run all tests."""
    print("🤖 Model Configuration Test Suite")
    print("Testing your AI model setup...\n")
    
    # Run all tests
    tests = [
        ("Configuration", test_configuration),
        ("Model Manager", test_model_manager),
        ("Health Check", test_health_check),
        ("Text Generation", test_generation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your model setup is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. See help below:")
        print_configuration_help()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 