# CEA Rule Refinement Prompt Sheet

> **Purpose**: This document captures all incorrect feedback from users to help refine CEA detection rules. Each entry includes the original detection, user feedback, and recommended rule improvements.
> 
> **Generated**: December 8, 2025  
> **Total Incorrect Feedback**: 56 entries

---

## Table of Contents

1. [Abbreviations](#1-abbreviations)
2. [Ambiguity Detection](#2-ambiguity-detection)
3. [Article Usage](#3-article-usage)
4. [Colon Usage](#4-colon-usage)
5. [Comma Usage](#5-comma-usage)
6. [Conjunctions & Parallelism](#6-conjunctions--parallelism)
7. [Headings](#7-headings)
8. [List Punctuation](#8-list-punctuation)
9. [Prepositions](#9-prepositions)
10. [Second Person Usage](#10-second-person-usage)
11. [Sentence Length](#11-sentence-length)
12. [Slash Usage](#12-slash-usage)
13. [Spacing](#13-spacing)
14. [Technical Commands](#14-technical-commands)
15. [Technical Keyboard Keys](#15-technical-keyboard-keys)
16. [Verb Usage](#16-verb-usage)
17. [Word Usage Rules](#17-word-usage-rules)

---

## 1. Abbreviations

### Issue: False positives for previously defined acronyms

| Field | Value |
|-------|-------|
| **Error Message** | Consider defining 'SBOM' on first use if it's not widely known. |
| **Confidence** | 0.53 |
| **User Feedback** | "The acronym was defined earlier in the document, so the usage here is correct." |

| Field | Value |
|-------|-------|
| **Error Message** | Consider defining 'VEX' on first use if it's not widely known. |
| **Confidence** | 0.57 |
| **User Feedback** | "The acronym 'VEX' is defined before stating the acronym." |

| Field | Value |
|-------|-------|
| **Error Message** | Consider defining 'UI' on first use if it's not widely known. |
| **Confidence** | 0.53 |
| **User Feedback** | (No comment provided) |

### 🔧 Rule Refinement Prompt

```
RULE: abbreviations
CURRENT BEHAVIOR: Flags acronyms that appear without definition in the analyzed text block.

PROBLEM: The rule does not track document context - acronyms defined earlier in the document are flagged again on subsequent uses.

REFINEMENT NEEDED:
1. Implement document-level acronym tracking - maintain a list of defined acronyms throughout the document
2. Only flag an acronym on its FIRST appearance in the document
3. Add common industry acronyms to an allowlist (UI, API, URL, HTML, CSS, etc.)
4. Consider adding a confidence decay - if acronym appears multiple times, it's likely defined

TEST CASES:
- "Software Bill of Materials (SBOM) is important. Later, SBOM analysis shows..." → Should NOT flag second SBOM
- "VEX (Vulnerability Exploitability eXchange) files are used. VEX data helps..." → Should NOT flag second VEX
```

---

## 2. Ambiguity Detection

### Issue: Over-flagging valid pronoun usage

| Field | Value |
|-------|-------|
| **Error Message** | Ambiguous pronoun reference: 'them' |
| **Confidence** | 0.95 |
| **User Feedback** | "Correct usage of the pronoun. See IBM Style Guide pages 27-29." |

| Field | Value |
|-------|-------|
| **Error Message** | Unclear antecedent for pronoun: 'It' |
| **Confidence** | 0.95 |
| **User Feedback** | "Correct usage of the pronoun. See IBM Style Guide pages 27-29." |

| Field | Value |
|-------|-------|
| **Error Message** | Ambiguous pronoun reference: 'their' |
| **Confidence** | 0.95 |
| **User Feedback** | "Correct usage of the pronoun. See IBM Style Guide pages 27-29." |

| Field | Value |
|-------|-------|
| **Error Message** | Ambiguous pronoun reference: 'that' |
| **Confidence** | 0.95 |
| **User Feedback** | "Correct usage of the pronoun. See IBM Style Guide pages 27-29." |

### Issue: Misidentifying common phrases

| Field | Value |
|-------|-------|
| **Error Message** | Risk of adding unverified information: 'work' |
| **Confidence** | 0.95 |
| **User Feedback** | "Not recognizing 'work in progress' as a phrase" |

### Issue: Misinterpreting instructional language

| Field | Value |
|-------|-------|
| **Error Message** | Unsupported claim or promise: 'always' |
| **Confidence** | 0.95 |
| **User Feedback** | "'Always' is used here as an instruction, not as a claim or promise" |

| Field | Value |
|-------|-------|
| **Error Message** | Unsupported claim or promise: 'always' |
| **Confidence** | 0.95 |
| **User Feedback** | "'Always' is not used as a claim or promise here." |

| Field | Value |
|-------|-------|
| **Error Message** | Unsupported claim or promise: 'always' |
| **Confidence** | 0.95 |
| **User Feedback** | "Same as above -- 'always' is not used here to make a claim or promise" |

### 🔧 Rule Refinement Prompt

```
RULE: ambiguity
CURRENT BEHAVIOR: Flags pronouns and words like "always" that may create ambiguity.

PROBLEMS IDENTIFIED:
1. High false positive rate for pronouns when antecedent is clear from context
2. Not recognizing common phrases like "work in progress"
3. Flagging "always" in instructional contexts where it's appropriate

REFINEMENT NEEDED:
1. PRONOUNS: Implement better antecedent detection
   - Check if pronoun has clear antecedent within same or previous sentence
   - Consider sentence structure (subject-verb agreement)
   - Reference IBM Style Guide pages 27-29 for acceptable pronoun patterns

2. PHRASES: Add common phrase recognition
   - "work in progress" - not an ambiguous use of "work"
   - Add phrase dictionary for technical documentation

3. INSTRUCTIONAL "ALWAYS": Distinguish between:
   - Claims: "This product always works" → FLAG
   - Instructions: "Always save your work before closing" → DO NOT FLAG
   - Detection hint: If "always" precedes a verb/action, it's likely instructional

TEST CASES:
- "Configure the settings. It allows customization." → Check if "It" clearly refers to settings
- "Work in progress features..." → Should NOT flag "work"
- "Always back up your data before updating" → Should NOT flag "always"
```

---

## 3. Article Usage

### Issue: False positives with compound nouns and technical terms

| Field | Value |
|-------|-------|
| **Error Message** | Missing article: Singular noun 'work' typically requires an article (a/an/the). |
| **Confidence** | 0.76 |
| **User Feedback** | (No comment provided) |

| Field | Value |
|-------|-------|
| **Error Message** | Consider using 'a' before 'RPM' for standard pronunciation. |
| **Confidence** | 0.61 |
| **User Feedback** | (No comment provided) |

### 🔧 Rule Refinement Prompt

```
RULE: articles
CURRENT BEHAVIOR: Flags missing articles before singular nouns.

PROBLEMS IDENTIFIED:
1. Not recognizing compound nouns or noun phrases where article is optional
2. Incorrect article suggestions for acronyms (pronunciation-based)

REFINEMENT NEEDED:
1. Add exceptions for compound nouns where article is optional
2. For acronyms, determine pronunciation:
   - "RPM" is pronounced letter-by-letter ("ar-pee-em") → use "an RPM"
   - Consider creating acronym pronunciation dictionary

TEST CASES:
- "RPM package" → "an RPM package" (letter pronunciation)
- "Work item tracking" → May not need article depending on context
```

---

## 4. Colon Usage

### Issue: Not accounting for technical documentation patterns

| Field | Value |
|-------|-------|
| **Error Message** | Incorrect colon usage: A colon must be preceded by a complete independent clause. |
| **Confidence** | 0.66 |
| **User Feedback** | "This is an acceptable practice, using a colon at the end of a step that then gives a syntax example, or example output from a command." |

| Field | Value |
|-------|-------|
| **Error Message** | Incorrect colon usage: A colon must be preceded by a complete independent clause. |
| **Confidence** | 0.65 |
| **User Feedback** | "This is a little weird, because it's just followed immediately by a sentence. So the rule makes sense when it's not bolded, monospaced, or just one word, and is followed by a carriage return in our ISG/RHSSG context." |

| Field | Value |
|-------|-------|
| **Error Message** | 📍 Row 3, Column 2 → Incorrect colon usage: A colon must be preceded by a complete independent clause. |
| **Confidence** | 0.80 |
| **User Feedback** | "The comment was great. I'm wondering if you could omit the header as a row count. When it suggested row 3, column 2, I was looking at the content rows, not including the header." |

### 🔧 Rule Refinement Prompt

```
RULE: colons
CURRENT BEHAVIOR: Requires colon to be preceded by complete independent clause.

PROBLEMS IDENTIFIED:
1. Technical documentation often uses colons after step introductions before code/commands
2. Table row counting includes headers, confusing users
3. Context matters: bolded/monospaced text or code blocks after colon is acceptable

REFINEMENT NEEDED:
1. Add exceptions for technical documentation patterns:
   - "Enter the following command:" followed by code block → ACCEPTABLE
   - "Syntax:" followed by code example → ACCEPTABLE
   - Step instructions followed by examples → ACCEPTABLE

2. TABLE REFERENCES: Start row counting from content rows, not headers
   - Current: "Row 3" includes header
   - Desired: "Row 3" = third data row (header is Row 0 or not counted)

3. CONTEXT DETECTION: Check what follows the colon
   - If followed by code block, command, or formatted example → Allow
   - If followed by standard paragraph text → Apply rule

TEST CASES:
- "Run the following command:" + code block → Should NOT flag
- "Syntax:" + syntax example → Should NOT flag
- "The result is: it worked" → SHOULD flag (sentence follows colon)
```

---

## 5. Comma Usage

### Issue: False positives for Oxford comma detection

| Field | Value |
|-------|-------|
| **Error Message** | Missing serial (Oxford) comma before conjunction in a list. |
| **Confidence** | 0.80 |
| **User Feedback** | "I'm seeing comma before 'and'." |

| Field | Value |
|-------|-------|
| **Error Message** | Missing serial (Oxford) comma before conjunction in a list. |
| **Confidence** | 0.81 |
| **User Feedback** | "There are only two parts to this 'list', no comma necessary" |

| Field | Value |
|-------|-------|
| **Error Message** | Missing serial (Oxford) comma before conjunction in a list. |
| **Confidence** | 0.80 |
| **User Feedback** | "There is actually a comma there" |

### 🔧 Rule Refinement Prompt

```
RULE: commas (Oxford comma)
CURRENT BEHAVIOR: Flags lists without Oxford comma before final conjunction.

PROBLEMS IDENTIFIED:
1. Detection failure - flagging when comma IS present
2. Flagging two-item lists (which don't need Oxford comma)
3. Possible parsing issues with complex list structures

REFINEMENT NEEDED:
1. FIX DETECTION: Ensure comma detection is accurate
   - Check character immediately before "and/or" in lists
   - Account for whitespace variations

2. LIST LENGTH CHECK: Only flag for 3+ item lists
   - "apples and oranges" → No comma needed (2 items)
   - "apples, oranges, and bananas" → Comma needed (3 items)
   - "apples, oranges and bananas" → FLAG: missing Oxford comma

3. IMPROVE PARSING: Handle complex list items
   - Items containing "and" within them
   - Items with nested commas

TEST CASES:
- "red, white, and blue" → Should NOT flag (comma present)
- "cats and dogs" → Should NOT flag (only 2 items)
- "apples, oranges and bananas" → SHOULD flag
```

---

## 6. Conjunctions & Parallelism

### Issue: False positives with special characters and proper nouns

| Field | Value |
|-------|-------|
| **Error Message** | Non-parallel structure: 'one' (CD), 'more' (JJR). Use consistent grammatical forms. |
| **Confidence** | 0.54 |
| **User Feedback** | "It seems to misunderstand parallelism if the structure involves words with special characters." |

| Field | Value |
|-------|-------|
| **Error Message** | Non-parallel structure: 'Node.js' (NOMINAL_PROPER_NOUN), 'Go' (base verb). Use consistent grammatical forms. |
| **Confidence** | 0.54 |
| **User Feedback** | "Technically Node.js is not a programming language, so I changed it to JavaScript. However, the suggestion was that the .js part was breaking parallelism." |

### 🔧 Rule Refinement Prompt

```
RULE: conjunctions (parallelism)
CURRENT BEHAVIOR: Flags non-parallel grammatical structures in lists/comparisons.

PROBLEMS IDENTIFIED:
1. Special characters (periods in "Node.js") confuse POS tagging
2. Proper nouns like programming languages misclassified
3. "Go" (programming language) parsed as verb instead of proper noun

REFINEMENT NEEDED:
1. PROPER NOUN HANDLING: Maintain dictionary of technical proper nouns
   - Programming languages: Go, Rust, Python, Node.js, JavaScript, etc.
   - Frameworks: React.js, Vue.js, Angular, etc.
   - Tools: Git, Docker, Kubernetes, etc.

2. SPECIAL CHARACTER HANDLING:
   - Recognize ".js", ".NET", "C++" as part of proper nouns
   - Don't split on periods within known technical terms

3. CONTEXT AWARENESS:
   - In lists of technologies/languages, assume proper noun context
   - "Python, Go, and Rust" → All proper nouns, parallel

TEST CASES:
- "Node.js, Python, and Go" → Should NOT flag (all programming languages)
- "one or more items" → Should NOT flag (valid English construction)
- "writing, reading, and to edit" → SHOULD flag (gerunds + infinitive)
```

---

## 7. Headings

### Issue: Poor replacement suggestions for gerunds

| Field | Value |
|-------|-------|
| **Error Message** | Headings for 'Concept' topics should not start with a gerund. |
| **Confidence** | 0.80 |
| **User Feedback** | "The suggestion of not using a gerund here is fine, but the suggestion is nonsensical, 'Overview of introduce' or 'Introduce Guide' to replace 'Introducing...'" |

### 🔧 Rule Refinement Prompt

```
RULE: headings
CURRENT BEHAVIOR: Flags gerund-starting headings and suggests alternatives.

PROBLEM: Suggestion generation produces grammatically incorrect alternatives.

REFINEMENT NEEDED:
1. IMPROVE SUGGESTION ALGORITHM:
   - "Introducing X" → "Introduction to X" or "X overview" (NOT "Introduce Guide")
   - "Configuring X" → "X configuration" or "How to configure X"
   - "Installing X" → "X installation" or "Installation guide for X"

2. SUGGESTION PATTERNS:
   | Gerund Pattern | Good Alternatives |
   |----------------|-------------------|
   | Introducing X | Introduction to X, X overview, About X |
   | Configuring X | X configuration, Configure X, How to configure X |
   | Understanding X | X concepts, About X, X fundamentals |
   | Managing X | X management, Manage X |

3. VALIDATION: Ensure suggested text is grammatically correct before presenting

TEST CASES:
- "Introducing the new API" → Suggest: "Introduction to the new API" or "New API overview"
- "Configuring authentication" → Suggest: "Authentication configuration" or "Configure authentication"
```

---

## 8. List Punctuation

### Issue: Misidentifying headings as list items

| Field | Value |
|-------|-------|
| **Error Message** | This list item contains a complete sentence and likely needs a period. |
| **Confidence** | 0.52 |
| **User Feedback** | "This is a heading, not a bulleted list. Is there a good way to provide markup in CEA? A lot of suggestions I get are trying to treat headings or code or other special blocks as actual paragraphs." |

### 🔧 Rule Refinement Prompt

```
RULE: list_punctuation
CURRENT BEHAVIOR: Flags list items that appear to be complete sentences without periods.

PROBLEM: Cannot distinguish between list items and headings/other markup.

REFINEMENT NEEDED:
1. MARKUP AWARENESS: Detect document structure
   - Headings (H1-H6, or markup like "##", "===")
   - Code blocks (fenced or indented)
   - Actual bulleted/numbered lists
   
2. EXCLUSION PATTERNS:
   - Lines starting with # (markdown headings) → Exclude
   - Lines in code blocks → Exclude
   - Bold/emphasized standalone lines → Likely headings, exclude

3. USER REQUEST: Consider accepting markup format as input
   - AsciiDoc, Markdown, HTML support
   - Better structural understanding

TEST CASES:
- "## Getting Started" → Should NOT flag (heading)
- "- Install the package" → May or may not need period (depends on style)
- "1. First, configure the settings" → Complete sentence, SHOULD flag
```

---

## 9. Prepositions

### Issue: Over-flagging valid prepositional structures

| Field | Value |
|-------|-------|
| **Error Message** | Sentence has many prepositional phrases (3). Consider simplifying. |
| **Confidence** | 0.47 |
| **User Feedback** | (No comment provided) |

| Field | Value |
|-------|-------|
| **Error Message** | 'click at' is incorrect. Use 'click on' instead. |
| **Confidence** | 0.62 |
| **User Feedback** | (Context issue - no comment) |

### 🔧 Rule Refinement Prompt

```
RULE: prepositions
CURRENT BEHAVIOR: Flags sentences with multiple prepositional phrases and incorrect preposition usage.

PROBLEMS IDENTIFIED:
1. Three prepositional phrases may be acceptable in technical documentation
2. "Click at" flagged but may be valid in certain contexts

REFINEMENT NEEDED:
1. THRESHOLD ADJUSTMENT: 
   - Consider raising threshold from 3 to 4+ prepositional phrases
   - Or add complexity scoring (simple phrases vs. nested phrases)

2. CONTEXT FOR "CLICK":
   - "Click on" - most common, for UI elements
   - "Click at" - may be valid for coordinates/positions
   - "Click in" - for text fields or areas

TEST CASES:
- "Click at position (100, 200)" → Valid use of "at"
- "Click on the button" → Standard usage
- "The file in the folder on the server in the data center" → Flag (too many)
```

---

## 10. Second Person Usage

### Issue: Over-recommending "you" in inappropriate contexts

| Field | Value |
|-------|-------|
| **Error Message** | 'Operator' could be replaced with 'you' for more personal communication. |
| **Confidence** | 0.42 |
| **User Feedback** | (Marked as unclear) |

| Field | Value |
|-------|-------|
| **Error Message** | Consider using 'you' instead of 'user' to address the user directly. |
| **Confidence** | 0.49 |
| **User Feedback** | (Context issue) |

### 🔧 Rule Refinement Prompt

```
RULE: second_person
CURRENT BEHAVIOR: Suggests replacing role terms with "you" for direct address.

PROBLEMS IDENTIFIED:
1. "Operator" is a specific role, not interchangeable with "you"
2. Context matters: API docs vs. user guides have different conventions
3. Low confidence scores indicate rule uncertainty

REFINEMENT NEEDED:
1. ROLE TERM EXCEPTIONS:
   - Administrator, Operator, Developer → Specific roles, don't replace
   - "the user" in generic context → May suggest "you"
   
2. DOCUMENT TYPE AWARENESS:
   - API documentation: Third person often preferred
   - User guides: Second person preferred
   - Reference docs: Either acceptable

3. CONFIDENCE THRESHOLD: Consider suppressing suggestions below 0.5

TEST CASES:
- "The operator must configure..." → Don't suggest "you" (specific role)
- "Users can click the button" → May suggest "You can click..."
- "The administrator should review" → Don't suggest (specific role)
```

---

## 11. Sentence Length

### Issue: Misidentifying multi-sentence blocks as single sentences

| Field | Value |
|-------|-------|
| **Error Message** | This 35-word sentence is long. Consider breaking it into shorter sentences. |
| **Confidence** | 0.64 |
| **User Feedback** | (Marked as unclear) |

| Field | Value |
|-------|-------|
| **Error Message** | This 52-word sentence is too long and complex. Break it into shorter, clearer sentences. |
| **Confidence** | 0.74 |
| **User Feedback** | "This block is not a single sentence. Maybe CEA is not recognizing the punctuation within the quotes?" |

### 🔧 Rule Refinement Prompt

```
RULE: sentence_length
CURRENT BEHAVIOR: Flags sentences exceeding word count thresholds.

PROBLEM: Sentence boundary detection fails with punctuation inside quotes.

REFINEMENT NEEDED:
1. SENTENCE BOUNDARY DETECTION:
   - Handle punctuation inside quotation marks correctly
   - "He said 'Hello.' Then he left." = 2 sentences
   - Distinguish sentence-ending punctuation from abbreviations

2. QUOTE HANDLING:
   - Quoted text with its own punctuation shouldn't end the containing sentence
   - Example: 'The message "Error: File not found." appears when...' = 1 sentence

3. ACCURATE COUNTING: Only count words in actual single sentence

TEST CASES:
- '"Click OK." The dialog closes.' → 2 sentences, not 1 long sentence
- 'The error "Permission denied." indicates...' → 1 sentence
```

---

## 12. Slash Usage

### Issue: Flagging well-established technical terms

| Field | Value |
|-------|-------|
| **Error Message** | Slash usage may be unclear ('CI/CD'): consider spelling out the relationship for general readers. |
| **Confidence** | 0.58 |
| **User Feedback** | "CI/CD is the common usage for continuous integration and continuous delivery. I would add this to an 'accept' file, assuming you have something similar to Vale." |

| Field | Value |
|-------|-------|
| **Error Message** | Slash usage may be unclear ('NBDE/Clevis'): consider spelling out the relationship for general readers. |
| **Confidence** | 0.59 |
| **User Feedback** | (Context issue) |

### 🔧 Rule Refinement Prompt

```
RULE: slashes
CURRENT BEHAVIOR: Flags slash usage that may be unclear to general readers.

PROBLEM: Flagging industry-standard compound terms.

REFINEMENT NEEDED:
1. ALLOWLIST OF ACCEPTED SLASH TERMS:
   - CI/CD
   - I/O
   - TCP/IP
   - client/server
   - read/write
   - true/false
   - on/off
   - and/or (though often discouraged)

2. USER ACCEPTANCE FILE: Implement Vale-style "accept" functionality
   - Allow users to mark terms as accepted for their project
   - Project-specific allowlist

3. CONTEXT: Technical documentation audience may not need spelling out

TEST CASES:
- "CI/CD pipeline" → Should NOT flag (standard term)
- "I/O operations" → Should NOT flag
- "development/testing" → MAY flag (could be clearer)
```

---

## 13. Spacing

### Issue: False positives for version numbers and formats

| Field | Value |
|-------|-------|
| **Error Message** | This sentence clearly has a missing space after a period. |
| **Confidence** | 0.71 |
| **User Feedback** | "'6.4.1' is a version in the X.Y.Z format, therefore a period is not required." |

| Field | Value |
|-------|-------|
| **Error Message** | This text likely has a missing space after a colon. |
| **Confidence** | 0.63 |
| **User Feedback** | (Context issue) |

| Field | Value |
|-------|-------|
| **Error Message** | This text likely has multiple consecutive spaces between words. |
| **Confidence** | 0.62 |
| **User Feedback** | "This paragraph does not have extra spaces" |

### 🔧 Rule Refinement Prompt

```
RULE: spacing
CURRENT BEHAVIOR: Flags missing spaces after punctuation and multiple consecutive spaces.

PROBLEMS IDENTIFIED:
1. Version numbers (X.Y.Z) incorrectly flagged as missing space after period
2. False positives for multiple spaces that don't exist
3. Time formats (HH:MM) may trigger colon spacing rule

REFINEMENT NEEDED:
1. VERSION NUMBER DETECTION:
   - Pattern: \d+\.\d+(\.\d+)* → Version number, skip
   - Examples: 6.4.1, 2.0, 10.15.7

2. TECHNICAL PATTERNS TO EXCLUDE:
   - IP addresses: 192.168.1.1
   - File extensions: file.txt
   - Domain names: example.com
   - Time formats: 10:30

3. FALSE POSITIVE FIX: Verify multiple spaces actually exist
   - Check raw text, not rendered/processed text
   - Account for HTML entities

TEST CASES:
- "Version 6.4.1 is available" → Should NOT flag
- "Visit example.com for more" → Should NOT flag
- "This  has  extra  spaces" → SHOULD flag
```

---

## 14. Technical Commands

### Issue: Overly broad command verb detection

| Field | Value |
|-------|-------|
| **Error Message** | Avoid using command name 'update' as a verb. IBM Style Guide: 'Do not use a command name as a verb.' |
| **Confidence** | 0.82 |
| **User Feedback** | "In a SQL context, UPDATE is a command, but it's not in most grammatical cases. So I think the ISG is flagging this assuming it's a command and it's not." |

| Field | Value |
|-------|-------|
| **Error Message** | Avoid using command name 'select' as a verb. IBM Style Guide: 'Do not use a command name as a verb.' |
| **Confidence** | 0.82 |
| **User Feedback** | "I think this might be useful in a database context, but the term 'select' is not always a command." |

| Field | Value |
|-------|-------|
| **Error Message** | Avoid using command name 'update' as a verb. |
| **Confidence** | 0.81 |
| **User Feedback** | "It is flagging 'update' but that word does not appear in the sentence. All the verbs are gerunds." |

### 🔧 Rule Refinement Prompt

```
RULE: technical_commands
CURRENT BEHAVIOR: Flags common command names used as verbs (select, update, delete, etc.)

PROBLEMS IDENTIFIED:
1. Rule applies too broadly - "select" and "update" are common English verbs
2. Only problematic in SQL/database documentation context
3. False positive: flagging words not actually in the sentence
4. Gerunds (updating, selecting) may be acceptable

REFINEMENT NEEDED:
1. CONTEXT-AWARE DETECTION:
   - Only apply in database/SQL documentation context
   - Check for nearby SQL keywords (SELECT, UPDATE, FROM, WHERE)
   - If discussing SQL commands specifically, apply rule
   - Otherwise, allow normal verb usage

2. WORD LIST REFINEMENT:
   | Word | Flag in SQL Context | Flag Generally |
   |------|---------------------|----------------|
   | select | Yes | No |
   | update | Yes | No |
   | delete | Maybe | No |
   | insert | Maybe | No |
   | drop | Yes | No |
   | create | Maybe | No |

3. VERIFICATION: Ensure flagged word actually exists in text

4. GERUND HANDLING: Consider allowing gerund forms
   - "Updating the database" vs "Update the database"

TEST CASES:
- "Select an option from the menu" → Should NOT flag (UI context)
- "Use SELECT to query the database" → May flag (SQL context)
- "Update your profile settings" → Should NOT flag (general usage)
- "The UPDATE statement modifies..." → May flag (SQL context)
```

---

## 15. Technical Keyboard Keys

### Issue: Over-broad pattern matching

| Field | Value |
|-------|-------|
| **Error Message** | Technical element 'shifting' requires formatting adjustment for professional documentation. |
| **Confidence** | 0.76 |
| **User Feedback** | "In this context, shifting does not refer to the keyboard" |

### 🔧 Rule Refinement Prompt

```
RULE: technical_keyboard_keys
CURRENT BEHAVIOR: Flags keyboard-related terms for formatting.

PROBLEM: Word "shifting" flagged as keyboard key when used as regular verb.

REFINEMENT NEEDED:
1. CONTEXT DETECTION:
   - "Press Shift" → Keyboard key, format as <kbd>Shift</kbd>
   - "shifting priorities" → Regular verb, don't flag
   - "Shift key" → Keyboard reference, format

2. PATTERN MATCHING:
   - Only flag when preceded by: "press", "hold", "tap", "click"
   - Or when followed by: "key", "button", "+[key]"
   - Don't flag verb forms: shifting, shifted, shifts

3. KEYBOARD KEY LIST: Be explicit about what constitutes a key name
   - Shift, Ctrl, Alt, Enter, Tab, Esc, etc.
   - NOT: shifting, controlling, entering

TEST CASES:
- "Press Shift+Enter" → Flag "Shift" and "Enter" for formatting
- "The workload is shifting" → Should NOT flag
- "Use the Shift key" → Flag for formatting
```

---

## 16. Verb Usage

### Issue: Poor suggestions and context-inappropriate flagging

| Field | Value |
|-------|-------|
| **Error Message** | Sentence may be in the passive voice. Consider using active voice for clarity. |
| **Confidence** | 0.62 |
| **User Feedback** | "Passive voice is acceptable in a prerequisites list. Prerequisites implies things done in the past." |

| Field | Value |
|-------|-------|
| **Error Message** | Consider replacing the weak verb-noun pair 'provide information' with a stronger, more direct verb. |
| **Confidence** | 0.46 |
| **User Feedback** | "The suggestion doesn't suggest a useful word: 'Suggestion: Rewrite using a stronger verb, such as informate.'" |

### 🔧 Rule Refinement Prompt

```
RULE: verbs
CURRENT BEHAVIOR: Flags passive voice and weak verb-noun pairs.

PROBLEMS IDENTIFIED:
1. Passive voice acceptable in certain contexts (prerequisites, descriptions)
2. Suggestion "informate" is not a real word
3. Context matters: reference docs vs. procedures

REFINEMENT NEEDED:
1. PASSIVE VOICE EXCEPTIONS:
   - Prerequisites sections → Allow passive
   - Descriptions of states → Allow passive
   - Procedures/instructions → Prefer active

2. SUGGESTION VALIDATION:
   - Verify suggested words exist in dictionary
   - "provide information" → "inform", "describe", "explain" (NOT "informate")
   - Only suggest real, appropriate alternatives

3. VERB-NOUN REPLACEMENT DICTIONARY:
   | Weak Pair | Good Alternatives |
   |-----------|-------------------|
   | provide information | inform, describe, explain |
   | make a decision | decide |
   | perform an action | act |
   | give assistance | assist, help |

TEST CASES:
- "Prerequisites: Python must be installed" → Don't flag passive
- "The file is created by the system" → May flag, suggest "The system creates the file"
- "provide information about" → Suggest "describe" or "explain" (NOT "informate")
```

---

## 17. Word Usage Rules

### Issue: Poor or circular suggestions

| Field | Value |
|-------|-------|
| **Error Message** | 'key' should not be used as a verb. Use a more specific action word. |
| **Confidence** | 0.70 |
| **User Feedback** | "This is a bad suggestion." |

| Field | Value |
|-------|-------|
| **Error Message** | 'lowercase' could be improved for better clarity. |
| **Confidence** | 0.41 |
| **User Feedback** | "You can't really replace 'lowercase' with 'lowercase'." |

| Field | Value |
|-------|-------|
| **Error Message** | Consider replacing 'perform' with a clearer alternative. |
| **Confidence** | 0.65 |
| **User Feedback** | "It suggests 'run', which would make it 'The pipeline run run the following tasks', which would be redundant and weird." |

| Field | Value |
|-------|-------|
| **Error Message** | Consider replacing 'node' with a clearer alternative. |
| **Confidence** | 0.54 |
| **User Feedback** | (No comment - marked incorrect) |

| Field | Value |
|-------|-------|
| **Error Message** | 'new' could be improved for better clarity. |
| **Confidence** | 0.38-0.39 |
| **User Feedback** | (Multiple instances marked incorrect) |

| Field | Value |
|-------|-------|
| **Error Message** | 'pane' could be improved for better clarity. |
| **Confidence** | 0.35 |
| **User Feedback** | (Marked unclear) |

| Field | Value |
|-------|-------|
| **Error Message** | 'secure' violates style guidelines. Use the recommended alternative. |
| **Confidence** | 0.70 |
| **User Feedback** | "The suggestion has a past participle, which doesn't quite work. The suggestion overall is fine though." |

| Field | Value |
|-------|-------|
| **Error Message** | '-' could be improved for better clarity. |
| **Confidence** | 0.36 |
| **User Feedback** | (Marked incorrect) |

| Field | Value |
|-------|-------|
| **Error Message** | Missing 'that' for clarity after 'find' |
| **Confidence** | 0.54 |
| **User Feedback** | "Adding the word 'that' after 'find' makes the sentence confusing." |

### 🔧 Rule Refinement Prompt

```
RULE: word_usage_* (multiple sub-rules)
CURRENT BEHAVIOR: Suggests alternatives for various words flagged by style guidelines.

PROBLEMS IDENTIFIED:
1. Circular suggestions ("lowercase" → "lowercase")
2. Context-unaware suggestions ("perform" → "run" creating "run run")
3. Low-value flags for common technical terms (node, pane, new)
4. Grammatically incorrect suggestions (wrong verb forms)
5. Flagging punctuation marks as words

REFINEMENT NEEDED:
1. SUGGESTION VALIDATION:
   - Never suggest the same word
   - Check resulting sentence for duplicates
   - Validate grammatical correctness of suggestion

2. CONTEXT-AWARE REPLACEMENT:
   - Check surrounding words before suggesting
   - "pipeline run performs" → Don't suggest "run" (would duplicate)
   - Consider part of speech matching

3. LOW-VALUE RULE SUPPRESSION:
   - Consider suppressing rules with confidence < 0.5
   - "new", "pane", "-" often flagged incorrectly
   
4. TECHNICAL TERM EXCEPTIONS:
   - "node" in Kubernetes/computing context → Valid term
   - "pane" in UI context → Valid term

5. GRAMMAR MATCHING:
   - If original is present tense, suggest present tense
   - If original is past participle, suggest past participle

TEST CASES:
- "lowercase letters" → Should NOT suggest "lowercase" again
- "The pipeline run performs tasks" → Don't suggest "run performs"
- "Create a new file" → "new" is fine here, don't flag
- "Select the left pane" → "pane" is correct UI term
```

---

## Summary: Priority Refinements

### High Priority (High Impact, Common Issues)

1. **Abbreviations**: Implement document-level acronym tracking
2. **Technical Commands**: Add context-awareness for SQL vs. general usage
3. **Spacing**: Add version number and technical pattern detection
4. **Commas**: Fix Oxford comma detection accuracy

### Medium Priority (Moderate Impact)

5. **Ambiguity**: Better pronoun antecedent detection, phrase recognition
6. **Colons**: Add exceptions for technical documentation patterns
7. **Word Usage**: Validate suggestions, prevent circular/duplicate recommendations
8. **Verbs**: Fix suggestion generation (no fake words)

### Lower Priority (Edge Cases)

9. **Sentence Length**: Fix quote punctuation handling
10. **Parallelism**: Better proper noun and special character handling
11. **Headings**: Improve gerund replacement suggestions
12. **Keyboard Keys**: Context-aware detection

---

## Implementation Notes

### Suggested Allowlist File Structure

```yaml
# .cea-accept.yml
abbreviations:
  - UI
  - API
  - CI/CD
  - SBOM
  - VEX

technical_terms:
  - node
  - pane
  - lowercase

slash_terms:
  - CI/CD
  - I/O
  - TCP/IP

programming_languages:
  - Node.js
  - Go
  - Rust
  - Python
```

### Confidence Threshold Recommendations

| Rule Category | Suggested Minimum Confidence |
|---------------|------------------------------|
| ambiguity | 0.85 |
| commas | 0.75 |
| word_usage_* | 0.50 |
| technical_commands | 0.70 (in non-SQL context) |
| spacing | 0.70 |

---

*This document should be reviewed and updated as more feedback is collected.*

