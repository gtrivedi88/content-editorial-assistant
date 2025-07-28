#!/usr/bin/env ruby
require 'asciidoctor'
require 'json'

# Recursively converts an Asciidoctor AST node to a detailed hash,
# preserving all information needed by the Python application.
def node_to_hash(node)
  return nil unless node

  # Get raw text content instead of HTML-converted content
  raw_content = get_raw_text_content(node)

  node_hash = {
    'context' => node.context.to_s,
    'content' => raw_content,  # Use our raw text extraction
    'text' => node.respond_to?(:text) ? node.text : nil,
    'source' => node.respond_to?(:source) ? node.source : '',
    'level' => node.respond_to?(:level) ? node.level : 0,
    'title' => node.respond_to?(:title) ? node.title : nil,
    'style' => node.respond_to?(:style) ? node.style : nil,
    'attributes' => node.attributes,
    'lineno' => node.respond_to?(:lineno) ? node.lineno : 0,
    'marker' => node.respond_to?(:marker) ? node.marker : nil,
    'children' => []
  }

  # Recursively process all child blocks
  if node.respond_to?(:blocks) && node.blocks
    node_hash['children'].concat(node.blocks.map { |child| node_to_hash(child) })
  end

  # Process list items as children ONLY if there are no blocks (to avoid duplication)
  # For lists, items and blocks often refer to the same children
  if node.respond_to?(:items) && node.items && (!node.respond_to?(:blocks) || node.blocks.empty?)
    node_hash['children'].concat(node.items.map { |item| node_to_hash(item) })
  end

  # Process table rows and cells as children
  if node.context == :table
    (node.rows.head + node.rows.body + node.rows.foot).each do |row|
        # Create a synthetic hash for the row, as it's not a standard block
        row_hash = { 'context' => 'table_row', 'children' => [], 'lineno' => row.first&.lineno || node.lineno, 'attributes' => {} }
        row.each { |cell| row_hash['children'] << node_to_hash(cell) }
        node_hash['children'] << row_hash
    end
  end

  node_hash
end

# Extract raw text content without HTML conversion
def get_raw_text_content(node)
  case node.context
  when :document
    # For documents, return the title if available
    node.respond_to?(:title) ? node.title : ''
  when :section
    # For sections, return the title
    node.respond_to?(:title) ? node.title : ''
  when :paragraph
    # For paragraphs, extract the raw text from lines
    if node.respond_to?(:lines) && node.lines
      node.lines.join(' ')
    elsif node.respond_to?(:source)
      node.source
    else
      ''
    end
  when :list_item
    # For list items, get the text without HTML conversion
    node.respond_to?(:text) ? node.text : ''
  when :listing, :literal
    # For code blocks, use source as-is
    node.respond_to?(:source) ? node.source : ''
  when :table_cell
    # For table cells, use text or source
    if node.respond_to?(:text) && node.text
      node.text
    elsif node.respond_to?(:source)
      node.source
    else
      ''
    end
  else
    # For other block types, try various fields but avoid HTML conversion
    if node.respond_to?(:source) && node.source
      node.source
    elsif node.respond_to?(:text) && node.text
      node.text
    else
      ''
    end
  end
end

def parse_asciidoc(content, filename = "")
  begin
    # Parse with safe mode to avoid security issues, but don't convert to HTML
    doc = Asciidoctor.load(content, safe: :safe, sourcemap: true, parse: true)
    ast_hash = node_to_hash(doc)
    { 'success' => true, 'data' => ast_hash }
  rescue => e
    { 'success' => false, 'error' => "Asciidoctor parsing failed: #{e.message}" }
  end
end

# Main execution logic
if __FILE__ == $0
  if ARGV.length != 2
    STDERR.puts "Usage: ruby asciidoc_parser.rb <input_file> <output_file>"
    exit 1
  end
  input_file = ARGV[0]
  output_file = ARGV[1]
  begin
    content = File.read(input_file)
    result = parse_asciidoc(content, input_file)
    File.write(output_file, result.to_json)
  rescue => e
    File.write(output_file, { 'success' => false, 'error' => e.message }.to_json)
    exit 1
  end
end