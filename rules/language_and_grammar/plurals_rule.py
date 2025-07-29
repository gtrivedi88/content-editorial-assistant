"""
Plurals Rule
Based on IBM Style Guide topic: "Plurals"
"""
import re
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PluralsRule(BaseLanguageRule):
    """
    Checks for several common pluralization errors, including the use of "(s)",
    and using plural nouns as adjectives.
    """
    def _get_rule_type(self) -> str:
        return 'plurals'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for pluralization errors.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        for i, sent in enumerate(doc.sents):
            # Rule 1: Avoid using "(s)" to indicate plural
            for match in re.finditer(r'\w+\(s\)', sent.text, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Avoid using '(s)' to indicate a plural.",
                    suggestions=["Rewrite the sentence to use either the singular or plural form, or use a phrase like 'one or more'."],
                    severity='medium',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))

                        # Rule 2: Avoid using plural nouns as adjectives (with technical exceptions)
            for token in sent:
                # LINGUISTIC ANCHOR: Check for plural nouns in modifier positions
                is_modifier = (token.tag_ == 'NNS' and 
                              token.dep_ in ('compound', 'nsubj', 'amod') and
                              token.lemma_ != token.lower_)
                
                if is_modifier:
                    # LINGUISTIC ANCHOR: Skip words that are actually functioning as verbs
                    if self._is_functioning_as_verb(token, sent.doc):
                        continue
                        
                    # LINGUISTIC ANCHOR: Skip legitimate technical compound plurals
                    if not self._is_legitimate_technical_compound(token, sent.doc):
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=f"Potential misuse of a plural noun '{token.text}' as an adjective.",
                            suggestions=[f"Consider using the singular form '{token.lemma_}' when a noun modifies another noun."],
                            severity='low',
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors

    def _is_functioning_as_verb(self, token, doc) -> bool:
        """
        LINGUISTIC ANCHOR: Detect when a token tagged as plural noun is actually functioning as a verb.
        This handles SpaCy parsing errors where verbs are incorrectly tagged as plural nouns.
        """
        # Check if the token is in a position where a verb would typically appear
        # and has verb-like dependencies or context
        
        # PATTERN 1: Check if it's the main predicate of the sentence
        if token.dep_ == 'ROOT':
            return True
        
        # PATTERN 2: Check if it has typical verb children (objects, adverbials, etc.)
        verb_children_deps = {'dobj', 'iobj', 'nsubjpass', 'advmod', 'aux', 'auxpass'}
        has_verb_children = any(child.dep_ in verb_children_deps for child in token.children)
        
        if has_verb_children:
            return True
        
        # PATTERN 3: Check if it's preceded by a subject and appears to be the main verb
        # Look for pattern: [subject] [this_token] [object]
        if (token.i > 0 and token.i < len(doc) - 1):
            prev_token = doc[token.i - 1]
            next_token = doc[token.i + 1]
            
            # Subject + verb + object pattern
            if (prev_token.dep_ in ('nsubj', 'compound') and 
                next_token.dep_ in ('dobj', 'attr')):
                return True
        
        # PATTERN 4: Common verb forms that might be mis-tagged
        # Check if the word commonly functions as a verb
        common_verbs_as_nouns = {
            'stores', 'processes', 'handles', 'manages', 'creates', 'generates',
            'provides', 'requires', 'ensures', 'validates', 'monitors',
            'executes', 'performs', 'delivers', 'supports', 'contains'
        }
        
        if token.lower_ in common_verbs_as_nouns:
            # Additional context check: if it's between a subject and object
            if (token.i > 0 and token.i < len(doc) - 1):
                prev_token = doc[token.i - 1]
                next_token = doc[token.i + 1]
                
                if (prev_token.pos_ == 'NOUN' and next_token.pos_ == 'NOUN'):
                    return True
        
        return False

    def _is_legitimate_technical_compound(self, token, doc) -> bool:
        """
        LINGUISTIC ANCHOR: Identifies legitimate technical compound plurals.
        These are plural nouns that are correctly used as modifiers in technical contexts.
        """
        lemma_lower = token.lemma_.lower()
        token_lower = token.lower_
        
        # LINGUISTIC ANCHOR 1: Technical mass nouns that are inherently plural
        # These are commonly used in their plural form as modifiers
        technical_mass_plurals = {
            'data',      # "data consistency", "data processing"
            'media',     # "media storage", "media streaming"  
            'criteria',  # "criteria validation", "criteria checking"
            'metadata',  # "metadata analysis", "metadata storage"
            'analytics', # "analytics dashboard", "analytics processing"
            'metrics',   # "metrics collection", "metrics analysis"
            'statistics', # "statistics gathering", "statistics reporting"
            'graphics',  # "graphics processing", "graphics rendering"
            'diagnostics', # "diagnostics tools", "diagnostics reporting"
            'logistics', # "logistics management", "logistics coordination"
        }
        
        if token_lower in technical_mass_plurals:
            return True
        
        # LINGUISTIC ANCHOR 2: Domain-specific technical plurals commonly used as modifiers
        technical_domain_plurals = {
            'systems',      # "systems architecture", "systems integration"
            'operations',   # "operations team", "operations management"
            'services',     # "services layer", "services architecture"
            'applications', # "applications layer", "applications server"
            'users',        # "users guide", "users manual" (debatable, but common)
            'communications', # "communications protocol", "communications layer"
            'networks',     # "networks administrator", "networks topology"
            'credentials',  # "credentials management", "credentials validation"
            'permissions',  # "permissions model", "permissions management"
            'requirements', # "requirements analysis", "requirements gathering"
            'specifications', # "specifications document", "specifications review"
            'procedures',   # "procedures manual", "procedures guide"
            'resources',    # "resources allocation", "resources management"
            'utilities',    # "utilities management", "utilities monitoring"
            'components',   # "components architecture", "components design"
            'tools',        # "diagnostics tools", "monitoring tools"
            'servers',      # "servers monitoring", "servers management"
        }
        
        if token_lower in technical_domain_plurals:
            return True
        
        # LINGUISTIC ANCHOR 3: Context-aware detection for technical compound phrases
        # Check if the compound is modifying a technical noun
        head_noun = token.head
        if head_noun.pos_ == 'NOUN':
            technical_head_nouns = {
                'architecture', 'design', 'framework', 'infrastructure', 'platform',
                'management', 'administration', 'coordination', 'integration',
                'analysis', 'processing', 'monitoring', 'validation', 'verification',
                'consistency', 'integrity', 'reliability', 'availability', 'security',
                'performance', 'optimization', 'configuration', 'deployment',
                'documentation', 'specification', 'requirement', 'procedure',
                'protocol', 'interface', 'layer', 'tier', 'model', 'pattern',
                'solution', 'approach', 'strategy', 'methodology', 'implementation'
            }
            
            if head_noun.lemma_.lower() in technical_head_nouns:
                return True
        
        # LINGUISTIC ANCHOR 4: Special case for "users" in documentation contexts
        # "users manual", "users guide" are widely accepted in technical writing
        if (token_lower == 'users' and head_noun.pos_ == 'NOUN' and
            head_noun.lemma_.lower() in {'manual', 'guide', 'documentation', 'handbook', 'reference'}):
            return True
        
        return False
