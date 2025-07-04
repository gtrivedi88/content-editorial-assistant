# Markdown Structural Parsing Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing structural parsing for Markdown documents in the style-guide-ai application.

## Prerequisites

### Dependencies
```bash
pip install markdown-it-py>=3.0.0
pip install mdit-py-plugins>=0.4.0
```

### Current System Understanding
- Existing: `DocumentProcessor` strips Markdown formatting
- New: Preserve structure while extracting content blocks
- Goal: Context-aware rule application

## Implementation Phases

### Phase 1: Core Infrastructure (Day 1-2)

#### Step 1: Create Core Data Types
Create `src/structural_parsing/__init__.py`:
```python
# Empty init file
```

Create `src/structural_parsing/types.py`:
```python
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional

class BlockType(Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM_ORDERED = "list_item_ordered"
    LIST_ITEM_UNORDERED = "list_item_unordered"
    CODE_BLOCK = "code_block"
    BLOCKQUOTE = "blockquote"
    HORIZONTAL_RULE = "horizontal_rule"

@dataclass
class StructuralBlock:
    type: BlockType
    content: str
    raw_content: str
    metadata: Dict[str, Any]
    start_line: int
    end_line: int
    start_pos: int
    end_pos: int
    
    def get_context_info(self) -> Dict[str, Any]:
        return {
            'block_type': self.type.value,
            'metadata': self.metadata,
            'position': {
                'start_line': self.start_line,
                'end_line': self.end_line
            }
        }
```

#### Step 2: Create Base Parser Interface
Create `src/structural_parsing/base_parser.py`:
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .types import StructuralBlock, BlockType

class StructuralParser(ABC):
    def __init__(self):
        self.supported_formats = self._get_supported_formats()
    
    @abstractmethod
    def _get_supported_formats(self) -> List[str]:
        pass
    
    @abstractmethod
    def parse(self, content: str, filename: str = "") -> List[StructuralBlock]:
        pass
    
    def supports_format(self, format_name: str) -> bool:
        return format_name.lower() in self.supported_formats
```

### Phase 2: Markdown Parser Implementation (Day 3-4)

#### Step 3: Implement Markdown Parser
Create `src/structural_parsing/markdown_parser.py`:
```python
import re
from typing import List, Dict, Any, Optional
from markdown_it import MarkdownIt
from .base_parser import StructuralParser
from .types import StructuralBlock, BlockType

class MarkdownStructuralParser(StructuralParser):
    def __init__(self):
        super().__init__()
        self.md = MarkdownIt("commonmark", {
            "html": True,
            "linkify": True,
            "typographer": True,
        })
    
    def _get_supported_formats(self) -> List[str]:
        return ['md', 'markdown']
    
    def parse(self, content: str, filename: str = "") -> List[StructuralBlock]:
        tokens = self.md.parse(content)
        content_lines = content.split('\n')
        return self._tokens_to_blocks(tokens, content_lines)
    
    def _tokens_to_blocks(self, tokens: List, content_lines: List[str]) -> List[StructuralBlock]:
        blocks = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token.type == 'heading_open':
                block = self._process_heading(tokens, i, content_lines)
                if block:
                    blocks.append(block)
                i += 3  # Skip heading_open, inline, heading_close
            elif token.type == 'paragraph_open':
                block = self._process_paragraph(tokens, i, content_lines)
                if block:
                    blocks.append(block)
                i += 3  # Skip paragraph_open, inline, paragraph_close
            elif token.type == 'ordered_list_open':
                list_blocks, consumed = self._process_ordered_list(tokens, i, content_lines)
                blocks.extend(list_blocks)
                i += consumed
            elif token.type == 'bullet_list_open':
                list_blocks, consumed = self._process_bullet_list(tokens, i, content_lines)
                blocks.extend(list_blocks)
                i += consumed
            elif token.type == 'blockquote_open':
                block = self._process_blockquote(tokens, i, content_lines)
                if block:
                    blocks.append(block)
                i += self._skip_blockquote_tokens(tokens, i)
            elif token.type in ['fence', 'code_block']:
                block = self._process_code_block(token, content_lines)
                if block:
                    blocks.append(block)
                i += 1
            else:
                i += 1
        
        return blocks
    
    def _process_heading(self, tokens: List, index: int, content_lines: List[str]) -> Optional[StructuralBlock]:
        if index + 2 >= len(tokens):
            return None
        
        heading_open = tokens[index]
        inline_token = tokens[index + 1]
        
        level = int(heading_open.tag[1])  # h1 -> 1, h2 -> 2, etc.
        content = inline_token.content if inline_token.content else ""
        
        start_line = heading_open.map[0] if heading_open.map else 0
        end_line = heading_open.map[1] if heading_open.map else start_line
        raw_content = self._get_raw_content(content_lines, start_line, end_line)
        
        return StructuralBlock(
            type=BlockType.HEADING,
            content=content,
            raw_content=raw_content,
            metadata={'level': level, 'format': 'markdown'},
            start_line=start_line,
            end_line=end_line,
            start_pos=0,  # Calculate properly
            end_pos=0     # Calculate properly
        )
    
    def _process_paragraph(self, tokens: List, index: int, content_lines: List[str]) -> Optional[StructuralBlock]:
        if index + 2 >= len(tokens):
            return None
        
        paragraph_open = tokens[index]
        inline_token = tokens[index + 1]
        
        content = inline_token.content if inline_token.content else ""
        start_line = paragraph_open.map[0] if paragraph_open.map else 0
        end_line = paragraph_open.map[1] if paragraph_open.map else start_line
        raw_content = self._get_raw_content(content_lines, start_line, end_line)
        
        return StructuralBlock(
            type=BlockType.PARAGRAPH,
            content=content,
            raw_content=raw_content,
            metadata={'format': 'markdown'},
            start_line=start_line,
            end_line=end_line,
            start_pos=0,
            end_pos=0
        )
    
    def _process_ordered_list(self, tokens: List, index: int, content_lines: List[str]) -> tuple:
        # Implementation for ordered lists
        blocks = []
        consumed = 1
        # TODO: Implement list processing
        return blocks, consumed
    
    def _process_bullet_list(self, tokens: List, index: int, content_lines: List[str]) -> tuple:
        # Implementation for bullet lists
        blocks = []
        consumed = 1
        # TODO: Implement list processing
        return blocks, consumed
    
    def _process_blockquote(self, tokens: List, index: int, content_lines: List[str]) -> Optional[StructuralBlock]:
        # TODO: Implement blockquote processing
        return None
    
    def _process_code_block(self, token, content_lines: List[str]) -> Optional[StructuralBlock]:
        # TODO: Implement code block processing
        return None
    
    def _skip_blockquote_tokens(self, tokens: List, index: int) -> int:
        # TODO: Implement token skipping logic
        return 1
    
    def _get_raw_content(self, content_lines: List[str], start_line: int, end_line: int) -> str:
        if start_line >= len(content_lines):
            return ""
        end_line = min(end_line, len(content_lines))
        return '\n'.join(content_lines[start_line:end_line])
```

#### Step 4: Create Parser Factory
Create `src/structural_parsing/parser_factory.py`:
```python
from typing import Optional
from .base_parser import StructuralParser
from .markdown_parser import MarkdownStructuralParser

class ParserFactory:
    _parsers = {
        'markdown': MarkdownStructuralParser,
    }
    
    @classmethod
    def get_parser(cls, format_name: str) -> Optional[StructuralParser]:
        parser_class = cls._parsers.get(format_name.lower())
        if parser_class:
            return parser_class()
        return None
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        return list(cls._parsers.keys())
```

### Phase 3: Integration with Document Processor (Day 5)

#### Step 5: Enhance Document Processor
Modify `src/document_processor.py`:
```python
# Add import
from structural_parsing.parser_factory import ParserFactory
from structural_parsing.types import StructuralBlock

class DocumentProcessor:
    def __init__(self):
        # Existing initialization
        self.parser_factory = ParserFactory()
        self.use_structural_parsing = True  # Feature flag
    
    def extract_text_with_structure(self, filepath: str) -> Dict[str, Any]:
        """Extract text with preserved structure."""
        file_ext = os.path.splitext(filepath)[1].lower()
        format_name = file_ext.lstrip('.')
        
        if not self.use_structural_parsing:
            # Fallback to existing method
            return {'text': self.extract_text(filepath), 'structure': None}
        
        parser = self.parser_factory.get_parser(format_name)
        if not parser:
            # Fallback to existing method
            return {'text': self.extract_text(filepath), 'structure': None}
        
        # Read raw content
        with open(filepath, 'r', encoding='utf-8') as file:
            raw_content = file.read()
        
        # Parse structure
        blocks = parser.parse(raw_content, filepath)
        
        # Extract plain text for backward compatibility
        plain_text = '\n\n'.join(block.content for block in blocks)
        
        return {
            'text': plain_text,
            'structure': blocks,
            'format': format_name
        }
```

### Phase 4: Context-Aware Analysis (Day 6-7)

#### Step 6: Create Context-Aware Analyzer
Create `src/context_aware_analyzer.py`:
```python
from typing import List, Dict, Any
from structural_parsing.types import StructuralBlock, BlockType
from style_analyzer.core_analyzer import StyleAnalyzer

class ContextAwareAnalyzer:
    def __init__(self, base_analyzer: StyleAnalyzer):
        self.base_analyzer = base_analyzer
        self.block_type_rules = {
            BlockType.HEADING: ['headings_rule'],
            BlockType.PARAGRAPH: ['all_language_grammar_rules'],
            BlockType.LIST_ITEM_ORDERED: ['procedures_rule', 'lists_rule'],
            BlockType.LIST_ITEM_UNORDERED: ['lists_rule'],
            BlockType.BLOCKQUOTE: ['all_language_grammar_rules'],
            # CODE_BLOCK typically skipped
        }
    
    def analyze_structured_content(self, blocks: List[StructuralBlock]) -> Dict[str, Any]:
        """Analyze content with structural context."""
        all_errors = []
        block_analyses = []
        
        for block in blocks:
            # Skip code blocks
            if block.type == BlockType.CODE_BLOCK:
                continue
            
            # Analyze block with context
            block_analysis = self._analyze_block(block)
            block_analyses.append(block_analysis)
            
            # Add context to errors
            for error in block_analysis.get('errors', []):
                error['structural_context'] = block.get_context_info()
                all_errors.append(error)
        
        return {
            'errors': all_errors,
            'block_analyses': block_analyses,
            'total_blocks': len(blocks),
            'analyzed_blocks': len(block_analyses)
        }
    
    def _analyze_block(self, block: StructuralBlock) -> Dict[str, Any]:
        """Analyze a single block with context."""
        # Use existing analyzer but with context awareness
        analysis = self.base_analyzer.analyze(block.content)
        
        # Filter rules based on block type
        applicable_rules = self.block_type_rules.get(block.type, [])
        
        # Add block context
        analysis['block_context'] = {
            'type': block.type.value,
            'metadata': block.metadata,
            'applicable_rules': applicable_rules
        }
        
        return analysis
```

#### Step 7: Update API Routes
Modify `app_modules/api_routes.py`:
```python
# Add import
from src.context_aware_analyzer import ContextAwareAnalyzer

@app.route('/analyze', methods=['POST'])
def analyze_content():
    try:
        data = request.get_json()
        content = data.get('content', '')
        use_structural = data.get('use_structural_parsing', True)
        session_id = data.get('session_id', '')
        
        if not content:
            return jsonify({'error': 'No content provided'}), 400
        
        if use_structural:
            # Try structural parsing first
            from structural_parsing.parser_factory import ParserFactory
            parser = ParserFactory.get_parser('markdown')  # Detect format
            
            if parser:
                blocks = parser.parse(content)
                context_analyzer = ContextAwareAnalyzer(style_analyzer)
                analysis = context_analyzer.analyze_structured_content(blocks)
                
                return jsonify({
                    'success': True,
                    'analysis': analysis,
                    'parsing_method': 'structural',
                    'session_id': session_id
                })
        
        # Fallback to existing analysis
        analysis = style_analyzer.analyze(content)
        return jsonify({
            'success': True,
            'analysis': analysis,
            'parsing_method': 'traditional',
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

### Phase 5: Testing and Validation (Day 8-9)

#### Step 8: Create Test Suite
Create `tests/test_markdown_parser.py`:
```python
import pytest
from src.structural_parsing.markdown_parser import MarkdownStructuralParser
from src.structural_parsing.types import BlockType

class TestMarkdownParser:
    def setup_method(self):
        self.parser = MarkdownStructuralParser()
    
    def test_heading_parsing(self):
        content = "# Main Title\n\nSome content"
        blocks = self.parser.parse(content)
        
        assert len(blocks) >= 1
        assert blocks[0].type == BlockType.HEADING
        assert blocks[0].content == "Main Title"
        assert blocks[0].metadata['level'] == 1
    
    def test_paragraph_parsing(self):
        content = "This is a paragraph.\n\nThis is another paragraph."
        blocks = self.parser.parse(content)
        
        paragraphs = [b for b in blocks if b.type == BlockType.PARAGRAPH]
        assert len(paragraphs) >= 2
    
    def test_ordered_list_parsing(self):
        content = "1. First item\n2. Second item\n3. Third item"
        blocks = self.parser.parse(content)
        
        list_items = [b for b in blocks if b.type == BlockType.LIST_ITEM_ORDERED]
        assert len(list_items) >= 3
    
    def test_mixed_content(self):
        content = """# Title
        
This is a paragraph.

1. First step
2. Second step

> This is a blockquote
"""
        blocks = self.parser.parse(content)
        
        types = [block.type for block in blocks]
        assert BlockType.HEADING in types
        assert BlockType.PARAGRAPH in types
        assert BlockType.LIST_ITEM_ORDERED in types
```

#### Step 9: Integration Testing
Create `tests/test_context_aware_analysis.py`:
```python
import pytest
from src.context_aware_analyzer import ContextAwareAnalyzer
from src.structural_parsing.markdown_parser import MarkdownStructuralParser
from style_analyzer.core_analyzer import StyleAnalyzer

class TestContextAwareAnalysis:
    def setup_method(self):
        self.parser = MarkdownStructuralParser()
        self.base_analyzer = StyleAnalyzer()
        self.context_analyzer = ContextAwareAnalyzer(self.base_analyzer)
    
    def test_structured_analysis(self):
        content = """# Our New Features
        
To update the software, you should complete these steps:

1. The new installer is downloaded by the user.
2. Clicking the "Update Now" button to begin.
"""
        
        blocks = self.parser.parse(content)
        analysis = self.context_analyzer.analyze_structured_content(blocks)
        
        assert 'errors' in analysis
        assert 'block_analyses' in analysis
        
        # Check that errors have structural context
        for error in analysis['errors']:
            assert 'structural_context' in error
```

### Phase 6: Frontend Integration (Day 10)

#### Step 10: Update Frontend Display
Modify `templates/base.html` to add structural parsing toggle:
```html
<!-- Add to analysis form -->
<div class="form-check mb-3">
    <input class="form-check-input" type="checkbox" id="useStructuralParsing" checked>
    <label class="form-check-label" for="useStructuralParsing">
        Use Structural Parsing (Recommended)
    </label>
</div>
```

Update JavaScript to send structural parsing flag:
```javascript
function analyzeContent(content) {
    const useStructural = document.getElementById('useStructuralParsing').checked;
    
    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            content: content,
            use_structural_parsing: useStructural,
            session_id: sessionId 
        })
    })
    // ... rest of the function
}
```

## Testing Strategy

### Unit Tests
- Test each parser component individually
- Test block type detection
- Test content extraction accuracy
- Test metadata preservation

### Integration Tests
- Test end-to-end parsing workflow
- Test context-aware analysis
- Test API integration
- Test error handling

### Performance Tests
- Test parsing speed on large documents
- Test memory usage
- Compare performance with traditional parsing

## Deployment Checklist

- [ ] Install dependencies
- [ ] Run all tests
- [ ] Test with sample Markdown files
- [ ] Verify backward compatibility
- [ ] Update documentation
- [ ] Deploy with feature flag enabled

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure all modules are in Python path
2. **Parsing failures**: Check markdown-it-py compatibility
3. **Performance issues**: Consider parsing caching
4. **Memory issues**: Implement streaming for large files

### Debugging
- Enable detailed logging in parsers
- Use debugger to step through token processing
- Test with minimal examples first
- Check token mapping accuracy

## Next Steps
After successful implementation:
1. Add caching for parsed structures
2. Implement document reconstruction
3. Add support for more Markdown features
4. Optimize performance for large documents
5. Add configuration options for parsing behavior 