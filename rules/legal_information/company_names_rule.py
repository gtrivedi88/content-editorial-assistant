"""
Company Names Rule
Based on IBM Style Guide topic: "Company names"
"""
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule

class CompanyNamesRule(BaseLegalRule):
    """
    Checks that company names are referred to by their full legal name
    where appropriate.
    """
    def _get_rule_type(self) -> str:
        return 'legal_company_names'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for proper company name usage (full legal name on first use).
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        # Known companies and typical legal suffixes (expand in real system)
        companies = {"Oracle", "Microsoft", "Red Hat"}
        suffixes = {
            "Corp", "Corporation", "Inc", "Incorporated", "LLC", "Ltd", "PLC", "GmbH",
            "S.A.", "NV", "Co.", "Limited"
        }

        doc = nlp(text)
        doc_sents = list(doc.sents)

        # Track first sentence index per company mention
        first_sent_index = {}
        for idx, s in enumerate(doc_sents):
            for e in s.ents:
                if e.label_ == 'ORG' and e.text in companies and e.text not in first_sent_index:
                    first_sent_index[e.text] = idx

        for i, sent in enumerate(doc_sents):
            for ent in sent.ents:
                if ent.label_ != 'ORG' or ent.text not in companies:
                    continue

                # Check if a legal suffix immediately follows the entity
                has_suffix = False
                if ent.end < len(doc):
                    following = doc[ent.end].text.strip('.')
                    if following in suffixes:
                        has_suffix = True

                if has_suffix:
                    continue

                is_first_mention = i == first_sent_index.get(ent.text, i)

                ev = self._calculate_company_name_evidence(
                    ent=ent, is_first_mention=is_first_mention, sent=sent, text=text, context=context or {}
                )
                if ev > 0.1:
                    message = self._get_contextual_company_name_message(ent.text, ev, is_first_mention, context or {})
                    suggestions = self._generate_smart_company_name_suggestions(ent.text, ev, is_first_mention, context or {})

                    span_start = ent.start_char
                    span_end = ent.end_char
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i if i < len(sentences) else -1,
                        message=message,
                        suggestions=suggestions,
                        severity='low' if ev < 0.7 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=ev,
                        span=(span_start, span_end),
                        flagged_text=ent.text
                    ))
        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_company_name_evidence(self, ent, is_first_mention: bool, sent, text: str, context: dict) -> float:
        """Calculate evidence (0.0-1.0) that a company name needs legal suffix here."""
        # Base: higher if first mention
        evidence: float = 0.75 if is_first_mention else 0.4

        # Linguistic clues
        evidence = self._apply_linguistic_clues_company_names(evidence, ent, is_first_mention, sent)

        # Structural clues
        evidence = self._apply_structural_clues_company_names(evidence, context)

        # Semantic clues
        evidence = self._apply_semantic_clues_company_names(evidence, text, context)

        # Feedback clues
        evidence = self._apply_feedback_clues_company_names(evidence, ent, context)

        return max(0.0, min(1.0, evidence))

    # === CLUE METHODS ===

    def _apply_linguistic_clues_company_names(self, ev: float, ent, is_first_mention: bool, sent) -> float:
        sent_lower = sent.text.lower()

        # Possessive or attributive use often indicates subsequent mentions
        if any(t.text == "'s" and t.i == ent.end for t in sent):
            ev -= 0.1

        # If sentence already contains a legal suffix elsewhere (appositive), reduce
        legal_suffix_markers = {"inc", "corp", "corporation", "llc", "ltd", "plc", "gmbh"}
        if any(tok.text.strip('.').lower() in legal_suffix_markers for tok in sent):
            ev -= 0.1

        # Headings or short sentences reduce necessity (handled also structurally)
        token_count = len([t for t in sent if not t.is_space])
        if token_count < 6 and not is_first_mention:
            ev -= 0.05

        return ev

    def _apply_structural_clues_company_names(self, ev: float, context: dict) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return ev - 0.8
        if block_type == 'inline_code':
            return ev - 0.6
        if block_type in {'table_cell', 'table_header'}:
            ev -= 0.05
        if block_type in {'heading', 'title'}:
            ev -= 0.1
        return ev

    def _apply_semantic_clues_company_names(self, ev: float, text: str, context: dict) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # Legal and marketing contexts stricter on first use
        if content_type in {'legal', 'marketing'}:
            ev += 0.15
        if content_type in {'technical', 'api', 'procedural'}:
            ev += 0.05

        if domain in {'legal', 'finance'}:
            ev += 0.1

        if audience in {'beginner', 'general'}:
            ev += 0.05

        return ev

    def _apply_feedback_clues_company_names(self, ev: float, ent, context: dict) -> float:
        patterns = self._get_cached_feedback_patterns_company_names()
        name = ent.text
        if name in patterns.get('often_accepted_without_suffix', set()):
            ev -= 0.2
        ctype = (context or {}).get('content_type', 'general')
        pc = patterns.get(f'{ctype}_patterns', {})
        if name in pc.get('accepted', set()):
            ev -= 0.1
        if name in pc.get('flagged', set()):
            ev += 0.1
        return ev

    def _get_cached_feedback_patterns_company_names(self) -> dict:
        return {
            'often_accepted_without_suffix': {"Microsoft", "Oracle"},  # common usage
            'marketing_patterns': {
                'accepted': set(),
                'flagged': {"Red Hat"}
            },
            'technical_patterns': {
                'accepted': {"Red Hat"},
                'flagged': set()
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_company_name_message(self, company: str, ev: float, is_first: bool, context: dict) -> str:
        if ev > 0.85:
            return f"Company name '{company}' should include its full legal name on first use."
        if ev > 0.6:
            return f"Consider writing the full legal name for '{company}' on first use."
        return f"Prefer using the full legal name for '{company}' on first mention."

    def _generate_smart_company_name_suggestions(self, company: str, ev: float, is_first: bool, context: dict) -> List[str]:
        suggestions: List[str] = []
        suggestions.append(f"Use the full legal name on first use, e.g., '{company} Inc.' or '{company} Corporation'.")
        if not is_first:
            suggestions.append("If this is not the first mention, consider keeping this usage but ensure the first mention includes the legal suffix.")
        suggestions.append("Follow subsequent mentions with the short name once the full legal name has been introduced.")
        return suggestions[:3]
