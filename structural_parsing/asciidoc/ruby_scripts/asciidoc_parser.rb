#!/usr/bin/env ruby

require 'asciidoctor'
require 'json'

def extract_block_info(block, level = 0)
  # Extract content using simple approach
  content = ''
  
  case block.context
  when :list_item
    content = block.respond_to?(:text) && !block.text.nil? ? block.text.to_s : ''
  when :paragraph, :sidebar, :example, :quote, :verse, :literal, :admonition
    if block.respond_to?(:lines) && block.lines && !block.lines.empty?
      content = block.lines.join("\n")
    elsif block.respond_to?(:source) && !block.source.nil?
      content = block.source.to_s
    elsif !block.content.nil?
      content = block.content.to_s
    end
  when :listing
    if block.respond_to?(:source) && !block.source.nil?
      content = block.source.to_s
    elsif block.respond_to?(:lines) && block.lines
      content = block.lines.join("\n")
    end
  when :table
    # For tables, reconstruct content from table structure
    if block.respond_to?(:rows) && block.rows
      content_parts = []
      
      # Add header row if present
      if block.rows.respond_to?(:head) && block.rows.head && !block.rows.head.empty?
        header_row = block.rows.head.first
        if header_row.respond_to?(:each)
          header_cells = header_row.map { |cell| cell.respond_to?(:text) ? cell.text : cell.to_s }
          content_parts << "|#{header_cells.join(" |")} |"
        end
      end
      
      # Add body rows if present
      if block.rows.respond_to?(:body) && block.rows.body
        block.rows.body.each do |row|
          if row.respond_to?(:each)
            row_cells = row.map { |cell| cell.respond_to?(:text) ? cell.text : cell.to_s }
            content_parts << "|#{row_cells.join(" |")} |"
          end
        end
      end
      
      content = content_parts.join("\n")
    else
      # Fallback
      content = ''
    end
  else
    if block.respond_to?(:source) && !block.source.nil?
      content = block.source.to_s
    elsif block.respond_to?(:lines) && block.lines && !block.lines.empty?
      content = block.lines.join("\n")
    elsif !block.content.nil?
      content = block.content.to_s
    elsif block.respond_to?(:text) && !block.text.nil?
      content = block.text.to_s
    end
  end
  
  # Clean up HTML tags (except for code blocks)
  unless [:listing, :literal].include?(block.context)
    if content.include?('<') && content.include?('>')
      content = content.gsub(/<[^>]+>/, '').gsub(/\s+/, ' ').strip
    end
  end
  
  # Determine block level
  block_level = level
  if block.context == :section
    block_level = block.level if block.respond_to?(:level)
  elsif block.context == :heading
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
    'style' => block.style,
    'title' => block.title,
    'id' => block.id,
    'attributes' => block.attributes.to_h,
    'raw_content' => content
  }
  
  # Add source location if available
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
  
  # Special handling for table blocks - extract rows and cells as children
  if block.context == :table && block.respond_to?(:rows) && block.rows
    # Add header row as a child if present
    if block.rows.respond_to?(:head) && block.rows.head && !block.rows.head.empty?
      header_row = block.rows.head.first
      if header_row.respond_to?(:each)
        row_info = {
          'context' => 'table_row',
          'content_model' => 'compound',
          'content' => '',
          'level' => level + 1,
          'style' => 'header',
          'title' => nil,
          'id' => nil,
          'attributes' => { 'role' => 'header' },
          'children' => []
        }
        
        # Add cells as children of the row
        header_row.each_with_index do |cell, cell_index|
          cell_content = cell.respond_to?(:text) ? cell.text : cell.to_s
          cell_info = {
            'context' => 'table_cell',
            'content_model' => 'simple',
            'content' => cell_content,
            'level' => level + 2,
            'style' => nil,
            'title' => nil,
            'id' => nil,
            'attributes' => { 'column' => cell_index + 1, 'role' => 'header' },
            'children' => []
          }
          row_info['children'] << cell_info
        end
        
        children << row_info
      end
    end
    
    # Add body rows as children if present
    if block.rows.respond_to?(:body) && block.rows.body
      block.rows.body.each_with_index do |row, row_index|
        if row.respond_to?(:each)
          row_info = {
            'context' => 'table_row',
            'content_model' => 'compound',
            'content' => '',
            'level' => level + 1,
            'style' => 'body',
            'title' => nil,
            'id' => nil,
            'attributes' => { 'row' => row_index + 1 },
            'children' => []
          }
          
          # Add cells as children of the row
          row.each_with_index do |cell, cell_index|
            cell_content = cell.respond_to?(:text) ? cell.text : cell.to_s
            cell_info = {
              'context' => 'table_cell',
              'content_model' => 'simple',
              'content' => cell_content,
              'level' => level + 2,
              'style' => nil,
              'title' => nil,
              'id' => nil,
              'attributes' => { 'column' => cell_index + 1, 'row' => row_index + 1 },
              'children' => []
            }
            row_info['children'] << cell_info
          end
          
          children << row_info
        end
      end
    end
  end
  
  # Regular children blocks (for non-table blocks or additional table children)
  if block.respond_to?(:blocks) && block.blocks
    block.blocks.each do |child_block|
      children << extract_block_info(child_block, level + 1)
    end
  end
  
  block_info['children'] = children
  
  # Handle special block types
  case block.context
  when :admonition
    block_info['admonition_name'] = block.attr('name') || block.attr('style') || 'NOTE'
  when :list_item
    block_info['text'] = block.text if block.respond_to?(:text)
    block_info['marker'] = block.marker if block.respond_to?(:marker)
  when :listing, :literal
    block_info['language'] = block.attr('language') if block.attr('language')
    block_info['linenums'] = block.attr('linenums') if block.attr('linenums')
  end
  
  block_info
end

def parse_asciidoc(content)
  begin
    # Parse the document
    doc = Asciidoctor.load(content, 
      sourcemap: true, 
      safe: :unsafe,
      parse_header_only: false,
      standalone: false)
    
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
    
    # Extract all blocks from the document
    doc.blocks.each do |block|
      block_info = extract_block_info(block)
      result['blocks'] << block_info if block_info
    end
    
    {
      'success' => true,
      'data' => result
    }
  rescue => e
    {
      'success' => false,
      'error' => e.message
    }
  end
end

# Main execution
if __FILE__ == $0
  if ARGV.length != 2
    STDERR.puts "Usage: ruby asciidoc_parser.rb input_file output_file"
    exit 1
  end
  
  input_file = ARGV[0]
  output_file = ARGV[1]
  
  begin
    content = File.read(input_file)
    result = parse_asciidoc(content)
    File.write(output_file, JSON.generate(result))
  rescue => e
    error_result = {
      'success' => false,
      'error' => e.message
    }
    File.write(output_file, JSON.generate(error_result))
    exit 1
  end
end 