"""
Simplified Ruby client for AsciiDoc parsing.
Uses direct subprocess calls with temporary files for reliable communication.
"""

import json
import tempfile
import subprocess
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SimpleRubyClient:
    """
    Simple Ruby client for AsciiDoc parsing.
    
    Uses direct subprocess calls with temporary files for communication,
    avoiding the complexity and reliability issues of persistent servers.
    """
    
    def __init__(self):
        self.ruby_script_path = self._get_ruby_script_path()
        self.asciidoctor_available = self._check_asciidoctor_availability()
    
    def _get_ruby_script_path(self) -> str:
        """Get the path to the Ruby parsing script."""
        current_dir = Path(__file__).parent
        return str(current_dir / "ruby_scripts" / "asciidoc_parser.rb")
    
    def _check_asciidoctor_availability(self) -> bool:
        """Check if Ruby and asciidoctor are available."""
        try:
            # Check if Ruby is available
            result = subprocess.run(['ruby', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                logger.warning("Ruby is not available")
                return False
            
            # Check if asciidoctor gem is available
            result = subprocess.run(['ruby', '-e', 'require "asciidoctor"; puts "OK"'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                logger.warning("Asciidoctor gem is not available")
                return False
            
            # Check if our script exists
            if not os.path.exists(self.ruby_script_path):
                logger.warning(f"Ruby script not found: {self.ruby_script_path}")
                return False
            
            logger.info("✅ Ruby and asciidoctor are available")
            return True
            
        except Exception as e:
            logger.warning(f"Error checking Ruby/asciidoctor availability: {e}")
            return False
    
    def parse_document(self, content: str) -> Dict[str, Any]:
        """
        Parse AsciiDoc content using Ruby script.
        
        Args:
            content: Raw AsciiDoc content
            
        Returns:
            Parsed document structure
        """
        if not self.asciidoctor_available:
            return {
                'success': False,
                'error': 'Ruby or asciidoctor is not available'
            }
        
        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.adoc', delete=False) as input_file:
            input_file.write(content)
            input_file.flush()
            input_path = input_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            # Run the Ruby script
            result = subprocess.run([
                'ruby', self.ruby_script_path, input_path, output_path
            ], capture_output=True, text=True, timeout=30)
            
            # Read the result
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    result_data = json.load(f)
                
                if result.returncode != 0 and not result_data.get('success', False):
                    logger.error(f"Ruby script failed: {result.stderr}")
                    return {
                        'success': False,
                        'error': f"Ruby script error: {result.stderr or result_data.get('error', 'Unknown error')}"
                    }
                
                return result_data
            else:
                return {
                    'success': False,
                    'error': f"Ruby script failed to create output: {result.stderr}"
                }
                
        except subprocess.TimeoutExpired:
            logger.error("Ruby script timed out")
            return {
                'success': False,
                'error': 'Ruby script execution timed out'
            }
        except Exception as e:
            logger.error(f"Error running Ruby script: {e}")
            return {
                'success': False,
                'error': f"Error running Ruby script: {str(e)}"
            }
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(input_path):
                    os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except Exception as e:
                logger.warning(f"Error cleaning up temporary files: {e}")
    
    def ping(self) -> bool:
        """
        Check if the Ruby client is working.
        
        Returns:
            True if Ruby and asciidoctor are available
        """
        return self.asciidoctor_available


# Global client instance
_client_instance: Optional[SimpleRubyClient] = None


def get_client() -> SimpleRubyClient:
    """Get or create the global Ruby client instance."""
    global _client_instance
    
    if _client_instance is None:
        _client_instance = SimpleRubyClient()
    
    return _client_instance


def shutdown_client():
    """Shutdown the global client instance (no-op for SimpleRubyClient)."""
    global _client_instance
    _client_instance = None 