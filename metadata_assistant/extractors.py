"""
Metadata Extraction Algorithms

Contains extractors for title, keywords, description, and other metadata components.
All extractors use a hybrid approach combining rule-based and AI-powered methods.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
import hashlib

# Try to import spacy for NLP features
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

logger = logging.getLogger(__name__)


class TitleExtractor:
    """Extracts document titles using multiple fallback methods."""
    
    def __init__(self, model_manager=None):
        """
        Initialize title extractor.
        
        Args:
            model_manager: Optional ModelManager for AI fallback
        """
        self.model_manager = model_manager
        
        # Common title patterns for different document formats
        self.title_patterns = [
            # Markdown/AsciiDoc headings (allow leading whitespace)
            r'^\s*#\s+(.+)$',              # Markdown H1
            r'^\s*=\s+(.+)$',              # AsciiDoc title
            r'^(.+)\n=+\s*$',              # Underlined heading (markdown style)
            r'^(.+)\n-+\s*$',              # Underlined heading (alternative)
            
            # DITA/XML titles
            r'<title[^>]*>(.+?)</title>',  # XML title tags
            r'<h1[^>]*>(.+?)</h1>',        # HTML H1 tags
            
            # Document metadata
            r'title:\s*["\']?(.+?)["\']?\s*$',  # YAML frontmatter
            r'Title:\s*(.+)$',                   # Simple title field
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.MULTILINE | re.IGNORECASE) 
                                for pattern in self.title_patterns]
    
    def extract_title(self, spacy_doc, structural_blocks: List[Dict], content: str) -> Dict[str, Any]:
        """
        Extract title using hierarchical approach with confidence scoring.
        
        Args:
            spacy_doc: Parsed spaCy document (may be None)
            structural_blocks: Document structure blocks
            content: Raw document content
            
        Returns:
            Dict with title, confidence, and source information
        """
        candidates = []
        
        # Method 1: Structural heading detection (highest priority)
        structural_title = self._extract_from_structural_blocks(structural_blocks)
        if structural_title:
            candidates.append(structural_title)
        
        # Method 2: Regex-based pattern matching
        pattern_title = self._extract_from_patterns(content)
        if pattern_title:
            candidates.append(pattern_title)
        
        # Method 3: First sentence analysis (if looks like title)
        if spacy_doc:
            sentence_title = self._extract_from_first_sentence(spacy_doc)
            if sentence_title:
                candidates.append(sentence_title)
        
        # Method 4: AI generation (fallback)
        if (not candidates or max(c['confidence'] for c in candidates) < 0.7) and self.model_manager:
            ai_title = self._generate_ai_title(content)
            if ai_title:
                candidates.append(ai_title)
        
        # Return best candidate or default
        if candidates:
            best_candidate = max(candidates, key=lambda x: x['confidence'])
            # Clean up the title
            best_candidate['text'] = self._clean_title(best_candidate['text'])
            return best_candidate
        else:
            return {
                'text': 'Untitled Document',
                'confidence': 0.1,
                'source': 'default',
                'method': 'fallback'
            }
    
    def _extract_from_structural_blocks(self, structural_blocks: List[Dict]) -> Optional[Dict[str, Any]]:
        """Extract title from structural document blocks."""
        if not structural_blocks:
            return None
        
        # Look for the first level 0 or 1 heading
        for block in structural_blocks:
            if (block.get('type') == 'heading' and 
                block.get('level', 999) <= 1 and 
                block.get('content')):
                
                title_text = block['content'].strip()
                if len(title_text) > 3:  # Reasonable title length
                    return {
                        'text': title_text,
                        'confidence': 0.95,
                        'source': 'structural_heading',
                        'method': 'structural_analysis'
                    }
        
        return None
    
    def _extract_from_patterns(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract title using regex patterns."""
        for pattern in self.compiled_patterns:
            match = pattern.search(content)
            if match:
                title_text = match.group(1).strip()
                if 3 <= len(title_text) <= 200:  # Reasonable title length
                    confidence = 0.85 if pattern == self.compiled_patterns[0] else 0.75
                    return {
                        'text': title_text,
                        'confidence': confidence,
                        'source': 'regex_pattern',
                        'method': 'pattern_matching'
                    }
        
        return None
    
    def _extract_from_first_sentence(self, spacy_doc) -> Optional[Dict[str, Any]]:
        """Analyze first sentence to see if it's a title."""
        try:
            first_sent = next(spacy_doc.sents, None)
            if not first_sent:
                return None
            
            sentence_text = first_sent.text.strip()
            
            # Check if it looks like a title
            if self._is_title_like(sentence_text):
                return {
                    'text': sentence_text,
                    'confidence': 0.75,
                    'source': 'linguistic_analysis',
                    'method': 'nlp_analysis'
                }
        except Exception as e:
            logger.debug(f"Error in first sentence analysis: {e}")
        
        return None
    
    def _is_title_like(self, text: str) -> bool:
        """Check if text has title-like characteristics."""
        # Title heuristics
        if len(text) > 200 or len(text) < 3:
            return False
        
        # Ends with period/question mark = less likely to be title
        if text.endswith('.') or text.endswith('?'):
            return False
        
        # All caps might be a title
        if text.isupper() and len(text.split()) <= 10:
            return True
        
        # Title case might be a title
        if text.istitle() and len(text.split()) <= 15:
            return True
        
        # Contains common title words
        title_indicators = ['guide', 'tutorial', 'introduction', 'overview', 'manual', 'documentation']
        if any(indicator in text.lower() for indicator in title_indicators):
            return True
        
        return False
    
    def _generate_ai_title(self, content: str) -> Optional[Dict[str, Any]]:
        """Generate title using AI model (fallback method)."""
        if not self.model_manager or not self.model_manager.is_available():
            return None
        
        try:
            # Use first 500 characters for title generation
            content_sample = content[:500] if content else ""
            
            prompt = f"""Based on this document content, generate a concise, descriptive title (maximum 10 words):

Content:
{content_sample}

Generate only the title, no other text:"""
            
            ai_title = self.model_manager.generate_text(prompt, max_tokens=50, temperature=0.3)
            if ai_title:
                # Clean up AI response
                ai_title = ai_title.strip().strip('"\'')
                if 3 <= len(ai_title) <= 200:
                    return {
                        'text': ai_title,
                        'confidence': 0.6,
                        'source': 'ai_generated',
                        'method': 'llm_generation'
                    }
        except Exception as e:
            logger.debug(f"AI title generation failed: {e}")
        
        return None
    
    def _clean_title(self, title: str) -> str:
        """Clean and normalize title text."""
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title.strip())
        
        # Remove markdown/HTML formatting
        title = re.sub(r'[#*_`]+', '', title)
        title = re.sub(r'<[^>]+>', '', title)
        
        # Remove leading/trailing punctuation and whitespace
        title = title.strip('.,;:!?- \t')
        
        return title


class KeywordExtractor:
    """Extracts relevant keywords using ensemble approach."""
    
    def __init__(self):
        """Initialize keyword extractor."""
        # Technical term boosters
        self.technical_indicators = {
            'api', 'server', 'database', 'configuration', 'install', 'setup',
            'troubleshoot', 'error', 'connection', 'authentication', 'security',
            'performance', 'optimization', 'deployment', 'monitoring', 'docker',
            'kubernetes', 'aws', 'azure', 'cloud', 'microservice', 'devops'
        }
        
        # Common words to filter out
        self.stopwords = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'shall', 'a', 'an', 'some', 'any',
            'all', 'each', 'every', 'few', 'more', 'most', 'other', 'another',
            'such', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
            'now', 'here', 'there', 'when', 'where', 'why', 'how', 'what', 'which',
            'who', 'whom', 'whose', 'whether', 'if', 'unless', 'until', 'while',
            'although', 'though', 'since', 'because', 'as', 'like', 'unlike'
        }
    
    def extract_keywords(self, spacy_doc, content: str, max_keywords: int = 8) -> List[Dict[str, Any]]:
        """
        Extract keywords using ensemble approach.
        
        Args:
            spacy_doc: Parsed spaCy document (may be None)
            content: Raw document text
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keyword dictionaries with scores
        """
        candidates = {}
        
        # Algorithm 1: Named Entity Recognition (if spaCy available)
        if spacy_doc and SPACY_AVAILABLE:
            ner_keywords = self._extract_named_entities(spacy_doc)
            for keyword, data in ner_keywords.items():
                candidates[keyword.lower()] = data
        
        # Algorithm 2: Technical noun phrases
        if spacy_doc and SPACY_AVAILABLE:
            noun_phrases = self._extract_noun_phrases(spacy_doc)
            for phrase, score in noun_phrases.items():
                key = phrase.lower()
                if key not in candidates or candidates[key]['score'] < score:
                    candidates[key] = {
                        'term': phrase,
                        'score': score,
                        'source': 'noun_phrase',
                        'category': 'TECHNICAL'
                    }
        
        # Algorithm 3: Capitalized term extraction (proper nouns, acronyms) - Higher priority
        capitalized_terms = self._extract_capitalized_terms(content)
        for term, score in capitalized_terms.items():
            key = term.lower()
            boosted_score = score * self._get_domain_boost(term)
            if key not in candidates or candidates[key]['score'] < boosted_score:
                candidates[key] = {
                    'term': term,
                    'score': boosted_score,
                    'source': 'capitalized',
                    'category': 'PROPER_NOUN'
                }
        
        # Algorithm 4: Frequency-based extraction (always available)
        freq_keywords = self._extract_frequency_keywords(content)
        for term, score in freq_keywords.items():
            key = term.lower()
            boosted_score = score * self._get_domain_boost(term)
            if key not in candidates or candidates[key]['score'] < boosted_score:
                candidates[key] = {
                    'term': term,
                    'score': boosted_score,
                    'source': 'frequency',
                    'category': 'GENERAL'
                }
        
        # Rank and return top keywords
        sorted_keywords = sorted(candidates.values(), key=lambda x: x['score'], reverse=True)
        
        # Filter out very short or very long terms
        filtered_keywords = []
        for kw in sorted_keywords:
            term = kw['term']
            if 2 <= len(term) <= 30 and not term.lower() in self.stopwords:
                filtered_keywords.append(kw)
        
        return filtered_keywords[:max_keywords]
    
    def _extract_named_entities(self, spacy_doc) -> Dict[str, Dict[str, Any]]:
        """Extract named entities from spaCy document."""
        entities = {}
        
        for ent in spacy_doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'GPE', 'EVENT', 'LANGUAGE']:
                entities[ent.text.lower()] = {
                    'term': ent.text,
                    'score': 0.9,
                    'source': 'ner',
                    'category': ent.label_
                }
        
        return entities
    
    def _extract_noun_phrases(self, spacy_doc) -> Dict[str, float]:
        """Extract technical noun phrases."""
        phrases = {}
        
        for chunk in spacy_doc.noun_chunks:
            phrase = chunk.text.strip()
            
            # Filter for technical relevance
            if (2 <= len(phrase.split()) <= 4 and 
                len(phrase) >= 4 and
                not phrase.lower().startswith(('the ', 'a ', 'an '))):
                
                # Score based on technical indicators and length
                score = 0.7
                if any(tech_word in phrase.lower() for tech_word in self.technical_indicators):
                    score += 0.2
                
                phrases[phrase] = score
        
        return phrases
    
    def _extract_frequency_keywords(self, content: str) -> Dict[str, float]:
        """Extract keywords based on frequency analysis."""
        # Simple word frequency analysis
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        word_freq = Counter(words)
        
        # Calculate scores based on frequency and filtering
        keywords = {}
        total_words = len(words)
        
        for word, freq in word_freq.most_common(50):  # Top 50 by frequency
            if (word not in self.stopwords and 
                freq >= 2 and  # Appears at least twice
                len(word) >= 3):
                
                # TF score with technical term boosting
                score = freq / total_words
                keywords[word] = score
        
        return keywords
    
    def _extract_capitalized_terms(self, content: str) -> Dict[str, float]:
        """Extract capitalized terms (proper nouns, acronyms)."""
        # Find capitalized words and acronyms
        capitalized_pattern = r'\b[A-Z][A-Z0-9]*\b|\b[A-Z][a-z]+\b'
        matches = re.findall(capitalized_pattern, content)
        
        term_freq = Counter(matches)
        terms = {}
        
        for term, freq in term_freq.items():
            if (len(term) >= 2 and 
                freq >= 1 and  # Appears at least once (reduced from 2 for better detection)
                term not in {'The', 'This', 'That', 'For', 'And', 'But', 'Or', 'It', 'Is', 'Are', 'Was', 'Were'}):
                
                # Acronyms get higher scores
                score = 0.8 if term.isupper() else 0.6
                terms[term] = score
        
        return terms
    
    def _get_domain_boost(self, term: str) -> float:
        """Boost scores for technical/domain-specific terms."""
        term_lower = term.lower()
        if term_lower in self.technical_indicators:
            return 1.5
        elif any(indicator in term_lower for indicator in self.technical_indicators):
            return 1.3
        return 1.0


class DescriptionExtractor:
    """Extracts document descriptions using hybrid approach."""
    
    def __init__(self, model_manager=None):
        """
        Initialize description extractor.
        
        Args:
            model_manager: Optional ModelManager for AI enhancement
        """
        self.model_manager = model_manager
    
    def extract_description(self, spacy_doc, content: str, title: str, 
                          max_words: int = 50) -> Dict[str, Any]:
        """
        Extract description using extractive + abstractive summarization.
        
        Args:
            spacy_doc: Parsed spaCy document (may be None)
            content: Raw document content
            title: Document title for context
            max_words: Maximum words in description
            
        Returns:
            Dict with description, confidence, and metadata
        """
        # Stage 1: Extractive summarization
        key_sentences = self._extract_key_sentences(spacy_doc, content, max_sentences=3)
        
        if key_sentences:
            # Combine key sentences
            draft_summary = ' '.join(key_sentences)
            
            # Stage 2: AI refinement (if available)
            if self.model_manager and self.model_manager.is_available():
                refined_description = self._refine_with_ai(draft_summary, title, max_words)
                if refined_description:
                    return {
                        'text': refined_description,
                        'confidence': 0.85,
                        'source': 'extractive_abstractive',
                        'word_count': len(refined_description.split()),
                        'method': 'hybrid_summarization'
                    }
            
            # Use extractive summary directly if AI not available
            truncated = self._truncate_to_words(draft_summary, max_words)
            return {
                'text': truncated,
                'confidence': 0.75,
                'source': 'extractive_only',
                'word_count': len(truncated.split()),
                'method': 'extractive_summarization'
            }
        
        # Fallback: Use first sentences
        first_sentences = self._extract_first_sentences(content, max_sentences=2)
        truncated = self._truncate_to_words(first_sentences, max_words)
        
        return {
            'text': truncated,
            'confidence': 0.5,
            'source': 'first_sentences',
            'word_count': len(truncated.split()),
            'method': 'simple_extraction'
        }
    
    def _extract_key_sentences(self, spacy_doc, content: str, max_sentences: int = 3) -> List[str]:
        """Extract key sentences using simple ranking."""
        if spacy_doc and SPACY_AVAILABLE:
            return self._extract_with_spacy(spacy_doc, max_sentences)
        else:
            return self._extract_with_heuristics(content, max_sentences)
    
    def _extract_with_spacy(self, spacy_doc, max_sentences: int) -> List[str]:
        """Extract key sentences using spaCy analysis."""
        sentences = list(spacy_doc.sents)
        if len(sentences) <= max_sentences:
            return [sent.text.strip() for sent in sentences]
        
        # Score sentences based on multiple factors
        sentence_scores = {}
        
        for i, sent in enumerate(sentences):
            score = 0.0
            
            # Position weight (early sentences more important)
            position_weight = 1.0 / (i + 1) ** 0.5
            score += position_weight * 0.4
            
            # Length weight (moderate length preferred)
            length_score = min(len(sent.text.split()), 20) / 20
            score += length_score * 0.2
            
            # Entity weight (sentences with entities more important)
            entity_count = len([ent for ent in sent.ents if ent.label_ in ['ORG', 'PRODUCT', 'GPE']])
            score += min(entity_count * 0.1, 0.2)
            
            # Technical term weight
            tech_words = ['api', 'server', 'database', 'system', 'application', 'service']
            tech_count = sum(1 for word in sent.text.lower().split() if word in tech_words)
            score += min(tech_count * 0.05, 0.2)
            
            sentence_scores[sent.text] = score
        
        # Select top sentences, maintaining original order
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
        
        # Return in document order
        result = []
        for sent in sentences:
            if sent.text in [s[0] for s in top_sentences]:
                result.append(sent.text.strip())
                if len(result) >= max_sentences:
                    break
        
        return result
    
    def _extract_with_heuristics(self, content: str, max_sentences: int) -> List[str]:
        """Extract key sentences using simple heuristics."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if len(sentences) <= max_sentences:
            return sentences
        
        # Score based on position and length
        scored_sentences = []
        for i, sent in enumerate(sentences[:10]):  # Only consider first 10
            score = 1.0 / (i + 1)  # Position score
            if 10 <= len(sent.split()) <= 25:  # Moderate length bonus
                score += 0.3
            scored_sentences.append((sent, score))
        
        # Return top sentences in original order
        top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:max_sentences]
        return [sent for sent, _ in top_sentences]
    
    def _extract_first_sentences(self, content: str, max_sentences: int = 2) -> str:
        """Simple fallback: extract first few sentences."""
        sentences = re.split(r'[.!?]+', content)
        first_sentences = [s.strip() for s in sentences[:max_sentences] if len(s.strip()) > 5]
        return '. '.join(first_sentences) + '.' if first_sentences else 'No description available.'
    
    def _refine_with_ai(self, draft_summary: str, title: str, max_words: int) -> Optional[str]:
        """Refine description using AI model."""
        try:
            prompt = f"""Refine this description to be more engaging and SEO-friendly while keeping the same meaning. Make it {max_words} words or less.

Title: {title}
Draft: {draft_summary}

Refined description:"""
            
            refined = self.model_manager.generate_text(prompt, max_tokens=max_words*2, temperature=0.3)
            if refined:
                refined = refined.strip()
                # Check word count
                if len(refined.split()) <= max_words * 1.2:  # Allow slight overflow
                    return self._truncate_to_words(refined, max_words)
        except Exception as e:
            logger.debug(f"AI description refinement failed: {e}")
        
        return None
    
    def _truncate_to_words(self, text: str, max_words: int) -> str:
        """Truncate text to maximum word count."""
        words = text.split()
        if len(words) <= max_words:
            return text
        
        truncated = ' '.join(words[:max_words])
        # Try to end at a sentence boundary
        if '.' in truncated:
            sentences = truncated.split('.')
            if len(sentences) > 1:
                truncated = '.'.join(sentences[:-1]) + '.'
        
        return truncated
