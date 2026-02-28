"""Analysis service -- orchestrates deterministic and LLM-based content checks.

Public API:
    run_analysis: Full three-phase analysis pipeline.
    calculate_score: Compute quality score from issues.
    preprocess: Text preprocessing and statistics.
    run_deterministic: Deterministic rules engine.
    merge_issues: Issue deduplication and merging.
"""

from app.services.analysis.deterministic import analyze as run_deterministic
from app.services.analysis.merger import merge as merge_issues
from app.services.analysis.orchestrator import analyze as run_analysis
from app.services.analysis.preprocessor import preprocess
from app.services.analysis.scorer import calculate_score

__all__ = [
    "run_analysis",
    "calculate_score",
    "preprocess",
    "run_deterministic",
    "merge_issues",
]
