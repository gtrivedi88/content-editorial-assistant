# AsciiDoc Structural Parsing Implementation Guide

## Overview
Implementation guide for adding AsciiDoc structural parsing to the style-guide-ai application.

## Quick Start Action Plan

### Phase 1: Setup (Days 1-2)
1. Install dependencies: `pip install asciidoctor` or `gem install asciidoctor`
2. Extend `src/structural_parsing/types.py` with AsciiDoc block types
3. Create `src/structural_parsing/asciidoc_parser.py`
4. Update `src/structural_parsing/parser_factory.py`

### Phase 2: Implementation (Days 3-4)
1. Implement AsciiDoc parser with regex fallback
2. Add AsciiDoc-specific rules for admonitions
3. Extend context-aware analyzer
4. Update document processor

### Phase 3: Integration (Days 5-6)
1. Update API routes for format detection
2. Add frontend controls for AsciiDoc
3. Implement comprehensive testing
4. Deploy with feature flags

## Key Implementation Files

### 1. Extended Block Types (`src/structural_parsing/types.py`)
```python
class BlockType(Enum):
    # Existing types...
    ADMONITION = "admonition"      # [NOTE], [WARNING], etc.
    SIDEBAR = "sidebar"            # ****
    EXAMPLE = "example"            # ====
    LISTING = "listing"            # ----
    LITERAL = "literal"            # ....
    QUOTE = "quote"                # ____
    VERSE = "verse"                # [verse]
    PASS = "pass"                  # ++++
    ATTRIBUTE = "attribute"        # :attr:
```

### 2. AsciiDoc Parser (`src/structural_parsing/asciidoc_parser.py`)
```python
class AsciiDocStructuralParser(StructuralParser):
    def __init__(self):
        super().__init__()
        self.block_patterns = {
            'admonition': re.compile(r'^\[(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]'),
            'heading': re.compile(r'^(=+)\s+(.+)$'),
            'sidebar': re.compile(r'^\*{4,}\s*$'),
            'listing': re.compile(r'^-{4,}\s*$'),
            # ... other patterns
        }
    
    def parse(self, content: str, filename: str = "") -> List[StructuralBlock]:
        # Implementation using regex patterns
        # Falls back from asciidoctor if available
```

### 3. Context-Aware Rules
```python
# Extended rule mapping for AsciiDoc
self.block_type_rules = {
    BlockType.ADMONITION: ['messages_rule', 'notes_rule'],
    BlockType.LISTING: [],  # Skip code analysis
    BlockType.LITERAL: [],  # Skip code analysis
    BlockType.PASS: [],     # Skip passthrough content
    # ... other mappings
}
```

### 4. API Integration (`app_modules/api_routes.py`)
```python
def _detect_content_format(content: str) -> str:
    """Auto-detect document format"""
    if content.strip().startswith('=') or '[NOTE]' in content:
        return 'asciidoc'
    elif content.strip().startswith('#') or '```' in content:
        return 'markdown'
    return 'markdown'  # Default
```

## Critical AsciiDoc Patterns

### Admonitions
```asciidoc
[NOTE]
This is a note.

[WARNING]
This is a warning.
```

### Delimited Blocks
```asciidoc
****
Sidebar content
****

====
Example content
====

----
Code listing
----
```

### Headings
```asciidoc
= Document Title
== Section Title
=== Subsection Title
```

## Testing Strategy

### Unit Tests (`tests/test_asciidoc_parser.py`)
- Test heading parsing: `= Title`
- Test admonition parsing: `[NOTE]`
- Test delimited blocks: `****`
- Test mixed content documents

### Integration Tests (`tests/test_asciidoc_integration.py`)
- Test context-aware analysis
- Test format detection
- Test API integration
- Test error handling

## Deployment Steps

1. **Install Dependencies**
   ```bash
   # Option 1: Ruby-based (recommended)
   gem install asciidoctor
   pip install asciidoctor
   
   # Option 2: Python fallback
   pip install asciidoc-py
   ```

2. **Create Files in Order**
   - `src/structural_parsing/types.py` (extend)
   - `src/structural_parsing/asciidoc_parser.py` (new)
   - `src/structural_parsing/parser_factory.py` (extend)
   - `src/context_aware_analyzer.py` (extend)
   - `rules/structure_and_format/admonitions_rule.py` (new)

3. **Update Existing Files**
   - `src/document_processor.py`
   - `app_modules/api_routes.py`
   - `ui/templates/index.html`

4. **Test and Deploy**
   - Run unit tests
   - Test with sample AsciiDoc files
   - Deploy with feature flag
   - Monitor performance

## Quick Validation

Test with this AsciiDoc sample:
```asciidoc
= Installation Guide

[NOTE]
Make sure you have admin privileges.

== Steps

1. Download the installer
2. Run as administrator
3. Follow instructions

[WARNING]
Do not interrupt the process.

----
# Sample code
echo "Hello World"
----
```

Expected parsing results:
- 1 heading (level 1): "Installation Guide"
- 1 heading (level 2): "Steps"
- 2 admonitions: NOTE and WARNING
- 1 paragraph with procedure steps
- 1 code listing

## Troubleshooting

### Common Issues
1. **Parser not found**: Install asciidoctor gem or python package
2. **Format detection fails**: Add explicit format hints
3. **Admonitions not parsed**: Check bracket syntax `[NOTE]`
4. **Performance issues**: Use regex fallback for large files

### Debug Steps
1. Check parser availability with `self._detect_parser_method()`
2. Validate regex patterns with small samples
3. Test format detection logic
4. Verify block type mappings

## Success Metrics

- [ ] AsciiDoc files parse without errors
- [ ] Admonitions are correctly identified and analyzed
- [ ] Context-aware rules apply appropriately
- [ ] Format detection works reliably
- [ ] Performance is acceptable (< 2s for typical documents)
- [ ] No regressions in Markdown functionality

## Next Steps After Implementation

1. Add table parsing support
2. Implement include directive handling
3. Add cross-reference support
4. Optimize parser performance
5. Add more AsciiDoc-specific style rules 

Key Considerations and Suggestions
The following are not criticisms, but rather minor points to consider that may help refine your already excellent plan.
1. Parser Library Choice and Fallback Strategy
Your plan correctly identifies asciidoctor (the Ruby gem) as the primary choice. This is the reference implementation and the most compliant parser available.
Suggestion: Be cautious about using asciidoc-py as a fallback. It is an older library that is not fully compliant with the latest AsciiDoc specification. Relying on it could lead to inconsistent parsing results. It would be better to make the asciidoctor gem a firm dependency for this feature.
Consideration: Your plan for AsciiDocStructuralParser mentions using regex as a fallback if asciidoctor isn't available. It may be better to rely entirely on the external library for parsing and use regex only for the initial, simple format detection in your API routes. Mixing parsing methods (regex vs. a full parser) can introduce hard-to-debug inconsistencies.
2. Performance Implications
The asciidoctor library is typically accessed from Python via a wrapper that calls the Ruby gem as an external process.
Consideration: While this is fine for many applications, be mindful of the performance overhead. For a high-throughput system, repeatedly shelling out to a new process for every analysis could become a bottleneck. Your success metric of < 2s is a good target, but it's worth testing with large documents to ensure you meet it.
3. Format Detection Robustness
The _detect_content_format function is a good start, but its heuristics are simple.
Suggestion: To make the detection more robust, you could look for a few more AsciiDoc-specific patterns. For example, in addition to a leading = or [NOTE], you could check for attribute entries (:author:) or other block delimiters (====, ----) near the top of the document. This would reduce the chance of misidentifying a Markdown file that happens to start with an equals sign.
