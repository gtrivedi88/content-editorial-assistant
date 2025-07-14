"""
Ruby server for persistent asciidoctor parsing.
Maintains a long-running Ruby process to avoid subprocess overhead.
"""

import json
import subprocess
import tempfile
import threading
import time
import signal
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RubyAsciidoctorServer:
    """
    Persistent Ruby server for asciidoctor parsing.
    
    This server maintains a long-running Ruby process to avoid the overhead
    of creating new processes for each document parse operation.
    """
    
    def __init__(self, timeout: int = 10):  # Reduced timeout
        self.timeout = timeout
        self.process: Optional[subprocess.Popen] = None
        self.lock = threading.Lock()
        self._failed_attempts = 0
        self._max_attempts = 3
        self._last_failure_time = 0
        self._failure_cooldown = 30  # 30 seconds before retry
        self._start_server()
    
    def _check_ruby_availability(self) -> bool:
        """Check if Ruby and asciidoctor are available."""
        try:
            # Check Ruby
            result = subprocess.run(['ruby', '--version'], 
                                    capture_output=True, 
                                    timeout=5, 
                                    text=True)
            if result.returncode != 0:
                return False
            
            # Check asciidoctor gem
            result = subprocess.run(['ruby', '-e', 'require "asciidoctor"'], 
                                    capture_output=True, 
                                    timeout=5, 
                                    text=True)
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def _start_server(self):
        """Start the Ruby server process with proper error handling."""
        # Check if we've failed too many times recently
        if (self._failed_attempts >= self._max_attempts and 
            time.time() - self._last_failure_time < self._failure_cooldown):
            logger.warning(f"Ruby server failed {self._failed_attempts} times, cooling down")
            return
        
        # Check if Ruby and asciidoctor are available
        if not self._check_ruby_availability():
            logger.warning("Ruby or asciidoctor not available, skipping server start")
            self._failed_attempts = self._max_attempts  # Prevent further attempts
            return
        
        try:
            # Create the Ruby server script with timeout handling
            ruby_server_script = '''
require 'asciidoctor'
require 'json'
require 'timeout'

# Set up signal handling for graceful shutdown
Signal.trap("TERM") { exit(0) }
Signal.trap("INT") { exit(0) }

def preprocess_content_for_lists(content)
  # Split content into lines
  lines = content.split('\n')
  processed_lines = []
  
  i = 0
  while i < lines.length
    current_line = lines[i]
    processed_lines << current_line
    
    # Check if this line is a paragraph (non-empty, not a special block)
    if i < lines.length - 1 && !current_line.strip.empty?
      next_line = lines[i + 1]
      
      # Check if current line is not already a special block or list item
      unless current_line.strip.match(/^(=+\\s|\\.+\\s|\\*+\\s|\\[.*\\]|----|----|^\\s*$|:.*:)/)
        # Check if next line is a list item (starts with *, -, numbers, or dots)
        if next_line.strip.match(/^(\\*+\\s+|-+\\s+|\\d+\\.\\s+|\\.+\\s+)/)
          # Insert a blank line to separate paragraph from list
          processed_lines << ''
        end
      end
    end
    
    i += 1
  end
  
  processed_lines.join('\n')
end

def parse_document(content)
  # Add timeout for processing
  Timeout::timeout(30) do  # 30 second timeout for parsing
    # Preprocess content to handle paragraph-list separation
    processed_content = preprocess_content_for_lists(content)
    
    # Parse the document with source mapping and full block parsing
    doc = Asciidoctor.load(processed_content, 
      sourcemap: true, 
      safe: :unsafe,
      parse_header_only: false,
      standalone: false)
    
    # Extract block information recursively
    def extract_block_info(block, level = 0)
      # Extract content preferring plain text over HTML - handle all block types dynamically
      content = ''
      
      # Priority order for content extraction based on block context
      case block.context
      when :list_item
        # For list items, use the text field which contains the plain content
        content = block.respond_to?(:text) && !block.text.nil? ? block.text.to_s : ''
      when :paragraph, :sidebar, :example, :quote, :verse, :literal, :admonition
        # For content blocks, prefer source lines if available
        if block.respond_to?(:lines) && block.lines && !block.lines.empty?
          content = block.lines.join('\n')
        elsif block.respond_to?(:source) && !block.source.nil?
          content = block.source.to_s
        elsif !block.content.nil?
          content = block.content.to_s
        end
      when :listing
        # For code blocks, preserve the source exactly
        if block.respond_to?(:source) && !block.source.nil?
          content = block.source.to_s
        elsif block.respond_to?(:lines) && block.lines
          content = block.lines.join('\n')
        end
      else
        # For any other block type, try multiple extraction methods
        if block.respond_to?(:source) && !block.source.nil?
          content = block.source.to_s
        elsif block.respond_to?(:lines) && block.lines && !block.lines.empty?
          content = block.lines.join('\\n')
        elsif !block.content.nil?
          content = block.content.to_s
        elsif block.respond_to?(:text) && !block.text.nil?
          content = block.text.to_s
        end
      end
      
      # Clean up HTML tags if present (but preserve structure for code blocks)
      unless [:listing, :literal].include?(block.context)
        if content.include?('<') && content.include?('>')
          content = content.gsub(/<[^>]+>/, '').gsub(/\\s+/, ' ').strip
        end
      end
      
      # Determine the correct level for this block
      block_level = level  # Default to nesting depth
      
      # For headings and sections, use the actual heading level instead of nesting depth
      if block.context == :section
        # For sections, use the section level (1, 2, 3, etc.)
        block_level = block.level if block.respond_to?(:level)
      elsif block.context == :heading
        # For heading blocks, extract level from attributes or style
        if block.respond_to?(:level)
          block_level = block.level
        elsif block.attributes && block.attributes['level']
          block_level = block.attributes['level'].to_i
        end
      end

      block_info = {
        'context' => block.context.to_s,
        'content_model' => block.content_model.to_s,
        'content' => content,
        'level' => block_level,
        'nesting_depth' => level,  # Keep track of nesting depth separately
        'style' => block.style,
        'title' => block.title,
        'id' => block.id,
        'attributes' => block.attributes.to_h,
        'raw_content' => content  # Keep raw content for reference
      }
      
      # Get source location if available
      if block.source_location
        block_info['source_location'] = {
          'file' => block.source_location.file,
          'lineno' => block.source_location.lineno,
          'path' => block.source_location.path
        }
      end
      
      # Get lines for content blocks
      if block.respond_to?(:lines) && block.lines
        block_info['lines'] = block.lines
      elsif block.respond_to?(:source) && block.source
        if block.source.is_a?(Array)
          block_info['lines'] = block.source
        else
          block_info['lines'] = [block.source.to_s]
        end
      end
      
      # Extract children blocks
      children = []
      if block.respond_to?(:blocks) && block.blocks
        block.blocks.each do |child_block|
          children << extract_block_info(child_block, level + 1)
        end
      end
      
      # Special handling for table children (rows and cells) - truncated for brevity
      if block.context == :table && block.respond_to?(:rows) && block.rows
        # Add simplified table processing to avoid hanging
        if block.rows.respond_to?(:head) && block.rows.head && !block.rows.head.empty?
          # Process header rows (simplified)
          row_index = 0
          block.rows.head.each do |row|
            row_info = {
              'context' => 'table_row',
              'content_model' => 'compound',
              'content' => '',
              'level' => level + 1,
              'children' => []
            }
            children << row_info
            row_index += 1
          end
        end
      end
      
      block_info['children'] = children
      
      # Handle special block types dynamically
      case block.context
      when :admonition
        block_info['admonition_name'] = block.attr('name') || block.attr('style') || 'NOTE'
      when :list_item
        block_info['text'] = block.text if block.respond_to?(:text)
        block_info['marker'] = block.marker if block.respond_to?(:marker)
      end
      
      block_info
    end
    
    # Build result
    blocks = []
    if doc.blocks
      doc.blocks.each do |block|
        blocks << extract_block_info(block, 0)
      end
    end
    
    {
      'blocks' => blocks,
      'title' => doc.doctitle,
      'attributes' => doc.attributes
    }
  end
rescue Timeout::Error
  raise "Document parsing timed out"
end

# Main server loop with timeout and error handling
STDOUT.sync = true
STDERR.sync = true

begin
  puts JSON.generate({'success' => true, 'data' => 'server_ready'})
  STDOUT.flush
  
  while line = STDIN.gets
    begin
      request = JSON.parse(line.strip)
      
      case request['action']
      when 'ping'
        puts JSON.generate({'success' => true, 'data' => 'pong'})
      when 'parse'
        result = parse_document(request['content'])
        puts JSON.generate({'success' => true, 'data' => result})
      when 'shutdown'
        puts JSON.generate({'success' => true, 'data' => 'goodbye'})
        STDOUT.flush
        exit(0)
      else
        puts JSON.generate({'success' => false, 'error' => 'Unknown action'})
      end
      
      STDOUT.flush
      
    rescue JSON::ParserError => e
      puts JSON.generate({'success' => false, 'error' => "JSON parse error: #{e.message}"})
      STDOUT.flush
    rescue => e
      puts JSON.generate({'success' => false, 'error' => "Processing error: #{e.message}"})
      STDOUT.flush
    end
  end
  
rescue => e
  puts JSON.generate({'success' => false, 'error' => "Server error: #{e.message}"})
  STDOUT.flush
  exit(1)
end
'''
            
            # Start Ruby process with proper configuration
            self.process = subprocess.Popen(
                ['ruby'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # Unbuffered
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None  # Create process group
            )
            
            # Send the script to Ruby
            if self.process.stdin:
                self.process.stdin.write(ruby_server_script)
                self.process.stdin.flush()
            
            # Wait for server ready confirmation with timeout
            if self.process.stdout:
                ready_line = self._read_with_timeout(self.process.stdout, self.timeout)
                if ready_line:
                    response = json.loads(ready_line.strip())
                    if response.get('success') and response.get('data') == 'server_ready':
                        logger.info("✅ Ruby asciidoctor server started successfully")
                        self._failed_attempts = 0  # Reset failure count on success
                        return
                    else:
                        raise Exception(f"Server startup failed: {response}")
                else:
                    raise Exception("Server startup timeout")
            else:
                raise Exception("No stdout available from Ruby process")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Ruby server: {e}")
            self._failed_attempts += 1
            self._last_failure_time = time.time()
            if self.process:
                self._terminate_process()
            self.process = None
            raise
    
    def _read_with_timeout(self, stream, timeout):
        """Read from stream with timeout to prevent hanging."""
        import select
        import sys
        
        if sys.platform == 'win32':
            # Windows doesn't support select on regular files
            # Use a simple timeout approach
            start_time = time.time()
            while time.time() - start_time < timeout:
                if stream.readable():
                    line = stream.readline()
                    if line:
                        return line
                time.sleep(0.1)
            return None
        else:
            # Unix/Linux - use select
            ready, _, _ = select.select([stream], [], [], timeout)
            if ready:
                return stream.readline()
            return None
    
    def _terminate_process(self):
        """Safely terminate the Ruby process."""
        if self.process:
            try:
                # Try graceful shutdown first
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()
                
                # Wait a bit for graceful shutdown
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()
                    self.process.wait()
                    
            except (ProcessLookupError, OSError):
                pass  # Process already terminated
            
            self.process = None

    def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the Ruby server and get response with timeout."""
        if not self.process:
            raise Exception("Ruby server is not running")
        
        try:
            # Send request
            request_json = json.dumps(request) + '\n'
            if self.process.stdin:
                self.process.stdin.write(request_json)
                self.process.stdin.flush()
            else:
                raise Exception("Ruby server stdin is not available")
            
            # Get response with timeout
            if self.process.stdout:
                response_line = self._read_with_timeout(self.process.stdout, self.timeout)
            else:
                raise Exception("Ruby server stdout is not available")
                
            if not response_line:
                raise Exception("No response from Ruby server (timeout)")
            
            response = json.loads(response_line.strip())
            
            if not response.get('success', False):
                raise Exception(f"Ruby server error: {response.get('error', 'Unknown error')}")
            
            return response['data']
            
        except Exception as e:
            logger.error(f"Error communicating with Ruby server: {e}")
            # Don't automatically restart on communication errors during tests
            if not os.environ.get('PYTEST_CURRENT_TEST'):
                self._restart_server()
            raise
    
    def _restart_server(self):
        """Restart the Ruby server process if not in test mode."""
        if self._failed_attempts >= self._max_attempts:
            logger.warning("Max restart attempts reached, not restarting Ruby server")
            return
            
        logger.info("🔄 Restarting Ruby server...")
        self.shutdown()
        self._start_server()
    
    def parse_document(self, content: str) -> Dict[str, Any]:
        """
        Parse AsciiDoc content using the persistent Ruby server.
        
        Args:
            content: Raw AsciiDoc content
            
        Returns:
            Parsed document structure
        """
        if not self.process:
            raise Exception("Ruby server is not available")
            
        with self.lock:
            return self._send_request({
                'action': 'parse',
                'content': content
            })
    
    def ping(self) -> bool:
        """
        Check if the Ruby server is responding.
        
        Returns:
            True if server is responding
        """
        if not self.process:
            return False
            
        try:
            with self.lock:
                response = self._send_request({'action': 'ping'})
                return response == 'pong'
        except:
            return False
    
    def shutdown(self):
        """Shutdown the Ruby server process."""
        if self.process:
            try:
                with self.lock:
                    # Try graceful shutdown
                    self._send_request({'action': 'shutdown'})
            except:
                pass
            
            self._terminate_process()
            logger.info("Ruby server shut down")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# Global server instance
_server_instance: Optional[RubyAsciidoctorServer] = None
_server_lock = threading.Lock()


def get_server() -> RubyAsciidoctorServer:
    """Get or create the global Ruby server instance with safe initialization."""
    global _server_instance
    
    with _server_lock:
        # Don't ping during initialization to avoid hanging
        if _server_instance is None:
            try:
                _server_instance = RubyAsciidoctorServer()
            except Exception as e:
                logger.warning(f"Failed to create Ruby server: {e}")
                # Create a dummy server that always fails
                _server_instance = None
                raise
        
        return _server_instance


def shutdown_server():
    """Shutdown the global server instance."""
    global _server_instance
    
    with _server_lock:
        if _server_instance:
            _server_instance.shutdown()
            _server_instance = None 