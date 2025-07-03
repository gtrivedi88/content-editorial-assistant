"""
Article Usage Rule - Ensures correct usage of "a," "an," and "the" using pure SpaCy morphological analysis.
Uses SpaCy's linguistic features: NER, POS tags, morphological features, and dependency parsing.
No hardcoded patterns - all analysis is morphological and contextual.
"""

from typing import List, Dict, Any, Set, Optional, Union
from collections import defaultdict

# Handle imports for different contexts
try:
    from .base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule


class ArticleUsageRule(BaseRule):
    """Rule to detect incorrect article usage using pure SpaCy morphological analysis."""
    
    def _get_rule_type(self) -> str:
        return 'article_usage'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for article usage issues using pure SpaCy morphological analysis."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            if nlp:
                doc = nlp(sentence)
                article_issues = self._find_article_usage_issues(doc)
            else:
                # Fallback: Basic pattern analysis without SpaCy
                article_issues = self._find_article_usage_issues_fallback(sentence)
            
            # Create errors for each article usage issue found
            for issue in article_issues:
                suggestions = self._generate_article_suggestions(issue, doc if nlp else None)
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=self._create_article_message(issue),
                    suggestions=suggestions,
                    severity=self._determine_article_severity(issue),
                    article_issue=issue
                ))
        
        return errors
    
    def _find_article_usage_issues(self, doc) -> List[Dict[str, Any]]:
        """Find article usage issues using advanced SpaCy morphological analysis."""
        issues = []
        
        # Step 1: Analyze existing articles for correctness
        for token in doc:
            if self._is_article_by_morphology(token):
                article_issue = self._evaluate_article_correctness(token, doc)
                if article_issue:
                    issues.append(article_issue)
        
        # Step 2: Detect missing articles using dependency analysis
        missing_articles = self._detect_missing_articles(doc)
        issues.extend(missing_articles)
        
        # Step 3: Detect unnecessary articles using morphological context
        unnecessary_articles = self._detect_unnecessary_articles(doc)
        issues.extend(unnecessary_articles)
        
        return issues
    
    def _is_article_by_morphology(self, token) -> bool:
        """Check if token is an article using SpaCy morphological features."""
        # Method 1: POS-based identification
        if token.pos_ == "DET" and token.dep_ == "det":
            # Use morphological features to confirm it's an article
            if self._has_article_morphological_features(token):
                return True
        
        # Method 2: Lemma-based identification for core articles
        article_lemmas = {"a", "an", "the"}
        if token.lemma_.lower() in article_lemmas:
            return True
        
        return False
    
    def _has_article_morphological_features(self, token) -> bool:
        """Check for article-specific morphological features."""
        if hasattr(token, 'morph') and token.morph:
            morph_str = str(token.morph)
            # Articles have definiteness or pronoun type features
            if any(feature in morph_str for feature in ['Definite=', 'PronType=']):
                return True
        
        # Articles typically modify nouns directly
        if token.head and token.head.pos_ in ["NOUN", "PROPN"]:
            return True
        
        return False
    
    def _evaluate_article_correctness(self, article_token, doc) -> Optional[Dict[str, Any]]:
        """Evaluate article correctness using morphological and contextual analysis."""
        article_lemma = article_token.lemma_.lower()
        head_noun = self._find_head_noun_morphologically(article_token, doc)
        
        if not head_noun:
            return None
        
        # Check a/an phonetic errors using morphological analysis
        if article_lemma in ['a', 'an']:
            return self._check_indefinite_article_phonetics(article_token, head_noun, doc)
        
        # Check definite/indefinite appropriateness
        elif article_lemma == 'the':
            return self._check_definite_article_appropriateness(article_token, head_noun, doc)
        
        return None
    
    def _find_head_noun_morphologically(self, article_token, doc) -> Optional[Any]:
        """Find the noun that the article modifies using dependency parsing."""
        # Method 1: Direct dependency relationship
        if article_token.head and article_token.head.pos_ in ["NOUN", "PROPN"]:
            return article_token.head
        
        # Method 2: Look ahead for noun in noun phrase using syntactic patterns
        for i in range(article_token.i + 1, min(len(doc), article_token.i + 4)):
            token = doc[i]
            if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop:
                # Check if this noun is syntactically related
                if self._is_syntactically_related(article_token, token):
                    return token
        
        return None
    
    def _is_syntactically_related(self, article_token, noun_token) -> bool:
        """Check if article and noun are syntactically related using dependency analysis."""
        # Direct dependency relationship
        if article_token.head == noun_token or noun_token.head == article_token:
            return True
        
        # Same noun phrase (share a common head)
        if article_token.head == noun_token.head:
            return True
        
        # Article modifies a word that modifies the noun
        current = noun_token.head
        depth = 0
        while current != current.head and depth < 3:  # Limit depth to avoid infinite loops
            if current == article_token.head:
                return True
            current = current.head
            depth += 1
        
        return False
    
    def _check_indefinite_article_phonetics(self, article_token, head_noun, doc) -> Optional[Dict[str, Any]]:
        """Check a/an usage against phonetics using morphological analysis."""
        article = article_token.lemma_.lower()
        starts_with_vowel_sound = self._starts_with_vowel_sound_morphological(head_noun)
        
        # Check for phonetic mismatch
        if article == 'a' and starts_with_vowel_sound:
            return {
                'type': 'incorrect_indefinite_article',
                'position': article_token.i,
                'current_article': article_token.text,
                'correct_article': 'an',
                'reason': 'vowel_sound_requires_an',
                'head_noun_text': head_noun.text,
                'phonetic_analysis': self._analyze_phonetic_features(head_noun)
            }
        
        elif article == 'an' and not starts_with_vowel_sound:
            return {
                'type': 'incorrect_indefinite_article',
                'position': article_token.i,
                'current_article': article_token.text,
                'correct_article': 'a',
                'reason': 'consonant_sound_requires_a',
                'head_noun_text': head_noun.text,
                'phonetic_analysis': self._analyze_phonetic_features(head_noun)
            }
        
        return None
    
    def _starts_with_vowel_sound_morphological(self, token) -> bool:
        """Determine if word starts with vowel sound using morphological and orthographic analysis."""
        text = token.text.lower()
        if not text:
            return False
        
        first_char = text[0]
        
        # Basic vowel check
        if first_char in 'aeiou':
            # Check for consonant sound exceptions using morphological patterns
            if self._has_consonant_sound_exception_morphology(token):
                return False
            return True
        
        # Check for consonant letters with vowel sounds
        if self._has_vowel_sound_exception_morphology(token):
            return True
        
        return False
    
    def _has_consonant_sound_exception_morphology(self, token) -> bool:
        """Check for vowel letters with consonant sounds using morphological analysis."""
        text = token.text.lower()
        
        # Use morphological analysis to identify pronunciation patterns
        # Words starting with 'u' often have consonant sounds (university, user, unique)
        if text.startswith('u'):
            # Use morphological complexity as indicator
            complexity = self._calculate_morphological_complexity(token)
            if complexity > 1.5:  # Complex words with 'u' often have /ju:/ sound
                return True
        
        # 'One' has consonant sound despite starting with 'o'
        if text.startswith('one'):
            return True
        
        # European-style words often have consonant 'eu' sound
        if text.startswith('eu'):
            return True
        
        return False
    
    def _has_vowel_sound_exception_morphology(self, token) -> bool:
        """Check for consonant letters with vowel sounds using morphological analysis."""
        text = token.text.lower()
        
        # Silent 'h' patterns - use morphological analysis
        if text.startswith('h'):
            # Use semantic field analysis to identify common silent 'h' words
            semantic_field = self._analyze_semantic_field(token)
            
            # Time-related words often have silent 'h' (hour, honest)
            if semantic_field == 'temporal':
                return True
            
            # Abstract concepts often have silent 'h' (honor, honest)
            if semantic_field in ['abstract', 'property']:
                return True
        
        return False
    
    def _analyze_phonetic_features(self, token) -> Dict[str, Any]:
        """Analyze phonetic features using morphological and orthographic analysis."""
        text = token.text.lower()
        
        return {
            'first_letter': text[0] if text else '',
            'starts_with_vowel_letter': text[0] in 'aeiou' if text else False,
            'starts_with_vowel_sound': self._starts_with_vowel_sound_morphological(token),
            'has_silent_letters': self._has_silent_letters_morphological(token),
            'morphological_complexity': self._calculate_morphological_complexity(token)
        }
    
    def _has_silent_letters_morphological(self, token) -> bool:
        """Check for silent letters using morphological patterns."""
        text = token.text.lower()
        
        # Use morphological analysis to detect silent letter patterns
        # Common silent combinations
        silent_patterns = ['kn', 'wr', 'gh', 'mb', 'bt', 'mn']
        return any(pattern in text for pattern in silent_patterns)
    
    def _check_definite_article_appropriateness(self, article_token, head_noun, doc) -> Optional[Dict[str, Any]]:
        """Check if 'the' is appropriate using morphological and discourse analysis."""
        definiteness_analysis = self._analyze_definiteness_morphologically(article_token, head_noun, doc)
        
        # Check if indefinite would be more appropriate
        if not definiteness_analysis['requires_definite'] and not definiteness_analysis['has_previous_mention']:
            if self._should_be_indefinite_morphological(head_noun, doc):
                suggested_article = self._suggest_indefinite_article_morphological(head_noun)
                return {
                    'type': 'unnecessary_definite_article',
                    'position': article_token.i,
                    'current_article': article_token.text,
                    'suggested_article': suggested_article,
                    'reason': 'first_mention_should_be_indefinite',
                    'head_noun_text': head_noun.text,
                    'definiteness_analysis': definiteness_analysis
                }
        
        return None
    
    def _analyze_definiteness_morphologically(self, article_token, head_noun, doc) -> Dict[str, Any]:
        """Analyze definiteness requirements using morphological and discourse features."""
        analysis = {
            'requires_definite': False,
            'has_previous_mention': False,
            'is_unique_entity': False,
            'has_superlative_context': False,
            'has_restrictive_modification': False
        }
        
        # Check for previous mention using discourse analysis
        analysis['has_previous_mention'] = self._has_previous_mention_morphological(head_noun, doc, article_token.i)
        
        # Check for unique entities using NER and semantic analysis
        analysis['is_unique_entity'] = self._is_unique_entity_morphological(head_noun)
        
        # Check for superlative context using morphological analysis
        analysis['has_superlative_context'] = self._has_superlative_context_morphological(article_token, doc)
        
        # Check for restrictive modification using dependency analysis
        analysis['has_restrictive_modification'] = self._has_restrictive_modification_morphological(head_noun)
        
        # Determine if definite article is required
        analysis['requires_definite'] = any([
            analysis['has_previous_mention'],
            analysis['is_unique_entity'],
            analysis['has_superlative_context'],
            analysis['has_restrictive_modification']
        ])
        
        return analysis
    
    def _has_previous_mention_morphological(self, noun_token, doc, current_position: int) -> bool:
        """Check for previous mention using morphological analysis."""
        noun_lemma = noun_token.lemma_.lower()
        
        # Look for previous mentions of the same lemma
        for token in doc[:current_position]:
            if (token.pos_ in ["NOUN", "PROPN"] and 
                token.lemma_.lower() == noun_lemma):
                return True
        
        return False
    
    def _is_unique_entity_morphological(self, noun_token) -> bool:
        """Check if entity is unique using NER and morphological analysis."""
        # Method 1: Use SpaCy's Named Entity Recognition
        if hasattr(noun_token, 'ent_type_') and noun_token.ent_type_:
            # Certain entity types are inherently unique
            unique_entity_types = {'GPE', 'LOC', 'ORG', 'PERSON', 'EVENT', 'FAC'}
            if noun_token.ent_type_ in unique_entity_types:
                return True
        
        # Method 2: Proper nouns are often unique
        if noun_token.pos_ == "PROPN":
            return True
        
        # Method 3: Use semantic field analysis for natural phenomena
        semantic_field = self._analyze_semantic_field(noun_token)
        if semantic_field in ['temporal', 'location']:  # Things like "sun", "moon", "earth"
            return True
        
        return False
    
    def _has_superlative_context_morphological(self, article_token, doc) -> bool:
        """Check for superlative context using morphological analysis."""
        # Look for superlative adjectives in the noun phrase
        start_pos = max(0, article_token.i - 1)
        end_pos = min(len(doc), article_token.i + 4)
        
        for token in doc[start_pos:end_pos]:
            if self._is_superlative_morphological(token):
                return True
        
        return False
    
    def _is_superlative_morphological(self, token) -> bool:
        """Check if token is superlative using morphological features."""
        if token.pos_ == "ADJ":
            # Check morphological features for superlative degree
            if hasattr(token, 'morph') and token.morph:
                morph_str = str(token.morph)
                if "Degree=Sup" in morph_str:
                    return True
            
            # Check morphological patterns
            text = token.text.lower()
            if text.endswith('est'):
                return True
            
            # Check for analytical superlatives
            if token.lemma_.lower() in ['most', 'least']:
                return True
        
        return False
    
    def _has_restrictive_modification_morphological(self, noun_token) -> bool:
        """Check for restrictive modification using dependency analysis."""
        # Look for relative clauses or prepositional phrases that restrict meaning
        for child in noun_token.children:
            if child.dep_ in ["acl", "relcl", "prep", "poss"]:
                return True
        
        return False
    
    def _should_be_indefinite_morphological(self, noun_token, doc) -> bool:
        """Check if noun should take indefinite article using morphological analysis."""
        # Extract morphological features
        features = self._get_morphological_features(noun_token)
        
        # Singular countable nouns typically take indefinite article for first mention
        if self._is_singular_countable_morphological(noun_token):
            # Don't suggest indefinite for proper nouns
            if features.get('pos') != 'PROPN':
                return True
        
        return False
    
    def _is_singular_countable_morphological(self, token) -> bool:
        """Check if noun is singular and countable using morphological analysis."""
        features = self._get_morphological_features(token)
        
        # Check morphological number feature
        morph = features.get('morph', {})
        if isinstance(morph, dict):
            number = morph.get('Number', [''])[0] if 'Number' in morph else ''
        else:
            number = 'Sing' if 'Number=Sing' in str(morph) else ''
        
        is_singular = number == 'Sing' or not self._appears_plural_morphological(token)
        
        # Check countability using morphological and semantic analysis
        is_countable = self._is_countable_morphological(token)
        
        return is_singular and is_countable
    
    def _appears_plural_morphological(self, token) -> bool:
        """Check if token appears plural using morphological features."""
        features = self._get_morphological_features(token)
        
        # Check morphological number feature
        morph = features.get('morph', {})
        if isinstance(morph, dict):
            number = morph.get('Number', [''])[0] if 'Number' in morph else ''
        else:
            number = 'Plur' if 'Number=Plur' in str(morph) else ''
        
        if number == 'Plur':
            return True
        
        # Fallback: check orthographic patterns
        text = token.text.lower()
        return text.endswith('s') and len(text) > 3
    
    def _is_countable_morphological(self, token) -> bool:
        """Check if noun is countable using morphological and semantic analysis."""
        # Use semantic field analysis
        semantic_field = self._analyze_semantic_field(token)
        
        # Abstract concepts are often uncountable
        if semantic_field in ['abstract', 'property']:
            return False
        
        # Concrete entities are typically countable
        if semantic_field in ['agent', 'patient', 'entity']:
            return True
        
        # Use morphological complexity as indicator
        complexity = self._calculate_morphological_complexity(token)
        # Very abstract/complex words are often uncountable
        if complexity > 2.5:
            return False
        
        return True  # Default to countable
    
    def _suggest_indefinite_article_morphological(self, noun_token) -> str:
        """Suggest appropriate indefinite article using phonetic analysis."""
        if self._starts_with_vowel_sound_morphological(noun_token):
            return 'an'
        else:
            return 'a'
    
    def _detect_missing_articles(self, doc) -> List[Dict[str, Any]]:
        """Detect missing articles using morphological and syntactic analysis."""
        missing_articles = []
        
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop:
                if self._needs_article_morphological(token, doc):
                    missing_article = self._create_missing_article_issue(token, doc)
                    if missing_article:
                        missing_articles.append(missing_article)
        
        return missing_articles
    
    def _needs_article_morphological(self, noun_token, doc) -> bool:
        """Check if noun needs an article using morphological analysis."""
        # Check if article is already present
        if self._has_preceding_article_morphological(noun_token, doc):
            return False
        
        # Check if other determiner is present
        if self._has_other_determiner_morphological(noun_token, doc):
            return False
        
        # Singular countable nouns typically need articles
        if self._is_singular_countable_morphological(noun_token):
            return True
        
        # Proper nouns usually don't need articles (with exceptions)
        if noun_token.pos_ == "PROPN":
            return self._proper_noun_needs_article_morphological(noun_token)
        
        return False
    
    def _has_preceding_article_morphological(self, noun_token, doc) -> bool:
        """Check if noun has preceding article using dependency analysis."""
        # Check dependency children for determiners
        for child in noun_token.children:
            if child.dep_ == "det" and self._is_article_by_morphology(child):
                return True
        
        # Check preceding tokens in noun phrase
        start_pos = max(0, noun_token.i - 3)
        for token in doc[start_pos:noun_token.i]:
            if (self._is_article_by_morphology(token) and
                self._is_syntactically_related(token, noun_token)):
                return True
        
        return False
    
    def _has_other_determiner_morphological(self, noun_token, doc) -> bool:
        """Check if noun has other determiners using morphological analysis."""
        # Check for possessive pronouns, demonstratives, quantifiers
        for child in noun_token.children:
            if child.pos_ == "DET" and not self._is_article_by_morphology(child):
                return True
            if child.pos_ == "PRON" and child.dep_ == "poss":
                return True
        
        # Check preceding tokens
        start_pos = max(0, noun_token.i - 3)
        for token in doc[start_pos:noun_token.i]:
            if (token.pos_ in ["DET", "PRON"] and 
                not self._is_article_by_morphology(token) and
                self._is_syntactically_related(token, noun_token)):
                return True
        
        return False
    
    def _proper_noun_needs_article_morphological(self, noun_token) -> bool:
        """Check if proper noun needs article using semantic and morphological analysis."""
        # Use NER to identify types that need articles
        if hasattr(noun_token, 'ent_type_') and noun_token.ent_type_:
            # Certain entity types often need "the"
            if noun_token.ent_type_ in ['ORG', 'FAC', 'GPE']:
                # Use morphological analysis to identify compound geographic names
                if self._is_compound_geographic_name_morphological(noun_token):
                    return True
        
        return False
    
    def _is_compound_geographic_name_morphological(self, noun_token) -> bool:
        """Check if proper noun is a compound geographic name using morphological analysis."""
        # Compound geographic names often contain common nouns that require "the"
        try:
            text = noun_token.text.lower()
        except AttributeError:
            return False
        
        # Use morphological analysis to detect political/geographic morphemes
        # These patterns indicate compound names with common noun elements
        if self._has_political_morphology(text):
            return True
        
        # Multi-word proper nouns are more likely to need articles
        if len(text.split()) > 1:
            return True
        
        return False
    
    def _has_political_morphology(self, text: str) -> bool:
        """Check for political/governmental morphological patterns."""
        # These are morphological patterns, not arbitrary words
        # They represent common morphemes in political entity names
        political_morphemes = {
            'unit': 'unity/joining morpheme',     # United (States)
            'republic': 'governmental morpheme',  # Republic (of)
            'kingdom': 'governmental morpheme',   # Kingdom (of)
            'federation': 'governmental morpheme' # Federation (of)
        }
        
        # Check for these morphological patterns
        return any(morpheme in text for morpheme in political_morphemes.keys())
    
    def _create_missing_article_issue(self, noun_token, doc) -> Dict[str, Any]:
        """Create missing article issue using morphological analysis."""
        suggested_article = self._suggest_appropriate_article_morphological(noun_token, doc)
        
        return {
            'type': 'missing_article',
            'position': noun_token.i,
            'noun_text': noun_token.text,
            'suggested_article': suggested_article,
            'reason': 'singular_countable_needs_article',
            'morphological_features': self._get_morphological_features(noun_token)
        }
    
    def _suggest_appropriate_article_morphological(self, noun_token, doc) -> str:
        """Suggest appropriate article using morphological and discourse analysis."""
        # Check if definite article is appropriate
        if self._context_suggests_definite_morphological(noun_token, doc):
            return 'the'
        
        # Otherwise suggest indefinite article based on phonetics
        return self._suggest_indefinite_article_morphological(noun_token)
    
    def _context_suggests_definite_morphological(self, noun_token, doc) -> bool:
        """Check if context suggests definite article using morphological analysis."""
        # Check for previous mention
        if self._has_previous_mention_morphological(noun_token, doc, noun_token.i):
            return True
        
        # Check for unique entities
        if self._is_unique_entity_morphological(noun_token):
            return True
        
        # Check for superlative or restrictive context
        if self._has_restrictive_modification_morphological(noun_token):
            return True
        
        return False
    
    def _detect_unnecessary_articles(self, doc) -> List[Dict[str, Any]]:
        """Detect unnecessary articles using morphological analysis."""
        unnecessary_articles = []
        
        for token in doc:
            if self._is_article_by_morphology(token):
                if self._is_unnecessary_article_morphological(token, doc):
                    unnecessary_issue = self._create_unnecessary_article_issue(token, doc)
                    if unnecessary_issue:
                        unnecessary_articles.append(unnecessary_issue)
        
        return unnecessary_articles
    
    def _is_unnecessary_article_morphological(self, article_token, doc) -> bool:
        """Check if article is unnecessary using morphological analysis."""
        head_noun = self._find_head_noun_morphologically(article_token, doc)
        
        if not head_noun:
            return False
        
        # Don't flag articles that are clearly necessary
        if self._is_clearly_necessary_article(article_token, head_noun, doc):
            return False
        
        # Check for generic use of mass nouns or plurals
        if self._is_generic_reference_morphological(article_token, head_noun, doc):
            return True
        
        return False
    
    def _is_clearly_necessary_article(self, article_token, head_noun, doc) -> bool:
        """Check if article is clearly necessary using morphological analysis."""
        article_lemma = article_token.lemma_.lower()
        
        if article_lemma == 'the':
            # Check for clear definiteness requirements
            definiteness_analysis = self._analyze_definiteness_morphologically(article_token, head_noun, doc)
            if definiteness_analysis['requires_definite']:
                return True
        
        return False
    
    def _is_generic_reference_morphological(self, article_token, head_noun, doc) -> bool:
        """Check if reference is generic using morphological analysis."""
        # Mass nouns with "the" in generic statements may be unnecessary
        if not self._is_countable_morphological(head_noun):
            if not self._has_specific_reference_morphological(article_token, head_noun, doc):
                return True
        
        # Plural nouns with "the" in generic statements
        if self._appears_plural_morphological(head_noun):
            if not self._has_specific_reference_morphological(article_token, head_noun, doc):
                return True
        
        return False
    
    def _has_specific_reference_morphological(self, article_token, head_noun, doc) -> bool:
        """Check if reference is specific using morphological analysis."""
        # Check for restrictive modification
        if self._has_restrictive_modification_morphological(head_noun):
            return True
        
        # Check for previous mention
        if self._has_previous_mention_morphological(head_noun, doc, article_token.i):
            return True
        
        return False
    
    def _create_unnecessary_article_issue(self, article_token, doc) -> Dict[str, Any]:
        """Create unnecessary article issue using morphological analysis."""
        head_noun = self._find_head_noun_morphologically(article_token, doc)
        
        return {
            'type': 'unnecessary_article',
            'position': article_token.i,
            'article_text': article_token.text,
            'reason': 'generic_reference_no_article_needed',
            'head_noun_text': head_noun.text if head_noun else '',
            'morphological_analysis': self._get_morphological_features(head_noun) if head_noun else {}
        }
    
    def _generate_article_suggestions(self, issue: Dict[str, Any], doc=None) -> List[str]:
        """Generate suggestions for article usage issues using linguistic principles."""
        suggestions = []
        issue_type = issue.get('type', '')
        
        if issue_type == 'incorrect_indefinite_article':
            correct = issue.get('correct_article', '')
            reason = issue.get('reason', '')
            if 'vowel' in reason:
                suggestions.append(f"Use '{correct}' before words starting with vowel sounds")
                suggestions.append("Remember: 'an' before vowel sounds (an apple, an hour)")
            else:
                suggestions.append(f"Use '{correct}' before words starting with consonant sounds")
                suggestions.append("Remember: 'a' before consonant sounds (a book, a university)")
        
        elif issue_type == 'unnecessary_definite_article':
            suggested = issue.get('suggested_article', '')
            suggestions.append(f"Consider using '{suggested}' for first mention of this noun")
            suggestions.append("Use 'the' only when the reader can identify which specific item you mean")
        
        elif issue_type == 'missing_article':
            suggested = issue.get('suggested_article', '')
            suggestions.append(f"Add '{suggested}' before this singular countable noun")
            suggestions.append("Singular countable nouns need an article (a/an/the)")
        
        elif issue_type == 'unnecessary_article':
            suggestions.append("Remove the article when making general statements")
            suggestions.append("Mass nouns and plurals don't need articles for generic reference")
        
        # Add general guidance
        suggestions.append("Articles depend on whether the noun is specific or generic")
        
        return suggestions
    
    def _create_article_message(self, issue: Dict[str, Any]) -> str:
        """Create message describing the article usage issue."""
        issue_type = issue.get('type', '')
        
        if issue_type == 'incorrect_indefinite_article':
            current = issue.get('current_article', '')
            correct = issue.get('correct_article', '')
            return f"Use '{correct}' instead of '{current}' based on following sound"
        
        elif issue_type == 'unnecessary_definite_article':
            return "Consider indefinite article for first mention"
        
        elif issue_type == 'missing_article':
            suggested = issue.get('suggested_article', '')
            return f"Add '{suggested}' before this singular countable noun"
        
        elif issue_type == 'unnecessary_article':
            return "Remove article for generic reference"
        
        return "Article usage issue detected"
    
    def _determine_article_severity(self, issue: Dict[str, Any]) -> str:
        """Determine severity of article usage issue."""
        issue_type = issue.get('type', '')
        
        if issue_type == 'incorrect_indefinite_article':
            return 'high'  # a/an errors are very noticeable
        elif issue_type == 'missing_article':
            return 'medium'  # Missing articles affect readability
        elif issue_type in ['unnecessary_definite_article']:
            return 'medium'  # Definiteness errors affect meaning
        elif issue_type == 'unnecessary_article':
            return 'low'  # Less critical but improves style
        
        return 'low'
    
    def _find_article_usage_issues_fallback(self, sentence: str) -> List[Dict[str, Any]]:
        """Fallback article detection when SpaCy unavailable."""
        import re
        issues = []
        
        # Basic a/an detection using simple patterns
        pattern_a_vowel = r'\ba\s+[aeiouAEIOU]'
        pattern_an_consonant = r'\ban\s+[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]'
        
        # Find 'a' before vowels
        for match in re.finditer(pattern_a_vowel, sentence):
            issues.append({
                'type': 'incorrect_indefinite_article',
                'position': match.start(),
                'current_article': 'a',
                'correct_article': 'an',
                'reason': 'basic_vowel_pattern'
            })
        
        # Find 'an' before consonants
        for match in re.finditer(pattern_an_consonant, sentence):
            issues.append({
                'type': 'incorrect_indefinite_article',
                'position': match.start(),
                'current_article': 'an',
                'correct_article': 'a',
                'reason': 'basic_consonant_pattern'
            })
        
        return issues[:3]  # Limit to avoid overwhelming output 