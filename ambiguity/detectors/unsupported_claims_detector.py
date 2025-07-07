"""
Unsupported Claims Detector

Detects language that makes unsupported claims, promises, or guarantees
that cannot be substantiated in technical documentation.

Examples:
- "guarantees" vs "ensures" 
- "will always" vs "typically"
- "never fails" vs "rarely fails"
"""

from typing import List, Dict, Any, Optional, Set
import re

from ..base_ambiguity_rule import AmbiguityDetector
from ..types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity,
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig
)


class UnsupportedClaimsDetector(AmbiguityDetector):
    """
    Detects unsupported claims and promises in technical writing.
    
    This detector identifies language that makes absolute claims or promises
    that cannot be substantiated, helping prevent over-promising in documentation.
    """
    
    def __init__(self, config: AmbiguityConfig):
        super().__init__(config)
        
        # Strong claim words that often indicate unsupported promises
        self.strong_claim_words = {
            'guarantee', 'guarantees', 'guaranteed', 'guaranteeing',
            'promise', 'promises', 'promised', 'promising',
            'always', 'never', 'impossible', 'certain', 'definitely',
            'absolutely', 'perfect', 'flawless', 'foolproof',
            '100%', 'zero', 'all', 'none', 'every', 'any'
        }
        
        # Moderate claim words that could be strengthened inappropriately
        self.moderate_claim_words = {
            'ensure', 'ensures', 'ensured', 'ensuring',
            'will', 'shall', 'must', 'should',
            'complete', 'completes', 'completed', 'completing',
            'total', 'full', 'entire', 'whole'
        }
        
        # Weaker alternatives that are more appropriate
        self.preferred_alternatives = {
            'guarantee': ['ensure', 'help ensure', 'is designed to'],
            'guarantees': ['ensures', 'helps ensure', 'is designed to'],
            'guaranteed': ['ensured', 'expected', 'intended'],
            'always': ['typically', 'usually', 'generally'],
            'never': ['rarely', 'seldom', 'not expected to'],
            'impossible': ['unlikely', 'not recommended'],
            'certain': ['likely', 'expected'],
            'definitely': ['likely', 'expected to'],
            'absolutely': ['generally', 'typically'],
            'perfect': ['optimal', 'recommended'],
            'flawless': ['reliable', 'well-tested'],
            'foolproof': ['straightforward', 'reliable'],
            '100%': ['high', 'very high'],
            'zero': ['minimal', 'very low'],
            'all': ['most', 'the majority of'],
            'none': ['few', 'very few'],
            'every': ['most', 'the majority of'],
            'any': ['some', 'certain']
        }
        
        # Phrases that often indicate unsupported promises
        self.promise_phrases = [
            r'will\s+always\s+work',
            r'will\s+never\s+fail',
            r'is\s+guaranteed\s+to',
            r'will\s+definitely',
            r'absolutely\s+ensures',
            r'perfect\s+solution',
            r'foolproof\s+method',
            r'never\s+goes\s+wrong',
            r'always\s+succeeds',
            r'100%\s+reliable',
            r'zero\s+risk',
            r'impossible\s+to\s+fail'
        ]
        
        # Minimum confidence threshold for flagging
        self.min_confidence = 0.5
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        """
        Detect unsupported claims in the given context.
        
        Args:
            context: Sentence context for analysis
            nlp: SpaCy nlp object
            
        Returns:
            List of ambiguity detections
        """
        detections = []
        
        if not context.sentence.strip():
            return detections
        
        try:
            # Parse sentence with SpaCy
            doc = nlp(context.sentence)
            
            # Check for strong claim words
            for token in doc:
                if self._is_strong_claim_word(token):
                    confidence = self._calculate_claim_strength(token, doc, context)
                    
                    if confidence >= self.min_confidence:
                        detection = self._create_detection(token, confidence, context)
                        detections.append(detection)
            
            # Check for promise phrases
            phrase_detections = self._detect_promise_phrases(context, doc)
            detections.extend(phrase_detections)
        
        except Exception as e:
            # Log error but don't fail the analysis
            print(f"Error in unsupported claims detection: {e}")
        
        return detections
    
    def _is_strong_claim_word(self, token) -> bool:
        """Check if a token is a strong or moderate claim word."""
        if not token:
            return False
        
        # Check lemma and text
        lemma = token.lemma_.lower()
        text = token.text.lower()
        
        return (lemma in self.strong_claim_words or text in self.strong_claim_words or
                lemma in self.moderate_claim_words or text in self.moderate_claim_words)
    
    def _calculate_claim_strength(self, token, doc, context: AmbiguityContext) -> float:
        """Calculate the strength/confidence of a claim."""
        word = token.text.lower()
        lemma = token.lemma_.lower()
        
        # Different confidence for different word types
        if lemma in self.strong_claim_words or word in self.strong_claim_words:
            confidence = 0.8  # High confidence for strong claims
            
            # Extra high confidence for absolute words
            if word in ['guarantee', 'guarantees', 'guaranteed', 'always', 'never', 'impossible']:
                confidence = 0.9
        
        elif lemma in self.moderate_claim_words or word in self.moderate_claim_words:
            confidence = 0.4  # Lower base confidence for moderate claims
            
            # But increase if context suggests strengthening risk
            if self._has_strengthening_risk(word, context):
                confidence += 0.4  # Flag "ensures" in contexts where it might become "guarantees"
        
        else:
            confidence = 0.3  # Base confidence for other potential claims
        
        # Adjust based on context
        if self._is_technical_context(context):
            confidence += 0.1
        
        if self._is_system_behavior_claim(token, doc):
            confidence += 0.1
        
        # Reduce confidence if there are qualifying words
        if self._has_qualifying_words(token, doc):
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _has_strengthening_risk(self, word: str, context: AmbiguityContext) -> bool:
        """Check if a moderate claim word has risk of being strengthened inappropriately."""
        # Words like "ensures" are at risk in technical contexts where they might become "guarantees"
        risky_patterns = [
            ('ensure', ['data', 'security', 'integrity', 'backup', 'protection']),
            ('will', ['always', 'never', 'work', 'function']),
            ('complete', ['full', 'total', 'entire']),
            ('must', ['always', 'never', 'all'])
        ]
        
        sentence_lower = context.sentence.lower()
        
        for pattern_word, risk_contexts in risky_patterns:
            if pattern_word in word:
                if any(risk_word in sentence_lower for risk_word in risk_contexts):
                    return True
        
        return False
    
    def _is_technical_context(self, context: AmbiguityContext) -> bool:
        """Check if this is a technical context where claims should be more conservative."""
        technical_keywords = [
            'system', 'server', 'application', 'software', 'database',
            'network', 'security', 'backup', 'configuration', 'installation',
            'deployment', 'integration', 'api', 'service', 'platform'
        ]
        
        sentence_lower = context.sentence.lower()
        return any(keyword in sentence_lower for keyword in technical_keywords)
    
    def _is_system_behavior_claim(self, token, doc) -> bool:
        """Check if the claim is about system behavior."""
        # Look for system-related subjects
        system_subjects = ['system', 'server', 'application', 'software', 'service']
        
        for sent in doc.sents:
            for chunk in sent.noun_chunks:
                if any(sys_word in chunk.text.lower() for sys_word in system_subjects):
                    return True
        
        return False
    
    def _has_qualifying_words(self, token, doc) -> bool:
        """Check if there are qualifying words that moderate the claim."""
        qualifying_words = [
            'usually', 'typically', 'generally', 'often', 'may', 'might',
            'can', 'could', 'should', 'likely', 'expected', 'designed',
            'intended', 'normally', 'commonly'
        ]
        
        # Check words around the token
        start_idx = max(0, token.i - 3)
        end_idx = min(len(doc), token.i + 4)
        
        for i in range(start_idx, end_idx):
            if i != token.i and doc[i].lemma_.lower() in qualifying_words:
                return True
        
        return False
    
    def _detect_promise_phrases(self, context: AmbiguityContext, doc) -> List[AmbiguityDetection]:
        """Detect promise phrases in the text."""
        detections = []
        
        sentence_lower = context.sentence.lower()
        
        for phrase_pattern in self.promise_phrases:
            matches = re.finditer(phrase_pattern, sentence_lower)
            
            for match in matches:
                # Find the tokens that match this phrase
                matched_text = match.group()
                tokens = [t.text for t in doc if t.text.lower() in matched_text]
                
                if tokens:
                    detection = self._create_phrase_detection(matched_text, tokens, context)
                    detections.append(detection)
        
        return detections
    
    def _create_detection(self, token, confidence: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Create an ambiguity detection for a strong claim word."""
        
        word = token.text.lower()
        alternatives = self.preferred_alternatives.get(word, ['more measured language'])
        
        # Create evidence
        evidence = AmbiguityEvidence(
            tokens=[token.text],
            linguistic_pattern=f"strong_claim_{word}",
            confidence=confidence,
            spacy_features={
                'pos': token.pos_,
                'lemma': token.lemma_,
                'dep': token.dep_,
                'is_absolute': word in ['always', 'never', 'guarantee', 'impossible']
            },
            context_clues={'alternatives': alternatives}
        )
        
        # Create resolution strategies
        strategies = [
            ResolutionStrategy.SPECIFY_REFERENCE,
            ResolutionStrategy.ADD_CONTEXT
        ]
        
        # Create AI instructions
        alternatives_text = "', '".join(alternatives)
        ai_instructions = [
            f"Replace '{token.text}' with more measured language that doesn't make unsupported promises",
            f"Consider alternatives: '{alternatives_text}'",
            "Avoid absolute claims unless you can substantiate them with evidence"
        ]
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.UNSUPPORTED_CLAIMS,
            category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL,
            context=context,
            evidence=evidence,
            resolution_strategies=strategies,
            ai_instructions=ai_instructions
        )
    
    def _create_phrase_detection(self, phrase: str, tokens: List[str], context: AmbiguityContext) -> AmbiguityDetection:
        """Create an ambiguity detection for a promise phrase."""
        
        # Create evidence
        evidence = AmbiguityEvidence(
            tokens=tokens,
            linguistic_pattern=f"promise_phrase_{phrase.replace(' ', '_')}",
            confidence=0.8,  # High confidence for phrase matches
            spacy_features={'phrase_type': 'promise'},
            context_clues={'phrase': phrase}
        )
        
        # Create resolution strategies
        strategies = [
            ResolutionStrategy.SPECIFY_REFERENCE,
            ResolutionStrategy.RESTRUCTURE_SENTENCE
        ]
        
        # Create AI instructions
        ai_instructions = [
            f"Rewrite the phrase '{phrase}' to avoid making unsupported promises",
            "Use more conservative language that reflects realistic expectations",
            "Consider adding qualifying words like 'typically' or 'expected to'"
        ]
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.UNSUPPORTED_CLAIMS,
            category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL,
            context=context,
            evidence=evidence,
            resolution_strategies=strategies,
            ai_instructions=ai_instructions
        ) 