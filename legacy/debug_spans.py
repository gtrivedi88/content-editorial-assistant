"""Debug script: trace block positions and error spans through the pipeline."""
import sys
import os
import logging
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.WARNING)

# Use the same initialization path as the app
from shared.spacy_singleton import get_spacy_model
from style_analyzer.readability_analyzer import ReadabilityAnalyzer
from style_analyzer.sentence_analyzer import SentenceAnalyzer
from style_analyzer.statistics_calculator import StatisticsCalculator
from style_analyzer.suggestion_generator import SuggestionGenerator
from rules import get_registry
from style_analyzer.structural_analyzer import StructuralAnalyzer

nlp = get_spacy_model()
registry = get_registry(nlp=nlp)
analyzer = StructuralAnalyzer(
    readability_analyzer=ReadabilityAnalyzer(),
    sentence_analyzer=SentenceAnalyzer(nlp),
    statistics_calculator=StatisticsCalculator(),
    suggestion_generator=SuggestionGenerator(),
    rules_registry=registry,
    nlp=nlp,
)

# Load test file
with open('test.adoc', 'r') as f:
    text = f.read()

print(f"=== Document length: {len(text)} chars ===")
print(f"First 200 chars:\n{text[:200]!r}\n")

# Run analysis
from style_analyzer.base_types import AnalysisMode
result = analyzer.analyze_with_blocks(text, format_hint='asciidoc', analysis_mode=AnalysisMode.SPACY_WITH_MODULAR_RULES)

blocks = result.get('structural_blocks', [])
print(f"=== {len(blocks)} top-level blocks ===\n")

def dump_block(block, indent=0):
    prefix = "  " * indent
    btype = block.get('block_type', '?')
    start_pos = block.get('start_pos', 'MISSING')
    raw = (block.get('raw_content') or '')[:80].replace('\n', '\\n')
    errors = block.get('errors', [])
    skip = block.get('should_skip_analysis', False)

    print(f"{prefix}[{btype}] start_pos={start_pos} skip={skip}")
    print(f"{prefix}  raw_content: {raw!r}")

    for err in errors:
        span = err.get('span', '?')
        raw_span = err.get('raw_span', 'MISSING')
        flagged = err.get('flagged_text', '?')
        etype = err.get('type', '?')
        msg = (err.get('message') or '')[:80]

        # Compute what globalSpan would be (same logic as frontend)
        if raw_span != 'MISSING':
            gs = [raw_span[0] + start_pos, raw_span[1] + start_pos]
        elif span != '?':
            gs = [span[0] + start_pos, span[1] + start_pos]
        else:
            gs = '?'

        print(f"{prefix}  ERROR: type={etype}")
        print(f"{prefix}    span={span}  raw_span={raw_span}")
        print(f"{prefix}    globalSpan={gs}")
        print(f"{prefix}    flagged_text={flagged!r}")
        if gs != '?' and isinstance(gs, list):
            s, e = max(0, gs[0]), min(len(text), gs[1])
            doc_text = text[s:e]
            if len(doc_text) > 120:
                doc_text = doc_text[:60] + '...' + doc_text[-60:]
            print(f"{prefix}    actual text at globalSpan: {doc_text!r}")
        print(f"{prefix}    message: {msg}")

    for child in block.get('children', []):
        dump_block(child, indent + 1)

for block in blocks:
    dump_block(block)
    print()
