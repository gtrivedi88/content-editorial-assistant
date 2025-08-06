# Evidence-Based Rule Development Guide
## Complete Workflow for Nuanced Rule Implementation

---

## 🎯 **Overview**

This guide provides the complete workflow for transforming binary rule decisions into sophisticated evidence-based analysis. Use this after completing Level 2 enhancements and confidence.md implementation.

**Goal**: Transform rules from binary True/False decisions to nuanced evidence scoring that adapts to writing context and reduces false positives.

---

## 📋 **Prerequisites**

Before starting rule updates, ensure:

✅ **Level 2 Enhanced Validation Complete** - All rules pass `text` and `context` to `_create_error()`
✅ **confidence.md Implementation Complete** - Universal threshold (0.35), normalized confidence, cleanup done
✅ **Enhanced Validation System Active** - ConfidenceCalculator, ValidationPipeline, ErrorConsolidator working

---

## 🏗️ **Architecture Overview**

### **Evidence-Based Rule Flow:**
```
1. Rule detects potential issue
2. Rule calculates evidence score (0.0-1.0) using nuanced analysis
3. BaseRule._create_error() integrates evidence with enhanced validation
4. ConfidenceCalculator combines evidence + linguistic anchors + context + domain
5. Universal threshold (0.35) filters final result
6. Only high-quality, contextually-appropriate errors surface
```

### **Key Principle:**
**Rules provide evidence strength, not binary decisions. The enhanced validation system handles complexity.**

---

## 🔧 **Rule Update Workflow**

### **Step 1: Identify Current Binary Logic**

Look for these patterns in existing rules:

```python
# BINARY PATTERN TO REPLACE:
def analyze(self, text, sentences, nlp, context):
    errors = []
    for sentence in sentences:
        if self._detect_issue(sentence):  # Binary True/False
            errors.append(self._create_error(...))  # Always same confidence
    return errors
```

### **Step 2: Transform to Evidence-Based Pattern**

Replace with nuanced evidence assessment:

```python
# NEW EVIDENCE-BASED PATTERN:
def analyze(self, text, sentences, nlp, context):
    errors = []
    for sentence in sentences:
        for potential_issue in self._find_potential_issues(sentence):
            # Calculate nuanced evidence score
            evidence_score = self._calculate_[RULE_TYPE]_evidence(
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
                    evidence_score=evidence_score,  # Your nuanced assessment
                    flagged_text=potential_issue.text,
                    span=[potential_issue.idx, potential_issue.idx + len(potential_issue.text)]
                )
                errors.append(error)
    return errors
```

### **Step 3: Implement Evidence Calculation Method**

Create sophisticated evidence assessment:

```python
def _calculate_[RULE_TYPE]_evidence(self, token, sentence, text, context) -> float:
    """
    Calculate evidence score (0.0-1.0) for potential rule violation.
    
    Higher scores indicate stronger evidence of an actual error.
    Lower scores indicate acceptable usage or ambiguous cases.
    
    Args:
        token: The potential issue token/phrase
        sentence: Sentence containing the token
        text: Full document text
        context: Document context (block_type, content_type, etc.)
        
    Returns:
        float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
    """
    evidence_score = 0.0
    
    # === STEP 1: BASE EVIDENCE ASSESSMENT ===
    if self._meets_basic_criteria(token):
        evidence_score = 0.7  # Start with moderate evidence
    else:
        return 0.0  # No evidence, skip this token
    
    # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
    evidence_score = self._apply_linguistic_clues(evidence_score, token, sentence)
    
    # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
    evidence_score = self._apply_structural_clues(evidence_score, token, context)
    
    # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
    evidence_score = self._apply_semantic_clues(evidence_score, token, text, context)
    
    # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
    evidence_score = self._apply_feedback_clues(evidence_score, token, context)
    
    return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
```

---

## 🧠 **Evidence Clue Categories**

### **1. Linguistic Clues (Micro-Level)**

Analyze the token and its immediate grammatical context:

```python
def _apply_linguistic_clues(self, evidence_score, token, sentence):
    """Apply SpaCy-based linguistic analysis clues."""
    
    # Part-of-Speech Analysis
    if token.pos_ == 'VERB':
        if token.tag_ in ['VBD', 'VBN']:  # Past tense/participle
            evidence_score += 0.1  # Often indicates error patterns
        elif token.tag_ == 'VBG':  # Gerund
            evidence_score -= 0.1  # Often acceptable
    
    # Dependency Parsing
    if token.dep_ == 'nsubj':  # Nominal subject
        evidence_score -= 0.2  # "The API is..." - standard usage
    elif token.dep_ == 'compound':  # Compound modifier
        evidence_score -= 0.3  # "API documentation" - technical compound
    elif token.dep_ == 'amod':  # Adjectival modifier
        evidence_score += 0.1  # "API weird" - likely error
    
    # Morphological Features
    if hasattr(token, 'morph') and token.morph:
        if 'Number=Plur' in str(token.morph):
            evidence_score -= 0.1  # Plural forms often acceptable
        if 'Tense=Past' in str(token.morph):
            evidence_score += 0.1  # Past tense misuse
    
    # Named Entity Recognition
    if token.ent_type_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT']:
        evidence_score -= 0.8  # Names/entities are not errors
    elif token.ent_type_ in ['MISC', 'EVENT']:
        evidence_score -= 0.3  # Miscellaneous entities often acceptable
    
    # Capitalization Patterns
    if token.text.isupper() and len(token.text) <= 5:
        evidence_score -= 0.2  # Short all-caps likely acronym
    elif token.text.istitle() and not token.is_sent_start:
        evidence_score += 0.1  # Mid-sentence title case suspicious
    
    # Surrounding Context
    prev_token = token.nbor(-1) if token.i > 0 else None
    next_token = token.nbor(1) if token.i < len(token.doc) - 1 else None
    
    if prev_token and prev_token.text.lower() in ['the', 'a', 'an']:
        evidence_score -= 0.1  # Article + word often acceptable
    
    if next_token and next_token.pos_ == 'PUNCT':
        if next_token.text in ['.', '!', '?']:
            evidence_score += 0.05  # End of sentence context
        elif next_token.text in [',', ';', ':']:
            evidence_score -= 0.05  # Mid-sentence punctuation
    
    return evidence_score
```

### **2. Structural Clues (Meso-Level)**

Analyze document structure and block context:

```python
def _apply_structural_clues(self, evidence_score, token, context):
    """Apply document structure-based clues."""
    
    block_type = context.get('block_type', 'paragraph')
    
    # Heading Context
    if block_type == 'heading':
        heading_level = context.get('block_level', 1)
        if heading_level == 1:  # H1 - Main headings
            evidence_score -= 0.4  # Product names, main concepts
        elif heading_level == 2:  # H2 - Section headings
            evidence_score -= 0.3  # Section-specific terms
        elif heading_level >= 3:  # H3+ - Subsection headings
            evidence_score -= 0.2  # Detailed technical terms
    
    # List Context
    elif block_type in ['ordered_list_item', 'unordered_list_item']:
        evidence_score -= 0.2  # Lists often use shorthand/technical terms
        
        # Nested list items are more technical
        if context.get('list_depth', 1) > 1:
            evidence_score -= 0.1
    
    # Code and Technical Blocks
    elif block_type in ['code_block', 'literal_block']:
        evidence_score -= 0.9  # Code blocks have different rules
    elif block_type == 'inline_code':
        evidence_score -= 0.7  # Inline code often technical
    
    # Admonition Context
    elif block_type == 'admonition':
        admonition_type = context.get('admonition_type', '').upper()
        if admonition_type in ['NOTE', 'TIP', 'HINT']:
            evidence_score -= 0.3  # More conversational tone
        elif admonition_type in ['WARNING', 'CAUTION', 'DANGER']:
            evidence_score -= 0.1  # Still formal but contextual
        elif admonition_type in ['IMPORTANT', 'ATTENTION']:
            evidence_score += 0.0  # Neutral adjustment
    
    # Table Context
    elif block_type in ['table_cell', 'table_header']:
        evidence_score -= 0.3  # Tables often use abbreviated terms
    
    # Quote/Citation Context
    elif block_type in ['block_quote', 'citation']:
        evidence_score -= 0.2  # Quotes may use different style
    
    # Sidebar/Callout Context
    elif block_type in ['sidebar', 'callout']:
        evidence_score -= 0.2  # Side content often less formal
    
    return evidence_score
```

### **3. Semantic Clues (Macro-Level)**

Analyze meaning and content type:

```python
def _apply_semantic_clues(self, evidence_score, token, text, context):
    """Apply semantic and content-type clues."""
    
    content_type = context.get('content_type', 'general')
    
    # Content Type Adjustments
    if content_type == 'technical':
        evidence_score -= 0.2  # Technical content more permissive
        
        # Check for technical indicators nearby
        if self._has_technical_context_words(token, distance=10):
            evidence_score -= 0.1  # API, SDK, JSON, etc. nearby
            
    elif content_type == 'academic':
        evidence_score -= 0.1  # Academic writing has different norms
        
    elif content_type == 'legal':
        evidence_score += 0.1  # Legal writing stricter
        
    elif content_type == 'marketing':
        evidence_score -= 0.3  # Marketing more creative/flexible
        
    elif content_type == 'narrative':
        evidence_score -= 0.2  # Storytelling context
    
    # Domain-Specific Terminology
    domain = context.get('domain', 'general')
    if domain in ['software', 'engineering', 'devops']:
        evidence_score -= 0.2  # Technical domains more permissive
    elif domain in ['finance', 'legal', 'medical']:
        evidence_score += 0.1  # Formal domains stricter
    
    # Document Length Context
    doc_length = len(text.split())
    if doc_length < 100:  # Short documents
        evidence_score -= 0.1  # More permissive for brief content
    elif doc_length > 5000:  # Long documents
        evidence_score += 0.05  # Consistency more important
    
    # Audience Level
    audience = context.get('audience', 'general')
    if audience in ['expert', 'developer']:
        evidence_score -= 0.2  # Expert audience expects technical terms
    elif audience in ['beginner', 'general']:
        evidence_score += 0.1  # General audience needs clearer language
    
    return evidence_score
```

### **4. Feedback Pattern Clues (Learning System)**

Apply patterns learned from user feedback:

```python
def _apply_feedback_clues(self, evidence_score, token, context):
    """Apply clues learned from user feedback patterns."""
    
    # Load cached feedback patterns
    feedback_patterns = self._get_cached_feedback_patterns()
    
    # Consistently Accepted Terms
    if token.text.lower() in feedback_patterns.get('accepted_terms', set()):
        evidence_score -= 0.5  # Users consistently accept this
    
    # Consistently Rejected Suggestions
    if token.text.lower() in feedback_patterns.get('rejected_suggestions', set()):
        evidence_score += 0.3  # Users consistently reject flagging this
    
    # Pattern: Short acronyms in technical context
    if (len(token.text) <= 4 and 
        token.text.isupper() and 
        context.get('content_type') == 'technical'):
        
        # Check historical acceptance rate
        acceptance_rate = feedback_patterns.get('short_acronym_acceptance', 0.7)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance, likely valid
    
    # Pattern: Industry-specific terms
    industry = context.get('industry', 'general')
    industry_terms = feedback_patterns.get(f'{industry}_accepted_terms', set())
    if token.text.lower() in industry_terms:
        evidence_score -= 0.3
    
    # Pattern: Context-specific acceptance
    block_type = context.get('block_type', 'paragraph')
    context_patterns = feedback_patterns.get(f'{block_type}_patterns', {})
    
    if token.text.lower() in context_patterns.get('accepted', set()):
        evidence_score -= 0.2
    elif token.text.lower() in context_patterns.get('flagged', set()):
        evidence_score += 0.2
    
    # Pattern: Frequency-based adjustment
    term_frequency = feedback_patterns.get('term_frequencies', {}).get(token.text.lower(), 0)
    if term_frequency > 10:  # Commonly seen term
        acceptance_rate = feedback_patterns.get('term_acceptance', {}).get(token.text.lower(), 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Frequently accepted
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Frequently rejected
    
    return evidence_score

def _get_cached_feedback_patterns(self):
    """Load feedback patterns from cache or feedback analysis."""
    # This would load from feedback analysis system
    # For now, return basic patterns
    return {
        'accepted_terms': set(),
        'rejected_suggestions': set(),
        'short_acronym_acceptance': 0.7,
        'term_frequencies': {},
        'term_acceptance': {},
        'paragraph_patterns': {'accepted': set(), 'flagged': set()},
        'heading_patterns': {'accepted': set(), 'flagged': set()},
        'code_patterns': {'accepted': set(), 'flagged': set()},
    }
```

---

## 📁 **Files That Need Updates**

### **Core Rule Files (Primary Updates)**

All rule files in these directories will need evidence-based transformation:

#### **Language and Grammar Rules:**
- `rules/language_and_grammar/abbreviations_rule.py`
- `rules/language_and_grammar/adverbs_only_rule.py`
- `rules/language_and_grammar/anthropomorphism_rule.py`
- `rules/language_and_grammar/articles_rule.py`
- `rules/language_and_grammar/capitalization_rule.py`
- `rules/language_and_grammar/conjunctions_rule.py`
- `rules/language_and_grammar/contractions_rule.py`
- `rules/language_and_grammar/inclusive_language_rule.py`
- `rules/language_and_grammar/passive_voice_analyzer.py` ⚠️
- `rules/language_and_grammar/plurals_rule.py`
- `rules/language_and_grammar/possessives_rule.py`
- `rules/language_and_grammar/prefixes_rule.py`
- `rules/language_and_grammar/prepositions_rule.py`
- `rules/language_and_grammar/pronouns_rule.py`
- `rules/language_and_grammar/spelling_rule.py`
- `rules/language_and_grammar/terminology_rule.py`
- `rules/language_and_grammar/verbs_rule.py`

#### **Word Usage Rules:**
- `rules/word_usage/a_words_rule.py` through `rules/word_usage/z_words_rule.py`
- `rules/word_usage/special_chars_rule.py`

#### **Punctuation Rules:**
- `rules/punctuation/colons_rule.py`
- `rules/punctuation/commas_rule.py`
- `rules/punctuation/dashes_rule.py`
- `rules/punctuation/ellipses_rule.py`
- `rules/punctuation/exclamation_points_rule.py`
- `rules/punctuation/hyphens_rule.py`
- `rules/punctuation/parentheses_rule.py`
- `rules/punctuation/periods_rule.py`
- `rules/punctuation/punctuation_and_symbols_rule.py`
- `rules/punctuation/quotation_marks_rule.py`
- `rules/punctuation/semicolons_rule.py`
- `rules/punctuation/slashes_rule.py`

#### **Structure and Format Rules:**
- `rules/structure_and_format/admonitions_rule.py`
- `rules/structure_and_format/glossaries_rule.py`
- `rules/structure_and_format/headings_rule.py`
- `rules/structure_and_format/highlighting_rule.py`
- `rules/structure_and_format/lists_rule.py`
- `rules/structure_and_format/messages_rule.py`
- `rules/structure_and_format/notes_rule.py`
- `rules/structure_and_format/paragraphs_rule.py`
- `rules/structure_and_format/procedures_rule.py`

#### **Technical Elements Rules:**
- `rules/technical_elements/commands_rule.py`
- `rules/technical_elements/files_and_directories_rule.py`
- `rules/technical_elements/keyboard_keys_rule.py`
- `rules/technical_elements/mouse_buttons_rule.py`
- `rules/technical_elements/programming_elements_rule.py`
- `rules/technical_elements/ui_elements_rule.py`
- `rules/technical_elements/web_addresses_rule.py`

#### **Numbers and Measurement Rules:**
- `rules/numbers_and_measurement/currency_rule.py`
- `rules/numbers_and_measurement/dates_and_times_rule.py`
- `rules/numbers_and_measurement/numbers_rule.py`
- `rules/numbers_and_measurement/numerals_vs_words_rule.py`
- `rules/numbers_and_measurement/units_of_measurement_rule.py`

#### **References Rules:**
- `rules/references/citations_rule.py`
- `rules/references/geographic_locations_rule.py`
- `rules/references/names_and_titles_rule.py`
- `rules/references/product_names_rule.py`
- `rules/references/product_versions_rule.py`

#### **Legal Information Rules:**
- `rules/legal_information/claims_rule.py`
- `rules/legal_information/company_names_rule.py`
- `rules/legal_information/personal_information_rule.py`

#### **Audience and Medium Rules:**
- `rules/audience_and_medium/conversational_style_rule.py`
- `rules/audience_and_medium/global_audiences_rule.py`
- `rules/audience_and_medium/llm_consumability_rule.py`
- `rules/audience_and_medium/tone_rule.py`

#### **Top-Level Rules:**
- `rules/sentence_length_rule.py`
- `rules/second_person_rule.py`

### **Supporting Files That May Need Updates**

#### **Base Classes (Update Pattern Methods):**
- `rules/base_rule.py` - Add evidence score handling in `_create_error()`
- `rules/language_and_grammar/base_language_rule.py` - Add common linguistic clue methods
- `rules/word_usage/base_word_usage_rule.py` - Add word-specific evidence patterns
- `rules/punctuation/base_punctuation_rule.py` - Add punctuation context clues
- `rules/structure_and_format/base_structure_rule.py` - Add structural clue methods
- `rules/technical_elements/base_technical_rule.py` - Add technical context clues
- `rules/numbers_and_measurement/base_numbers_rule.py` - Add numeric context clues
- `rules/references/base_references_rule.py` - Add reference validation clues
- `rules/legal_information/base_legal_rule.py` - Add legal context clues
- `rules/audience_and_medium/base_audience_rule.py` - Add audience awareness clues

#### **Configuration Files:**
- `rules/rule_mappings.yaml` - May need updates for evidence-based rules
- `validation/config/confidence_weights.yaml` - Evidence score weighting (if needed)

#### **Feedback System Files (For Future Learning):**
- `app_modules/feedback_storage.py` - Store evidence-specific feedback
- `validation/feedback/` (directory) - Feedback analysis for pattern learning

### **Files to Remove (Legacy Cleanup)**

Remove these legacy components that will no longer be needed:

#### **Legacy Confidence Code:**
- Any hardcoded confidence calculations in individual rules
- Legacy threshold management code
- Old binary decision patterns

#### **Deprecated Validation Components:**
- Remove any rule-specific confidence overrides
- Remove content-type specific threshold configurations
- Remove legacy error filtering logic

---

## 🧪 **Testing Strategy**

### **Test After Each Rule Update**

Since evidence-based changes may significantly alter rule behavior, test rigorously:

#### **1. Unit Tests (Per Rule)**
```python
# test_evidence_based_[rule_name].py

def test_evidence_calculation_range():
    """Test evidence scores are in valid range [0.0, 1.0]"""
    
def test_high_evidence_scenarios():
    """Test scenarios that should produce high evidence scores"""
    
def test_low_evidence_scenarios():
    """Test scenarios that should produce low evidence scores"""
    
def test_context_sensitivity():
    """Test evidence varies appropriately with context"""
    
def test_linguistic_clue_application():
    """Test linguistic clues affect evidence correctly"""
    
def test_structural_clue_application():
    """Test structural clues affect evidence correctly"""
    
def test_semantic_clue_application():
    """Test semantic clues affect evidence correctly"""
```

#### **2. Integration Tests (Per Rule)**
```python
def test_enhanced_validation_integration():
    """Test rule works with enhanced validation system"""
    
def test_confidence_calculation_flow():
    """Test evidence flows through ConfidenceCalculator correctly"""
    
def test_universal_threshold_filtering():
    """Test universal threshold filters appropriately"""
    
def test_error_consolidation_compatibility():
    """Test rule works with ErrorConsolidator"""
```

#### **3. Regression Tests (System-Wide)**
```python
def test_no_false_positive_increase():
    """Verify evidence-based rules don't increase false positives"""
    
def test_error_count_stability():
    """Verify error counts remain reasonable"""
    
def test_performance_impact():
    """Verify evidence calculation doesn't hurt performance"""
    
def test_backward_compatibility():
    """Verify existing functionality still works"""
```

#### **4. Real Document Tests**
```python
def test_real_document_analysis():
    """Test with actual technical documents"""
    
def test_diverse_writing_styles():
    """Test with different technical writing approaches"""
    
def test_context_variation():
    """Test with various document structures"""
```

### **Performance Benchmarks**

Monitor these metrics during rule updates:

- **Analysis Time**: Evidence calculation should add <10ms per rule
- **Memory Usage**: Evidence methods should not increase memory significantly  
- **Error Quality**: False positive rate should decrease
- **Error Count**: Total errors should remain reasonable
- **Cache Hit Rate**: Evidence calculations should cache effectively

---

## 📊 **Success Metrics**

### **Per-Rule Success Criteria:**

- ✅ **Evidence Range**: All evidence scores between 0.0-1.0
- ✅ **Context Sensitivity**: Evidence varies appropriately with context
- ✅ **False Positive Reduction**: Fewer inappropriate flags
- ✅ **Performance**: <10ms additional processing time
- ✅ **Integration**: Works seamlessly with enhanced validation

### **System-Wide Success Criteria:**

- ✅ **Overall False Positive Reduction**: 20-40% decrease expected
- ✅ **Error Quality Improvement**: Higher precision, maintained recall
- ✅ **Context Adaptation**: Same text, different contexts, appropriate handling
- ✅ **Performance Stability**: <20% increase in total analysis time
- ✅ **Threshold Effectiveness**: Universal threshold (0.35) works across all rules

---

## 🔄 **Development Process**

### **Recommended Update Order:**

1. **Start with High-Impact Rules** (most common false positives)
   - `abbreviations_rule.py`
   - `adverbs_only_rule.py` 
   - `pronouns_rule.py`
   - `terminology_rule.py`

2. **Move to Grammar Rules** (linguistic clues)
   - `articles_rule.py`
   - `prepositions_rule.py`
   - `conjunctions_rule.py`
   - `verbs_rule.py`

3. **Update Structural Rules** (context clues)
   - `headings_rule.py`
   - `lists_rule.py`
   - `admonitions_rule.py`
   - `paragraphs_rule.py`

4. **Complete Specialized Rules** (domain clues)
   - Technical elements rules
   - Legal information rules
   - Numbers and measurement rules

### **Per-Rule Update Process:**

1. **Analyze Current Binary Logic**
2. **Identify False Positive Patterns**
3. **Design Evidence Calculation Method**
4. **Implement Linguistic, Structural, Semantic Clues**
5. **Add Feedback Pattern Support**
6. **Update Tests**
7. **Performance Test**
8. **Integration Test**
9. **Real Document Validation**
10. **Monitor for 1-2 Days**
11. **Move to Next Rule**

---

## 🎯 **Key Implementation Notes**

### **Critical Requirements:**

1. **Always Use Level 2 Enhanced Validation**: Pass `text` and `context` to `_create_error()`
2. **Evidence Score Range**: Always return 0.0-1.0 from evidence methods
3. **Graceful Degradation**: Handle missing context gracefully
4. **Performance Conscious**: Cache expensive computations
5. **Test Thoroughly**: Each rule change affects system behavior

### **Common Pitfalls to Avoid:**

- ❌ **Don't return binary True/False** - Always calculate evidence scores
- ❌ **Don't hardcode confidence values** - Let enhanced validation handle it
- ❌ **Don't ignore context** - Always consider structural and semantic clues
- ❌ **Don't over-engineer** - Start simple, add complexity as needed
- ❌ **Don't skip testing** - Rule changes can have unexpected effects

### **Best Practices:**

- ✅ **Start with conservative evidence scores** - Err on the side of lower scores initially
- ✅ **Log evidence scores during development** - Help understand rule behavior
- ✅ **Use meaningful variable names** - `evidence_score`, not `conf` or `val`
- ✅ **Comment clue logic extensively** - Explain why each clue matters
- ✅ **Test with diverse content** - Technical, marketing, academic, legal documents

---

## 🚀 **Expected Outcomes**

After completing evidence-based rule updates:

### **Developer Experience:**
- 🎯 **Focus on Rule Quality**: Spend time improving evidence logic, not threshold tuning
- 🧠 **Contextual Intelligence**: Rules that understand nuanced writing contexts
- 🔧 **Maintainable Code**: Clear evidence logic easier to understand and improve
- 📊 **Data-Driven Improvement**: Feedback patterns guide rule enhancement

### **User Experience:**
- ✅ **Fewer False Positives**: Context-aware rules reduce inappropriate flags
- 🎪 **Consistent Quality**: Universal threshold provides consistent filtering
- 📝 **Respect Writing Style**: Rules adapt to different technical writing approaches
- 🚀 **Continuous Improvement**: Rules get smarter with user feedback

### **System Characteristics:**
- 🏗️ **Adaptive Architecture**: Rules that learn and improve over time
- ⚡ **Performance Stable**: Evidence calculation adds minimal overhead
- 🔒 **Production Ready**: Robust, tested, reliable rule system
- 🌟 **World-Class Quality**: Comparable to professional language tools

---

*This guide represents the complete transformation from binary rule decisions to sophisticated, context-aware evidence assessment. Use it as your comprehensive reference during the rule update process.*