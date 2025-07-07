"""
Ruby server for persistent asciidoctor parsing.
Maintains a long-running Ruby process to avoid subprocess overhead.
"""

import json
import subprocess
import tempfile
import threading
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RubyAsciidoctorServer:
    """
    Persistent Ruby server for asciidoctor parsing.
    
    This server maintains a long-running Ruby process to avoid the overhead
    of creating new processes for each document parse operation.
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.process: Optional[subprocess.Popen] = None
        self.lock = threading.Lock()
        self._start_server()
    
    def _start_server(self):
        """Start the Ruby server process."""
        ruby_server_script = '''
require 'asciidoctor'
require 'json'
require 'tempfile'

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
        content = block.lines.join('\n')
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
    block_info['children'] = children
    
    # Handle special block types dynamically
    case block.context
    when :admonition
      block_info['admonition_name'] = block.attr('name') || block.attr('style') || 'NOTE'
    when :list_item
      block_info['text'] = block.text if block.respond_to?(:text)
      block_info['marker'] = block.marker if block.respond_to?(:marker)
    when :listing, :literal
      block_info['language'] = block.attr('language') if block.attr('language')
      block_info['linenums'] = block.attr('linenums') if block.attr('linenums')
    when :table
      block_info['cols'] = block.attr('cols') if block.attr('cols')
      block_info['format'] = block.attr('format') if block.attr('format')
    end
    
    # Add any additional attributes that might be useful
    if block.respond_to?(:caption) && block.caption
      block_info['caption'] = block.caption
    end
    
    if block.respond_to?(:role) && block.role
      block_info['role'] = block.role
    end
    
    block_info
  end
  
  # Extract document structure
  result = {
    'title' => doc.doctitle,
    'attributes' => doc.attributes.to_h,
    'blocks' => []
  }
  
  # Add document title as a heading block if it exists
  if doc.doctitle && doc.header?
    title_block = {
      'context' => 'heading',
      'content_model' => 'empty',
      'content' => doc.doctitle,
      'level' => 0,
      'style' => nil,
      'title' => nil,
      'id' => nil,
      'attributes' => {},
      'source_location' => {
        'file' => '<content>',
        'lineno' => 1,
        'path' => '<content>'
      },
      'lines' => ["= #{doc.doctitle}"],
      'children' => []
    }
    result['blocks'] << title_block
  end
  
  # Add document attributes as attribute_entry blocks
  doc.attributes.each do |name, value|
    next if name.start_with?('_') # Skip internal attributes
    next unless ['author', 'revdate', 'version', 'email'].include?(name)
    
    attr_block = {
      'context' => 'attribute_entry',
      'content_model' => 'empty', 
      'content' => ":#{name}: #{value}",
      'level' => 0,
      'style' => nil,
      'title' => nil,
      'id' => nil,
      'attributes' => {'name' => name, 'value' => value},
      'source_location' => {
        'file' => '<content>',
        'lineno' => 2,
        'path' => '<content>'
      },
      'lines' => [":#{name}: #{value}"],
      'children' => []
    }
    result['blocks'] << attr_block
  end
  
  # Extract all blocks from the document
  doc.blocks.each do |block|
    block_info = extract_block_info(block)
    if block_info
      result['blocks'] << block_info
    else
      # Log unhandled block types for debugging
      STDERR.puts "UNHANDLED BLOCK: context=#{block.context}, style=#{block.style}, content_model=#{block.content_model}"
    end
  end
  
  result
end

# Server loop
STDOUT.sync = true
STDERR.sync = true

puts "ASCIIDOCTOR_SERVER_READY"

while true
  begin
    line = STDIN.gets
    break if line.nil?
    
    request = JSON.parse(line.strip)
    
    case request['action']
    when 'parse'
      result = parse_document(request['content'])
      puts JSON.generate({
        'success' => true,
        'data' => result
      })
    when 'ping'
      puts JSON.generate({
        'success' => true,
        'data' => 'pong'
      })
    when 'shutdown'
      break
    else
      puts JSON.generate({
        'success' => false,
        'error' => "Unknown action: #{request['action']}"
      })
    end
  rescue => e
    puts JSON.generate({
      'success' => false,
      'error' => e.message
    })
  end
end
'''
        
        try:
            self.process = subprocess.Popen(
                ['ruby', '-e', ruby_server_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Wait for server to be ready
            if self.process.stdout:
                ready_line = self.process.stdout.readline().strip()
                if ready_line != "ASCIIDOCTOR_SERVER_READY":
                    raise Exception(f"Server failed to start: {ready_line}")
            else:
                raise Exception("Ruby server stdout is not available")
            
            logger.info("✅ Ruby asciidoctor server started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Ruby server: {e}")
            self.process = None
            raise
    
    def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the Ruby server and get response."""
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
            
            # Get response
            if self.process.stdout:
                response_line = self.process.stdout.readline().strip()
            else:
                raise Exception("Ruby server stdout is not available")
                
            if not response_line:
                raise Exception("No response from Ruby server")
            
            response = json.loads(response_line)
            
            if not response.get('success', False):
                raise Exception(f"Ruby server error: {response.get('error', 'Unknown error')}")
            
            return response['data']
            
        except Exception as e:
            logger.error(f"Error communicating with Ruby server: {e}")
            self._restart_server()
            raise
    
    def _restart_server(self):
        """Restart the Ruby server process."""
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
                    self._send_request({'action': 'shutdown'})
            except:
                pass
            
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None
            logger.info("Ruby server shut down")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# Global server instance
_server_instance: Optional[RubyAsciidoctorServer] = None
_server_lock = threading.Lock()


def get_server() -> RubyAsciidoctorServer:
    """Get or create the global Ruby server instance."""
    global _server_instance
    
    with _server_lock:
        if _server_instance is None or not _server_instance.ping():
            if _server_instance:
                _server_instance.shutdown()
            _server_instance = RubyAsciidoctorServer()
        
        return _server_instance


def shutdown_server():
    """Shutdown the global server instance."""
    global _server_instance
    
    with _server_lock:
        if _server_instance:
            _server_instance.shutdown()
            _server_instance = None 