"""
LLM Consumability Rule — Deterministic structural detection.
IBM Style Guide (Page 69): Write content that LLMs can consume effectively.

Checks:
1. Tiny topics (fewer than 5 sentences) — LLMs struggle with very short content
   that lacks context. "RAG implementations can only find information that is
   returned in search results."

Configuration loaded from config/llm_consumability_config.yaml.
"""
import os
import yaml
from typing import List, Dict, Any
from .base_audience_rule import BaseAudienceRule


def _load_config() -> Dict[str, Any]:
    """Load LLM consumability config from YAML."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'llm_consumability_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()

# Minimum sentences per content block for LLM consumability
_MIN_SENTENCES = _CONFIG.get('min_sentences_per_topic', 5)


class LLMConsumabilityRule(BaseAudienceRule):
    """Detects content that is difficult for LLMs to consume effectively."""

    def _get_rule_type(self) -> str:
        return 'llm_consumability'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in (
            'listing', 'literal', 'code_block', 'inline_code',
        ):
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        # Check: Tiny topics (fewer than min_sentences)
        sent_list = list(doc.sents)
        sentence_count = len(sent_list)

        if 0 < sentence_count < _MIN_SENTENCES:
            error = self._create_error(
                sentence=sent_list[0].text if sent_list else text,
                sentence_index=0,
                message=(
                    f"Content block has only {sentence_count} "
                    f"sentence{'s' if sentence_count != 1 else ''}. "
                    f"LLMs perform better with at least "
                    f"{_MIN_SENTENCES} sentences of context. "
                    f"Consider expanding or combining with "
                    f"related content."
                ),
                suggestions=[
                    "Add more context to help LLMs understand "
                    "the topic, or combine with a related topic",
                ],
                severity='low',
                text=text,
                context=context,
                flagged_text=text[:100] + ('...' if len(text) > 100 else ''),
                span=(0, min(len(text), 100)),
            )
            if error:
                errors.append(error)

        return errors
