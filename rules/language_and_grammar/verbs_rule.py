"""
Verbs Rule (Consolidated and Enhanced for Accuracy)
Based on IBM Style Guide topics: "Verbs: Tense", "Verbs: Voice"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class VerbsRule(BaseLanguageRule):
    """
    Checks for verb-related style issues with high-accuracy linguistic checks
    to prevent false positives.
    """
    def _get_rule_type(self) -> str:
        return 'verbs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sent_text in enumerate(sentences):
            if not sent_text.strip():
                continue
            
            doc = nlp(sent_text)
            
            # --- PRIORITY 1 FIX: High-Accuracy Passive Voice Check ---
            # This logic now iterates through each token to find a passive subject ('nsubjpass')
            # or a passive auxiliary verb ('auxpass'). This is a highly reliable
            # linguistic signal for passive voice and will not trigger on active sentences.
            passive_token = self._find_passive_token(doc)
            if passive_token:
                flagged_text = passive_token.head.text
                # Calculate span for consolidation
                span_start = passive_token.head.idx
                span_end = span_start + len(flagged_text)
                
                # Generate intelligent, context-specific suggestions
                suggestions = self._generate_active_voice_suggestions(doc, passive_token, sent_text)
                
                errors.append(self._create_error(
                    sentence=sent_text,
                    sentence_index=i,
                    message="Sentence may be in the passive voice.",
                    suggestions=suggestions,
                    severity='medium',
                    span=(span_start, span_end),
                    flagged_text=flagged_text
                ))

            # --- Future Tense Check ('will') ---
            for token in doc:
                if token.lemma_.lower() == "will" and token.tag_ == "MD":
                    head_verb = token.head
                    if head_verb.pos_ == "VERB":
                        suggestion = f"Use the present tense '{head_verb.lemma_}s' or the imperative mood '{head_verb.lemma_.capitalize()}'."
                        flagged_text = f"{token.text} {head_verb.text}"
                        # Calculate span for the will + verb construction
                        span_start = token.idx
                        span_end = head_verb.idx + len(head_verb.text)
                        errors.append(self._create_error(
                            sentence=sent_text,
                            sentence_index=i,
                            message="Avoid future tense in procedural and descriptive text.",
                            suggestions=[suggestion],
                            severity='medium',
                            span=(span_start, span_end),
                            flagged_text=flagged_text
                        ))

            # --- Past Tense Check ---
            # Only flag past tense if it's NOT part of a passive construction
            root_verb = self._find_root_token(doc)
            if (root_verb and root_verb.pos_ == 'VERB' and 'Tense=Past' in str(root_verb.morph) 
                and not self._is_passive_construction(root_verb, doc)):
                flagged_text = root_verb.text
                span_start = root_verb.idx
                span_end = span_start + len(flagged_text)
                errors.append(self._create_error(
                    sentence=sent_text,
                    sentence_index=i,
                    message="Sentence may not be in the preferred present tense.",
                    suggestions=["Use present tense for instructions and system descriptions."],
                    severity='low',
                    span=(span_start, span_end),
                    flagged_text=flagged_text
                ))
        
        return errors

    def _find_passive_token(self, doc: Doc) -> Token | None:
        """Finds the first token that indicates a passive construction."""
        for token in doc:
            if token.dep_ in ('nsubjpass', 'auxpass'):
                return token
        return None

    def _find_root_token(self, doc: Doc) -> Token | None:
        """Finds the root token of the sentence."""
        for token in doc:
            if token.dep_ == "ROOT":
                return token
        return None

    def _is_passive_construction(self, verb_token: Token, doc: Doc) -> bool:
        """Check if a verb token is part of a passive voice construction."""
        if not verb_token:
            return False
        
        # Check if this verb is the head of a passive subject (nsubjpass)
        for token in doc:
            if token.dep_ == 'nsubjpass' and token.head == verb_token:
                return True
        
        # Check if this verb has an auxiliary passive marker (auxpass)
        for child in verb_token.children:
            if child.dep_ == 'auxpass':
                return True
                
        return False

    def _generate_active_voice_suggestions(self, doc: Doc, passive_token: Token, sentence: str) -> List[str]:
        """Generate intelligent, context-specific suggestions for converting passive to active voice."""
        suggestions = []
        
        try:
            # Find the main verb (head of the passive token)
            main_verb = passive_token.head if passive_token.dep_ in ('nsubjpass', 'auxpass') else passive_token
            
            # Find the passive subject (what's being acted upon)
            passive_subject = None
            for token in doc:
                if token.dep_ == 'nsubjpass' and token.head == main_verb:
                    passive_subject = token
                    break
            
            # Find the agent (who/what performs the action) - look for "by" phrases
            agent = self._find_agent_in_by_phrase(doc, main_verb)
            
            # Check for negative constructions
            is_negative = self._has_negative_context(doc, main_verb)
            
            # Generate suggestions based on sentence structure
            if passive_subject and main_verb:
                base_verb = main_verb.lemma_
                
                # Strategy 1: Analyze sentence structure for context-aware suggestions
                if is_negative:
                    # For negative constructions, suggest positive alternatives by analyzing context
                    antonym = self._get_positive_alternative(base_verb, doc)
                    if antonym:
                        suggestions.append(f"Rewrite positively: 'You must {antonym} {passive_subject.text.lower()}' (use positive action)")
                    else:
                        suggestions.append(f"Rewrite as requirement: 'You must ensure {passive_subject.text.lower()} is {self._get_past_participle(base_verb)}' (specify the requirement)")
                else:
                    # For positive constructions, use imperative
                    if passive_subject.text.lower() in ['it', 'this', 'that']:
                        suggestions.append(f"Use imperative: '{base_verb.capitalize()} {passive_subject.text.lower()}' (make the user the actor)")
                    else:
                        suggestions.append(f"Use imperative: '{base_verb.capitalize()} the {passive_subject.text.lower()}' (make the user the actor)")
                
                # Strategy 2: If there's an explicit agent, use it
                if agent:
                    suggestions.append(f"Make the agent active: '{agent.capitalize()} {self._conjugate_verb(base_verb, agent)} {passive_subject.text.lower()}'")
                
                # Strategy 3: Use specific actors for technical contexts
                if self._is_technical_context(doc):
                    if base_verb in ['configure', 'install', 'setup', 'deploy']:
                        suggestions.append(f"Specify the actor: 'The administrator {self._conjugate_verb(base_verb, 'administrator')} {passive_subject.text.lower()}'")
                    else:
                        suggestions.append(f"Specify the system: 'The system {self._conjugate_verb(base_verb, 'system')} {passive_subject.text.lower()}'")
                
                # Strategy 4: Generic improvement (only if we don't have better suggestions)
                if len(suggestions) < 2:
                    suggestions.append(f"Identify who or what performs '{base_verb}' and make them the subject")
            
            # Fallback suggestion
            if not suggestions:
                suggestions.append("Identify who or what performs the action and make them the sentence subject")
                
        except Exception as e:
            # Fallback to generic suggestion if analysis fails
            suggestions = ["Rewrite in active voice by identifying who or what performs the action"]
        
        return suggestions[:3]  # Limit to 3 most relevant suggestions

    def _find_agent_in_by_phrase(self, doc: Doc, main_verb: Token) -> str:
        """Find the agent in a 'by' phrase (e.g., 'by the user')."""
        for token in doc:
            if token.lemma_ == 'by' and token.head == main_verb:
                # Look for the object of the 'by' preposition
                for child in token.children:
                    if child.dep_ == 'pobj':
                        return child.text
        return None

    def _has_negative_context(self, doc: Doc, main_verb: Token) -> bool:
        """Check if the passive construction is in a negative context."""
        # Look for negative words near the main verb
        for token in doc:
            if token.dep_ == 'neg' or token.lemma_ in ['not', 'never', 'cannot']:
                # Check if the negative is related to our main verb
                if token.head == main_verb or token.head.head == main_verb:
                    return True
        
        # Also check for "can not" or "cannot" patterns
        sentence_text = doc.text.lower()
        negative_patterns = ['can not be', 'cannot be', 'should not be', 'must not be']
        return any(pattern in sentence_text for pattern in negative_patterns)

    def _get_positive_alternative(self, verb_lemma: str, doc: Doc) -> str:
        """Get a positive alternative for a negated verb based on context analysis."""
        # Analyze surrounding context to determine semantic intent
        verb_alternatives = {
            'overlook': 'address',
            'ignore': 'consider', 
            'miss': 'include',
            'skip': 'complete',
            'avoid': 'ensure',
            'neglect': 'maintain',
            'forget': 'remember'
        }
        
        # Check if we have a semantic alternative
        if verb_lemma in verb_alternatives:
            return verb_alternatives[verb_lemma]
        
        # For other verbs, analyze context to suggest appropriate action
        context_words = [token.lemma_.lower() for token in doc]
        
        # If it's about configuration/setup, suggest "ensure"
        if any(word in context_words for word in ['configure', 'setup', 'install', 'deploy']):
            return 'ensure'
        
        # If it's about dependencies/requirements, suggest "address"  
        if any(word in context_words for word in ['dependency', 'requirement', 'critical', 'important']):
            return 'address'
        
        # Default fallback
        return None

    def _get_past_participle(self, verb_lemma: str) -> str:
        """Get the past participle form of a verb for requirement statements."""
        # Common irregular past participles
        irregular_participles = {
            'overlook': 'overlooked',
            'configure': 'configured', 
            'setup': 'set up',
            'install': 'installed',
            'deploy': 'deployed',
            'ignore': 'ignored',
            'address': 'addressed',
            'consider': 'considered',
            'include': 'included',
            'complete': 'completed',
            'ensure': 'ensured',
            'maintain': 'maintained'
        }
        
        if verb_lemma in irregular_participles:
            return irregular_participles[verb_lemma]
        
        # Regular past participle formation
        if verb_lemma.endswith('e'):
            return verb_lemma + 'd'
        elif verb_lemma.endswith(('t', 'd')):
            return verb_lemma + 'ed'
        else:
            return verb_lemma + 'ed'

    def _is_technical_context(self, doc: Doc) -> bool:
        """Check if the sentence appears to be in a technical context."""
        technical_words = {'server', 'database', 'system', 'application', 'service', 'configuration', 'software'}
        return any(token.lemma_.lower() in technical_words for token in doc)

    def _conjugate_verb(self, verb_lemma: str, subject: str) -> str:
        """Simple verb conjugation for common cases."""
        if subject.lower() in ['system', 'server', 'application', 'service']:
            # Third person singular
            if verb_lemma.endswith('e'):
                return verb_lemma + 's'
            elif verb_lemma.endswith(('s', 'sh', 'ch', 'x', 'z')):
                return verb_lemma + 'es'
            else:
                return verb_lemma + 's'
        else:
            # Default to base form for other subjects
            return verb_lemma
