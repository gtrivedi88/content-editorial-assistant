"""
Claims and Recommendations Rule
Based on IBM Style Guide topic: "Claims and recommendations"
"""
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ClaimsRule(BaseLegalRule):
    """
    Checks for unsupported claims and subjective words that could have
    legal implications, such as "secure," "easy," or "best practice."
    """
    def _get_rule_type(self) -> str:
        return 'legal_claims'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for legally risky claims (subjective/absolute terms).
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        
        doc = nlp(text)

        # Linguistic Anchor: subjective/absolute claim terms
        claim_words = {
            "secure", "easy", "effortless", "best practice", "future-proof",
            "guaranteed", "bulletproof", "always", "never"
        }

        for i, sent in enumerate(doc.sents):
            for word in claim_words:
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', sent.text, re.IGNORECASE):
                    char_start = sent.start_char + match.start()
                    char_end = sent.start_char + match.end()
                    matched_text = match.group(0)

                    token = None
                    for t in sent:
                        if t.idx == char_start and t.idx + len(t.text) == char_end:
                            token = t
                            break

                    evidence_score = self._calculate_claim_evidence(
                        matched_text, token, sent, text, context or {}
                    )

                    if evidence_score > 0.1:
                        suggestions = self._generate_contextual_suggestions(matched_text.lower(), sent)
                        message = self._get_contextual_claim_message(matched_text, evidence_score, context or {})
                        severity = 'medium' if evidence_score < 0.75 else 'high'
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=message,
                            suggestions=suggestions,
                            severity=severity,
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(char_start, char_end),
                            flagged_text=matched_text
                        ))
        return errors
    
    def _generate_contextual_suggestions(self, word: str, sentence) -> List[str]:
        """Generate context-aware suggestions using spaCy morphological analysis."""
        suggestions = []
        
        # Context-specific replacements using linguistic patterns
        if word == "easy":
            # Analyze surrounding context for better suggestions
            if any(token.lemma_ in ["process", "step", "procedure"] for token in sentence):
                suggestions.append("Replace with 'straightforward' or 'simple'")
                suggestions.append("Example: 'This is a straightforward process'")
            elif any(token.lemma_ in ["use", "configure", "setup"] for token in sentence):
                suggestions.append("Replace with 'quick' or 'direct'")
                suggestions.append("Example: 'This provides a direct setup method'")
            else:
                suggestions.append("Replace with 'accessible' or 'user-friendly'")
        
        elif word == "future-proof":
            # Check if it's about technology/architecture
            if any(token.lemma_ in ["system", "architecture", "design", "solution"] for token in sentence):
                suggestions.append("Replace with 'scalable' or 'adaptable'")
                suggestions.append("Example: 'This is a scalable solution'")
            elif any(token.lemma_ in ["process", "approach", "method"] for token in sentence):
                suggestions.append("Replace with 'sustainable' or 'long-term'")
                suggestions.append("Example: 'This is a sustainable approach'")
            else:
                suggestions.append("Replace with 'durable' or 'robust'")
        
        elif word == "secure":
            suggestions.append("Replace with 'security-enhanced' or specify the security feature")
            suggestions.append("Example: 'encrypted' or 'access-controlled'")
        
        elif word == "best practice":
            suggestions.append("Replace with 'recommended approach' or 'standard method'")
            suggestions.append("Example: 'Use the recommended configuration'")
        
        elif word == "effortless":
            if any(token.lemma_ in ["install", "setup", "configure"] for token in sentence):
                suggestions.append("Replace with 'automated' or 'streamlined'")
                suggestions.append("Example: 'automated installation'")
            else:
                suggestions.append("Replace with 'smooth' or 'simplified'")
        
        # Fallback suggestion if no specific context found
        if not suggestions:
            suggestions.append(f"Replace '{word}' with a more specific, objective description")
            suggestions.append("Describe the actual feature or benefit instead of using subjective language")
        
        return suggestions

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_claim_evidence(self, term: str, token, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that a term is an unsupported/subjective claim."""
        evidence: float = 0.65  # base for claim terms

        # Linguistic clues
        evidence = self._apply_linguistic_clues_claims(evidence, term, token, sentence)

        # Structural clues
        evidence = self._apply_structural_clues_claims(evidence, context)

        # Semantic clues
        evidence = self._apply_semantic_clues_claims(evidence, term, text, context)

        # Feedback clues
        evidence = self._apply_feedback_clues_claims(evidence, term, context)

        return max(0.0, min(1.0, evidence))

    # === CLUE METHODS ===

    def _apply_linguistic_clues_claims(self, ev: float, term: str, token, sentence) -> float:
        sent = sentence
        sent_lower = sent.text.lower()

        # Presence of objective qualifiers reduces risk
        qualifiers = {"per nist", "per iso", "according to", "evidence", "benchmark", "metrics", "data", "tested"}
        if any(q in sent_lower for q in qualifiers):
            ev -= 0.2

        # Presence of numbers/metrics reduces risk slightly
        has_number = any(getattr(t, 'like_num', False) for t in sent)
        if has_number:
            ev -= 0.05

        # Hedging reduces severity
        hedges = {"can", "may", "typically", "designed to", "helps", "aims to"}
        if any(t.lemma_.lower() in hedges for t in sent):
            ev -= 0.1

        # Absolutes increase severity
        absolutes = {"always", "never", "guarantee", "guaranteed", "completely"}
        if any(t.lemma_.lower() in absolutes for t in sent):
            ev += 0.15

        # Quotes/reporting reduce severity
        if '"' in sent.text or "'" in sent.text:
            ev -= 0.05

        return ev

    def _apply_structural_clues_claims(self, ev: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return ev - 0.8
        if block_type == 'inline_code':
            return ev - 0.6
        if block_type in {'table_cell', 'table_header'}:
            ev -= 0.05
        if block_type in {'heading', 'title'}:
            ev -= 0.05
        return ev

    def _apply_semantic_clues_claims(self, ev: float, term: str, text: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # Legal/marketing stricter
        if content_type in {'marketing', 'legal'}:
            ev += 0.15
        if content_type in {'technical', 'api', 'procedural'}:
            ev += 0.08
        
        if domain in {'legal', 'finance', 'medical'}:
            ev += 0.1
        
        if audience in {'beginner', 'general'}:
            ev += 0.05

        # Document-level: if many UK/marketing adjectives present, slight bump
        marketing_adjs = {"innovative", "revolutionary", "seamless"}
        text_lower = text.lower()
        if sum(1 for a in marketing_adjs if a in text_lower) >= 2:
            ev += 0.05

        return ev

    def _apply_feedback_clues_claims(self, ev: float, term: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_claims()
        t = term.lower()
        if t in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        if t in patterns.get('accepted_terms', set()):
            ev -= 0.2
        ctype = (context or {}).get('content_type', 'general')
        pc = patterns.get(f'{ctype}_patterns', {})
        if t in pc.get('flagged', set()):
            ev += 0.1
        if t in pc.get('accepted', set()):
            ev -= 0.1
        return ev

    def _get_cached_feedback_patterns_claims(self) -> Dict[str, Any]:
        return {
            'often_flagged_terms': {"secure", "effortless", "future-proof", "guaranteed"},
            'accepted_terms': set(),
            'marketing_patterns': {
                'flagged': {"best practice", "always", "never"},
                'accepted': set()
            },
            'technical_patterns': {
                'flagged': {"secure", "future-proof"},
                'accepted': set()
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_claim_message(self, term: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.85:
            return f"The term '{term}' is a risky claim without evidence. Use specific, verifiable language."
        if ev > 0.6:
            return f"Consider replacing '{term}' with a specific, objective description."
        return f"Prefer objective phrasing over '{term}' to avoid subjective claims."
