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
    def __init__(self):
        self.ruby_script_path = self._get_ruby_script_path()
        self.asciidoctor_available = self._check_asciidoctor_availability()

    def _get_ruby_script_path(self) -> str:
        current_dir = Path(__file__).parent
        return str(current_dir / "ruby_scripts" / "asciidoc_parser.rb")

    def _check_asciidoctor_availability(self) -> bool:
        try:
            subprocess.run(['ruby', '-e', 'require "asciidoctor"'], check=True, capture_output=True, timeout=5)
            logger.info("✅ Ruby and asciidoctor are available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Ruby/asciidoctor check failed: {e}")
            return False

    # This method is now correctly named 'run' and accepts 'filename'
    def run(self, content: str, filename: str = "") -> Dict[str, Any]:
        """
        Parse AsciiDoc content by running the Ruby script.
        """
        if not self.asciidoctor_available:
            return {'success': False, 'error': 'Ruby or asciidoctor is not available'}

        input_path, output_path = None, None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.adoc', delete=False) as input_file:
                input_file.write(content)
                input_path = input_file.name

            with tempfile.NamedTemporaryFile(mode='r', encoding='utf-8', suffix='.json', delete=False) as output_file:
                output_path = output_file.name

            cmd = ['ruby', self.ruby_script_path, input_path, output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')

            if result.returncode != 0:
                error_msg = result.stderr or "Ruby parser failed with no stderr"
                return {'success': False, 'error': f"Ruby script error: {error_msg}"}

            with open(output_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Ruby script execution timed out'}
        except Exception as e:
            return {'success': False, 'error': f"Error running Ruby script: {str(e)}"}
        finally:
            if input_path and os.path.exists(input_path): os.unlink(input_path)
            if output_path and os.path.exists(output_path): os.unlink(output_path)

    def ping(self) -> bool:
        return self.asciidoctor_available

# Global client instance
_client_instance: Optional[SimpleRubyClient] = None

def get_client() -> SimpleRubyClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = SimpleRubyClient()
    return _client_instance