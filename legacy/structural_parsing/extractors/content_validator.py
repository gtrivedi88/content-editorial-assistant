"""
Content Validator Module
Validates that uploaded content is technical writing, not resumes, invoices, etc.
"""

import re
import logging
from typing import Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of content validation."""
    is_valid: bool
    confidence: float  # 0.0 to 1.0
    detected_type: str  # e.g., "technical_documentation", "resume", "invoice"
    message: str  # User-friendly message


class ContentValidator:
    """Validates content to ensure it's technical writing."""
    
    # Patterns indicating non-technical content (rejection patterns)
    REJECTION_PATTERNS = {
        'resume': {
            'keywords': [
                r'\b(curriculum vitae|resume|cv)\b',
                r'\b(work experience|employment history|professional experience)\b',
                r'\b(education|bachelor|master|phd|degree|university|college)\b',
                r'\b(skills|competencies|proficiencies)\b',
                r'\b(references available|upon request)\b',
                r'\b(career objective|professional summary|about me)\b',
                r'\b(linkedin\.com|github\.com/[a-z]+$)\b',
                r'\b(gpa|cgpa|grade point)\b',
                r'\b(internship|intern at|worked at|employed at)\b',
                r'\b(hobbies|interests|extracurricular)\b',
            ],
            'weight': 1.5,  # Higher weight = more decisive
            'message': "This appears to be a resume or CV"
        },
        'purchase_order': {
            'keywords': [
                r'\b(purchase order|po number|p\.o\. number)\b',
                r'\b(ship to|bill to|sold to)\b',
                r'\b(quantity ordered|unit price|line total)\b',
                r'\b(subtotal|grand total|tax amount)\b',
                r'\b(payment terms|net \d+ days)\b',
                r'\b(vendor|supplier|buyer)\b',
                r'\b(delivery date|ship date|expected delivery)\b',
            ],
            'weight': 1.5,
            'message': "This appears to be a purchase order"
        },
        'invoice': {
            'keywords': [
                r'\b(invoice|inv\s*#|invoice number)\b',
                r'\b(amount due|total due|balance due)\b',
                r'\b(payment due|due date)\b',
                r'\b(remit to|pay to|payable to)\b',
                r'\b(tax id|ein|vat)\b',
                r'\b(billing address|invoice date)\b',
                r'\b(receipt|paid in full)\b',
            ],
            'weight': 1.5,
            'message': "This appears to be an invoice or receipt"
        },
        'legal_contract': {
            'keywords': [
                r'\b(hereby agree|parties agree|agreement between)\b',
                r'\b(whereas|heretofore|hereinafter)\b',
                r'\b(terms and conditions|binding agreement)\b',
                r'\b(indemnify|indemnification|liability)\b',
                r'\b(jurisdiction|governing law|arbitration)\b',
                r'\b(witness whereof|executed on|effective date)\b',
                r'\b(party of the first part|party of the second part)\b',
                r'\b(non-disclosure|nda|confidentiality agreement)\b',
            ],
            'weight': 1.3,
            'message': "This appears to be a legal contract or agreement"
        },
        'marketing_sales': {
            'keywords': [
                r'\b(limited time offer|act now|don\'t miss)\b',
                r'\b(buy now|order today|shop now)\b',
                r'\b(discount|% off|sale price|special offer)\b',
                r'\b(free shipping|money back guarantee)\b',
                r'\b(call to action|conversion rate|roi)\b',
                r'\b(testimonial|customer review|5 stars)\b',
                r'\b(subscribe now|sign up today|join now)\b',
            ],
            'weight': 1.2,
            'message': "This appears to be marketing or sales content"
        },
        'personal_email': {
            'keywords': [
                r'\b(dear\s+(mom|dad|friend|honey|sweetie))\b',
                r'\b(love you|miss you|thinking of you)\b',
                r'\b(happy birthday|merry christmas|happy anniversary)\b',
                r'\b(how are you|hope you\'re well|hope this finds you)\b',
                r'\b(sent from my iphone|sent from my android)\b',
                r'\b(xoxo|hugs and kisses|yours truly)\b',
            ],
            'weight': 1.3,
            'message': "This appears to be personal correspondence"
        },
        'job_posting': {
            'keywords': [
                r'\b(we are hiring|job opening|position available)\b',
                r'\b(apply now|submit your resume|send cv)\b',
                r'\b(required qualifications|preferred qualifications)\b',
                r'\b(years of experience required|minimum \d+ years)\b',
                r'\b(competitive salary|benefits package|401k)\b',
                r'\b(equal opportunity employer|eoe)\b',
                r'\b(full-time|part-time|contract position)\b',
            ],
            'weight': 1.3,
            'message': "This appears to be a job posting"
        },
        'fiction': {
            'keywords': [
                r'\b(once upon a time|happily ever after)\b',
                r'\b(chapter \d+|prologue|epilogue)\b',
                r'\b(he said|she said|they whispered)\b',
                r'\b(the protagonist|the antagonist|character arc)\b',
                r'\b(plot twist|climax|denouement)\b',
            ],
            'weight': 1.2,
            'message': "This appears to be fiction or creative writing"
        },
        'news_article': {
            'keywords': [
                r'\b(breaking news|developing story|just in)\b',
                r'\b(according to sources|sources say|reportedly)\b',
                r'\b(press release|for immediate release)\b',
                r'\b(correspondent|journalist|reporter)\b',
                r'\b(associated press|reuters|afp)\b',
            ],
            'weight': 1.1,
            'message': "This appears to be a news article"
        },
    }
    
    # Patterns indicating technical content (acceptance patterns)
    TECHNICAL_PATTERNS = {
        'keywords': [
            r'\b(procedure|prerequisites|steps|instructions)\b',
            r'\b(install|configure|deploy|setup)\b',
            r'\b(api|endpoint|request|response)\b',
            r'\b(parameter|argument|return value|method)\b',
            r'\b(error|exception|troubleshoot|debug)\b',
            r'\b(user guide|admin guide|reference guide)\b',
            r'\b(syntax|command|cli|terminal)\b',
            r'\b(module|component|service|function)\b',
            r'\b(authentication|authorization|permission)\b',
            r'\b(database|schema|query|table)\b',
            r'\b(server|client|protocol|port)\b',
            r'\b(file|directory|path|configuration)\b',
            r'\b(note:|important:|warning:|tip:)\b',
            r'\b(example|sample|demonstration)\b',
            r'\b(version|release|changelog)\b',
            r'```[\s\S]*?```',  # Code blocks
            r'`[^`]+`',  # Inline code
        ],
        'weight': 1.0
    }
    
    def __init__(self):
        """Initialize the content validator."""
        # Compile all regex patterns for efficiency
        self._compiled_rejection = {}
        for content_type, config in self.REJECTION_PATTERNS.items():
            self._compiled_rejection[content_type] = {
                'patterns': [re.compile(p, re.IGNORECASE) for p in config['keywords']],
                'weight': config['weight'],
                'message': config['message']
            }
        
        self._compiled_technical = [
            re.compile(p, re.IGNORECASE | re.MULTILINE) 
            for p in self.TECHNICAL_PATTERNS['keywords']
        ]
    
    def validate(self, text: str) -> ValidationResult:
        """
        Validate if content is technical writing.
        
        Args:
            text: The text content to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        if not text or len(text.strip()) < 50:
            return ValidationResult(
                is_valid=False,
                confidence=1.0,
                detected_type="insufficient_content",
                message="Content is too short to analyze"
            )
        
        text_lower = text.lower()
        text_length = len(text)
        
        # Calculate rejection scores
        rejection_scores = self._calculate_rejection_scores(text_lower, text_length)
        
        # Calculate technical score
        technical_score = self._calculate_technical_score(text, text_length)
        
        # Find highest rejection score
        max_rejection = max(rejection_scores.items(), key=lambda x: x[1])
        max_rejection_type, max_rejection_score = max_rejection
        
        logger.debug(f"Rejection scores: {rejection_scores}")
        logger.debug(f"Technical score: {technical_score}")
        
        # Decision logic
        return self._make_decision(
            max_rejection_type, 
            max_rejection_score, 
            technical_score,
            rejection_scores
        )
    
    def _calculate_rejection_scores(self, text: str, text_length: int) -> Dict[str, float]:
        """Calculate rejection scores for each non-technical content type."""
        scores = {}
        
        for content_type, config in self._compiled_rejection.items():
            match_count = 0
            for pattern in config['patterns']:
                matches = pattern.findall(text)
                match_count += len(matches)
            
            # Normalize by text length (per 1000 chars) and apply weight
            if text_length > 0:
                normalized_score = (match_count / (text_length / 1000)) * config['weight']
                scores[content_type] = min(normalized_score, 1.0)  # Cap at 1.0
            else:
                scores[content_type] = 0.0
        
        return scores
    
    def _calculate_technical_score(self, text: str, text_length: int) -> float:
        """Calculate technical content score."""
        match_count = 0
        
        for pattern in self._compiled_technical:
            matches = pattern.findall(text)
            match_count += len(matches)
        
        # Normalize by text length (per 1000 chars)
        if text_length > 0:
            normalized_score = (match_count / (text_length / 1000)) * self.TECHNICAL_PATTERNS['weight']
            return min(normalized_score, 1.0)
        
        return 0.0
    
    def _make_decision(
        self, 
        max_rejection_type: str, 
        max_rejection_score: float, 
        technical_score: float,
        all_rejection_scores: Dict[str, float]
    ) -> ValidationResult:
        """Make final validation decision based on scores."""
        
        # High confidence rejection (>80% rejection score)
        if max_rejection_score > 0.8:
            message = self._compiled_rejection[max_rejection_type]['message']
            return ValidationResult(
                is_valid=False,
                confidence=max_rejection_score,
                detected_type=max_rejection_type,
                message=f"{message}. This tool is designed for technical documentation only."
            )
        
        # Medium confidence (50-80%): Allow with warning if technical score is also present
        if max_rejection_score > 0.5:
            if technical_score > 0.3:
                # Mixed content - allow with warning
                message = self._compiled_rejection[max_rejection_type]['message']
                return ValidationResult(
                    is_valid=True,
                    confidence=0.6,
                    detected_type="mixed_content",
                    message=f"Warning: {message}, but technical elements were detected. Results may be limited."
                )
            else:
                # More likely non-technical
                message = self._compiled_rejection[max_rejection_type]['message']
                return ValidationResult(
                    is_valid=False,
                    confidence=max_rejection_score,
                    detected_type=max_rejection_type,
                    message=f"{message}. This tool is designed for technical documentation only."
                )
        
        # Low rejection score - likely technical content
        if technical_score > 0.2:
            return ValidationResult(
                is_valid=True,
                confidence=0.9,
                detected_type="technical_documentation",
                message="Content validated as technical documentation"
            )
        
        # Uncertain - allow but with lower confidence
        return ValidationResult(
            is_valid=True,
            confidence=0.7,
            detected_type="unknown",
            message="Content type uncertain, proceeding with analysis"
        )


# Singleton instance for easy import
content_validator = ContentValidator()

