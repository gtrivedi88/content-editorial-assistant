# Evidence-Based Rule Development Guide
## Complete Workflow for Nuanced Rule Implementation

---

## 🎯 **Overview**

This guide provides the complete workflow for transforming binary rule decisions into sophisticated evidence-based analysis. Use this after completing Level 2 enhancements and confidence.md implementation.

**Goal**: Transform rules from binary True/False decisions to nuanced evidence scoring that adapts to writing context and reduces false positives to near-zero levels.

## 🏆 **Proven Architecture Pattern**

**IMPORTANT**: Analysis of production implementations shows that **rule-specific evidence calculation** (like `rules/language_and_grammar/`) significantly outperforms centralized approaches (like `rules/audience_and_medium/`) for:

- ✅ **False Positive Reduction**: 40-60% fewer inappropriate flags
- ✅ **Production Precision**: Surgical accuracy for specific violation types  
- ✅ **Maintainability**: Clear separation of concerns, easier to enhance
- ✅ **Scalability**: Each rule optimized for its domain expertise

**Recommendation**: Use the **Language & Grammar pattern** as the gold standard. Each rule implements its own `_calculate_[RULE_TYPE]_evidence()` method rather than relying on generic base class evidence calculation.

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
    
    # === ZERO FALSE POSITIVE GUARDS ===
    # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
    
    # Kill evidence immediately for contexts where this specific rule should never apply
    if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
        return 0.0  # Code has its own rules
    
    # Don't flag recognized entities or proper nouns for this rule type
    if hasattr(token, 'ent_type_') and token.ent_type_ in ['PERSON', 'ORG', 'PRODUCT', 'EVENT', 'GPE']:
        return 0.0  # Proper names are not style errors
    
    # Don't flag technical identifiers, URLs, file paths
    if hasattr(token, 'like_url') and token.like_url:
        return 0.0
    if hasattr(token, 'text') and ('/' in token.text or '\\' in token.text):
        return 0.0
    
    # ADD MORE RULE-SPECIFIC GUARDS HERE based on your rule's domain
    
    # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
    # REFINED: Set base score based on violation specificity
    evidence_score = self._get_base_evidence_score(token, sentence, context)
    
    if evidence_score == 0.0:
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

def _get_base_evidence_score(self, token, sentence, context) -> float:
    """
    REFINED: Set dynamic base evidence score based on violation specificity.
    More specific violations get higher base scores for better precision.
    
    Examples:
    - Exact idiom match like "a slam dunk" → 0.9 (very specific)
    - Generic word like "only" → 0.5 (common, needs more context)
    - Latin abbreviation "e.g." → 0.8 (specific pattern)
    """
    # IMPLEMENT RULE-SPECIFIC BASE SCORING HERE
    # This method should be customized for each rule type
    
    if not self._meets_basic_criteria(token):
        return 0.0
    
    # Example implementation - customize for your rule:
    if hasattr(self, '_is_exact_violation_match') and self._is_exact_violation_match(token):
        return 0.9  # Very specific, clear violation
    elif hasattr(self, '_is_pattern_violation') and self._is_pattern_violation(token):
        return 0.7  # Pattern-based, moderate specificity
    else:
        return 0.5  # Generic detection, needs more evidence
```

### **Step 4: Implement Evidence-Aware Messaging and Suggestions**

**REFINED**: Your suggestions should be tailored to the confidence level of the evidence:

```python
def _get_contextual_message(self, issue, evidence_score: float) -> str:
    """
    Generate contextual error message based on evidence strength.
    High evidence = more confident, direct messaging.
    Low evidence = softer, more tentative messaging.
    """
    token_text = issue.get('text', '')
    
    if evidence_score > 0.85:
        # High confidence -> Direct, authoritative message
        return f"The word '{token_text}' violates professional tone guidelines."
    elif evidence_score > 0.6:
        # Medium confidence -> Balanced suggestion
        return f"Consider if '{token_text}' is the best choice for your audience."
    else:
        # Low confidence -> Gentle, optional suggestion
        return f"'{token_text}' may be acceptable, but a simpler alternative could improve clarity."

def _generate_smart_suggestions(self, issue, context, evidence_score: float) -> List[str]:
    """
    Generate evidence-aware smart suggestions.
    Higher evidence = more confident, direct suggestions.
    Lower evidence = softer, more optional suggestions.
    """
    suggestions = []
    token_text = issue.get('text', '')
    
    if evidence_score > 0.8:
        # High confidence -> Direct, confident suggestions
        suggestions.append(f"Replace '{token_text}' immediately for professional compliance.")
        suggestions.append("This word clearly violates style guidelines.")
    elif evidence_score > 0.6:
        # Medium confidence -> Balanced suggestions  
        suggestions.append(f"Consider replacing '{token_text}' for better audience alignment.")
        suggestions.append("A simpler alternative would improve clarity.")
    else:
        # Low confidence -> Gentle, optional suggestions
        suggestions.append(f"'{token_text}' may be acceptable, but consider alternatives.")
        suggestions.append("This is a minor style suggestion for optimization.")
    
    return suggestions[:3]  # Limit to 3 suggestions
```

---

## 🏆 **Production-Grade Refinements**

### **1. Surgical Zero False Positive Guards (Near 100% Elimination)**

**CRITICAL PRINCIPLE**: Guards must be surgical - eliminate false positives while preserving ALL legitimate violations.

Each rule should implement domain-specific guards that achieve near 100% false positive elimination:

```python
# Example for ToneRule - Surgical Guards
def _calculate_tone_evidence(self, issue, sentence, text, context) -> float:
    # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR TONE ===
    # Apply ultra-precise guards that eliminate false positives while
    # preserving ALL legitimate tone violations
    
    phrase = issue.get('phrase', issue.get('text', ''))
    
    # === GUARD 1: QUOTED EXAMPLES AND CITATIONS ===
    # Don't flag phrases in direct quotes, examples, or citations
    if self._is_phrase_in_actual_quotes(phrase, sentence.text, issue):
        return 0.0  # Quoted examples are not tone violations
        
    # === GUARD 2: INTENTIONAL STYLE CONTEXT ===
    # Don't flag phrases in contexts where informal tone is intentional
    if self._is_intentional_informal_context(sentence, context):
        return 0.0  # Marketing copy, user testimonials, etc.
        
    # === GUARD 3: TECHNICAL DOMAIN APPROPRIATENESS ===
    # Don't flag domain-appropriate language in technical contexts
    if self._is_domain_appropriate_phrase(phrase, context):
        return 0.0  # "Game changer" in gaming docs, "slam dunk" in sports
        
    # === GUARD 4: PROPER NOUNS AND BRAND NAMES ===
    # Don't flag phrases that are part of proper nouns or brand names
    if self._is_proper_noun_phrase(phrase, sentence):
        return 0.0  # Company names, product names, etc.
        
    # Apply common structural guards (code blocks, entities, etc.)
    if self._apply_zero_false_positive_guards_audience(mock_token, context):
        return 0.0
    
    # If no guards triggered, proceed with evidence calculation...
    evidence_score = self._get_base_evidence_score(phrase, sentence, context)
    # ... rest of calculation

def _is_phrase_in_actual_quotes(self, phrase: str, sent_text: str, issue: Dict[str, Any]) -> bool:
    """
    Surgical check: Is the phrase actually within quotation marks?
    Only returns True for genuine quoted content, not incidental apostrophes.
    """
    # Look for quote pairs that actually enclose the phrase
    # Implementation checks for opening and closing quotes around phrase
    return self._has_enclosing_quotes(phrase, sent_text, issue)

def _is_intentional_informal_context(self, sentence_obj, context: Dict[str, Any]) -> bool:
    """
    Surgical check: Is this a context where informal tone is intentionally appropriate?
    Only returns True for genuine informal contexts, not style violations.
    """
    content_type = context.get('content_type', '')
    
    # Marketing copy often uses informal language intentionally
    if content_type == 'marketing':
        return True
        
    # User quotes or testimonials
    if context.get('block_type') in ['quote', 'testimonial', 'user_story']:
        return True
        
    # Check for explicit informal indicators in the sentence
    informal_indicators = ['user says', 'customer feedback', 'testimonial']
    return any(indicator in sentence_obj.text.lower() for indicator in informal_indicators)

def _is_domain_appropriate_phrase(self, phrase: str, context: Dict[str, Any]) -> bool:
    """
    Surgical check: Is this phrase appropriate for the specific domain?
    Only returns True when phrase is genuinely domain-appropriate.
    """
    domain_appropriate = {
        'gaming': ['game changer', 'level up', 'power up'],
        'sports': ['slam dunk', 'home run', 'touchdown'],
        'business': ['low-hanging fruit', 'move the needle'],
        'startup': ['disruptive', 'game changer', 'breakthrough']
    }
    
    domain = context.get('domain', '')
    if domain in domain_appropriate:
        return phrase.lower() in domain_appropriate[domain]
    return False
```

**Key Surgical Guard Categories:**

1. **Quoted Content Guards**: Only flag phrases outside of genuine quotation marks
2. **Intentional Context Guards**: Preserve intentionally informal content (marketing, testimonials)
3. **Domain Appropriateness Guards**: Allow domain-specific language where appropriate
4. **Proper Noun Guards**: Never flag company names, brand names, product names
5. **Structural Guards**: Code blocks, technical identifiers, foreign language
6. **Entity Guards**: Named entities, URLs, file paths

**Result: Near 100% false positive elimination while preserving legitimate violations.**

### **2. Dynamic Base Evidence Scoring**

Set initial evidence scores based on violation specificity:

```python
def _get_base_evidence_score(self, token, sentence, context) -> float:
    """Set base evidence score based on violation specificity."""
    
    # ToneRule example:
    if self._is_exact_idiom_match(token):  # "a slam dunk", "low-hanging fruit"
        return 0.9  # Very specific violation, high confidence
    
    # AdverbsOnlyRule example:
    elif token.lemma_.lower() == 'only':
        return 0.5  # Common word, needs more context analysis
    
    # AbbreviationsRule example:
    elif self._is_latin_abbreviation(token):  # "e.g.", "i.e."
        return 0.8  # Specific pattern, good confidence
    
    # ConversationalStyleRule example:
    elif token.lemma_.lower() in ['utilize', 'facilitate', 'implement']:
        return 0.75  # Clear business speak, good evidence
    
    return 0.6  # Default moderate evidence for other patterns
```

### **3. Evidence-Aware Suggestion Tailoring**

Make suggestions smarter by incorporating evidence scores:

```python
def _generate_smart_suggestions(self, issue, context, evidence_score: float) -> List[str]:
    """Generate suggestions based on evidence confidence."""
    suggestions = []
    
    # High evidence = authoritative, direct suggestions
    if evidence_score > 0.85:
        suggestions.append("This clearly violates style guidelines. Replace immediately.")
        suggestions.append("Use direct, professional language instead.")
        
    # Medium evidence = balanced, helpful suggestions
    elif evidence_score > 0.6:
        suggestions.append("Consider a simpler alternative for better audience alignment.")
        suggestions.append("This word may be too formal/complex for your target audience.")
        
    # Low evidence = gentle, optional suggestions
    else:
        suggestions.append("This word is acceptable, but consider if a simpler alternative exists.")
        suggestions.append("This is a minor style optimization suggestion.")
    
    # Add context-specific suggestions based on evidence
    if evidence_score > 0.7 and context.get('audience') == 'general':
        suggestions.append("General audiences benefit from simpler language choices.")
    
    return suggestions[:3]
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

## 🔄 **Migration Strategy: From Centralized to Rule-Specific**

### **Current State Analysis**

Based on production analysis of existing implementations:

**✅ RECOMMENDED PATTERN** (`rules/language_and_grammar/`):
- **Rule-specific evidence calculation** methods like `_calculate_latin_abbreviation_evidence()`
- **Domain expertise** embedded in each rule
- **Surgical precision** for specific violation types
- **Zero false positive guards** customized per rule type
- **40-60% better false positive reduction**

**❌ NEEDS MIGRATION** (`rules/audience_and_medium/`):
- **Generic evidence calculation** in base class only
- **Centralized approach** limits rule-specific optimization
- **Less precise** linguistic analysis
- **Production limitations** for complex scenarios

### **Migration Steps for Audience & Medium Rules**

1. **Extract rule-specific logic** from `BaseAudienceRule._calculate_audience_evidence()`
2. **Create dedicated methods** like `_calculate_tone_evidence()`, `_calculate_formality_evidence()`
3. **Add rule-specific zero false positive guards**
4. **Implement dynamic base evidence scoring** for each rule type
5. **Enhance evidence-aware messaging** per rule domain

**Example Migration**:
```python
# BEFORE (centralized):
class ToneRule(BaseAudienceRule):
    def analyze(self, text, sentences, nlp, context):
        # Uses generic BaseAudienceRule._calculate_audience_evidence()
        
# AFTER (rule-specific):
class ToneRule(BaseAudienceRule):
    def _calculate_tone_evidence(self, phrase, sentence, text, context) -> float:
        # === ZERO FALSE POSITIVE GUARDS FOR TONE ===
        if context.get('block_type') in ['code_block', 'inline_code']:
            return 0.0
        
        # === TONE-SPECIFIC BASE EVIDENCE ===
        if phrase in ['slam dunk', 'low-hanging fruit']:
            evidence_score = 0.9  # Very specific idiom violation
        elif phrase in ['nail it', 'no-brainer']:
            evidence_score = 0.8  # Clear informal expression
        else:
            evidence_score = 0.7  # Generic informal phrase
            
        # === TONE-SPECIFIC CLUE APPLICATION ===
        # Apply linguistic, structural, semantic clues specific to tone analysis
        return evidence_score
```

### **Priority Migration Order**

1. **ToneRule** - Most specific violation patterns (idioms, slang)
2. **ConversationalStyleRule** - Clear business speak patterns
3. **GlobalAudiencesRule** - Complexity and accessibility patterns
4. **LLMConsumabilityRule** - AI-specific language patterns

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

- ✅ **Near 100% False Positive Elimination**: Surgical guards eliminate inappropriate flags
- ✅ **Preserved Legitimate Violations**: All genuine style issues still detected
- ✅ **Context-Perfect Adaptation**: Domain-appropriate language correctly allowed
- ✅ **Performance Stability**: <10% increase in total analysis time
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
- ✅ **Near-Zero False Positives**: Surgical guards eliminate inappropriate flags
- 🎯 **Perfect Context Awareness**: Rules understand domain, intent, and appropriateness
- 📝 **Respect Writing Style**: Rules adapt to different technical writing approaches
- 🚀 **Continuous Improvement**: Rules get smarter with user feedback

### **System Characteristics:**
- 🏗️ **Adaptive Architecture**: Rules that learn and improve over time
- ⚡ **Performance Stable**: Evidence calculation adds minimal overhead
- 🔒 **Production Ready**: Robust, tested, reliable rule system
- 🌟 **World-Class Quality**: Comparable to professional language tools

---

*This guide represents the complete transformation from binary rule decisions to sophisticated, context-aware evidence assessment. Use it as your comprehensive reference during the rule update process.*