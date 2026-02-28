"""Diagnostic script: run the full deterministic pipeline against test.adoc."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Read the test file
with open("test.adoc", "r") as f:
    raw_content = f.read()

print("=" * 80)
print("STEP 1: PARSE THE ASCIIDOC FILE")
print("=" * 80)

from app.services.parsing.asciidoc_parser import AsciidocParser
parser = AsciidocParser()
result = parser.parse(raw_content, "test.adoc")

print(f"\nParser used: {result.metadata.get('parser', 'unknown')}")
print(f"Number of blocks: {len(result.blocks)}")
print(f"\nBlocks:")
for i, block in enumerate(result.blocks):
    content_preview = block.content[:80].replace('\n', '\\n') if block.content else ''
    print(f"  [{i}] type={block.block_type:<25} skip={block.should_skip_analysis}  content={content_preview!r}")

print(f"\n--- PLAIN TEXT sent to analysis ---")
print(result.plain_text)
print(f"--- END PLAIN TEXT ({len(result.plain_text)} chars) ---")

print("\n" + "=" * 80)
print("STEP 2: PREPROCESS AND EXTRACT SENTENCES")
print("=" * 80)

from app.services.analysis.preprocessor import preprocess
prep = preprocess(result.plain_text)

print(f"\nSentences ({len(prep['sentences'])}):")
for i, s in enumerate(prep["sentences"]):
    print(f"  [{i}] {s!r}")

print(f"\nWord count: {prep['word_count']}")

print("\n" + "=" * 80)
print("STEP 3: RUN DETERMINISTIC RULES")
print("=" * 80)

from app.services.analysis.deterministic import analyze as run_deterministic
issues = run_deterministic(
    prep["text"], prep["sentences"], prep["spacy_doc"],
    content_type="concept",
    original_text=prep.get("original_text"),
)

print(f"\nTotal issues found: {len(issues)}")
print()

for i, issue in enumerate(issues):
    print(f"--- Issue {i+1} ---")
    print(f"  Rule:     {issue.rule_name}")
    print(f"  Severity: {issue.severity.value if hasattr(issue.severity, 'value') else issue.severity}")
    print(f"  Flagged:  {issue.flagged_text!r}")
    print(f"  Message:  {issue.message}")
    print(f"  Sentence: {issue.sentence!r}")
    if issue.suggestions:
        print(f"  Suggest:  {issue.suggestions}")
    print()

# Categorize
print("=" * 80)
print("SUMMARY BY RULE TYPE")
print("=" * 80)
from collections import Counter
rule_counts = Counter(issue.rule_name for issue in issues)
for rule, count in rule_counts.most_common():
    print(f"  {rule}: {count}")

print("\n" + "=" * 80)
print("FALSE POSITIVE ANALYSIS")
print("=" * 80)
for i, issue in enumerate(issues):
    flagged = issue.flagged_text
    sentence = issue.sentence
    # Check if the flagged text is actually AsciiDoc syntax
    is_asciidoc_syntax = False
    reasons = []

    if '{' in flagged or '}' in flagged:
        is_asciidoc_syntax = True
        reasons.append("AsciiDoc attribute reference")
    if '::' in flagged or 'xref:' in flagged or 'link:' in flagged or 'image::' in flagged:
        is_asciidoc_syntax = True
        reasons.append("AsciiDoc directive/xref")
    if flagged.startswith('[') or flagged.startswith('.'):
        is_asciidoc_syntax = True
        reasons.append("AsciiDoc metadata/block title")
    if '`' in flagged:
        is_asciidoc_syntax = True
        reasons.append("AsciiDoc inline code")

    # Check if sentence contains AsciiDoc syntax
    if '{' in sentence or '::' in sentence or 'xref:' in sentence:
        is_asciidoc_syntax = True
        reasons.append("Sentence contains AsciiDoc syntax")

    if is_asciidoc_syntax:
        print(f"  LIKELY FALSE POSITIVE [{issue.rule_name}]: {flagged!r}")
        print(f"    Reasons: {', '.join(reasons)}")
        print(f"    Sentence: {sentence!r}")
        print()
