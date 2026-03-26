"""
Verbs Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Pages 113-116): Use present tense, active voice. Avoid future tense.
"""

from typing import List, Dict, Any, Optional
from .base_language_rule import BaseLanguageRule

# Citation auto-loaded from style_guides/ibm/ibm_style_mapping.yaml by BaseRule

# Lemmas where passive voice is standard technical phrasing and should not be flagged.
# Original CEA exceptions + Vale PassiveVoice + state-of-being categories.
_STATE_OF_BEING_LEMMAS: frozenset = frozenset({
    # Original CEA exceptions
    'require', 'recommend', 'expect', 'need', 'design', 'intend', 'base',
    # Vale PassiveVoice exceptions
    'deprecate', 'display', 'import', 'interest', 'support', 'test', 'trust',
    # State-of-being location/storage
    'install', 'instal', 'store', 'locate', 'deploy', 'host', 'mount', 'place',
    # State-of-being status
    'configure', 'enable', 'disable', 'activate', 'deactivate',
    'distribute', 'license', 'certify', 'surface',
    # State-of-being detection/result
    'detect', 'discover', 'find', 'determine', 'observe',
    # Release notes patterns
    'fix', 'add', 'remove', 'resolve', 'address', 'update',
    'optimize', 'optimise', 'improve', 'enhance', 'reduce',
    'consolidate', 'streamline', 'migrate', 'introduce',
})

# Action verbs where passive is acceptable in reference docs and release notes
# but should be flagged in procedures and concepts.
_REFERENCE_OK_PASSIVE: frozenset = frozenset({
    'list', 'describe', 'document', 'specify', 'define', 'include',
    'associate', 'relate', 'connect', 'link', 'bind', 'map',
    'push', 'publish', 'release', 'ship',
    'build', 'provide', 'package',
})


class VerbsRule(BaseLanguageRule):
    """Detects passive voice and future tense using SpaCy dependency parsing."""

    def __init__(self):
        super().__init__()

    def _get_rule_type(self) -> str:
        return 'verbs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in ['listing', 'literal', 'code_block', 'inline_code']:
            return []
        if not nlp and not spacy_doc:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for i, sent in enumerate(doc.sents):
            errors.extend(self._check_passive_voice(sent, i, text, context))
            errors.extend(self._check_future_tense(sent, i, text, context))

        return errors

    # --- Passive voice: SpaCy marks auxpass dependency ---

    @staticmethod
    def _is_passive_exempt(sent_text: str, main_verb, context: Optional[Dict]) -> bool:
        """Check whether passive voice is acceptable for this verb in context."""
        if sent_text.lower().startswith(('error:', 'warning:', 'caution:', 'note:', 'important:')):
            return True
        if context and context.get('block_type') in ['dlist', 'description_list']:
            return True
        if main_verb.lemma_ in _STATE_OF_BEING_LEMMAS:
            return True
        if main_verb.lemma_ in _REFERENCE_OK_PASSIVE:
            content_type = context.get('content_type') if context else None
            if content_type in ('reference', 'release_notes'):
                return True
        return False

    def _check_passive_voice(self, sent, sent_index: int, text: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        errors = []
        for token in sent:
            if token.dep_ != 'auxpass':
                continue

            main_verb = token.head
            sent_text = sent.text.strip()

            if self._is_passive_exempt(sent_text, main_verb, context):
                continue

            suggestion = self._suggest_active(sent, main_verb)
            errors.append(self._create_error(
                sentence=sent.text,
                sentence_index=sent_index,
                message="Use active voice instead of passive.",
                suggestions=[suggestion],
                severity='medium',
                text=text,
                context=context,
                flagged_text=f"{token.text} {main_verb.text}",
                span=(token.idx, main_verb.idx + len(main_verb.text))
            ))
            break  # One passive voice error per sentence is enough

        return errors

    def _suggest_active(self, sent, main_verb) -> str:
        """Build an active-voice suggestion from the passive agent.

        Falls back to a generic message when no agent is found or
        when the extracted agent is not a valid sentence subject
        (e.g., a gerund like 'removing' from 'optimized by removing').
        """
        agent_token = None
        for child in main_verb.children:
            if child.dep_ == 'agent':
                for grandchild in child.children:
                    if grandchild.dep_ == 'pobj':
                        agent_token = grandchild
                        break
        if agent_token is not None:
            # Guard: only suggest when the agent is a noun/proper noun,
            # not a gerund (VBG) or other non-subject POS.
            if agent_token.tag_ in ('NN', 'NNP', 'NNS', 'NNPS', 'PRP'):
                return (
                    f"Consider: '{agent_token.text} "
                    f"{main_verb.lemma_}s ...' (active voice)"
                )
        return (
            "Rewrite in active voice: make the actor "
            "the subject of the sentence."
        )

    # --- Future tense: "will" + verb ---

    def _check_future_tense(self, sent, sent_index: int, text: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        errors = []
        for token in sent:
            if token.lemma_ != 'will' or token.pos_ != 'AUX':
                continue

            # Guard: conditional "will" ("If you click Save, the file will be saved")
            if any(t.lemma_ == 'if' for t in sent):
                continue

            # Guard: "will" in quoted text or UI labels
            if context and context.get('block_type') in ['quote', 'blockquote']:
                continue

            main_verb = token.head
            errors.append(self._create_error(
                sentence=sent.text,
                sentence_index=sent_index,
                message="Use present tense instead of future tense ('will').",
                suggestions=[f"Rewrite using present tense: '{main_verb.lemma_}s' instead of 'will {main_verb.text}'."],
                severity='low',
                text=text,
                context=context,
                flagged_text=f"will {main_verb.text}",
                span=(token.idx, main_verb.idx + len(main_verb.text))
            ))
            break  # One future tense error per sentence

        return errors
