#!/usr/bin/env ruby
require 'asciidoctor'
require 'json'

# Extracts raw text from a node, cleans it of inline comments, and returns it.
def get_cleaned_text(node, field = :source)
  raw_text = ""
  # Prioritize the 'text' field for certain contexts as it's often cleaner.
  if [:list_item, :table_cell].include?(node.context) && node.respond_to?(:text)
    raw_text = node.text || ""
  # For paragraphs and verses, the 'lines' array is the most reliable source.
  elsif [:paragraph, :verse].include?(node.context) && node.respond_to?(:lines)
    raw_text = node.lines.join(' ')
  # Fallback to the 'source' attribute for most other blocks.
  elsif node.respond_to?(:source)
    raw_text = node.source || ""
  # Final fallback to 'text' if source is unavailable.
  elsif node.respond_to?(:text)
    raw_text = node.text || ""
  end

  # **PRODUCTION-GRADE FIX**: Globally strip AsciiDoc inline comments (e.g., // comment)
  # from the final content to prevent them from ever being analyzed or displayed.
  # **CRITICAL**: Don't match // in URLs (https:// or http://)
  # Only match // that comes after whitespace (actual comments), not after : or /
  raw_text.gsub(/(?<!:)(?<!\/)\s\/\/.*/, '').strip
end


# Special handler for definition lists to structure them correctly.
def dlist_to_hash(dlist_node)
  dlist_hash = {
    'context' => 'dlist',
    'content' => '', # The dlist container has no direct content.
    'lineno' => dlist_node.lineno,
    'attributes' => dlist_node.attributes,
    'children' => []
  }

  # A dlist's items are an array of [term(s), description] pairs.
  dlist_node.items.each do |term_nodes, desc_node|
    # A description can have multiple terms; we join them.
    term_text = term_nodes.map { |t| get_cleaned_text(t, :text) }.join(', ')

    # The description can be a simple text block or a complex block with children.
    desc_text = desc_node.text if desc_node.respond_to?(:text)
    desc_source = desc_node.source if desc_node.respond_to?(:source)

    # Create a synthetic block for this term/description item.
    item_hash = {
      'context' => 'description_list_item',
      'term' => term_text,
      'description' => get_cleaned_text(desc_node, :text),
      'description_source' => desc_source,
      'lineno' => term_nodes.first.lineno,
      'attributes' => desc_node.attributes,
      'children' => []
    }

    # If the description has its own blocks (e.g., a paragraph or nested list), process them.
    if desc_node.respond_to?(:blocks) && desc_node.blocks
        item_hash['children'] = desc_node.blocks.map { |child| node_to_hash(child) }.compact
    end

    dlist_hash['children'] << item_hash
  end

  dlist_hash
end


# Recursively converts an Asciidoctor AST node to a detailed hash.
def node_to_hash(node)
  return nil unless node

  # Delegate definition lists to the specialized handler.
  return dlist_to_hash(node) if node.context == :dlist

  node_hash = {
    'context' => node.context.to_s,
    'content' => get_cleaned_text(node),
    'text' => get_cleaned_text(node, :text),
    'source' => node.respond_to?(:source) ? node.source : '',
    'level' => node.respond_to?(:level) ? node.level : 0,
    'title' => node.respond_to?(:title) ? node.title : nil,
    'style' => node.respond_to?(:style) ? node.style : nil,
    'attributes' => node.attributes,
    'lineno' => node.respond_to?(:lineno) ? node.lineno : 0,
    'marker' => node.respond_to?(:marker) ? node.marker : nil,
    'children' => []
  }

  # Recursively process all child blocks.
  if node.respond_to?(:blocks) && node.blocks
    node_hash['children'].concat(node.blocks.map { |child| node_to_hash(child) }.compact)
  end

  # Process list items as children if they aren't already in blocks.
  if node.respond_to?(:items) && node.items && node.blocks.empty?
    node_hash['children'].concat(node.items.map { |item| node_to_hash(item) }.compact)
  end

  # Process table rows and cells as children.
  if node.context == :table
    (node.rows.head + node.rows.body + node.rows.foot).each do |row|
        row_hash = { 'context' => 'table_row', 'children' => [], 'lineno' => row.first&.lineno || node.lineno, 'attributes' => {} }
        row.each do |cell|
          cell_hash = node_to_hash(cell)
          
          # **FIX**: If this is an AsciiDoc-style cell (a|), it can contain nested blocks.
          # The inner_document contains the parsed blocks like lists, admonitions, paragraphs.
          if cell.style == :asciidoc && cell.respond_to?(:inner_document) && cell.inner_document
            inner_blocks = cell.inner_document.blocks || []
            cell_hash['children'] = inner_blocks.map { |block| node_to_hash(block) }.compact
          end
          
          row_hash['children'] << cell_hash
        end
        node_hash['children'] << row_hash
    end
  end

  node_hash
end


# Main parsing function
def parse_asciidoc(content, filename = "")
  begin
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
