# Editorial Assistant Enhancement Implementation Plan

## Overview

This document outlines the comprehensive enhancement plan for the editorial assistant to detect additional writing mistakes, formatting issues, and general editorial improvements. 

**🏗️ IMPORTANT**: All enhancements will seamlessly integrate with the existing sophisticated architecture documented in:
- **`confidence.md`**: Universal threshold (0.35), normalized confidence scoring, ConfidenceCalculator, ValidationPipeline, ErrorConsolidator
- **`evidence_based_rule_development.md`**: Evidence-based scoring (0.0-1.0), surgical zero false positive guards, rule-specific evidence calculation
- **`level_2_implementation.adoc`**: Level 2 enhanced validation with `text` and `context` parameters to `_create_error()`

## Current Architecture Integration

The enhancements will build upon the **production-ready enhanced validation system**:
- **Level 2 Enhanced Validation**: All new rules will pass `text` and `context` to `_create_error()` 
- **Evidence-Based Analysis**: Transform binary True/False decisions to nuanced evidence scoring (0.0-1.0)
- **Universal Threshold**: Use established threshold (0.35) instead of rule-specific thresholds
- **Surgical Guards**: Implement zero false positive guards following proven Language & Grammar patterns
- **Enhanced Error Creation**: Leverage existing ConfidenceCalculator and ValidationPipeline infrastructure

## 1. Spacing and Whitespace Detection

### 1.1 New Rule: `spacing_rule.py`

**Location**: `rules/punctuation/spacing_rule.py`

**Capabilities**:
- **Double Spaces**: Detect multiple consecutive spaces between words
- **Extra Whitespace**: Identify unnecessary spaces at line beginnings/endings
- **Inconsistent Spacing**: Check spacing around punctuation marks
- **Missing Spaces**: Detect missing spaces after periods, commas, colons
- **Tab vs Space Issues**: Inconsistent indentation characters

**Detection Patterns**:
```python
{
    'double_spaces': r'\S\s{2,}\S',  # Multiple spaces between non-whitespace
    'trailing_spaces': r'\s+$',       # Spaces at end of lines
    'leading_spaces': r'^\s+\S',      # Unnecessary leading spaces
    'missing_space_after_period': r'\.\w',
    'missing_space_after_comma': r',\w',
    'space_before_punctuation': r'\s+[,.;:!?]'
}
```

**Evidence Scoring**:
- Double spaces: 0.9 (high confidence)
- Missing spaces after punctuation: 0.8
- Trailing spaces: 0.7
- Context adjustments for code blocks, technical documentation

### 1.2 Configuration File

**Location**: `rules/punctuation/config/spacing_patterns.yaml`

```yaml
spacing_violations:
  double_spaces:
    pattern: "\\S\\s{2,}\\S"
    evidence: 0.9
    severity: "medium"
    message: "Multiple consecutive spaces detected"
    
  missing_space_after_period:
    pattern: "\\.\\w"
    evidence: 0.8
    severity: "medium"
    message: "Missing space after period"
    
context_exceptions:
  code_blocks: -0.8  # Very permissive in code
  technical_commands: -0.6
  file_paths: -0.7
```

## 2. Enhanced Periods Detection

### 2.1 Extend Existing `periods_rule.py`

**New Capabilities**:
- **Duplicate Periods**: Detect sequences like ".." or "..."
- **Extra Periods**: Unnecessary periods in lists, headings
- **Missing Periods**: Sentence endings without periods
- **Context-Aware Period Rules**: Different rules for different content types

**Additional Patterns**:
```python
{
    'duplicate_periods': r'\.{2,}(?!\.\.))',  # Exclude legitimate ellipses
    'unnecessary_period_in_heading': r'^#{1,6}.*\.$',
    'missing_sentence_period': r'[a-z]\s*\n',
    'period_in_list_item': r'^\s*[-*+]\s+.*\.$'
}
```

**Evidence Calculation Enhancements**:
- Consider document structure (headings, lists, paragraphs)
- Adjust for writing style (technical vs. narrative)
- Account for abbreviations and technical terms

## 3. List Punctuation Rules

### 3.1 New Rule: `list_punctuation_rule.py`

**Location**: `rules/structure_and_format/list_punctuation_rule.py`

**Capabilities**:
- **Ordered List Periods**: Detect when periods are needed/unnecessary
- **Unordered List Periods**: Same for bullet points
- **Consistency Checking**: Ensure uniform punctuation across list items
- **Fragment vs. Sentence Detection**: Different rules based on content type

**List Item Classification**:
```python
def classify_list_item(self, item_text: str) -> str:
    """
    Classify list items as:
    - 'sentence': Complete sentences (should have periods)
    - 'fragment': Phrases/words (periods optional)
    - 'mixed': Lists with both types (needs consistency)
    """
```

**Detection Logic**:
- Analyze grammatical structure using spaCy
- Check for verbs, complete thoughts
- Ensure consistency within the same list
- Context-aware suggestions based on list purpose

### 3.2 Configuration

**Location**: `rules/structure_and_format/config/list_punctuation.yaml`

```yaml
list_punctuation_rules:
  ordered_lists:
    sentences_need_periods: true
    fragments_optional_periods: true
    consistency_required: true
    
  unordered_lists:
    sentences_need_periods: true
    fragments_no_periods: true
    
  context_adjustments:
    procedural_steps: 0.2    # More strict for procedures
    feature_lists: -0.3     # More permissive for feature lists
```

## 4. Indentation Detection

### 4.1 New Rule: `indentation_rule.py`

**Location**: `rules/structure_and_format/indentation_rule.py`

**Capabilities**:
- **Incorrect Indentation Levels**: Detect non-standard indentation
- **Mixed Indentation**: Tabs vs. spaces inconsistency
- **Accidental Indentation**: Unintentional leading spaces
- **Context-Aware Validation**: Different rules for different content types

**Detection Patterns**:
```python
{
    'mixed_indentation': r'^(\t+ +| +\t+)',  # Mixed tabs and spaces
    'odd_indentation': r'^[ ]{1}[^ ]|^[ ]{3}[^ ]|^[ ]{5}[^ ]',  # Odd number of spaces
    'excessive_indentation': r'^[ ]{9,}[^ ]',  # More than 8 spaces
    'accidental_single_space': r'^[ ]{1}[A-Z]'  # Single space before capital letter
}
```

**Context Considerations**:
- Code blocks should be excluded
- List items have expected indentation
- Quote blocks may have intentional indentation
- Different standards for AsciiDoc vs. Markdown

## 5. Admonition Content Validation

### 5.1 New Rule: `admonition_content_rule.py`

**Location**: `rules/structure_and_format/admonition_content_rule.py`

**Capabilities**:
- **Code Block Detection**: Flag code blocks within NOTE/IMPORTANT/WARNING
- **Inappropriate Content**: Detect content that doesn't belong in admonitions
- **Admonition Structure**: Validate proper admonition formatting
- **Content Type Validation**: Ensure content matches admonition type

**Detection Logic**:
```python
def analyze_admonition_content(self, admonition_type: str, content: str) -> List[Dict]:
    """
    Detect inappropriate content in admonitions:
    - Code blocks (backticks, code fences)
    - Complex procedures (belongs in procedure modules)
    - Long explanations (belongs in concept modules)
    - Tables or complex formatting
    """
```

**Prohibited Content Patterns**:
```python
{
    'code_blocks': r'```[\s\S]*?```|`[^`]+`',
    'procedure_steps': r'^\d+\.\s+',
    'complex_tables': r'\|.*\|.*\|',
    'excessive_length': lambda text: len(text.split()) > 100
}
```

## 6. General Writing Mistakes Detection

### 6.1 New Rule: `general_writing_rule.py`

**Location**: `rules/language_and_grammar/general_writing_rule.py`

**Capabilities**:

**Basic Text Issues**:
- **Repeated Words**: Detect duplicate words (e.g., "the the")
- **Extra Commas**: Identify unnecessary comma usage
- **Missing Commas**: Detect missing commas in series (Oxford comma)
- **Inconsistent Capitalization**: Pattern analysis
- **Run-on Sentences**: Sentence length and complexity analysis
- **Misplaced Apostrophes**: Common apostrophe errors

**Grammar Issues**:
- **Subject-Verb Disagreement**: Detect mismatched subjects and verbs
- **Sentence Fragments**: Identify incomplete sentences
- **Comma Splices**: Incorrect joining of independent clauses
- **Double Negatives**: Detect and suggest corrections
- **Dangling Modifiers**: Flag unclear modifying phrases

**Word Usage Issues**:
- **Common Word Confusions**: affect/effect, its/it's, then/than, your/you're
- **Misused Contractions**: "should of" → "should have"
- **Preposition Errors**: "different than" → "different from"
- **Redundancy Detection**: "very unique" → "unique"
- **Weak Verb Overuse**: Excessive use of "is", "are", "was", "were"

**Style and Clarity Issues**:
- **Parallel Structure**: Inconsistent grammatical patterns in lists
- **Inconsistent Tense**: Mixed past/present tense usage
- **Unclear Pronoun References**: Ambiguous pronoun antecedents
- **Passive Voice Overuse**: Suggest active voice alternatives
- **Wordiness**: Detect unnecessarily complex phrasing

**Advanced Punctuation**:
- **Semicolon Misuse**: Incorrect semicolon placement
- **Quotation Mark Issues**: Misplaced or inconsistent quote styles
- **Hyphen Problems**: Missing/extra hyphens in compound words

**Detection Patterns**:
```python
{
    # Basic Text Issues
    'repeated_words': r'\b(\w+)\s+\1\b',
    'extra_commas': r',\s*,',
    'missing_oxford_comma': r'\w+,\s+\w+\s+and\s+\w+',
    'misplaced_apostrophe': r"\w+'s\s+\w+",
    'run_on_sentence': lambda sent: len(sent.split()) > 25,
    
    # Grammar Issues
    'sentence_fragment': r'^[A-Z][^.!?]*[^.!?]$',  # No ending punctuation
    'comma_splice': r'\w+,\s+[a-z]+.*\.',  # Independent clauses joined by comma
    'double_negative': r"\b(don't|doesn't|didn't|won't|can't|isn't)\s+(no|nothing|nobody|nowhere)\b",
    
    # Word Usage Issues
    'affect_effect': r'\b(affect|effect)\b',  # Requires context analysis
    'its_its': r"\b(its|it's)\b",
    'then_than': r'\b(then|than)\b',
    'your_youre': r"\b(your|you're)\b",
    'should_of': r'\bshould\s+of\b',
    'could_of': r'\bcould\s+of\b',
    'would_of': r'\bwould\s+of\b',
    'different_than': r'\bdifferent\s+than\b',
    'very_unique': r'\bvery\s+unique\b',
    
    # Style Issues
    'passive_voice': r'\b(was|were|is|are|been)\s+\w+ed\b',
    'weak_verbs': r'\b(is|are|was|were|be|being|been)\s+',
    'inconsistent_tense': 'requires_nlp_analysis',  # Complex pattern
    
    # Advanced Punctuation
    'semicolon_misuse': r';[^A-Z]',  # Semicolon not followed by capital
    'quote_inconsistency': r'["\'"].+?["\''']',  # Mixed quote styles
    'hyphen_compound': r'\b\w+\s+\w+\b',  # Requires compound word dictionary
}
```

**Advanced Detection Requirements**:
- **NLP Analysis**: Subject-verb agreement, tense consistency, pronoun references
- **Dictionary Lookups**: Compound words, common confusables
- **Context Analysis**: Distinguishing correct from incorrect usage
- **Sentiment Analysis**: Detecting unclear or ambiguous phrasing

### 6.2 Implementation Complexity Notes

**Phase 1 (Simple Patterns)**: Basic text issues, some word usage
**Phase 2 (NLP Required)**: Grammar issues, style analysis, advanced punctuation
**Phase 3 (Advanced)**: Context-dependent analysis, semantic understanding

**Dependencies**:
- **spaCy**: Advanced grammar analysis, part-of-speech tagging
- **Custom Dictionaries**: Compound words, confusable word pairs
- **Machine Learning**: Context-dependent corrections
- **Performance Optimization**: Caching for complex analysis

## 7. Configuration and Context Integration

### 7.1 Enhanced Context Guards

**Location**: `rules/enhanced_rules/config/enhanced_context_guards.yaml`

```yaml
enhanced_context_adjustments:
  spacing_rules:
    code_blocks: -0.8  # Very permissive in code
    technical_commands: -0.6
    file_paths: -0.7
    
  indentation_rules:
    code_blocks: -0.9  # Exclude code blocks
    list_items: -0.3   # Permissive for list indentation
    quote_blocks: -0.4 # Allow quote indentation
    
  list_punctuation:
    procedural_steps: 0.2    # More strict for procedures
    feature_lists: -0.3     # More permissive for feature lists
```

### 7.2 Rule Priority Updates

**Location**: `rules/rule_mappings.yaml`

Add new rules to existing priority structure:

```yaml
rule_priorities:
  critical:
    - spacing  # Add to existing critical rules
    - indentation  # Critical for readability
    
  high:
    - list_punctuation
    - admonition_content
    
  medium:
    - general_writing
```

## 8. Integration with Existing Architecture

### 8.1 Adherence to Established Patterns

All editorial enhancements will follow the production-ready architecture documented in:

- **`confidence.md`**: Universal threshold (0.35), normalized confidence scoring, enhanced validation system with ConfidenceCalculator and ValidationPipeline
- **`evidence_based_rule_development.md`**: Evidence-based scoring (0.0-1.0), surgical zero false positive guards, rule-specific evidence calculation methods
- **`level_2_implementation.adoc`**: Level 2 enhanced validation where all rules pass `text` and `context` parameters to `_create_error()`

### 8.2 Evidence-Based Editorial Rules

New editorial rules will implement evidence-based analysis following the proven **Language & Grammar pattern**:

```python
class SpacingRule(BasePunctuationRule):
    """Enhanced spacing detection with evidence-based analysis"""
    
    def analyze(self, text, sentences, nlp, context):
        errors = []
        for sentence in sentences:
            for potential_issue in self._find_spacing_issues(sentence):
                # Calculate evidence score (0.0-1.0) instead of binary True/False
                evidence_score = self._calculate_spacing_evidence(
                    potential_issue, sentence, text, context
                )
                
                # Only create error if evidence suggests it's worth evaluating
                if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                    error = self._create_error(
                        sentence=sentence.text,
                        sentence_index=sentence_index,
                        message=self._get_contextual_message(potential_issue, evidence_score),
                        suggestions=self._generate_smart_suggestions(potential_issue, context),
                        text=text,      # Level 2 ✅
                        context=context, # Level 2 ✅
                        evidence_score=evidence_score,  # Evidence-based ✅
                        flagged_text=potential_issue.text,
                        span=[potential_issue.idx, potential_issue.idx + len(potential_issue.text)]
                    )
                    errors.append(error)
        return errors
    
    def _calculate_spacing_evidence(self, issue, sentence, text, context) -> float:
        """Calculate evidence score following evidence_based_rule_development.md patterns"""
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return 0.0  # Code has its own spacing rules
        
        if self._is_intentional_formatting(issue, sentence, context):
            return 0.0  # Tables, forms, alignment formatting
            
        # === DYNAMIC BASE EVIDENCE SCORING ===
        evidence_score = self._get_base_spacing_evidence(issue, sentence, context)
        
        # === APPLY CLUE CATEGORIES ===
        evidence_score = self._apply_linguistic_clues(evidence_score, issue, sentence)
        evidence_score = self._apply_structural_clues(evidence_score, issue, context)  
        evidence_score = self._apply_semantic_clues(evidence_score, issue, text, context)
        evidence_score = self._apply_feedback_clues(evidence_score, issue, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
```

### 8.3 Universal Threshold Integration

Editorial rules will use the **universal confidence threshold (0.35)** established in `confidence.md`:

- ✅ No rule-specific thresholds needed
- ✅ Enhanced validation system handles filtering automatically  
- ✅ Rules focus on quality evidence calculation, not threshold management
- ✅ ConfidenceCalculator provides normalized confidence scoring

## 9. Testing Strategy

### 9.1 Test Coverage Areas

1. **Unit Tests**: Individual rule functionality
2. **Integration Tests**: Rule interaction and evidence calculation
3. **Enhanced Rules Tests**: Spacing, punctuation, and formatting validation
4. **Performance Tests**: Large document processing
5. **Context Tests**: Different document types and writing styles

### 9.2 Test Data Requirements

- Sample documents with spacing issues
- List formatting examples with various punctuation styles
- Indentation inconsistency examples
- General writing mistake samples
- Edge cases and boundary conditions

## 10. Configuration Management

### 10.1 Rule Configuration Strategy

Each new rule will include:
- Pattern definitions in YAML
- Evidence scoring thresholds
- Context-specific adjustments
- Severity mappings
- Suggestion templates

### 10.2 Customization Options

- Domain-specific rule sets
- Organization-specific requirements
- Configurable strictness levels
- Custom pattern additions

## 11. Performance Considerations

### 11.1 Optimization Strategies

- **Incremental Analysis**: Process only changed content
- **Rule Prioritization**: Run high-impact rules first
- **Caching**: Cache analysis results for unchanged content
- **Parallel Processing**: Analyze independent rules concurrently

### 11.2 Scalability Planning

- Large document support
- Real-time analysis capabilities
- Memory-efficient processing
- Batch processing options

## 12. User Experience Enhancements

### 12.1 Error Reporting

- Clear, actionable error messages
- Context-specific explanations
- Multiple suggestion options
- Confidence indicators

### 12.2 Dashboard Integration

- Enhanced rule scoring
- Progress tracking
- Rule-specific metrics
- Trend analysis

## 13. Future Extensibility

### 13.1 Plugin Architecture

Design rules to support:
- Custom organization standards
- Domain-specific requirements
- Third-party integrations
- Community-contributed rules

### 13.2 Machine Learning Integration

- Pattern learning from user feedback
- Automatic threshold adjustment
- Context-aware rule selection
- Continuous improvement capabilities

## 14. Implementation Timeline

### Phase 1: Core Enhancements (Weeks 1-2)
**Prerequisites**: Ensure `confidence.md` and `level_2_implementation.adoc` are fully implemented
- Spacing rule implementation with evidence-based analysis (0.0-1.0 scoring)
- Enhanced periods detection following surgical zero false positive guards
- List punctuation rules with Level 2 enhanced validation (`text` and `context` parameters)

### Phase 2: Structure Validation (Weeks 3-4)
**Following**: `evidence_based_rule_development.md` patterns for rule-specific evidence calculation
- Indentation detection using universal threshold (0.35) and ConfidenceCalculator
- Admonition content validation with structural and semantic clues
- General writing mistakes using existing enhanced validation system

### Phase 3: Integration and Testing (Weeks 5-6)
**Integration**: With existing ConfidenceCalculator, ValidationPipeline, and ErrorConsolidator
- Rule integration testing with established enhanced validation test patterns
- Performance optimization maintaining <100ms per rule target (existing benchmark)
- Documentation updates following established architectural documentation standards
- User experience refinement through existing feedback storage and analysis system

## 15. Success Metrics

- **Detection Accuracy**: >95% for clear violations
- **False Positive Rate**: <5% for context-aware rules
- **Performance**: <2 seconds for 10,000-word documents
- **User Satisfaction**: Positive feedback on suggestion quality
- **Writing Quality Improvement**: Measurable improvement in document formatting and style

This comprehensive implementation plan ensures that the editorial assistant will become a powerful tool for detecting spacing issues, punctuation problems, indentation errors, and general writing mistakes while preserving the existing architecture's strengths and extensibility.

**Note**: For modular documentation compliance features, refer to the separate `mod_doc_implementation_guide.md` which provides complete end-to-end implementation for Red Hat modular documentation standards.
